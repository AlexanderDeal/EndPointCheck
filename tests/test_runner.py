import threading
from collections.abc import Iterator
from concurrent.futures import Future, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import cast

import pytest
from test_config import configuration, endpoint

import endpointcheck.checker as checker
import endpointcheck.runner as runner
from endpointcheck.checker import CheckResult
from endpointcheck.config import EndpointSettings, Settings, parse_configuration


def settings(workers: int, urls: list[str]) -> Settings:
    return parse_configuration(
        configuration(
            *(
                endpoint(
                    name=f"endpoint-{index}",
                    url=url,
                    latency_threshold_seconds=3,
                    connect_timeout_seconds=1,
                    read_timeout_seconds=1,
                )
                for index, url in enumerate(urls)
            ),
            workers=workers,
        )
    )


def healthy(item: EndpointSettings) -> CheckResult:
    return CheckResult(item.name, item.url, "healthy", 0.01, 200, None)


class ConcurrentServer(ThreadingHTTPServer):
    # Join handler threads on close, rather than abandoning daemon threads.
    daemon_threads = False

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), Handler)
        self.lock = threading.Lock()
        self.active = 0
        self.maximum = 0
        self.visited: list[str] = []
        self.overlap = threading.Event()
        self.stop = threading.Event()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server_port}"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        server = cast(ConcurrentServer, self.server)
        self.connection.settimeout(2)
        counted = True
        with server.lock:
            server.active += 1
            server.maximum = max(server.maximum, server.active)
            server.visited.append(self.path)
            if server.active >= 2:
                server.overlap.set()
        try:
            if self.path.startswith("/overlap"):
                # Concurrent requests rendezvous; single-worker runs use /serial.
                server.overlap.wait(2)
            elif self.path.startswith("/serial"):
                server.stop.wait(0.03)
            status = 503 if self.path == "/failed" else 200
            self.send_response(status)
            self.send_header("Content-Length", "1")
            self.end_headers()
            if self.path == "/timeout":
                server.stop.wait(0.7)
            # Keep final-byte delivery and decrement atomic with respect to new
            # handler counting, so handler tail bookkeeping cannot inflate overlap.
            with server.lock:
                self.wfile.write(b"x")
                self.wfile.flush()
                server.active -= 1
                counted = False
        except (
            BrokenPipeError,
            ConnectionResetError,
            ConnectionAbortedError,
            TimeoutError,
        ):
            pass
        finally:
            if counted:
                with server.lock:
                    server.active -= 1

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> Iterator[ConcurrentServer]:
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    instance = ConcurrentServer()
    thread = threading.Thread(
        target=instance.serve_forever, kwargs={"poll_interval": 0.02}
    )
    thread.start()
    try:
        yield instance
    finally:
        instance.stop.set()
        instance.overlap.set()
        instance.shutdown()
        instance.server_close()  # Waits for all non-daemon handlers.
        thread.join(timeout=3)
        assert not thread.is_alive()
        assert instance.active == 0


@pytest.mark.parametrize("workers", [1, 2, 3])
def test_real_http_concurrency(server: ConcurrentServer, workers: int) -> None:
    route = "serial" if workers == 1 else "overlap"
    config = settings(workers, [f"{server.url}/{route}-{i}" for i in range(7)])
    results = runner.run_checks(config)
    assert [result.name for result in results] == [
        item.name for item in config.endpoints
    ]
    assert all(result.outcome == "healthy" for result in results)
    assert len(server.visited) == 7
    assert server.maximum <= workers
    if workers == 1:
        assert server.maximum == 1
        assert not server.overlap.is_set()
    else:
        assert server.maximum >= 2
        assert server.overlap.is_set()


