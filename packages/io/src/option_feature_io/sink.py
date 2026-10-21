"""Separate four-table DuckDB generations, one writer and atomic readback."""

from dataclasses import replace
import json
import re
import threading
import unicodedata

import duckdb
from option_feature_contracts import (
    R25_LIMITS, canonical_bytes, content_digest, from_payload, record_digest, validate_results,
)

from .errors import PublicationConflict, StorageIntegrityError, StorageSchemaError
from .publication import CommitReceipt, Publication
from .wire import _pairs, _nonfinite, _text

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_TABLES = {
    "option_schema": (("version", "VARCHAR"),),
    "generations": (("run_key", "VARCHAR"), ("work_sha256", "VARCHAR"),
                    ("request_sha256", "VARCHAR"), ("snapshot_sha256", "VARCHAR"),
                    ("cohort_sha256", "VARCHAR"), ("results_sha256", "VARCHAR"),
                    ("result_count", "BIGINT"), ("state", "VARCHAR")),
    "result_rows": (("run_key", "VARCHAR"), ("ordinal", "BIGINT"),
                    ("canonical_json", "VARCHAR")),
    "source_bindings": (("run_key", "VARCHAR"), ("binding_id", "VARCHAR"),
                        ("record_sha256", "VARCHAR"), ("canonical_json", "VARCHAR")),
}
_KEYS = {"option_schema": ("version",), "generations": ("run_key",),
         "result_rows": ("run_key", "ordinal"),
         "source_bindings": ("run_key", "binding_id")}
_CREATE = (
    "CREATE TABLE option_schema(version VARCHAR PRIMARY KEY)",
    "CREATE TABLE generations(run_key VARCHAR PRIMARY KEY, work_sha256 VARCHAR, "
    "request_sha256 VARCHAR, snapshot_sha256 VARCHAR, cohort_sha256 VARCHAR, "
    "results_sha256 VARCHAR, result_count BIGINT, state VARCHAR)",
    "CREATE TABLE result_rows(run_key VARCHAR, ordinal BIGINT, canonical_json VARCHAR, "
    "PRIMARY KEY(run_key, ordinal))",
    "CREATE TABLE source_bindings(run_key VARCHAR, binding_id VARCHAR, "
    "record_sha256 VARCHAR, canonical_json VARCHAR, PRIMARY KEY(run_key, binding_id))",
)


def _run_key(value):
    if (type(value) is not str or not value or len(value) > 256
            or any(unicodedata.category(char) == "Cc" for char in value)):
        raise ValueError("invalid run_key")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise ValueError("invalid run_key Unicode") from exc
    if len(encoded) > 1024:
        raise ValueError("invalid run_key")


def validate_publication(publication: Publication) -> Publication:
    if type(publication) is not Publication:
        raise ValueError("expected Publication")
    _run_key(publication.run_key)
    for name in ("work_sha256", "request_sha256", "snapshot_sha256", "cohort_sha256"):
        value = getattr(publication, name)
        if type(value) is not str or _SHA.fullmatch(value) is None:
            raise ValueError("invalid " + name)
    validate_results(publication.results)
    if not publication.results or type(publication.bindings) is not tuple:
        raise ValueError("publication requires results and typed binding tuple")
    if len(publication.bindings) > 100000:
        raise ValueError("admission_limit_exceeded")
    bindings = {}
    binding_bytes = 0
    for binding in publication.bindings:
        # Pure contract expansion validates every exact InputBinding field.
        encoded = canonical_bytes(binding)
        binding_bytes += len(encoded)
        if binding_bytes > 16777216:
            raise ValueError("admission_limit_exceeded")
        payload = from_payload("input_binding", json.loads(encoded))
        if payload.binding_id in bindings:
            raise ValueError("duplicate binding_id")
        bindings[payload.binding_id] = payload
    for result in publication.results:
        if result.config_sha256 != publication.request_sha256:
            raise ValueError("request hash mismatch")
        if result.snapshot_sha256 != publication.snapshot_sha256:
            raise ValueError("snapshot hash mismatch")
        if any(identifier not in bindings for identifier in result.dependency_binding_ids):
            raise ValueError("unbound result dependency")
    return replace(publication, bindings=tuple(bindings[key] for key in sorted(bindings)))


