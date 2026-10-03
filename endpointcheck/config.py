"""Load strict JSON and validate the entire configuration without network I/O."""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


class ConfigurationError(ValueError):
    """An expected configuration or file error suitable for display to users."""


@dataclass(frozen=True)
class EndpointSettings:
    name: str
    url: str
    expected_status: int
    latency_threshold_seconds: int | float
    connect_timeout_seconds: int | float
    read_timeout_seconds: int | float


@dataclass(frozen=True)
class Settings:
    max_workers: int
    endpoints: tuple[EndpointSettings, ...]


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigurationError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ConfigurationError(f"Nonstandard JSON constant: {value}")


def _fields(value: object, required: set[str], location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{location} must be an object")
    missing = required - value.keys()
    unknown = value.keys() - required
    if missing:
        raise ConfigurationError(f"{location}: missing fields {sorted(missing)}")
    if unknown:
        raise ConfigurationError(f"{location}: unknown fields {sorted(unknown)}")
    return value


def _integer(
    value: object, location: str, minimum: int, maximum: int | None = None
) -> int:
    if (
        type(value) is not int
        or value < minimum
        or (maximum is not None and value > maximum)
    ):
        bounds = (
            f"{minimum} through {maximum}" if maximum is not None else f">= {minimum}"
        )
        raise ConfigurationError(
            f"{location} must be an integer {bounds}, excluding booleans"
        )
    return value


def _duration(value: object, location: str) -> int | float:
    # Python integers are finite; do not convert them to floats (which can overflow).
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConfigurationError(f"{location} must be a positive finite number")
    if value <= 0 or (isinstance(value, float) and not math.isfinite(value)):
        raise ConfigurationError(f"{location} must be a positive finite number")
    return value


def _name(value: object, location: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ConfigurationError(
            f"{location} must be nonempty with no surrounding whitespace"
        )
    return value


def _url(value: object, location: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ConfigurationError(
            f"{location} must be a URL without surrounding whitespace"
        )
    # urlsplit strips some control characters; reject them instead of silently repairing.
    if any(
        character.isspace() or ord(character) < 32 or ord(character) == 127
        for character in value
    ):
        raise ConfigurationError(
            f"{location} contains whitespace or control characters"
        )
    try:
        parsed = urlsplit(value)
        port = parsed.port  # Forces validation of numeric syntax and range.
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("HTTP/HTTPS and a hostname are required")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("embedded credentials are forbidden")
        if "#" in value:
            raise ValueError("fragments are forbidden")
        if parsed.netloc.endswith(":") and port is None:
            raise ValueError("empty port is invalid")
    except ValueError as error:
        raise ConfigurationError(f"{location}: invalid URL ({error})") from error
    return value


def parse_configuration(text: str) -> Settings:
    """Return settings only after every endpoint passes validation."""
    try:
        data = json.loads(
            text, object_pairs_hook=_unique_object, parse_constant=_reject_constant
        )
    except (ValueError, RecursionError) as error:
        raise ConfigurationError(f"Invalid JSON: {error}") from error
    root = _fields(data, {"max_workers", "endpoints"}, "configuration")
    workers = _integer(root["max_workers"], "max_workers", 1)
    entries = root["endpoints"]
    if not isinstance(entries, list) or not entries:
        raise ConfigurationError("endpoints must be a nonempty list")
    required = set(EndpointSettings.__dataclass_fields__)
    endpoints: list[EndpointSettings] = []
    names: set[str] = set()
    for index, entry in enumerate(entries):
        location = f"endpoints[{index}]"
        fields = _fields(entry, required, location)
        name = _name(fields["name"], f"{location}.name")
        if name in names:
            raise ConfigurationError(f"{location}.name: duplicate name {name!r}")
        names.add(name)
        endpoints.append(
            EndpointSettings(
                name=name,
                url=_url(fields["url"], f"{location}.url"),
                expected_status=_integer(
                    fields["expected_status"], f"{location}.expected_status", 100, 599
                ),
                latency_threshold_seconds=_duration(
                    fields["latency_threshold_seconds"],
                    f"{location}.latency_threshold_seconds",
                ),
                connect_timeout_seconds=_duration(
                    fields["connect_timeout_seconds"],
                    f"{location}.connect_timeout_seconds",
                ),
                read_timeout_seconds=_duration(
                    fields["read_timeout_seconds"], f"{location}.read_timeout_seconds"
                ),
            )
        )
    return Settings(workers, tuple(endpoints))


def load_configuration(path: Path) -> Settings:
    """Read a UTF-8 JSON file, translating expected read failures into user errors."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ConfigurationError(
            f"Cannot read configuration {path}: {error}"
        ) from error
    return parse_configuration(text)
