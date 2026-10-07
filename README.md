# EndpointCheck

EndpointCheck is a Python command-line tool for checking API health and request
latency. It helps developers inspect a list of GET endpoints, identify unexpected
statuses and slow responses, and use the result in scripts through exit codes.

It validates configuration before making requests, checks endpoints with a bounded
thread pool, and reports healthy, slow, failed or timed-out results in configuration
order. Individual request failures do not cancel unrelated checks.

## Prerequisites and installation

Requires Python 3.14+. Verified environments used Python 3.14.7 locally and
3.14.8 in containers. Git is required for cloning. Docker is optional and requires
Compose with a running Linux-container daemon. Local instructions use Windows
PowerShell; container execution uses Linux.

Clone the repository and enter it; skip this step if you already have a checkout:

```powershell
git clone https://github.com/AlexanderDeal/EndPointCheck.git
cd EndPointCheck
```

From the repository root, create a project-local environment and install the tool
and development checks:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

This creates `.venv\Scripts\endpointcheck.exe` and installs pytest, Ruff and mypy.
The explicit executable paths avoid shell activation. With the environment active,
use `endpointcheck` directly. Checking uses requests; configuration validation
uses the standard library and performs no DNS lookups or network requests.

## Configuration

Use a UTF-8 JSON file. For example:

```json
{
  "max_workers": 2,
  "endpoints": [
    {
      "name": "local-health",
      "url": "http://localhost:8000/health",
      "expected_status": 200,
      "latency_threshold_seconds": 0.5,
      "connect_timeout_seconds": 1.0,
      "read_timeout_seconds": 2.0
    }
  ]
}
```

`max_workers` must be a positive integer, and `endpoints` must be nonempty. Each
endpoint requires every field shown. Names must be unique (case-sensitive),
nonblank and free of leading/trailing whitespace. URLs require HTTP/HTTPS and a
hostname; credentials, fragments, whitespace and invalid ports are rejected.
Expected statuses range from 100 through 599; timing values must be positive and
finite. Booleans are not accepted as numbers.

Missing/unknown fields, duplicate JSON keys and nonstandard constants are rejected.
Values are not repaired or given defaults. The threshold may exceed either timeout.
See [REQUIREMENTS.md](REQUIREMENTS.md) for the full contract.

[examples/config.json](examples/config.json) is ready to validate. Checking its
localhost URL requires your own API on port 8000; validation requires no server.

## Validate and check

For a self-contained demonstration that requires no existing API, follow the
Docker quick start in [DEMO.md](DEMO.md).

```powershell
.\.venv\Scripts\endpointcheck.exe validate examples/config.json
.\.venv\Scripts\endpointcheck.exe check examples/config.json
.\.venv\Scripts\endpointcheck.exe --help
```

Validation prints `Configuration valid: 1 endpoint(s).` for this example.
Equivalent module commands are:

```powershell
.\.venv\Scripts\python.exe -m endpointcheck validate examples/config.json
.\.venv\Scripts\python.exe -m endpointcheck check examples/config.json
```

Replace the path with your configuration. Relative paths resolve from the current
working directory; quote paths containing spaces. Checks validate the entire file
before sending requests. Redirects are not followed.

Example report (illustrative elapsed time):

```text
local-health [healthy]
  URL: http://localhost:8000/health
  HTTP status: 200
  Elapsed: 0.012 s

Summary: healthy=1, slow=0, failed=0, timed out=0
```

Reports go to stdout. They include errors when present and show `unavailable` when
no HTTP status arrived. A received status is preserved after a body failure or
timeout. Bodies are not printed. Control characters are escaped.

Elapsed time is measured with a monotonic clock and includes complete body
consumption or time until a request error. Worker queue time is excluded.
Display rounding to three decimals does not change classification.

| Exit | Meaning |
| --- | --- |
| 0 | Configuration valid (`validate`), or all endpoints healthy (`check`). |
| 1 | Completed checks include a slow, failed or timed-out result. |
| 2 | Configuration, file or invocation error; error is written to stderr. |

Unexpected programming exceptions remain visible.

## Docker demonstration

See [DEMO.md](DEMO.md) for build, mixed/healthy runs, exit-code inspection and
project-scoped cleanup commands. The mixed demo exits 1 with one of each outcome;
the all-healthy demo exits 0.

The demo runs Linux containers separately from the local Windows environment.
Inspector uses the installed CLI and exits after reporting. Both processes run as
UID 10001. API URLs use `http://demo-api:8000` on the Compose network; localhost
inside inspector would refer to inspector itself. No host ports are published.
A dedicated health check gates startup, without guaranteeing later availability.

## Development checks

Run from the repository root after installing the development extra:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy
```

HTTP tests use controlled local servers and require temporary-file access and
loopback socket binding/connections. No public API is needed. Mypy checks the
inspector, demo API and tests in strict mode.

## Limitations

- There is no total wall-clock deadline or response-size cap. Checks target small,
  finite responses; connection/read-inactivity timeouts do not bound total duration.
  Regularly arriving data can keep a response running beyond either timeout.
- No retries or forced thread cancellation. Shutdown may wait for running/queued
  checks; queued-task memory grows with endpoint count.
- TLS/proxy behavior and unusual console encodings are not comprehensively tested.
- URL syntax checks do not establish that a host exists. Display escaping does
  not redact query data or errors.
- The demo API lacks graceful SIGTERM handling and may exit 137 when Compose stops
  it. This is separate from inspector health exit codes.
- Image tags and transitive dependencies are not fully locked; identical rebuilds
  are not guaranteed.

## Supporting documentation

- [REQUIREMENTS.md](REQUIREMENTS.md): behavior and acceptance criteria.
- [ARCHITECTURE.md](ARCHITECTURE.md): components, Python APIs and design tradeoffs.
- [DEMO.md](DEMO.md): controlled Docker demonstration.
- [AGENTS.md](AGENTS.md): repository working instructions.
- [AI_ENGINEERING_LOG.md](AI_ENGINEERING_LOG.md): development history, decisions,
  verification evidence and limitations.