def _load(record_type, text):
    if type(text) is not str or len(text) > 16777216:
        raise StorageIntegrityError("invalid stored record bytes")
    try:
        encoded = text.encode("utf-8", errors="strict")
        value = from_payload(record_type, json.loads(_text(encoded, R25_LIMITS),
            object_pairs_hook=_pairs, parse_constant=_nonfinite))
    except (ValueError, RecursionError) as exc:
        raise StorageIntegrityError("invalid stored canonical JSON") from exc
    if canonical_bytes(value).decode("utf-8") != text:
        raise StorageIntegrityError("stored record is not canonical")
    return value


class DuckDBSink:
    """Caller-owned explicit destination; context-manager close is supported.

    A single instance serializes all reads/writes. Cross-process multi-writer use
    is outside the admitted profile; DuckDB's own lock failures remain failures.
    """

    def __init__(self, destination: str):
        if type(destination) is not str or not destination:
            raise ValueError("explicit destination required")
        self._lock = threading.RLock()
        self._connection = duckdb.connect(destination, config={"threads": 1})
        try:
            with self._lock:
                self._connection.execute("BEGIN TRANSACTION")
                try:
                    if not self._objects():
                        for statement in _CREATE:
                            self._connection.execute(statement)
                        self._connection.execute("INSERT INTO option_schema VALUES (?)",
                                                 ["option-generation1"])
                    self._schema()
                    self._connection.execute("COMMIT")
                except BaseException:
                    self._connection.execute("ROLLBACK")
                    raise
        except BaseException:
            self._connection.close()
            raise

    def _objects(self):
        return self._connection.execute(
            "SELECT table_schema, table_name, table_type FROM information_schema.tables "
            "WHERE table_schema NOT IN ('information_schema','pg_catalog') "
            "ORDER BY table_schema, table_name").fetchall()

    def _schema(self):
        expected = sorted(("main", name, "BASE TABLE") for name in _TABLES)
        if self._objects() != expected:
            raise StorageSchemaError("unrecognized tables/views; refusing migration")
        if self._connection.execute("SELECT count(*) FROM duckdb_indexes()").fetchone()[0]:
            raise StorageSchemaError("unexpected explicit index")
        if self._connection.execute("SELECT count(*) FROM duckdb_sequences()").fetchone()[0]:
            raise StorageSchemaError("unexpected sequence")
        for table, columns in _TABLES.items():
            actual = self._connection.execute(
                "SELECT column_name, data_type, is_nullable, column_default "
                "FROM information_schema.columns "
                "WHERE table_schema='main' AND table_name=? ORDER BY ordinal_position",
                [table]).fetchall()
            expected_columns = tuple((name, kind, "NO" if name in _KEYS[table] else "YES", None)
                                     for name, kind in columns)
            if tuple(actual) != expected_columns:
                raise StorageSchemaError("column mismatch: " + table)
        constraints = self._connection.execute(
            "SELECT table_name, constraint_type, constraint_column_names "
            "FROM duckdb_constraints() WHERE schema_name='main'").fetchall()
        primary = {}
        for table, kind, columns in constraints:
            if kind == "PRIMARY KEY":
                if table in primary:
                    raise StorageSchemaError("duplicate primary key")
                primary[table] = tuple(columns)
            elif kind != "NOT NULL" or any(col not in _KEYS.get(table, ()) for col in columns):
                raise StorageSchemaError("unexpected constraint")
        if primary != _KEYS:
            raise StorageSchemaError("primary key mismatch")
        if self._connection.execute("SELECT version FROM option_schema").fetchall() != [
                ("option-generation1",)]:
            raise StorageSchemaError("storage version mismatch")

    def _read(self, run_key):
        """One integrity boundary for public reads and every retry/readback."""
        try:
            return self._read_content(run_key)
        except StorageIntegrityError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError) as exc:
            raise StorageIntegrityError("invalid typed stored content") from exc

    def _read_content(self, run_key):
        rows = self._connection.execute(
            "SELECT work_sha256, request_sha256, snapshot_sha256, cohort_sha256, "
            "results_sha256, result_count, state FROM generations WHERE run_key=?",
            [run_key]).fetchall()
        if not rows:
            # Orphans cannot be mistaken for an absent successful generation.
            for table in ("result_rows", "source_bindings"):
                if self._connection.execute(
                        "SELECT count(*) FROM " + table + " WHERE run_key=?", [run_key]).fetchone()[0]:
                    raise StorageIntegrityError("orphaned generation rows")
            return None
        work, request, snapshot, cohort, digest, count, state = rows[0]
        if state != "committed" or type(count) is not int or not 0 < count <= 32001:
            raise StorageIntegrityError("invalid generation state/count")
        for table in ("result_rows", "source_bindings"):
            total_bytes = self._connection.execute(
                "SELECT coalesce(sum(octet_length(encode(canonical_json))), 0) FROM "
                + table + " WHERE run_key=?", [run_key]).fetchone()[0]
            if total_bytes > 16777216:
                raise StorageIntegrityError("stored content exceeds byte admission")
        stored = self._connection.execute(
            "SELECT ordinal, canonical_json FROM result_rows WHERE run_key=? ORDER BY ordinal LIMIT 32002",
            [run_key]).fetchall()
        if len(stored) != count or [row[0] for row in stored] != list(range(count)):
            raise StorageIntegrityError("noncontiguous result rows")
        results = tuple(_load("result", row[1]) for row in stored)
        if content_digest("results", results) != digest:
            raise StorageIntegrityError("ordered results digest mismatch")
        source = self._connection.execute(
            "SELECT binding_id, record_sha256, canonical_json FROM source_bindings "
            "WHERE run_key=? ORDER BY binding_id LIMIT 100001", [run_key]).fetchall()
        if len(source) > 100000:
            raise StorageIntegrityError("binding count exceeds admission")
        bindings = []
        for identifier, claimed, text in source:
            value = _load("input_binding", text)
            if value.binding_id != identifier or record_digest("input_binding", value) != claimed:
                raise StorageIntegrityError("binding identity/digest mismatch")
            bindings.append(value)
        return validate_publication(Publication(run_key, work, request, snapshot, cohort,
                                                results, tuple(bindings)))

    def read(self, run_key: str) -> Publication | None:
        _run_key(run_key)
        with self._lock:
            self._schema()
            return self._read(run_key)

    def commit(self, publication: Publication) -> CommitReceipt:
        publication = validate_publication(publication)
        digest = content_digest("results", publication.results)
        with self._lock:
            self._schema()
            self._connection.execute("BEGIN TRANSACTION")
            try:
                existing = self._read(publication.run_key)
                if existing is not None:
                    if existing != publication:
                        raise PublicationConflict("run_key content differs")
                    outcome = "already_committed"
                else:
                    self._connection.execute(
                        "INSERT INTO generations VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        [publication.run_key, publication.work_sha256,
                         publication.request_sha256, publication.snapshot_sha256,
                         publication.cohort_sha256, digest, len(publication.results), "committed"])
                    for ordinal, result in enumerate(publication.results):
                        self._connection.execute("INSERT INTO result_rows VALUES (?, ?, ?)",
                            [publication.run_key, ordinal, canonical_bytes(result).decode("utf-8")])
                    for binding in publication.bindings:
                        self._connection.execute("INSERT INTO source_bindings VALUES (?, ?, ?, ?)",
                            [publication.run_key, binding.binding_id,
                             record_digest("input_binding", binding),
                             canonical_bytes(binding).decode("utf-8")])
                    if self._read(publication.run_key) != publication:
                        raise StorageIntegrityError("transaction readback differs")
                    outcome = "committed"
                self._connection.execute("COMMIT")
            except BaseException:
                self._connection.execute("ROLLBACK")
                raise
            # A post-commit failure is deliberately observable for worker recovery.
            if self._read(publication.run_key) != publication:
                raise StorageIntegrityError("committed readback differs")
            return CommitReceipt(publication.run_key, publication.work_sha256, digest,
                                 len(publication.results), outcome, True)

    def close(self):
        with self._lock:
            self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.close()
