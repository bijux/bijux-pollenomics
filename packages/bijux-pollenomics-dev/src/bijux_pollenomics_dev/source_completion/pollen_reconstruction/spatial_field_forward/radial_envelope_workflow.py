"""Refine the saved spatial study's conditional envelope without new points."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import inspect
from itertools import combinations
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
import warnings

import numpy as np
import scipy

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_lra.dispersal.kernels import gpm_values
from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus

from ..abborrtjarnen_ppe_dependence.sources import bound_files
from . import radial_envelope as exact

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/spatial-field-forward/radial-envelope/protocol.json"
)
FAMILIES = (
    "direct_pollen_idw",
    "centre_cover_idw_forward",
    "spatial_cover_idw_forward",
)
CORES = ("BOKE", "BUS", "SOLSOE83")
AXIS = ("Betula", "Ulmus")


def source_revision(repository: Path, protocol: dict[str, Any]) -> str:
    files = [
        Path(__file__),
        Path(exact.__file__),
        repository / PROTOCOL,
        repository / protocol["original_protocol"],
    ]
    files.extend(
        Path(inspect.getfile(function))
        for function in (
            bound_files,
            circular_receiver_annulus,
            gpm_values,
            require_absent_artifact_output,
        )
    )
    relative = sorted({str(path.resolve().relative_to(repository)) for path in files})
    git = ["git", "-C", str(repository)]
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    for command in (
        [*git, "ls-files", "--error-unmatch", "--", *relative],
        [*git, "diff", "--exit-code", revision, "--", *relative],
    ):
        subprocess.run(command, check=True, capture_output=True)
    return revision


def read_prediction_inputs(
    repository: Path, protocol: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The old scored result is deliberately absent from this phase's reader."""
    exact.require(
        protocol["design"]
        == {
            "coarse_rings": 8,
            "subdivisions_per_coarse_ring": 16,
            "refined_rings_per_geometry": 128,
            "taxon_geometries": 6,
            "fixed_homogeneous_ring_calls": 768,
            "endpoint_lattice_bits": 96,
        }
        and protocol["cores"] == list(CORES)
        and protocol["axis"] == list(AXIS),
        "Prospective design or scientific axes differ",
    )
    roles = (
        "source_prediction",
        "source_result",
        "source_verification",
        "source_execution",
    )
    exact.require(
        set(protocol["repository_inputs"]) == {protocol[role] for role in roles},
        "Exactly four qualified artifacts required",
    )
    selected = {
        protocol[role]: protocol["repository_inputs"][protocol[role]]
        for role in roles
        if role != "source_result"
    }
    bodies = bound_files(repository, selected)
    prediction = json.loads(bodies[protocol["source_prediction"]])
    verification = json.loads(bodies[protocol["source_verification"]])
    execution = json.loads(bodies[protocol["source_execution"]])
    pins = protocol["repository_inputs"]
    exact.require(
        prediction["schema_version"] == "spatial-field-forward-predictions.v1"
        and prediction["source_commit"] == protocol["prior_producer_source_commit"]
        and execution["source_commit"] == protocol["prior_observer_source_commit"]
        and execution["exit_code"] == 0
        and execution["pytest_passed"] == 1
        and verification["predictions_sha256"]
        == execution["source_results"]["predictions_sha256"]
        == pins[protocol["source_prediction"]]["sha256"]
        and verification["result_sha256"]
        == execution["source_results"]["result_sha256"]
        == pins[protocol["source_result"]]["sha256"]
        and (
            verification["source_rows"],
            verification["selected_samples"],
            verification["source_contexts"],
            verification["scores"]["scored_rows"],
            verification["scores"]["refused_rows"],
        )
        == (147, 59, 18, 54, 0),
        "Existing independent source/study qualification differs",
    )
    original = json.loads((repository / protocol["original_protocol"]).read_bytes())
    original_bytes = subprocess.check_output(
        [
            "git",
            "-C",
            str(repository),
            "show",
            f"{protocol['prior_producer_source_commit']}:{protocol['original_protocol']}",
        ]
    )
    exact.require(
        original_bytes == (repository / protocol["original_protocol"]).read_bytes(),
        "Original geometry protocol changed since the qualified study",
    )
    exact.require(
        prediction["axis"] == list(AXIS)
        and len(prediction["geometry"]) == 3
        and len(prediction["contexts"]) == 18,
        "Saved prediction population differs",
    )
    exact.require(
        [row["core"] for row in prediction["geometry"]] == list(CORES),
        "Saved geometry order differs",
    )
    exact.require(
        len({row["context_id"] for row in prediction["contexts"]}) == 18,
        "Duplicate prediction context",
    )
    exact.require(
        protocol["ring_quadrature"]["absolute_tolerance_per_ring"] == 1e-9 / 128
        and protocol["ring_quadrature"]["relative_tolerance"] == 1e-8
        and protocol["ring_quadrature"]["quadrature_limit"] == 100,
        "Prospective ring quadrature settings differ",
    )
    return prediction, original


