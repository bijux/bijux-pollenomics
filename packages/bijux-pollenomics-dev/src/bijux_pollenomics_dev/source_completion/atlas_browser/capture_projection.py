"""Publish authenticated browser captures without repeating browser execution."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import _regular_confined_file
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.atlas_source_views import (
    CAPTURE_PATH,
    CAPTURE_SHA256,
    OWNER_IDS,
    ValidatedAtlasCapture,
    read_object,
    validated_atlas_source_views,
)

SELECTOR_SCHEMA = "atlas-source-view-capture-projection.v1"
SELECTOR_ROOT = Path("configs/ci/report-capture-projections/atlas-source-views")


def _json(value: object) -> bytes:
    return (
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode()


def _case(capture: ValidatedAtlasCapture, name: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        next(row for row in capture.document["cases"] if row["case_id"] == name),
    )


def _receipt(capture: ValidatedAtlasCapture, name: str) -> dict[str, Any]:
    return read_object(capture.members[_case(capture, name)["receipt"]])


def _generation(capture: ValidatedAtlasCapture, name: str) -> dict[str, Any]:
    member = capture.document["generations"][name]
    return read_object(capture.members[member])


def _source(capture: ValidatedAtlasCapture) -> dict[str, Any]:
    return {
        "capture_path": CAPTURE_PATH,
        "capture_sha256": CAPTURE_SHA256,
        "source_candidate": capture.document["source_candidate"],
        "operation": "retained byte transport and metadata projection",
        "browser_executed_by_this_projection": False,
        "numerical_execution": False,
        "scientific_admission": False,
    }


def _keyless_identity(capture: ValidatedAtlasCapture) -> dict[str, Any]:
    generation = _generation(capture, "nordic-source-contexts")
    path = capture.members[capture.document["generations"]["nordic-source-contexts"]]
    return {
        "schema_version": "atlas-keyless-cache-candidate-inputs.v1",
        "candidate_build_id": generation["candidate_build_id"],
        "generation_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_atlas_build_id": generation["source_atlas_build_id"],
        "countries": generation["countries"],
        "input_sha256": generation["inputs_sha256"],
        "source_record_ids": [row["record_id"] for row in generation["source_records"]],
        "source_capture": _source(capture),
    }


def _provider_review(capture: ValidatedAtlasCapture) -> dict[str, Any]:
    receipt = _receipt(capture, "provider-accessibility")
    source_case = _case(capture, "provider-accessibility")
    observations = {}
    for product in capture.document["products"]:
        prefix = "atlas/provider-accessibility/observations/"
        if product["output_path"].startswith(prefix):
            name = product["output_path"].removeprefix(prefix)
            observations[name] = hashlib.sha256(
                capture.members[product["source"]].read_bytes()
            ).hexdigest()
    return {
        "schema_version": "atlas-provider-accessibility-review.v1",
        "status": receipt["status"],
        "browser": receipt,
        "browser_receipt_path": "browser-receipt.json",
        "candidate_generation_path": "candidate-generation.json",
        "retained_observations_sha256": observations,
        "verifier": {
            "sha256": receipt["verifier_sha256"],
            "actual_argv": source_case["native_execution"]["actual_argv"],
        },
        "selected_checks": {
            "keyboard_routes": len(receipt["keyboard_routes"]),
            "source_downloads": len(receipt["downloads"]),
            "provider_fallbacks": len(receipt["provider_fallbacks"]),
            "tile_free_modes": len(receipt["tile_free_modes"]),
            "runtime_errors": len(receipt["runtime_errors"]),
            "layout_negative_controls": receipt["layout_negative_controls"],
        },
        "source_capture": _source(capture),
        "limitations": capture.document["limits"],
    }


def _modeled_review(capture: ValidatedAtlasCapture) -> dict[str, Any]:
    receipt = _receipt(capture, "modeled-panel-browser")
    generation = _generation(capture, "modeled-panels")
    source_case = _case(capture, "modeled-panel-browser")
    screenshots = {
        row["output_path"].removeprefix(
            "atlas/modeled-panel-browser/observations/"
        ): hashlib.sha256(capture.members[row["source"]].read_bytes()).hexdigest()
        for row in capture.document["products"]
        if row["output_path"].startswith("atlas/modeled-panel-browser/observations/")
        and row["output_path"].endswith(".png")
    }
    return {
        "schema_version": "atlas-modeled-panel-browser-report.v1",
        "status": receipt["status"],
        "browser_product": receipt["browser"],
        "browser_receipt_path": "browser-receipt.json",
        "browser_receipt_sha256": hashlib.sha256(
            capture.members[source_case["receipt"]].read_bytes()
        ).hexdigest(),
        "candidate_generation_path": "candidate-generation.json",
        "candidate_generation_sha256": hashlib.sha256(
            capture.members[source_case["generation"]].read_bytes()
        ).hexdigest(),
        "frozen_source_input_count": len(generation["inputs_sha256"]),
        "frozen_source_inputs_sha256": generation["inputs_sha256"],
        "numerical_execution": generation["numerical_execution"],
        "scientific_admission": False,
        "source_feature_count": generation["source_feature_count"],
        "source_feature_sha256": generation["source_feature_sha256"],
        "source_records_equal": all(
            x["source_records_equal"] for x in receipt["scenarios"]
        ),
        "estimates_and_standard_errors_equal": all(
            x["estimates_and_standard_errors_equal"] for x in receipt["scenarios"]
        ),
        "panel_csv_equal": all(x["panel_csv_equal"] for x in receipt["scenarios"]),
        "panel_csv_sha256": generation["panel_csv_sha256"],
        "panel_row_count": generation["panel_rows"],
        "runtime_error_count": len(receipt["runtime_errors"]),
        "scenario_count": len(receipt["scenarios"]),
        "scenarios": receipt["scenarios"],
        "blocked_tile_requests": receipt["blocked_tile_requests"],
        "served_files_sha256": receipt["served_files_sha256"],
        "screenshots_sha256": screenshots,
        "verifier_path": "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/modeled-panel-browser.mjs",
        "verifier_sha256": receipt["verifier_sha256"],
        "source_capture": _source(capture),
        "checks": {
            "native_observation": "PASS; exact retained browser receipt and served/download bytes",
            "publication": "retained transport; no new browser or numerical execution",
        },
    }


def build_capture_products(repository: Path, selector: Path) -> dict[str, bytes]:
    """Produce exactly one reviewed owner's files from its native capture packet."""
    repository = repository.absolute()
    selector = selector.absolute()
    try:
        relative = selector.relative_to(repository)
    except ValueError as error:
        raise ReportRebuildError(
            "Atlas projection selector is outside repository"
        ) from error
    if relative.parent != SELECTOR_ROOT:
        raise ReportRebuildError("Atlas projection selector is not a governed selector")
    selected = read_object(
        _regular_confined_file(
            repository, relative.as_posix(), "atlas capture selector"
        )
    )
    if (
        set(selected) != {"schema_version", "owner_id", "capture_sha256"}
        or selected["schema_version"] != SELECTOR_SCHEMA
        or selected["capture_sha256"] != CAPTURE_SHA256
        or selected["owner_id"] not in OWNER_IDS
    ):
        raise ReportRebuildError("Atlas projection selector differs")
    capture = validated_atlas_source_views(repository)
    products = {}
    builders = {
        "keyless-identity": _keyless_identity,
        "provider-review": _provider_review,
        "modeled-review": _modeled_review,
    }
    for row in capture.document["products"]:
        if row["owner_id"] != selected["owner_id"]:
            continue
        products[row["output_path"]] = (
            capture.members[row["source"]].read_bytes()
            if row["operation"] == "copy"
            else _json(builders[row["operation"]](capture))
        )
    return products


def publish_capture_products(repository: Path, selector: Path, output: Path) -> None:
    """Write an absent artifact destination only after complete source admission."""
    repository = repository.absolute()
    destination = require_absent_artifact_output(repository, output)
    products = build_capture_products(repository, selector)
    destination.mkdir()
    for name, raw in sorted(products.items()):
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def main(argv: list[str] | None = None) -> int:
    """Publish one configured owner's retained source-view browser account."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument(
        "--receipt",
        type=Path,
        required=True,
        help="reviewed capture projection selector",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    publish_capture_products(args.repository, args.receipt, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
