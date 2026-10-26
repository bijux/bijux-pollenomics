"""Arithmetic reconciliation of horse source alternatives on their native scale."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, localcontext
import re
from typing import cast

_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?")
_HEADERS = {
    "T1": "IntCal13",
    "T2": "Unmodelled (BC/AD) ",
    "T3": "From",
    "U3": "To",
    "V3": "%",
    "W3": "Average",
    "X3": "Years ago",
}


def _records(value: object) -> dict[str, dict[str, object]]:
    if not isinstance(value, list) or any(not isinstance(cell, dict) for cell in value):
        raise ValueError("Horse alternative evidence requires source cell records")
    records = cast(list[dict[str, object]], value)
    result = {str(cell["cell_reference"]): cell for cell in records}
    if len(result) != len(records):
        raise ValueError("Horse alternative evidence has duplicate cell references")
    return result


def _number(cell: Mapping[str, object], *, numeric_xml: bool) -> Decimal | None:
    token = cell.get("resolved_literal")
    if (
        cell.get("formula_present") is not False
        or cell.get("cell_state") != "present_value"
        or not isinstance(token, str)
        or len(token) > 128
        or _NUMBER.fullmatch(token) is None
        or (numeric_xml and cell.get("native_type_attribute") not in {None, "n"})
    ):
        return None
    value = Decimal(token)
    return value if abs(value.adjusted()) <= 100 else None


def _text(value: Decimal) -> str:
    return format(value.normalize(), "f") if value else "0"


def horse_source_chronology_alternatives(
    evidence: Mapping[str, object],
) -> dict[str, object]:
    """Reconcile source arithmetic without selecting ages or resolving year zero.

    The affine 2017 offsets are coordinates of the source's signed BC/AD
    numbers, not physical durations across the absent civil calendar year zero.
    Radiocarbon R/S remain unconverted despite the adjacent epoch label.
    """
    result: dict[str, object] = {
        "evidence_role": "source_context_only",
        "status": "refused",
        "repo_stable_sample_id": evidence["repo_stable_sample_id"],
        "literal_evidence_field": "source_chronology_fields",
        "reference_year": 2017,
        "coordinate_scale": "source_signed_BC_AD",
        "calendar_year_zero_convention": "not_explicitly_defined_by_source",
        "epoch_evidence": {
            "paper_doi": "10.1016/j.cell.2019.03.049",
            "paper_section": "STAR Methods: Experimental Model and Subject Details",
            "definition_scope": "specimen-name ages in years ago from 2017",
            "calibration_method": "OxCalOnline with IntCal13; source calibration only",
            "worksheet_header_references": list(_HEADERS),
        },
        "radiocarbon_R_S_normalized": False,
        "canonical_bp_conversion_performed": False,
        "reference_arithmetic_performed": False,
        "formula_evaluation_performed": False,
        "selected_chronology_changed": False,
        "scientific_admission": False,
    }
    if evidence.get("status") != "retained_literal_source_fields":
        result["reason_code"] = "literal_source_evidence_unavailable"
        return result
    headers = _records(evidence.get("header_cells"))
    if any(
        headers.get(reference, {}).get("resolved_literal") != literal
        or headers.get(reference, {}).get("formula_present") is not False
        for reference, literal in _HEADERS.items()
    ):
        result["reason_code"] = "source_alternative_headers_differ"
        return result
    fields = _records(evidence.get("fields"))
    row = evidence["physical_row_number"]
    required = [fields.get(f"{column}{row}", {}) for column in "RSTUVWX"]
    if all(cell.get("cell_state") == "present_blank" for cell in required):
        result["reason_code"] = "all_seven_source_alternatives_present_blank"
        return result
    parsed = [_number(cell, numeric_xml=True) for cell in required[2:]]
    if any(value is None for value in parsed):
        result["reason_code"] = (
            "source_alternatives_incomplete_or_non_numeric_or_formula"
        )
        return result
    start, end, coverage, average, signed_offset = cast(list[Decimal], parsed)
    if start > end or not Decimal(0) < coverage <= Decimal(100):
        result["reason_code"] = "source_alternative_bounds_or_coverage_invalid"
        return result
    with localcontext() as context:
        context.prec = 512
        midpoint_residual = average - (start + end) / 2
        signed_offset_residual = signed_offset - (average - 2017)
        result.update(
            {
                "status": "source_alternative_arithmetic_accounted",
                "reference_arithmetic_performed": True,
                "source_average_minus_endpoint_midpoint": _text(midpoint_residual),
                "source_X_minus_expected_signed_offset": _text(signed_offset_residual),
                "signed_offset_residual_formula": "X-(W-2017)",
                "source_arithmetic_consistent": midpoint_residual == 0
                and signed_offset_residual == 0,
                "derived_elapsed_2017_coordinate": {
                    "lower": _text(2017 - end),
                    "upper": _text(2017 - start),
                    "midpoint": _text(2017 - average),
                    "formula": "lower=2017-U; upper=2017-T; midpoint=2017-W",
                    "interpretation": "affine source coordinate, not a physical calendar duration or selected date",
                },
                "source_coverage_percent": _text(coverage),
                "coverage_interpretation": "source interval coverage; not a Gaussian sigma, density or propagated uncertainty",
            }
        )
        selected = fields.get(f"D{row}", {})
        value = _number(selected, numeric_xml=False)
        if value is None:
            result["D_comparison"] = {
                "status": "not_compared_non_numeric_missing_or_formula",
                "source_cell_reference": f"D{row}",
            }
        else:
            residual = value - (2017 - average)
            result["D_comparison"] = {
                "status": "equal_numeric_coordinate"
                if residual == 0
                else "different_numeric_coordinate",
                "source_cell_reference": f"D{row}",
                "D_minus_derived_elapsed_2017_midpoint": _text(residual),
                "interpretation": "literal numeric comparison only; does not establish D epoch, dating basis or precision",
            }
    return result