def nested_edges(geometry: dict[str, Any], outer: float) -> list[float]:
    rings = geometry["taxa"][0]["step_bounds"]["annuli"]
    exact.require(len(rings) == 8, "Eight original rings required")
    coarse = [rings[0]["inner_radius_m"], *[row["outer_radius_m"] for row in rings]]
    exact.require(
        coarse[0] == geometry["radius_m"]
        and coarse[-1] == outer
        and all(row["inner_radius_m"] == coarse[i] for i, row in enumerate(rings))
        and all(math.isfinite(value) and value > 0 for value in coarse)
        and all(a < b for a, b in zip(coarse[:-1], coarse[1:], strict=True)),
        "Original ring partition differs",
    )
    edges = [coarse[0]]
    for left, right in zip(coarse[:-1], coarse[1:], strict=True):
        edges.extend(
            math.exp(math.log(left) + (math.log(right) - math.log(left)) * j / 16)
            for j in range(1, 16)
        )
        edges.append(right)
    exact.require(
        len(edges) == 129
        and all(a < b for a, b in zip(edges[:-1], edges[1:], strict=True)),
        "Refined nested partition is unresolved",
    )
    return edges


def refine_geometry(
    saved: dict[str, Any], original: dict[str, Any], protocol: dict[str, Any]
) -> dict[str, Any]:
    edges = nested_edges(saved, original["physical"]["regional_extent_m"])
    anchors = saved["anchor_xy_m"]
    certificates = [
        exact.angular_certificate(edge, anchors[0], anchors[1]) for edge in edges
    ]
    taxa = []
    for index, taxon in enumerate(saved["taxa"]):
        masses: list[float | None] = []
        errors: list[float | None] = []
        statuses: list[str] = []
        reasons: list[str | None] = []
        settings, physical = protocol["ring_quadrature"], original["physical"]
        for left, right in zip(edges[:-1], edges[1:], strict=True):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error")
                    response = circular_receiver_annulus(
                        receiver_radius_m=saved["radius_m"],
                        inner_radius_m=left,
                        outer_radius_m=right,
                        fall_speed_m_s=taxon["fall_speed_m_s"],
                        diffusion_coefficient=physical["diffusion_coefficient"],
                        turbulence_parameter=physical["turbulence_parameter"],
                        wind_speed_m_s=physical["wind_speed_m_s"],
                        absolute_tolerance=settings["absolute_tolerance_per_ring"],
                        relative_tolerance=settings["relative_tolerance"],
                        quadrature_limit=settings["quadrature_limit"],
                    )
                exact.require(
                    math.isfinite(response.factor)
                    and response.factor > 0
                    and math.isfinite(response.estimated_absolute_error)
                    and response.estimated_absolute_error >= 0,
                    "Nonpositive/nonfinite ring mass or error estimate",
                )
                masses.append(response.factor)
                errors.append(response.estimated_absolute_error)
                statuses.append("computed_positive_mass")
                reasons.append(None)
            except (ValueError, ArithmeticError, RuntimeError, Warning) as error:
                masses.append(None)
                errors.append(None)
                statuses.append("refused_ring_mass")
                reasons.append(f"{type(error).__name__}: {error}")
        record: dict[str, Any] = {
            "taxon": taxon["taxon"],
            "fall_speed_m_s": taxon["fall_speed_m_s"],
            "ring_masses": masses,
            "ring_error_estimates": errors,
            "ring_statuses": statuses,
            "ring_refusals": reasons,
        }
        if any(mass is None for mass in masses):
            record.update(
                status="refused_ring_mass",
                refined_K_exact=None,
                anchor_factor_bounds_exact=None,
                legacy_mass_gaps_exact=None,
                legacy_mass_correspondence_status="refused_ring_mass",
            )
        else:
            finite = [float(mass) for mass in masses if mass is not None]
            total, coefficients = exact.coefficients(finite, certificates)
            old, primary = saved["homogeneous_taxa"][index], taxon["primary"]
            gaps = {
                "homogeneous_baseline": total - exact.rational(old["factor"]),
                "primary_homogeneous": total
                - exact.rational(primary["homogeneous_factor"]),
                "primary_partition": total
                - sum(
                    (exact.rational(value) for value in primary["anchor_factors"]),
                    Fraction(0),
                ),
            }
            posture = protocol["reference_correspondence"]
            tolerance = posture["mass_absolute_tolerance"] + posture[
                "mass_relative_tolerance"
            ] * abs(old["factor"])
            record.update(
                status="finite_mass_envelope",
                refined_K_exact=str(total),
                anchor_factor_bounds_exact=[
                    exact.encoded(interval) for interval in coefficients
                ],
                legacy_mass_gaps_exact={
                    name: str(value) for name, value in gaps.items()
                },
                legacy_mass_correspondence_tolerance=tolerance,
                legacy_mass_correspondence_status=(
                    "passed_numerical_mass_diagnostic"
                    if all(
                        abs(value) <= exact.rational(tolerance)
                        for value in gaps.values()
                    )
                    else "refused_reference_point_correspondence"
                ),
            )
        taxa.append(record)
    return {
        "core": saved["core"],
        "anchor_order": saved["anchor_order"],
        "anchor_xy_m": anchors,
        "radius_m": saved["radius_m"],
        "edges_m": edges,
        "angular_certificates": certificates,
        "taxa": taxa,
        "status": "finite_mass_envelope"
        if all(row["status"] == "finite_mass_envelope" for row in taxa)
        else "refused_geometry_envelope",
    }


