"""Compute conditional composition for explicitly reported native pollen panels."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

import numpy as np

from bijux_pollenomics_lra.api import fixed_site_cover_covariance
from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus

from .sources import FAMILY, explicit_panel, load_inputs, selected_age, sha256

PARAMETERS = Path("data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv")


def parameter_vectors(
    repository: Path, taxa: list[str]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Require literal positive public parameter values on the selected taxon axis."""
    with (repository / PARAMETERS).open(newline="") as stream:
        rows = {
            row["Plant taxa/Pollen-morphological types"]: row
            for row in csv.DictReader(stream)
        }
    if len(rows) != 31 or not taxa or len(set(taxa)) != len(taxa):
        raise ValueError("parameter source or selected panel is ambiguous")
    ppe, deviation, fall = [], [], []
    for name in taxa:
        if name not in rows:
            raise ValueError("panel target lacks a literal public parameter row")
        parameter = rows[name]
        matched = re.fullmatch(r"([0-9.]+) \(([0-9.]+)\)", parameter["PPE (SD)"])
        if matched is None or re.fullmatch(r"[0-9.]+", parameter["FSP (m/s)"]) is None:
            raise ValueError("parameter annotation needs an explicit interpretation")
        values = (float(matched[1]), float(matched[2]), float(parameter["FSP (m/s)"]))
        if (
            any(not math.isfinite(value) for value in values)
            or values[0] <= 0
            or values[1] < 0
            or values[2] <= 0
        ):
            raise ValueError("public parameter values have invalid domains")
        ppe.append(values[0])
        deviation.append(values[1])
        fall.append(values[2])
    return np.asarray(ppe), np.asarray(deviation), np.asarray(fall)


def validate_protocol(protocol: dict[str, Any]) -> np.ndarray:
    """Require ordered age windows and distinct physical sensitivity profiles."""
    edges = np.asarray(protocol["age_window_edges_cal_bp"], dtype=float)
    if (
        edges.ndim != 1
        or len(edges) < 2
        or not np.isfinite(edges).all()
        or not np.all(np.diff(edges) > 0)
    ):
        raise ValueError("declared calendar BP windows must be strictly increasing")
    profiles = protocol["profiles"]
    ids = [profile["id"] for profile in profiles]
    if len(set(ids)) != len(ids) or "metadata_radius_wind_3" not in ids:
        raise ValueError(
            "sensitivity profiles need unique identities and a named baseline"
        )
    for profile in profiles:
        if any(
            not math.isfinite(profile[key]) or profile[key] <= 0
            for key in ("radius_multiplier", "wind_speed_m_s")
        ):
            raise ValueError(
                "sensitivity geometry and wind must be positive finite values"
            )
    if (
        protocol["historical_reproduction"] is not False
        or protocol["full_31_taxon_claim"] is not False
    ):
        raise ValueError(
            "this explicit-panel consumer cannot establish historical/full31 claims"
        )
    return edges


