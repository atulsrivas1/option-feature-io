"""Unexecuted supplied synthetic mapping example, without a database write."""

from option_feature_io import (decode_snapshot, encode_snapshot,
                               snapshot_from_synthetic_mapping)


def roundtrip_explicit_scenario(payload, certification_reference):
    snapshot = snapshot_from_synthetic_mapping(
        payload, certification_reference=certification_reference)
    return decode_snapshot(encode_snapshot(snapshot))
