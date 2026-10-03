# Proposed architecture

Status: four-component design accepted; configuration and validation CLI implemented.
Product behavior and acceptance criteria are defined in
[REQUIREMENTS.md](REQUIREMENTS.md). This document describes design choices, not
additional product rules.

## Components and data flow

| Proposed module | Responsibility |
| --- | --- |
| `config.py` (implemented) | Load strict JSON, validate the complete configuration, and produce immutable typed settings. |
| `checker.py` (planned) | Perform one GET, measure elapsed time, classify it, and return a result. |
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

Simple dataclasses are recommended for future result records.
The result should carry endpoint identity, classification, elapsed seconds,
and relevant HTTP status/error evidence. Exact fields remain to be reviewed.

Use `ThreadPoolExecutor` with the configured worker count. Associate each future
with its input position so results can be collected independently of completion
order and reported in configuration order. Workers should not print or mutate a
shared report. Expected request exceptions become results inside the checker;
handling unexpected programming errors remains a design detail to review.

## Dependencies and tradeoffs

- Standard library: JSON parsing, dataclasses, CLI parsing, monotonic timing,
  and bounded thread pooling.
- Recommended runtime dependency: `requests`, for straightforward synchronous
  HTTP calls and request exceptions.
- Implemented development tools: `pytest` for tests, Ruff for lint/format checks,
  and mypy in strict mode for application and test typing.

Milestone one has no runtime dependencies. The user explicitly requested the
three development tools, installed in `.venv`; their tested versions are pinned
in `pyproject.toml`. Transitive development dependencies are not locked.
Python 3.14.7 was the available installation discovered via PATH and the local
Python installation directory (the `py` launcher was unavailable). Python 3.14
is supported according to [Python's version status](https://devguide.python.org/versions/).
Metadata requires Python >=3.14; only 3.14.7 has been tested. This avoids claiming
older-version compatibility without verification. The HTTP dependency remains
a recommendation and is not installed.

Synchronous workers keep this learning project small and understandable.
An async framework and additional configuration frameworks are unnecessary for
the proposed initial design.

## HTTP and timing implementation considerations

Apply separate connection and read-inactivity timeout values; disable redirects.
Place monotonic measurements directly around the HTTP operation and complete
body consumption, including its request-exception path (AC-07 through AC-10).
Verify how the chosen HTTP library surfaces timeouts during body consumption
before mapping exceptions to classifications.

A read-inactivity timeout can allow a response to continue while data keeps
arriving. Connection handling may also have timing outside a simple timeout
interpretation. Do not claim a total wall-clock deadline. Waiting on a future
with a timeout does not stop its underlying running request.

Full-body consumption makes timing easy to explain but may consume substantial
time or memory for large responses. The requirements document records the small,
finite-response usage limitation; there is no enforced response-size cap.

## Reviewable milestones and planned verification

| Milestone | Scope | Independent verification planned |
| --- | --- | --- |
| 1. Configuration validation and a minimal validation CLI | Validate JSON and expose validation through the CLI. | Valid/invalid input matrix, boundary cases, subprocess invocation, and evidence that validation makes zero requests. |
| 2. Single-endpoint checking | GET, timing, classifications, result evidence. | Controlled local server for statuses, redirect targets, delayed body, disconnect, and read timeout; controlled connection-timeout test; injected clock values for exact threshold boundaries. |
| 3. Bounded concurrent orchestration | Worker limit, collection, isolation, ordered results. | Independent server-side concurrency counters, deliberately reversed completion order, and mixed success/failure/timeout checks. |
| 4. Complete CLI reporting | Approved output contract and exit codes. | Subprocess checks against independently specified expected output and exit codes. |
| 5. Docker and a controlled demonstration API | Container execution and repeatable demonstration scenarios. | Approved scenarios through container networking, including readiness and inspector process outcomes. |

Milestone-one verification is recorded in the engineering log; milestones 2–5
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
