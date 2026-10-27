"""Source-read boundaries and complete score/refusal accounting controls."""

from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path
from typing import Any

import pytest

from .certificates import quadrature_rules, verify_geometry
from .exact_arithmetic import finite, interval
from .metrics import METRICS, metric_bounds
from .result_checks import (
    average_ranges,
    encoded,
    verify_contexts,
    verify_scores,
    verify_summaries,
)
from .sources import AXIS, CORES, FAMILIES, PROTOCOL, prediction_inputs


@pytest.fixture(scope="module")
def rules() -> Any:
    return quadrature_rules()


def geometry_fixture() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    coarse = [
        {"inner_radius_m": 2.0**i, "outer_radius_m": 2.0 ** (i + 1)} for i in range(8)
    ]
    old = {
        "core": "BOKE",
        "anchor_order": ["BUS", "SOLSOE83"],
        "anchor_xy_m": [[111319.49079327357, 0.0], [-111319.49079327357, 0.0]],
        "radius_m": 1.0,
        "taxa": [
            {
                "taxon": taxon,
                "fall_speed_m_s": speed,
                "step_bounds": {"annuli": coarse},
                "primary": {
                    "homogeneous_factor": 128.0,
                    "anchor_factors": [64.0, 64.0],
                },
            }
            for taxon, speed in zip(AXIS, (0.02, 0.03), strict=True)
        ],
        "homogeneous_taxa": [{"factor": 128.0}, {"factor": 128.0}],
    }
    edges = [1.0]
    for ring in coarse:
        lo, hi = ring["inner_radius_m"], ring["outer_radius_m"]
        edges.extend(
            math.exp(math.log(lo) + (math.log(hi) - math.log(lo)) * j / 16)
            for j in range(1, 16)
        )
        edges.append(hi)
    row = {
        key: deepcopy(old[key])
        for key in ("core", "anchor_order", "anchor_xy_m", "radius_m")
    }
    tolerance = 1e-9 + 1e-8 * 128
    row.update(
        edges_m=edges,
        angular_certificates=[
            {
                "radius_m": radius,
                "symmetry": True,
                "sqrt_radicand_exact": None,
                "sqrt_bounds_exact": None,
                "weight_bounds_exact": ["1/2", "1/2"],
            }
            for radius in edges
        ],
        taxa=[
            {
                "taxon": taxon,
                "fall_speed_m_s": speed,
                "ring_masses": [1.0] * 128,
                "ring_error_estimates": [0.0] * 128,
                "ring_statuses": ["computed_positive_mass"] * 128,
                "ring_refusals": [None] * 128,
                "status": "finite_mass_envelope",
                "refined_K_exact": "128",
                "anchor_factor_bounds_exact": [["64", "64"], ["64", "64"]],
                "legacy_mass_gaps_exact": {
                    "homogeneous_baseline": "0",
                    "primary_homogeneous": "0",
                    "primary_partition": "0",
                },
                "legacy_mass_correspondence_tolerance": tolerance,
                "legacy_mass_correspondence_status": "passed_numerical_mass_diagnostic",
            }
            for taxon, speed in zip(AXIS, (0.02, 0.03), strict=True)
        ],
        status="finite_mass_envelope",
    )
    protocol = {
        "independent_correspondence": {
            "projection_absolute_tolerance_m": 1e-5,
            "projection_relative_tolerance": 1e-12,
            "angular_absolute_tolerance": 2e-12,
            "angular_resolution_absolute_tolerance": 1e-11,
        },
        "reference_correspondence": {
            "mass_absolute_tolerance": 1e-9,
            "mass_relative_tolerance": 1e-8,
        },
    }
    original = {
        "cores": [
            {"id": core, "analysis_centre_lon_lat": centre}
            for core, centre in zip(
                CORES, ([0.0, 0.0], [1.0, 0.0], [-1.0, 0.0]), strict=True
            )
        ],
        "physical": {"regional_extent_m": 256.0},
    }
    return row, old, protocol, original


def test_actual_certificate_consumer_accepts_symmetric_finite_mass(rules: Any) -> None:
    checked = verify_geometry(*geometry_fixture(), rules)
    assert (
        checked["coefficients"] == [(Fraction(128), (Fraction(64), Fraction(64)))] * 2
    )
    assert checked["mass_matches"] is True and checked["refused_ring_calls"] == 0


