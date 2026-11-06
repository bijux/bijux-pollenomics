"""Check every available native training item, including signed refused folds."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

from .exposure import count_free_evidence
from .lineage import digest
from .reading import csv_rows, decode, exact, product
from .scalar import AXIS, number, require, reveals, signed_love


def near(actual: object, expected: object, tolerance: dict[str, Any]) -> float:
    """Check a scalar against the declared absolute and relative tolerances."""
    left = float(number(actual))
    right = float(expected if isinstance(expected, Fraction) else number(expected))
    difference = abs(left - right)
    require(
        difference
        <= tolerance["scalar_absolute_tolerance"]
        + tolerance["scalar_relative_tolerance"] * abs(right),
        "saved scalar differs from independent equation",
    )
    return difference


def named(values: dict[str, Any]) -> list[object]:
    """Return composition values in the exact two-taxon axis order."""
    require(set(values) == set(AXIS), "literal two-taxon composition keys required")
    return [values[taxon] for taxon in AXIS]


def native_fit(
    directory: Path,
    pin: dict[str, Any],
    request: dict[str, Any],
    tolerance: dict[str, Any],
) -> dict[str, Any]:
    """Reconstruct signed scalar outputs from a pinned saved native product."""
    manifest, members = product(directory, pin["manifest_sha256"])
    require(
        manifest["schema_version"] == "lra-product.v1"
        and manifest["scientific_acceptance"] == "not_evaluated"
        and manifest["request_sha256"] == digest(request)
        and manifest["scientific_content_sha256"] == pin["scientific_content_sha256"],
        "native training product identity differs",
    )
    exact(decode(members["request.json"]), request)
    ppe = [row["ppe"] for row in request["parameters"]]
    regional_counts = request["regional"]["samples"][0]["counts"]
    local_counts = request["local"]["samples"][0]["counts"]
    factors = csv_rows(members["numerical/regional_reveals/deposition_factors.csv"])
    require(
        len(factors) == 2 and [row["index"] for row in factors] == list(AXIS),
        "native regional coefficient axis differs",
    )
    kernels = [float(row["K"]) for row in factors]
    regional = reveals(regional_counts, ppe, kernels)
    regional_rows = csv_rows(members["numerical/regional_reveals/reconstruction.csv"])
    require(len(regional_rows) == 1, "one deterministic regional source row required")
    maximum = 0.0
    for i, taxon in enumerate(AXIS):
        for statistic in ("mean", "median", "q90", "q10"):
            maximum = max(
                maximum,
                near(
                    float(regional_rows[0][taxon + "." + statistic]) / 100,
                    regional[i],
                    tolerance,
                ),
            )
        near(float(regional_rows[0][taxon + ".sd"]), 0, tolerance)
    native = {}
    for key in ("Kloc", "Kreg"):
        native[key] = csv_rows(members["numerical/local_love/aux_" + key + ".csv"])
        require(
            len(native[key]) == 2, "both native inversion ring coefficients required"
        )
    saved = csv_rows(members["numerical/local_love/cover_mean.csv"])
    require(
        len(saved) == 2 and len(request["rings"]) == 2,
        "both signed local reconstruction rows required",
    )
    covers = []
    for index, row in enumerate(saved):
        for values in (row, native["Kloc"][index], native["Kreg"][index]):
            near(float(values["index"]), request["rings"][index]["mean_m"], tolerance)
        expected = signed_love(
            local_counts,
            ppe,
            [float(value) for value in regional],
            [float(native["Kloc"][index][taxon]) for taxon in AXIS],
            [float(native["Kreg"][index][taxon]) for taxon in AXIS],
        )
        actual = [float(row[taxon]) for taxon in AXIS]
        for left, right in zip(actual, expected, strict=True):
            maximum = max(maximum, near(left, right, tolerance))
        covers.append(tuple(number(value) for value in actual))
    local_manifest = decode(members["numerical/local_love/run_manifest.json"])
    require(
        local_manifest["parameters"]["paired_regional_cover_draws"] is True,
        "local reconstruction lacks paired regional provenance",
    )
    return {
        "cover": covers[-1],
        "all_signed_covers": covers,
        "regional": regional,
        "maximum_scalar_difference": maximum,
        "request_sha256": manifest["request_sha256"],
        "scientific_content_sha256": manifest["scientific_content_sha256"],
        "scientific_identity_sha256": digest(manifest["scientific_identity"]),
    }


def check_batches(
    repository: Path,
    directory: Path,
    members: dict[str, bytes],
    folds: list[dict[str, Any]],
    context: dict[str, Any],
    tolerance: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Check saved local and regional requests and native product ownership."""
    attempts = [
        (name, decode(body))
        for name, body in members.items()
        if name.startswith("batches/")
        and name.endswith("/receipt.json")
        and decode(body).get("schema_version") == "lra-batch-attempt.v1"
    ]
    require(len(attempts) <= 3, "native attempt population exceeds three target folds")
    result: dict[str, dict[str, Any]] = {}
    for name, attempt in attempts:
        prefix = name.removesuffix("/receipt.json")
        fold_index = int(Path(prefix).name.removeprefix("fold-"))
        require(0 <= fold_index < len(folds), "unknown native fold attempt")
        fold = folds[fold_index]
        anchor = context["ids"]["KRAGMJNY"]
        expected_local = set(fold["train_record_ids"]) - {anchor}
        items = attempt["items"]
        require(
            len(items) == 2 and {item["item_id"] for item in items} == expected_local,
            "both exact local training requests required",
        )
        summary = decode(members[prefix + "/summary/receipt.json"])
        require(
            summary["schema_version"] == "lra-batch-result.v1"
            and summary["batch_sha256"] == attempt["batch_sha256"]
            and len(summary["items"]) == 2,
            "closed native attempt summary required",
        )
        outputs = {}
        for index, item in enumerate(items):
            request = item["request"]
            require(
                item["request_sha256"] == digest(request),
                "native request identity differs",
            )
            require(
                request["taxa"] == list(AXIS)
                and request["configuration"]
                == context["experiment"]["request_template"]["configuration"]
                and request["parameters"]
                == context["experiment"]["request_template"]["parameters"],
                "native equation/profile parameters differ",
            )
            common = [
                row
                for row in request["evidence"]
                if row["role"] not in {"raw_snapshot", "geometry"}
            ]
            exact(common, context["experiment"]["request_template"]["evidence"])
            for evidence in common:
                count_free_evidence(context["members"][evidence["path"]])
            snapshots = [
                row for row in request["evidence"] if row["role"] == "raw_snapshot"
            ]
            require(
                len(snapshots) == 2
                and {row["evidence_id"] for row in snapshots}
                == {"raw:" + item["item_id"], "raw:" + anchor},
                "only admitted local/regional counts may enter native cache ancestry",
            )
            for role, record in (("local", item["item_id"]), ("regional", anchor)):
                samples = request[role]["samples"]
                require(
                    len(samples) == 1,
                    "one physical native source sample per role required",
                )
                code = next(
                    code
                    for code, identifier in context["ids"].items()
                    if identifier == record
                )
                raw = context["members"][code + "-raw.json"]["sample"]
                exact(samples[0], {**raw, "raw_evidence_id": "raw:" + record})
                site = next(
                    site
                    for site in context["experiment"]["sites"]
                    if site["record_id"] == record
                )
                evidence = next(
                    row for row in snapshots if row["evidence_id"] == "raw:" + record
                )
                require(
                    evidence["path"] == site["raw"]["path"]
                    and evidence["sha256"] == site["raw"]["sha256"],
                    "native raw snapshot source reference differs",
                )
                expected_geometry = context["members"][code + "-geometry.json"]
                exact(
                    request[role]["basin"],
                    {
                        **expected_geometry["basin"],
                        "geometry_evidence_id": "geometry:" + record,
                    },
                )
            require(
                item["item_id"] not in fold["test_record_ids"]
                and anchor not in fold["test_record_ids"],
                "target source reached native fitting",
            )
            completed = summary["items"][index]
            require(
                completed["item_id"] == item["item_id"]
                and completed["request_sha256"] == item["request_sha256"],
                "native item ownership differs",
            )
            exact(
                decode(members[prefix + f"/items/{index:06d}/receipt.json"]), completed
            )
            if completed["item_status"] == "completed":
                pin = completed["product"]
                path = Path(pin["directory"])
                require(
                    path.is_relative_to(repository / "artifacts")
                    and path.is_relative_to(Path(attempt["cache_root"])),
                    "native cache product escaped owned artifacts",
                )
                outputs[item["item_id"]] = native_fit(path, pin, request, tolerance)
            else:
                require(
                    completed["item_status"]
                    in {"refused", "failed", "not_run", "unobserved"}
                    and "product" not in completed,
                    "unknown failed native item disposition",
                )
                outputs[item["item_id"]] = {
                    "status": completed["item_status"],
                    "receipt": completed,
                }
        result[fold["fold_id"]] = outputs
    return result
