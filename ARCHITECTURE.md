# Proposed architecture

Status: configuration, validation CLI, single-endpoint checking, and bounded
orchestration implemented, with checking CLI and reports. Docker packaging and
the demo API are implemented; the controlled container scenarios are verified.
Product behavior and acceptance criteria are defined in
[REQUIREMENTS.md](REQUIREMENTS.md). This document describes design choices, not
additional product rules.

## Components and data flow

| Proposed module | Responsibility |
| --- | --- |
| `config.py` (implemented) | Load strict JSON, validate the complete configuration, and produce immutable typed settings. |
| `checker.py` (implemented) | Perform one GET, consume the body, measure elapsed time, and return status/error evidence and outcome. |
| `runner.py` (implemented) | Submit all checks to a bounded thread pool, collect completed futures on the caller thread, and return configuration-order results. |
| `cli.py` (implemented) | Parse validation/check commands, load configuration first, invoke the runner, print completed reports, and return approved exit codes. |
| `reporting.py` (implemented helper) | Pure plain-text formatting and safe display of untrusted fields. |

Flow: CLI → complete configuration validation → runner → checker workers →
main-thread collection → CLI report. Milestone 1 stops after validation.

Both module invocation and the installed `endpointcheck` console script call
`cli.main`. Project metadata's script entry creates the launcher on installation;
it was recreated and tested in `.venv`. `validate` returns before calling the
runner. `check` loads the entire file first, then calls the existing runner on
the main thread, formats its ordered results, and chooses exit 0/1 from existing
outcomes. Configuration/file errors alone are caught as user errors (exit 2);
argparse handles invocation errors. Programming exceptions are not caught.

`reporting.format_report` accepts a sequence of results and returns text without
printing or mutation. It preserves sequence order, formats elapsed seconds to
three decimals, renders missing status as `unavailable`, includes applicable
errors, and emits all four summary counts. Classification is never recomputed
from rounded text. `safe_display` uses printable-character checks and Python
backslash escapes for controls, nonprintable Unicode characters, and literal
backslashes. Ordinary printable Unicode remains readable. Expected input errors
and argparse error messages use the same escaping; help uses a fixed program name.
This helper keeps formatting concerns out of workers and the runner.

Frozen dataclasses and an endpoint tuple hold validated configuration. The parser
uses JSON hooks to reject duplicate keys/constants before field validation;
small helpers check structure, integers, durations, names, and URLs. It returns
only after all endpoints validate, but reports the first error rather than
aggregating errors. `urllib.parse.urlsplit` is a syntax parser, not a network
client or comprehensive RFC validator. See the requirements for its validation
boundary. File-read/parse/validation errors become `ConfigurationError`; the CLI
handles that error, and argparse handles invocation errors.

`checker.CheckResult` is a frozen dataclass with name, URL, literal outcome,
elapsed seconds, optional status code, and optional error string, as specified
in requirements. `check_endpoint` accepts one validated `EndpointSettings`.

`runner.run_checks(settings)` accepts validated `Settings` and returns a list of
`CheckResult` objects. It submits one future per endpoint to `ThreadPoolExecutor`
with `max_workers`, associating each future with its configuration position.
`as_completed` yields finished futures for collection; a position-indexed local
dictionary restores order on return. Available workers start queued jobs without
waiting for the collector or an earlier endpoint. Workers only return results;
the runner prints nothing and owns no shared reporting state.

Collection runs synchronously on the calling thread; the intended application
caller is the main thread. The API does not enforce which thread invokes it.
Failed/timed-out results are ordinary values and do not cancel other futures.
Unexpected programming exceptions propagate from `future.result()`; the runner
does not invent failure results or promise a complete result list in that case.
The executor context waits for shutdown, including running/queued checks, before
an exception leaves the function. It does not forcibly cancel threads or add a
total deadline; a continually producing response can keep shutdown waiting.

Submitting all endpoints keeps the runner small. The worker count bounds active
checks, not the number of queued futures; submission/storage use O(endpoint count)
memory. No load balancer, retry policy, or report formatting is introduced.

## Dependencies and tradeoffs

- Standard library: JSON parsing, dataclasses, CLI parsing, monotonic timing,
  and bounded thread pooling.
