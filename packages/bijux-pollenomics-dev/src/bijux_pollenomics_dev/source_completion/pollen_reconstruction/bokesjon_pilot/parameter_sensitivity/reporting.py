"""Compare two conditional point estimates without inferring a probability law."""

from __future__ import annotations

from copy import deepcopy
from math import isfinite
from typing import Any

from .preparation import CASE_IDS


def compare(manifest: dict[str, Any]) -> dict[str, Any]:
    """Consume reader-validated cases and retain the complete two-case denominator."""
    rows = manifest["cases"]
    if len(rows) != 2 or {r["case_id"] for r in rows} != set(CASE_IDS):
        raise ValueError("Exactly the two declared nominal cases are required")
    by_id = {r["case_id"]: r for r in rows}
    ordered = [by_id[name] for name in CASE_IDS]
    if any(r["status"] not in {"success", "refused", "not_run"} for r in ordered):
        raise ValueError("Unknown nominal case outcome")
    complete = all(r["status"] == "success" for r in ordered)
    result: dict[str, Any] = {
        "status": "complete_conditional_nominal_comparison"
        if complete
        else "incomplete_conditional_nominal_comparison",
        "outcomes": [
            {
                "case_id": r["case_id"],
                "status": r["status"],
                "reason_code": r.get("reason_code"),
            }
            for r in ordered
        ],
        "coordinates": None,
        "cases": None,
        "raw_delta_percentage_points": None,
        "adjusted_delta_percentage_points": None,
        "clipping_masks_nominal_change": None,
        "mean": None,
        "covariance": None,
        "probability_mass": None,
        "source_standard_errors": None,
        "measured_accuracy_evaluated": False,
        "scientific_admission": "not_evaluated",
    }
    if not complete:
        return result
    coordinates = ordered[0]["coordinates"]
    if (
        not coordinates
        or ordered[1]["coordinates"] != coordinates
        or any(c["unit"] != "fraction" for c in coordinates)
    ):
        raise ValueError("Nominal cases require identical fraction-valued axes")
    for row in ordered:
        for kind in ("raw", "adjusted"):
            values = row[kind + "_values"]
            if len(values) != len(coordinates) or not all(
                type(v) in (int, float) and isfinite(v) for v in values
            ):
                raise ValueError("Complete finite vectors required for differences")
    result["coordinates"] = deepcopy(coordinates)
    result["cases"] = [
        {
            "case_id": r["case_id"],
            "raw_values": list(r["raw_values"]),
            "adjusted_values": list(r["adjusted_values"]),
        }
        for r in ordered
    ]
    for kind in ("raw", "adjusted"):
        result[kind + "_delta_percentage_points"] = [
            100 * (after - before)
            for before, after in zip(
                ordered[0][kind + "_values"], ordered[1][kind + "_values"], strict=True
            )
        ]
    result["clipping_masks_nominal_change"] = any(
        abs(raw - adjusted) > 1e-9
        for raw, adjusted in zip(
            result["raw_delta_percentage_points"],
            result["adjusted_delta_percentage_points"],
            strict=True,
        )
    )
    return result


def markdown(result: dict[str, Any]) -> str:
    """Explain the nominal difference with separate raw and adjusted cover tables."""
    lines = [
        "# Conditional BOKE/KRAG nominal PPE comparison",
        "",
        "This is a two-tree composition of Betula and Ulmus under the retained "
        "pooled count, chronology, basin and regional-background assumptions. "
        "It is neither full forest/open/cereal cover nor measured vegetation accuracy.",
        "",
        "The comparison changes shared Betula PPE from 5.106 to 4.94 in both "
        "stages. Ulmus remains 1.27 because the selected European reference is "
        "missing. Fall speeds and source SD metadata are unchanged. No source SD "
        "law is propagated and the unweighted design supplies no mean, covariance, "
        "probability interval or empirical confidence interval.",
        "",
        "Changes below are comparison minus baseline in percentage points. "
        "Each local result is clipped and renormalized before comparison; raw "
        "signed values remain visible. A zero adjusted change can hide a raw change.",
        "",
        "The clipping policy follows the discussion with supervisor Anneli Poska "
        "reported by the project author (personal communication; discussion date "
        "not recorded). Negatives become zero and surviving positive mass is "
        "renormalized. A realization with no positive mass fails explicitly.",
        "",
    ]
    if result["status"] != "complete_conditional_nominal_comparison":
        lines += [
            "The two-case difference is unavailable. Refused and unrun cases "
            "remain explicit; no successful subset is substituted.",
            "",
            "| Case | Outcome | Reason |",
            "| --- | --- | --- |",
        ]
        lines += [
            f"| {r['case_id']} | {r['status']} | {r['reason_code'] or 'not supplied'} |"
            for r in result["outcomes"]
        ]
        return "\n".join(lines) + "\n"
    for kind, label in (("raw", "Raw signed cover"), ("adjusted", "Adjusted cover")):
        lines += [
            "## " + label,
            "",
            "| Support | Taxon | Baseline (%) | Comparison (%) | Change (percentage points) |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
        before, after = result["cases"]
        for index, coordinate in enumerate(result["coordinates"]):
            support = (
                "Regional"
                if coordinate["role"] == "regional"
                else (f"Local ring midpoint {coordinate['ring_mean_m']:g} m")
            )
            taxon = coordinate["taxon"].replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {support} | {taxon} | {100 * before[kind + '_values'][index]:.6f} | "
                f"{100 * after[kind + '_values'][index]:.6f} | "
                f"{result[kind + '_delta_percentage_points'][index]:.6f} |"
            )
        lines.append("")
    lines += [
        "See report.json and source-cases/manifest.json for exact values, "
        "source references and case outcomes. Original source members and "
        "full child bundles remain in private analytical storage.",
        "",
    ]
    return "\n".join(lines)