def _support_digest(samples: list[dict[str, Any]]) -> str:
    return hashlib.sha256(
        json.dumps(
            samples,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def reconstruct(repository: Path, candidate: str) -> dict[str, Any]:
    """Reconstruct only explicitly reported native pollen panels and their named ages."""
    if re.fullmatch(r"[0-9a-f]{40}", candidate) is None:
        raise ValueError("candidate must be an exact lowercase Git SHA")
    identity_path = repository / FAMILY / "inputs/source-identities.json"
    protocol_path = repository / FAMILY / "assumptions/protocol.json"
    producer_before = {
        path.name: sha256(path) for path in Path(__file__).parent.glob("*.py")
    }
    declaration_before = {path: sha256(path) for path in (identity_path, protocol_path)}
    protocol, datasets, metadata, identities = load_inputs(repository)
    edges = validate_protocol(protocol)
    output = []
    for selected in protocol["cores"]:
        code, did, chronology = (
            selected["metadata_code"],
            selected["native_dataset_id"],
            selected["chronology_id"],
        )
        taxa = selected["taxa"]
        ppe, deviation, fall = parameter_vectors(repository, taxa)
        covariance = np.diag(deviation**2)
        dataset, basin = datasets[did], metadata[code]
        radius = basin["radius_m"]
        grouped: dict[int, list[dict[str, Any]]] = {}
        exclusions: Counter[str] = Counter()
        excluded_support = []
        for sample in dataset["samples"]:
            age, reason = selected_age(sample, chronology)
            if reason is None:
                assert age is not None
                if not edges[0] <= age["age"] < edges[-1]:
                    reason = "point_age_outside_declared_windows"
            if reason is None:
                _, reason = explicit_panel(sample, taxa)
            if reason:
                exclusions[reason] += 1
                excluded_support.append(
                    {"sample_id": sample["sample_id"], "reason": reason}
                )
                continue
            assert age is not None
            index = int(np.searchsorted(edges, age["age"], side="right") - 1)
            grouped.setdefault(index, []).append(sample)
        deposition = {}
        quadrature = []
        for profile in protocol["profiles"]:
            physical_radius = radius * profile["radius_multiplier"]
            values = [
                circular_receiver_annulus(
                    receiver_radius_m=physical_radius,
                    inner_radius_m=physical_radius,
                    outer_radius_m=protocol["regional_extent_m"],
                    fall_speed_m_s=float(speed),
                    diffusion_coefficient=protocol["diffusion_coefficient"],
                    turbulence_parameter=protocol["turbulence_parameter"],
                    wind_speed_m_s=profile["wind_speed_m_s"],
                )
                for speed in fall
            ]
            deposition[profile["id"]] = np.asarray([[value.factor for value in values]])
            quadrature.append(
                {
                    "profile": profile["id"],
                    "factors": deposition[profile["id"]].tolist(),
                    "estimated_absolute_error": [
                        value.estimated_absolute_error for value in values
                    ],
                    "rigorous_error_bound": False,
                }
            )
        windows = []
        for index, samples in sorted(grouped.items()):
            counts = np.asarray(
                [[sum(sample["counts"][name] for sample in samples) for name in taxa]],
                dtype=np.int64,
            )
            ages = []
            for sample in samples:
                admitted_age, reason = selected_age(sample, chronology)
                assert reason is None and admitted_age is not None
                ages.append(admitted_age)
            support = [
                {
                    key: sample[key]
                    for key in (
                        "sample_id",
                        "analysis_unit_id",
                        "depth",
                        "ages",
                        "datum_rows",
                    )
                }
                for sample in samples
            ]
            scope = {
                "younger_cal_bp": float(edges[index]),
                "older_cal_bp_exclusive": float(edges[index + 1]),
                "native_sample_count": len(samples),
                "local_native_sample_support_sha256": _support_digest(support),
                "raw_age_bounds_missing": sum(
                    age.get("ageolder") is None and age.get("ageyounger") is None
                    for age in ages
                ),
                "counts": counts.tolist(),
                "panel_count_denominator": int(counts.sum()),
                "reported_all_pollen_NISP_sum": sum(
                    sample["reported_all_pollen_NISP_sum"] for sample in samples
                ),
                "direct_pollen_panel_fraction": (counts[0] / counts.sum()).tolist(),
            }
            for profile in protocol["profiles"]:
                k = deposition[profile["id"]]
                result = fixed_site_cover_covariance(
                    counts,
                    k,
                    ppe,
                    covariance,
                    taxon_measured=np.ones(counts.shape, dtype=bool),
                )
                inverse = counts[0] / (k[0] * ppe)
                inverse /= inverse.sum()
                if not np.allclose(result.cover, inverse, rtol=1e-12, atol=1e-14):
                    raise ValueError(
                        "maintained cover differs from independent inverse closure"
                    )
                if not np.allclose(
                    result.total_covariance,
                    result.counting_covariance + result.ppe_covariance,
                    rtol=1e-12,
                    atol=1e-14,
                ):
                    raise ValueError(
                        "maintained conditional covariance decomposition differs"
                    )
                windows.append(
                    {
                        **scope,
                        "profile": profile["id"],
                        "cover": result.cover.tolist(),
                        "standard_error": result.standard_error.tolist(),
                        "counting_covariance": result.counting_covariance.tolist(),
                        "ppe_covariance": result.ppe_covariance.tolist(),
                        "total_covariance": result.total_covariance.tolist(),
                    }
                )
            zero = fixed_site_cover_covariance(
                counts,
                deposition["metadata_radius_wind_3"],
                ppe,
                np.zeros_like(covariance),
                taxon_measured=np.ones(counts.shape, dtype=bool),
            )
            windows.append(
                {
                    "profile": "metadata_radius_wind_3_zero_ppe_uncertainty",
                    "younger_cal_bp": float(edges[index]),
                    "older_cal_bp_exclusive": float(edges[index + 1]),
                    "cover": zero.cover.tolist(),
                    "standard_error": zero.standard_error.tolist(),
                }
            )
        output.append(
            {
                "metadata_code": code,
                "publication_row": basin["publication_row"],
                "native_dataset_id": did,
                "native_site_id": dataset["native_site_id"],
                "native_collection_unit_id": dataset["native_collection_unit_id"],
                "source_core_handle": dataset["source_core_handle"],
                "chronology_id": chronology,
                "source_default_chronology": dataset["source_default_chronology"],
                "selected_chronology": dataset["selected_chronology"],
                "source_dataset": dataset["source_dataset"],
                "metadata_static_radius_m": radius,
                "metadata_disk_area_m2": math.pi * radius**2,
                "parameter_taxa": taxa,
                "ppe": ppe.tolist(),
                "ppe_standard_deviation": deviation.tolist(),
                "ppe_covariance": covariance.tolist(),
                "fall_speed_m_s": fall.tolist(),
                "historical_metadata_access_flag": basin["fields"][
                    "DataRestricted/NotRestriced"
                ],
                "native_sample_count": len(dataset["samples"]),
                "included_sample_count": sum(map(len, grouped.values())),
                "exclusions_by_reason": dict(exclusions),
                "local_native_exclusions_sha256": _support_digest(excluded_support),
                "occupied_window_count": len(grouped),
                "quadrature": quadrature,
                "results": windows,
            }
        )
    if not all(core["occupied_window_count"] > 0 for core in output):
        raise ValueError("a declared supported core has no executable explicit panel")
    # Each bound source is checked again after computation, including maintained engine files.
    from .sources import read_bound

    for name, identity in identities.items():
        read_bound(repository, name, identity)
    if any(sha256(path) != value for path, value in declaration_before.items()):
        raise ValueError("producer declaration changed during computation")
    producer_after = {
        path.name: sha256(path) for path in Path(__file__).parent.glob("*.py")
    }
    if producer_after != producer_before:
        raise ValueError("maintained producer source changed during computation")
    return {
        "producer_source_sha256": producer_before,
        "candidate_binding_scope": "Declared exact source revision; external immutable execution receipt establishes actual checkout/overlay custody. The SHA argument alone does not authenticate Git history.",
        "schema_version": "swedish-static-basin-maintained-producer.v1",
        "producer_candidate": candidate,
        "protocol": protocol,
        "source_files": identities,
        "source_identity_declaration_sha256": declaration_before[identity_path],
        "protocol_authority": "Authored scientific assumption input; exact bytes bound by the independent execution receipt, not a generated numerical-output authority.",
        "protocol_sha256": sha256(repository / FAMILY / "assumptions/protocol.json"),
        "cores": output,
        "historical_reproduction_claimed": False,
        "full_31_target_reconstruction_claimed": False,
        "vegetation_accuracy_claimed": False,
        "chronology_or_geometry_uncertainty_quantified": False,
        "source_lake_algorithm_parity_claimed": False,
        "distribution_of_raw_source_counts_authorized": False,
    }