def test_different_old_K_refuses_correspondence_without_changing_new_model(
    rules: Any,
) -> None:
    row, old, protocol, original = geometry_fixture()
    old["homogeneous_taxa"][0]["factor"] = 127.0
    row["taxa"][0]["legacy_mass_gaps_exact"]["homogeneous_baseline"] = "1"
    row["taxa"][0]["legacy_mass_correspondence_tolerance"] = 1e-9 + 1e-8 * 127
    row["taxa"][0]["legacy_mass_correspondence_status"] = (
        "refused_reference_point_correspondence"
    )
    checked = verify_geometry(row, old, protocol, original, rules)
    assert checked["mass_matches"] is False
    assert checked["coefficients"][0] == (Fraction(128), (Fraction(64), Fraction(64)))


def test_one_failed_ring_keeps_all_outcomes_and_refuses_its_geometry(
    rules: Any,
) -> None:
    row, old, protocol, original = geometry_fixture()
    taxon = row["taxa"][0]
    taxon["ring_masses"][0] = taxon["ring_error_estimates"][0] = None
    taxon["ring_statuses"][0] = "refused_ring_mass"
    taxon["ring_refusals"][0] = "RuntimeError: synthetic unresolved integral"
    taxon.update(
        status="refused_ring_mass",
        refined_K_exact=None,
        anchor_factor_bounds_exact=None,
        legacy_mass_gaps_exact=None,
        legacy_mass_correspondence_status="refused_ring_mass",
    )
    row["status"] = "refused_geometry_envelope"
    checked = verify_geometry(row, old, protocol, original, rules)
    assert checked["refused_ring_calls"] == 1 and checked["coefficients"][0] is None
    assert checked["coefficients"][1] is not None
    taxon["ring_refusals"][0] = None
    with pytest.raises(ValueError, match="literal reason"):
        verify_geometry(row, old, protocol, original, rules)


@pytest.mark.parametrize(
    "defect",
    [
        "complement",
        "negative_mass",
        "dropped_ring",
        "false_gap",
        "edge",
        "anchor",
        "taxon",
        "false_symmetry",
    ],
)
def test_changed_geometric_evidence_cannot_be_hidden(defect: str, rules: Any) -> None:
    row, old, protocol, original = geometry_fixture()
    if defect == "complement":
        row["taxa"][0]["anchor_factor_bounds_exact"][1] = ["65", "65"]
    elif defect == "negative_mass":
        row["taxa"][0]["ring_masses"][0] = -1.0
    elif defect == "dropped_ring":
        row["taxa"][0]["ring_masses"].pop()
    elif defect == "false_gap":
        row["taxa"][0]["legacy_mass_gaps_exact"]["primary_partition"] = "1"
    elif defect == "edge":
        row["edges_m"][1] *= 1.01
    elif defect == "anchor":
        row["anchor_xy_m"][0][0] += 1
    elif defect == "taxon":
        row["taxa"][0]["taxon"] = "unrelated"
    else:
        row["angular_certificates"][0]["symmetry"] = False
    with pytest.raises(ValueError):
        verify_geometry(row, old, protocol, original, rules)


