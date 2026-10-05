"""Observe the real demo handler independently of the inspector implementation."""

import json
import os
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import closing
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from demo_api.server import DemoHandler
from endpointcheck.config import load_configuration

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def demo_server() -> Iterator[ThreadingHTTPServer]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
    server.daemon_threads = False
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.05}
    )
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()


@pytest.mark.parametrize(
    "path,status",
    [("/ready", 200), ("/healthy", 200), ("/error", 500), ("/missing", 404)],
)
def test_prompt_response(
    demo_server: ThreadingHTTPServer, path: str, status: int
) -> None:
    with closing(
        HTTPConnection("127.0.0.1", demo_server.server_port, timeout=2)
    ) as connection:
        started = time.monotonic()
        connection.request("GET", path)
        response = connection.getresponse()
        assert response.status == status
        assert response.read() == b"demo response\n"
        assert time.monotonic() - started < 1


@pytest.mark.parametrize("path", ["/slow", "/timeout"])
def test_delays_and_flushed_headers(
    demo_server: ThreadingHTTPServer, path: str
) -> None:
    with closing(
        HTTPConnection("127.0.0.1", demo_server.server_port, timeout=3)
    ) as connection:
        started = time.monotonic()
        connection.request("GET", path)
        response = connection.getresponse()
        headers_elapsed = time.monotonic() - started
        assert response.status == 200
        assert response.read() == b"demo response\n"
        elapsed = time.monotonic() - started
        if path == "/slow":
            assert headers_elapsed >= 0.5
            assert 0.5 <= elapsed < 2
        else:
            assert headers_elapsed < 0.5
            assert 0.9 <= elapsed < 2.5


def test_concurrent_readiness(
    demo_server: ThreadingHTTPServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Readiness can complete while two handlers are waiting to deliver bodies.
    both_waiting = threading.Event()
    release = threading.Event()
    lock = threading.Lock()
    waiting = 0

    def controlled_delay(seconds: float) -> None:
        nonlocal waiting
        with lock:
            waiting += 1
            if waiting == 2:
                both_waiting.set()
        release.wait(timeout=3)

    monkeypatch.setattr("demo_api.server.sleep", controlled_delay)
    connections = [
        HTTPConnection("127.0.0.1", demo_server.server_port, timeout=3)
        for _ in range(2)
    ]
    try:
        for connection in connections:
            connection.request("GET", "/timeout")
        responses = [connection.getresponse() for connection in connections]
        assert both_waiting.wait(timeout=2)
        with closing(
            HTTPConnection("127.0.0.1", demo_server.server_port, timeout=2)
        ) as ready:
            ready.request("GET", "/ready")
            assert ready.getresponse().read() == b"demo response\n"
        assert all(response.status == 200 for response in responses)
        release.set()
        assert all(response.read() == b"demo response\n" for response in responses)
    finally:
        release.set()
        for connection in connections:
            connection.close()


def test_expected_disconnect_is_quiet(
    demo_server: ThreadingHTTPServer, capsys: pytest.CaptureFixture[str]
) -> None:
    with closing(
        HTTPConnection("127.0.0.1", demo_server.server_port, timeout=2)
    ) as connection:
        connection.request("GET", "/timeout")
        response = connection.getresponse()
        assert response.status == 200
        response.close()
    # Join handler threads before inspecting stderr, rather than racing the delay.
    demo_server.shutdown()
    demo_server.server_close()
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize(
    "filename,expected_code",
    [("mixed.json", 1), ("mixed.json", 1), ("all-healthy.json", 0)],
)
def test_local_demo_cli(
    demo_server: ThreadingHTTPServer, tmp_path: Path, filename: str, expected_code: int
) -> None:
    original = ROOT / "demo" / filename
    load_configuration(
        original
    )  # Verify service-name config itself before adapting locally.
    configuration = json.loads(original.read_text())
    host, port = "127.0.0.1", demo_server.server_port
    for endpoint in configuration["endpoints"]:
        endpoint["url"] = endpoint["url"].replace(
            "http://demo-api:8000", f"http://{host}:{port}"
        )
    local = tmp_path / "config.json"
    local.write_text(json.dumps(configuration))
    result = subprocess.run(
        [sys.executable, "-m", "endpointcheck", "check", str(local)],
        capture_output=True,
        text=True,
        timeout=8,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    assert result.returncode == expected_code
    assert result.stderr == ""
    if filename == "mixed.json":
        assert "Summary: healthy=1, slow=1, failed=1, timed out=1" in result.stdout
        headings = [line for line in result.stdout.splitlines() if " [" in line]
        assert headings == [
            "healthy [healthy]",
            "slow [slow]",
            "error [failed]",
            "timeout [timed out]",
        ]
        assert "HTTP status: 200" in result.stdout.split("timeout [timed out]", 1)[1]
    else:
        assert "Summary: healthy=1, slow=0, failed=0, timed out=0" in result.stdout
    print(
        f"\nLocal {filename}; actual inspector exit={result.returncode}\n{result.stdout}"
    )
