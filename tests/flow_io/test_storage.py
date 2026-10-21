"""Literal supplied facts exercise persistence, not an independent math oracle."""
from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import duckdb
from option_flow_contracts import (
    FLOW_LIMITS, FlowBinding, FlowCheckpoint, FlowCoverage, FlowEvidence,
    FlowGroup, FlowOperand, FlowPartitionWeight, FlowPolicy, FlowPopulation, FlowPublication, FlowReference,
    FlowRequest, FlowRational, FlowResult, FlowSnapshot, FlowValidationError,
    encode_flow_snapshot, flow_canonical_bytes, flow_record_digest,
)
from option_flow_io import (
    FlowDuckDBSink, PublicationConflict, StorageIntegrityError, StorageSchemaError,
    SyntheticFlowAdapter,
)


def attack_json(payload):
    """Test-only malicious bytes; never call a validating codec on corruption."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def attack_record_digest(record_type, payload):
    return sha256(b"option-flow-record1\n" + record_type.encode("ascii") +
                  b"\n" + attack_json(payload)).hexdigest()


def literal_snapshot():
    binding = FlowBinding("synthetic", "tiny-tape", "1", "0" * 64,
                          "synthetic", "Original synthetic test facts")
    reference = FlowReference(
        reference_id="ref", contract_id="C", underlying_id="U", currency="USD",
        action_basis_id="basis", right="call", strike=Decimal("100"),
        multiplier=Decimal("100"), expiry_ordinal=100,
        civil_ordinal=None, civil_instant_ns=None, civil_known_at_ns=None,
        calendar_id=None, calendar_revision=None, spot=None, spot_event_ns=None,
        spot_known_at_ns=None, spot_stream_id=None, spot_position=None,
        effective_from_ns=0, effective_to_ns=None, known_at_ns=0,
        revision_id="r1", input_binding_id="synthetic")
    group = FlowGroup("G", "underlying", "U", ("C",), None, None, "USD", "basis")
    population = FlowPopulation("P", "G", 0, 10, ("C",), (), (), True, 0, "synthetic")
    return FlowSnapshot("option-flow-canonical1", (binding,), (reference,), (), (),
                        (group,), (population,), (), (), ())


def literal_request(output="execution.cluster_premium"):
    policy = FlowPolicy("r26-flow-policy1", "option-origin-context1",
                        "option-quote-midpoint1", 10, 10, 1, 2, "horizon", 1)
    return FlowRequest("option-flow-request1", ("G",), (output,), 0, 10, 10,
                       1, policy, (), (), "option-flow-formulas1", FLOW_LIMITS)


def literal_publication(with_result=False, with_checkpoint=True):
    snapshot = literal_snapshot()
    request = literal_request("flow.premium" if with_result else "execution.cluster_premium")
    snapshot_digest = flow_record_digest("flow_snapshot", snapshot)
    request_digest = flow_record_digest("flow_request", request)
    policy_digest = flow_record_digest("flow_policy", request.policy)
    checkpoint = FlowCheckpoint("option-flow-checkpoint1", snapshot, request,
                                snapshot_digest, request_digest, policy_digest,
                                "option-flow-formulas1") if with_checkpoint else None
    work = sha256(b"option-flow-work1\n" + json.dumps(
        [snapshot_digest, request_digest, "1" * 64, None],
        separators=(",", ":")).encode()).hexdigest()
    results = ()
    if with_result:
        # This literal zero is a complete-empty supplied persistence fixture.
        # It is never used as proof that an evaluator computes this row.
        coverage = FlowCoverage("P", True, 0, 0, 0, 0, 0, 0, 0)
        operands = tuple(FlowOperand(name, FlowRational(0, 1), unit) for name, unit in sorted((
            ("count", "executions"), ("contracts", "contracts"), ("share_equivalent", "payoff_units"),
            ("premium", "group_currency"), ("buy_premium", "group_currency"),
            ("sell_premium", "group_currency"), ("unknown_premium", "group_currency"),
            ("signed_premium", "group_currency"), ("call_premium", "group_currency"),
            ("put_premium", "group_currency"))))
        partitions = (FlowPartitionWeight("contract", "C", FlowRational(0, 1)),
                      FlowPartitionWeight("expiry", "100", FlowRational(0, 1)))
        evidence = FlowEvidence((), (), (), operands, partitions, (), None, (), (), (), ("complete_empty",))
        results = (FlowResult(
            schema_version="option-flow-result1", group_id="G", output_id="flow.premium",
            cluster_id=None, window_start_ns=0, window_end_ns=10,
            knowledge_cutoff_ns=10, available_at_ns=0,
            temporal_profile="option-origin-context1", currency="USD", action_basis_id="basis",
            origin="computed", value=FlowRational(0, 1), unit="group_currency", status="available",
            reason="ok", quality_flags=("complete_empty",), coverage=coverage,
            sign_witnesses=(), evidence=evidence, numerator=None, denominator=None,
            baseline_ids=(), dependency_binding_ids=("synthetic",), dependency_record_sha256s=(),
            policy_sha256=policy_digest, request_sha256=request_digest,
            snapshot_sha256=snapshot_digest, checkpoint_sha256=None,
            formula_version="option-flow-formulas1", contracts_package_version="0.1.0a1",
            calculation_package_version="0.1.0a1"),)
    return FlowPublication("option-flow-generation1", "run", work, request,
                           request_digest, snapshot_digest, "1" * 64, None,
                           results, snapshot.bindings, checkpoint)


class AdapterTests(unittest.TestCase):
    def test_strict_synthetic_roundtrip_and_receipt(self):
        snapshot = literal_snapshot()
        wire = encode_flow_snapshot(snapshot)
        adapter = SyntheticFlowAdapter(wire)
        self.assertEqual(adapter.load(), snapshot)
        self.assertEqual(adapter.receipt.input_sha256, sha256(wire).hexdigest())
        self.assertEqual(adapter.receipt.snapshot_sha256, flow_record_digest("flow_snapshot", snapshot))
        self.assertEqual(adapter.receipt.input_bytes, len(wire))
        self.assertEqual(adapter.receipt.deduplicated_count, 0)

    def test_observed_binding_is_not_relabelled_synthetic(self):
        snapshot = literal_snapshot()
        snapshot = replace(snapshot, bindings=(replace(snapshot.bindings[0], provenance_mode="licensed"),))
        with self.assertRaises(FlowValidationError):
            SyntheticFlowAdapter(encode_flow_snapshot(snapshot)).load()

    def test_noncanonical_wire_fails(self):
        with self.assertRaises(FlowValidationError):
            SyntheticFlowAdapter(b" " + encode_flow_snapshot(literal_snapshot())).load()


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.path = str(Path(self.directory.name) / "flow.duckdb")

    def tearDown(self):
        self.directory.cleanup()

    def test_empty_cluster_generation_checkpoint_reopen_retry(self):
        publication = literal_publication()
        with FlowDuckDBSink(self.path) as sink:
            receipt = sink.publish(publication)
            self.assertEqual(receipt.outcome, "committed")
            self.assertTrue(receipt.verified_readback)
            self.assertEqual(receipt.result_count, 0)
            self.assertIsNotNone(receipt.output_checkpoint_sha256)
        with FlowDuckDBSink(self.path) as sink:
            self.assertEqual(flow_canonical_bytes(sink.read("run")), flow_canonical_bytes(publication))
            self.assertEqual(sink.publish(publication).outcome, "already_committed")

    def test_result_binding_checkpoint_complete_parity(self):
        publication = literal_publication(with_result=True)
        with FlowDuckDBSink(self.path) as sink:
            sink.publish(publication)
            self.assertEqual(flow_canonical_bytes(sink.read("run")), flow_canonical_bytes(publication))
            self.assertEqual(sink.publish(publication).result_count, 1)

    def test_changed_run_key_publication_conflicts(self):
        publication = literal_publication()
        with FlowDuckDBSink(self.path) as sink:
            sink.publish(publication)
            with self.assertRaises(PublicationConflict):
                sink.publish(replace(publication, output_checkpoint=None))
            self.assertEqual(sink.read("run"), publication)

    def test_precommit_failure_rolls_back_all_five_tables(self):
        publication = literal_publication(with_result=True)
        with FlowDuckDBSink(self.path) as sink:
            connection = sink._connection
            class WriteFault:
                def execute(self, statement, parameters=None):
                    if statement.startswith("INSERT INTO flow_checkpoints"):
                        raise RuntimeError("fault after generation/results/bindings inserts")
                    return connection.execute(statement) if parameters is None else connection.execute(statement, parameters)
            with patch.object(sink, "_connection", WriteFault()):
                with self.assertRaises(RuntimeError):
                    sink.publish(publication)
            self.assertIsNone(sink.read("run"))
            self.assertEqual(sink.publish(publication).outcome, "committed")

    def test_commit_then_lost_ack_recovers_complete_generation(self):
        publication = literal_publication()
        with FlowDuckDBSink(self.path) as sink:
            def commit_then_raise():
                sink._connection.execute("COMMIT")
                raise RuntimeError("ack lost")
            with patch.object(sink, "_commit_transaction", side_effect=commit_then_raise):
                receipt = sink.publish(publication)
            self.assertEqual(receipt.outcome, "committed")
            self.assertTrue(receipt.verified_readback)
            self.assertEqual(sink.publish(publication).outcome, "already_committed")

    def test_failed_commit_without_commit_never_claims_success(self):
        publication = literal_publication()
        with FlowDuckDBSink(self.path) as sink:
            with patch.object(sink, "_commit_transaction", side_effect=RuntimeError("before commit")):
                with self.assertRaises(RuntimeError):
                    sink.publish(publication)
            self.assertIsNone(sink.read("run"))

    def _corrupt(self, statement):
        with FlowDuckDBSink(self.path) as sink:
            sink.publish(literal_publication(with_result=True))
        connection = duckdb.connect(self.path)
        try:
            connection.execute(statement)
        finally:
            connection.close()

    def test_missing_result_is_corruption_on_read_and_retry(self):
        self._corrupt("DELETE FROM flow_result_rows")
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read("run")
            with self.assertRaises(StorageIntegrityError):
                sink.publish(literal_publication(with_result=True))

    def test_altered_binding_is_corruption(self):
        self._corrupt("UPDATE flow_bindings SET record_sha256=repeat('a',64)")
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read("run")

    def test_missing_checkpoint_is_corruption(self):
        self._corrupt("DELETE FROM flow_checkpoints")
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read("run")

    def test_altered_publication_bytes_do_not_hide_valid_separate_rows(self):
        self._corrupt("UPDATE flow_generations SET canonical_publication='{}'")
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read("run")

    def test_result_ordinal_gap_is_corruption(self):
        self._corrupt("UPDATE flow_result_rows SET ordinal=1")
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read("run")

    def test_spurious_checkpoint_rejected(self):
        publication = literal_publication(with_checkpoint=False)
        with FlowDuckDBSink(self.path) as sink:
            sink.publish(publication)
        connection = duckdb.connect(self.path)
        try:
            connection.execute("INSERT INTO flow_checkpoints VALUES ('run',?,?)", (
                "0" * 64, flow_canonical_bytes(literal_publication().output_checkpoint).decode()))
        finally:
            connection.close()
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read("run")

    def test_unknown_generation_state_is_corruption(self):
        self._corrupt("UPDATE flow_generations SET state='pending'")
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read("run")

    def test_orphan_row_rejected_at_open(self):
        self._corrupt("DELETE FROM flow_generations")
        with self.assertRaises(StorageIntegrityError):
            FlowDuckDBSink(self.path)

    def test_r25_or_unknown_schema_never_migrated(self):
        connection = duckdb.connect(self.path)
        connection.execute("CREATE TABLE option_schema(version VARCHAR PRIMARY KEY)")
        connection.close()
        with self.assertRaises(StorageSchemaError):
            FlowDuckDBSink(self.path)

    def test_extra_index_rejected(self):
        with FlowDuckDBSink(self.path):
            pass
        connection = duckdb.connect(self.path)
        connection.execute("CREATE INDEX unexpected ON flow_generations(work_sha256)")
        connection.close()
        with self.assertRaises(StorageSchemaError):
            FlowDuckDBSink(self.path)

    def test_extra_schema_rejected_without_tables(self):
        connection = duckdb.connect(self.path)
        connection.execute("CREATE SCHEMA unexpected")
        connection.close()
        with self.assertRaises(StorageSchemaError):
            FlowDuckDBSink(self.path)

    def test_unknown_column_never_migrated(self):
        with FlowDuckDBSink(self.path):
            pass
        connection = duckdb.connect(self.path)
        connection.execute("ALTER TABLE flow_generations ADD COLUMN unexpected VARCHAR")
        connection.close()
        with self.assertRaises(StorageSchemaError):
            FlowDuckDBSink(self.path)

    def test_closed_sink_rejects_use(self):
        sink = FlowDuckDBSink(self.path)
        sink.close()
        sink.close()
        with self.assertRaises(RuntimeError):
            sink.read("run")

    def test_generation_bad_work_digest_rejected_before_write(self):
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(FlowValidationError):
                sink.publish(replace(literal_publication(), work_sha256="0" * 64))
            self.assertIsNone(sink.read("run"))

    def test_result_output_unit_mismatch_rejected_before_write(self):
        publication = literal_publication(with_result=True)
        malformed = replace(publication, results=(replace(publication.results[0], unit="contracts"),))
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(FlowValidationError):
                sink.publish(malformed)
            self.assertIsNone(sink.read("run"))

    def test_result_status_value_incoherence_rejected_before_write(self):
        publication = literal_publication(with_result=True)
        with FlowDuckDBSink(self.path) as sink:
            for changes in ({"status": "unavailable", "reason": "incomplete_population"},
                            {"value": None}, {"reason": "zero_denominator"}):
                with self.subTest(changes=changes):
                    malformed = replace(publication, results=(replace(publication.results[0], **changes),))
                    with self.assertRaises(FlowValidationError):
                        sink.publish(malformed)
                    self.assertIsNone(sink.read("run"))

    def test_checkpoint_actual_history_cannot_hide_behind_claimed_digest(self):
        publication = literal_publication()
        checkpoint = publication.output_checkpoint
        changed_history = replace(checkpoint.history, references=(
            replace(checkpoint.history.references[0], known_at_ns=1),))
        malformed = replace(publication, output_checkpoint=replace(checkpoint, history=changed_history))
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(FlowValidationError):
                sink.publish(malformed)
            self.assertIsNone(sink.read("run"))

    def test_checkpoint_prior_request_digest_cannot_be_forged(self):
        publication = literal_publication()
        malformed = replace(publication, output_checkpoint=replace(
            publication.output_checkpoint, prior_request_sha256="2" * 64))
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(FlowValidationError):
                sink.publish(malformed)
            self.assertIsNone(sink.read("run"))

    def test_checkpoint_policy_digest_cannot_be_forged(self):
        publication = literal_publication()
        malformed = replace(publication, output_checkpoint=replace(
            publication.output_checkpoint, policy_sha256="2" * 64))
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(FlowValidationError):
                sink.publish(malformed)
            self.assertIsNone(sink.read("run"))

    def test_checkpoint_semantic_history_invalid_even_with_rebound_hashes(self):
        publication = literal_publication()
        checkpoint = publication.output_checkpoint
        # Valid field types and freshly bound digests do not fix the mismatch
        # between the group's declared underlying and its actual reference.
        history = replace(checkpoint.history, groups=(replace(checkpoint.history.groups[0], underlying_id="other"),))
        # Start with valid canonical source bytes, then independently mutate and
        # hash the malicious payload. Public codecs correctly refuse this input.
        history_payload = json.loads(flow_canonical_bytes(checkpoint.history))
        self.assertEqual(attack_record_digest("flow_snapshot", history_payload),
                         flow_record_digest("flow_snapshot", checkpoint.history))
        history_payload["groups"][0]["underlying_id"] = "other"
        digest = attack_record_digest("flow_snapshot", history_payload)
        work = sha256(b"option-flow-work1\n" + json.dumps(
            [digest, publication.request_sha256, publication.cohort_sha256, None],
            separators=(",", ":")).encode()).hexdigest()
        malformed = replace(publication, snapshot_sha256=digest, work_sha256=work,
                            output_checkpoint=replace(checkpoint, history=history, history_sha256=digest))
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(FlowValidationError):
                sink.publish(malformed)
            self.assertIsNone(sink.read("run"))

    def test_semantically_bad_stored_result_rejected_even_with_rebound_metadata(self):
        publication = literal_publication(with_result=True)
        payload = json.loads(flow_canonical_bytes(publication))
        self.assertEqual(attack_record_digest("flow_publication", payload),
                         flow_record_digest("flow_publication", publication))
        payload["results"][0]["unit"] = "contracts"
        with FlowDuckDBSink(self.path) as sink:
            sink.publish(publication)
        # Simulate external corruption that consistently rehashes every changed
        # row. Integrity hashes alone must not admit semantically invalid output.
        connection = duckdb.connect(self.path)
        try:
            metadata = list(connection.execute("SELECT * FROM flow_generations WHERE run_key='run'").fetchone())
            metadata[6] = attack_record_digest("flow_results", payload["results"])
            metadata[9] = attack_record_digest("flow_publication", payload)
            metadata[12] = attack_json(payload).decode("utf-8")
            connection.execute("DELETE FROM flow_generations")
            connection.execute("INSERT INTO flow_generations VALUES (" + ",".join("?" for _ in metadata) + ")", metadata)
            connection.execute("UPDATE flow_result_rows SET record_sha256=?,canonical_json=?", (
                attack_record_digest("flow_result", payload["results"][0]),
                attack_json(payload["results"][0]).decode("utf-8")))
        finally:
            connection.close()
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read("run")
            with self.assertRaises(StorageIntegrityError):
                sink.publish(publication)


    def test_forged_stored_checkpoint_rejected_even_with_rebound_metadata(self):
        publication = literal_publication()
        payload = json.loads(flow_canonical_bytes(publication))
        self.assertEqual(attack_record_digest("flow_publication", payload),
                         flow_record_digest("flow_publication", publication))
        payload["output_checkpoint"]["policy_sha256"] = "2" * 64
        with FlowDuckDBSink(self.path) as sink:
            sink.publish(publication)
        connection = duckdb.connect(self.path)
        try:
            metadata = list(connection.execute("SELECT * FROM flow_generations WHERE run_key='run'").fetchone())
            metadata[8] = attack_record_digest("flow_checkpoint", payload["output_checkpoint"])
            metadata[9] = attack_record_digest("flow_publication", payload)
            metadata[12] = attack_json(payload).decode("utf-8")
            connection.execute("DELETE FROM flow_generations")
            connection.execute("INSERT INTO flow_generations VALUES (" + ",".join("?" for _ in metadata) + ")", metadata)
            connection.execute("UPDATE flow_checkpoints SET record_sha256=?,canonical_json=?", (
                attack_record_digest("flow_checkpoint", payload["output_checkpoint"]),
                attack_json(payload["output_checkpoint"]).decode("utf-8")))
        finally:
            connection.close()
        with FlowDuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read("run")
            with self.assertRaises(StorageIntegrityError):
                sink.publish(publication)


if __name__ == "__main__":
    unittest.main()
