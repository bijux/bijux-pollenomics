"""Bind declarations to retained request bodies and predictive source identities."""

from __future__ import annotations

from ....lra.batches.models import LRABatchItem
from ...contracts import (
    ValidationRefusal,
    canonical_json,
    finite_number,
    manifest_sha256,
)
from ..configuration import FITTED_PROFILE, identity, object_list, object_mapping
from ..outputs import ExperimentProduct, read_member


def _same(left: object, right: object, label: str) -> None:
    if canonical_json(left) != canonical_json(right):
        raise ValidationRefusal("retained_source_identity_mismatch", label)


def validate_singleton_provenance(
    product: ExperimentProduct,
    manifest: dict[str, object],
    metadata: dict[str, object],
    folds: dict[str, dict[str, object]],
    predictions: dict[tuple[str, str], dict[str, object]],
) -> None:
    """Read authenticated product members only; never follow cache or raw-source paths."""
    fitted = manifest["profile"] == FITTED_PROFILE
    files = object_mapping(manifest["files"], "files")
    catalogue = {
        identity(row["record_id"]): row
        for value in object_list(metadata["source_catalogue"], "source_catalogue")
        if (row := object_mapping(value, "source"))
    }
    template = object_mapping(metadata["request_template"], "template")
    successful = {key[0] for key in predictions}
    training: dict[str, dict[str, object]] = {}
    if not fitted and successful:
        for value in object_list(read_member(product, "training.json"), "training"):
            row = object_mapping(value, "training")
            fold_id = identity(row["fold_id"])
            if fold_id in training:
                raise ValidationRefusal("duplicate_retained_training", fold_id)
            training[fold_id] = row
        if set(training) != successful:
            raise ValidationRefusal(
                "retained_training_inventory_mismatch",
                "Exactly completed folds required",
            )
    for index, (fold_id, outer) in enumerate(folds.items()):
        name = f"batches/fold-{index:04}/receipt.json"
        if name not in files:
            if fold_id in successful:
                raise ValidationRefusal("missing_retained_batch_request", fold_id)
            continue
        batch = object_mapping(read_member(product, name), "batch")
        if batch["event"] != "attempt_started":
            raise ValidationRefusal("invalid_retained_batch_request", fold_id)
        admitted = object_list(outer["train_record_ids"], "train_record_ids")
        anchor = next(
            (
                identity(value)
                for value in object_list(
                    metadata["regional_priority"], "regional_priority"
                )
                if value in admitted
            ),
            None,
        )
        if anchor is None:
            raise ValidationRefusal("retained_regional_identity_mismatch", fold_id)
        items: dict[str, dict[str, object]] = {}
        for value in object_list(batch["items"], "items"):
            item = object_mapping(value, "item")
            record = identity(item["item_id"])
            if record in items or record not in admitted or record == anchor:
                raise ValidationRefusal("retained_request_membership_mismatch", record)
            request = object_mapping(item["request"], "request")
            _same(
                LRABatchItem(record, request).request_sha256,
                item["request_sha256"],
                "request digest",
            )
            _validate_request(metadata, template, catalogue, record, anchor, request)
            items[record] = item
        if set(items) != set(admitted) - {anchor}:
            raise ValidationRefusal("retained_request_inventory_mismatch", fold_id)
        fold_rows = [row for key, row in predictions.items() if key[0] == fold_id]
        if not fold_rows:
            continue
        state = fold_rows[0] if fitted else training[fold_id]
        _same(state["outer_fold"], outer, "training fold")
        _same(state["regional_anchor_record_id"], anchor, "training anchor")
        products = [
            object_mapping(value, "training_product")
            for value in object_list(state["training_products"], "training_products")
        ]
        if len(products) != len(items) or {
            identity(row["record_id"]) for row in products
        } != set(items):
            raise ValidationRefusal("retained_training_inventory_mismatch", fold_id)
        for row in products:
            _same(
                row["request_sha256"],
                items[identity(row["record_id"])]["request_sha256"],
                "fit request identity",
            )
        for row in fold_rows:
            _validate_forward(
                metadata, template, catalogue, row, fitted, anchor, products
            )


