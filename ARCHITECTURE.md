# Proposed architecture

Status: configuration, validation CLI, and single-endpoint checking implemented.
Product behavior and acceptance criteria are defined in
[REQUIREMENTS.md](REQUIREMENTS.md). This document describes design choices, not
additional product rules.

## Components and data flow

| Proposed module | Responsibility |
| --- | --- |
| `config.py` (implemented) | Load strict JSON, validate the complete configuration, and produce immutable typed settings. |
| `checker.py` (implemented) | Perform one GET, consume the body, measure elapsed time, and return status/error evidence and outcome. |
| `runner.py` (planned) | Submit checks to a bounded thread pool and collect results on the main thread. |
| `cli.py` (validation implemented) | Validate a configuration; checking/reporting remain planned. |

Flow: CLI → complete configuration validation → runner → checker workers →
main-thread collection → CLI report. Milestone 1 stops after validation.

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

Use `ThreadPoolExecutor` with the configured worker count. Associate each future
with its input position so results can be collected independently of completion
order and reported in configuration order. Workers should not print or mutate a
shared report. Expected request exceptions become results inside the checker;
Unexpected programming errors propagate. The runner itself is not implemented.

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

Milestone-one and milestone-two verification is recorded in the engineering log; milestones 3–5
remain pending. Real timing tests should use generous
margins; exact threshold equality should use controlled clock inputs. Avoid
unreliable public endpoints or assumptions that an unreachable address will
consistently trigger a connection timeout.

The validator imports file/JSON/type utilities and a URL syntax parser, with no
HTTP client, socket invocation, DNS lookup, or request execution path. A test
guards socket construction and common DNS functions while loading a valid
configuration with a nonexistent hostname. That guard covers exercised paths,
not every possible network mechanism or future change; source review supplies
additional evidence. Passing checks are not proof of correctness.

Working instructions live in [AGENTS.md](AGENTS.md); recommendations, decisions,
and evidence are tracked in [AI_ENGINEERING_LOG.md](AI_ENGINEERING_LOG.md).
