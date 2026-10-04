# EndpointCheck

A small Python command-line API inspector and learning project for AI-assisted
engineering. **Milestones one through three are implemented:** strict JSON
validation, immutable settings, a validation-only CLI, single-endpoint GET
checking, and bounded concurrent orchestration. A checking CLI, report formatting,
and Docker are not implemented.

## Setup (PowerShell, from the repository root)

Tested with Python 3.14.7. Metadata requires Python >=3.14; other versions have
not been tested. Validation uses only the standard library; checking uses requests.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

The development extra installs tested pytest, Ruff, and mypy versions. Using the
environment executable avoids shell activation.

## Validate

```powershell
.\.venv\Scripts\python.exe -m endpointcheck validate examples/config.json
```

Expected output: `Configuration valid: 1 endpoint(s).` Exit 0 means valid.
Expected configuration/file/invocation errors print to stderr without a traceback
and exit 2. Paths resolve from the current working directory; quote paths with
spaces. With the environment active, use
`python -m endpointcheck validate CONFIG_PATH`.

Validation reads a UTF-8 file and checks every endpoint before returning settings.
It does not resolve hostnames or contact endpoints. The sample localhost URL
requires no running server. See [REQUIREMENTS.md](REQUIREMENTS.md) for the exact
schema, examples, and acceptance criteria.

## Verify

These commands were run successfully in the project-local environment:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy
```

pytest temporary files live under ignored `.pytest_cache/tmp`, which pytest owns
and clears on a run. Strict mypy checks application and tests. Tests include raw
duplicate-key JSON, field boundaries, whole-config rejection, subprocess CLI
behavior, and guarded socket/DNS calls. Checks provide evidence, not proof of
correctness or an exhaustive network audit.

Checker tests use a controlled loopback server with clean fixture shutdown:
statuses, redirects, delayed headers/body, incomplete downloads, refusal, and
regularly arriving data. Connection timeout is simulated; exact latency equality
uses a controlled clock. No public endpoint is needed.

Runner tests also use a concurrent local server with lock-protected handler
counters, plus simulated checks and synchronization events for worker limits,
overlap, ordering, failure isolation, and queue-time exclusion. Server counters
observe request handlers rather than all client activity stages.

## Single-endpoint checker (Python API)

`endpointcheck.checker.check_endpoint(endpoint)` takes one validated
`EndpointSettings` and returns a `CheckResult` containing name, URL, outcome,
elapsed seconds, optional status, and optional error. It does not print or retry.
The existing validation CLI remains unchanged; there is no checking command yet.

The checker streams the complete body and closes response/session resources,
including after a body error. A received status is preserved even when body
consumption fails. Separate connection/read-inactivity timeouts are not a total
deadline: regularly arriving data can finish slowly without a read timeout.
Elapsed time includes the whole body, using a monotonic clock. Small finite API
responses remain the intended use, without an enforced size/duration cap.

## Concurrent runner (Python API)

`endpointcheck.runner.run_checks(settings)` accepts validated `Settings`, submits
all endpoints using `max_workers`, and returns one result per endpoint in
configuration order for ordinary request outcomes. Workers start queued checks
as capacity becomes available. Collection stays on the calling thread (normally
the main thread); the runner does not print or format reports.

Failed/timed-out results do not cancel other checks. Programming exceptions
remain visible; executor shutdown may wait for running and queued checks before
they propagate. There is no total deadline or forced thread cancellation.
All endpoints are submitted at once, so queued-future memory grows with endpoint
count. The validation CLI still performs no HTTP checks.

## Documentation and remaining milestones

- [REQUIREMENTS.md](REQUIREMENTS.md): behavior and acceptance criteria.
- [ARCHITECTURE.md](ARCHITECTURE.md): implemented/planned components and tradeoffs.
- [AGENTS.md](AGENTS.md): repository working instructions.
- [AI_ENGINEERING_LOG.md](AI_ENGINEERING_LOG.md): recommendations, explicit user
  decisions, verification evidence, and limitations.

Remaining, separately authorized milestones: complete CLI reporting; Docker and a controlled
demonstration API. Future HTTP timeouts will not enforce a total deadline; the
small/finite-response usage limitation is recorded in requirements.
