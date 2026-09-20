"""Lossless retained-row projection with exact rational accounting."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from ....analysis.lra.uncertainty.contracts import mass
from ..contracts import canonical, digest


def _rational(value: Fraction) -> dict[str, int | str]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "text": f"{value.numerator}/{value.denominator}",
    }


def _pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _coordinate_label(value: dict[str, Any]) -> str:
    ring = value["ring_mean_m"]
    suffix = "ring=null" if ring is None else f"ring={ring} m"
    return f"{value['role']} / {value['taxon']} / {suffix}"


def project_joint_product(
    manifest: dict[str, Any],
    plan: dict[str, Any],
    *,
    product_manifest_sha256: str,
) -> dict[str, Any]:
    """Project verified retained content without recalculation or renormalization."""
    rows = manifest["rows"]
    summaries = manifest["summaries"]
    bins: list[dict[str, Any]] = []
    means: list[dict[str, Any]] = []
    covariance: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        value = mass(row["mass"])
        diagnostic: object = row.get("error", row.get("detail"))
        ledger.append(
            {
                "row_index": index,
                "row_id": row["row_id"],
                "draw_id": row["draw_id"],
                "bin_id": row["bin_id"],
                "mass": _rational(value),
                "selected_samples": row["selected_samples"],
                "status": row["status"],
                "reason_code": row.get("reason_code"),
                "diagnostic": diagnostic,
                "child": row.get("child"),
                "child_manifest_sha256": row.get("child_manifest_sha256"),
                "child_scientific_content_sha256": row.get(
                    "child_scientific_content_sha256"
                ),
                "child_request_sha256": row.get("child_request_sha256"),
                "source_pointer": f"/rows/{index}",
                "source_member": "manifest.json",
                "source_member_sha256": product_manifest_sha256,
                "source_row_sha256": digest(canonical(row)),
                "retained_row": row,
            }
        )
    for bin_index, band in enumerate(plan["bins"]):
        bin_id = band["bin_id"]
        selected = [row for row in rows if row["bin_id"] == bin_id]
        by_status = {
            status: [row for row in selected if row["status"] == status]
            for status in ("success", "refused", "not_run")
        }
        masses = {
            status: sum((mass(row["mass"]) for row in values), Fraction())
            for status, values in by_status.items()
        }
        requested = sum((mass(row["mass"]) for row in selected), Fraction())
        unsuccessful = masses["refused"] + masses["not_run"]
        summary = summaries[bin_id]
        if requested != 1:
            raise ValueError("Requested finite-law mass must equal one in every bin")
        if (
            _rational(masses["success"])["numerator"]
            != summary["successful_mass"]["numerator"]
            or _rational(masses["success"])["denominator"]
            != summary["successful_mass"]["denominator"]
            or _rational(unsuccessful)["numerator"]
            != summary["failed_mass"]["numerator"]
            or _rational(unsuccessful)["denominator"]
            != summary["failed_mass"]["denominator"]
        ):
            raise ValueError("Projected status masses differ from retained summary")
        coordinates = summary["coordinates"]
        vector = summary["mean"]
        matrix = summary["population_covariance"]
        if summary["complete"]:
            if not isinstance(coordinates, list) or not isinstance(vector, list):
                raise ValueError("Complete retained summary lacks coordinates or means")
            if not isinstance(matrix, list) or len(matrix) != len(coordinates):
                raise ValueError("Complete retained summary lacks full covariance")
            for coordinate_index, (coordinate, mean_value) in enumerate(
                zip(coordinates, vector, strict=True)
            ):
                means.append(
                    {
                        "bin_id": bin_id,
                        "coordinate_index": coordinate_index,
                        "coordinate_label": _coordinate_label(coordinate),
                        "coordinate": coordinate,
                        "value": mean_value,
                        "unit": "fraction",
                        "source_pointer": (
                            f"/summaries/{_pointer(bin_id)}/mean/{coordinate_index}"
                        ),
                        "source_member_sha256": product_manifest_sha256,
                    }
                )
            for row_index, (row_coordinate, matrix_row) in enumerate(
                zip(coordinates, matrix, strict=True)
            ):
                if not isinstance(matrix_row, list) or len(matrix_row) != len(
                    coordinates
                ):
                    raise ValueError("Retained covariance is not a full square matrix")
                for column_index, (column_coordinate, covariance_value) in enumerate(
                    zip(coordinates, matrix_row, strict=True)
                ):
                    covariance.append(
                        {
                            "bin_id": bin_id,
                            "row_index": row_index,
                            "column_index": column_index,
                            "row_label": _coordinate_label(row_coordinate),
                            "column_label": _coordinate_label(column_coordinate),
                            "row_coordinate": row_coordinate,
                            "column_coordinate": column_coordinate,
                            "value": covariance_value,
                            "unit": summary["covariance_unit"],
                            "source_pointer": (
                                f"/summaries/{_pointer(bin_id)}/"
                                f"population_covariance/{row_index}/{column_index}"
                            ),
                            "source_member_sha256": product_manifest_sha256,
                        }
                    )
        elif any(value is not None for value in (coordinates, vector, matrix)):
            raise ValueError("Incomplete retained summary must keep moments null")
        bins.append(
            {
                "bin_index": bin_index,
                "bin_id": bin_id,
                "younger_bp": band["younger_bp"],
                "older_bp": band["older_bp"],
                "membership": band["membership"],
                "stationarity": "declared_bin_stationarity",
                "complete": summary["complete"],
                "counts": {
                    "requested": len(selected),
                    "successful": len(by_status["success"]),
                    "refused": len(by_status["refused"]),
                    "not_run": len(by_status["not_run"]),
                },
                "masses": {
                    "requested": _rational(requested),
                    "successful": _rational(masses["success"]),
                    "refused": _rational(masses["refused"]),
                    "not_run": _rational(masses["not_run"]),
                    "combined_unsuccessful": _rational(unsuccessful),
                },
                "coordinates": coordinates,
                "mean": vector,
                "population_covariance": matrix,
                "covariance_unit": summary["covariance_unit"],
                "intervals": summary["intervals"],
                "summary_profile": summary["summary_profile"],
                "monte_carlo_standard_error_claimed": summary[
                    "monte_carlo_standard_error_claimed"
                ],
                "automatic_renormalization": summary["automatic_renormalization"],
                "source_pointer": f"/summaries/{_pointer(bin_id)}",
                "plan_source_pointer": f"/bins/{bin_index}",
                "source_member_sha256": product_manifest_sha256,
                "plan_sha256": manifest["plan_sha256"],
            }
        )
    return {
        "schema_version": "lra-joint-summary-download.v1",
        "product_manifest_sha256": product_manifest_sha256,
        "scientific_content_sha256": manifest["scientific_content_sha256"],
        "plan_sha256": manifest["plan_sha256"],
        "profile": manifest["profile"],
        "product_status": manifest["status"],
        "interrupted": manifest["interrupted"],
        "scientific_acceptance": manifest["scientific_acceptance"],
        "publication_authorized": False,
        "uncertainty_scope": manifest["uncertainty_scope"],
        "denominators": manifest["denominators"],
        "bins": bins,
        "draw_bin_ledger": ledger,
        "means": means,
        "covariance": covariance,
    }


__all__ = ["project_joint_product"]