def prediction_context(
    context: dict[str, Any], geometry: dict[str, Any], ppe: list[float]
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "context_id": context["context_id"],
        "core": context["target"]["core"],
        "window": context["target"]["window"],
    }
    exact.require(
        result["core"] == geometry["core"]
        and [row["core"] for row in context["training"]] == geometry["anchor_order"]
        and all(row["core"] != result["core"] for row in context["training"]),
        "Held-place/anchor identity differs",
    )
    if geometry["status"] != "finite_mass_envelope":
        return {
            **result,
            "status": "refused_geometry_envelope",
            "deposition_bounds_exact": None,
            "conditional_spatial_prediction_bounds_exact": None,
            "reference_point_membership": False,
            "reference_point_status": "refused_geometry_envelope",
            "legacy_mass_correspondence_status": "refused_geometry_envelope",
        }
    deposits = tuple(
        exact.deposition(
            Fraction(taxon["refined_K_exact"]),
            exact.decoded(taxon["anchor_factor_bounds_exact"][0]),
            [row["cover"][index] for row in context["training"]],
            ppe[index],
        )
        for index, taxon in enumerate(geometry["taxa"])
    )
    exact.require(len(deposits) == 2, "Two taxon deposition ranges required")
    probability = exact.normalized((deposits[0], deposits[1]))
    ranges = probability, (1 - probability[1], 1 - probability[0])
    old = context["families"][FAMILIES[2]]["pollen_fraction"]
    membership = all(
        lo <= exact.rational(value) <= hi
        for value, (lo, hi) in zip(old, ranges, strict=True)
    )
    masses_match = all(
        row["legacy_mass_correspondence_status"] == "passed_numerical_mass_diagnostic"
        for row in geometry["taxa"]
    )
    return {
        **result,
        "status": "finite_mass_envelope",
        "deposition_bounds_exact": [exact.encoded(interval) for interval in deposits],
        "conditional_spatial_prediction_bounds_exact": [
            exact.encoded(interval) for interval in ranges
        ],
        "reference_point_membership": membership,
        "reference_point_status": "passed_finite_scalar_membership"
        if membership and masses_match
        else "refused_reference_point_correspondence",
        "legacy_mass_correspondence_status": "passed_numerical_mass_diagnostic"
        if masses_match
        else "refused_reference_point_correspondence",
    }


