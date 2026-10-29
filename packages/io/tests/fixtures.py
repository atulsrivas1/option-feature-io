"""Original constructed transport fixtures, never a numerical oracle."""

from option_feature_contracts import from_payload
from option_feature_io import Publication

EMPTY = {
    "schema_version": "option-canonical1", "bindings": [], "civil_bindings": [],
    "definitions": [], "spots": [], "model_facts": [], "quotes": [],
    "supplied_metrics": [], "trades": [], "coverage_certificates": [],
    "quote_coverage_windows": [], "activity_window": None,
}
BINDING = {
    "binding_id": "synthetic-1", "source_id": "original-fixture",
    "source_revision": "1", "source_content_sha256": "1" * 64,
    "provenance_mode": "synthetic", "rights_reference": "original-test-scenario1",
}
RESULT = {
    "schema_version": "option-result1", "contract_id": "OPTION-1",
    "underlying_id": "UNDERLYING-1", "output_id": "contract.multiplier",
    "currency": "USD", "action_basis_id": "unadjusted1", "origin": "computed",
    "value": 100.0, "unit": "underlying_units_per_contract", "status": "available",
    "reason": "ok", "quality_flags": [], "coverage": None, "solver_evidence": None,
    "pricing_evidence": None, "converted_operands": None,
    "dependency_binding_ids": ["synthetic-1"], "dependency_record_sha256s": ["2" * 64],
    "valuation_ns": 0, "knowledge_cutoff_ns": 0, "model_id": "option-bsm1",
    "formula_version": "r25-formulas1", "producer_model_id": None, "producer_formula_id": None,
    "config_sha256": "3" * 64, "snapshot_sha256": "4" * 64,
    "contracts_package_version": "0.2.0a1", "calculation_package_version": "0.2.0a1",
}
REQUEST = {
    "schema_version": "option-request1", "contract_ids": ["OPTION-1"],
    "output_ids": ["contract.multiplier"], "origin_policy": "computed_only",
    "supplied_delta_policy": "exact_only", "valuation_ns": 0,
    "knowledge_cutoff_ns": 0, "valuation_ordinal": 719163,
    "civil_binding_id": "civil1", "model_id": "option-bsm1",
    "formula_version": "r25-formulas1",
    "eligibility": {"max_quote_age_ns": 0, "max_spot_age_ns": 0,
                    "max_supplied_metric_age_ns": 0},
    "solver": {"method": "bisection1", "quote_basis": "midpoint", "max_sigma": 5.0,
               "max_iterations": 128, "price_abs_tol": 1e-8, "price_rel_tol": 1e-8,
               "vol_abs_tol": 1e-8, "vol_rel_tol": 1e-8},
    "limits": {"max_wire_bytes": 16777216, "max_snapshot_records": 100000,
               "max_requested_contracts": 1000, "max_selected_outputs": 32,
               "max_result_rows": 32001, "max_solver_iterations": 4096},
}


def publication(run_key="synthetic-run1"):
    return Publication(run_key, "5" * 64, "3" * 64, "4" * 64, "6" * 64,
                       (from_payload("result", RESULT),),
                       (from_payload("input_binding", BINDING),))
