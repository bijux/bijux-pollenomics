"""Supplement artifact and archive-member registries."""

from __future__ import annotations

from functools import cache
from pathlib import Path
import zipfile

from ..models import AdnaSupplementRegistryRow
from ..storage import _source_library_cache_key, build_source_artifact_index


def build_supplement_registry(
    output_root: Path,
) -> tuple[AdnaSupplementRegistryRow, ...]:
    """Return the supplementary-material registry."""
    rows: list[AdnaSupplementRegistryRow] = []
    for artifact in build_source_artifact_index(output_root):
        if not artifact.artifact_kind.startswith("supplementary_"):
            continue
        rows.append(
            AdnaSupplementRegistryRow(
                artifact_id=artifact.artifact_id,
                paper_doi=artifact.paper_doi or "",
                source_url=artifact.source_url,
                local_path=artifact.local_path,
                artifact_kind=artifact.artifact_kind,
                fetch_status=artifact.fetch_status,
                project_accessions=artifact.project_accessions,
                purpose="sample_or_site_support",
            )
        )
    return tuple(sorted(rows, key=lambda item: item.artifact_id))


def build_supplement_zip_member_registry(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    """Return the tracked member inventory for archived supplementary zip bundles."""
    return _build_supplement_zip_member_registry_cached(
        _source_library_cache_key(output_root)
    )


def _build_supplement_zip_member_registry_uncached(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    output_root = Path(output_root)
    rows: list[dict[str, object]] = []
    for artifact in build_source_artifact_index(output_root):
        if artifact.artifact_kind != "supplementary_zip":
            continue
        local_path = output_root / artifact.local_path
        if not local_path.is_file():
            continue
        try:
            with zipfile.ZipFile(local_path) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    rows.append(
                        {
                            "paper_doi": artifact.paper_doi,
                            "parent_artifact_id": artifact.artifact_id,
                            "zip_local_path": artifact.local_path,
                            "member_name": member.filename,
                            "member_local_path": f"{artifact.local_path}#{member.filename}",
                            "member_byte_size": member.file_size,
                            "inferred_purpose": _infer_zip_member_purpose(
                                member.filename
                            ),
                        }
                    )
        except zipfile.BadZipFile:
            rows.append(
                {
                    "paper_doi": artifact.paper_doi,
                    "parent_artifact_id": artifact.artifact_id,
                    "zip_local_path": artifact.local_path,
                    "member_name": "",
                    "member_local_path": artifact.local_path,
                    "member_byte_size": None,
                    "inferred_purpose": "invalid_zip_bundle",
                }
            )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                str(item.get("paper_doi", "")),
                str(item.get("zip_local_path", "")),
                str(item.get("member_name", "")),
            ),
        )
    )


@cache
def _build_supplement_zip_member_registry_cached(
    output_root_key: str,
) -> tuple[dict[str, object], ...]:
    return _build_supplement_zip_member_registry_uncached(Path(output_root_key))


def _infer_zip_member_purpose(member_name: str) -> str:
    lowered = member_name.lower()
    if lowered.endswith((".xlsx", ".xls", ".csv", ".tsv")):
        return "structured_table_candidate"
    if lowered.endswith(".pdf"):
        return "supplementary_pdf_note"
    if lowered.endswith((".txt", ".md")):
        return "readme_or_plaintext_note"
    if lowered.endswith((".fasta", ".fa", ".fq", ".fastq", ".bam")):
        return "sequence_or_alignment_payload"
    return "unclassified_bundle_member"


def _paper_manifest_rows(
    output_root: Path,
    doi: str,
) -> tuple[dict[str, object], ...]:
    output_root = Path(output_root)
    artifact_rows = [
        artifact
        for artifact in build_source_artifact_index(output_root)
        if artifact.paper_doi == doi
    ]
    member_rows = [
        row
        for row in build_supplement_zip_member_registry(output_root)
        if row["paper_doi"] == doi
    ]
    rows: list[dict[str, object]] = []
    for artifact in artifact_rows:
        rows.append(
            {
                "row_kind": "archived_asset",
                "paper_doi": doi,
                "artifact_id": artifact.artifact_id,
                "artifact_kind": artifact.artifact_kind,
                "label": artifact.label,
                "source_url": artifact.source_url,
                "local_path": artifact.local_path,
                "fetch_status": artifact.fetch_status,
                "content_type": artifact.content_type,
                "byte_size": artifact.byte_size,
                "member_name": "",
                "member_local_path": "",
                "inferred_purpose": artifact.remote_note,
            }
        )
    rows.extend(
        {
            "row_kind": "zip_member",
            "paper_doi": doi,
            "artifact_id": row["parent_artifact_id"],
            "artifact_kind": "supplementary_zip_member",
            "label": row["member_name"],
            "source_url": "",
            "local_path": row["zip_local_path"],
            "fetch_status": "archived",
            "content_type": "",
            "byte_size": row["member_byte_size"],
            "member_name": row["member_name"],
            "member_local_path": row["member_local_path"],
            "inferred_purpose": row["inferred_purpose"],
        }
        for row in member_rows
    )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                str(item["row_kind"]),
                str(item["local_path"]),
                str(item["member_name"]),
            ),
        )
    )
