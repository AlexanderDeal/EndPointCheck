"""Synchronous single-endpoint GET checking; no reporting or orchestration."""

from dataclasses import dataclass
from time import monotonic
from typing import Literal

import requests
from urllib3.exceptions import ReadTimeoutError

from endpointcheck.config import EndpointSettings

Outcome = Literal["healthy", "slow", "failed", "timed out"]


@dataclass(frozen=True)
class CheckResult:
    name: str
    url: str
    outcome: Outcome
    elapsed_seconds: float
    status_code: int | None
    error: str | None


def _is_timeout(error: requests.RequestException) -> bool:
    if isinstance(error, requests.Timeout):
        return True
    # requests.iter_content wraps urllib3's read timeout in ConnectionError.
    # Match its typed payload, not message text or all connection failures.
    return isinstance(error, requests.ConnectionError) and any(
        isinstance(argument, ReadTimeoutError) for argument in error.args
    )


def check_endpoint(endpoint: EndpointSettings) -> CheckResult:
    """Check one validated endpoint, preserving headers even on body failure."""
    response: requests.Response | None = None
    status: int | None = None
    error_message: str | None = None
    elapsed = 0.0
    outcome: Outcome

    def consume_response(received: requests.Response, **kwargs: object) -> None:
        nonlocal response, status, elapsed
        # Capture before Session.get returns: requests can consume redirect bodies
        # while preparing Response.next even with allow_redirects=False.
        response = received
        status = received.status_code
        # Consume here so redirect preparation cannot hide a body failure.
        for _chunk in received.iter_content(chunk_size=64 * 1024):
            pass
        elapsed = monotonic() - start

    with requests.Session() as session:
        start = monotonic()
        try:
            session.get(
                endpoint.url,
                timeout=(
                    endpoint.connect_timeout_seconds,
                    endpoint.read_timeout_seconds,
                ),
                allow_redirects=False,
                stream=True,
                hooks={"response": consume_response},
            )
        except requests.RequestException as error:
            elapsed = monotonic() - start
            outcome = "timed out" if _is_timeout(error) else "failed"
            error_message = f"{type(error).__name__}: {error}"
        else:
            if status != endpoint.expected_status:
                outcome = "failed"
                error_message = (
                    f"Expected HTTP {endpoint.expected_status}, received HTTP {status}"
                )
            elif elapsed > endpoint.latency_threshold_seconds:
                outcome = "slow"
            else:
                outcome = "healthy"
        finally:
            if response is not None:
                response.close()

    return CheckResult(
        endpoint.name, endpoint.url, outcome, elapsed, status, error_message
    )
