# EndpointCheck requirements

Status: validation, single-endpoint checking, orchestration, and checking CLI/
reports implemented. Docker packaging and the demo API are implemented;
container execution is verified for the controlled mixed and healthy scenarios.
This document is the source of truth for product behavior and acceptance
criteria. Design belongs in [ARCHITECTURE.md](ARCHITECTURE.md); repository
working instructions belong in [AGENTS.md](AGENTS.md).

## Scope

EndpointCheck is a small Python command-line API health and latency inspector.
It validates JSON configuration before making any requests and checks GET
endpoints concurrently. Version one targets small, finite API responses. This
is a usage limitation, not an enforced response-size limit.

## Configuration contract

The root object has exactly two required fields:

| Field | Required value |
| --- | --- |
| `max_workers` | Positive integer |
| `endpoints` | Nonempty list of endpoint objects |

Each endpoint has exactly these required fields:

| Field | Required value |
| --- | --- |
| `name` | Unique, nonempty string |
| `url` | HTTP or HTTPS URL with a hostname |
| `expected_status` | Integer from 100 through 599, inclusive |
| `latency_threshold_seconds` | Positive finite number |
| `connect_timeout_seconds` | Positive finite number |
| `read_timeout_seconds` | Positive finite number |

Names must contain non-whitespace characters and have no leading or trailing
whitespace. Compare uniqueness case-sensitively; internal spaces are allowed.
Do not trim or otherwise repair names.

URLs must have HTTP/HTTPS scheme and a hostname. Reject surrounding whitespace,
embedded credentials, fragments (including an empty `#`), and invalid ports.
Permit localhost and query strings. Validate syntax without DNS or network I/O.
The current syntax interpretation also rejects literal whitespace/control
characters anywhere in a URL, including characters a parser might strip. Encode
spaces in paths/query values, for example `%20`. Explicit empty ports are invalid;
numeric ports use the parser's 0–65535 range. Host existence is not validated.

Reject duplicate JSON keys at every object level and nonstandard constants
(`NaN`, `Infinity`, `-Infinity`). Read configuration files as UTF-8. Preserve
accepted values without defaults or normalization. Return settings only after
every endpoint validates; validation may stop at the first error.

## Milestone-one CLI

`python -m endpointcheck validate CONFIG_PATH` validates only; it never checks
endpoints. Relative paths resolve from the current working directory.

- Valid configuration: exit 0, short success message on stdout, empty stderr.
- Invalid configuration, unreadable file, or invocation error: exit 2,
  understandable stderr error without a traceback, and no success output.
- Standard `--help` behavior: display help and exit 0.

## Checking CLI and reporting contract

Installed commands are `endpointcheck validate CONFIG_PATH` and
`endpointcheck check CONFIG_PATH`, with equivalent `python -m endpointcheck`
subcommands. Help lists both commands. The installed launcher is generated from
the existing CLI `main` function by project metadata.

Checking validates the entire configuration before invoking the existing runner.
Completed checks are reported on stdout in configuration order. Input/file/
invocation errors go to stderr without a traceback and exit 2. Unexpected
programming exceptions remain visible, not disguised as endpoint outcomes.

- Exit 0 when every endpoint is healthy.
- Exit 1 when completed checks contain any slow, failed, or timed-out result.
- Validation retains its existing exit codes and network-free behavior.

Reports use readable plain text without color. Each endpoint displays its name,
URL, classification, received HTTP status or the literal `unavailable`, elapsed
seconds, and an error when present. Response bodies are neither retained in
results nor printed. A final summary includes counts for healthy, slow, failed,
and timed out, including zeros.

Display elapsed seconds to three decimal places with an explicit seconds unit.
Classification and exit decisions use existing outcomes computed from unrounded
time, never the displayed value. Escape embedded line breaks and terminal control
characters in names, URLs, and errors as visible backslash escapes. Escape literal
backslashes too so escaped controls are distinguishable from literal text.
Preserve ordinary printable characters. Formatting does not modify result values.

Example report layout (illustrative duration):

```text
local-health [healthy]
  URL: http://localhost:8000/health
  HTTP status: 200
  Elapsed: 0.012 s

Summary: healthy=1, slow=0, failed=0, timed out=0
```

Reject missing or unknown fields and incorrect types at either object level.
Booleans are not numbers or integers for this contract. Do not require any
ordering relationship between the threshold and either timeout.

Example valid configuration:

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

