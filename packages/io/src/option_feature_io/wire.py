"""Strict option-json1 envelopes; canonical payload rules belong to contracts."""

import json

from option_feature_contracts import (
    AdmissionLimits, R25_LIMITS, Request, Result, Snapshot, canonical_bytes,
    content_digest, from_payload, validate_limits,
)

from .errors import WireFormatError

_FIELDS = {"wire_version", "record_type", "payload", "content_sha256"}


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise WireFormatError("duplicate JSON key")
        value[key] = item
    return value


def _nonfinite(token):
    raise WireFormatError("nonfinite JSON number")


def _text(data: bytes, limits: AdmissionLimits) -> str:
    validate_limits(limits)
    if type(data) is not bytes:
        raise WireFormatError("wire input must be bytes")
    if len(data) > limits.max_wire_bytes:
        raise WireFormatError("admission_limit_exceeded")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise WireFormatError("invalid UTF-8") from exc
    if text.startswith("\ufeff"):
        raise WireFormatError("UTF-8 BOM forbidden")
    # Bound nesting before the JSON parser allocates recursive structures.
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > 16:
                raise WireFormatError("unexpected nesting")
        elif char in "]}":
            depth -= 1
    return text


def _encode(record_type, value):
    payload = canonical_bytes(value)
    digest = content_digest(record_type, value)
    # Prefix/suffix are fixed and the content digest is hexadecimal ASCII.
    encoded = (b'{"content_sha256":"' + digest.encode("ascii")
               + b'","payload":' + payload + b',"record_type":"'
               + record_type.encode("ascii") + b'","wire_version":"option-json1"}')
    if len(encoded) > R25_LIMITS.max_wire_bytes:
        raise WireFormatError("admission_limit_exceeded")
    return encoded


def _decode(record_type, data, limits):
    # Caller admission errors retain their structural contract type and precede
    # parsing; only failures originating in the JSON parser are wire failures.
    text = _text(data, limits)
    try:
        raw = json.loads(text, object_pairs_hook=_pairs,
                         parse_constant=_nonfinite)
    except (ValueError, RecursionError) as exc:
        if isinstance(exc, WireFormatError):
            raise
        raise WireFormatError("invalid JSON") from exc
    if type(raw) is not dict or set(raw) != _FIELDS:
        raise WireFormatError("unknown or missing envelope fields")
    if raw["wire_version"] != "option-json1" or raw["record_type"] != record_type:
        raise WireFormatError("unsupported envelope identity")
    claimed = raw["content_sha256"]
    if type(claimed) is not str or len(claimed) != 64:
        raise WireFormatError("invalid content digest")
    value = from_payload(record_type, raw["payload"], limits=limits)
    if content_digest(record_type, value, limits=limits) != claimed:
        raise WireFormatError("content digest mismatch")
    return value


def encode_snapshot(value: Snapshot) -> bytes:
    return _encode("snapshot", value)


def decode_snapshot(data: bytes, limits: AdmissionLimits = R25_LIMITS) -> Snapshot:
    return _decode("snapshot", data, limits)


def encode_request(value: Request) -> bytes:
    return _encode("request", value)


def decode_request(data: bytes, limits: AdmissionLimits = R25_LIMITS) -> Request:
    return _decode("request", data, limits)


def encode_results(value: tuple[Result, ...]) -> bytes:
    return _encode("results", value)


def decode_results(data: bytes, limits: AdmissionLimits = R25_LIMITS) -> tuple[Result, ...]:
    return _decode("results", data, limits)
