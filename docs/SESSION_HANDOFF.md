## Owner clarification: local merge evidence — October 20, 2026

The owner reaffirmed that local builds and local test runs provide merge validation. This supersedes older mandatory hosted-CI wording: GitHub Actions completion is not an acceptance or merge prerequisite. Retain independent review, appropriate exact-commit local checks, build/install evidence where applicable, numerical fixtures and integration/release gates. Documentation-only changes use relevant local source/document checks; do not invent package builds for them. Record actual commands, source commit, environment and results. Do not claim unexecuted local checks or infer validation of another platform from a local run. Any actual repository protection conflict must be reported separately; it does not redefine this agreement. Existing ownership/resource reservations remain protected.

# R25 preparation handoff

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
