"""Admit the exact one-product Amsoldingersee refusal replay and its retained public source proof."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ....contracts import JsonObject, ReportRebuildError
from ....ownership import ReportOwnershipError, _regular_confined_file
from .execution import (
    REFERENCE_SHAS,
    SOURCE_CANDIDATE,
    exact,
    native_histories,
    refusal,
    require,
)
from .members import catalogs, content, load, namespace

CAPTURE = "data/source-custody/landclim/amsoldingersee/capture.json"
CAPTURE_SHA256 = "3c1d102fb62d1ff91229104e313795da733deb81901f5b74402232c01d1c4415"
OWNER = "publication-replay/landclim-amsoldingersee-source-review/report-products"
REPORT = (
    "docs/report/publication-replay/landclim-amsoldingersee-source-review/report.json"
)
REPORT_SHA256 = "eb1d20e578c9bdbdb12ffbeab3eba87522cc98006de7c8919bac2bc29683d1a7"


def regular(repository: Path, name: str) -> Path:
    try:
        return _regular_confined_file(
            repository, name, "Amsoldingersee retained source"
        )
    except (OSError, ReportOwnershipError) as error:
        raise ReportRebuildError("Unconfined retained Amsoldingersee file") from error


def validate_packet(root: Path, capture: dict[str, Any]) -> None:
    require(
        capture["schema_version"] == "amsoldingersee-retained-source-capture.v1",
        "Capture schema changed",
    )
    namespace(root, capture["members"])
    require(
        set(capture["jobs"]) == {"production", "observation"},
        "Two original source histories required",
    )
    jobs: dict[str, dict[str, Any]] = {}
    for label, refs in capture["jobs"].items():
        require(
            set(refs) == set(REFERENCE_SHAS[label]),
            "Complete original reference set differs",
        )
        jobs[label] = {}
        for name, member in refs.items():
            require(
                capture["members"][member]["sha256"] == REFERENCE_SHAS[label][name],
                "Original reference bytes changed",
            )
            jobs[label][name] = load(root / member)
    native_histories(jobs)
    catalogs(root, capture, jobs)
    require(
        capture["original_execution_candidate"] == SOURCE_CANDIDATE
        and exact(capture["original_whole_exits"], [1, 0])
        and exact(capture["original_native_exits"], [[0, 1], [0]]),
        "Original candidate/history claims changed",
    )
    require(
        capture["metadata_assembly_candidate"] == SOURCE_CANDIDATE,
        "Metadata candidate missing",
    )
    require(
        capture["new_model_or_HTTP_execution"] is False
        and capture["rights_human_ecology_or_LRA_admitted"] is False,
        "Retention inflated scientific/source rights scope",
    )
    report = load(root / capture["report_member"])
    refusal(report)
    require(
        exact(
            content(root / capture["report_member"]),
            {"sha256": REPORT_SHA256, "bytes": 4006},
        ),
        "Actual source report changed",
    )
    require(
        exact(
            capture["original_input_counts"],
            {label: len(doc["plan.json"]["input_pins"]) for label, doc in jobs.items()},
        ),
        "Original catalog count claim changed",
    )
    source_paths = sorted(
        {
            row["path"]
            for label, doc in jobs.items()
            for row, role in zip(
                doc["plan.json"]["input_pins"],
                capture["input_roles"][label],
                strict=True,
            )
            if role["role"] == "public_source"
        }
    )
    require(
        exact(capture["public_source_original_paths"], source_paths)
        and exact(capture["public_first_party_source_identities"], len(source_paths)),
        "Public original source count/membership claim changed",
    )


def validated_amsoldingersee_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject | None]:
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    if not selected and not (repository / CAPTURE).exists():
        return (), None
    try:
        require(len(selected) == 1, "Exactly one source-review owner required")
        for key, value in {
            "role": "retained_source",
            "paths": [REPORT],
            "producer_paths": [],
            "producer_inputs": [],
        }.items():
            require(
                exact(selected[0][key], value), "Exact retained owner boundary changed"
            )
        require(CAPTURE_SHA256 != "UNASSEMBLED", "No actual metadata capture assembled")
        capture_path = regular(repository, CAPTURE)
        require(
            hashlib.sha256(capture_path.read_bytes()).hexdigest() == CAPTURE_SHA256,
            "Closed source capture SHA differs",
        )
        capture = load(capture_path)
        validate_packet(capture_path.parent, capture)
        product = regular(repository, REPORT)
        source = capture_path.parent / capture["report_member"]
        require(
            product.read_bytes() == source.read_bytes(),
            "Tracked report differs from genuine source output",
        )
        entry = tracked_by_path.get(REPORT)
        require(entry is not None, "Governed tracked report missing")
        assert entry is not None
        require(
            entry.path == REPORT.removeprefix("docs/report/")
            and entry.kind == "file"
            and entry.sha256 == REPORT_SHA256
            and entry.size == 4006,
            "Tracked inventory identity differs",
        )
        return (entry,), {
            "capture_sha256": CAPTURE_SHA256,
            "original_execution_candidate": SOURCE_CANDIDATE,
            "original_whole_exits": [1, 0],
            "original_native_exits": [[0, 1], [0]],
            "tracked_byte_checker_exit": 0,
            "historical_E69_chronology_rights_human_or_LRA_admitted": False,
        }
    except (KeyError, ValueError, OSError, TypeError) as error:
        raise ReportRebuildError(
            "Invalid retained Amsoldingersee source proof"
        ) from error
