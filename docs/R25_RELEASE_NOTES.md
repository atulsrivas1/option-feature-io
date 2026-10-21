# R25 release notes — 0.1.0a1 candidate

**UNRELEASED; final qualification/acceptance pending.** No date/tag, registry publication or final platform pass is claimed. Final exact-artifact acceptance evidence is not yet published; follow [EQ187](https://github.com/atulsrivas1/equity-features/issues/532). Earlier cohort/component runs do not qualify later edits or rebuilt wheels.

## Scope and new APIs

`option-feature-io==0.1.0a1` adds strict `option-json1` snapshot/request/result encode/decode APIs, explicit synthetic canonical mapping conversion, immutable `Publication`/`CommitReceipt`, `ResultSink` and `DuckDBSink`. Bytes/nesting are bounded before parsing; duplicate keys/nonfinite constants fail; typed validation and canonical digest checks preserve identity.

Four closed option-generation1 tables in a separate output database provide atomic publication/full typed readback. Identical retries return `already_committed`; changed content under a reused key conflicts. Schema mismatch/corruption fail explicitly. No equity-database migration or cross-process writer service is delivered.

The adapter preserves distinct option/underlying identity, units, causal clocks and source/rights bindings. It does not fetch providers or infer completeness/timezone facts. Mathematics stays in pure features; workers own dispatch and artifact verification. See [API](R25_IO_API.md) and [synthetic example](../packages/io/examples/synthetic_roundtrip.py). Transport fixtures do not establish numerical correctness.

## Compatibility and limits

CPython `>=3.12,<3.13`. Project cohort versions: `option-feature-contracts==0.1.0a1`, `option-features==0.1.0a1`, `option-feature-io==0.1.0a1`, `option-feature-workers==0.1.0a1`. Exact numerical/storage backends are `python-flint==0.9.0` and `duckdb==1.5.6`; individual package direct dependencies are listed in the [README](../README.md). This is a compatibility cohort, not a claim that every layer directly depends on every package. Exact source/wheel hashes, complete inventory, interpreter patch and platform require qualification. Alpha labels do not promise a stable API.

Only batch snapshots/replay of independent snapshots are admitted; no incremental update/restore/merge. Supplied spot introduces no unused equity dependency; equity packages never import options. Fixed count/byte/scalar/Decimal/range/solver ceilings apply and callers may lower them. There is no hard RSS guarantee, throughput claim, private-score parity, real/provider dataset acceptance or production-service qualification.

## Validation and publication

Remaining final evidence includes independently reviewed wire-identical fixtures, exact-source rebuilt wheels/sdists and clean installation on each supported platform, actual direct/batch/replay/stored semantic parity, resource/retry/cancellation/tamper checks, native-license inventory and an inspected stored-output browser demo. Windows and Linux require separate runs and canonical-output comparison. Source review and historical component checks do not replace final receipts. Local builds/tests provide merge evidence; hosted CI is optional.

Install only retained locally qualified wheels with reviewed hashes/platform locks. Controlled build identity is established before wheel creation, not inferred from a source install. Own code is [Apache-2.0](../LICENSE); dependencies/native components retain separate licenses/notices requiring artifact-specific inventory. No data rights are granted. Public registry/package publication retains owner approval.

[Implementation PR](https://github.com/atulsrivas1/option-feature-io/pull/2), [R25 epic](https://github.com/atulsrivas1/equity-features/issues/526), [release page](https://github.com/atulsrivas1/option-feature-io/releases), [version policy](VERSIONING.md).
