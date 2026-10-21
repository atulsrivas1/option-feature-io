# R25 native I/O source candidate

EQ185 implementation source targets frozen contract commit
`9403854ff37a7c0b5dbc57c142893a1ce0a262e4`. Package source lives in
`packages/io`; distribution `option-feature-io==0.1.0a1` targets Python3.12,
`option-feature-contracts==0.1.0a1` and `duckdb==1.5.6`. These are exact candidate
dependencies, not registry availability, installed-artifact or platform claims.

`encode_snapshot`, `encode_request`, `encode_results` and corresponding
`decode_*` functions transport strict option-json1 bytes. Decoders check caller
limits and byte size before JSON parsing, reject BOM, duplicate keys, unknown
envelope fields, nonfinite constants and excessive nesting; pure contract
helpers reconstruct closed records, validate canonical Decimals and recompute
content identity. Encoders use bounded canonical payload helpers and enforce
the full envelope byte ceiling. JSON key order/whitespace is not identity.

`snapshot_from_synthetic_mapping(payload, certification_reference=...)` accepts
an explicitly authored canonical mapping with synthetic source bindings. It
does not fetch a source, infer missing clocks, generate completeness from
observations, convert quote scale, certify licensed/provider coverage or invent
timezone facts. Caller certification must match each synthetic binding's
original rights reference. Completeness/profile certification remains an
explicit source claim, whose truth needs source qualification independently.

`DuckDBSink(destination)` opens a caller-selected separate option database.
Use it as a context manager or call `close()`. It creates the four native
option-generation1 tables only in an empty target; existing destinations must
match table names, types, columns, nullability, defaults, primary keys and
version. Additional tables/views/explicit indexes/sequences are rejected.
It never migrates an equity database. This is a single-owner sink, not a
cross-process writer service. Its connection explicitly selects one DuckDB
thread. This is a native thread configuration, not a hard RSS/native-memory
bound; no memory-performance qualification is claimed. SQL parameters bind all
caller data.

`commit(Publication(...))` validates result/request/snapshot identities and
dependency bindings, writes one atomic transaction, reconstructs typed content
before commit and verifies readback after commit. Identical complete content
returns `already_committed`; a changed value, binding or summary hash using
the same key raises `PublicationConflict`. `read(run_key)` returns the complete
immutable publication or `None` for an absent generation. Corrupt committed
rows, gaps, digest mismatches and orphan rows raise `StorageIntegrityError`.
Summary hashes cannot independently verify an installed artifact cohort;
worker verification remains required.

Publication binding order is canonicalized by binding ID; result order is
semantic and preserved. `validate_publication` exposes that normalization for
worker recovery comparisons. Returned receipts truthfully distinguish
`committed` and `already_committed`, and require full readback verification.
An exception after actual commit remains an exception; the worker may recover
only by verified matching readback.

The original `unittest` sources cover an independently written golden payload,
malformed wire, canonical decimal rejection, typed constructed results,
schema retention, rollback injection, identical retries, changed-content
conflicts and tamper detection. Constructed results are transport fixtures and
do not establish numerical correctness. All runtime tests/builds/installs and
database operations remain UNEXECUTED under the EQ142 resource hold.

After the coordinator confirms the resource gate is clear, planned local
commands from repository root are:

```powershell
python -m pip install <qualified-contracts-wheel> <qualified-duckdb-wheel> <built-io-wheel>
python -m unittest discover -s packages/io/tests -v
```

Build/install records must capture exact source commit, wheel SHA256, Python,
OS and results. Controlled build staging supplies `_build_identity.json` with
the actual reviewed source commit; no invented marker is checked in. A local
Windows result cannot prove Linux support. EQ187 additionally requires actual
computed results through direct/worker/stored paths and a stored browser demo.
