"""Pinned synthetic older inputs and distinct younger target support."""

import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    FITTED_METHOD,
    FITTED_PROFILE,
    FittedSpatialExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out
from bijux_pollenomics.analysis.lra_validation.temporal import (
    CalendarSupport,
    RecordChronology,
    TemporalAdmissionPlan,
)
from bijux_pollenomics.analysis.lra_validation.temporal.persistence.configuration import (
    TemporalPersistenceSpec,
    YoungerCalendarBin,
)

from ...experiments.test_inputs import fixture_inputs, store


def fixture_payload(root: Path) -> dict[str, Any]:
    payload = fixture_inputs(root)
    payload.pop("baselines")
    payload["profile"] = FITTED_PROFILE
    payload["method"] = {
        "profile": FITTED_METHOD,
        "length_scale_km": 10,
        "ridge_penalty": 0.1,
    }
    target = payload["sites"][-1]
    geometry = json.loads((root / target["geometry"]["path"]).read_text())
    geometry["sample_metadata"].update(
        bin_id="younger", coordinate=2, age_support_bp=[[4900, 5000]]
    )
    target["geometry"] = store(root, target["geometry"]["path"], geometry)
    return payload


def spec_from_payload(
    payload: dict[str, Any], *, maximum_lead: float = 1000
) -> TemporalPersistenceSpec:
    older = FittedSpatialExperimentSpec(payload)
    folds = grouped_leave_one_out([site.record for site in older.sites])
    target = older.sites[-1].record.record_id
    fold = next(row for row in folds if row.test_record_ids == (target,))
    ownership = tuple(
        (record, row.test_group_ids[0])
        for row in folds
        for record in row.test_record_ids
    )
    sha = next(
        row["sha256"]
        for row in payload["request_template"]["evidence"]
        if row["role"] == "chronology"
    )
    supports = tuple(
        RecordChronology(
            site.record.record_id,
            CalendarSupport(
                ((4900, 5000),) if site.record.record_id == target else ((5400, 5600),),
                sha,
                "declared-model-different-from-evidence-id",
            ),
        )
        for site in older.sites
    )
    plan = TemporalAdmissionPlan(
        fold,
        ownership,
        supports,
        (older.regional_priority[0],),
        400,
        maximum_lead,
        "a" * 64,
        "synthetic chronology declaration; no reviewer approval",
    )
    return TemporalPersistenceSpec(
        older,
        plan,
        YoungerCalendarBin("younger", 4900, 5000),
        "b" * 64,
        "synthetic no-change assumption",
    )


def refused_product(root: Path) -> tuple[object, TemporalPersistenceSpec]:
    """Generate an actual complete chronology refusal without a numerical dependency."""
    from bijux_pollenomics.analysis.lra_validation.temporal.persistence.workflow import (
        prepare_temporal_persistence_predictions,
    )

    spec = spec_from_payload(fixture_payload(root / "inputs"), maximum_lead=400)
    product = prepare_temporal_persistence_predictions(
        spec,
        input_root=root / "missing",
        cache_root=root / "cache",
        destination=root / "predictions",
    )
    return product, spec


def rehash_product(directory: Path, scientific: dict[str, Any]) -> str:
    """Give adversarial retained metadata a fully self-consistent byte inventory."""
    import hashlib

    from bijux_pollenomics.analysis.lra_validation.contracts import (
        canonical_json,
        manifest_sha256,
    )

    for name, key in (
        ("folds.json", "folds"),
        ("predictions.json", "predictions"),
        ("failures.json", "failures"),
        ("admission.json", "source_admission"),
        ("training.json", "older_training_state"),
    ):
        (directory / name).write_text(canonical_json(scientific[key]) + "\n")
    manifest = json.loads((directory / "manifest.json").read_text())
    manifest["scientific_payload"] = scientific
    manifest["scientific_content_sha256"] = manifest_sha256(scientific)
    manifest["files"] = {
        path.relative_to(directory).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in directory.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    # Nested LRA manifests remain ordinary inventoried members.
    for path in directory.rglob("manifest.json"):
        if path != directory / "manifest.json":
            manifest["files"][path.relative_to(directory).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    content = (canonical_json(manifest) + "\n").encode()
    (directory / "manifest.json").write_bytes(content)
    return hashlib.sha256(content).hexdigest()