def _validate_request(
    metadata: dict[str, object],
    template: dict[str, object],
    catalogue: dict[str, dict[str, object]],
    record: str,
    anchor: str,
    request: dict[str, object],
) -> None:
    expected = {
        key: value
        for key, value in template.items()
        if key not in {"configuration", "evidence"}
    }
    _same(
        {
            key: value
            for key, value in request.items()
            if key not in {"local", "regional", "rings", "configuration", "evidence"}
        },
        expected,
        "request template fields",
    )
    config = object_mapping(request["configuration"], "configuration")
    declared = object_mapping(template["configuration"], "configuration")
    love = object_mapping(config["love"], "love")
    declared_love = object_mapping(declared["love"], "love")
    # make_request always overwrites this one field from the explicit experiment count.
    count = love.pop("max_ring")
    declared_love.pop("max_ring", None)
    if (
        type(count) is not int
        or count < 1
        or ("local_ring_count" in metadata and count != metadata["local_ring_count"])
    ):
        raise ValidationRefusal("retained_request_ring_count_mismatch", record)
    config["love"], declared["love"] = love, declared_love
    _same(
        config,
        declared,
        "request configuration excluding documented max_ring overwrite",
    )
    evidence = object_list(template["evidence"], "evidence")
    for role, key in (("local", record), ("regional", anchor)):
        source = catalogue[key]
        for field, evidence_role in (("raw", "raw_snapshot"), ("geometry", "geometry")):
            evidence.append(
                {
                    "evidence_id": field + ":" + key,
                    "role": evidence_role,
                    "path": source[field + "_path"],
                    "sha256": source[field + "_sha256"],
                }
            )
        section = object_mapping(request[role], role)
        samples = object_list(section["samples"], "samples")
        if len(samples) != 1:
            raise ValidationRefusal("retained_request_sample_mismatch", key)
        sample = object_mapping(samples[0], "sample")
        _same(sample["site_id"], source["site_id"], "request site ownership")
        _same(sample["raw_evidence_id"], "raw:" + key, "request raw ownership")
        _same(
            object_mapping(section["basin"], "basin")["geometry_evidence_id"],
            "geometry:" + key,
            "request basin ownership",
        )
    _same(request["evidence"], evidence, "exact consumed source references")
    rings = object_list(request["rings"], "rings")
    if len(rings) < count or any(
        object_mapping(ring, "ring")["geometry_evidence_id"] != "geometry:" + record
        for ring in rings
    ):
        raise ValidationRefusal("retained_request_geometry_mismatch", record)


def _validate_forward(
    metadata: dict[str, object],
    template: dict[str, object],
    catalogue: dict[str, dict[str, object]],
    row: dict[str, object],
    fitted: bool,
    anchor: str,
    products: list[dict[str, object]],
) -> None:
    record = identity(row["record_id"])
    if fitted:
        _same(
            row["target_geometry_sha256"],
            catalogue[record]["geometry_sha256"],
            "target geometry",
        )
        context = object_mapping(row["forward_preparation"], "forward_preparation")
        _same(
            context["target_geometry_sha256"],
            catalogue[record]["geometry_sha256"],
            "forward geometry",
        )
    else:
        inner = object_mapping(row["prediction_manifest"], "prediction_manifest")
        context = object_mapping(inner["forward_inputs"], "forward_inputs")
        _same(
            context["geometry_input_ids"],
            ["experiment-geometry:" + identity(catalogue[record]["geometry_sha256"])],
            "forward geometry identity",
        )
        _same(
            context["parameter_input_ids"],
            [
                "experiment-parameters:"
                + manifest_sha256(
                    {
                        "parameters": template["parameters"],
                        "evidence": template["evidence"],
                    }
                )
            ],
            "forward parameter identity",
        )
        _same(
            context["regional_input_ids"],
            [
                "experiment-regional:"
                + manifest_sha256({"anchor": anchor, "fits": products})
            ],
            "forward regional products",
        )
    taxa = object_list(template["taxa"], "taxa")
    parameters = [
        object_mapping(value, "parameter")
        for value in object_list(template["parameters"], "parameters")
    ]
    by_taxon = {
        identity(value["taxon"]): finite_number(value["ppe"]) for value in parameters
    }
    if len(by_taxon) != len(parameters) or set(by_taxon) != set(taxa):
        raise ValidationRefusal("retained_parameter_taxa_mismatch", record)
    _same(context["taxa"], taxa, "forward parameter order")
    if tuple(
        finite_number(value) for value in object_list(context["ppe"], "ppe")
    ) != tuple(by_taxon[identity(taxon)] for taxon in taxa):
        raise ValidationRefusal("retained_forward_ppe_mismatch", record)
