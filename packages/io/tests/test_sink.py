"""Constructed sink scenarios; no result here establishes numerical accuracy."""

from dataclasses import replace
import tempfile
from pathlib import Path
import unittest

import duckdb
from option_feature_io import (DuckDBSink, PublicationConflict, StorageIntegrityError,
                               StorageSchemaError)
from fixtures import publication


class SinkTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = str(Path(self.directory.name) / "synthetic.duckdb")

    def tearDown(self):
        self.directory.cleanup()

    def test_full_publication_roundtrip_and_identical_retry(self):
        value = publication()
        with DuckDBSink(self.path) as sink:
            self.assertIsNone(sink.read(value.run_key))
            receipt = sink.commit(value)
            self.assertEqual(receipt.outcome, "committed")
            self.assertTrue(receipt.readback_verified)
            self.assertEqual(sink.read(value.run_key), value)
            self.assertEqual(sink.commit(value).outcome, "already_committed")
        with DuckDBSink(self.path) as sink:
            self.assertEqual(sink.read(value.run_key), value)

    def test_native_connection_explicitly_selects_one_thread(self):
        with DuckDBSink(self.path) as sink:
            self.assertEqual(sink._connection.execute(
                "SELECT current_setting('threads')").fetchone()[0], 1)

    def test_changed_summary_binding_or_result_conflicts(self):
        value = publication()
        with DuckDBSink(self.path) as sink:
            sink.commit(value)
            for changed in (replace(value, cohort_sha256="7" * 64),
                    replace(value, bindings=(replace(value.bindings[0], source_revision="2"),)),
                    replace(value, results=(replace(value.results[0], value=101.0),))):
                with self.assertRaises(PublicationConflict):
                    sink.commit(changed)
            self.assertEqual(sink.read(value.run_key), value)

    def test_reject_equity_or_extra_schema_without_mutation(self):
        connection = duckdb.connect(self.path)
        connection.execute("CREATE TABLE equity_private_marker(value INTEGER)")
        connection.execute("INSERT INTO equity_private_marker VALUES (42)")
        connection.close()
        with self.assertRaises(StorageSchemaError):
            DuckDBSink(self.path)
        connection = duckdb.connect(self.path)
        self.assertEqual(connection.execute("SELECT * FROM equity_private_marker").fetchall(), [(42,)])
        self.assertEqual(connection.execute("SHOW TABLES").fetchall(), [("equity_private_marker",)])
        connection.close()

    def test_transaction_failure_rolls_back_generation_and_reopens(self):
        class InjectedFailure(DuckDBSink):
            def _read(self, run_key):
                value = super()._read(run_key)
                if value is not None:
                    raise RuntimeError("injected before transaction commit")
                return value
        with InjectedFailure(self.path) as sink:
            with self.assertRaisesRegex(RuntimeError, "injected"):
                sink.commit(publication())
            self.assertIsNone(sink.read("synthetic-run1"))
        with DuckDBSink(self.path) as sink:
            self.assertEqual(sink.commit(publication()).outcome, "committed")

    def test_tampered_rows_fail_full_readback_and_retry(self):
        value = publication()
        with DuckDBSink(self.path) as sink:
            sink.commit(value)
        connection = duckdb.connect(self.path)
        connection.execute("UPDATE source_bindings SET record_sha256=?", ["0" * 64])
        connection.close()
        with DuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read(value.run_key)
            with self.assertRaises(StorageIntegrityError):
                sink.commit(value)

    def test_failure_after_commit_recovers_by_identical_readback(self):
        class AfterCommitFailure(DuckDBSink):
            calls = 0

            def _read(self, run_key):
                self.calls += 1
                value = super()._read(run_key)
                if self.calls == 3:
                    raise RuntimeError("injected after atomic commit")
                return value
        value = publication()
        with AfterCommitFailure(self.path) as sink:
            with self.assertRaisesRegex(RuntimeError, "after atomic commit"):
                sink.commit(value)
        with DuckDBSink(self.path) as sink:
            self.assertEqual(sink.read(value.run_key), value)
            self.assertEqual(sink.commit(value).outcome, "already_committed")

    def test_missing_ordinal_and_orphan_are_corruption(self):
        with DuckDBSink(self.path) as sink:
            sink.commit(publication())
        connection = duckdb.connect(self.path)
        connection.execute("UPDATE result_rows SET ordinal=8")
        connection.close()
        with DuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read("synthetic-run1")

    def test_schema_change_and_invalid_result_hash_fail(self):
        with DuckDBSink(self.path) as sink:
            value = publication()
            with self.assertRaises(ValueError):
                sink.commit(replace(value, results=(replace(value.results[0], config_sha256="0" * 64),)))
            self.assertIsNone(sink.read(value.run_key))
        connection = duckdb.connect(self.path)
        connection.execute("ALTER TABLE result_rows ADD COLUMN extra INTEGER")
        connection.close()
        with self.assertRaises(StorageSchemaError):
            DuckDBSink(self.path)

    def test_corrupt_excessive_json_nesting_is_typed_integrity_error(self):
        with DuckDBSink(self.path) as sink:
            sink.commit(publication())
        connection = duckdb.connect(self.path)
        connection.execute("UPDATE result_rows SET canonical_json=?",
                           ["[" * 2000 + "0" + "]" * 2000])
        connection.close()
        with DuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read("synthetic-run1")
            with self.assertRaises(StorageIntegrityError):
                sink.commit(publication())

    def test_run_key_rejects_c0_del_c1_and_unpaired_surrogates(self):
        with DuckDBSink(self.path) as sink:
            for key in ("bad\x00key", "bad\x7fkey", "bad\x85key", "bad\ud800key"):
                with self.assertRaises(ValueError):
                    sink.read(key)
                with self.assertRaises(ValueError):
                    sink.commit(replace(publication(), run_key=key))

    def test_corrupt_wellformed_request_hash_read_and_retry_are_integrity_errors(self):
        value = publication()
        with DuckDBSink(self.path) as sink:
            sink.commit(value)
        connection = duckdb.connect(self.path)
        connection.execute("UPDATE generations SET request_sha256=?", ["9" * 64])
        connection.close()
        with DuckDBSink(self.path) as sink:
            with self.assertRaises(StorageIntegrityError):
                sink.read(value.run_key)
            with self.assertRaises(StorageIntegrityError):
                sink.commit(value)
