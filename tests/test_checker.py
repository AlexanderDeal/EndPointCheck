import socket
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import cast

import pytest
import requests
from test_config import configuration, endpoint
from urllib3.exceptions import ReadTimeoutError

import endpointcheck.checker as checker
from endpointcheck.config import EndpointSettings, parse_configuration


class LocalServer(HTTPServer):
    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), Handler)
        self.visited: list[str] = []
        self.stop = threading.Event()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server_port}"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        try:
            self._respond()
        except BrokenPipeError, ConnectionResetError, ConnectionAbortedError:
            pass

    def _respond(self) -> None:
        server = cast(LocalServer, self.server)
        server.visited.append(self.path)
        if self.path == "/headers":
            server.stop.wait(0.8)
        status = 503 if self.path == "/unexpected" else 200
        if self.path.startswith("/redirect"):
            status = 302
        self.send_response(status)
        if status == 302:
            self.send_header("Location", "/target")
        length = 10 if self.path in {"/broken", "/redirect-broken"} else 6
        self.send_header("Content-Length", str(length))
        self.end_headers()
        try:
            if self.path in {"/stall", "/redirect-stall"}:
                self.wfile.write(b"a")
                self.wfile.flush()
                server.stop.wait(0.8)
                self.wfile.write(b"bcdef")
            elif self.path in {"/broken", "/redirect-broken"}:
                self.wfile.write(b"a")
                self.wfile.flush()
                self.close_connection = True
            elif self.path == "/body-delay":
                server.stop.wait(0.35)
                self.wfile.write(b"abcdef")
            elif self.path == "/trickle":
                for byte in b"abcdef":
                    server.stop.wait(0.08)
                    self.wfile.write(bytes([byte]))
                    self.wfile.flush()
            else:
                self.wfile.write(b"abcdef")
        except BrokenPipeError, ConnectionResetError, ConnectionAbortedError:
            # Expected when the client times out and closes its connection.
            pass

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> Iterator[LocalServer]:
    # Keep loopback test traffic independent of machine proxy settings.
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    instance = LocalServer()
    thread = threading.Thread(
        target=instance.serve_forever, kwargs={"poll_interval": 0.02}
    )
    thread.start()
    try:
        yield instance
    finally:
        instance.stop.set()
        instance.shutdown()
        instance.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive(), "test server did not shut down"


def settings(url: str, **changes: object) -> EndpointSettings:
    values: dict[str, object] = {
        "url": url,
        "latency_threshold_seconds": 2,
        "connect_timeout_seconds": 0.4,
        "read_timeout_seconds": 1,
    }
    values.update(changes)
    return parse_configuration(configuration(endpoint(**values))).endpoints[0]


def test_fast_expected_response(
    server: LocalServer, capsys: pytest.CaptureFixture[str]
) -> None:
    item = settings(server.url + "/fast")
    result = checker.check_endpoint(item)
    assert (result.name, result.url) == (item.name, item.url)
    assert result.outcome == "healthy"
    assert result.status_code == 200
    assert result.error is None
    assert 0 <= result.elapsed_seconds < 2
    assert capsys.readouterr() == ("", "")


def test_full_body_time_and_slow_result(server: LocalServer) -> None:
    result = checker.check_endpoint(
        settings(server.url + "/body-delay", latency_threshold_seconds=0.1)
    )
    assert result.outcome == "slow"
    assert result.elapsed_seconds >= 0.3
    assert result.status_code == 200
    assert result.error is None


