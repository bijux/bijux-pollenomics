"""Reader-valid retained joint fixtures without optional numerical imports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from bijux_pollenomics.analysis.lra.outputs.contracts import request_metadata
from bijux_pollenomics.analysis.lra.outputs.reading import read_lra_product
from bijux_pollenomics.analysis.lra.uncertainty.admission import admit
from bijux_pollenomics.analysis.lra.uncertainty.contracts import (
    SCOPE,
    JointLRAPlan,
    canonical,
    digest,
)
from bijux_pollenomics.analysis.lra.uncertainty.projection import projections
from bijux_pollenomics.analysis.lra.uncertainty.reading import (
    denominators,
    inventory,
    read_joint_lra_ensemble,
    scientific_identity,
)
from bijux_pollenomics.analysis.lra.uncertainty.statistics import (
    child_values,
    summaries,
)
from tests.unit.analysis.lra.support import request_fixture

FixtureState = Literal["complete", "refused", "interrupted"]


def _code_identity() -> dict[str, dict[str, str]]:
    runtime = {
        "python": "fixture",
        "platform": "fixture",
        "bijux-pollenomics": "fixture",
        "numpy": "not-imported",
        "scipy": "not-imported",
        "pandas": "not-imported",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
    }
    return {
        "engine_files": {"api.py": "0" * 64},
        "host_adapter_files": {"api.py": "1" * 64},
        "host_publication_files": {"core/owned_tree.py": "2" * 64},
        "runtime_environment": runtime,
    }


def _base_and_plan(source: Path, bin_id: str) -> dict[str, Any]:
    source.mkdir(parents=True)
    base = request_fixture(source, "series")
    base["temporal_matching"]["bins"] = [
        {"bin_id": "source", "younger_bp": 50, "older_bp": 250}
    ]
    for role in ("regional", "local"):
        original = base[role]["samples"][0]
        base[role]["samples"] = [
            {
                **original,
                "sample_id": role + str(index),
                "bin_id": "source",
                "coordinate": index,
                "counts": counts,
                "age_support_bp": support,
            }
            for index, counts, support in (
                (1, [1, 3], [[50, 150]]),
                (2, [3, 1], [[150, 250]]),
            )
        ]
    for parameter in base["parameters"]:
        parameter.update(ppe=1, fallspeed_m_s=0.05)
    base["configuration"]["reveals"].update(iterations=1)
    base["configuration"]["love"].update(repeats=1)
    (source / "base.json").write_bytes(canonical(base))
    (source / "law.txt").write_text(
        "Explicit synthetic finite law; scientific authenticity unverified.\n",
        encoding="utf-8",
    )
    realizations = []
    for shift, ages in enumerate(((50, 150), (150, 250))):
        for ppe in (1, 3):
            realizations.append(
                {
                    "draw_id": f"draw-{shift}-{ppe}",
                    "mass": {"numerator": 1, "denominator": 4},
                    "ppe_realization_id": f"ppe-{ppe}",
                    "ppe_by_taxon": {"Alnus": ppe, "Betula": 1},
                    "chronology_realization_id": f"chronology-{shift}",
                    "ages_by_sample_id": {
                        role + str(index): age
                        for role in ("regional", "local")
                        for index, age in enumerate(ages, 1)
                    },
                    "count_realization_id": "counts-fixed",
                    "counts_by_sample_id": {
                        sample["sample_id"]: sample["counts"]
                        for role in ("regional", "local")
                        for sample in base[role]["samples"]
                    },
                }
            )
    return {
        "schema_version": "lra-joint-realizations.v1",
        "profile": "synthetic-explicit-joint-analytical-v1",
        "purpose": "exploratory",
        "data_kind": "synthetic",
        "base_request_ref": {
            "path": "base.json",
            "sha256": digest((source / "base.json").read_bytes()),
        },
        "law_evidence_ref": {
            "path": "law.txt",
            "sha256": digest((source / "law.txt").read_bytes()),
        },
        "bins": [
            {
                "bin_id": bin_id,
                "younger_bp": 100,
                "older_bp": 200,
                "membership": "younger_closed_older_open",
            }
        ],
        "realizations": realizations,
        "limits": {
            "max_realizations": 64,
            "max_child_runs": 512,
            "max_draw_cells": 1_000_000,
            "max_covariance_cells": 1_000_000,
        },
    }


def _write_child(
    directory: Path,
    request: dict[str, Any],
    code: dict[str, dict[str, str]],
    regional_alnus: float,
    local_alnus: float,
) -> None:
    regional_betula, local_betula = 1 - regional_alnus, 1 - local_alnus
    regional = directory / "numerical/regional_reveals"
    local = directory / "numerical/local_love"
    regional.mkdir(parents=True)
    local.mkdir(parents=True)
    taxa = request["taxa"]
    statistics = ("mean", "median", "q90", "q10", "sd")
    header = ["Distance.weighting", "Basin.type", "coordinate"] + [
        f"{taxon}.{statistic}" for statistic in statistics for taxon in taxa
    ]
    pair = [regional_alnus * 100, regional_betula * 100]
    values: list[object] = []
    for statistic in statistics:
        values.extend(["", ""] if statistic == "sd" else pair)
    regional.joinpath("reconstruction.csv").write_text(
        ",".join(header)
        + "\n"
        + ",".join(
            str(value)
            for value in [
                1,
                request["regional"]["basin"]["site_type"],
                request["regional"]["samples"][0]["coordinate"],
                *values,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    regional.joinpath("deposition_factors.csv").write_text(
        "index,K\n" + "".join(f"{taxon},1\n" for taxon in taxa),
        encoding="utf-8",
    )
    regional.joinpath("result_contract.json").write_bytes(
        canonical(
            {
                "schema_version": "1.0.0",
                "result_type": "reveals",
                "primary_artifact": "reconstruction.csv",
                "units": {"cover": "percent", "distance": "metre"},
            }
        )
    )
    local.joinpath("cover_mean.csv").write_text(
        "index," + ",".join(taxa) + "\n"
        f"{request['rings'][0]['mean_m']},{local_alnus},{local_betula}\n",
        encoding="utf-8",
    )
    local.joinpath("result_contract.json").write_bytes(
        canonical(
            {
                "schema_version": "1.0.0",
                "result_type": "love",
                "primary_artifact": "cover_mean.csv",
                "units": {
                    "cover": "fraction",
                    "distance": "metre",
                    "pollen_percentages": "percent",
                },
                "method": "analytical",
            }
        )
    )
    (directory / "request.json").write_bytes(canonical(request))
    scientific = {"fixture": "retained joint presentation boundary"}
    (directory / "scientific_manifest.json").write_bytes(canonical(scientific))
    numerical = {
        path.relative_to(directory / "numerical").as_posix(): digest(path.read_bytes())
        for path in sorted((directory / "numerical").rglob("*"))
        if path.is_file()
    }
    request_sha = digest(canonical(request).rstrip(b"\n"))
    engine = {"package": "synthetic-report-fixture"}
    identity: dict[str, Any] = {
        "request_sha256": request_sha,
        "engine": engine,
        "engine_scientific_manifest": scientific,
        "numerical_files": numerical,
        **code,
    }
    child_manifest = {
        "schema_version": "lra-product.v1",
        "status": "generated_exploratory",
        "scientific_acceptance": "not_evaluated",
        **request_metadata(request),
        "request_sha256": request_sha,
        "scientific_content_sha256": digest(canonical(identity)),
        "scientific_identity": identity,
        "engine": engine,
        "files": {
            path.relative_to(directory).as_posix(): digest(path.read_bytes())
            for path in sorted(directory.rglob("*"))
            if path.is_file() and path != directory / "manifest.json"
        },
    }
    (directory / "manifest.json").write_bytes(canonical(child_manifest))
    read_lra_product(
        directory,
        expected_manifest_sha256=digest((directory / "manifest.json").read_bytes()),
    )


def joint_fixture(
    root: Path,
    *,
    state: FixtureState = "complete",
    bin_id: str = "target",
) -> tuple[Path, str]:
    source = root / "source-input"
    plan_payload = _base_and_plan(source, bin_id)
    plan = JointLRAPlan.from_dict(plan_payload)
    admitted = admit(plan, source)
    product = root / "joint-product"
    retained_source = product / "source"
    for name, value in admitted.files:
        path = retained_source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    (product / "plan.json").write_text(plan.canonical_json, encoding="utf-8")
    code = _code_identity()
    prepared = projections(admitted)
    rows: list[dict[str, Any]] = []
    # Regional and local sequences are orthogonal, while each role's second
    # taxon is its complement.  The retained fixture therefore exercises
    # positive, negative and exactly zero covariance cells.
    values = ((0.2, 0.2), (0.4, 0.8), (0.6, 0.8), (0.8, 0.2))
    interrupted = state == "interrupted"
    for index, (selection, request, generated) in enumerate(prepared):
        for name, value in generated.items():
            path = retained_source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        if request is None:
            rows.append(selection)
            continue
        row = dict(selection)
        if state == "refused" and index == 1:
            row.update(
                status="refused",
                reason_code="numerical_refusal",
                error={
                    "status": "refused",
                    "reason_code": "no_valid_local_rings",
                    "detail": "controlled retained fixture refusal",
                    "diagnostics": {"finite_rings": 0},
                },
            )
        elif state == "interrupted" and index > 0:
            row.update(status="not_run", reason_code="interrupted")
        else:
            child = product / "children" / f"{index:04d}"
            _write_child(
                child,
                request,
                code,
                values[index][0],
                values[index][1],
            )
            child_checksum = digest((child / "manifest.json").read_bytes())
            verified = read_lra_product(child, expected_manifest_sha256=child_checksum)
            coordinates, vector = child_values(child, request)
            row.update(
                status="success",
                reason_code=None,
                child=f"children/{index:04d}",
                child_manifest_sha256=child_checksum,
                child_scientific_content_sha256=verified.product.scientific_content_sha256,
                coordinates=coordinates,
                values=vector,
            )
        rows.append(row)
    counts = denominators(rows)
    manifest: dict[str, Any] = {
        "schema_version": "lra-joint-product.v1",
        "profile": "synthetic-explicit-joint-analytical-v1",
        "scientific_acceptance": "not_evaluated",
        "status": "complete"
        if counts["successful_draw_bins"] == len(rows)
        else "incomplete",
        "interrupted": interrupted,
        "plan_sha256": plan.sha256,
        "base_request_sha256": digest(admitted.base_json.encode("utf-8")),
        "code_identity": code,
        "rows": rows,
        "denominators": counts,
        "summaries": summaries(rows, [bin_id]),
        "uncertainty_scope": SCOPE,
    }
    manifest["scientific_content_sha256"] = digest(
        canonical(scientific_identity(manifest))
    )
    manifest["files"] = inventory(product)
    (product / "manifest.json").write_bytes(canonical(manifest))
    checksum = digest((product / "manifest.json").read_bytes())
    read_joint_lra_ensemble(product, expected_manifest_sha256=checksum)
    return product, checksum


__all__ = ["FixtureState", "joint_fixture"]
