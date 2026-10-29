"""Validate additive Sweden observations while preserving the unresolved receipt owner."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ....contracts import JsonObject, ReportRebuildError
from ....retained_source import validated_descriptor
from .contracts import require, strict_equal
from .execution import OLD_REPORT_SHA, OWNER
from .execution import REPORT as REPORT
from .members import MAX_CAPTURE, load_reference, validate_capture
from .metadata import (
    PROOF_IDENTITIES,
    exact_file,
    object_buffer,
    validate_historical_reader,
    validate_metadata,
    validate_recorded_source_contracts,
)

CAPTURE = "data/source-custody/country-reports/sweden/packet/capture.json"
CURRENT_RECEIPT = "reports/science/country-reports/sweden-current-receipt.json"
WITNESS = "reports/science/country-reports/sweden-current-semantic-replay.json"
CAPTURE_SHA256 = "db9b8c79c3be74c567344bfb5002430dd408067ec2ccdfe6bd68b8d44afcd05d"
WITNESS_SHA256 = "935a24e5ec96d45c6580b3add8574f0765a3b0c337c33ad5455cad4cae2f8653"
ORIGINAL_OWNER: dict[str, Any] = {
    "owner_id": "countries/sweden/land-use-replay/semantic-receipt",
    "role": "unresolved",
    "paths": ["docs/report/countries/sweden/land-use-replay/receipt.json"],
    "producer_paths": [
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/sweden_land_use_replay.py"
    ],
    "producer_inputs": [
        "data/aadr/v66/1240k/v66.1240K.aadr.PUB.anno",
        "data/aadr/v66/ho/v66.HO.aadr.PUB.anno",
        "data/aadr/v66/release_manifest.json",
        "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson",
        "data/sead/normalized/nordic_temporal_evidence.geojson",
        "data/svar/review/lake_candidate_registry_review.json",
        "data/svar/review/sweden_lake_candidate_registry.geojson",
    ],
    "verification": "The replay invokes the full country-report bundle producer, hashes published outputs and upstream products, and uses runtime generated date. Seven direct source files alone are not the complete producer input/template closure. Bind full country-producer source closure, published comparands and time control before generated ownership; this receipt is reproducibility evidence, not vegetation validation.",
}


def selected_owner(owners: list[JsonObject]) -> dict[str, Any] | None:
    """Require the unique declared report owner and its source roles."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    require(len(selected) <= 1, "Duplicate Sweden receipt owner")
    if not selected:
        return None
    expected = deepcopy(ORIGINAL_OWNER)
    require(
        expected.get("owner_id") == OWNER
        and expected.get("role") == "unresolved"
        and expected.get("paths") == [REPORT],
        "Full original Sweden criterion absent",
    )
    require(
        strict_equal(selected[0], expected),
        "Exact unresolved Sweden owner criterion changed",
    )
    for row in owners:
        if row not in selected:
            paths = row.get("paths")
            require(
                not isinstance(paths, list) or REPORT not in paths,
                "Sweden receipt ownership overlap",
            )
    return selected[0]


