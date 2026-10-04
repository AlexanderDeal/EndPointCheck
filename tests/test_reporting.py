from pathlib import Path

import pytest
from test_config import configuration, endpoint

import endpointcheck.cli as cli
from endpointcheck.checker import CheckResult
from endpointcheck.config import Settings
from endpointcheck.reporting import format_report, safe_display


def test_report_exact_evidence_counts_and_unrounded_classification() -> None:
    results = [
        CheckResult("ready", "http://localhost/ready", "healthy", 0.1, 200, None),
        CheckResult("slower", "http://localhost/slow", "slow", 0.50001, 200, None),
        CheckResult(
            "down", "http://localhost/down", "failed", 0.2, None, "connection refused"
        ),
        CheckResult(
            "body", "http://localhost/body", "timed out", 0.3, 200, "body stalled"
        ),
    ]
    assert format_report(results) == (
        "ready [healthy]\n"
        "  URL: http://localhost/ready\n"
        "  HTTP status: 200\n"
        "  Elapsed: 0.100 s\n\n"
        "slower [slow]\n"
        "  URL: http://localhost/slow\n"
        "  HTTP status: 200\n"
        "  Elapsed: 0.500 s\n\n"
        "down [failed]\n"
        "  URL: http://localhost/down\n"
        "  HTTP status: unavailable\n"
        "  Elapsed: 0.200 s\n"
        "  Error: connection refused\n\n"
        "body [timed out]\n"
        "  URL: http://localhost/body\n"
        "  HTTP status: 200\n"
        "  Elapsed: 0.300 s\n"
        "  Error: body stalled\n\n"
        "Summary: healthy=1, slow=1, failed=1, timed out=1"
    )
    assert results[1].elapsed_seconds == 0.50001


@pytest.mark.parametrize(
    "raw, escaped",
    [
        ("a\nb", r"a\nb"),
        ("a\rb", r"a\rb"),
        ("a\tb", r"a\tb"),
        ("a\x1bb", r"a\x1bb"),
        ("a\x00b", r"a\x00b"),
        ("a\x7fb", r"a\x7fb"),
        ("a\x9bb", r"a\x9bb"),
        ("a\u2028b", r"a\u2028b"),
        ("a\u202eb", r"a\u202eb"),
        ("a\\nb", r"a\\nb"),
        ("café", "café"),
    ],
)
def test_safe_display(raw: str, escaped: str) -> None:
    assert safe_display(raw) == escaped


def test_report_escapes_all_untrusted_fields() -> None:
    result = CheckResult(
        "name\n\x1b[31m",
        "http://localhost/\r\x9b",
        "failed",
        0.1,
        None,
        "error\t\x00\u202e",
    )
    report = format_report([result])
    assert report.splitlines() == [
        r"name\n\x1b[31m [failed]",
        r"  URL: http://localhost/\r\x9b",
        "  HTTP status: unavailable",
        "  Elapsed: 0.100 s",
        r"  Error: error\t\x00\u202e",
        "",
        "Summary: healthy=0, slow=0, failed=1, timed out=0",
    ]


def test_cli_uses_existing_outcome_not_displayed_rounding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "config.json"
    path.write_text(configuration(endpoint()), encoding="utf-8")

    def run(settings: Settings) -> list[CheckResult]:
        item = settings.endpoints[0]
        return [CheckResult(item.name, item.url, "slow", 0.50001, 200, None)]

    monkeypatch.setattr(cli, "run_checks", run)
    assert cli.main(["check", str(path)]) == 1
    output = capsys.readouterr()
    assert "health [slow]" in output.out
    assert "Elapsed: 0.500 s" in output.out
    assert output.err == ""


def test_programming_error_not_hidden_by_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "config.json"
    path.write_text(configuration(endpoint()), encoding="utf-8")

    def run(settings: Settings) -> list[CheckResult]:
        raise RuntimeError("programming bug")

    monkeypatch.setattr(cli, "run_checks", run)
    with pytest.raises(RuntimeError, match="programming bug"):
        cli.main(["check", str(path)])
    assert capsys.readouterr() == ("", "")
