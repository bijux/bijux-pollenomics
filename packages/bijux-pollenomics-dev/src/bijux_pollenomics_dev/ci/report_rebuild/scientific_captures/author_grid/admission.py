"""Admit five retained original-R/source-Python products with explicit failed histories."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.author_grid.transport import (
    ASSEMBLY_PLAN_SHA256,
    ASSEMBLY_REVIEW_SHA256,
    ASSEMBLY_TERMINAL_SHA256,
    CAPTURE,
    CAPTURE_SHA256,
    EPOCHS,
    file,
    json_object,
    member,
    object_value,
    require,
    sha,
    typed,
    validate_retained_ledger,
    validated_retained_author_grid,
)
from bijux_pollenomics_dev.essd_reproduction.example_reexecution import verify_report

from ...contracts import JsonObject, ReportRebuildError, canonical_json_sha256
from ...retained_source import SourceCapsule
from ..source_correspondence import VERSION_SOURCE, validated_current_scientific_source
from .historical_reader import FAMILY, historical_reader_scope

EXECUTION_REPORT = (
    "docs/report/publication-replay/landclim-example-reexecution/report.json"
)
ACCOUNTS = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/scientific_accounts.json"
OWNERS = {
    "publication-replay/landclim-example-reexecution/report-products": [
        EXECUTION_REPORT
    ],
    "publication-replay/landclim-author-example-correspondence/report-products": sorted(
        FAMILY + name
        for name in ["REPORT.md", "paper-correspondence.csv", "report.json"]
    ),
    "publication-replay/landclim-author-example-correspondence/source-manifest": [
        FAMILY + "manifest.json"
    ],
}
PRODUCTS = {
    EXECUTION_REPORT: ("numerical-source-review", "retained-products/report.json"),
    **{
        FAMILY + name: ("correspondence-writer", "source-products/" + name)
        for name in [
            "REPORT.md",
            "paper-correspondence.csv",
            "report.json",
            "manifest.json",
        ]
    },
}


def owner_rows(owners: list[JsonObject]) -> list[JsonObject]:
    """Require the three disjoint retained author-grid report owners."""
    selected = [row for row in owners if row.get("owner_id") in OWNERS]
    require(
        len(selected) == len(OWNERS)
        and len({r["owner_id"] for r in selected}) == len(selected),
        "Author-grid exact three owners required",
    )
    for row in selected:
        owner_id = row["owner_id"]
        require(isinstance(owner_id, str), "Author-grid owner identifier is not text")
        assert isinstance(owner_id, str)
        require(
            row.get("role") == "retained_source"
            and row.get("paths") == OWNERS[owner_id]
            and row.get("producer_paths") == []
            and row.get("producer_inputs") == [],
            "Author-grid retained role/path/producer contract differs",
        )
    for row in owners:
        if row not in selected:
            paths = row.get("paths")
            require(
                not isinstance(paths, list) or not set(PRODUCTS).intersection(paths),
                "Author-grid ownership overlaps another role",
            )
    return selected


def _current_numerical_source_role(
    repository: Path,
    row: JsonObject,
    members: dict[str, JsonObject],
    source_buffer: SourceCapsule,
) -> JsonObject | None:
    """Keep numeric sources exact and authenticate only declared version provenance."""
    name = member(row["path"])
    logical = member(row["captured_path"])
    retained = members.get(logical)
    require(
        type(row["bytes"]) is int
        and retained is not None
        and (retained["sha256"], retained["bytes"]) == (row["sha256"], row["bytes"]),
        "Author-grid retained numerical source is unbound",
    )
    if name in {
        VERSION_SOURCE,
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/__init__.py",
    }:
        return validated_current_scientific_source(
            repository,
            {key: row[key] for key in ("path", "bytes", "sha256")},
            logical,
            source_buffer,
        )
    source = file(repository, name)
    require(
        sha(source) == row["sha256"] and source.stat().st_size == row["bytes"],
        "Author-grid numerical source changed; no metadata/presentation waiver applies",
    )
    return None


def numerical_scope(
    repository: Path,
    packet: Path,
    capture: JsonObject,
    members: dict[str, JsonObject],
    source_buffer: SourceCapsule,
) -> tuple[JsonObject, ...]:
    """Verify saved grid receipts and exact current numerical source correspondence."""
    report = json_object(file(packet, "raw-numerical/report.json"))
    require(
        verify_report(
            file(packet, "raw-numerical/report.json"), packet / "raw-numerical"
        )
        == {"passed": True, "grids": ["512", "562"], "raw_bytes_verified": True},
        "Author-grid maintained numerical receipt failed",
    )
    require(
        len(report["native_source_files"]) == 59
        and report["private_snapshot_members_verified"] == 193,
        "Author-grid numerical source/private denominator differs",
    )
    require(
        report["admission"]
        == {
            "two_grid_numerical_parity": True,
            "full_study_reproduction": False,
            "independent_vegetation_accuracy": False,
            "private_input_redistribution_rights_cleared": False,
        }
        and all(type(v) is bool for v in report["admission"].values()),
        "Author-grid computational control was promoted to empirical acceptance",
    )
    projection = capture["current_numerical_source_projection"]
    require(
        isinstance(projection, list)
        and len(projection) == len({r["path"] for r in projection}) == 59,
        "Author-grid complete numerical projection differs",
    )
    assert isinstance(projection, list)
    require(
        {r["path"]: r["sha256"] for r in projection} == report["native_source_files"],
        "Author-grid declared numerical source map differs",
    )
    source_roles = []
    for row in projection:
        role = _current_numerical_source_role(repository, row, members, source_buffer)
        if role is not None:
            source_roles.append(role)
    saved = json_object(
        file(
            packet,
            "executions/saved-ledger-review/independent-correspondence-review.json",
        )
    )
    require(
        members[
            "executions/saved-ledger-review/independent-correspondence-review.json"
        ]["sha256"]
        == "94b0a398c78ddd0213195afe770b064e666a3c7578874dc5ab59ed09f87ab9d4",
        "Author-grid saved ledger review identity differs",
    )
    typed(saved["ordered_unique_ledger_cells"], 14074)
    for key in [
        "all_ledger_cells_rejoined_to_saved_R_and_Python",
        "Python_unavailable_estimates_remain_missing",
        "original_R_zero_placeholders_excluded_by_source_support",
        "all_original_saved_input_pins_reauthenticated",
    ]:
        require(
            saved[key] is True, "Author-grid support/missingness source proof differs"
        )
    require(
        saved["cross_epoch_baseline_substitution"] is False
        and saved["historical_9dd1_raw_receipt_available"] is False,
        "Author-grid unavailable history was substituted",
    )
    for key, value in [
        ("source_execution_candidate", EPOCHS["numerical-execution"][0]),
        ("numerical_review_candidate", EPOCHS["numerical-source-review"][0]),
        ("correspondence_producer_candidate", EPOCHS["correspondence-writer"][0]),
    ]:
        require(saved[key] == value, "Author-grid scientific epochs differ")
    for key, wanted in [
        ("correspondence_whole_job_actual_exit", 1),
        ("prior_correspondence_observer_actual_exit", 1),
        ("original_numerical_whole_actual_exit", 1),
        ("correspondence_producer_actual_exit", 0),
        ("new_R_Python_numerical_or_fitting_calls", 0),
    ]:
        typed(saved[key], wanted)
    validate_retained_ledger(
        file(packet, "products/" + FAMILY + "paper-correspondence.csv")
    )
    manifest = json_object(file(packet, "products/" + FAMILY + "manifest.json"))
    require(
        manifest["schema_version"] == "landclim-correspondence-custody.v1"
        and manifest["historical_9dd1_raw_receipt_available"] is False,
        "Author-grid source manifest history differs",
    )
    typed(manifest["original_numerical_whole_job_actual_exit"], 1)
    typed(manifest["saved_output_observer_actual_exit"], 0)
    require(
        manifest["successful_numerical_stage_exits"] == [0, 0]
        and all(type(v) is int for v in manifest["successful_numerical_stage_exits"]),
        "Author-grid successful numerical stage proof differs",
    )
    require(
        manifest["fresh_execution"] == EXECUTION_REPORT
        and manifest["fresh_execution_sha256"]
        == members["products/" + EXECUTION_REPORT]["sha256"],
        "Author-grid current execution report is unbound",
    )
    for name in ["REPORT.md", "paper-correspondence.csv", "report.json"]:
        raw = file(packet, "products/" + FAMILY + name)
        require(
            manifest["retained_files"][name]
            == {"sha256": sha(raw), "bytes": raw.stat().st_size},
            "Author-grid raw writer manifest differs",
        )
    require(
        manifest["admission"]
        == {
            "two_grid_computational_control_only": True,
            "full1128_study_reproduction": False,
            "independent_measured_vegetation_accuracy": False,
            "private_source_redistribution_rights": False,
            "qualified_human_or_official_release": False,
        }
        and all(type(v) is bool for v in manifest["admission"].values()),
        "Author-grid source manifest acceptance was broadened",
    )
    return tuple(source_roles)


def _admit(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    owner_rows(owners)
    capture, members, source_buffer = validated_retained_author_grid(repository)
    packet = file(repository, CAPTURE).parent
    numerical_roles = numerical_scope(
        repository, packet, capture, members, source_buffer
    )
    from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
        parse_routes,
        verified_authored_reader,
    )
    from bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications import (
        validate_evidence,
    )

    routes = parse_routes(file(repository, ACCOUNTS).read_text())
    rows = capture["report_outputs"]
    require(
        isinstance(rows, list)
        and len(rows) == len({r["path"] for r in rows}) == 5
        and {r["path"] for r in rows} == set(PRODUCTS),
        "Author-grid five produced paths differ",
    )
    terminals = {
        lane: json_object(file(packet, "executions/" + lane + "/terminal.json"))
        for lane in ["numerical-source-review", "correspondence-writer"]
    }
    accepted = []
    for raw_row in rows:
        row = object_value(raw_row)
        name = member(row["path"])
        lane, raw_name = PRODUCTS[name]
        require(
            row["execution_lane"] == lane
            and row["raw_name"] == raw_name
            and name in OWNERS.get(row["owner_id"], []),
            "Author-grid produced role attribution differs",
        )
        raw = file(packet, member(row["captured_path"]))
        published = file(packet, member(row["published_captured_path"]))
        current = file(repository, name)
        proof = [
            r for r in terminals[lane]["products"] if r["path"] == row["raw"]["path"]
        ]
        require(
            len(proof) == 1
            and proof[0] == row["raw"] == row["native_terminal_product_proof"]
            and sha(raw) == row["raw"]["sha256"]
            and raw.stat().st_size == row["raw"]["bytes"],
            "Author-grid actual native product proof differs",
        )
        require(
            sha(published) == row["published"]["sha256"]
            and published.stat().st_size == row["published"]["bytes"],
            "Author-grid original published source identity differs",
        )
        entry = tracked_by_path.get(name)
        require(
            entry is not None
            and entry.kind == "file"
            and entry.sha256 == sha(current)
            and entry.size == current.stat().st_size,
            "Author-grid current inventory bytes differ",
        )
        if name == FAMILY + "REPORT.md":
            current_qualification = routes[name].qualification
            require(
                current_qualification is not None,
                "Author-grid current qualification is absent",
            )
            assert current_qualification is not None
            validate_evidence(repository, current_qualification, portal=False)
            require(
                row["comparison"] == "verified_authored_reader",
                "Author-grid managed REPORT comparison differs",
            )
            historical_scope = historical_reader_scope(
                packet, members, raw.read_bytes(), published.read_bytes()
            )
            for scope in [historical_scope, routes[name].scope_reason]:
                require(
                    scope.startswith("Current source-Python")
                    and "not installed-distribution execution" in scope,
                    "Author-grid raw installed vocabulary was promoted to distribution execution",
                )
            require(
                verified_authored_reader(current.read_bytes(), routes[name])
                == raw.read_bytes(),
                "Author-grid current managed REPORT authored bytes differ",
            )
        else:
            require(
                row["comparison"] == "raw_bytes"
                and current.read_bytes() == published.read_bytes() == raw.read_bytes(),
                "Author-grid exact published product bytes differ",
            )
        assert entry is not None
        accepted.append(entry)
    return tuple(accepted), {
        "owner_ids": sorted(OWNERS),
        "capture_sha256": CAPTURE_SHA256,
        "capture_members": 4237,
        "actual_assembly_plan_sha256": ASSEMBLY_PLAN_SHA256,
        "actual_assembly_terminal_sha256": ASSEMBLY_TERMINAL_SHA256,
        "actual_assembly_independent_review_sha256": ASSEMBLY_REVIEW_SHA256,
        "executed_source_candidates": {lane: row[0] for lane, row in EPOCHS.items()},
        "original_numerical_whole_actual_exit": 1,
        "original_correspondence_whole_actual_exit": 1,
        "report_outputs": 5,
        "current_numerical_source_projection": 59,
        "current_byteequal_numerical_sources": 59 - len(numerical_roles),
        "historical_generated_version_metadata": [
            role
            for role in numerical_roles
            if role["classification"] == "historical_generated_version_metadata"
        ],
        "counting_api_source_correspondences": [
            role
            for role in numerical_roles
            if role["classification"] == "finite_counting_api_addition"
        ],
        "original_first_party_source_rows_retained": 15759,
        "source_supported_ledger_cells": 14074,
        "original_R_zero_placeholder_cells_excluded": 15376,
        "historical_9dd1_raw_receipt_available": False,
        "source_Python_distribution_execution_claimed": False,
        "paths_sha256": canonical_json_sha256(sorted(PRODUCTS)),
        "scope": "Five genuinely produced two-grid original-authorR/current-sourcePython reports retained with four distinct epochs. Original numerical and writer whole1/failed observers remain literal; later saved-output/ledger observers and metadata assembly0 are separate. Raw REPORT/installed_lra vocabulary preserved through managed authored-reader verification, no installed-distribution claim. No model/writer replay, full1128 study, vegetation/Nordic ecological accuracy, rights, human or official-release acceptance.",
    }


def validated_author_grid_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit only the five source-bound retained author-grid reports."""
    if not any(row.get("owner_id") in OWNERS for row in owners) and not set(
        PRODUCTS
    ).intersection(tracked_by_path):
        return (), {}
    try:
        return _admit(repository, tracked_by_path, owners)
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise ReportRebuildError(
            "Retained author-grid source admission refused: " + str(error)
        ) from error
