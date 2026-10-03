import subprocess
import sys
from pathlib import Path

import pytest
from test_config import configuration, endpoint

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "endpointcheck", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


def test_valid_cli(tmp_path: Path) -> None:
    path = tmp_path / "valid config.json"
    path.write_text(configuration(endpoint()), encoding="utf-8")
    result = run_cli("validate", str(path))
    assert result.returncode == 0
    assert result.stdout == "Configuration valid: 1 endpoint(s).\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    "content, expected",
    [
        ("{", "Invalid JSON"),
        (configuration(endpoint(expected_status=600)), "expected_status"),
        (
            configuration(endpoint(), endpoint(name="other", expected_status=600)),
            "endpoints[1]",
        ),
    ],
)
def test_invalid_config_cli(tmp_path: Path, content: str, expected: str) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(content, encoding="utf-8")
    result = run_cli("validate", str(path))
    assert result.returncode == 2
    assert result.stdout == ""
    assert expected in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("kind", ["missing", "directory", "invalid_encoding"])
def test_unreadable_cli(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "config.json"
    if kind == "directory":
        path.mkdir()
    elif kind == "invalid_encoding":
        path.write_bytes(b"\xff")
    result = run_cli("validate", str(path))
    assert result.returncode == 2
    assert result.stdout == ""
    assert "Cannot read configuration" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["validate"],
        ["check", "config.json"],
        ["validate", "config.json", "extra"],
        ["--unknown"],
    ],
)
def test_invalid_invocation(arguments: list[str]) -> None:
    result = run_cli(*arguments)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr
