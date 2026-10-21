# R26 flow I/O implementation checkpoint

Source author: `/root/r26_native_io_implementation`, October 21, 2026.
Story: [EQ191 #537](https://github.com/atulsrivas1/equity-features/issues/537).
Branch: `codex/r26-flow-io`, actual clean starting source
`244ed1cea07fd0b5a497677a7d9755332f0d8e6a`.
The coordinator granted source authoring against the independently reviewed
library contract source `d1fce33945832c78ea039efd41408564a8d382c2`, merged
as `f78e9c26a298b213fb54c129e09546e2744d7530`, tree
`8918dc707ab5c9dd5cbc9ee513e3b048eef3dc1c`.

The new optional `option-flow-io==0.1.0a1` distribution lives in
`packages/flow-io`, imports as `option_flow_io`, and pins
`option-flow-contracts==0.1.0a1` and `duckdb==1.5.6`. It imports no R25
package. Existing R25 source, manifests, tests, tools and artifacts are untouched.

`SyntheticFlowAdapter(mapping_bytes).load()` delegates to the new contracts'
closed strict canonical snapshot decoder, rejects nonsynthetic source bindings,
and exposes `adapter.receipt` after successful loading. The receipt binds the
actual wire SHA256, snapshot record digest and byte count; deduplication is zero
for this strict canonical format. It supplies no missing market facts and reads
no external source. The I/O namespace reexports the frozen flow codec APIs;
their implementation remains in the pure contracts package.

`FlowDuckDBSink(destination)` owns a serialized connection configured with one
DuckDB thread. It transactionally initializes only an empty separate database,
then checks exact five-table order/types/nullability/defaults/primary keys,
version, and absence of extra tables, views, indexes, sequences, schemas or user
functions. It refuses source/R25 stores and performs no migrations. Canonical
publications, each result, each binding and the optional full checkpoint are
written in one transaction. Every read/retry verifies full metadata, canonical
bytes, domain hashes, counts, ordinal continuity, identities and absence of
orphan rows. Successful commits perform complete readback. Changed publications
under one run key conflict; retries preserve committed output. An internal
commit seam permits tests of a lost acknowledgement both before and after a
real commit. Recovery reads the expected complete generation before issuing a
verified receipt. No cancellation callback is admitted in the sink; the worker
owns cancellation before entering publication and finishes recovery after entry.

The sink checks request, work, result input, policy, group/output and checkpoint
hash/record consistency. It does not establish numerical derivation or independently
prove an empty cluster population. Those remain worker and independent fixture
qualification responsibilities. Literal storage fixtures exercise persistence;
they are not claimed as independent evaluator expectations.

## Historical initial validation and independent review correction

The coordinator actually executed `python -B -m unittest discover -s
tests/flow_io -v` under the serialized `R26-IO-DEVELOPMENT-01` lease on Windows,
CPython 3.12.10 and DuckDB 1.5.6. The original 23 tests passed in 8.913 seconds
(9.657 seconds command elapsed); the private run receipt records identical source
hashes before/after. This was a development source run, not installed-artifact,
Linux, independent numerical or final release evidence.

Fresh independent source reviewer `/root/r26_native_io_independent_review`
subsequently found a P1 defect: payload reconstruction checks structural/local
fields and did not invoke the complete semantic publication validator. The sink
could admit a result with the wrong output unit or incoherent status/value, or a
checkpoint whose claimed hashes did not attest its actual history/request/policy.
The historical passing run remains valid for its old source but does not establish
conformance of the corrected source.

The correction calls the public semantic `encode_flow_publication` boundary before
each write and through the same validation path during stored readback. This
invokes full result/request and checkpoint validation while retaining the sink's
additional window/policy/binding/content checks. Eight new regression methods
cover malformed result unit/status/value, forged checkpoint history/request/policy,
semantically invalid history with freshly rebound digests, and corrupted stored
result/checkpoint packets with consistently rebound row/metadata hashes. Rehashed
storage is tested as a semantic attack, rather than merely a hash mismatch.

## Closure fixture correction and validation chronology

The later coordinator development closure `R26-IO-DEV03` executed 31 methods:
28 passed and three errored during adversarial fixture construction (16.846
seconds unittest time; 17.608 seconds command elapsed). The strengthened public
contracts correctly rejected invalid history, a forged checkpoint policy hash
and a wrong result unit while the test attempted to serialize/hash those invalid
fixtures. These errors occurred before the intended sink assertions and did not
demonstrate a new production defect. The failed closure is retained; it is not a
passing run of 31 methods.

The narrow test correction starts from valid canonical payloads, mutates explicit
JSON fields, and independently renders/hashes the intentionally malicious bytes
using the frozen record domain. It rebinds the affected stored row and generation
metadata without calling a validating codec or the production metadata builder
on malformed input. Positive controls verify the independent hash matches the
public digest on the unmodified valid input and successfully publish the valid
generation before storage corruption. Only those three adversarial fixture
builders and their test-only byte/hash helpers changed. Production validation and
all other positive/negative tests are preserved. At the author checkpoint this fixture correction had
received AST/whitespace checks only; the later actual closure run is below.

Windows PowerShell with Python 3.12.10: source-only `ast.parse` over all six new
Python source/test files passes. Thirty-one unittest methods are authored,
covering strict adapter provenance/wire, empty and scalar publications,
checkpoint persistence, retry/conflict, precommit rollback, uncertain commit
recovery, corrupt/missing/extra rows, metadata and schema rejection. No production
module was imported during the fixture correction. At that source-only checkpoint the three corrected
adversarial builders had not executed since their repair. AST and whitespace
checks passed; subsequent execution evidence is recorded below.

Actual contracts bootstrap and a separate serialized bounded runtime lease are
required before further imports, DuckDB execution, tests, builds or installs.
DuckDB metadata queries executed in the historical development run; current
semantic boundary and repaired adversarial fixtures need a fresh complete passing
development run. Exact-source Windows/Linux wheel and
sdist installations, embedded exact-source build markers, independent fixture and
worker/stored byte parity, fault/cancellation checks and browser inspection remain
open. The package-data declaration reserves `_build_identity.json`; the
coordinator must materialize its actual build-source marker during artifact
preparation, replacing the explicit `UNBUILT_SOURCE_ONLY` placeholder rather than
inferring provenance from this source-only checkpoint.

Full R26 acceptance retains actual EQ153/EQ158 integration for EQ190. This
implementation does not qualify an equity producer, release R26, or authorize
publication. Hosted CI is optional; appropriate exact-commit local validation
and fresh independent review remain required.

## Coordinator corrected-source development run

After the P1 semantic validation repair, the coordinator actually ran all31I/O methods on Windows CPython3.12.10 with DuckDB1.5.6 and real source contracts: PASS12.283s, no failures/errors/skips. Exact before/after contract, I/O and test source hashes were equal. Fresh independent reviewer /root/r26_native_io_independent_review resolved the P1 at sinkSHA7c1b6ee1d1b22aa1204a9b475af510b72621da04c99b3925d1fde757253b1693 and testSHAfa7828d0efc8cd39b7c80e78bcc13a528b582c97556742fd26e36af91d901ca6. The earlier unexecuted language above records the author correction checkpoint. Later pure-contract validation changes require a closure recheck before final artifact acceptance; this run does not qualify installed packages, Linux, numerical derivation or the full R26 release. Coordinator is preparing the locally reviewed source commit/build candidate; no publication is authorized.


## Latest bounded development closure

The coordinator actually executed `python -B -m unittest discover -s
 tests/flow_io -v` in `R26-IO-DEV04`: all 31 methods passed in 17.985 seconds
(unittest time; 18.740 seconds command elapsed), command exit 0. The corrected
adversarial test source SHA256 is
`750082122eefa602dfcfe752eb7508ae456509cbe5a0944b467284f4d1eca5de`;
production I/O source is unchanged from the reviewed semantic-validation repair.
This is Windows source-development evidence against the actual source contracts,
not installed-artifact, Linux, independent numerical or full-release proof.

The broad controller receipt retains `source_unchanged=false` and `passed=false`.
Its 37-before/38-after census differs solely by a newly authored library test
helper, `option-features/tests/flow_features/check_independent_complete_rows.py`.
That helper is outside I/O discovery and is not imported by this test module or
its producer modules. Every I/O test and production dependency in the recorded
census has identical before/after hashes. Thus the I/O command passed with stable
execution inputs; the broader controller is not relabelled as passing. The
historical DEV03 fixture-construction failures above remain recorded.

Fresh independent source review by `/root/r26_native_io_independent_review`
checked the three test-only fixture changes, their independent malicious byte/hash
construction and the raw DEV03/DEV04 receipts. No production change or repeat
runtime was performed during this review. Artifact builds/installs, exact committed
closure qualification, worker/stored integration and release gates remain open.
