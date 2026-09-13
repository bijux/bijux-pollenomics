"""Synthetic admitted prediction products with explicitly separate effort and outcomes."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from bijux_pollenomics.analysis.lra_validation.contracts import Fold, canonical_json
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
    folds = [
        Fold(
            "f" + str(i),
            tuple("p" + str(j) for j in range(1, 4) if j != i),
            ("p" + str(i),),
            tuple("g" + str(j) for j in range(1, 4) if j != i),
            ("g" + str(i),),
        )
        for i in range(1, 4)
    ]
    rows = []
    entries: list[EffortDeclaration] = []
    outcomes = {}
    for fold in folds:
        record = fold.test_record_ids[0]
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
            if failed and fold == folds[0]:
                continue
            external = ("region", "parameters", "geometry", "time")
            graph = dict.fromkeys((*fold.train_record_ids, *external), ())
            context = ForwardInputs(
                taxa,
                (0.1, 0.1),
                ((0.1, 0.1),),
                (1.0,),
                (1.0, 1.0),
                ("region",),
                ("parameters",),
                ("geometry",),
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
                {
                    g: dict(zip(taxa, (0.5, 0.5), strict=True))
                    for g in fold.train_group_ids
                },
                context,
                forward,
                spatial_method=method,
                training_input_ids=fold.train_record_ids,
                dependency_graph=graph,
                admitted_external_ids=external,
                distances_km={
                    g: float(i + 1) for i, g in enumerate(fold.train_group_ids)
                },
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
        "folds": [f.as_dict() for f in folds],
        "predictions": rows,
        "baselines": ["training_mean", "nearest_site"],
        "failures": [{"fold_id": folds[0].fold_id, "reason_code": "source_refused"}]
        if failed
        else [],
    }
    target = root / "predictions"
    stage = stage_directory(target)
    write_json(stage, "predictions.json", rows)
    write_json(
        stage,
        "experiment.json",
        {
            "request_template": {
                "taxa": list(taxa),
                "temporal_matching": {
                    "bins": [{"bin_id": "bin", "younger_bp": 0, "older_bp": 100}]
                },
            }
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