def validated_sweden_country_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject | None]:
    """Authenticate retained Sweden country evidence and metadata correspondence."""
    for name in (CAPTURE, WITNESS, CURRENT_RECEIPT):
        path = repository / name
        if any(node.is_symlink() for node in (path, *path.parents)):
            raise ReportRebuildError("Current Sweden evidence ancestry alias refused")
    evidence_present = any(
        (repository / name).exists() or (repository / name).is_symlink()
        for name in (CAPTURE, WITNESS, CURRENT_RECEIPT)
    )
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    if not selected and not evidence_present:
        return (), None
    try:
        if not evidence_present:
            require(
                selected_owner(owners) is not None,
                "Original receipt owner absent",
            )
            path = repository / REPORT
            require(
                path.is_file()
                and not any(p.is_symlink() for p in (path, *path.parents))
                and hashlib.sha256(path.read_bytes()).hexdigest() == OLD_REPORT_SHA,
                "Legacy unresolved Sweden receipt changed",
            )
            return (), None
        require(
            selected_owner(owners) is not None,
            "Original unresolved receipt owner absent",
        )
        require(
            CAPTURE_SHA256 != "UNASSEMBLED" and WITNESS_SHA256 != "UNASSEMBLED",
            "No actual portable country capture assembled",
        )
        capture_path = repository / CAPTURE
        require(
            capture_path.is_file()
            and type(capture_path.stat().st_size) is int
            and 0 < capture_path.stat().st_size <= MAX_CAPTURE,
            "Bounded capture metadata absent",
        )
        capture_raw = exact_file(
            repository,
            CAPTURE,
            {"sha256": CAPTURE_SHA256, "bytes": capture_path.stat().st_size},
        )
        capture = object_buffer(capture_raw)
        resolver = validated_descriptor(
            repository, Path(CAPTURE).parent.as_posix(), capture["members"]
        )
        native = validate_capture(capture_path.parent, capture, resolver)
        declaration = load_reference(
            capture_path.parent, "source-declaration", capture, resolver
        )
        require(
            type(declaration["maintained_source_contracts"]) is list
            and len(declaration["maintained_source_contracts"]) == 51
            and len({row["path"] for row in declaration["maintained_source_contracts"]})
            == 51,
            "Complete current maintained science source correspondence required",
        )
        source_contracts = validate_recorded_source_contracts(
            repository, declaration["maintained_source_contracts"], resolver
        )
        saved = load_reference(capture_path.parent, "saved-plan", capture, resolver)
        metadata_plan = PROOF_IDENTITIES.get("plan")
        require(metadata_plan is not None, "Actual portable metadata plan absent")
        assert metadata_plan is not None
        original_capture = {
            "path": str(Path(metadata_plan["path"]).parent / "packet/capture.json"),
            "sha256": CAPTURE_SHA256,
            "bytes": len(capture_raw),
        }
        metadata = validate_metadata(repository, capture, original_capture, saved)
        expected_receipt = capture["reference_original_identities"]["country-receipt"]
        report_raw = exact_file(
            repository, CURRENT_RECEIPT, expected_receipt, MAX_CAPTURE
        )
        require(
            report_raw
            == resolver.read_source(capture["references"]["country-receipt"]),
            "Additive receipt is not the actual native emitted bytes",
        )
        witness_path = repository / WITNESS
        require(
            witness_path.is_file() and witness_path.stat().st_size <= MAX_CAPTURE,
            "Current receipt witness absent",
        )
        witness = object_buffer(
            exact_file(
                repository,
                WITNESS,
                {"sha256": WITNESS_SHA256, "bytes": witness_path.stat().st_size},
            )
        )
        require(
            strict_equal(witness["native_witness"], native)
            and strict_equal(witness["metadata_retention"], metadata)
            and witness["portable_capture"]
            == {"path": CAPTURE, "sha256": CAPTURE_SHA256, "bytes": len(capture_raw)}
            and witness["historical_receipt_sha256"] == OLD_REPORT_SHA
            and witness["original_report_owner_admitted"] is False
            and witness["governed_historical_receipt_unchanged"] is True
            and strict_equal(
                witness["current_receipt"],
                {
                    "path": CURRENT_RECEIPT,
                    "sha256": expected_receipt["sha256"],
                    "bytes": expected_receipt["bytes"],
                },
            ),
            "Current witness/native/portable source joins differ",
        )
        exact_file(
            repository,
            REPORT,
            {"sha256": OLD_REPORT_SHA, "bytes": 5680},
        )
        validate_historical_reader(repository, witness["historical_reader_raw_sha256"])
        entry = tracked_by_path.get(REPORT)
        require(entry is not None, "Governed Sweden receipt inventory missing")
        assert entry is not None
        require(
            entry.path == REPORT.removeprefix("docs/report/")
            and entry.kind == "file"
            and entry.sha256 == OLD_REPORT_SHA
            and entry.size == 5680,
            "Governed historical receipt inventory differs",
        )
        return (), {
            "owner_ids": [],
            "admitted_inventory_entries": 0,
            "original_owner_role": "unresolved",
            "original_owner_acceptance_established": False,
            "current_receipt_path": CURRENT_RECEIPT,
            "governed_historical_receipt_path": REPORT,
            "capture_sha256": CAPTURE_SHA256,
            "current_receipt_sha256": expected_receipt["sha256"],
            "country_call_returned_normally": True,
            "original_controller_actual_exit": 1,
            "original_whole_actual_exit": 1,
            "saved_observer_actual_exit": 0,
            "saved_whole_actual_exit": 0,
            "metadata_assembly_actual_exit": 0,
            "metadata_observer_actual_exit": 0,
            "metadata_whole_actual_exit": 0,
            "source_owned_native_UTC_day": native["native_UTC_clock"]["native_UTC_day"],
            "recorded_producer_source_contracts": source_contracts,
            "tracked_byte_checker_actual_exit": native[
                "tracked_byte_checker_actual_exit"
            ],
            "missing_full_return_read_or_origin_telemetry_recovered": False,
            "vegetation_rights_human_biology_or_LRA_acceptance": False,
        }
    except (KeyError, ValueError, TypeError, OSError, ReportRebuildError) as error:
        raise ReportRebuildError(
            "Invalid retained current Sweden source receipt"
        ) from error
