"""Actual train-only REVEALS/LOVE batches and strictly reopened compositions."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from ...lra.api import LRABatchItem, LRABatchLimits, read_lra_product, run_lra_batch
from ...lra.outputs.publication import LRAProduct
from ..contracts import Fold, ValidationRefusal, finite_number, manifest_sha256
from ..metrics import closed_composition
from .configuration import (
    ExperimentScope,
    ExperimentSite,
    ExperimentSpec,
    object_list,
    object_mapping,
)
from .inputs import make_request


@dataclass(frozen=True)
class FoldFits:
    """Observed training fits with regional anchor kept in outer training ancestry."""

    anchor: ExperimentSite
    predictors: tuple[ExperimentSite, ...]
    compositions: dict[str, dict[str, float]]
    regional_cover: tuple[float, ...]
    fit_identities: tuple[dict[str, object], ...]
    operational_batch: dict[str, object]


def _table(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValidationRefusal("empty_reconstruction_table", str(path))
    return rows


def reconstruct_fold(
    spec: ExperimentSpec,
    fold: Fold,
    group_by_record: dict[str, str],
    *,
    input_root: Path,
    cache_root: Path,
    report_root: Path,
    workers: int,
) -> FoldFits:
    """Use one declared eligible physical basin, never pooled counts/mean geometry."""
    by_record = {site.record.record_id: site for site in spec.sites}
    eligible = [
        record for record in spec.regional_priority if record in fold.train_record_ids
    ]
    if not eligible:
        raise ValidationRefusal("missing_regional_anchor", fold.fold_id)
    anchor = by_record[eligible[0]]
    anchor_group = group_by_record[anchor.record.record_id]
    predictors = tuple(
        by_record[record]
        for record in fold.train_record_ids
        if group_by_record[record] != anchor_group
    )
    if not predictors:
        raise ValidationRefusal("missing_local_predictors", fold.fold_id)
    if len({group_by_record[record] for record in fold.train_record_ids}) != len(
        fold.train_record_ids
    ):
        raise ValidationRefusal(
            "unsupported_multi_record_group",
            "A reviewed within-group observation selection is required",
        )
    items = [
        LRABatchItem(
            site.record.record_id, make_request(spec, site, anchor, fold, input_root)
        )
        for site in predictors
    ]
    batch = run_lra_batch(
        items,
        input_root=input_root,
        cache_root=cache_root,
        report_root=report_root,
        limits=LRABatchLimits(max_workers=workers, max_items=len(items)),
    )
    if batch.interrupted:
        raise ValidationRefusal("experiment_interrupted", str(report_root))
    if not batch.all_items_completed:
        # Durable per-item diagnostics remain in the owned batch receipt.
        raise ValidationRefusal("training_reconstruction_incomplete", str(report_root))
    compositions: dict[str, dict[str, float]] = {}
    identities = []
    common_regional: tuple[float, ...] | None = None
    for item, declared in zip(batch.items, items, strict=True):
        if item.product is None:
            raise ValidationRefusal("missing_training_product", item.item_id)
        product = item.product
        request = declared.payload()
        composition, regional, extracted = extract_reconstruction(
            product, request, spec
        )
        compositions[group_by_record[item.item_id]] = composition
        if common_regional is not None and regional != common_regional:
            raise ValidationRefusal(
                "inconsistent_regional_reconstruction",
                "Deterministic shared anchor differs across fits",
            )
        common_regional = regional
        identities.append(
            {
                "record_id": item.item_id,
                "group_id": group_by_record[item.item_id],
                "request_sha256": item.request_sha256,
                **extracted,
            }
        )
    if common_regional is None:
        raise ValidationRefusal("missing_regional_reconstruction", fold.fold_id)
    return FoldFits(
        anchor,
        predictors,
        compositions,
        common_regional,
        tuple(identities),
        batch.as_dict(),
    )


def extract_reconstruction(
    product: LRAProduct, request: dict[str, object], spec: ExperimentScope
) -> tuple[dict[str, float], tuple[float, ...], dict[str, object]]:
    """Reopen and extract actual paired numerical output without clipping or normalization."""
    verified = read_lra_product(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    manifest = verified.manifest()
    taxa = tuple(str(value) for value in object_list(spec.template()["taxa"], "taxa"))
    local_rows = _table(product.directory / "numerical/local_love/cover_mean.csv")
    if len(local_rows) != spec.local_ring_count:
        raise ValidationRefusal(
            "reconstruction_radius_mismatch", str(product.directory)
        )
    row = local_rows[spec.local_ring_count - 1]
    ring = object_mapping(
        object_list(request["rings"], "rings")[spec.local_ring_count - 1], "ring"
    )
    if set(row) != {"index", *taxa} or finite_number(
        float(row["index"])
    ) != finite_number(ring["mean_m"]):
        raise ValidationRefusal(
            "reconstruction_radius_mismatch", str(product.directory)
        )
    composition = closed_composition(
        {taxon: finite_number(float(row[taxon])) for taxon in taxa}
    )
    regional_rows = _table(
        product.directory / "numerical/regional_reveals/reconstruction.csv"
    )
    if len(regional_rows) != 1:
        raise ValidationRefusal("regional_reconstruction_shape", str(product.directory))
    regional = tuple(
        finite_number(float(regional_rows[0][taxon + ".mean"])) / 100 for taxon in taxa
    )
    read_lra_product(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    extracted: dict[str, object] = {
        "scientific_content_sha256": product.scientific_content_sha256,
        "scientific_identity_sha256": manifest_sha256(manifest["scientific_identity"]),
        "source_radius_label_m": float(row["index"]),
        "local_support_radius_m": finite_number(ring["outer_m"]),
        "support_profile": spec.support_profile,
        "composition": composition,
    }
    return composition, regional, extracted
