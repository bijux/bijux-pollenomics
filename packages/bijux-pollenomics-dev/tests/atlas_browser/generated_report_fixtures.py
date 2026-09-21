"""Synthetic managed-publication fixtures for the focused RAÄ browser profile."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_pollenomics_dev.ci.atlas_browser.artifact_candidate import (
    canonical_digest,
    inventory,
)
from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    RAA_RETAINED_CONTEXT_PROFILE,
    AtlasGeneratedReportCandidate,
    AtlasScope,
    BrowserVerificationPlan,
)

from .fixtures import BUILD_ID


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def generated_report_plan(root: Path) -> BrowserVerificationPlan:
    presentation = root / "artifacts/publication/docs-report"
    scope = presentation / "regions/nordic"
    scope.mkdir(parents=True)
    (scope / "nordic_map.html").write_text(
        f"<!doctype html><script>const build='{BUILD_ID}';"
        "const tile='https://tile.openstreetmap.org/{z}/{x}/{y}.png';</script>",
        encoding="utf-8",
    )
    reasons = [
        "missing_raw_inventory",
        "missing_raw_summary",
        "missing_scientific_review",
    ]
    layer = {
        "key": "raa-archaeology",
        "label": "RAÄ archaeology density",
        "count": 106,
        "default_enabled": True,
        "applies_time_filter": False,
        "semantic_role": "archaeology_context",
        "contribution_role": "display_only",
        "candidate_ranking_eligible": False,
        "scientific_classification_eligible": False,
        "scientific_selection_enabled": False,
        "propagation_status": "refused",
        "propagation_reason_code": "archaeology_context_only",
        "edge_count": 0,
        "authority_status": "degraded",
        "authority_reason_codes": reasons,
        "display_warning_codes": ["retained_density_metadata_count_mismatch"],
    }
    status = {
        "schema_version": "raa-atlas-input-status.v1",
        "atlas_input_status": "degraded",
        "reason_codes": reasons,
        "evidence_role": "archaeology_context_only",
        "propagation_eligible": False,
        "geometry_publication": {
            "default_map_state": "enabled_degraded_context",
            "default_enabled": True,
            "retained_density_is_authoritative": False,
        },
        "density_count_accounting": {
            "density_feature_count": 106,
            "density_cell_count_sum": 339_412,
            "metadata_fornlamning_count": 318_265,
            "difference": 21_147,
            "reconciled": False,
        },
    }
    fields = [
        "domain",
        "sha256",
        "payload_sha256",
        "record_count",
        "layer_index",
        "layer_key",
        "layer_kind",
        "country_keys",
        "bounds",
        "time_min_bp",
        "time_max_bp",
        "untimed_record_count",
        "chronology_absent_record_count",
        "refused_chronology_record_count",
        "contextual_chronology_record_count",
        "scientific_signal_ids",
    ]
    manifest = {
        "build_id": BUILD_ID,
        "assets": {
            "fields": fields,
            "records": [
                [
                    "nodes",
                    "a030442075107e8024eb4dbf223a10272419bdf956176f05569cb2781e5c939c",
                    "29eb02bd2359bde3882ab36ec9be5847b95f2857eecc52134ea18306fd4dfadf",
                    106,
                    20,
                    "raa-archaeology",
                    "polygon",
                    ["Sweden"],
                    [55, 11, 69, 25],
                    None,
                    None,
                    106,
                    106,
                    0,
                    0,
                    [],
                ]
            ],
        },
        "domains": {
            "edges": {
                "status": "unavailable",
                "reason_code": "governed_map_edge_model_not_available",
                "record_count": 0,
            }
        },
    }
    _write(scope / "raa_atlas_input_status.json", status)
    _write(scope / "nordic_map_publication_contract.json", {"layer_rows": [layer]})
    _write(scope / "nordic_map_assets.json", manifest)
    physical = inventory(presentation)
    hashes = {row["path"]: row["sha256"] for row in physical}
    receipt_path = root / "artifacts/jobs/raa-fixture/result.json"
    receipt = {
        "job_id": "raa-fixture",
        "input_commit": "a" * 40,
        "input_tree": "b" * 40,
        "exit_code": 0,
        "termination": "exited",
        "read_set_unchanged": True,
        "command": [
            "/python",
            "-m",
            "bijux_pollenomics",
            "publish-reports",
            "--countries",
            "Sweden",
            "Norway",
            "Finland",
            "Denmark",
            "--output-root",
            str(presentation),
            "--published-output-root",
            "docs/report",
        ],
        "cwd": str(root / "artifacts/snapshot/repository"),
        "outputs": [str(presentation)],
        "output_hashes": {
            str(presentation / member): digest for member, digest in hashes.items()
        },
    }
    _write(receipt_path, receipt)
    candidate = AtlasGeneratedReportCandidate(
        build_id=BUILD_ID,
        generator_repository_head="a" * 40,
        generator_repository_tree="b" * 40,
        generator_receipt="artifacts/jobs/raa-fixture/result.json",
        generator_receipt_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        presentation_root="artifacts/publication/docs-report",
        presentation_inventory_sha256=canonical_digest(hashes),
    )
    browser = root / "browser"
    browser.write_bytes(b"browser")
    return BrowserVerificationPlan(
        repository_root=root,
        artifact_root=root / "artifacts/browser-evidence",
        browser_binary=browser,
        candidate=candidate,
        scopes=(
            AtlasScope(
                "nordic",
                "artifacts/publication/docs-report/regions/nordic/nordic_map.html",
                "artifacts/publication/docs-report/regions/nordic/"
                "nordic_map_assets.json",
            ),
        ),
        verification_profile=RAA_RETAINED_CONTEXT_PROFILE,
    )
