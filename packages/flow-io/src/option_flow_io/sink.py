"""Separate five-table flow store, serialized transactions and complete readback."""
from hashlib import sha256
import json
import re
from threading import RLock

import duckdb
from option_flow_contracts import (
    FLOW_LIMITS, FlowPublication, FlowValidationError, flow_canonical_bytes,
    encode_flow_publication, flow_from_payload, flow_record_digest, flow_to_payload,
)

from .errors import PublicationConflict, StorageIntegrityError, StorageSchemaError
from .publication import FlowCommitReceipt

_VERSION = "option-flow-generation1"
_KEYS = {"flow_schema": ("version",), "flow_generations": ("run_key",),
         "flow_result_rows": ("run_key", "ordinal"),
         "flow_bindings": ("run_key", "binding_id"), "flow_checkpoints": ("run_key",)}
_TABLES = {
    "flow_schema": (("version", "VARCHAR"),),
    "flow_generations": tuple((name, "VARCHAR") for name in (
        "run_key", "work_sha256", "request_sha256", "snapshot_sha256", "cohort_sha256",
        "input_checkpoint_sha256", "results_sha256", "bindings_sha256",
        "output_checkpoint_sha256", "publication_sha256")) + (
            ("result_count", "BIGINT"), ("binding_count", "BIGINT"),
            ("canonical_publication", "VARCHAR"), ("state", "VARCHAR")),
    "flow_result_rows": (("run_key", "VARCHAR"), ("ordinal", "BIGINT"),
                         ("record_sha256", "VARCHAR"), ("canonical_json", "VARCHAR")),
    "flow_bindings": (("run_key", "VARCHAR"), ("binding_id", "VARCHAR"),
                      ("record_sha256", "VARCHAR"), ("canonical_json", "VARCHAR")),
    "flow_checkpoints": (("run_key", "VARCHAR"), ("record_sha256", "VARCHAR"),
                         ("canonical_json", "VARCHAR")),
}
_NULLABLE = {("flow_generations", "input_checkpoint_sha256"),
             ("flow_generations", "output_checkpoint_sha256")}
_CREATE = tuple(
    "CREATE TABLE " + table + "(" + ",".join(
        name + " " + kind + ("" if (table, name) in _NULLABLE else " NOT NULL")
        for name, kind in columns) + ", PRIMARY KEY(" + ",".join(_KEYS[table]) + "))"
    for table, columns in _TABLES.items())


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _binding_digest(bindings):
    payload = [flow_to_payload(item) for item in sorted(bindings, key=lambda b: b.binding_id)]
    return sha256(b"option-flow-bindings1\n" + _json(payload)).hexdigest()


