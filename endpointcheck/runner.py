"""Bounded checking with caller-thread collection in configuration order."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from endpointcheck.checker import CheckResult, check_endpoint
from endpointcheck.config import Settings


def run_checks(settings: Settings) -> list[CheckResult]:
    """Run validated settings; programming errors propagate after executor cleanup.

    Shutdown waits for running checks. There is no total deadline or forced
    thread cancellation.
    """
    with ThreadPoolExecutor(max_workers=settings.max_workers) as executor:
        positions = {
            executor.submit(check_endpoint, endpoint): index
            for index, endpoint in enumerate(settings.endpoints)
        }
        collected = {
            positions[future]: future.result() for future in as_completed(positions)
        }
    return [collected[index] for index in range(len(settings.endpoints))]
