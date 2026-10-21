"""Only explicit synthetic canonical envelopes are admitted by this adapter."""
from dataclasses import dataclass
from hashlib import sha256

from option_flow_contracts import (
    FlowValidationError, decode_flow_snapshot, flow_record_digest,
)


@dataclass(frozen=True, slots=True)
class FlowAdapterReceipt:
    input_sha256: str
    snapshot_sha256: str
    input_bytes: int
    deduplicated_count: int
    provenance_mode: str


class SyntheticFlowAdapter:
    def __init__(self, mapping_bytes: bytes):
        if type(mapping_bytes) is not bytes:
            raise FlowValidationError("type_mismatch", "/mapping_bytes")
        self._mapping_bytes = mapping_bytes
        self.receipt = None

    def load(self):
        snapshot = decode_flow_snapshot(self._mapping_bytes)
        for index, binding in enumerate(snapshot.bindings):
            if binding.provenance_mode != "synthetic":
                raise FlowValidationError(
                    "identity_mismatch", f"/bindings/{index}/provenance_mode")
        self.receipt = FlowAdapterReceipt(
            sha256(self._mapping_bytes).hexdigest(),
            flow_record_digest("flow_snapshot", snapshot),
            len(self._mapping_bytes), 0, "synthetic")
        return snapshot
