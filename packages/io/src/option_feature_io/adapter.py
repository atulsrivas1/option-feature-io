"""Explicit supplied synthetic mappings; no provider acquisition or inference."""

from option_feature_contracts import R25_LIMITS, Snapshot, from_payload


def snapshot_from_synthetic_mapping(payload: dict, *, certification_reference: str) -> Snapshot:
    """Admit a caller's already canonical synthetic scenario.

    The caller authors known-at clocks, civil bindings, sample/population lists,
    trade classification and completeness certificates explicitly. This adapter
    does not derive completeness from observed rows or certify external data.
    The reference must equal every source binding's original rights reference;
    it names the synthetic scenario's certification, not a provider approval.
    Prices are supplied per underlying payoff unit; no implicit scaling occurs.
    """
    if type(certification_reference) is not str or not certification_reference:
        raise ValueError("explicit synthetic certification reference required")
    snapshot = from_payload("snapshot", payload, limits=R25_LIMITS)
    if not snapshot.bindings:
        raise ValueError("synthetic adapter requires source bindings")
    for binding in snapshot.bindings:
        if binding.provenance_mode != "synthetic":
            raise ValueError("this adapter admits only synthetic source evidence")
        if binding.rights_reference != certification_reference:
            raise ValueError("synthetic certification reference mismatch")
    return snapshot
