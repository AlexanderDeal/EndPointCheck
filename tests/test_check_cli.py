import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from test_checker import LocalServer
from test_checker import server as server
from test_config import configuration, endpoint


def command(entrypoint: str) -> list[str]:
    if entrypoint == "module":
        return [sys.executable, "-m", "endpointcheck"]
    launcher = Path(sys.executable).parent / (
        "endpointcheck.exe" if os.name == "nt" else "endpointcheck"
    )
    assert launcher.is_file(), "reinstall the project to create its launcher"
    return [str(launcher)]


def invoke(
    entrypoint: str, cwd: Path, *arguments: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command(entrypoint) + list(arguments),
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
        timeout=10,
        check=False,
    )


def write_config(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


@pytest.mark.parametrize("entrypoint", ["module", "launcher"])
def test_all_healthy_subprocess(
    entrypoint: str, tmp_path: Path, server: LocalServer
) -> None:
    path = tmp_path / "config with spaces.json"
    write_config(
        path,
        configuration(
            endpoint(name="first", url=server.url + "/fast"),
            endpoint(name="second", url=server.url + "/target"),
        ),
    )
    result = invoke(entrypoint, tmp_path, "check", str(path))
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.index("first [healthy]") < result.stdout.index(
        "second [healthy]"
    )
    assert f"URL: {server.url}/fast" in result.stdout
    assert f"URL: {server.url}/target" in result.stdout
    assert result.stdout.count("HTTP status: 200") == 2
    assert len(re.findall(r"Elapsed: \d+\.\d{3} s", result.stdout)) == 2
    assert result.stdout.endswith("Summary: healthy=2, slow=0, failed=0, timed out=0\n")
    assert "abcdef" not in result.stdout  # The server's response body.


@pytest.mark.parametrize("entrypoint", ["module", "launcher"])
def test_mixed_subprocess(entrypoint: str, tmp_path: Path, server: LocalServer) -> None:
    path = tmp_path / "mixed.json"
    write_config(
        path,
        configuration(
            endpoint(
                name="slow",
                url=server.url + "/body-delay",
                latency_threshold_seconds=0.1,
                read_timeout_seconds=2,
            ),
            endpoint(name="failed", url=server.url + "/unexpected"),
            endpoint(
                name="stalled", url=server.url + "/stall", read_timeout_seconds=0.15
            ),
            endpoint(
                name="healthy",
                url=server.url + "/fast",
                read_timeout_seconds=2,
                latency_threshold_seconds=3,
            ),
            workers=1,
        ),
    )
    result = invoke(entrypoint, tmp_path, "check", str(path))
    assert result.returncode == 1
    assert result.stderr == ""
    headers = [
        "slow [slow]",
        "failed [failed]",
        "stalled [timed out]",
        "healthy [healthy]",
    ]
    positions = [result.stdout.index(header) for header in headers]
    assert positions == sorted(positions)
    assert result.stdout.count("HTTP status: 200") == 3
    assert "HTTP status: 503" in result.stdout
    assert "Error: Expected HTTP 200, received HTTP 503" in result.stdout
    stalled_block = result.stdout.split("stalled [timed out]")[1].split(
        "healthy [healthy]"
    )[0]
    assert "HTTP status: 200" in stalled_block
    assert "Error: ConnectionError:" in stalled_block
    assert "timed out" in stalled_block.lower()
    assert result.stdout.endswith("Summary: healthy=1, slow=1, failed=1, timed out=1\n")
    assert "abcdef" not in result.stdout


@pytest.mark.parametrize("entrypoint", ["module", "launcher"])
def test_unavailable_status_subprocess(
    entrypoint: str, tmp_path: Path, server: LocalServer
) -> None:
    path = tmp_path / "timeout.json"
    write_config(
        path,
        configuration(endpoint(url=server.url + "/headers", read_timeout_seconds=0.15)),
    )
    result = invoke(entrypoint, tmp_path, "check", str(path))
    assert result.returncode == 1
    assert result.stderr == ""
    assert "health [timed out]" in result.stdout
    assert "HTTP status: unavailable" in result.stdout
    assert "Error: ReadTimeout:" in result.stdout
    assert result.stdout.endswith("Summary: healthy=0, slow=0, failed=0, timed out=1\n")


@pytest.mark.parametrize("entrypoint", ["module", "launcher"])
@pytest.mark.parametrize("invalid", ["json", "later_endpoint", "workers"])
def test_invalid_input_makes_zero_requests(
    entrypoint: str, invalid: str, tmp_path: Path, server: LocalServer
) -> None:
    path = tmp_path / "invalid.json"
    first = endpoint(url=server.url + "/fast")
    text = configuration(first)
    if invalid == "json":
        text = text[:-1]
    elif invalid == "later_endpoint":
        text = configuration(
            first,
            endpoint(name="later", url=server.url + "/target", expected_status=600),
        )
    else:
        text = configuration(first, workers=True)
    write_config(path, text)
    result = invoke(entrypoint, tmp_path, "check", str(path))
    assert result.returncode == 2
    assert result.stdout == ""
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr
    assert server.visited == []


@pytest.mark.parametrize("entrypoint", ["module", "launcher"])
def test_validate_still_makes_zero_requests(
    entrypoint: str, tmp_path: Path, server: LocalServer
) -> None:
    path = tmp_path / "valid.json"
    write_config(path, configuration(endpoint(url=server.url + "/fast")))
    result = invoke(entrypoint, tmp_path, "validate", str(path))
    assert result.returncode == 0
    assert result.stdout == "Configuration valid: 1 endpoint(s).\n"
    assert result.stderr == ""
    assert server.visited == []


@pytest.mark.parametrize("entrypoint", ["module", "launcher"])
def test_control_characters_in_name_subprocess(
    entrypoint: str, tmp_path: Path, server: LocalServer
) -> None:
    path = tmp_path / "controls.json"
    name = "a\n\r\t\x1b[31m\x9b\u202eb"
    write_config(path, configuration(endpoint(name=name, url=server.url + "/fast")))
    result = invoke(entrypoint, tmp_path, "check", str(path))
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines()[0] == r"a\n\r\t\x1b[31m\x9b\u202eb [healthy]"
    assert "\x1b" not in result.stdout and "\x9b" not in result.stdout
    assert len(result.stdout.splitlines()) == 6


@pytest.mark.parametrize(
    "arguments",
    [
        ["--help"],
        ["validate", "--help"],
        ["check", "--help"],
        [],
        ["unknown"],
        ["unknown\n\x1b[31m"],
        ["check"],
        ["check", "missing.json"],
        ["validate", "missing.json"],
    ],
)
def test_entrypoints_equivalent_help_and_errors(
    tmp_path: Path, arguments: list[str]
) -> None:
    module = invoke("module", tmp_path, *arguments)
    launcher = invoke("launcher", tmp_path, *arguments)
    assert (module.returncode, module.stdout, module.stderr) == (
        launcher.returncode,
        launcher.stdout,
        launcher.stderr,
    )
    if "--help" in arguments:
        assert module.returncode == 0
        assert module.stderr == ""
        if arguments == ["--help"]:
            assert "validate" in module.stdout and "check" in module.stdout
    else:
        assert module.returncode == 2
        assert module.stdout == ""
        assert "Traceback" not in module.stderr
        assert "\x1b" not in module.stderr


@pytest.mark.parametrize("entrypoint", ["module", "launcher"])
def test_broken_body_preserves_received_status(
    entrypoint: str, tmp_path: Path, server: LocalServer
) -> None:
    path = tmp_path / "broken.json"
    write_config(path, configuration(endpoint(url=server.url + "/broken")))
    result = invoke(entrypoint, tmp_path, "check", str(path))
    assert result.returncode == 1
    assert result.stderr == ""
    assert "health [failed]" in result.stdout
    assert "HTTP status: 200" in result.stdout
    assert "Error: ChunkedEncodingError:" in result.stdout
    assert result.stdout.endswith("Summary: healthy=0, slow=0, failed=1, timed out=0\n")


def test_check_entrypoints_equivalent_except_duration(
    tmp_path: Path, server: LocalServer
) -> None:
    path = tmp_path / "config.json"
    write_config(path, configuration(endpoint(url=server.url + "/fast")))
    results = [
        invoke(entrypoint, tmp_path, "check", str(path))
        for entrypoint in ["module", "launcher"]
    ]
    assert all(result.returncode == 0 and not result.stderr for result in results)
    normalized = [
        re.sub(r"Elapsed: \d+\.\d{3} s", "Elapsed: <measured> s", result.stdout)
        for result in results
    ]
    assert normalized[0] == normalized[1]
