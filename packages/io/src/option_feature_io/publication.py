"""Option-owned immutable publication records and sink protocol."""

from dataclasses import dataclass
from typing import Literal, Protocol

from option_feature_contracts import InputBinding, Result


@dataclass(frozen=True, slots=True)
class Publication:
    run_key: str
    work_sha256: str
    request_sha256: str
    snapshot_sha256: str
    cohort_sha256: str
    results: tuple[Result, ...]
    bindings: tuple[InputBinding, ...]


@dataclass(frozen=True, slots=True)
class CommitReceipt:
    run_key: str
    work_sha256: str
    results_sha256: str
    result_count: int
    outcome: Literal["committed", "already_committed"]
    readback_verified: bool


class ResultSink(Protocol):
    def commit(self, publication: Publication) -> CommitReceipt: ...

    def read(self, run_key: str) -> Publication | None: ...