def score_closed(
    path: Path, source: dict[str, Any], prediction: dict[str, Any]
) -> list[dict[str, Any]]:
    """Read closed ranges before receiving the already exposed observed fractions."""
    packet = json.loads(path.read_bytes())
    contexts = {row["context_id"]: row for row in packet["contexts"]}
    references = {row["context_id"]: row for row in prediction["contexts"]}
    exact.require(
        len(source["scores"]) == 54
        and source["source_commit"] == prediction["source_commit"],
        "Saved score population/source differs",
    )
    observed_ids = set()
    scores = []
    for old in source["scores"]:
        key = old["context_id"], old["family"]
        exact.require(
            key not in observed_ids
            and old["status"] == "scored"
            and old["family"] in FAMILIES
            and old["context_id"] in contexts,
            "Duplicate, missing or refused saved score",
        )
        observed_ids.add(key)
        context = contexts[old["context_id"]]
        reference = references[old["context_id"]]
        exact.require(
            old["predicted_fraction"]
            == reference["families"][old["family"]]["pollen_fraction"]
            and old["sample_ids"] == reference["target"]["sample_ids"]
            and old["core"] == reference["target"]["core"]
            and old["window"] == reference["target"]["window"],
            "Saved score/prediction ownership differs",
        )
        row: dict[str, Any] = {
            "context_id": old["context_id"],
            "core": old["core"],
            "window": old["window"],
            "family": old["family"],
            "legacy_point_score": {metric: old[metric] for metric in exact.METRICS},
        }
        if old["family"] != FAMILIES[2]:
            ranges = {
                metric: exact.encoded(
                    (exact.rational(old[metric]), exact.rational(old[metric]))
                )
                for metric in exact.METRICS
            }
            row.update(
                status="fixed_saved_point_reference",
                reference_point_status="fixed_saved_point_reference",
                conditional_metric_ranges_exact=ranges,
            )
        elif context["status"] != "finite_mass_envelope":
            row.update(
                status="refused_geometry_envelope",
                reference_point_status="refused_geometry_envelope",
                conditional_metric_ranges_exact=None,
            )
        else:
            ranges = exact.metric_ranges(
                exact.decoded(
                    context["conditional_spatial_prediction_bounds_exact"][0]
                ),
                old["observed_fraction"],
            )
            membership = all(
                exact.decoded(ranges[metric])[0]
                <= exact.rational(old[metric])
                <= exact.decoded(ranges[metric])[1]
                for metric in exact.METRICS
            )
            row.update(
                status="finite_mass_conditional_score_enclosure",
                reference_point_status="passed_finite_scalar_membership"
                if membership
                and context["reference_point_status"]
                == "passed_finite_scalar_membership"
                else "refused_reference_point_correspondence",
                conditional_metric_ranges_exact=ranges,
            )
        scores.append(row)
    exact.require(
        len(observed_ids) == 54
        and all(
            (context, family) in observed_ids
            for context in contexts
            for family in FAMILIES
        ),
        "Incomplete matched family population",
    )
    return scores


