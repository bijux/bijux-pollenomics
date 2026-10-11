"""Reconcile counts, identities and byte receipts in existing source manifests."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import PurePosixPath
from typing import Any

from .evidence import EvidenceReader, digest


def audit_neotoma(reader: EvidenceReader) -> dict[str, Any]:
    """Reconcile relational parts and raw-request IDs without merging entity levels."""
    path = "data/neotoma/relational/manifest.json"
    manifest = reader.json(path)
    if manifest is None:
        reader.issue("governing_neotoma_manifest_missing", path)
        return {"accounting_status": "missing_manifest", "path": path}
    surfaces = []
    dataset_ids: set[int] = set()
    variables: list[dict[str, Any]] = []
    for name, surface in sorted(manifest["surfaces"].items()):
        ids: list[str] = []
        count = 0
        country_counts: Counter[str] = Counter()
        for part in surface["parts"]:
            relative = str(PurePosixPath(path).parent / part["path"])
            content = reader.verify(relative, part)
            if content is None:
                continue
            payload = json.loads(content)
            rows = payload["rows"]
            if len(rows) != part["row_count"] or payload["row_count"] != len(rows):
                reader.issue("relational_part_count_mismatch", relative)
            count += len(rows)
            for row in rows:
                identity = row.get(surface["id_field"])
                if identity is None:
                    reader.issue("relational_identity_missing", relative)
                else:
                    ids.append(identity)
                country_counts[row.get("country_code") or "unresolved"] += 1
                if name == "datasets":
                    dataset_ids.add(row["source_dataset_id"])
                if name == "variables":
                    variables.append(row)
        duplicates = sorted(k for k, n in Counter(ids).items() if n > 1)
        if duplicates:
            reader.issue(
                "relational_duplicate_identity", path, surface=name, ids=duplicates
            )
        if count != surface["row_count"]:
            reader.issue(
                "relational_surface_count_mismatch",
                path,
                surface=name,
                declared=surface["row_count"],
                observed=count,
            )
        if surface["part_count"] != len(surface["parts"]):
            reader.issue("relational_part_inventory_mismatch", path, surface=name)
        surfaces.append(
            {
                "entity_level": name,
                "declared_row_count": surface["row_count"],
                "observed_row_count": count,
                "distinct_identity_count": len(set(ids)),
                "identity_set_sha256": digest(sorted(set(ids))),
                "duplicate_ids": duplicates,
                "country_counts": dict(sorted(country_counts.items())),
            }
        )
    raw_path = "data/neotoma/raw/neotoma_pollen_dataset_downloads/manifest.json"
    raw = reader.json(raw_path)
    request_audit: dict[str, Any] = {"accounting_status": "missing_raw_manifest"}
    if raw is None:
        reader.issue("raw_download_manifest_missing", raw_path)
    if raw is not None:
        requested = raw["requested_dataset_ids"]
        downloaded = raw["downloaded_dataset_ids"]
        for field, values in (("requested", requested), ("downloaded", downloaded)):
            if raw[f"{field}_dataset_count"] != len(values) or len(set(values)) != len(
                values
            ):
                reader.issue("dataset_request_count_mismatch", raw_path, field=field)
        differences = {
            "requested_not_downloaded": sorted(set(requested) - set(downloaded)),
            "downloaded_not_requested": sorted(set(downloaded) - set(requested)),
            "downloaded_not_normalized": sorted(set(downloaded) - dataset_ids),
            "normalized_not_downloaded": sorted(dataset_ids - set(downloaded)),
        }
        if any(differences.values()):
            reader.issue("dataset_request_identity_mismatch", raw_path, **differences)
        raw_part_ids: list[int] = []
        for part in raw.get("parts", []):
            relative = str(PurePosixPath(raw_path).parent / part["filename"])
            content = reader.verify(relative, part)
            if content is None:
                continue
            payload = json.loads(content)
            actual_ids = [
                row["site"]["dataset"]["datasetid"] for row in payload["rows"]
            ]
            raw_part_ids.extend(actual_ids)
            if (
                len(actual_ids) != part["row_count"]
                or len(actual_ids) != payload["row_count"]
                or sorted(actual_ids) != sorted(part["downloaded_dataset_ids"])
                or sorted(actual_ids) != sorted(payload["downloaded_dataset_ids"])
            ):
                reader.issue("raw_download_part_identity_mismatch", relative)
        if "parts" in raw and (
            sorted(raw_part_ids) != sorted(downloaded)
            or raw["part_count"] != len(raw["parts"])
        ):
            reader.issue("raw_download_inventory_mismatch", raw_path)
        request_audit = {
            "requested_dataset_ids": requested,
            "downloaded_dataset_ids": downloaded,
            "normalized_dataset_ids": sorted(dataset_ids),
            **differences,
            "raw_part_dataset_ids": sorted(raw_part_ids),
            "scope_note": "Pinned request scope; not all records in the live provider.",
        }
    return {
        "manifest_path": path,
        "source_snapshot_id": manifest["source_snapshot_id"],
        "surfaces": surfaces,
        "requests": request_audit,
        "taxa_review_inventory": variables,
        "semantic_confirmation": "not_established_by_count_reconciliation",
    }


def audit_sead(reader: EvidenceReader, governing_path: str | None) -> dict[str, Any]:
    """Follow the fact ownership authority, never select the newest directory."""
    if governing_path is None:
        reader.issue(
            "governing_sead_manifest_reference_missing",
            "data/source_fact_ownership_registry.json",
        )
        return {"accounting_status": "missing_governing_manifest_reference"}
    manifest = reader.json(governing_path)
    if manifest is None:
        reader.issue("governing_sead_manifest_missing", governing_path)
        return {
            "accounting_status": "missing_governing_manifest",
            "path": governing_path,
        }
    parent = PurePosixPath(governing_path).parent
    for entry in manifest["files"]:
        reader.verify(str(parent / entry["path"]), entry)
    acquisition = f"data/sead/raw/acquisitions/{parent.name}/manifest.json"
    raw = reader.json(acquisition)
    if raw is None:
        reader.issue("sead_acquisition_manifest_missing", acquisition)
    if raw is not None:
        for entry in raw["files"]:
            reader.verify(str(PurePosixPath(acquisition).parent / entry["path"]), entry)
    native_path = str(parent / "source_native_observations.json")
    native = reader.json(native_path)
    if native is None:
        reader.issue("sead_native_observation_index_missing", native_path)
    result = {
        key: value
        for key, value in manifest.items()
        if key.endswith("count") or key in ("build_id", "source_run_id")
    }
    result["governing_manifest_path"] = governing_path
    result["acquisition_receipt"] = (
        None
        if raw is None
        else {key: value for key, value in raw.items() if key != "files"}
    )
    if native is not None:
        result["source_native_denominators"] = {
            key: value
            for key, value in native.items()
            if key.endswith("counts") or key == "observation_count"
        }
        total = native["observation_count"]
        for dimension in (
            "country_counts",
            "observation_table_counts",
            "chronology_link_status_counts",
            "taxon_status_counts",
            "unit_status_counts",
        ):
            if sum(native[dimension].values()) != total:
                reader.issue(
                    "source_native_denominator_mismatch",
                    native_path,
                    dimension=dimension,
                )
        if total != manifest["observation_count"]:
            reader.issue("source_native_observation_count_mismatch", native_path)
    if (
        manifest["eligible_event_count"] + manifest["refused_event_count"]
        != manifest["observation_count"]
    ):
        reader.issue("event_disposition_count_mismatch", governing_path)
    result["semantic_confirmation"] = "not_established_by_file_reconciliation"
    return result
