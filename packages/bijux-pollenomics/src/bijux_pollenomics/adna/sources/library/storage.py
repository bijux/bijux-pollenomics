"""aDNA source artifact storage, indexing, and reference-stash discovery."""

from __future__ import annotations

import json
import os
from functools import cache
from pathlib import Path

from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog
from bijux_pollenomics.adna.workflow.paths import (
    adna_source_library_root,
)
from bijux_pollenomics.adna.workflow.source_artifacts import (
    resolve_source_artifact_path,
    source_artifact_exists,
)

from .models import (
    SOURCE_LIBRARY_SCHEMA_VERSION,
    AdnaSourceArtifact,
    _ReferenceStashDraft,
    _ReferenceStashRecord,
)
from .specifications import (
    _doi_slug,
    _expand_remote_assets,
    _paper_source_specs,
    _project_remote_assets,
)


def _source_library_cache_key(output_root: Path) -> str:
    return str(Path(output_root).resolve())


def build_source_artifact_index(output_root: Path) -> tuple[AdnaSourceArtifact, ...]:
    """Return the tracked source artifact index from the local archive tree."""
    return _build_source_artifact_index_cached(_source_library_cache_key(output_root))


def build_source_storage_audit(output_root: Path) -> dict[str, object]:
    """Return storage posture for tracked local source artifacts."""
    artifacts = build_source_artifact_index(output_root)
    archived_artifacts = tuple(
        artifact for artifact in artifacts if artifact.fetch_status == "archived"
    )
    html_artifacts = tuple(
        artifact
        for artifact in archived_artifacts
        if artifact.local_path.endswith(".html")
    )
    compressed_html_artifacts = tuple(
        artifact
        for artifact in html_artifacts
        if artifact.content_encoding == "gzip"
        or str(artifact.storage_path or "").endswith(".html.gz")
    )
    rows = []
    for artifact in html_artifacts:
        rows.append(
            {
                "artifact_id": artifact.artifact_id,
                "artifact_kind": artifact.artifact_kind,
                "paper_doi": artifact.paper_doi,
                "local_path": artifact.local_path,
                "storage_path": artifact.storage_path or artifact.local_path,
                "content_encoding": artifact.content_encoding or "identity",
                "byte_size": artifact.byte_size,
                "storage_byte_size": artifact.storage_byte_size,
                "project_accessions": list(artifact.project_accessions),
            }
        )
    rows.sort(key=lambda item: (str(item["paper_doi"] or ""), str(item["artifact_id"])))
    return {
        "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
        "archived_artifact_count": len(archived_artifacts),
        "archived_html_artifact_count": len(html_artifacts),
        "compressed_html_artifact_count": len(compressed_html_artifacts),
        "uncompressed_html_artifact_count": len(html_artifacts)
        - len(compressed_html_artifacts),
        "archived_payload_byte_count": sum(
            artifact.byte_size or 0 for artifact in archived_artifacts
        ),
        "archived_storage_byte_count": sum(
            artifact.storage_byte_size or artifact.byte_size or 0
            for artifact in archived_artifacts
        ),
        "html_payload_byte_count": sum(
            artifact.byte_size or 0 for artifact in html_artifacts
        ),
        "html_storage_byte_count": sum(
            artifact.storage_byte_size or artifact.byte_size or 0
            for artifact in html_artifacts
        ),
        "rows": rows,
    }


def _build_source_artifact_index_uncached(
    output_root: Path,
) -> tuple[AdnaSourceArtifact, ...]:
    output_root = Path(output_root)
    rows = list(_iter_materialized_artifacts(output_root))
    return tuple(
        sorted(rows, key=lambda item: (item.paper_doi or "", item.artifact_id))
    )


@cache
def _build_source_artifact_index_cached(
    output_root_key: str,
) -> tuple[AdnaSourceArtifact, ...]:
    return _build_source_artifact_index_uncached(Path(output_root_key))


def _artifact_kind_from_filename(filename: str) -> str:
    lowered = filename.lower()
    if lowered.endswith(".zip"):
        return "supplementary_zip"
    if lowered.endswith((".pdf", ".docx")):
        return "supplementary_pdf"
    if lowered.endswith((".xlsx", ".xls", ".csv", ".tsv")):
        return "supplementary_table"
    if lowered.endswith((".jpg", ".jpeg", ".png")):
        return "supplementary_image"
    return "supplementary_other"


