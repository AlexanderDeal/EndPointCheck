import json
import socket
from pathlib import Path

import pytest

from endpointcheck.config import (
    ConfigurationError,
    load_configuration,
    parse_configuration,
)


def endpoint(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "name": "health",
        "url": "http://localhost:8000/health?ready=1",
        "expected_status": 200,
        "latency_threshold_seconds": 0.5,
        "connect_timeout_seconds": 1,
        "read_timeout_seconds": 2,
    }
    value.update(changes)
    return value


def configuration(*entries: object, workers: object = 2) -> str:
    return json.dumps({"max_workers": workers, "endpoints": list(entries)})


@pytest.mark.parametrize("count", [1, 2])
def test_valid_settings(count: int) -> None:
    settings = parse_configuration(
        configuration(*(endpoint(name=f"health-{i}") for i in range(count)))
    )
    assert settings.max_workers == 2
    assert [item.name for item in settings.endpoints] == [
        f"health-{i}" for i in range(count)
    ]
    assert settings.endpoints[0].url == "http://localhost:8000/health?ready=1"
    assert settings.endpoints[0].expected_status == 200
    assert settings.endpoints[0].latency_threshold_seconds == 0.5
    assert settings.endpoints[0].connect_timeout_seconds == 1
    assert settings.endpoints[0].read_timeout_seconds == 2


def test_positive_worker_boundary() -> None:
    assert parse_configuration(configuration(endpoint(), workers=1)).max_workers == 1


@pytest.mark.parametrize("damage", ["truncate", "trailing_comma", "missing_colon"])
def test_malformed_json(damage: str) -> None:
    text = configuration(endpoint())
    if damage == "truncate":
        text = text[:-1]
    elif damage == "trailing_comma":
        text = text[:-1] + ",}"
    else:
        text = text.replace('"max_workers":', '"max_workers"')
    with pytest.raises(ConfigurationError, match="Invalid JSON"):
        parse_configuration(text)


@pytest.mark.parametrize("level", ["root", "endpoint"])
def test_duplicate_keys_raw_json(level: str) -> None:
    # Preserve duplicate keys as raw text; constructing a dict would erase them.
    text = configuration(endpoint())
    if level == "root":
        text = text.replace('"max_workers": 2', '"max_workers": 2, "max_workers": 2')
    else:
        text = text.replace('"name": "health"', '"name": "health", "name": "health"')
    with pytest.raises(ConfigurationError, match="Duplicate JSON key"):
        parse_configuration(text)


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_nonstandard_constants(constant: str) -> None:
    text = configuration(endpoint()).replace(
        '"latency_threshold_seconds": 0.5', f'"latency_threshold_seconds": {constant}'
    )
    with pytest.raises(ConfigurationError, match="Nonstandard JSON constant"):
        parse_configuration(text)


@pytest.mark.parametrize("root", [None, [], "config", 1, True])
def test_wrong_root(root: object) -> None:
    with pytest.raises(ConfigurationError, match="must be an object"):
        parse_configuration(json.dumps(root))


@pytest.mark.parametrize("entries", [None, {}, "endpoints", 1, True, []])
def test_wrong_endpoint_list(entries: object) -> None:
    with pytest.raises(ConfigurationError, match="nonempty list"):
        parse_configuration(json.dumps({"max_workers": 2, "endpoints": entries}))


@pytest.mark.parametrize("entry", [None, [], "endpoint", 1, True])
def test_wrong_endpoint(entry: object) -> None:
    with pytest.raises(ConfigurationError, match="must be an object"):
        parse_configuration(configuration(entry))


@pytest.mark.parametrize("field", ["max_workers", "endpoints"])
def test_missing_root_field(field: str) -> None:
    root: dict[str, object] = {"max_workers": 2, "endpoints": [endpoint()]}
    del root[field]
    with pytest.raises(ConfigurationError, match="missing fields"):
        parse_configuration(json.dumps(root))


@pytest.mark.parametrize("field", list(endpoint()))
def test_missing_endpoint_field(field: str) -> None:
    entry = endpoint()
    del entry[field]
    with pytest.raises(ConfigurationError, match="missing fields"):
        parse_configuration(configuration(entry))


@pytest.mark.parametrize("level", ["root", "endpoint"])
def test_unknown_field(level: str) -> None:
    root: dict[str, object] = {"max_workers": 2, "endpoints": [endpoint()]}
    if level == "root":
        root["extra"] = 1
    else:
        root["endpoints"] = [endpoint(extra=1)]
    with pytest.raises(ConfigurationError, match="unknown fields"):
        parse_configuration(json.dumps(root))