- Runtime dependency: `requests` 2.34.2, for synchronous HTTP and request errors.
- Explicit runtime dependency: `urllib3` 2.8.0 (also used by requests), because
  streamed-timeout recognition imports its `ReadTimeoutError` type directly.
- Implemented development tools: `pytest` for tests, Ruff for lint/format checks,
  and mypy in strict mode for application and test typing.

Validation still has no network path and uses only the standard library; the
checker imports HTTP dependencies separately. The user explicitly requested the
three development tools, installed in `.venv`; their tested versions are pinned
in `pyproject.toml`. Added pinned `types-requests` stubs for strict mypy; installed
library source and real-network tests verify behavior beyond the stubs.
Remaining transitive dependencies are not locked.
Python 3.14.7 was the available installation discovered via PATH and the local
Python installation directory (the `py` launcher was unavailable). Python 3.14
is supported according to [Python's version status](https://devguide.python.org/versions/).
Metadata requires Python >=3.14; only 3.14.7 has been tested. This avoids claiming
older-version compatibility without verification.

Synchronous workers keep this learning project small and understandable.
An async framework and additional configuration frameworks are unnecessary for
the proposed initial design.

## HTTP and timing implementation considerations

Create a per-check Session (default adapter has zero retries). Start the
monotonic clock immediately before `Session.get`, passing a separate timeout
tuple, `stream=True`, and `allow_redirects=False`. A local response hook captures
headers and consumes/discards body chunks of up to 64 KiB. It records end time
at completion; request exceptions record end time on arrival. Response cleanup
and session cleanup occur after timing, via `finally` and a context manager.

The hook is necessary because requests prepares `Response.next` even when
redirects are disabled: that path can consume a redirect body and handle some
body errors internally. Reading in the hook preserves the status and exposes
download failures before that preparation; no redirect target is requested.
The hook has only per-call state and does not retain the body in the result.

Catch only `requests.RequestException`. Recognize `requests.Timeout` directly;
also recognize `ConnectionError` whose arguments contain the typed urllib3
`ReadTimeoutError`. Installed `Response.iter_content` source converts that read
timeout to `ConnectionError`; controlled tests independently observe the shape.
Other connection errors (including refusal) remain failed, without message-text
matching. See [requests source](https://requests.readthedocs.io/en/latest/_modules/requests/models/).

Default requests environment/proxy, certificate verification, and decompression
behavior are retained. Tests isolate loopback traffic with `NO_PROXY`; TLS,
proxy, and internet behavior are not verified here. No total deadline is added.

A read-inactivity timeout can allow a response to continue while data keeps
arriving. Connection handling may also have timing outside a simple timeout
interpretation. Do not claim a total wall-clock deadline. Waiting on a future
with a timeout does not stop its underlying running request.

Body streaming avoids intentionally retaining the full body, but has no size
or total duration cap. The requirements document records the small,
finite-response usage limitation; there is no enforced response-size cap.

## Reviewable milestones and planned verification

| Milestone | Scope | Independent verification planned |
| --- | --- | --- |
| 1. Configuration validation and a minimal validation CLI | Validate JSON and expose validation through the CLI. | Valid/invalid input matrix, boundary cases, subprocess invocation, and evidence that validation makes zero requests. |
| 2. Single-endpoint checking | GET, timing, classifications, result evidence. | Controlled local server for statuses, redirect targets, delayed body, disconnect, and read timeout; controlled connection-timeout test; injected clock values for exact threshold boundaries. |
| 3. Bounded concurrent orchestration | Worker limit, collection, isolation, ordered results. | Independent server-side concurrency counters, deliberately reversed completion order, and mixed success/failure/timeout checks. |
| 4. Complete CLI reporting | Approved output contract and exit codes. | Subprocess checks against independently specified expected output and exit codes. |
| 5. Docker and a controlled demonstration API | Container execution and repeatable demonstration scenarios. | Approved scenarios through container networking, including readiness and inspector process outcomes. |

Milestones one through three have verification recorded in the engineering log;
milestone four adds installed/module subprocess verification and formatting tests;
milestone five adds packaging and local demo tests, with container execution
verified on Docker Desktop Linux containers. Real timing tests should use generous
margins; exact threshold equality should use controlled clock inputs. Avoid
unreliable public endpoints or assumptions that an unreachable address will
consistently trigger a connection timeout.

Milestone-three tests combine simulated checks with a concurrent local HTTP
server. Lock-protected simulated counters/barriers observe whole worker-call
overlap and limits; events force queued work to start before an earlier check
finishes. Completion records and returned names independently establish order.
A collection iterator spy records main-thread collection and worker identities.

The real server records active handlers and maximum overlap under a lock, with
final-byte delivery/decrement serialized against new handler counting to avoid
tail-bookkeeping inflation. These counters observe server-side request handling,
not DNS, TCP connection setup, client cleanup, or every client activity stage.
Separate tests show one-worker sequencing, actual multiworker overlap, and
healthy checks after failed/timed-out results. A queued real HTTP check uses a
controlled monotonic clock advanced while its worker is occupied, proving its
elapsed value begins at HTTP execution rather than submission. This is a
deterministic boundary check, not a real-world queue-latency benchmark.
Fixture waits are bounded; shutdown signals handlers, joins non-daemon handler
threads, and asserts the server thread ended. Passing tests are evidence, not
exhaustive scheduling or network correctness.

Milestone-four subprocess tests invoke both entry points from a temporary working
directory against a controlled loopback server. They observe exit codes, streams,
order, evidence, counts, zero requests after input rejection (including a later
invalid endpoint), and network-free validation. They also verify status retention
for stalled/incomplete bodies, unavailable status, and safe name display.
Synthetic results test exact errors/URL control escaping and rounded display
without outcome changes. Entry-point comparison ignores real measured durations.
Server observations cover received HTTP requests, not an exhaustive network audit.
Fixtures reuse the bounded single-endpoint test server and join its thread.

The validator imports file/JSON/type utilities and a URL syntax parser, with no
HTTP client, socket invocation, DNS lookup, or request execution path. A test
guards socket construction and common DNS functions while loading a valid
configuration with a nonexistent hostname. That guard covers exercised paths,
not every possible network mechanism or future change; source review supplies
additional evidence. Passing checks are not proof of correctness.

Working instructions live in [AGENTS.md](AGENTS.md); recommendations, decisions,
and evidence are tracked in [AI_ENGINEERING_LOG.md](AI_ENGINEERING_LOG.md).

## Milestone-five packaging and demonstration

`demo_api/server.py` is separate from the installed inspector package. Its
standard-library `ThreadingHTTPServer` handles simultaneous requests; `/ready`
is independent of the controlled endpoint delays specified in requirements.
Response lengths are explicit and finite. `/timeout` flushes headers before its
body delay; expected broken-pipe/reset/aborted disconnects are handled quietly.
Other errors remain visible. This is a small demonstration server, not a
hardened production service or a concurrency/load-testing tool.

One Dockerfile has `demo-api` and `inspector` targets sharing Python 3.14 slim
(compatible with metadata). The moving image tag accepts upstream patch updates;
it is not digest-pinned and reproducible builds are not promised. The inspector
uses a normal `pip install .` and the existing launcher. Only inspector package
files are installed; demo code is copied into the separate demo image. Both
processes run as UID/GID 10001. The allowlist `.dockerignore` restricts context
to build metadata, Python sources and the two demo configurations.

Compose creates two services and their private default network without published
ports. Inspector addresses `http://demo-api:8000`; health checks inside demo-api
use loopback `/ready`. `depends_on: service_healthy` gates startup, not continued
availability. Inspector has no restart policy and exits after its report. The
all-healthy scenario overrides only the CLI configuration argument.

Tests observe real headers before stalled body delivery, completed delays and
local subprocess exit codes. A controlled delay plus events holds two handlers
open while readiness completes, independently demonstrating overlap without
fragile scheduling assertions. These observations cover HTTP handlers rather
than every client activity stage. Fixture waits and client sockets are bounded;
non-daemon handler threads are joined on teardown. Compose syntax is validated;
image builds, normal installation, live UID 10001 processes, service DNS and
startup ordering were subsequently verified on Docker 29.8.1 / Compose 5.5.1
with Python 3.14.8 containers. Health-check completion timestamps precede
inspector start, and mixed/healthy actual exits were 1/0. Compose stops the API
after mixed completion; observed API exit 137 is separate from inspector exit.
Graceful SIGTERM handling is not implemented in this controlled server.
Operational steps are in [DEMO.md](DEMO.md).
