"""Independent successful/refused fold accounting and physical forward arithmetic."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .lineage import allowed_closure, digest, expected_folds
from .native_fits import check_batches, named, near
from .reading import decode, exact, product
from .scalar import (
    AXIS,
    METHODS,
    admitted_cover,
    forward,
    number,
    require,
    spatial_cover,
    spatial_weights,
)


def check_prediction(
    repository: Path,
    pin: dict[str, Any],
    context: dict[str, Any],
    tolerance: dict[str, Any],
) -> dict[str, Any]:
    directory = Path(pin["directory"])
    require(
        directory.is_relative_to(repository / "artifacts"),
        "prediction product escaped artifacts",
    )
    manifest, files = product(directory, pin["manifest_sha256"])
    require(
        manifest["phase"] == "predictions"
        and manifest["scientific_content_sha256"] == pin["scientific_content_sha256"]
        and manifest["scientific_acceptance"] == "not_evaluated",
        "prediction identity or scientific posture differs",
    )
    scientific = manifest["scientific_payload"]
    spec = context["experiment"]
    folds = expected_folds(
        spec["sites"], spec["target_record_ids"], context["ids"]["KRAGMJNY"]
    )
    exact(scientific["folds"], folds)
    require(
        scientific["split_manifest_sha256"] == digest(folds)
        and scientific["requested_folds"] == 3
        and scientific["requested_predictions"] == 9
        and scientific["baselines"] == list(METHODS),
        "complete prediction fold authority differs",
    )
    for key in ("predictions", "training", "preparations", "failures"):
        exact(decode(files[key + ".json"]), scientific[key])
    saved_metadata = decode(files["experiment.json"])
    expected_catalogue = [
        {
            "record_id": site["record_id"],
            "site_id": site["site_id"],
            "identity_keys": site["identity_keys"],
            "raw_path": site["raw"]["path"],
            "raw_sha256": site["raw"]["sha256"],
            "geometry_path": site["geometry"]["path"],
            "geometry_sha256": site["geometry"]["sha256"],
        }
        for site in spec["sites"]
    ]
    exact(saved_metadata["source_catalogue"], expected_catalogue)
    exact(saved_metadata["target_record_ids"], spec["target_record_ids"])
    exact(saved_metadata["regional_priority"], spec["regional_priority"])
    exact(saved_metadata["request_template"], spec["request_template"])
    batches = check_batches(repository, directory, files, folds, context, tolerance)
    failures = {row["fold_id"]: row for row in scientific["failures"]}
    training = {row["fold_id"]: row for row in scientific["training"]}
    preparations = {row["fold_id"]: row for row in scientific["preparations"]}
    require(
        len(failures) == len(scientific["failures"])
        and len(training) == len(scientific["training"])
        and len(preparations) == len(scientific["preparations"]),
        "duplicate fold products refused",
    )
    expected_successes = {row["fold_id"] for row in folds} - set(failures)
    require(
        set(training) == set(preparations) == expected_successes
        and len(expected_successes) + len(failures) == 3,
        "complete fold success/refusal partition required",
    )
    rows = {(row["fold_id"], row["baseline"]): row for row in scientific["predictions"]}
    require(
        len(rows) == len(scientific["predictions"]) == 3 * len(expected_successes)
        and set(rows)
        == {(fold, method) for fold in expected_successes for method in METHODS},
        "exact prediction population required",
    )
    dispositions = []
    output = {}
    negative = 0
    maximum = 0.0
    for fold in folds:
        fold_id = fold["fold_id"]
        native = batches.get(fold_id, {})
        target = fold["test_record_ids"][0]
        invalid_native = any(
            "cover" in item and (min(item["cover"]) < 0 or max(item["cover"]) > 1)
            for item in native.values()
        )
        negative += sum(
            "cover" in item and min(item["cover"]) < 0 for item in native.values()
        )
        if fold_id in failures:
            failure = failures[fold_id]
            require(
                failure["record_ids"] == [target]
                and failure["status"] in {"refused", "not_run"}
                and bool(failure["reason_code"]),
                "original failed target disposition required",
            )
            if failure["reason_code"] == "invalid_composition":
                require(
                    invalid_native,
                    "invalid-composition refusal lacks signed native evidence",
                )
            for method in METHODS:
                dispositions.append(
                    {
                        "fold_id": fold_id,
                        "method": method,
                        **{
                            key: failure[key]
                            for key in (
                                "status",
                                "reason_code",
                                "detail",
                                "exception_type",
                            )
                            if key in failure
                        },
                    }
                )
            continue
        require(
            len(native) == 2
            and all("cover" in item for item in native.values())
            and not invalid_native,
            "both admissible local native reconstructions required",
        )
        fit, prepared = training[fold_id], preparations[fold_id]
        exact(fit["outer_fold"], fold)
        exact(prepared["outer_fold"], fold)
        anchor = context["ids"]["KRAGMJNY"]
        anchor_group = "site-group:" + digest([anchor])
        predictor_records = sorted(set(fold["train_record_ids"]) - {anchor})
        groups = {
            record: "site-group:" + digest([record]) for record in predictor_records
        }
        predictor_groups = sorted(groups.values())
        require(
            fit["regional_anchor_record_id"]
            == prepared["regional_anchor_record_id"]
            == anchor
            and fit["regional_anchor_group_id"]
            == prepared["regional_anchor_group_id"]
            == anchor_group
            and fit["predictor_group_ids"] == sorted(predictor_groups)
            and set(prepared["predictor_group_ids"]) == set(predictor_groups),
            "permanent regional/two local predictor roles differ",
        )
        identities = fit["training_products"]
        require(
            len(identities) == 2
            and {item["record_id"] for item in identities} == set(predictor_records),
            "both source-specific training identities required",
        )
        covers = {}
        for item in identities:
            record = item["record_id"]
            require(item["group_id"] == groups[record], "local training group differs")
            for field in (
                "request_sha256",
                "scientific_content_sha256",
                "scientific_identity_sha256",
            ):
                require(
                    item[field] == native[record][field],
                    "training identity differs from native product",
                )
            cover = native[record]["cover"]
            admitted_cover(cover)
            for left, right in zip(named(item["composition"]), cover, strict=True):
                maximum = max(maximum, near(left, right, tolerance))
            covers[groups[record]] = cover
        regional = native[predictor_records[0]]["regional"]
        for record in predictor_records:
            for left, right in zip(native[record]["regional"], regional, strict=True):
                near(float(left), right, tolerance)
        for left, right in zip(prepared["regional_cover"], regional, strict=True):
            near(left, right, tolerance)
        forward_inputs = prepared["forward_inputs"]
        full = prepared["full_k"]
        fractions = prepared["full_terrestrial_fraction"]
        require(
            len(full) == len(fractions) == 4
            and fractions == [1.0] * 4
            and forward_inputs["taxa"] == list(AXIS)
            and forward_inputs["local_k"] == full[:2]
            and forward_inputs["terrestrial_fraction"] == fractions[:2],
            "saved native full/local ring partition differs",
        )
        ppe = [row["ppe"] for row in spec["request_template"]["parameters"]]
        exact(forward_inputs["ppe"], ppe)
        for i in range(2):
            expected_regional = (
                number(ppe[i])
                * regional[i]
                * sum(number(full[j][i]) * number(fractions[j]) for j in (2, 3))
            )
            near(forward_inputs["regional_deposition"][i], expected_regional, tolerance)
        require(
            set(prepared["distances_km"]) == set(predictor_groups),
            "distances must identify exactly both local predictors",
        )
        order = sorted(predictor_groups)
        compositions = [covers[group] for group in order]
        distances = [prepared["distances_km"][group] for group in order]
        for method in METHODS:
            row = rows[(fold_id, method)]
            require(row["record_id"] == target, "prediction target differs")
            weights = spatial_weights(method, distances)
            vegetation = spatial_cover(compositions, weights)
            pollen = forward(
                vegetation,
                forward_inputs["regional_deposition"],
                forward_inputs["local_k"],
                forward_inputs["terrestrial_fraction"],
                forward_inputs["ppe"],
            )
            for field, values in (
                ("vegetation_fraction", vegetation),
                ("pollen_fraction", pollen),
            ):
                for left, right in zip(named(row[field]), values, strict=True):
                    maximum = max(maximum, near(left, right, tolerance))
            prediction_manifest = row["prediction_manifest"]
            require(
                row["prediction_manifest_sha256"] == digest(prediction_manifest)
                and prediction_manifest["target_group_id"] == fold["test_group_ids"][0]
                and prediction_manifest["spatial_method"] == method,
                "prediction publication digest or target role differs",
            )
            exact(prediction_manifest["fold"], fold)
            exact(prediction_manifest["forward_inputs"], forward_inputs)
            exact(
                prediction_manifest["vegetation_fraction"], row["vegetation_fraction"]
            )
            exact(prediction_manifest["pollen_fraction"], row["pollen_fraction"])
            external = [
                *forward_inputs["regional_input_ids"],
                *forward_inputs["parameter_input_ids"],
                *forward_inputs["geometry_input_ids"],
                forward_inputs["temporal_support_id"],
            ]
            graph = prediction_manifest["input_lineage"]
            closure = allowed_closure(
                [*fold["train_record_ids"], *external],
                graph,
                fold["train_record_ids"],
                fold["test_record_ids"],
                external,
            )
            exact(closure, prediction_manifest["allowed_input_closure"])
            require(
                all(not graph[record] for record in fold["train_record_ids"]),
                "raw training lineage must remain leaves",
            )
            require(
                set(graph[forward_inputs["regional_input_ids"][0]])
                == set(fold["train_record_ids"]),
                "regional identity must retain all training ancestry",
            )
            require(
                prediction_manifest["predictor_group_ids"] == predictor_groups,
                "regional group reached local interpolation",
            )
            output[(fold_id, method)] = {
                "row": row,
                "pollen": pollen,
                "vegetation": vegetation,
            }
            dispositions.append(
                {"fold_id": fold_id, "method": method, "status": "predicted"}
            )
    exact(dispositions, pin["method_dispositions"])
    return {
        "folds": folds,
        "dispositions": dispositions,
        "predictions": output,
        "native_negative_final_covers": negative,
        "native_fit_references": sum(len(rows) for rows in batches.values()),
        "native_request_sha256": sorted(
            {
                item.get(
                    "request_sha256", item.get("receipt", {}).get("request_sha256")
                )
                for values in batches.values()
                for item in values.values()
            }
        ),
        "maximum_scalar_difference": maximum,
        "manifest": manifest,
        "files": files,
    }
