"""I/O-owned commit evidence; FlowPublication itself is a pure contract."""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FlowCommitReceipt:
    run_key: str
    work_sha256: str
    publication_sha256: str
    results_sha256: str
    output_checkpoint_sha256: str | None
    result_count: int
    outcome: str
    verified_readback: bool
