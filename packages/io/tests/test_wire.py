"""Unexecuted source fixtures until the resource hold is explicitly released."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import unittest

from option_feature_contracts import ContractValidationError, R25_LIMITS, from_payload
from option_feature_io import (
    WireFormatError, decode_request, decode_results, decode_snapshot,
    encode_request, encode_results, encode_snapshot,
    snapshot_from_synthetic_mapping,
)
from fixtures import BINDING, EMPTY, REQUEST, publication


class WireTests(unittest.TestCase):
    def test_original_golden_empty_snapshot_bytes(self):
        # Independently written literal canonical payload, not encoder-derived.
        payload = (b'{"activity_window":null,"bindings":[],"civil_bindings":[],'
                   b'"coverage_certificates":[],"definitions":[],"model_facts":[],'
                   b'"quote_coverage_windows":[],"quotes":[],"schema_version":'
                   b'"option-canonical1","spots":[],"supplied_metrics":[],"trades":[]}')
        digest = hashlib.sha256(b"option-json1\nsnapshot\n" + payload).hexdigest()
        expected = (b'{"content_sha256":"' + digest.encode() + b'","payload":' + payload
                    + b',"record_type":"snapshot","wire_version":"option-json1"}')
        value = from_payload("snapshot", EMPTY)
        self.assertEqual(encode_snapshot(value), expected)
        self.assertEqual(decode_snapshot(expected), value)

    def test_duplicate_keys_at_envelope_and_nested_depth(self):
        for data in (b'{"wire_version":0,"wire_version":1}',
                     b'{"payload":{"x":0,"x":1}}'):
            with self.assertRaises(WireFormatError):
                decode_snapshot(data)

    def test_byte_limit_precedes_parse(self):
        with self.assertRaisesRegex(WireFormatError, "admission_limit_exceeded"):
            decode_snapshot(b"x" * 33, replace(R25_LIMITS, max_wire_bytes=32))

    def test_reject_bom_nonfinite_bad_utf8_deep_arrays(self):
        for data in (b'\xef\xbb\xbf{}', b'{"x":NaN}', b'{"x":Infinity}', b'\xff',
                     b"[" * 17 + b"0" + b"]" * 17):
            with self.assertRaises(WireFormatError):
                decode_snapshot(data)

    def test_envelope_unknown_missing_and_digest_tamper(self):
        encoded = encode_snapshot(from_payload("snapshot", EMPTY))
        for change in ("extra", "missing", "digest"):
            raw = json.loads(encoded)
            if change == "extra":
                raw["extra"] = None
            elif change == "missing":
                del raw["payload"]
            else:
                raw["content_sha256"] = "0" * 64
            with self.assertRaises(WireFormatError):
                decode_snapshot(json.dumps(raw).encode())

    def test_key_order_and_whitespace_are_not_payload_identity(self):
        encoded = encode_snapshot(from_payload("snapshot", EMPTY))
        raw = json.loads(encoded)
        pretty = json.dumps(dict(reversed(list(raw.items()))), indent=2).encode()
        self.assertEqual(decode_snapshot(pretty), decode_snapshot(encoded))

    def test_full_constructed_result_roundtrip(self):
        results = publication().results
        self.assertEqual(decode_results(encode_results(results)), results)

    def test_request_roundtrip_and_raised_decoder_limits(self):
        request = from_payload("request", REQUEST)
        self.assertEqual(decode_request(encode_request(request)), request)
        with self.assertRaises(ContractValidationError):
            decode_request(b"not-json", replace(R25_LIMITS, max_wire_bytes=16777217))

    def test_exact_decimal_payload_roundtrip(self):
        payload = deepcopy(EMPTY)
        payload["bindings"] = [BINDING]
        payload["spots"] = [{"underlying_id": "U", "value": "0.000000000000000001",
            "currency": "USD", "action_basis_id": "basis1", "event_ns": 0,
            "known_at_ns": 0, "revision_id": "1", "input_binding_id": "synthetic-1"}]
        snapshot = from_payload("snapshot", payload)
        self.assertEqual(decode_snapshot(encode_snapshot(snapshot)), snapshot)

    def test_reject_unknown_payload_and_noncanonical_decimals(self):
        raw = json.loads(encode_snapshot(from_payload("snapshot", EMPTY)))
        raw["payload"]["unknown"] = 1
        with self.assertRaises(ContractValidationError):
            decode_snapshot(json.dumps(raw).encode())
        for value in ("01", "+1", "1.0", "1e2", "-0", "NaN"):
            payload = deepcopy(EMPTY)
            payload["bindings"] = [BINDING]
            payload["spots"] = [{"underlying_id": "U", "value": value,
                "currency": "USD", "action_basis_id": "basis1", "event_ns": 0,
                "known_at_ns": 0, "revision_id": "1", "input_binding_id": "synthetic-1"}]
            with self.assertRaises(ContractValidationError):
                from_payload("snapshot", payload)

    def test_synthetic_adapter_requires_original_explicit_binding(self):
        payload = deepcopy(EMPTY)
        payload["bindings"] = [BINDING]
        snapshot = snapshot_from_synthetic_mapping(
            payload, certification_reference="original-test-scenario1")
        self.assertEqual(snapshot.bindings[0].provenance_mode, "synthetic")
        with self.assertRaises(ValueError):
            snapshot_from_synthetic_mapping(payload, certification_reference="other")
        payload["bindings"][0] = dict(BINDING, provenance_mode="licensed")
        with self.assertRaises(ValueError):
            snapshot_from_synthetic_mapping(payload,
                certification_reference="original-test-scenario1")