def _content_type_from_filename(filename: str) -> str:
    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        return "application/pdf"
    if lowered.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if lowered.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if lowered.endswith(".xls"):
        return "application/vnd.ms-excel"
    if lowered.endswith(".csv"):
        return "text/csv"
    if lowered.endswith(".json"):
        return "application/json"
    if lowered.endswith(".tsv"):
        return "text/tab-separated-values"
    if lowered.endswith(".zip"):
        return "application/zip"
    if lowered.endswith(".xml"):
        return "application/xml"
    if lowered.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lowered.endswith(".png"):
        return "image/png"
    return "application/octet-stream"


def _iter_materialized_artifacts(output_root: Path) -> tuple[AdnaSourceArtifact, ...]:
    source_root = adna_source_library_root(Path(output_root))
    rows: list[AdnaSourceArtifact] = []
    seen_artifact_ids: set[str] = set()
    catalog = build_archive_project_catalog()
    for project in catalog:
        local_path = (
            source_root
            / "projects"
            / project.project_accession
            / "archive_metadata.html"
        )
        metadata_path = local_path.with_suffix(local_path.suffix + ".metadata.json")
        fetch_status = "missing"
        content_type = None
        byte_size = None
        storage_path = None
        storage_byte_size = None
        content_encoding = None
        if metadata_path.is_file():
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            fetch_status = "archived"
            content_type = payload.get("content_type")
            byte_size = payload.get("byte_size")
            storage_path = payload.get("storage_path")
            storage_byte_size = payload.get("storage_byte_size")
            content_encoding = payload.get("content_encoding")
        elif source_artifact_exists(local_path):
            fetch_status = "archived"
            stored_path = resolve_source_artifact_path(local_path)
            byte_size = stored_path.stat().st_size
            storage_path = str(stored_path.relative_to(output_root))
            storage_byte_size = stored_path.stat().st_size
            content_encoding = "gzip" if stored_path.suffix == ".gz" else None
        rows.append(
            AdnaSourceArtifact(
                artifact_id=f"{project.project_accession}:archive_metadata.html",
                artifact_kind="archive_metadata_html",
                label="archive metadata page",
                source_url=project.metadata_url,
                local_path=str(local_path.relative_to(output_root)),
                fetch_status=fetch_status,
                remote_note="Archive-facing metadata page captured for the tracked accession.",
                project_accessions=(project.project_accession,),
                paper_doi=None
                if project.paper_linkage is None
                else project.paper_linkage.doi,
                content_type=content_type,
                byte_size=byte_size,
                storage_path=storage_path,
                storage_byte_size=storage_byte_size,
                content_encoding=content_encoding,
            )
        )
        seen_artifact_ids.add(f"{project.project_accession}:archive_metadata.html")
        for remote in _project_remote_assets(project.project_accession):
            asset_path = source_root / remote.relative_path
            metadata_path = asset_path.with_suffix(asset_path.suffix + ".metadata.json")
            metadata = (
                json.loads(metadata_path.read_text(encoding="utf-8"))
                if metadata_path.is_file()
                else {}
            )
            artifact_id = f"{project.project_accession}:{asset_path.name}"
            rows.append(
                AdnaSourceArtifact(
                    artifact_id=artifact_id,
                    artifact_kind=remote.artifact_kind,
                    label=remote.label,
                    source_url=remote.source_url,
                    local_path=str(asset_path.relative_to(output_root)),
                    fetch_status=(
                        "archived" if source_artifact_exists(asset_path) else "missing"
                    ),
                    remote_note=remote.remote_note,
                    project_accessions=(project.project_accession,),
                    paper_doi=(
                        None
                        if project.paper_linkage is None
                        else project.paper_linkage.doi
                    ),
                    content_type=metadata.get("content_type"),
                    byte_size=metadata.get("byte_size"),
                    storage_path=(
                        str(
                            resolve_source_artifact_path(asset_path).relative_to(
                                output_root
                            )
                        )
                        if source_artifact_exists(asset_path)
                        else None
                    ),
                    storage_byte_size=metadata.get("storage_byte_size"),
                    content_encoding=metadata.get("content_encoding"),
                )
            )
            seen_artifact_ids.add(artifact_id)
            if metadata_path.is_file():
                receipt_id = f"{project.project_accession}:{metadata_path.name}"
                rows.append(
                    AdnaSourceArtifact(
                        artifact_id=receipt_id,
                        artifact_kind="source_receipt_json",
                        label=f"capture receipt for {remote.label}",
                        source_url=remote.source_url,
                        local_path=str(metadata_path.relative_to(output_root)),
                        fetch_status="archived",
                        remote_note=(
                            "Capture receipt preserves source URL, byte and digest "
                            "identity, licensing, and evidence locators."
                        ),
                        project_accessions=(project.project_accession,),
                        paper_doi=(
                            None
                            if project.paper_linkage is None
                            else project.paper_linkage.doi
                        ),
                        content_type="application/json",
                        byte_size=metadata_path.stat().st_size,
                        storage_path=str(metadata_path.relative_to(output_root)),
                        storage_byte_size=metadata_path.stat().st_size,
                    )
                )
                seen_artifact_ids.add(receipt_id)
        if project.project_accession == "PRJEB59481":
            for filename, artifact_kind in (
                (
                    "material_evidence_conflicts.json",
                    "material_evidence_conflict_json",
                ),
                (
                    "material_evidence_conflicts.csv",
                    "material_evidence_conflict_csv",
                ),
            ):
                artifact_path = (
                    source_root / "projects" / project.project_accession / filename
                )
                artifact_id = f"{project.project_accession}:{filename}"
                exists = artifact_path.is_file()
                rows.append(
                    AdnaSourceArtifact(
                        artifact_id=artifact_id,
                        artifact_kind=artifact_kind,
                        label="unresolved ENA-versus-supplement material evidence",
                        source_url="",
                        local_path=str(artifact_path.relative_to(output_root)),
                        fetch_status="archived" if exists else "missing",
                        remote_note=(
                            "Source-derived conflict ledger preserves both anatomical "
                            "claims without selecting either one."
                        ),
                        project_accessions=(project.project_accession,),
                        paper_doi=(
                            None
                            if project.paper_linkage is None
                            else project.paper_linkage.doi
                        ),
                        content_type=_content_type_from_filename(filename),
                        byte_size=artifact_path.stat().st_size if exists else None,
                        storage_path=(
                            str(artifact_path.relative_to(output_root))
                            if exists
                            else None
                        ),
                        storage_byte_size=(
                            artifact_path.stat().st_size if exists else None
                        ),
                    )
                )
                seen_artifact_ids.add(artifact_id)
    for doi, spec in _paper_source_specs().items():
        projects = tuple(
            sorted(
                project.project_accession
                for project in catalog
                if project.paper_linkage is not None
                and project.paper_linkage.doi == doi
            )
        )
        for remote in _expand_remote_assets(spec, catalog):
            local_path = source_root / remote.relative_path
            metadata_path = local_path.with_suffix(local_path.suffix + ".metadata.json")
            fetch_status = "missing"
            content_type = None
            byte_size = None
            storage_path = None
            storage_byte_size = None
            content_encoding = None
            if metadata_path.is_file():
                payload = json.loads(metadata_path.read_text(encoding="utf-8"))
                fetch_status = "archived"
                content_type = payload.get("content_type")
                byte_size = payload.get("byte_size")
                storage_path = payload.get("storage_path")
                storage_byte_size = payload.get("storage_byte_size")
                content_encoding = payload.get("content_encoding")
            elif source_artifact_exists(local_path):
                fetch_status = "archived"
                stored_path = resolve_source_artifact_path(local_path)
                byte_size = stored_path.stat().st_size
                storage_path = str(stored_path.relative_to(output_root))
                storage_byte_size = stored_path.stat().st_size
                content_encoding = "gzip" if stored_path.suffix == ".gz" else None
            rows.append(
                AdnaSourceArtifact(
                    artifact_id=_artifact_id(doi, local_path.name),
                    artifact_kind=remote.artifact_kind,
                    label=remote.label,
                    source_url=remote.source_url,
                    local_path=str(local_path.relative_to(output_root)),
                    fetch_status=fetch_status,
                    remote_note=remote.remote_note,
                    project_accessions=projects,
                    paper_doi=doi,
                    content_type=content_type,
                    byte_size=byte_size,
                    storage_path=storage_path,
                    storage_byte_size=storage_byte_size,
                    content_encoding=content_encoding,
                )
            )
            seen_artifact_ids.add(_artifact_id(doi, local_path.name))
            if (
                remote.artifact_kind == "article_full_text_xml"
                and metadata_path.is_file()
            ):
                receipt_id = _artifact_id(doi, metadata_path.name)
                rows.append(
                    AdnaSourceArtifact(
                        artifact_id=receipt_id,
                        artifact_kind="source_receipt_json",
                        label=f"capture receipt for {remote.label}",
                        source_url=remote.source_url,
                        local_path=str(metadata_path.relative_to(output_root)),
                        fetch_status="archived",
                        remote_note=(
                            "Capture receipt preserves source URL, byte and digest "
                            "identity, licensing, and evidence locators."
                        ),
                        project_accessions=projects,
                        paper_doi=doi,
                        content_type="application/json",
                        byte_size=metadata_path.stat().st_size,
                        storage_path=str(metadata_path.relative_to(output_root)),
                        storage_byte_size=metadata_path.stat().st_size,
                    )
                )
                seen_artifact_ids.add(receipt_id)
    for metadata_path in sorted(
        source_root.glob("papers/*/supplementary/*.*.metadata.json")
    ):
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        paper_doi = str(payload.get("paper_doi", "")).strip()
        artifact_path = Path(str(metadata_path)[: -len(".metadata.json")])
        artifact_id = _artifact_id(paper_doi, artifact_path.name)
        if not paper_doi or artifact_id in seen_artifact_ids:
            continue
        rows.append(
            AdnaSourceArtifact(
                artifact_id=artifact_id,
                artifact_kind=str(payload.get("artifact_kind", "supplementary_other")),
                label=str(payload.get("artifact_label", artifact_path.name)),
                source_url=str(payload.get("source_url", "")),
                local_path=str(artifact_path.relative_to(output_root)),
                fetch_status="archived"
                if source_artifact_exists(artifact_path)
                else "missing",
                remote_note=str(payload.get("source_note", "")),
                project_accessions=tuple(
                    str(item) for item in payload.get("project_accessions", [])
                ),
                paper_doi=paper_doi,
                content_type=payload.get("content_type"),
                byte_size=payload.get("byte_size"),
                storage_path=str(
                    resolve_source_artifact_path(artifact_path).relative_to(output_root)
                )
                if source_artifact_exists(artifact_path)
                else None,
                storage_byte_size=payload.get("storage_byte_size"),
                content_encoding=payload.get("content_encoding"),
            )
        )
        seen_artifact_ids.add(artifact_id)
    return tuple(rows)