def score_fixture() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    prior: dict[str, Any] = {"contexts": []}
    native: dict[str, Any] = {"scores": []}
    actual: dict[str, Any] = {"scores": []}
    contexts = {}
    spatial = {
        metric: encoded(bounds)
        for metric, bounds in metric_bounds(
            (Fraction(1, 4), Fraction(3, 4)), (Fraction(1, 2), Fraction(1, 2))
        ).items()
    }
    zero = {metric: ["0", "0"] for metric in METRICS}
    for place, core in enumerate(CORES):
        for window in range(6):
            identity = f"{core}:{window}:{window + 1}"
            target = {
                "core": core,
                "window": [window, window + 1],
                "sample_ids": [place * 10 + window],
            }
            prior["contexts"].append(
                {
                    "context_id": identity,
                    "target": target,
                    "families": {
                        family: {"pollen_fraction": [0.5, 0.5]} for family in FAMILIES
                    },
                }
            )
            contexts[identity] = {
                "status": "finite_mass_envelope",
                "conditional_spatial_prediction_bounds_exact": [
                    ["1/4", "3/4"],
                    ["1/4", "3/4"],
                ],
                "reference_point_status": "passed_finite_scalar_membership",
            }
            for family in FAMILIES:
                old = {
                    "context_id": identity,
                    "family": family,
                    **target,
                    "status": "scored",
                    "predicted_fraction": [0.5, 0.5],
                    "observed_fraction": [0.5, 0.5],
                    **dict.fromkeys(METRICS, 0.0),
                }
                native["scores"].append(old)
                row = {
                    key: old[key] for key in ("context_id", "core", "window", "family")
                }
                status = (
                    "fixed_saved_point_reference"
                    if family != FAMILIES[2]
                    else "finite_mass_conditional_score_enclosure"
                )
                row.update(
                    legacy_point_score=dict.fromkeys(METRICS, 0.0),
                    status=status,
                    reference_point_status="fixed_saved_point_reference"
                    if family != FAMILIES[2]
                    else "passed_finite_scalar_membership",
                    conditional_metric_ranges_exact=deepcopy(
                        zero if family != FAMILIES[2] else spatial
                    ),
                )
                actual["scores"].append(row)
    native["summaries"] = {
        "families": [
            {"family": family, "equal_place": {"metrics": dict.fromkeys(METRICS, 0.0)}}
            for family in FAMILIES
        ],
        "pairwise": [
            {
                "first_family": a,
                "second_family": b,
                "metrics": {metric: {"point_difference": 0.0} for metric in METRICS},
            }
            for a, b in combinations(FAMILIES, 2)
        ],
    }
    summaries: dict[str, Any] = {"families": [], "pairwise": []}
    for family in FAMILIES:
        ranges = deepcopy(zero if family != FAMILIES[2] else spatial)
        summaries["families"].append(
            {
                "family": family,
                "status": "complete_conditional_context",
                "places": [
                    {"core": core, "conditional_metric_ranges_exact": deepcopy(ranges)}
                    for core in CORES
                ],
                "equal_place": {
                    "conditional_metric_ranges_exact": ranges,
                    "legacy_point_metrics": dict.fromkeys(METRICS, 0.0),
                },
            }
        )
    for a, b in combinations(FAMILIES, 2):
        summaries["pairwise"].append(
            {
                "first_family": a,
                "second_family": b,
                "status": "matched_complete_conditional_context",
                "legacy_comparison_status": "numerical_reference_correspondence_only",
                "metrics": {
                    metric: {
                        "conditional_difference_range_exact": [
                            str(-interval(spatial[metric])[1])
                            if b == FAMILIES[2]
                            else "0",
                            "0",
                        ],
                        "legacy_point_difference": 0.0,
                        "conditional_resolution": "unresolved_finite_mass_context",
                    }
                    for metric in METRICS
                },
            }
        )
    actual["summaries"] = summaries
    return actual, native, prior, contexts


def test_complete_score_and_equal_place_consumer_keeps_all_families() -> None:
    actual, native, prior, contexts = score_fixture()
    rows = verify_scores(actual, native, prior, contexts)
    assert len(rows) == 54
    verify_summaries(actual["summaries"], rows, native["summaries"])


def context_fixture() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    _, _, prior, _ = score_fixture()
    prior["ppe"] = [1.0, 1.0]
    packet: dict[str, Any] = {"contexts": []}
    geometries = {
        core: {
            "coefficients": [(Fraction(1), (Fraction(1, 4), Fraction(3, 4)))] * 2,
            "mass_matches": True,
        }
        for core in CORES
    }
    for source in prior["contexts"]:
        core = source["target"]["core"]
        source["geometry_core"] = core
        source["target"]["site_id"] = CORES.index(core)
        source["training"] = [
            {
                "core": name,
                "site_id": CORES.index(name),
                "window": source["target"]["window"],
                "sample_ids": [100 + CORES.index(name)],
                "cover": [0.5, 0.5],
            }
            for name in sorted(set(CORES) - {core})
        ]
        packet["contexts"].append(
            {
                "context_id": source["context_id"],
                "core": core,
                "window": source["target"]["window"],
                "status": "finite_mass_envelope",
                "deposition_bounds_exact": [["1/2", "1/2"], ["1/2", "1/2"]],
                "conditional_spatial_prediction_bounds_exact": [
                    ["1/2", "1/2"],
                    ["1/2", "1/2"],
                ],
                "reference_point_membership": True,
                "reference_point_status": "passed_finite_scalar_membership",
                "legacy_mass_correspondence_status": "passed_numerical_mass_diagnostic",
            }
        )
    return packet, prior, geometries