The URL illustrates configuration only; no demonstration API exists yet.

## Request and result behavior

Use separate connection and read-inactivity timeouts. Neither establishes a
total wall-clock deadline. Disable automatic redirects.

Measure elapsed time with a monotonic clock, starting immediately before the
HTTP call and ending after complete response-body consumption or when a request
exception occurs. Exclude time waiting for a thread-pool worker.

Classify in this order:

1. Connection or read timeout: **timed out**.
2. Other request failure or unexpected HTTP status: **failed**.
3. Expected status with elapsed time strictly above the threshold: **slow**.
4. Otherwise: **healthy**.

Each check result contains endpoint name and URL, outcome (`healthy`, `slow`,
`failed`, or `timed out`), elapsed seconds, received HTTP status code or `None`,
and an informative error when applicable or `None`. Slow/healthy completed
responses need no error. Unexpected statuses carry an explanatory error.

Preserve a received status even if body consumption later fails or times out.
For example, a 200 response with a stalled body is timed out with status 200;
headers alone do not establish success. Consume the complete body without
retaining it in the result. Close response/network resources on success and
failure. A checker takes one validated endpoint and returns one result without
printing, threads, retries, or shared reporting state. Unexpected programming
errors remain visible rather than becoming request failures.

Individual request failures must not cancel unrelated checks. Workers return results;
the main thread collects and reports them in configuration order.

## Numbered acceptance criteria

1. **AC-01 — Validate before requests:** Malformed JSON or any invalid endpoint
   invalidates the configuration before any HTTP request begins, including when
   other endpoints are valid.
2. **AC-02 — Exact structure:** Reject missing fields, unknown root/endpoint
   fields, a non-object root, and non-object endpoint entries. For example,
   adding `retries` to an endpoint is invalid.
3. **AC-03 — Workers and endpoint list:** Accept `max_workers: 1`; reject `0`,
   `-1`, `1.5`, `true`, and `"2"`. Reject `endpoints: []` and a non-list value.
4. **AC-04 — Names and URLs:** Reject empty or duplicate names, non-string
   names/URLs, URLs without a hostname, and non-HTTP(S) schemes. For example,
   `file:///health` is invalid.
5. **AC-05 — Expected status:** Accept 100 and 599; reject 99, 600, `200.0`,
   `true`, and `"200"`.
6. **AC-06 — Durations:** For each duration, accept positive finite integers
   and floats; reject zero, negative, non-finite, boolean, and string values.
   A threshold of 5 seconds with both timeouts at 1 second is valid.
7. **AC-07 — Request behavior:** Issue GET checks without following redirects.
   A 302 response expecting 200 is failed, and the redirect target is not checked
   automatically. Apply distinct connection and read-inactivity limits without
   claiming a total deadline.
8. **AC-08 — Timing:** Record monotonic elapsed time for successes and request
   exceptions using the boundaries above. A queued check's elapsed time excludes
   its queue wait. Full body consumption is included.
9. **AC-09 — Classification precedence:** A timeout is timed out even if the
   threshold has been exceeded. A 500 response expecting 200 is failed even if
   slow. With expected status 200 and threshold 0.5 seconds, elapsed 0.6 is slow
   and elapsed exactly 0.5 is healthy.
10. **AC-10 — Result evidence:** Each attempted check retains its elapsed time
    and relevant status/error evidence. A status mismatch retains the received
    status; a request failure retains an informative error.
    Preserve the received status after a partial-body failure/timeout; use `None`
    when no status arrived. A received 200 with incomplete body is not healthy.
11. **AC-11 — Bounded concurrency and isolation:** Active checks never exceed
    `max_workers`. One failed or timed-out request does not prevent other checks
    from completing and returning results.
12. **AC-12 — Collection and order:** Workers return results without reporting
    them. The main thread collects and reports results in configuration order,
    even if endpoint B finishes before endpoint A.
13. **AC-13 — Strict JSON:** Reject duplicate keys at root and endpoint levels,
    malformed JSON, and nonstandard constants. Raw `{"max_workers": 2,
    "max_workers": 2, "endpoints": [...]}` is invalid even when duplicate values
    agree. A numeric token `1e999` in a duration is rejected as non-finite.
14. **AC-14 — Name policy:** Reject `""`, `" "`, `" health"`, and `"health "`.
    Accept distinct names `"Health"` and `"health"`; reject identical names.
