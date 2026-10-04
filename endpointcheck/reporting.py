"""Plain-text formatting of completed results, without changing classifications."""

from collections.abc import Sequence

from endpointcheck.checker import CheckResult, Outcome


def safe_display(value: str) -> str:
    """Render controls/nonprintable characters and backslashes as visible escapes."""
    return "".join(
        character
        if character.isprintable() and character != "\\"
        else character.encode("unicode_escape").decode("ascii")
        for character in value
    )


def format_report(results: Sequence[CheckResult]) -> str:
    counts: dict[Outcome, int] = {"healthy": 0, "slow": 0, "failed": 0, "timed out": 0}
    lines: list[str] = []
    for result in results:
        counts[result.outcome] += 1
        status = (
            str(result.status_code) if result.status_code is not None else "unavailable"
        )
        lines.extend(
            [
                f"{safe_display(result.name)} [{result.outcome}]",
                f"  URL: {safe_display(result.url)}",
                f"  HTTP status: {status}",
                f"  Elapsed: {result.elapsed_seconds:.3f} s",
            ]
        )
        if result.error is not None:
            lines.append(f"  Error: {safe_display(result.error)}")
        lines.append("")
    lines.append(
        "Summary: "
        + ", ".join(f"{outcome}={count}" for outcome, count in counts.items())
    )
    return "\n".join(lines)
