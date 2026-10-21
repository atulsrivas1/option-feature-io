# Option feature I/O

Strict option-native transport, explicit synthetic input conversion and atomic DuckDB result storage. This layer converts and persists canonical records; mathematics belongs to [option-features](https://github.com/atulsrivas1/option-features).

**R25 / option-feature-io 0.1.0a1 is UNRELEASED and under qualification.** Final rebuilt artifacts, numerical fixtures, integration and an inspected stored-output browser demo remain release gates. No registry/provider dataset qualification is claimed. See [release notes](docs/R25_RELEASE_NOTES.md), [EQ185](https://github.com/atulsrivas1/equity-features/issues/530) and [R25 acceptance](https://github.com/atulsrivas1/equity-features/issues/532).

## Transport and storage

`option_feature_io` exports `encode_snapshot`, `encode_request`, `encode_results` and matching `decode_*` functions. Strict `option-json1` decoding bounds input bytes/nesting before parsing, rejects duplicate keys/nonfinite values, reconstructs closed records and verifies content identity. Whitespace/key ordering is not identity. Caller limits may lower fixed ceilings, including the 16 MiB envelope limit.

For an explicitly supplied original synthetic mapping:

```python
from option_feature_io import (
    decode_snapshot, encode_snapshot, snapshot_from_synthetic_mapping,
)

def roundtrip(payload, certification_reference):
    snapshot = snapshot_from_synthetic_mapping(
        payload, certification_reference=certification_reference,
    )
    return decode_snapshot(encode_snapshot(snapshot))
```

This follows the [synthetic example](packages/io/examples/synthetic_roundtrip.py). Callers supply canonical fields and matching rights/certification references. The adapter does not fetch observations or infer clocks, units, completeness or timezone facts. Synthetic completeness certifies only its declared toy universe; real source claims need independent qualification.

`DuckDBSink(destination)` opens an explicit separate output path, supports context management and creates four option-generation1 tables only in an empty target. Existing destinations must match its closed schema. `commit(Publication(...))` performs atomic write/full typed readback; identical retries return `already_committed`, changed content under a reused key raises `PublicationConflict`. `read(run_key)` returns the publication or `None`; corrupt storage raises `StorageIntegrityError`. Recovery after an exception requires full matching committed readback. See the [I/O API](docs/R25_IO_API.md).

The sink has one owner and one DuckDB thread, without a hard native-memory claim. It does not migrate equity databases or provide cross-process writer coordination. Inputs stay separate from generated outputs. Distinct option/underlying IDs and contract/underlying quantities remain explicit; closed equity codecs are not silently extended.

## Installation and boundaries

CPython `>=3.12,<3.13`; exact dependencies `option-feature-contracts==0.1.0a1` and `duckdb==1.5.6`. I/O does not depend on numerical features; workers compose conversion, pure evaluation and storage. R25 supports batch snapshots/independent replay, not update/restore/merge. No unused equity dependency is added; equity packages never import options.

Install reviewed locally qualified wheels with hashes and a clean runtime. Replace placeholders with actual qualification artifacts:

```text
python -m pip --python <clean-runtime-python> install --no-index --find-links <qualified-wheelhouse> --require-hashes --no-compile -r <reviewed-platform-lock.txt>
```

No PyPI availability is implied. Controlled staging supplies project build identities before wheel creation; source/editable installs alone do not establish them. Worker composition requires the complete reviewed cohort and fresh no-bytecode `python -B` runtime described in the [verification API](https://github.com/atulsrivas1/option-feature-workers/blob/codex/r25-worker-implementation/docs/API.md).

[Implementation PR](https://github.com/atulsrivas1/option-feature-io/pull/2), [releases](https://github.com/atulsrivas1/option-feature-io/releases), [R25 epic](https://github.com/atulsrivas1/equity-features/issues/526), [version policy](docs/VERSIONING.md), [handoff](docs/SESSION_HANDOFF.md), [work agreements](AGENTS.md).

Own code is [Apache-2.0](LICENSE). DuckDB/native dependencies retain separate licenses/notices requiring artifact-specific qualification. Code licensing grants no source-data rights.