15. **AC-15 — URL policy:** Accept `http://localhost:8000/health?ready=1` without
    resolving localhost. Reject credentials, any fragment, surrounding
    whitespace, and ports such as `abc`, `-1`, `65536`, or an empty port.
16. **AC-16 — Validation CLI:** Subprocess verification must demonstrate the
    approved command, output streams and exit codes, including malformed or
    invalid configuration, nonexistent/unreadable files, and invalid invocation.
17. **AC-17 — No repair or partial acceptance:** Missing fields do not get
    defaults. A valid first endpoint followed by an invalid second endpoint
    rejects the entire configuration; no settings are returned.
18. **AC-18 — Single check and cleanup:** Given one validated endpoint, return
    the result contract above. Consume the whole body and close response/session
    resources on success or failure, without retaining body data in the result.
    Do not print, retry, start threads, or suppress unexpected programming errors.
19. **AC-19 — Timeout evidence:** Delayed headers time out with status `None`;
    received 200 headers followed by a stalled body time out with status 200.
    A refused connection is failed, not timed out. An incomplete download is
    failed with its received status. Identify actual timeout types rather than
    treating every connection failure as a timeout.
20. **AC-20 — Body timing:** Include complete body consumption in elapsed time.
    Regularly arriving data may allow a completed slow response whose total time
    exceeds the read-inactivity timeout. Verify strict threshold equality with
    a controlled monotonic clock rather than real-time equality assertions.
21. **AC-21 — Checking command and exit codes:** Both entry points support
    validation and checking. All-healthy checks exit 0; any completed nonhealthy
    outcome exits 1. Invalid input/file/invocation exits 2 on stderr. An invalid
    later endpoint causes zero requests and no report, even if earlier entries
    are valid. Programming exceptions remain visible.
22. **AC-22 — Report evidence and order:** Display each endpoint's name, URL,
    outcome, elapsed seconds, available status or `unavailable`, and applicable
    error in configuration order. A body timeout after 200 headers displays
    status 200 and the timeout error. Do not print response bodies.
23. **AC-23 — Summary and precision:** Always include all four counts, including
    zeros. A slow result just above a 0.5-second threshold remains slow and exits
    1 even when displayed as `0.500 s`.
24. **AC-24 — Safe display:** Names/errors containing newline, carriage return,
    tab, escape, C1 controls, or other nonprintable characters display visible
    escapes rather than injecting lines or terminal actions. Apply the same
    escaping to URLs; do not change underlying values or outcomes.
25. **AC-25 — Installed entry point:** Reinstall the project to create its actual
    launcher and test it alongside module invocation for command/help/errors and
    real checking. Equivalent reports retain the same structural evidence, but
    independently measured HTTP durations need not match exactly.

26. **AC-26 — Controlled demonstration:** A concurrent API exposes `/ready` and
    `/healthy` with prompt 200 finite bodies; `/slow` returns 200 after 0.6 seconds;
    `/error` promptly returns 500; `/timeout` flushes 200 headers immediately and
    waits one second before delivering its body. Expected client disconnects
    must not produce noisy server tracebacks.
27. **AC-27 — Mixed demonstration:** Four workers check healthy, slow, error,
    timeout in that configuration order, expecting 200. Slow uses threshold 0.2
    seconds and read timeout 2 seconds; timeout uses read timeout 0.3 seconds.
    Healthy/error thresholds are generous. The report shows healthy, slow, failed,
    timed out, one of each; timeout retains status 200 and the inspector exits 1.
    Repeat the mixed run; an all-healthy configuration exits 0.
28. **AC-28 — Container lifecycle:** Two Compose services, `demo-api` and
    `inspector`, communicate at `http://demo-api:8000`. A dedicated readiness
    health check gates inspector startup. Readiness is a startup observation,
    not a guarantee of later availability. The installed inspector CLI reports
    and exits. No host ports are published by default.
29. **AC-29 — Packaging and verification:** Both container processes run as
    non-root users on a Python version compatible with metadata. Install the
    inspector normally, without editable installation or host virtualenv usage.
    Exclude unnecessary files and local secrets from build context. Validate
    Compose and verify real builds, networking, readiness and inspector exit
    codes when Docker is available; explicitly report unverified execution when
    unavailable. Cleanup is limited to this project's demonstration resources.

## Decisions still pending

- Whether future URL validation needs stricter hostname/percent-escape rules
  beyond the current structural parser checks; no DNS validation is intended.

Resolve these here before implementing dependent behavior. Do not infer approval
from an architecture recommendation.
