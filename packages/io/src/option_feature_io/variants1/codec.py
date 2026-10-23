"""Envelope encode/decode for option-flow-variants-json1 records."""

import json
import re

from option_feature_contracts.variants1 import (
    RECORDS, VariantValidationError, canonical_json, content_digest, record_digest,
    validate_scalars, validate_shape,
)
from option_feature_contracts.variants1.canonical import SCHEMA_JSON, fail

DEFAULT_WIRE_BYTES = 16777216
DEFAULT_DEPTH = 32
ENVELOPE_KEYS = ("content_sha256", "payload", "record_type", "schema_version")
LIMIT_KEYS = ("wire_bytes", "depth")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_STRING = re.compile(r'"(?:[^"\\]|\\.)*"')
_BOM = "﻿"
_PREFIX = "variant_"
_MAX_INT_DIGITS = 4300


class _BigInt:
    """Integer literal beyond the decimal conversion bound; never a valid int scalar."""

    def __init__(self, literal):
        self.literal = literal


def _parse_int(literal):
    if len(literal.lstrip("-")) > _MAX_INT_DIGITS:
        return _BigInt(literal)
    return int(literal)


def _escape(segment):
    return segment.replace("~", "~0").replace("/", "~1")


def _first_duplicate(text):
    """Pointer of the document-order first repeated key in valid JSON text."""
    frames = []  # each: {"obj": bool, "keys": set, "expect_key": bool, "cur": str, "idx": int}
    pos, n = 0, len(text)
    while pos < n:
        ch = text[pos]
        if ch in " \t\r\n:":
            pos += 1
        elif ch == "{" or ch == "[":
            frames.append({"obj": ch == "{", "keys": set(), "expect_key": ch == "{",
                           "cur": "" if ch == "{" else "0", "idx": 0})
            pos += 1
        elif ch == "}" or ch == "]":
            frames.pop()
            pos += 1
        elif ch == ",":
            if frames and frames[-1]["obj"]:
                frames[-1]["expect_key"] = True
            elif frames:
                frames[-1]["idx"] += 1
                frames[-1]["cur"] = str(frames[-1]["idx"])
            pos += 1
        elif ch == '"':
            token = _STRING.match(text, pos).group(0)
            pos += len(token)
            value = json.loads(token)
            top = frames[-1] if frames else None
            if top is not None and top["obj"] and top["expect_key"]:
                if value in top["keys"]:
                    prefix = "/envelope"
                    for frame in frames[:-1]:
                        prefix += "/" + _escape(frame["cur"])
                    return prefix + "/" + _escape(value)
                top["keys"].add(value)
                top["cur"] = value
                top["expect_key"] = False
        else:
            while pos < n and text[pos] not in " \t\r\n,:]}":
                pos += 1
    return None


class _Dup(Exception):
    pass


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise _Dup()
        value[key] = item
    return value


def _nonfinite(token):
    raise ValueError("nonfinite number")


def _limit(limits, name, default):
    if limits is None or name not in limits:
        return default
    value = limits[name]
    if type(value) is not int or value < 0:
        fail("type_mismatch", "/limits/%s" % name, 3)
    return value


def _stage1(raw, limits):
    if type(raw) is not bytes:
        fail("type_mismatch", "/envelope", 1)
    if len(raw) > _limit(limits, "wire_bytes", DEFAULT_WIRE_BYTES):
        fail("resource_limit", "/envelope", 1)
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        fail("invalid_utf8", "/envelope", 1)
    cap = _limit(limits, "depth", DEFAULT_DEPTH)
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
            if depth > cap:
                fail("resource_limit", "/envelope", 1)
        elif char in "]}":
            depth -= 1
    return text


def _name(record_type):
    """Envelope record_type is 'variant_<Name>'; RECORDS is keyed by <Name>."""
    if type(record_type) is not str or not record_type.startswith(_PREFIX):
        return None
    name = record_type[len(_PREFIX):]
    return name if name in RECORDS else None


def _shape(payload, name, root):
    """Stage 3 closed-record check; a field-set defect is reported at its record."""
    try:
        validate_shape(payload, name, root)
    except VariantValidationError as exc:
        if exc.code == "field_set" and exc.stage == 3:
            exc.path = exc.path.rsplit("/", 1)[0]
        raise


def record_sha256(record_type, payload):
    return record_digest(record_type, payload)


def encode_record(record_type, payload, limits=None):
    """Return canonical envelope bytes for a validated payload."""
    name = _name(record_type)
    if name is None:
        fail("unsupported_schema", "/envelope/record_type", None)
    _shape(payload, name, "/envelope/payload")
    validate_scalars(payload, name, "/envelope/payload")
    envelope = {
        "content_sha256": content_digest(record_type, payload),
        "payload": payload,
        "record_type": record_type,
        "schema_version": SCHEMA_JSON,
    }
    encoded = canonical_json(envelope)
    if len(encoded) > _limit(limits, "wire_bytes", DEFAULT_WIRE_BYTES):
        fail("resource_limit", "/envelope", 1)
    return encoded


def decode_record(raw, record_type, limits=None):
    """Strictly decode envelope bytes to the validated payload.

    Raises VariantValidationError with code, RFC 6901 path and stage. The
    returned payload is valid for stages 3 and 4; producer stages 5-8 are not
    evaluated here.
    """
    text = _stage1(raw, limits)
    if text.startswith(_BOM):
        fail("invalid_json", "/envelope", 2)
    dup = False

    def hook(pairs):
        nonlocal dup
        value = {}
        for key, item in pairs:
            if key in value:
                dup = True
            value[key] = item
        return value

    try:
        value = json.loads(text, object_pairs_hook=hook, parse_constant=_nonfinite,
                           parse_int=_parse_int)
    except (ValueError, RecursionError):
        fail("invalid_json", "/envelope", 2)
    if dup:
        fail("field_set", _first_duplicate(text), 2)
    if type(value) is not dict:
        fail("type_mismatch", "/envelope", 3)
    if set(value) != set(ENVELOPE_KEYS):
        fail("field_set", "/envelope", 3)
    if value["schema_version"] != SCHEMA_JSON:
        fail("unsupported_schema", "/envelope/schema_version", 3)
    name = _name(record_type)
    if value["record_type"] != record_type or name is None:
        fail("unsupported_schema", "/envelope/record_type", 3)
    claimed = value["content_sha256"]
    if type(claimed) is not str:
        fail("type_mismatch", "/envelope/content_sha256", 3)
    payload = value["payload"]
    _shape(payload, name, "/envelope/payload")
    if not _HASH.match(claimed):
        fail("invalid_scalar", "/envelope/content_sha256", 4)
    validate_scalars(payload, name, "/envelope/payload")
    if text.encode("utf-8") != canonical_json(value):
        fail("noncanonical", "/envelope", 9)
    if content_digest(record_type, payload) != claimed:
        fail("digest_mismatch", "/envelope/content_sha256", 9)
    return payload
