"""Synthetic admitted prediction products with explicitly separate effort and outcomes."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from bijux_pollenomics.analysis.lra_validation.contracts import (
    canonical_json,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    ExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    ExperimentProduct,
    publish_phase,
    stage_directory,
    write_json,
)
from bijux_pollenomics.analysis.lra_validation.observation_uncertainty import (
    EffortDeclaration,
    ObservationUncertaintyPlan,
)
from bijux_pollenomics.analysis.lra_validation.prediction import (
    ForwardInputs,
    predict_withheld_site,
)
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out

from ..experiments.reading.test_provenance import (
    fixture_identities,
    retained_fold_evidence,
    write_retained_evidence,
)
from ..experiments.test_inputs import fixture_inputs


def store(root: Path, name: str, payload: object) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    path = root / name
    path.write_text(canonical_json(payload) + "\n")
    return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def fixture(
    root: Path,
    *,
    failed: bool = False,
    counts: dict[str, int | None] | None = None,
    taxa: tuple[str, str] = ("a", "b"),
) -> tuple[ExperimentProduct, ObservationUncertaintyPlan, dict[str, Any]]:
    declaration = fixture_inputs(root / "source", count=3)
    declaration["baselines"] = ["training_mean", "nearest_site"]
    template = declaration["request_template"]
    template["taxa"] = list(taxa)
    for parameter, taxon in zip(template["parameters"], taxa, strict=True):
        parameter["taxon"] = taxon
    template["temporal_matching"]["bins"] = [
        {"bin_id": "bin", "younger_bp": 0, "older_bp": 100}
    ]
    for index, site in enumerate(declaration["sites"], start=1):
        name = "p" + str(index)
        site.update(record_id=name, site_id=name)
        for field in ("raw", "geometry"):
            data = json.loads((root / "source" / site[field]["path"]).read_text())
            sample = data["sample"] if field == "raw" else data["sample_metadata"]
            sample.update(
                site_id=name,
                sample_id=name + "-sample",
                bin_id="bin",
                age_support_bp=[[0, 100]],
            )
            if field == "raw":
                data["taxa"] = list(taxa)
            site[field] = store(root / "source", site[field]["path"], data)
    declaration["regional_priority"] = [
        site["record_id"] for site in declaration["sites"]
    ]
    spec = ExperimentSpec(declaration)
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    failed_fold = next(fold for fold in folds if fold.test_record_ids == ("p1",))
    rows = []
    training_rows = []
    batches = []
    entries: list[EffortDeclaration] = []
    outcomes = {}
    for fold in folds:
        record = fold.test_record_ids[0]
        training, batch = retained_fold_evidence(
            spec, fold, root / "source", dict(zip(taxa, (0.5, 0.5), strict=True))
        )
        batches.append(batch)
        if not (failed and fold == failed_fold):
            training_rows.append(training)
        regional_id, parameter_id, geometry_id = fixture_identities(
            spec, record, training
        )
        predictors = tuple(training["predictor_group_ids"])
        evidence = store(
            root / "effort",
            record + ".json",
            {
                "schema_version": "lra-synthetic-counting-design.v1",
                "data_kind": "synthetic",
                "record_id": record,
                "bin_id": "bin",
                "planned_effort": 10,
                "effort_unit": "pollen_grains",
                "timing_declaration": "before_outcome_access",
                "declaration_provenance": "Synthetic fixture protocol, not observed count total",
            },
        )
        outcomes[record] = store(
            root / "outcomes",
            record + ".json",
            {
                "schema_version": "lra-experiment-observation.v1",
                "data_kind": "synthetic",
                "record_id": record,
                "bin_id": "bin",
                "vegetation_unit": "fraction",
                "pollen_unit": "count",
                "vegetation_fraction": dict(zip(taxa, (0.5, 0.5), strict=True)),
                "pollen_count": dict(zip(taxa, (7, 3), strict=True))
                if counts is None
                else counts,
            },
        )
        for method in ("training_mean", "nearest_site"):
            entries.append(
                EffortDeclaration(
                    fold.fold_id,
                    record,
                    "bin",
                    method,
                    taxa,
                    10,
                    len(entries),
                    evidence["path"],
                    evidence["sha256"],
                )
            )
            if failed and fold == failed_fold:
                continue
            external = (regional_id, parameter_id, geometry_id, "time")
            graph: dict[str, tuple[str, ...]] = dict.fromkeys(
                (*fold.train_record_ids, *external), ()
            )
            graph[regional_id] = fold.train_record_ids
            context = ForwardInputs(
                taxa,
                (0.1, 0.1),
                ((0.1, 0.1), (0.1, 0.1)),
                (1.0, 1.0),
                (4.0, 3.0),
                (regional_id,),
                (parameter_id,),
                (geometry_id,),
                "time",
                "synthetic-forward-fixture",
                "fixture-build",
            )

            def forward(
                local_cover: tuple[float, ...],
                regional_deposition: tuple[float, ...],
                local_k: tuple[tuple[float, ...], ...],
                terrestrial_fraction: tuple[float, ...],
                ppe: tuple[float, ...],
            ) -> Any:
                return SimpleNamespace(
                    pollen_fraction=(0.7, 0.3),
                    method_profile="synthetic-forward-fixture",
                )

            result = predict_withheld_site(
                fold,
                fold.test_group_ids[0],
                {g: dict(zip(taxa, (0.5, 0.5), strict=True)) for g in predictors},
                context,
                forward,
                spatial_method=method,
                predictor_group_ids=predictors,
                training_input_ids=fold.train_record_ids,
                dependency_graph=graph,
                admitted_external_ids=external,
                distances_km={g: float(i + 1) for i, g in enumerate(predictors)},
            )
            rows.append(
                {
                    "fold_id": fold.fold_id,
                    "record_id": record,
                    "bin_id": "bin",
                    "baseline": method,
                    "vegetation_fraction": dict(result.vegetation_fraction),
                    "pollen_fraction": dict(result.pollen_fraction),
                    "prediction_manifest": json.loads(result.input_manifest_json),
                    "prediction_manifest_sha256": result.prediction_manifest_sha256,
                }
            )
    scientific = {
        "profile": "synthetic-withheld-site-baselines-v1",
        "experiment": "all_target_pollen_withheld",
        "uncertainty_status": "point_predictions_only_intervals_not_implemented",
        "interrupted": False,
        "requested_folds": len(folds),
        "requested_predictions": len(folds) * 2,
        "generated_predictions": len(rows),
        "failed_folds": int(failed),
        "all_predictions_generated": not failed,
        "split_manifest_sha256": manifest_sha256([fold.as_dict() for fold in folds]),
        "folds": [f.as_dict() for f in folds],
        "predictions": rows,
        "baselines": ["training_mean", "nearest_site"],
        "failures": [
            {
                "fold_id": failed_fold.fold_id,
                "record_ids": failed_fold.test_record_ids,
                "status": "refused",
                "reason_code": "source_refused",
            }
        ]
        if failed
        else [],
    }
    target = root / "predictions"
    stage = stage_directory(target)
    write_json(stage, "predictions.json", rows)
    write_retained_evidence(stage, training_rows, batches)
    write_json(
        stage,
        "experiment.json",
        {
            "profile": "synthetic-withheld-site-baselines-v1",
            "request_template": spec.template(),
            "regional_priority": spec.regional_priority,
            "local_ring_count": spec.local_ring_count,
            "local_support_radius_m": spec.local_support_radius_m,
            "support_profile": spec.support_profile,
            "source_catalogue": [
                {
                    "record_id": site.record.record_id,
                    "site_id": site.record.site_id,
                    "identity_keys": site.record.identity_keys,
                    "raw_path": site.raw.path,
                    "raw_sha256": site.raw.sha256,
                    "geometry_path": site.geometry.path,
                    "geometry_sha256": site.geometry.sha256,
                }
                for site in spec.sites
            ],
        },
    )
    product = publish_phase(stage, target, phase="predictions", scientific=scientific)
    plan = ObservationUncertaintyPlan(product.manifest_sha256, tuple(entries), 10, 0.9)
    return (
        product,
        plan,
        {
            "schema_version": "lra-experiment-outcomes.v1",
            "data_kind": "synthetic",
            "records": outcomes,
        },
    )


def rewrite(
    product: ExperimentProduct,
    *,
    phase: str | None = None,
    profile: str | None = None,
    payload_change: Any = None,
    member: str | None = None,
    member_change: Any = None,
) -> ExperimentProduct:
    """Rehash a test-owned product to challenge semantics beyond ordinary tampering."""
    from bijux_pollenomics.analysis.lra_validation.contracts import manifest_sha256

    root = product.directory
    manifest = json.loads((root / "manifest.json").read_text())
    if phase is not None:
        manifest["phase"] = phase
    if profile is not None:
        manifest["profile"] = profile
    if member is not None:
        rows = json.loads((root / member).read_text())
        member_change(rows)
        (root / member).write_text(canonical_json(rows) + "\n")
        field = "rows" if member == "uncertainty.json" else "scores"
        manifest["scientific_payload"][field] = rows
    if payload_change is not None:
        payload_change(manifest["scientific_payload"])
    manifest["scientific_content_sha256"] = manifest_sha256(
        manifest["scientific_payload"]
    )
    manifest["files"] = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file() and p.name != "manifest.json"
    }
    (root / "manifest.json").write_text(canonical_json(manifest) + "\n")
    return ExperimentProduct(
        root,
        hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest(),
        manifest["scientific_content_sha256"],
    )