@pytest.mark.parametrize("workers", [1, 2, 3])
def test_simulated_active_checks_and_sequential_execution(
    workers: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = settings(workers, [f"http://localhost/{i}" for i in range(6)])
    lock = threading.Lock()
    rendezvous = threading.Barrier(workers, timeout=3)
    active = 0
    maximum = 0
    starts: list[str] = []
    finishes: list[str] = []

    def check(item: EndpointSettings) -> CheckResult:
        nonlocal active, maximum
        with lock:
            active += 1
            maximum = max(maximum, active)
            starts.append(item.name)
        try:
            rendezvous.wait()
            return healthy(item)
        finally:
            with lock:
                finishes.append(item.name)
                active -= 1

    monkeypatch.setattr(runner, "check_endpoint", check)
    results = runner.run_checks(config)
    assert maximum == workers
    assert active == 0
    assert len(results) == 6
    assert sorted(starts) == sorted(item.name for item in config.endpoints)
    if workers == 1:
        assert starts == finishes == [item.name for item in config.endpoints]


def test_queued_work_starts_before_first_finishes_and_collection_is_on_main_thread(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config = settings(
        2,
        ["http://localhost/first", "http://localhost/second", "http://localhost/third"],
    )
    first_started = threading.Event()
    first_finished = threading.Event()
    third_finished = threading.Event()
    lock = threading.Lock()
    completed: list[str] = []
    worker_threads: list[int] = []
    main_id = threading.get_ident()
    observed_collections: list[int] = []

    def check(item: EndpointSettings) -> CheckResult:
        with lock:
            worker_threads.append(threading.get_ident())
        if item.name == "endpoint-0":
            first_started.set()
            assert third_finished.wait(3), "queued third check never started"
            first_finished.set()
        else:
            assert first_started.wait(3)
            assert not first_finished.is_set()
        with lock:
            completed.append(item.name)
        if item.name == "endpoint-2":
            third_finished.set()
        return healthy(item)

    def collect(
        futures: dict[Future[CheckResult], int],
    ) -> Iterator[Future[CheckResult]]:
        for future in as_completed(futures):
            observed_collections.append(threading.get_ident())
            yield future

    monkeypatch.setattr(runner, "check_endpoint", check)
    monkeypatch.setattr(runner, "as_completed", collect)
    results = runner.run_checks(config)
    assert completed == ["endpoint-1", "endpoint-2", "endpoint-0"]
    assert [result.name for result in results] == [
        "endpoint-0",
        "endpoint-1",
        "endpoint-2",
    ]
    assert observed_collections == [main_id] * 3
    assert all(worker_id != main_id for worker_id in worker_threads)
    assert capsys.readouterr() == ("", "")


def test_real_mixed_outcomes_do_not_cancel_checks(server: ConcurrentServer) -> None:
    # A single worker forces good requests to run after both failed outcomes.
    config = parse_configuration(
        configuration(
            endpoint(name="failed", url=server.url + "/failed"),
            endpoint(
                name="timeout", url=server.url + "/timeout", read_timeout_seconds=0.15
            ),
            endpoint(name="good-a", url=server.url + "/good-a"),
            endpoint(name="good-b", url=server.url + "/good-b"),
            workers=1,
        )
    )
    results = runner.run_checks(config)
    assert [result.name for result in results] == [
        "failed",
        "timeout",
        "good-a",
        "good-b",
    ]
    assert [result.outcome for result in results] == [
        "failed",
        "timed out",
        "healthy",
        "healthy",
    ]
    assert [result.status_code for result in results] == [503, 200, 200, 200]
    assert len(results) == len(config.endpoints)
    assert set(server.visited) == {"/failed", "/timeout", "/good-a", "/good-b"}


def test_programming_exception_propagates_and_executor_shuts_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = settings(1, ["http://localhost/bug", "http://localhost/good"])
    finished = threading.Event()
    workers: list[threading.Thread] = []

    def check(item: EndpointSettings) -> CheckResult:
        workers.append(threading.current_thread())
        if item.name == "endpoint-0":
            raise RuntimeError("checker bug")
        finished.set()
        return healthy(item)

    monkeypatch.setattr(runner, "check_endpoint", check)
    with pytest.raises(RuntimeError, match="checker bug"):
        runner.run_checks(config)
    assert finished.is_set()
    assert all(not worker.is_alive() for worker in workers)


def test_elapsed_excludes_queue_wait(
    server: ConcurrentServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = settings(1, [server.url + "/first", server.url + "/queued"])
    release_first = threading.Event()
    first_started = threading.Event()
    real_check = checker.check_endpoint
    all_submitted = threading.Event()
    logical_clock = 0.0
    calls: list[tuple[str, float]] = []
    controller_errors: list[str] = []

    def clock() -> float:
        nonlocal logical_clock
        result = logical_clock
        logical_clock += 0.25
        return result

    def check(item: EndpointSettings) -> CheckResult:
        if item.name == "endpoint-0":
            first_started.set()
            assert release_first.wait(3)
            return healthy(item)
        calls.append((item.name, logical_clock))
        return real_check(item)

    def release() -> None:
        nonlocal logical_clock
        if not first_started.wait(3):
            controller_errors.append("first check never started")
        if not all_submitted.wait(3):
            controller_errors.append("queued check was never submitted")
        # Simulate a long queue wait; monotonic time advances before HTTP begins.
        logical_clock = 100.0
        release_first.set()

    def collect(
        futures: dict[Future[CheckResult], int],
    ) -> Iterator[Future[CheckResult]]:
        all_submitted.set()
        yield from as_completed(futures)

    monkeypatch.setattr(runner, "check_endpoint", check)
    monkeypatch.setattr(checker, "monotonic", clock)
    monkeypatch.setattr(runner, "as_completed", collect)
    controller = threading.Thread(target=release)
    controller.start()
    try:
        results = runner.run_checks(config)
    finally:
        release_first.set()
        controller.join(timeout=3)
    assert not controller.is_alive()
    assert not controller_errors
    assert calls == [("endpoint-1", 100.0)]
    assert results[1].elapsed_seconds == 0.25
    assert results[1].outcome == "healthy"
    assert server.visited == ["/queued"]
