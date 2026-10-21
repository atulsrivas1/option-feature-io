## Current R25 qualification handoff — October 21, 2026

See the library [current qualification report](https://github.com/atulsrivas1/option-features/blob/codex/r25-qualification-evidence/docs/R25_LOCAL_QUALIFICATION.md) and [public component evidence](https://github.com/atulsrivas1/equity-features/issues/526#issuecomment-6308022775). The earlier I/O attempt-01 failure below is retained; later exact-source rebuilt qualification supersedes it.

The original EQ142 exclusive hold was explicitly released after actual-state reconciliation; the original study remains unknown/unaccepted and its ownership is preserved. Bounded R25 local work is admitted. Historical hold/unexecuted/push restrictions below describe their dated source checkpoints, not current execution authority.

Exact qualified sources: library `60aed608b2020764bff40d4cdfa434abbc2bde03`, I/O `d893272f94e0967cc4a0ff965798a3e06439ad5f`, workers `153b73464e67d12d0e859b2061ded3c0c361b040`. Windows attempt-03 (CPython 3.12.10) and Ubuntu 24.04/WSL Linux attempt-20261021-c (CPython 3.12.3) each passed 216 methods across original-wheel and original-sdist-rebuilt-wheel forms, with clean pip-free runtimes and no failures/errors/skips. These include the independently reviewed 111-case/378-row fixture plus 5 structural errors; see the report for counts, hashes and evidence limitations.

All four artifact cohorts received coordinator source/native/license admission. Final-wheel tamper checks passed on both platforms: Windows verified 253 files, Linux 207, each computed before rejecting seven separate next-execute mutations. Additional layer-isolation checks passed 172 methods per platform across six fresh pip-free environments (contracts only, features closure and I/O closure, each in both artifact forms), with exact closure inventory and absent unselected layers checked. The first Linux isolation harness aborted before tests on an inappropriate full-cohort origin requirement; a freshly reviewed corrected v2 helper passed without changing production packages. All four frozen five-scenario integration harnesses passed. Broad golden 111-case batch/replay integration passed both Linux forms and Windows original wheels; Windows rebuilt-sdist broad golden integration remains running and mandatory. Fresh separately reviewed direct/stored comparison additionally established byte-identical full payloads for all 111 cases/378 rows in Linux original/rebuilt and Windows original cohorts, binding completed commits and freshly verifying cohorts. Windows rebuilt-sdist full payload parity is pending; expected-subset integration and independent-oracle proof remain distinct. Both portable v2 platform bundles passed fresh-download/two-form installation/verifier/five-scenario checks. Final documentation-only wrapper review is pending. The coordinator actually inspected five stored-output browser tables/45 rows and a supplemental all-14-output price/IV round trip; full Result parity is integration evidence, not an independent oracle. See the report for bundle hashes, externally trusted manifests and numeric round-trip details.

Source PRs are merged with entire source trees equal to qualified trees. Six source stories remain Test; EQ187 is In progress. R25 remains UNRELEASED, with registry/package publication requiring owner approval. Next: finish Windows rebuilt-sdist broad integration, final byte comparison and wrapper review, reconcile exact source/review/local evidence and evaluate EQ187 acceptance. Package/build inputs and test sources remain unchanged by this documentation-only reconciliation; source commit labels of already built artifacts are not rewritten.

## Historical handoff records

## Owner clarification: local merge evidence — October 20, 2026

The owner reaffirmed that local builds and local test runs provide merge validation. This supersedes older mandatory hosted-CI wording: GitHub Actions completion is not an acceptance or merge prerequisite. Retain independent review, appropriate exact-commit local checks, build/install evidence where applicable, numerical fixtures and integration/release gates. Documentation-only changes use relevant local source/document checks; do not invent package builds for them. Record actual commands, source commit, environment and results. Do not claim unexecuted local checks or infer validation of another platform from a local run. Any actual repository protection conflict must be reported separately; it does not redefine this agreement. Existing ownership/resource reservations remain protected.

# R25 preparation handoff

## Windows attempt-01 failure and corrective candidate

The coordinator's actual Windows qualification attempt-01 ran the installed
I/O wheel from source `9b598762433b9432e5cc338db4994f057378c74d`:
22 tests passed and one errored. This attempt FAILED. The original
`test_request_roundtrip_and_raised_decoder_limits` exposed `_decode` catching
the structural `ContractValidationError` from caller limit admission and
relabeling it as invalid JSON. Contracts/features test results are separately
owned coordinator evidence and are not inferred from this I/O report.

The corrective source candidate moves byte/text/limit preflight before the
JSON parser's exception-conversion block, preserving structural admission
errors before malformed payload parsing. The original failing test is retained
unchanged. A new authored regression checks every decoder with raised byte
limits and zero record limits, asserting the structural code/path. There are
now24 test definitions. This corrective candidate has not been runtime-tested
or rebuilt; attempt-01 remains historical failing evidence. No qualification
environment or receipt was modified. Coordinator and fresh independent review
precede push; the coordinator owns rebuilding/retesting the next exact head.

Source-only corrective checks: Windows PowerShell/Python3.12.10 `ast.parse`
over all ten Python source/test/example files and `git diff --check` pass.

## EQ185 source authoring checkpoint

Fresh layer author `/root/r25_io_implementation` started actual source work on
`codex/r25-io-implementation` against frozen contracts
`9403854ff37a7c0b5dbc57c142893a1ce0a262e4`. Source candidate now includes the
native package, strict codec, explicit synthetic mapping adapter, separate
single-owner transactional DuckDB sink and original unexecuted test sources.
See [API and validation limits](R25_IO_API.md). Existing equity schemas and
code were not edited. This source is uncommitted pending coordinator actual
diff review; no push is authorized yet.

The EQ142 exclusive resource hold is retained. No package imports, runtime
tests, numerical generator, typechecker, build, installation, database action,
benchmark or real-data access has run. Text/AST/whitespace checks establish
source syntax only; independent PR review and exact-source local runtime,
build/install, numerical/integration/platform and release gates remain open.
Next: coordinator review actual source, reconcile contracts helper exports,
resolve findings, then obtain fresh independent PR review and run appropriate
local validation only after the existing resource hold is explicitly clear.

Actual source-only checks on the uncommitted working tree based on
`ba3d015250ab6630d536126c757806bf8a06efe5`: Windows PowerShell,
Python3.12.10; `ast.parse` over all ten package/example/test Python files
succeeded, `tomllib.load` parsed the package metadata, and `git diff --check`
returned zero. After coordinator source review, stored JSON now uses the same
bounded strict preparse checks as transport, wrapping corrupt nesting as typed
`StorageIntegrityError`; run keys reject all Unicode Cc controls and unpaired
surrogates with consistent `ValueError`. Fresh independent review also found
retry paths bypassing public read's typed-error conversion. Conversion is now
centralized in `_read` for public reads and every transaction/retry/readback;
a well-formed but inconsistent stored request hash has an authored regression.
The exact setuptools build pin is now80.9.0 to support SPDX metadata, with
package-local original Apache LICENSE and explicit license-files inclusion;
controlled `_build_identity.json` package-data inclusion remains configured.
AST inspection now counts twenty-three test definitions; none ran. Source-only
TOML and byte-equality checks verified the backend/license configuration.
Worker integration source review additionally identified the native-thread
setting: the DuckDB connection now explicitly selects `threads=1`, matching
the frozen single-worker profile without claiming a hard native-memory bound.
An authored, unexecuted test queries `current_setting('threads')` to verify the
actual native setting after future resource clearance.
These checks do not validate package imports, DuckDB SQL behavior or numerical
results. Exact-commit execution evidence must be recorded after review/commit
and resource clearance rather than inferred from this uncommitted source pass.

October 20, 2026. Owner selected first option release and dedicated repository homes. option-feature-io owns: Convert supplied or qualified external facts into option-owned canonical records and persist canonical results. Keep contract quantities and distinct option/underlying identities. Existing equity codecs/sinks are closed and are not assumed compatible.

Historical initial baseline: documentation/licensing/work agreements only, with no source package, tests, numerical fixture execution, CI workflow or database. The subsequent contract draft adds a lightweight documentation CI workflow; its presence or success does not establish numerical or installed compatibility. The coordinator prepares reviewed canonical option and cross-layer contracts under GOV037 #581. Existing equity quantity units, result codecs, sink schemas and worker identity admission are incompatible with native option facts without a reviewed extension.

Current owner decision (October 20, 2026): R25 may proceed independently of the former blanket R18/EQ146 and EQ143/EQ144 delivery prerequisites. R17/EQ141 remains the accepted reference; R18 status and active ownership are unchanged. R25 must review and freeze its own contracts/interface choices, qualify its selected exact artifacts and executor/resource behavior, and pass independent numerical, cross-platform and integrated release gates. None of those gates is claimed passed here.

Next: inspect canonical #581 and the revised coordinator agreement; resolve and independently review the concrete R25 contracts and named scopes; pin reviewed contracts before fresh implementation workers. Keep exact artifact/platform qualification under EQ187 and execution/resource qualification under EQ186, with EQ185 responsible for transport/storage conformance. Preserve any current EF1/R18 owner and reserved resource window. Do not claim Ready, numerical parity, installed compatibility, benchmark or release acceptance from these documents.