def test_prediction_boundary_uses_frozen_covers_and_keeps_all_contexts() -> None:
    packet, prior, geometries = context_fixture()
    checked = verify_contexts(packet, prior, geometries)
    assert len(checked) == 18
    assert all(
        row["conditional_spatial_prediction_bounds_exact"]
        == [["1/2", "1/2"], ["1/2", "1/2"]]
        for row in checked.values()
    )


@pytest.mark.parametrize(
    "defect",
    [
        "same_place",
        "same_sample",
        "different_window",
        "drop_context",
        "changed_cover",
        "nonclosed_legacy_pair",
        "mass_gap_hidden",
    ],
)
def test_context_source_leakage_and_reference_promotion_refuse(defect: str) -> None:
    packet, prior, geometries = context_fixture()
    source = prior["contexts"][0]
    if defect == "same_place":
        source["training"][0]["site_id"] = source["target"]["site_id"]
    elif defect == "same_sample":
        source["training"][0]["sample_ids"] = source["target"]["sample_ids"]
    elif defect == "different_window":
        source["training"][0]["window"] = [999, 1000]
    elif defect == "drop_context":
        packet["contexts"].pop()
    elif defect == "changed_cover":
        source["training"][0]["cover"][0] = 0.4
    elif defect == "nonclosed_legacy_pair":
        source["families"][FAMILIES[2]]["pollen_fraction"][1] = 0.5000001
    else:
        geometries["BOKE"]["mass_matches"] = False
    with pytest.raises(ValueError):
        verify_contexts(packet, prior, geometries)


def test_refused_geometry_preserves_a_legacy_score_without_scoring_a_false_range() -> (
    None
):
    actual, native, prior, contexts = score_fixture()
    identity = next(iter(contexts))
    contexts[identity]["status"] = "refused_geometry_envelope"
    row = next(
        row
        for row in actual["scores"]
        if row["context_id"] == identity and row["family"] == FAMILIES[2]
    )
    row.update(
        status="refused_geometry_envelope",
        reference_point_status="refused_geometry_envelope",
        conditional_metric_ranges_exact=None,
    )
    checked = verify_scores(actual, native, prior, contexts)
    assert (
        len(checked) == 54
        and sum(row["conditional_metric_ranges_exact"] is None for row in checked) == 1
    )
    assert row["legacy_point_score"] == dict.fromkeys(METRICS, 0.0)


@pytest.mark.parametrize(
    "defect",
    [
        "drop",
        "legacy_point",
        "observed_component",
        "scope_status",
        "false_reference",
        "summary_denominator",
        "legacy_aggregate",
    ],
)
def test_score_or_summary_changes_do_not_manufacture_correspondence(
    defect: str,
) -> None:
    actual, native, prior, contexts = score_fixture()
    if defect == "drop":
        actual["scores"].pop()
    elif defect == "legacy_point":
        actual["scores"][0]["legacy_point_score"][METRICS[0]] = 0.01
    elif defect == "observed_component":
        native["scores"][0]["observed_fraction"][1] = 0.4
    elif defect == "scope_status":
        actual["scores"][0]["status"] = "certified_new_baseline_metric"
    elif defect == "false_reference":
        contexts[next(iter(contexts))]["reference_point_status"] = (
            "refused_reference_point_correspondence"
        )
    elif defect == "summary_denominator":
        actual["summaries"]["families"][0]["places"].pop()
    else:
        actual["summaries"]["families"][0]["equal_place"]["legacy_point_metrics"][
            METRICS[0]
        ] = 0.01
    with pytest.raises(ValueError):
        rows = verify_scores(actual, native, prior, contexts)
        verify_summaries(actual["summaries"], rows, native["summaries"])


def test_saved_float_means_do_not_erase_additional_rounding() -> None:
    values = [finite(value) for value in (0.1, 0.2, 0.3)]
    rows = [
        {
            "conditional_metric_ranges_exact": {
                metric: encoded((value, value)) for metric in METRICS
            }
        }
        for value in values
    ]
    actual = average_ranges(rows)
    expected = Fraction(21617278211378381, 108086391056891904)
    assert all(interval(bounds) == (expected, expected) for bounds in actual.values())
    assert expected != finite(0.2)


