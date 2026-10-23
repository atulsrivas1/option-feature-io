"""Output coherence for decoded Results against recomputed output.

Stages 5-8 are produced by the option-features evaluator; this module only
compares an enclosing Results payload with the payload recomputed from the
decoded Snapshot and Request. Records are walked in schema declaration order
so the reported first difference follows the contract scan order.
"""

from option_feature_contracts.variants1 import UNIONS, RECORDS
from option_feature_contracts.variants1.canonical import fail


def _fields(name):
    return [tuple(tok.split(":", 1)) for tok in RECORDS[name].split()]


def _child_record(spec, value):
    """Record name addressed by a field spec, or None for scalars and plain arrays."""
    base = spec.lstrip("?")
    if base.startswith("[]"):
        base = base[2:]
    if base.startswith("R."):
        return base[2:]
    if base.startswith("U.") and isinstance(value, dict):
        table = UNIONS.get(base[2:], {})
        return table.get(value.get("kind"))
    return None


def first_difference(expected, actual, path, record=None, spec=None):
    """Return the first differing RFC 6901 path in declared/array order, or None."""
    if type(expected) is not type(actual):
        return path
    if spec is not None and isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return path
        for index, (left, right) in enumerate(zip(expected, actual)):
            found = first_difference(left, right, "%s/%d" % (path, index), None, spec)
            if found:
                return found
        return None
    if isinstance(expected, dict):
        if record is not None and record in RECORDS:
            for field, field_spec in _fields(record):
                if field not in actual or field not in expected:
                    return "%s/%s" % (path, field)
                child = _child_record(field_spec, expected[field])
                found = first_difference(expected[field], actual[field], "%s/%s" % (path, field),
                                         child, field_spec)
                if found:
                    return found
            for key in list(expected) + list(actual):
                if key not in expected or key not in actual:
                    return "%s/%s" % (path, key)
            return None
        for key in expected:
            if key not in actual:
                return "%s/%s" % (path, key)
            found = first_difference(expected[key], actual[key], "%s/%s" % (path, key))
            if found:
                return found
        for key in actual:
            if key not in expected:
                return "%s/%s" % (path, key)
        return None
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return path
        for index, (left, right) in enumerate(zip(expected, actual)):
            found = first_difference(left, right, "%s/%d" % (path, index))
            if found:
                return found
        return None
    return None if expected == actual else path


def check_results_coherence(recomputed_payload, decoded_payload):
    """Raise identity_mismatch at stage 9 when the Results payloads differ."""
    found = first_difference(recomputed_payload, decoded_payload, "/results", "Results")
    if found is not None:
        fail("identity_mismatch", found, 9)