@pytest.mark.parametrize("workers", [0, -1, 1.5, "2", True, False, None])
def test_invalid_workers(workers: object) -> None:
    with pytest.raises(ConfigurationError, match="max_workers"):
        parse_configuration(configuration(endpoint(), workers=workers))


@pytest.mark.parametrize(
    "name", ["", " ", "\t", " health", "health ", "health\n", 1, True, None]
)
def test_invalid_name(name: object) -> None:
    with pytest.raises(ConfigurationError, match="name"):
        parse_configuration(configuration(endpoint(name=name)))


def test_names_are_case_sensitive_and_internal_spaces_are_valid() -> None:
    assert (
        len(
            parse_configuration(
                configuration(
                    endpoint(name="Health check"), endpoint(name="health check")
                )
            ).endpoints
        )
        == 2
    )


def test_duplicate_names() -> None:
    with pytest.raises(ConfigurationError, match="duplicate name"):
        parse_configuration(configuration(endpoint(), endpoint()))


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost",
        "https://example.com/api?q=a%20b",
        "http://127.0.0.1:80",
        "http://[::1]:8000",
        "HTTP://example.com",
        "http://example.com:65535",
    ],
)
def test_valid_url(url: str) -> None:
    assert parse_configuration(configuration(endpoint(url=url))).endpoints[0].url == url


@pytest.mark.parametrize(
    "url",
    [
        "",
        "ftp://example.com",
        "http:///path",
        "https://",
        "example.com",
        " http://localhost",
        "http://localhost ",
        "http://user:pass@localhost",
        "http://user@localhost",
        "http://localhost#part",
        "http://localhost#",
        "http://localhost:abc",
        "http://localhost:-1",
        "http://localhost:65536",
        "http://localhost:",
        "http://[broken",
        "http://local host",
        "http://localhost/\tpath",
        1,
        True,
        None,
    ],
)
def test_invalid_url(url: object) -> None:
    with pytest.raises(ConfigurationError, match="url"):
        parse_configuration(configuration(endpoint(url=url)))


@pytest.mark.parametrize("status", [100, 599])
def test_status_boundaries(status: int) -> None:
    assert (
        parse_configuration(configuration(endpoint(expected_status=status)))
        .endpoints[0]
        .expected_status
        == status
    )


@pytest.mark.parametrize("status", [99, 600, 200.0, "200", True, False, None])
def test_invalid_status(status: object) -> None:
    with pytest.raises(ConfigurationError, match="expected_status"):
        parse_configuration(configuration(endpoint(expected_status=status)))


TIMINGS = [
    "latency_threshold_seconds",
    "connect_timeout_seconds",
    "read_timeout_seconds",
]


@pytest.mark.parametrize("field", TIMINGS)
@pytest.mark.parametrize("value", [1, 0.25])
def test_positive_timings(field: str, value: int | float) -> None:
    assert (
        getattr(
            parse_configuration(configuration(endpoint(**{field: value}))).endpoints[0],
            field,
        )
        == value
    )


@pytest.mark.parametrize("field", TIMINGS)
@pytest.mark.parametrize(
    "value",
    [0, -1, -0.1, float("nan"), float("inf"), float("-inf"), "1", True, False, None],
)
def test_invalid_timings(field: str, value: object) -> None:
    with pytest.raises(ConfigurationError):
        parse_configuration(configuration(endpoint(**{field: value})))


@pytest.mark.parametrize("field", TIMINGS)
def test_overflowing_json_float(field: str) -> None:
    text = configuration(endpoint(**{field: 1})).replace(
        f'"{field}": 1', f'"{field}": 1e999'
    )
    with pytest.raises(ConfigurationError, match="positive finite"):
        parse_configuration(text)


def test_threshold_can_exceed_both_timeouts() -> None:
    settings = parse_configuration(
        configuration(
            endpoint(
                latency_threshold_seconds=5,
                connect_timeout_seconds=1,
                read_timeout_seconds=2,
            )
        )
    )
    assert settings.endpoints[0].latency_threshold_seconds == 5


def test_invalid_second_endpoint_rejects_whole_configuration() -> None:
    with pytest.raises(ConfigurationError, match=r"endpoints\[1\].expected_status"):
        parse_configuration(
            configuration(endpoint(), endpoint(name="other", expected_status=600))
        )


def test_load_utf8(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(configuration(endpoint(name="santé")), encoding="utf-8")
    assert load_configuration(path).endpoints[0].name == "santé"


def test_no_socket_or_dns_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        pytest.fail("validation attempted network activity")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "gethostbyname", forbidden)
    path = tmp_path / "config.json"
    path.write_text(
        configuration(endpoint(url="https://does-not-exist.invalid/")), encoding="utf-8"
    )
    assert (
        load_configuration(path).endpoints[0].url == "https://does-not-exist.invalid/"
    )