def _resolve_reference_stash_root(output_root: Path) -> Path | None:
    env_root = os.environ.get("BIJUX_POLLENOMICS_REFERENCE_STASH_ROOT", "").strip()
    candidates: list[Path] = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(
        Path(output_root).resolve().parent.parent
        / "bijan-references"
        / "bijux-pollenomics"
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def _reference_stash_records(output_root: Path) -> dict[str, _ReferenceStashRecord]:
    return _reference_stash_records_cached(_source_library_cache_key(output_root))


def _reference_stash_records_uncached(
    output_root: Path,
) -> dict[str, _ReferenceStashRecord]:
    stash_root = _resolve_reference_stash_root(output_root)
    if stash_root is None:
        return {}
    records: dict[str, _ReferenceStashDraft] = {}
    for article_path in stash_root.glob("*.pdf"):
        slug = article_path.stem
        records.setdefault(
            slug,
            {
                "stash_slug": slug,
                "article_formats": set(),
                "supplementary_assets": [],
                "structured_table_count": 0,
                "archive_bundle_count": 0,
            },
        )
        records[slug]["article_formats"].add(
            article_path.suffix.lower().removeprefix(".")
        )
    for doi_dir in sorted(
        path
        for path in stash_root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    ):
        record = records.setdefault(
            doi_dir.name,
            {
                "stash_slug": doi_dir.name,
                "article_formats": set(),
                "supplementary_assets": [],
                "structured_table_count": 0,
                "archive_bundle_count": 0,
            },
        )
        for asset in sorted(path for path in doi_dir.rglob("*") if path.is_file()):
            if (
                asset.name.startswith(".")
                or asset.name == ".DS_Store"
                or asset.suffix.lower() == ".md"
            ):
                continue
            record["supplementary_assets"].append(str(asset.relative_to(doi_dir)))
            suffix = asset.suffix.lower()
            if suffix in {".csv", ".tsv", ".xls", ".xlsx", ".json"}:
                record["structured_table_count"] += 1
            if suffix == ".zip":
                record["archive_bundle_count"] += 1
    payload: dict[str, _ReferenceStashRecord] = {}
    for slug, record in records.items():
        payload[slug] = {
            "stash_slug": slug,
            "article_formats": tuple(sorted(record["article_formats"])),
            "supplementary_assets": tuple(record["supplementary_assets"]),
            "structured_table_count": int(record["structured_table_count"]),
            "archive_bundle_count": int(record["archive_bundle_count"]),
        }
    return payload


@cache
def _reference_stash_records_cached(
    output_root_key: str,
) -> dict[str, _ReferenceStashRecord]:
    return _reference_stash_records_uncached(Path(output_root_key))


def _local_reference_article_status(stash_record: _ReferenceStashRecord) -> str:
    if stash_record.get("article_formats"):
        return "local_reference_staged"
    return "missing"


def _local_reference_supplement_status(stash_record: _ReferenceStashRecord) -> str:
    if stash_record.get("supplementary_assets"):
        return "local_reference_staged"
    return "missing"


def _artifact_id(doi: str, filename: str) -> str:
    return f"{_doi_slug(doi)}:{filename}"
