# EndpointCheck requirements

Status: agreed behavior documented; implementation has not started.
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

Preserve elapsed time and relevant HTTP status codes or errors. Individual
request failures must not cancel unrelated checks. Workers return results;
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
11. **AC-11 — Bounded concurrency and isolation:** Active checks never exceed
    `max_workers`. One failed or timed-out request does not prevent other checks
    from completing and returning results.
12. **AC-12 — Collection and order:** Workers return results without reporting
    them. The main thread collects and reports results in configuration order,
    even if endpoint B finishes before endpoint A.

## Decisions still pending

- CLI syntax, configuration path handling, output format, summaries, and exit
  codes. The validation-only CLI must not issue HTTP requests.
- Whether whitespace-only names are valid; whether names are trimmed or compared
  case-sensitively for uniqueness.
- URL edge cases: credentials, fragments, malformed ports, and surrounding
  whitespace; define the intended validation boundary.
- Handling duplicate JSON object keys and nonstandard JSON constants such as
  `NaN` and `Infinity` throughout the input.
- Which evidence to retain when an exception occurs after response headers
  arrive, and how errors are represented in results and reports.
- Docker/demo scenarios, startup/readiness behavior, and acceptance criteria.

Resolve these here before implementing dependent behavior. Do not infer approval
from an architecture recommendation.