def test_unexpected_status_precedes_slow(
    server: LocalServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    ticks = iter([10.0, 12.0])
    monkeypatch.setattr(checker, "monotonic", lambda: next(ticks))
    result = checker.check_endpoint(
        settings(server.url + "/unexpected", latency_threshold_seconds=0.5)
    )
    assert result.outcome == "failed"
    assert result.status_code == 503
    assert result.elapsed_seconds == 2
    assert result.error == "Expected HTTP 200, received HTTP 503"


@pytest.mark.parametrize("expected, outcome", [(200, "failed"), (302, "healthy")])
def test_redirect_is_not_followed(
    server: LocalServer, expected: int, outcome: str
) -> None:
    result = checker.check_endpoint(
        settings(server.url + "/redirect", expected_status=expected)
    )
    assert result.outcome == outcome
    assert result.status_code == 302
    assert result.elapsed_seconds >= 0
    assert server.visited == ["/redirect"]


@pytest.mark.parametrize(
    "path, status", [("/headers", None), ("/stall", 200), ("/redirect-stall", 302)]
)
def test_real_timeouts_preserve_status(
    server: LocalServer, path: str, status: int | None
) -> None:
    result = checker.check_endpoint(
        settings(
            server.url + path, read_timeout_seconds=0.15, latency_threshold_seconds=0.01
        )
    )
    assert result.outcome == "timed out"
    assert result.status_code == status
    assert result.elapsed_seconds >= 0.1
    assert result.error is not None and "timed out" in result.error.lower()
    assert server.visited == [path]


@pytest.mark.parametrize("path", ["/headers", "/stall"])
def test_installed_requests_timeout_shapes(server: LocalServer, path: str) -> None:
    # Independent library observation, not just an assertion about our mapper.
    with requests.Session() as session:
        with pytest.raises(requests.RequestException) as caught:
            with session.get(
                server.url + path, stream=True, timeout=(0.4, 0.15)
            ) as response:
                for _chunk in response.iter_content(65536):
                    pass
    if path == "/headers":
        assert isinstance(caught.value, requests.ReadTimeout)
    else:
        assert isinstance(caught.value, requests.ConnectionError)
        assert not isinstance(caught.value, requests.ReadTimeout)
        assert isinstance(caught.value.args[0], ReadTimeoutError)


def test_connection_refusal_is_failed(server: LocalServer) -> None:
    # A bound, non-listening socket reserves the port without accepting connections.
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
        result = checker.check_endpoint(
            settings(f"http://127.0.0.1:{port}/", connect_timeout_seconds=5)
        )
    assert result.outcome == "failed"
    assert result.status_code is None
    assert result.elapsed_seconds >= 0
    assert result.error is not None and "ConnectionError" in result.error


@pytest.mark.parametrize("path, status", [("/broken", 200), ("/redirect-broken", 302)])
def test_incomplete_body_is_failed(server: LocalServer, path: str, status: int) -> None:
    result = checker.check_endpoint(settings(server.url + path, expected_status=status))
    assert result.outcome == "failed"
    assert result.status_code == status
    assert result.elapsed_seconds >= 0
    assert result.error is not None and "ChunkedEncodingError" in result.error


def test_regular_data_exceeds_read_timeout_without_timing_out(
    server: LocalServer,
) -> None:
    result = checker.check_endpoint(
        settings(
            server.url + "/trickle",
            read_timeout_seconds=0.3,
            latency_threshold_seconds=0.1,
        )
    )
    assert result.outcome == "slow"
    assert result.elapsed_seconds >= 0.4
    assert result.elapsed_seconds > 0.3
    assert result.status_code == 200
    assert result.error is None


@pytest.mark.parametrize(
    "elapsed, outcome", [(0.5, "healthy"), (0.5001, "slow"), (0.4999, "healthy")]
)
def test_exact_threshold(
    server: LocalServer, monkeypatch: pytest.MonkeyPatch, elapsed: float, outcome: str
) -> None:
    ticks = iter([0.0, elapsed])
    monkeypatch.setattr(checker, "monotonic", lambda: next(ticks))
    result = checker.check_endpoint(
        settings(server.url + "/fast", latency_threshold_seconds=0.5)
    )
    assert result.outcome == outcome
    assert result.elapsed_seconds == elapsed


def test_simulated_connection_timeout_and_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item = settings(
        "https://example.invalid/",
        connect_timeout_seconds=0.25,
        read_timeout_seconds=0.75,
    )

    def timeout(
        self: requests.Session, url: str, **kwargs: object
    ) -> requests.Response:
        assert url == item.url
        assert kwargs["timeout"] == (0.25, 0.75)
        assert kwargs["allow_redirects"] is False
        assert kwargs["stream"] is True
        adapter = cast(requests.adapters.HTTPAdapter, self.get_adapter(url))
        assert adapter.max_retries.total == 0
        raise requests.ConnectTimeout("simulated connection timeout")

    monkeypatch.setattr(requests.Session, "get", timeout)
    ticks = iter([1.0, 1.25])
    monkeypatch.setattr(checker, "monotonic", lambda: next(ticks))
    result = checker.check_endpoint(item)
    assert result.outcome == "timed out"
    assert result.status_code is None
    assert result.elapsed_seconds == 0.25
    assert result.error == "ConnectTimeout: simulated connection timeout"


@pytest.mark.parametrize(
    "path", ["/fast", "/headers", "/stall", "/broken", "/redirect-stall"]
)
def test_resources_closed(
    server: LocalServer, monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    responses: list[requests.Response] = []
    sessions: list[requests.Session] = []
    close_response = requests.Response.close
    close_session = requests.Session.close

    def response_close(self: requests.Response) -> None:
        responses.append(self)
        close_response(self)

    def session_close(self: requests.Session) -> None:
        sessions.append(self)
        close_session(self)

    monkeypatch.setattr(requests.Response, "close", response_close)
    monkeypatch.setattr(requests.Session, "close", session_close)
    checker.check_endpoint(settings(server.url + path, read_timeout_seconds=0.15))
    if path == "/headers":
        assert not responses  # requests has not delivered a Response to the hook.
    else:
        assert responses
    assert all(response.raw.closed for response in responses)
    assert len(sessions) == 1


def test_programming_error_during_body_closes_response(
    server: LocalServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    closed: list[requests.Response] = []
    original_close = requests.Response.close

    def broken(self: requests.Response, chunk_size: int) -> Iterator[bytes]:
        raise RuntimeError("body programming bug")

    def close(self: requests.Response) -> None:
        closed.append(self)
        original_close(self)

    monkeypatch.setattr(requests.Response, "iter_content", broken)
    monkeypatch.setattr(requests.Response, "close", close)
    with pytest.raises(RuntimeError, match="body programming bug"):
        checker.check_endpoint(settings(server.url + "/fast"))
    assert len(closed) == 1
    assert closed[0].raw.closed


def test_unexpected_programming_error_visible_and_session_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[requests.Session] = []
    original_close = requests.Session.close

    def broken(self: requests.Session, url: str, **kwargs: object) -> requests.Response:
        raise RuntimeError("programming bug")

    def close(self: requests.Session) -> None:
        closed.append(self)
        original_close(self)

    monkeypatch.setattr(requests.Session, "get", broken)
    monkeypatch.setattr(requests.Session, "close", close)
    with pytest.raises(RuntimeError, match="programming bug"):
        checker.check_endpoint(settings("https://example.invalid/"))
    assert len(closed) == 1