def _pairs(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            raise StorageIntegrityError("duplicate stored JSON key")
        output[key] = value
    return output


def _load(kind, text):
    if type(text) is not str or len(text.encode("utf-8")) > FLOW_LIMITS.max_wire_bytes:
        raise StorageIntegrityError("stored canonical value exceeds bounds")
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
            if depth > 32:
                raise StorageIntegrityError("stored JSON nesting exceeds bounds")
        elif char in "]}":
            depth -= 1
    def reject(_):
        raise StorageIntegrityError("noninteger stored JSON number")
    payload = json.loads(text, object_pairs_hook=_pairs, parse_float=reject,
                         parse_constant=reject)
    value = flow_from_payload(kind, payload)
    if flow_canonical_bytes(value) != text.encode("utf-8"):
        raise StorageIntegrityError("noncanonical stored value")
    return value


def _publication(value):
    # Payload reconstruction alone checks shape/local fields, not full semantic
    # coherence. The public encoder calls the contracts' complete publication,
    # result/request and checkpoint validators before any storage transaction.
    if type(value) is not FlowPublication:
        raise FlowValidationError("type_mismatch", "/publication")
    encode_flow_publication(value)
    canonical = flow_canonical_bytes(value)
    checked = flow_from_payload("flow_publication", json.loads(canonical))
    if flow_canonical_bytes(checked) != canonical:
        raise FlowValidationError("noncanonical", "/publication")
    if flow_record_digest("flow_request", value.request) != value.request_sha256:
        raise FlowValidationError("digest_mismatch", "/request_sha256")
    expected_work = sha256(b"option-flow-work1\n" + _json([
        value.snapshot_sha256, value.request_sha256, value.cohort_sha256,
        value.input_checkpoint_sha256])).hexdigest()
    if value.work_sha256 != expected_work:
        raise FlowValidationError("digest_mismatch", "/work_sha256")
    if not value.results and not set(value.request.output_ids).issubset({
            "execution.cluster_premium", "execution.cluster_trade_count",
            "execution.cluster_contracts", "execution.cluster_span_ns", "execution.cluster_venue_count"}):
        raise FlowValidationError("identity_mismatch", "/results")
    binding_ids = tuple(binding.binding_id for binding in value.bindings)
    if binding_ids != tuple(sorted(set(binding_ids))):
        raise FlowValidationError("identity_conflict", "/bindings")
    for index, result in enumerate(value.results):
        for field, expected in (("request_sha256", value.request_sha256),
                                ("snapshot_sha256", value.snapshot_sha256),
                                ("checkpoint_sha256", value.input_checkpoint_sha256)):
            if getattr(result, field) != expected:
                raise FlowValidationError("identity_mismatch", f"/results/{index}/{field}")
        if not set(result.dependency_binding_ids).issubset(binding_ids):
            raise FlowValidationError("missing_identity", f"/results/{index}/dependency_binding_ids")
        if result.group_id not in value.request.group_ids or result.output_id not in value.request.output_ids:
            raise FlowValidationError("identity_mismatch", f"/results/{index}")
        for field in ("window_start_ns", "window_end_ns", "knowledge_cutoff_ns", "formula_version"):
            if getattr(result, field) != getattr(value.request, field):
                raise FlowValidationError("identity_mismatch", f"/results/{index}/{field}")
        if result.policy_sha256 != flow_record_digest("flow_policy", value.request.policy):
            raise FlowValidationError("digest_mismatch", f"/results/{index}/policy_sha256")
    if value.output_checkpoint is not None:
        checkpoint = value.output_checkpoint
        if flow_canonical_bytes(checkpoint.prior_request) != flow_canonical_bytes(value.request):
            raise FlowValidationError("identity_mismatch", "/output_checkpoint/prior_request")
        if checkpoint.history_sha256 != value.snapshot_sha256:
            raise FlowValidationError("digest_mismatch", "/output_checkpoint/history_sha256")
        actual = {binding.binding_id: flow_canonical_bytes(binding) for binding in value.bindings}
        for binding in checkpoint.history.bindings:
            if actual.get(binding.binding_id) != flow_canonical_bytes(binding):
                raise FlowValidationError("missing_identity", "/output_checkpoint/history/bindings")
    return canonical


def _metadata(publication):
    checkpoint = publication.output_checkpoint
    return (
        publication.run_key, publication.work_sha256, publication.request_sha256,
        publication.snapshot_sha256, publication.cohort_sha256,
        publication.input_checkpoint_sha256,
        flow_record_digest("flow_results", publication.results),
        _binding_digest(publication.bindings),
        None if checkpoint is None else flow_record_digest("flow_checkpoint", checkpoint),
        flow_record_digest("flow_publication", publication),
        len(publication.results), len(publication.bindings),
        flow_canonical_bytes(publication).decode("utf-8"), "committed")


class FlowDuckDBSink:
    """One owned connection. No user SQL, migration or multiwriter API."""
    def __init__(self, destination: str):
        if type(destination) is not str or not destination or "\0" in destination:
            raise ValueError("destination must be an explicit database path")
        self._lock = RLock()
        self._closed = False
        self._connection = duckdb.connect(destination, config={"threads": "1"})
        try:
            self._connection.execute("BEGIN TRANSACTION")
            try:
                if not self._objects():
                    self._reject_other_objects()
                    for statement in _CREATE:
                        self._connection.execute(statement)
                    self._connection.execute("INSERT INTO flow_schema VALUES (?)", [_VERSION])
                self._schema()
                self._orphans()
                self._connection.execute("COMMIT")
            except BaseException:
                self._connection.execute("ROLLBACK")
                raise
        except BaseException:
            self._connection.close()
            self._closed = True
            raise

    def _objects(self):
        return self._connection.execute(
            "SELECT table_schema,table_name,table_type FROM information_schema.tables "
            "WHERE table_schema NOT IN ('information_schema','pg_catalog') "
            "ORDER BY table_schema,table_name").fetchall()

    def _reject_other_objects(self):
        for query in (
            "SELECT count(*) FROM duckdb_indexes()",
            "SELECT count(*) FROM duckdb_sequences()",
            "SELECT count(*) FROM duckdb_schemas() WHERE NOT internal AND schema_name <> 'main'",
            "SELECT count(*) FROM duckdb_functions() WHERE NOT internal",
        ):
            if self._connection.execute(query).fetchone()[0]:
                raise StorageSchemaError("unexpected user-defined database object")

    def _schema(self):
        if self._objects() != sorted(("main", name, "BASE TABLE") for name in _TABLES):
            raise StorageSchemaError("unexpected table/view/schema")
        self._reject_other_objects()
        for table, columns in _TABLES.items():
            actual = self._connection.execute(
                "SELECT column_name,data_type,is_nullable,column_default "
                "FROM information_schema.columns WHERE table_schema='main' AND table_name=? "
                "ORDER BY ordinal_position", [table]).fetchall()
            expected = [(name, kind, "YES" if (table, name) in _NULLABLE else "NO", None)
                        for name, kind in columns]
            if actual != expected:
                raise StorageSchemaError("column shape/nullability/default mismatch: " + table)
        constraints = self._connection.execute(
            "SELECT table_name,constraint_type,constraint_column_names "
            "FROM duckdb_constraints() WHERE schema_name='main'").fetchall()
        primary = {}
        for table, kind, columns in constraints:
            if kind == "PRIMARY KEY" and table not in primary:
                primary[table] = tuple(columns)
            elif kind == "NOT NULL" and all(
                    (table, column) not in _NULLABLE and
                    column in dict(_TABLES.get(table, ())) for column in columns):
                continue
            else:
                raise StorageSchemaError("unexpected or duplicate constraint")
        if primary != _KEYS:
            raise StorageSchemaError("primary key mismatch")
        if self._connection.execute("SELECT version FROM flow_schema").fetchall() != [(_VERSION,)]:
            raise StorageSchemaError("storage version mismatch")

    def _orphans(self):
        for table in ("flow_result_rows", "flow_bindings", "flow_checkpoints"):
            count = self._connection.execute(
                "SELECT count(*) FROM " + table + " r LEFT JOIN flow_generations g "
                "ON r.run_key=g.run_key WHERE g.run_key IS NULL").fetchone()[0]
            if count:
                raise StorageIntegrityError("orphaned publication row")

    def _ensure_open(self):
        if self._closed:
            raise RuntimeError("flow sink is closed")

    def _read(self, run_key):
        try:
            return self._read_content(run_key)
        except (StorageIntegrityError, StorageSchemaError):
            raise
        except (FlowValidationError, ValueError, TypeError, KeyError, RecursionError) as exc:
            raise StorageIntegrityError("invalid stored typed content") from exc

    def _read_content(self, run_key):
        # Check storage allocation bounds before bringing canonical strings into Python.
        for table, field in (("flow_generations", "canonical_publication"),
                             ("flow_result_rows", "canonical_json"),
                             ("flow_bindings", "canonical_json"),
                             ("flow_checkpoints", "canonical_json")):
            size = self._connection.execute(
                "SELECT coalesce(sum(octet_length(encode(" + field + "))),0) FROM " +
                table + " WHERE run_key=?", [run_key]).fetchone()[0]
            if size > FLOW_LIMITS.max_wire_bytes:
                raise StorageIntegrityError("stored generation exceeds canonical byte bounds")
        rows = self._connection.execute(
            "SELECT * FROM flow_generations WHERE run_key=?", [run_key]).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise StorageIntegrityError("ambiguous generation")
        row = rows[0]
        publication = _load("flow_publication", row[12])
        _publication(publication)
        if row != _metadata(publication) or publication.run_key != run_key:
            raise StorageIntegrityError("generation metadata disagreement")
        result_rows = self._connection.execute(
            "SELECT ordinal,record_sha256,canonical_json FROM flow_result_rows "
            "WHERE run_key=? ORDER BY ordinal LIMIT 8193", [run_key]).fetchall()
        expected_results = [(index, flow_record_digest("flow_result", result),
                             flow_canonical_bytes(result).decode("utf-8"))
                            for index, result in enumerate(publication.results)]
        if result_rows != expected_results:
            raise StorageIntegrityError("result rows differ from complete publication")
        for _, digest, text in result_rows:
            if flow_record_digest("flow_result", _load("flow_result", text)) != digest:
                raise StorageIntegrityError("result digest mismatch")
        binding_rows = self._connection.execute(
            "SELECT binding_id,record_sha256,canonical_json FROM flow_bindings "
            "WHERE run_key=? ORDER BY binding_id LIMIT 100001", [run_key]).fetchall()
        expected_bindings = [(binding.binding_id, flow_record_digest("flow_binding", binding),
                              flow_canonical_bytes(binding).decode("utf-8"))
                             for binding in publication.bindings]
        if binding_rows != expected_bindings:
            raise StorageIntegrityError("binding rows differ from complete publication")
        for binding_id, digest, text in binding_rows:
            binding = _load("flow_binding", text)
            if binding.binding_id != binding_id or flow_record_digest("flow_binding", binding) != digest:
                raise StorageIntegrityError("binding digest/identity mismatch")
        checkpoints = self._connection.execute(
            "SELECT record_sha256,canonical_json FROM flow_checkpoints WHERE run_key=?",
            [run_key]).fetchall()
        expected_checkpoint = [] if publication.output_checkpoint is None else [(
            flow_record_digest("flow_checkpoint", publication.output_checkpoint),
            flow_canonical_bytes(publication.output_checkpoint).decode("utf-8"))]
        if checkpoints != expected_checkpoint:
            raise StorageIntegrityError("checkpoint rows differ from complete publication")
        for digest, text in checkpoints:
            if flow_record_digest("flow_checkpoint", _load("flow_checkpoint", text)) != digest:
                raise StorageIntegrityError("checkpoint digest mismatch")
        return publication

    def read(self, run_key):
        if type(run_key) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}", run_key) is None:
            raise FlowValidationError("invalid_scalar", "/run_key")
        with self._lock:
            self._ensure_open()
            self._connection.execute("BEGIN TRANSACTION")
            try:
                self._schema()
                self._orphans()
                value = self._read(run_key)
                self._connection.execute("COMMIT")
                return value
            except BaseException:
                self._connection.execute("ROLLBACK")
                raise

    def _commit_transaction(self):
        """Internal fault-injection seam; no user callback/API is admitted."""
        self._connection.execute("COMMIT")

    def _receipt(self, publication, outcome):
        meta = _metadata(publication)
        return FlowCommitReceipt(publication.run_key, publication.work_sha256,
                                 meta[9], meta[6], meta[8], len(publication.results),
                                 outcome, True)

    def publish(self, publication):
        canonical = _publication(publication)
        with self._lock:
            self._ensure_open()
            self._connection.execute("BEGIN TRANSACTION")
            commit_started = False
            try:
                self._schema()
                self._orphans()
                previous = self._read(publication.run_key)
                if previous is not None:
                    if flow_canonical_bytes(previous) != canonical:
                        raise PublicationConflict("run key already binds a different publication")
                    self._connection.execute("COMMIT")
                    return self._receipt(publication, "already_committed")
                meta = _metadata(publication)
                self._connection.execute(
                    "INSERT INTO flow_generations VALUES (" + ",".join("?" for _ in meta) + ")", meta)
                for index, result in enumerate(publication.results):
                    self._connection.execute("INSERT INTO flow_result_rows VALUES (?,?,?,?)", (
                        publication.run_key, index, flow_record_digest("flow_result", result),
                        flow_canonical_bytes(result).decode("utf-8")))
                for binding in publication.bindings:
                    self._connection.execute("INSERT INTO flow_bindings VALUES (?,?,?,?)", (
                        publication.run_key, binding.binding_id,
                        flow_record_digest("flow_binding", binding),
                        flow_canonical_bytes(binding).decode("utf-8")))
                if publication.output_checkpoint is not None:
                    self._connection.execute("INSERT INTO flow_checkpoints VALUES (?,?,?)", (
                        publication.run_key, meta[8],
                        flow_canonical_bytes(publication.output_checkpoint).decode("utf-8")))
                commit_started = True
                self._commit_transaction()
            except BaseException:
                if not commit_started:
                    self._connection.execute("ROLLBACK")
                    raise
                # A raised commit acknowledgement may describe either committed
                # output or a still-open transaction. Rollback only an uncommitted
                # transaction; it cannot erase a successful commit.
                try:
                    self._connection.execute("ROLLBACK")
                except duckdb.TransactionException:
                    pass
                recovered = self.read(publication.run_key)
                if recovered is None:
                    raise
                if flow_canonical_bytes(recovered) != canonical:
                    raise PublicationConflict("uncertain commit recovered changed generation")
                return self._receipt(publication, "committed")
            readback = self.read(publication.run_key)
            if readback is None or flow_canonical_bytes(readback) != canonical:
                raise StorageIntegrityError("committed generation failed complete readback")
            return self._receipt(publication, "committed")

    def close(self):
        with self._lock:
            if not self._closed:
                self._connection.close()
                self._closed = True

    def __enter__(self):
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
