# EndpointCheck

A small Python command-line API inspector and learning project for AI-assisted
engineering. **Milestones one through four are implemented:** strict validation,
single-endpoint GET checking, bounded orchestration, and an installed CLI with
plain-text reports and health-based exit codes. Milestone five adds Docker
packaging and a controlled demo API. Local demo tests and Compose configuration
and container builds/runs are verified for the mixed and all-healthy scenarios. See [DEMO.md](DEMO.md) for the short demonstration and cleanup sequence.

## Setup (PowerShell, from the repository root)

Tested with Python 3.14.7. Metadata requires Python >=3.14; other versions have
not been tested. Validation uses only the standard library; checking uses requests.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

The development extra installs tested pytest, Ruff, and mypy versions. Using the
environment executable avoids shell activation.

Installation also creates `.venv\Scripts\endpointcheck.exe`. With the environment
active, use `endpointcheck` directly. Reinstall after project metadata changes.

## Validate

```powershell
.\.venv\Scripts\python.exe -m endpointcheck validate examples/config.json
.\.venv\Scripts\endpointcheck.exe validate examples/config.json
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

## Check and report

```powershell
.\.venv\Scripts\endpointcheck.exe check CONFIG_PATH
.\.venv\Scripts\python.exe -m endpointcheck check CONFIG_PATH
.\.venv\Scripts\endpointcheck.exe --help
```

Both entry points were verified against controlled local HTTP configurations.
Replace `CONFIG_PATH` with your JSON file. The sample config targets localhost
port 8000; checking it requires your own API there (validation does not).

Checks validate the whole file before sending requests and print a completed
report on stdout in configuration order. Exit 0 means all healthy; exit 1 means
at least one slow/failed/timed-out result. Input/file/invocation errors use stderr
and exit 2. Unexpected programming errors remain visible.

Illustrative report; actual measured durations vary:

```text
local-health [healthy]
  URL: http://localhost:8000/health
  HTTP status: 200
  Elapsed: 0.012 s

Summary: healthy=1, slow=0, failed=0, timed out=0
```

Unavailable statuses display `unavailable`; errors are included when present.
Summary counts always include all four outcomes. Display time is rounded to
three decimals; classification uses the existing unrounded result. Names, URLs,
and errors escape nonprintable characters and literal backslashes; body content
is not printed. Reports use no color, JSON output, or new dependencies.

## Verify

These commands were run successfully in the project-local environment:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy
```

pytest manages per-run temporary directories under the system temporary location
by default, including retention and cleanup of older runs. No fixed `basetemp`
is configured. Strict mypy checks application, demo API and tests. Tests include raw
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

Reporting tests cover exact output, safe display, and rounding without changing
outcomes. Subprocess tests run the actual installed launcher and module entry
point from outside the repository root, compare behavior (excluding measured
durations), and observe zero server requests for invalid files and validation.

## Single-endpoint checker (Python API)

`endpointcheck.checker.check_endpoint(endpoint)` takes one validated
`EndpointSettings` and returns a `CheckResult` containing name, URL, outcome,
elapsed seconds, optional status, and optional error. It does not print or retry.
The checking CLI calls the existing runner; validation remains network-free.

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

## Docker demonstration

The two services use a private Compose network, with no published host ports.
Inspector uses the installed CLI and exits after reporting. Demo configurations
are `demo/mixed.json` (expected exit 1) and `demo/all-healthy.json` (expected exit
0); their URLs use `demo-api:8000`, so they are intended for Compose networking.
The API health check gates startup, without guaranteeing later availability.

Actually verified commands in this environment:

```powershell
docker --version
docker compose version
docker info
docker compose -p endpointcheck-m5-review config --quiet
.\.venv\Scripts\python.exe -m pytest tests/test_demo_api.py -s
```

The daemon was initially unavailable; subsequent runtime verification used
Docker 29.8.1, Compose 5.5.1 and Python 3.14.8 Linux containers. The build, two
mixed runs, healthy run and project-scoped container/network cleanup commands
in [DEMO.md](DEMO.md) were then verified. Actual inspector exits were 1, 1 and 0.
Readiness timestamps preceded inspector execution; service-name DNS and live
UID 10001 processes were observed. Normal package installation was confirmed
from outside the image source directory. No Docker installation or machine
settings changes were needed. Local tests independently verify endpoint behavior.

## Documentation

- [REQUIREMENTS.md](REQUIREMENTS.md): behavior and acceptance criteria.
- [ARCHITECTURE.md](ARCHITECTURE.md): implemented/planned components and tradeoffs.
- [AGENTS.md](AGENTS.md): repository working instructions.
- [AI_ENGINEERING_LOG.md](AI_ENGINEERING_LOG.md): recommendations, explicit user
  decisions, verification evidence, and limitations.

Milestone five is accepted; controlled container scenarios are verified. HTTP timeouts
do not enforce a total deadline; the small/finite-response usage limitation is
recorded in requirements. TLS/proxy behavior and unusual console encodings remain
incompletely tested.