def average_ranges(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    exact.require(len(rows) > 0, "Empty aggregate denominator")
    result = {}
    for metric in exact.METRICS:
        lower = sum(
            (
                exact.decoded(row["conditional_metric_ranges_exact"][metric])[0]
                for row in rows
            ),
            Fraction(0),
        ) / len(rows)
        upper = sum(
            (
                exact.decoded(row["conditional_metric_ranges_exact"][metric])[1]
                for row in rows
            ),
            Fraction(0),
        ) / len(rows)
        result[metric] = exact.encoded((lower, upper))
    return result


def summarize(scores: list[dict[str, Any]], original: dict[str, Any]) -> dict[str, Any]:
    families = []
    for family in FAMILIES:
        rows = [row for row in scores if row["family"] == family]
        old = next(row for row in original["families"] if row["family"] == family)
        if len(rows) != 18 or any(
            row["conditional_metric_ranges_exact"] is None for row in rows
        ):
            families.append(
                {
                    "family": family,
                    "status": "refused_incomplete_context",
                    "legacy_point_metrics": old["equal_place"]["metrics"],
                }
            )
            continue
        places = []
        for core in CORES:
            selected = [row for row in rows if row["core"] == core]
            exact.require(len(selected) == 6, "Six fixed windows per place required")
            places.append(
                {
                    "core": core,
                    "conditional_metric_ranges_exact": average_ranges(selected),
                }
            )
        families.append(
            {
                "family": family,
                "status": "complete_conditional_context",
                "places": places,
                "equal_place": {
                    "conditional_metric_ranges_exact": average_ranges(places),
                    "legacy_point_metrics": old["equal_place"]["metrics"],
                },
            }
        )
    pairwise = []
    for first, second in combinations(families, 2):
        identity = {"first_family": first["family"], "second_family": second["family"]}
        if any(
            row["status"] != "complete_conditional_context" for row in (first, second)
        ):
            pairwise.append({**identity, "status": "refused_incomplete_context"})
            continue
        old = next(
            row
            for row in original["pairwise"]
            if row["first_family"] == first["family"]
            and row["second_family"] == second["family"]
        )
        metrics = {}
        for metric in exact.METRICS:
            a = exact.decoded(
                first["equal_place"]["conditional_metric_ranges_exact"][metric]
            )
            b = exact.decoded(
                second["equal_place"]["conditional_metric_ranges_exact"][metric]
            )
            difference = a[0] - b[1], a[1] - b[0]
            metrics[metric] = {
                "conditional_difference_range_exact": exact.encoded(difference),
                "legacy_point_difference": old["metrics"][metric]["point_difference"],
                "conditional_resolution": "unresolved_finite_mass_context"
                if difference[0] <= 0 <= difference[1]
                else "separated_finite_mass_context",
            }
        correspondence = all(
            row["reference_point_status"] != "refused_reference_point_correspondence"
            for row in scores
            if row["family"] in (first["family"], second["family"])
        )
        pairwise.append(
            {
                **identity,
                "status": "matched_complete_conditional_context",
                "legacy_comparison_status": "numerical_reference_correspondence_only"
                if correspondence
                else "refused_reference_point_correspondence",
                "metrics": metrics,
            }
        )
    return {"families": families, "pairwise": pairwise}


def publish(repository: Path, output: Path) -> dict[str, Any]:
    started = time.monotonic()
    repository = repository.resolve()
    destination = require_absent_artifact_output(repository, output)
    protocol = json.loads((repository / PROTOCOL).read_bytes())
    revision = source_revision(repository, protocol)
    prediction, original = read_prediction_inputs(repository, protocol)
    destination.mkdir(parents=True)
    geometries = [
        refine_geometry(row, original, protocol) for row in prediction["geometry"]
    ]
    geometry_by_core = {row["core"]: row for row in geometries}
    contexts = [
        prediction_context(
            row, geometry_by_core[row["target"]["core"]], prediction["ppe"]
        )
        for row in prediction["contexts"]
    ]
    calls = sum(
        len(taxon["ring_statuses"])
        for geometry in geometries
        for taxon in geometry["taxa"]
    )
    exact.require(calls == 768, "Fixed ring-call population differs")
    packet = {
        "schema_version": "spatial-field-radial-envelope-predictions.v1",
        "source_commit": revision,
        "prior_source_commit": prediction["source_commit"],
        "input_sha256": {
            key: row["sha256"] for key, row in protocol["repository_inputs"].items()
        },
        "geometry": geometries,
        "contexts": contexts,
        "actual_ring_calls": calls,
        "finite_target": protocol["finite_target"],
        "scope": protocol["scope"],
    }
    prediction_body = json.dumps(packet, indent=2, allow_nan=False) + "\n"
    prediction_path = destination / "prediction-ranges.json"
    prediction_path.write_text(prediction_body)
    native_body = bound_files(
        repository,
        {
            protocol["source_result"]: protocol["repository_inputs"][
                protocol["source_result"]
            ]
        },
    )[protocol["source_result"]]
    native = json.loads(native_body)
    exact.require(
        native["prediction_file"]["sha256"]
        == protocol["repository_inputs"][protocol["source_prediction"]]["sha256"],
        "Saved result identifies another prediction packet",
    )
    scores = score_closed(prediction_path, native, prediction)
    result = {
        "schema_version": "spatial-field-radial-envelope-result.v1",
        "status": "conditional_finite_mass_radial_envelope",
        "source_commit": revision,
        "input_sha256": packet["input_sha256"],
        "prediction_file": {
            "path": prediction_path.name,
            "bytes": len(prediction_body.encode()),
            "sha256": hashlib.sha256(prediction_body.encode()).hexdigest(),
        },
        "native_population": {
            "source_rows": 147,
            "selected_samples": 59,
            "contexts": 18,
            "family_outcomes": 54,
        },
        "scores": scores,
        "summaries": summarize(scores, native["summaries"]),
        "actual_ring_calls": calls,
        "refused_ring_calls": sum(
            status != "computed_positive_mass"
            for row in geometries
            for taxon in row["taxa"]
            for status in taxon["ring_statuses"]
        ),
        "reference_point_refusals": sum(
            row["reference_point_status"] == "refused_reference_point_correspondence"
            for row in scores
        ),
        "model_fits": 0,
        "new_point_predictions": 0,
        "raw_count_or_age_inputs_read": False,
        "prior_point_values_changed": False,
        "true_integral_or_field_accuracy_claim": False,
        "finite_target": protocol["finite_target"],
        "scope": protocol["scope"],
        "rights_and_use": protocol["rights_and_use"],
        "environment": {
            "python": sys.version,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
    }
    bound_files(repository, protocol["repository_inputs"])
    exact.require(
        source_revision(repository, protocol) == revision
        and prediction_path.read_text() == prediction_body,
        "Consumed source or closed predictions changed",
    )
    result["elapsed_seconds"] = time.monotonic() - started
    body = json.dumps(result, indent=2, allow_nan=False) + "\n"
    exact.require(
        result["elapsed_seconds"] <= protocol["resource_budget"]["wall_seconds"]
        and len(body.encode()) + len(prediction_body.encode())
        <= protocol["resource_budget"]["output_bytes"],
        "Refinement runtime/output bound exceeded",
    )
    (destination / "result.json").write_text(body)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = publish(args.repository, args.output)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "source_commit",
                    "actual_ring_calls",
                    "refused_ring_calls",
                    "reference_point_refusals",
                    "elapsed_seconds",
                )
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