def test_phase_one_never_opens_the_old_scored_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_paths = {
        name: f"artifacts/{name}.json"
        for name in ("prediction", "native", "observer", "execution")
    }
    bodies: dict[str, dict[str, Any]] = {
        "prediction": {
            "schema_version": "spatial-field-forward-predictions.v1",
            "source_commit": "1" * 40,
            "axis": list(AXIS),
            "geometry": [{"core": core} for core in CORES],
            "contexts": [{"context_id": str(i)} for i in range(18)],
        },
        "native": {"must_not_be_read": True},
        "observer": {
            "source_rows": 147,
            "selected_samples": 59,
            "source_contexts": 18,
            "scores": {"scored_rows": 54, "refused_rows": 0},
        },
        "execution": {
            "source_commit": "2" * 40,
            "exit_code": 0,
            "pytest_passed": 1,
            "source_results": {},
        },
    }
    pins = {}
    for name in ("prediction", "native"):
        content = json.dumps(bodies[name]).encode()
        path = tmp_path / source_paths[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        pins[source_paths[name]] = {
            "bytes": len(content),
            "sha256": sha256(content).hexdigest(),
        }
    for name in ("observer", "execution"):
        destination = (
            bodies[name] if name == "observer" else bodies[name]["source_results"]
        )
        destination.update(
            predictions_sha256=pins[source_paths["prediction"]]["sha256"],
            result_sha256=pins[source_paths["native"]]["sha256"],
        )
        content = json.dumps(bodies[name]).encode()
        (tmp_path / source_paths[name]).write_bytes(content)
        pins[source_paths[name]] = {
            "bytes": len(content),
            "sha256": sha256(content).hexdigest(),
        }
    original_body = b'{"physical": {}}'
    original_path = "reports/original-protocol.json"
    (tmp_path / original_path).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / original_path).write_bytes(original_body)
    protocol = {
        "schema_version": "spatial-field-radial-envelope-protocol.v1",
        "cores": list(CORES),
        "axis": list(AXIS),
        "design": {
            "coarse_rings": 8,
            "subdivisions_per_coarse_ring": 16,
            "refined_rings_per_geometry": 128,
            "taxon_geometries": 6,
            "fixed_homogeneous_ring_calls": 768,
            "endpoint_lattice_bits": 96,
        },
        "source_prediction": source_paths["prediction"],
        "source_result": source_paths["native"],
        "source_verification": source_paths["observer"],
        "source_execution": source_paths["execution"],
        "repository_inputs": pins,
        "prior_producer_source_commit": "1" * 40,
        "prior_observer_source_commit": "2" * 40,
        "original_protocol": original_path,
    }
    path = tmp_path / PROTOCOL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(protocol))
    import subprocess

    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: original_body)
    read = Path.read_bytes

    def guarded(path: Path) -> bytes:
        assert path != tmp_path / source_paths["native"]
        return read(path)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    loaded, prediction, original = prediction_inputs(tmp_path)
    assert (
        loaded == protocol
        and len(prediction["contexts"]) == 18
        and original == {"physical": {}}
    )


def test_actual_oracle_rejects_bad_prediction_certificates_before_native_observations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.source_completion.pollen_reconstruction import (
        test_radial_envelope_result as consumer,
    )

    protocol = {
        "source_result": "artifacts/native.json",
        "repository_inputs": {"artifacts/native.json": {"sha256": "0" * 64}},
        "finite_target": "synthetic conditional target",
        "scope": "synthetic scope",
    }
    prior = {"source_commit": "1" * 40, "geometry": [{"core": core} for core in CORES]}
    packet = {
        "schema_version": "spatial-field-radial-envelope-predictions.v1",
        "prior_source_commit": "1" * 40,
        "input_sha256": {"artifacts/native.json": "0" * 64},
        "finite_target": protocol["finite_target"],
        "scope": protocol["scope"],
        "geometry": [{"core": core} for core in CORES],
    }
    prediction = tmp_path / "prediction-ranges.json"
    prediction.write_text(json.dumps(packet))
    monkeypatch.setattr(
        consumer, "prediction_inputs", lambda root: (protocol, prior, {})
    )
    monkeypatch.setattr(consumer, "quadrature_rules", dict)

    def bad_geometry(*args: Any) -> None:
        raise ValueError("synthetic angular certificate refusal")

    def no_native_reads(*args: Any) -> bytes:
        raise AssertionError("native observations read before prediction validation")

    monkeypatch.setattr(consumer, "verify_geometry", bad_geometry)
    monkeypatch.setattr(consumer, "bound", no_native_reads)
    with pytest.raises(ValueError, match="synthetic angular certificate"):
        consumer.verify(tmp_path, tmp_path / "result.json")
