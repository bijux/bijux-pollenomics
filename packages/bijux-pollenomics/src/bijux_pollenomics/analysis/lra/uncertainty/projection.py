"""Compile modeled child inputs without altering the retained source catalogue."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .admission import AdmittedJointPlan
from .contracts import canonical, digest, refuse


def projections(
    admitted: AdmittedJointPlan,
) -> list[tuple[dict[str, Any], dict[str, Any] | None, dict[str, bytes]]]:
    plan = admitted.plan.payload()
    base = admitted.base()
    rows = []
    for draw in sorted(plan["realizations"], key=lambda item: item["draw_id"]):
        for band in sorted(plan["bins"], key=lambda item: item["bin_id"]):
            row, request, files = project(admitted, base, draw, band)
            rows.append((row, request, files))
    return rows


def project(
    admitted: AdmittedJointPlan,
    base: dict[str, Any],
    draw: dict[str, Any],
    band: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, bytes]]:
    selected = {
        role: [
            sample
            for sample in base[role]["samples"]
            if band["younger_bp"]
            <= draw["ages_by_sample_id"][sample["sample_id"]]
            < band["older_bp"]
        ]
        for role in ("regional", "local")
    }
    row_id = digest(canonical([draw["draw_id"], band["bin_id"]]))
    row = {
        "row_id": row_id,
        "draw_id": draw["draw_id"],
        "bin_id": band["bin_id"],
        "mass": draw["mass"],
        "selected_samples": {
            role: [s["sample_id"] for s in samples]
            for role, samples in selected.items()
        },
    }
    if any(len(values) != 1 for values in selected.values()):
        row.update(
            status="refused",
            reason_code="missing_role_in_bin"
            if any(not values for values in selected.values())
            else "ambiguous_role_in_bin",
        )
        return row, None, {}
    child = deepcopy(base)
    child["operation"] = "lra"
    files: dict[str, bytes] = {}
    evidence = child["evidence"]
    original_ids = {item["evidence_id"] for item in evidence}

    def modeled(role: str, detail: dict[str, Any]) -> str:
        value = {
            "schema_version": "lra-joint-modeled-input.v1",
            "plan_sha256": admitted.plan.sha256,
            "base_request_sha256": digest(canonical(base)),
            "draw": draw,
            "allocation_bin": band,
            "role": role,
            "detail": detail,
            "source_values_changed": False,
            "scientific_authenticity_verified": False,
        }
        encoded = canonical(value)
        identity = "joint-" + digest(encoded)
        if identity in original_ids:
            refuse("Generated evidence identity collides with original input")
        path = "__joint_realizations__/" + row_id + "/" + identity + ".json"
        if any(name == path for name, _ in admitted.files):
            refuse("Generated evidence path collides with original input")
        files[path] = encoded
        evidence.append(
            {
                "evidence_id": identity,
                "role": role,
                "path": path,
                "sha256": digest(encoded),
            }
        )
        return identity

    for role in ("regional", "local"):
        source = selected[role][0]
        sample = deepcopy(source)
        sample_id = source["sample_id"]
        age = draw["ages_by_sample_id"][sample_id]
        sample.update(
            counts=draw["counts_by_sample_id"][sample_id],
            age_support_bp=[[age, age]],
            age_type="calendar_bp",
            coordinate=0,
            bin_id=band["bin_id"],
        )
        sample["raw_evidence_id"] = modeled(
            "raw_snapshot",
            {
                "source_sample": source,
                "realized_counts": sample["counts"],
                "source_raw_evidence_id": source["raw_evidence_id"],
            },
        )
        sample["chronology_evidence_id"] = modeled(
            "chronology",
            {
                "source_sample": source,
                "realized_age_bp": age,
                "source_chronology_evidence_id": source["chronology_evidence_id"],
            },
        )
        child[role]["samples"] = [sample]
    for parameter in child["parameters"]:
        parameter["ppe"] = draw["ppe_by_taxon"][parameter["taxon"]]
        parameter["ppe_sd"] = 0
    modeled(
        "parameters",
        {
            "source_parameters": base["parameters"],
            "realized_parameters": child["parameters"],
        },
    )
    decision = modeled(
        "decision",
        {
            "allocation_rule": "younger_closed_older_open",
            "child_assumption": "declared_bin_stationarity",
            "source_temporal_matching": base["temporal_matching"],
        },
    )
    child["temporal_matching"] = {
        "rule": "declared_bin_stationarity",
        "decision_evidence_id": decision,
        "bins": [{k: band[k] for k in ("bin_id", "younger_bp", "older_bp")}],
    }
    included = {s[0]["sample_id"] for s in selected.values()}
    child["exclusions"] = deepcopy(base["exclusions"]) + [
        {"sample_id": s["sample_id"], "reason_code": "outside_joint_realization_bin"}
        for role in ("regional", "local")
        for s in base[role]["samples"]
        if s["sample_id"] not in included
    ]
    config = child["configuration"]
    config.setdefault("reveals", {}).update(
        iterations=1, stochastic=False, retain_samples=True
    )
    config["love"].update(
        repeats=1, stochastic=False, ppe_error=False, retain_samples=True
    )
    config["couple_regional_draws"] = True
    child["versions"] = {
        **child["versions"],
        "chronology": "modeled-joint-" + admitted.plan.sha256,
        "parameters": "modeled-joint-" + admitted.plan.sha256,
        "binning": "synthetic-half-open-calendar-bp-v1",
    }
    row.update(
        status="ready",
        reason_code=None,
        child_request_sha256=digest(canonical(child).rstrip(b"\n")),
    )
    return row, child, files
