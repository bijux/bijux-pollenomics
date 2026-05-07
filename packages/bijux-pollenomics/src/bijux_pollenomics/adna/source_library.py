from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..core.files import write_json, write_text
from .ena import build_archive_project_catalog
from .paths import ADNA_SOURCE_LIBRARY_DIR, adna_source_library_root

__all__ = [
    "AdnaPaperRegistryRow",
    "AdnaProjectRegistryRow",
    "AdnaSourceArtifact",
    "AdnaSourceBundleManifest",
    "AdnaSupplementRegistryRow",
    "build_cross_project_source_audit",
    "build_missing_source_blockers",
    "build_paper_registry",
    "build_project_source_bundles",
    "build_source_artifact_index",
    "build_supplement_registry",
    "materialize_source_library",
    "refresh_source_library",
]


@dataclass(frozen=True)
class AdnaSourceArtifact:
    """One tracked source artifact backing a paper, supplement, or metadata claim."""

    artifact_id: str
    artifact_kind: str
    label: str
    source_url: str
    local_path: str
    fetch_status: str
    remote_note: str
    project_accessions: tuple[str, ...]
    paper_doi: str | None = None
    content_type: str | None = None
    byte_size: int | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_kind": self.artifact_kind,
            "label": self.label,
            "source_url": self.source_url,
            "local_path": self.local_path,
            "fetch_status": self.fetch_status,
            "remote_note": self.remote_note,
            "project_accessions": list(self.project_accessions),
            "paper_doi": self.paper_doi,
            "content_type": self.content_type,
            "byte_size": self.byte_size,
        }


@dataclass(frozen=True)
class AdnaProjectRegistryRow:
    """Cross-species registry row for one tracked animal aDNA project or accession."""

    species_latin_name: str
    project_accession: str
    source_family: str
    archive_status: str
    evidence_strength: str
    accession_scope: str
    project_url: str
    primary_paper_doi: str | None
    primary_paper_url: str | None
    source_bundle_path: str
    paper_download_status: str
    supplement_download_status: str
    ingestion_status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "project_accession": self.project_accession,
            "source_family": self.source_family,
            "archive_status": self.archive_status,
            "evidence_strength": self.evidence_strength,
            "accession_scope": self.accession_scope,
            "project_url": self.project_url,
            "primary_paper_doi": self.primary_paper_doi,
            "primary_paper_url": self.primary_paper_url,
            "source_bundle_path": self.source_bundle_path,
            "paper_download_status": self.paper_download_status,
            "supplement_download_status": self.supplement_download_status,
            "ingestion_status": self.ingestion_status,
        }


@dataclass(frozen=True)
class AdnaPaperRegistryRow:
    """Unique paper registry row across the tracked animal aDNA program."""

    paper_doi: str
    canonical_url: str
    article_source_url: str
    journal: str | None
    publication_year: int | None
    title: str
    species_latin_names: tuple[str, ...]
    project_accessions: tuple[str, ...]
    article_download_status: str
    article_local_path: str
    supplementary_download_status: str
    supplementary_count: int
    parsing_status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "paper_doi": self.paper_doi,
            "canonical_url": self.canonical_url,
            "article_source_url": self.article_source_url,
            "journal": self.journal,
            "publication_year": self.publication_year,
            "title": self.title,
            "species_latin_names": list(self.species_latin_names),
            "project_accessions": list(self.project_accessions),
            "article_download_status": self.article_download_status,
            "article_local_path": self.article_local_path,
            "supplementary_download_status": self.supplementary_download_status,
            "supplementary_count": self.supplementary_count,
            "parsing_status": self.parsing_status,
        }


@dataclass(frozen=True)
class AdnaSupplementRegistryRow:
    """Tracked supplementary-material registry row for one supporting artifact."""

    artifact_id: str
    paper_doi: str
    source_url: str
    local_path: str
    artifact_kind: str
    fetch_status: str
    project_accessions: tuple[str, ...]
    purpose: str

    def as_dict(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "paper_doi": self.paper_doi,
            "source_url": self.source_url,
            "local_path": self.local_path,
            "artifact_kind": self.artifact_kind,
            "fetch_status": self.fetch_status,
            "project_accessions": list(self.project_accessions),
            "purpose": self.purpose,
        }


@dataclass(frozen=True)
class AdnaSourceBundleManifest:
    """Per-project manifest tying archive, paper, and supplementary assets together."""

    project_accession: str
    species_latin_name: str
    archive_status: str
    evidence_strength: str
    project_url: str
    paper_doi: str | None
    paper_title: str | None
    archive_metadata_sufficient: bool
    paper_required: bool
    supplement_required: bool
    paper_download_status: str
    supplement_download_status: str
    local_artifact_ids: tuple[str, ...]
    local_artifact_paths: tuple[str, ...]
    blockers: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "species_latin_name": self.species_latin_name,
            "archive_status": self.archive_status,
            "evidence_strength": self.evidence_strength,
            "project_url": self.project_url,
            "paper_doi": self.paper_doi,
            "paper_title": self.paper_title,
            "archive_metadata_sufficient": self.archive_metadata_sufficient,
            "paper_required": self.paper_required,
            "supplement_required": self.supplement_required,
            "paper_download_status": self.paper_download_status,
            "supplement_download_status": self.supplement_download_status,
            "local_artifact_ids": list(self.local_artifact_ids),
            "local_artifact_paths": list(self.local_artifact_paths),
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class _RemoteArtifactSpec:
    artifact_kind: str
    label: str
    source_url: str
    relative_path: str
    remote_note: str


@dataclass(frozen=True)
class _PaperSourceSpec:
    doi: str
    article_source_url: str
    article_local_path: str
    article_kind: str
    article_note: str
    supplementary_assets: tuple[_RemoteArtifactSpec, ...] = ()
    parsing_status: str = "ready_for_project_sample_extraction"
    registry_note: str = ""


SOURCE_LIBRARY_SCHEMA_VERSION = "adna-source-library.v1"
_USER_AGENT = "Mozilla/5.0 (compatible; bijux-pollenomics/1.0)"
_NATURE_DOI_RE = re.compile(r"https?://www\.nature\.com/articles/(?P<slug>[A-Za-z0-9_.-]+)")


def build_source_artifact_index(output_root: Path) -> tuple[AdnaSourceArtifact, ...]:
    """Return the tracked source artifact index from the local archive tree."""
    output_root = Path(output_root)
    rows: list[AdnaSourceArtifact] = []
    for artifact in _iter_materialized_artifacts(output_root):
        rows.append(artifact)
    return tuple(sorted(rows, key=lambda item: (item.paper_doi or "", item.artifact_id)))


def build_project_source_bundles(output_root: Path) -> tuple[AdnaSourceBundleManifest, ...]:
    """Return one per-project manifest describing local paper and supplement support."""
    output_root = Path(output_root)
    artifacts_by_project: dict[str, list[AdnaSourceArtifact]] = {}
    for artifact in _iter_materialized_artifacts(output_root):
        for accession in artifact.project_accessions:
            artifacts_by_project.setdefault(accession, []).append(artifact)

    bundles: list[AdnaSourceBundleManifest] = []
    for project in build_archive_project_catalog():
        project_artifacts = tuple(
            sorted(
                artifacts_by_project.get(project.project_accession, ()),
                key=lambda item: item.artifact_id,
            )
        )
        local_project_artifacts = tuple(
            item for item in project_artifacts if item.fetch_status == "archived"
        )
        paper_artifacts = tuple(
            item
            for item in local_project_artifacts
            if item.artifact_kind in {"article_html", "article_pdf", "paper_metadata_json"}
        )
        supplement_artifacts = tuple(
            item
            for item in local_project_artifacts
            if item.artifact_kind.startswith("supplementary_")
        )
        paper_required = _paper_required(project.archive_status)
        supplement_required = _supplement_required(project)
        blockers = []
        if paper_required and not paper_artifacts:
            blockers.append("missing_local_paper_evidence")
        if supplement_required and not supplement_artifacts:
            blockers.append("missing_local_supplementary_material")
        if project.paper_linkage is None:
            blockers.append("paper_linkage_not_curated")
        bundles.append(
            AdnaSourceBundleManifest(
                project_accession=project.project_accession,
                species_latin_name=project.species_latin_name,
                archive_status=project.archive_status,
                evidence_strength=project.as_dict()["evidence_strength"],
                project_url=project.metadata_url,
                paper_doi=None if project.paper_linkage is None else project.paper_linkage.doi,
                paper_title=(
                    None if project.paper_linkage is None else project.paper_linkage.paper_title
                ),
                archive_metadata_sufficient=not paper_required,
                paper_required=paper_required,
                supplement_required=supplement_required,
                paper_download_status=_fold_fetch_status(paper_artifacts),
                supplement_download_status=_fold_fetch_status(supplement_artifacts),
                local_artifact_ids=tuple(item.artifact_id for item in local_project_artifacts),
                local_artifact_paths=tuple(item.local_path for item in local_project_artifacts),
                blockers=tuple(blockers),
            )
        )
    return tuple(sorted(bundles, key=lambda item: item.project_accession))


def build_project_registry(output_root: Path) -> tuple[AdnaProjectRegistryRow, ...]:
    """Return the master cross-species project registry."""
    output_root = Path(output_root)
    bundles = {bundle.project_accession: bundle for bundle in build_project_source_bundles(output_root)}
    rows: list[AdnaProjectRegistryRow] = []
    for project in build_archive_project_catalog():
        bundle = bundles[project.project_accession]
        paper_url = None
        if project.paper_linkage is not None and project.paper_linkage.doi is not None:
            paper_url = f"https://doi.org/{project.paper_linkage.doi}"
        rows.append(
            AdnaProjectRegistryRow(
                species_latin_name=project.species_latin_name,
                project_accession=project.project_accession,
                source_family=project.source_family,
                archive_status=project.archive_status,
                evidence_strength=project.as_dict()["evidence_strength"],
                accession_scope=project.accession_scope,
                project_url=project.metadata_url,
                primary_paper_doi=None if project.paper_linkage is None else project.paper_linkage.doi,
                primary_paper_url=paper_url,
                source_bundle_path=(
                    f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project.project_accession}/bundle_manifest.json"
                ),
                paper_download_status=bundle.paper_download_status,
                supplement_download_status=bundle.supplement_download_status,
                ingestion_status=_derive_ingestion_status(bundle),
            )
        )
    return tuple(sorted(rows, key=lambda item: (item.species_latin_name, item.project_accession)))


def build_paper_registry(output_root: Path) -> tuple[AdnaPaperRegistryRow, ...]:
    """Return the master unique-paper registry."""
    output_root = Path(output_root)
    artifacts = build_source_artifact_index(output_root)
    artifacts_by_doi: dict[str, list[AdnaSourceArtifact]] = {}
    projects_by_doi: dict[str, list[object]] = {}
    for project in build_archive_project_catalog():
        if project.paper_linkage is None or project.paper_linkage.doi is None:
            continue
        projects_by_doi.setdefault(project.paper_linkage.doi, []).append(project)
    for artifact in artifacts:
        if artifact.paper_doi is None:
            continue
        artifacts_by_doi.setdefault(artifact.paper_doi, []).append(artifact)

    rows: list[AdnaPaperRegistryRow] = []
    for doi, projects in sorted(projects_by_doi.items()):
        first = projects[0]
        linkage = first.paper_linkage
        assert linkage is not None
        doi_artifacts = tuple(artifacts_by_doi.get(doi, ()))
        article_artifacts = tuple(
            item for item in doi_artifacts if item.artifact_kind in {"article_html", "article_pdf", "paper_metadata_json"}
        )
        supplement_artifacts = tuple(
            item for item in doi_artifacts if item.artifact_kind.startswith("supplementary_")
        )
        rows.append(
            AdnaPaperRegistryRow(
                paper_doi=doi,
                canonical_url=f"https://doi.org/{doi}",
                article_source_url=_paper_source_spec(doi).article_source_url,
                journal=linkage.journal_title,
                publication_year=linkage.publication_year,
                title=linkage.paper_title,
                species_latin_names=tuple(
                    sorted({project.species_latin_name for project in projects})
                ),
                project_accessions=tuple(sorted(project.project_accession for project in projects)),
                article_download_status=_fold_fetch_status(article_artifacts),
                article_local_path=_paper_source_spec(doi).article_local_path,
                supplementary_download_status=_fold_fetch_status(supplement_artifacts),
                supplementary_count=len(supplement_artifacts),
                parsing_status=_paper_source_spec(doi).parsing_status,
            )
        )
    return tuple(rows)


def build_supplement_registry(output_root: Path) -> tuple[AdnaSupplementRegistryRow, ...]:
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


def build_cross_project_source_audit(output_root: Path) -> dict[str, object]:
    """Summarize how much of the tracked program is archive-sufficient versus paper-dependent."""
    bundles = build_project_source_bundles(output_root)
    summary = {
        "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
        "archive_sufficient_count": 0,
        "paper_dependent_count": 0,
        "supplement_dependent_count": 0,
        "blocked_count": 0,
        "rows": [],
    }
    for bundle in bundles:
        if bundle.archive_metadata_sufficient:
            summary["archive_sufficient_count"] += 1
        else:
            summary["paper_dependent_count"] += 1
        if bundle.supplement_required:
            summary["supplement_dependent_count"] += 1
        if bundle.blockers:
            summary["blocked_count"] += 1
        summary["rows"].append(
            {
                "project_accession": bundle.project_accession,
                "species_latin_name": bundle.species_latin_name,
                "archive_status": bundle.archive_status,
                "archive_metadata_sufficient": bundle.archive_metadata_sufficient,
                "paper_required": bundle.paper_required,
                "supplement_required": bundle.supplement_required,
                "paper_download_status": bundle.paper_download_status,
                "supplement_download_status": bundle.supplement_download_status,
                "blockers": list(bundle.blockers),
            }
        )
    return summary


def build_missing_source_blockers(output_root: Path) -> dict[str, object]:
    """Return the explicit blocker ledger for paper and supplementary archive gaps."""
    rows = []
    for bundle in build_project_source_bundles(output_root):
        if not bundle.blockers:
            continue
        rows.append(
            {
                "project_accession": bundle.project_accession,
                "species_latin_name": bundle.species_latin_name,
                "paper_doi": bundle.paper_doi,
                "paper_title": bundle.paper_title,
                "archive_status": bundle.archive_status,
                "paper_download_status": bundle.paper_download_status,
                "supplement_download_status": bundle.supplement_download_status,
                "blockers": list(bundle.blockers),
            }
        )
    return {"schema_version": SOURCE_LIBRARY_SCHEMA_VERSION, "rows": rows}


def refresh_source_library(
    output_root: Path,
    *,
    downloader: Callable[[str], tuple[bytes, str]] | None = None,
) -> None:
    """Download or refresh local paper and supplementary artifacts."""
    output_root = Path(output_root)
    downloader = _download_url if downloader is None else downloader
    source_root = adna_source_library_root(output_root)
    source_root.mkdir(parents=True, exist_ok=True)

    for project in build_archive_project_catalog():
        project_dir = source_root / "projects" / project.project_accession
        project_dir.mkdir(parents=True, exist_ok=True)
        try:
            payload, content_type = downloader(project.metadata_url)
        except (HTTPError, URLError, TimeoutError, ValueError):
            pass
        else:
            archive_path = project_dir / "archive_metadata.html"
            archive_path.write_bytes(payload)
            write_json(
                archive_path.with_suffix(archive_path.suffix + ".metadata.json"),
                {
                    "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
                    "source_url": project.metadata_url,
                    "artifact_kind": "archive_metadata_html",
                    "content_type": content_type,
                    "byte_size": len(payload),
                    "project_accession": project.project_accession,
                },
            )

    for doi, spec in _paper_source_specs().items():
        for asset in _expand_remote_assets(spec, build_archive_project_catalog()):
            local_path = source_root / asset.relative_path
            local_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                payload, content_type = downloader(asset.source_url)
            except (HTTPError, URLError, TimeoutError, ValueError):
                continue
            local_path.write_bytes(payload)
            metadata = {
                "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
                "source_url": asset.source_url,
                "artifact_kind": asset.artifact_kind,
                "content_type": content_type,
                "byte_size": len(payload),
                "paper_doi": doi,
            }
            write_json(local_path.with_suffix(local_path.suffix + ".metadata.json"), metadata)


def materialize_source_library(output_root: Path) -> None:
    """Write registries, per-project manifests, and curation notes for the local source library."""
    output_root = Path(output_root)
    source_root = adna_source_library_root(output_root)
    source_root.mkdir(parents=True, exist_ok=True)

    project_registry = build_project_registry(output_root)
    paper_registry = build_paper_registry(output_root)
    supplement_registry = build_supplement_registry(output_root)
    source_audit = build_cross_project_source_audit(output_root)
    blockers = build_missing_source_blockers(output_root)

    write_json(
        source_root / "project_registry.json",
        {"schema_version": SOURCE_LIBRARY_SCHEMA_VERSION, "rows": [row.as_dict() for row in project_registry]},
    )
    write_text(source_root / "project_registry.csv", _render_csv([row.as_dict() for row in project_registry]))
    write_json(
        source_root / "paper_registry.json",
        {"schema_version": SOURCE_LIBRARY_SCHEMA_VERSION, "rows": [row.as_dict() for row in paper_registry]},
    )
    write_text(source_root / "paper_registry.csv", _render_csv([row.as_dict() for row in paper_registry]))
    write_json(
        source_root / "supplement_registry.json",
        {"schema_version": SOURCE_LIBRARY_SCHEMA_VERSION, "rows": [row.as_dict() for row in supplement_registry]},
    )
    write_text(source_root / "supplement_registry.csv", _render_csv([row.as_dict() for row in supplement_registry]))
    write_json(source_root / "source_audit.json", source_audit)
    write_json(source_root / "source_blockers.json", blockers)

    bundles = build_project_source_bundles(output_root)
    for bundle in bundles:
        project_dir = source_root / "projects" / bundle.project_accession
        project_dir.mkdir(parents=True, exist_ok=True)
        write_json(project_dir / "bundle_manifest.json", bundle.as_dict())
        write_text(project_dir / "curation_note.md", _render_curation_note(bundle))


def _render_curation_note(bundle: AdnaSourceBundleManifest) -> str:
    requirement = (
        "Paper and supplementary materials are required to recover sample and site detail."
        if bundle.paper_required and bundle.supplement_required
        else (
            "Paper-level evidence is required for this project, but no supplementary artifact is currently curated."
            if bundle.paper_required
            else "Archive metadata is sufficient for the current curation posture."
        )
    )
    blockers = (
        "\n".join(f"- `{item}`" for item in bundle.blockers)
        if bundle.blockers
        else "- none"
    )
    return (
        f"# {bundle.project_accession}\n\n"
        f"- Species: `{bundle.species_latin_name}`\n"
        f"- Archive status: `{bundle.archive_status}`\n"
        f"- Evidence strength: `{bundle.evidence_strength}`\n"
        f"- Project URL: {bundle.project_url}\n"
        f"- Paper DOI: `{bundle.paper_doi or 'none'}`\n"
        f"- Paper download status: `{bundle.paper_download_status}`\n"
        f"- Supplement download status: `{bundle.supplement_download_status}`\n\n"
        f"{requirement}\n\n"
        "## Local artifacts\n\n"
        + ("\n".join(f"- `{path}`" for path in bundle.local_artifact_paths) or "- none")
        + "\n\n## Blockers\n\n"
        + blockers
        + "\n"
    )


def _iter_materialized_artifacts(output_root: Path) -> tuple[AdnaSourceArtifact, ...]:
    source_root = adna_source_library_root(Path(output_root))
    rows: list[AdnaSourceArtifact] = []
    catalog = build_archive_project_catalog()
    for project in catalog:
        local_path = source_root / "projects" / project.project_accession / "archive_metadata.html"
        metadata_path = local_path.with_suffix(local_path.suffix + ".metadata.json")
        fetch_status = "missing"
        content_type = None
        byte_size = None
        if metadata_path.is_file():
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            fetch_status = "archived"
            content_type = payload.get("content_type")
            byte_size = payload.get("byte_size")
        elif local_path.is_file():
            fetch_status = "archived"
            byte_size = local_path.stat().st_size
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
                paper_doi=None if project.paper_linkage is None else project.paper_linkage.doi,
                content_type=content_type,
                byte_size=byte_size,
            )
        )
    for doi, spec in _paper_source_specs().items():
        projects = tuple(
            sorted(
                project.project_accession
                for project in catalog
                if project.paper_linkage is not None and project.paper_linkage.doi == doi
            )
        )
        for remote in _expand_remote_assets(spec, catalog):
            local_path = source_root / remote.relative_path
            metadata_path = local_path.with_suffix(local_path.suffix + ".metadata.json")
            fetch_status = "missing"
            content_type = None
            byte_size = None
            if metadata_path.is_file():
                payload = json.loads(metadata_path.read_text(encoding="utf-8"))
                fetch_status = "archived"
                content_type = payload.get("content_type")
                byte_size = payload.get("byte_size")
            elif local_path.is_file():
                fetch_status = "archived"
                byte_size = local_path.stat().st_size
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
                )
            )
    return tuple(rows)


def _paper_source_specs() -> dict[str, _PaperSourceSpec]:
    return {
        "10.1038/s42003-021-02794-8": _PaperSourceSpec(
            doi="10.1038/s42003-021-02794-8",
            article_source_url="https://www.nature.com/articles/s42003-021-02794-8",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s42003-021-02794-8/article.pdf",
            article_kind="article_pdf",
            article_note="Nature article PDF is directly downloadable and anchors sheep project metadata plus supplementary sample tables.",
            supplementary_assets=(
                _RemoteArtifactSpec(
                    artifact_kind="supplementary_pdf",
                    label="supplementary note 1",
                    source_url="https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02794-8/MediaObjects/42003_2021_2794_MOESM1_ESM.pdf",
                    relative_path="papers/10.1038-s42003-021-02794-8/supplementary/42003_2021_2794_MOESM1_ESM.pdf",
                    remote_note="Nature supplementary PDF discovered from article page.",
                ),
                _RemoteArtifactSpec(
                    artifact_kind="supplementary_pdf",
                    label="supplementary note 2",
                    source_url="https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02794-8/MediaObjects/42003_2021_2794_MOESM2_ESM.pdf",
                    relative_path="papers/10.1038-s42003-021-02794-8/supplementary/42003_2021_2794_MOESM2_ESM.pdf",
                    remote_note="Nature supplementary PDF discovered from article page.",
                ),
                _RemoteArtifactSpec(
                    artifact_kind="supplementary_pdf",
                    label="supplementary note 3",
                    source_url="https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02794-8/MediaObjects/42003_2021_2794_MOESM3_ESM.pdf",
                    relative_path="papers/10.1038-s42003-021-02794-8/supplementary/42003_2021_2794_MOESM3_ESM.pdf",
                    remote_note="Nature supplementary PDF discovered from article page.",
                ),
                _RemoteArtifactSpec(
                    artifact_kind="supplementary_zip",
                    label="supplementary data zip",
                    source_url="https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02794-8/MediaObjects/42003_2021_2794_MOESM4_ESM.zip",
                    relative_path="papers/10.1038-s42003-021-02794-8/supplementary/42003_2021_2794_MOESM4_ESM.zip",
                    remote_note="Nature supplementary data bundle discovered from article page.",
                ),
                _RemoteArtifactSpec(
                    artifact_kind="supplementary_pdf",
                    label="supplementary note 5",
                    source_url="https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-021-02794-8/MediaObjects/42003_2021_2794_MOESM5_ESM.pdf",
                    relative_path="papers/10.1038-s42003-021-02794-8/supplementary/42003_2021_2794_MOESM5_ESM.pdf",
                    remote_note="Nature supplementary PDF discovered from article page.",
                ),
            ),
        ),
        "10.1038/s41562-021-01083-y": _PaperSourceSpec(
            doi="10.1038/s41562-021-01083-y",
            article_source_url="https://www.nature.com/articles/s41562-021-01083-y",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41562-021-01083-y/article.html",
            article_kind="article_html",
            article_note="Nature Human Behaviour article page is archived as the accessible paper surface.",
        ),
        "10.1038/s41586-021-04018-9": _PaperSourceSpec(
            doi="10.1038/s41586-021-04018-9",
            article_source_url="https://www.nature.com/articles/s41586-021-04018-9",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41586-021-04018-9/article.html",
            article_kind="article_html",
            article_note="Nature article page is archived because direct PDF automation is inconsistent.",
        ),
        "10.1038/s41586-024-08112-6": _PaperSourceSpec(
            doi="10.1038/s41586-024-08112-6",
            article_source_url="https://www.nature.com/articles/s41586-024-08112-6",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41586-024-08112-6/article.html",
            article_kind="article_html",
            article_note="Nature article page is archived as the accessible paper surface.",
        ),
        "10.1038/s41598-024-54296-2": _PaperSourceSpec(
            doi="10.1038/s41598-024-54296-2",
            article_source_url="https://www.nature.com/articles/s41598-024-54296-2",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41598-024-54296-2/article.html",
            article_kind="article_html",
            article_note="Scientific Reports article page is archived as the accessible paper surface.",
        ),
        "10.1038/ncomms16082": _PaperSourceSpec(
            doi="10.1038/ncomms16082",
            article_source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5520058/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-ncomms16082/article.html",
            article_kind="article_html",
            article_note="PMC full-text HTML is archived for the dog paper.",
        ),
        "10.1093/gbe/evae114": _PaperSourceSpec(
            doi="10.1093/gbe/evae114",
            article_source_url="https://academic.oup.com/gbe/article/doi/10.1093/gbe/evae114/7682331",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1093-gbe-evae114/article.html",
            article_kind="article_html",
            article_note="Publisher article page is archived where accessible; OUP bot protection can still block richer downloads.",
        ),
        "10.1093/gbe/evaf181": _PaperSourceSpec(
            doi="10.1093/gbe/evaf181",
            article_source_url="https://academic.oup.com/gbe/article/doi/10.1093/gbe/evaf181/8317779",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1093-gbe-evaf181/article.html",
            article_kind="article_html",
            article_note="Publisher article page is archived where accessible; OUP bot protection can still block richer downloads.",
        ),
        "10.1111/1755-0998.12551": _PaperSourceSpec(
            doi="10.1111/1755-0998.12551",
            article_source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5324683/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1111-1755-0998.12551/article.html",
            article_kind="article_html",
            article_note="PMC full-text HTML is archived for the camel paper.",
        ),
        "10.1126/science.aam5298": _PaperSourceSpec(
            doi="10.1126/science.aam5298",
            article_source_url="https://pubmed.ncbi.nlm.nih.gov/28450643/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.aam5298/article.html",
            article_kind="article_html",
            article_note="PubMed landing page is archived because publisher automation is blocked.",
            parsing_status="full_paper_download_blocked",
        ),
        "10.1126/science.aao3297": _PaperSourceSpec(
            doi="10.1126/science.aao3297",
            article_source_url="https://pubmed.ncbi.nlm.nih.gov/29472442/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.aao3297/article.html",
            article_kind="article_html",
            article_note="PubMed landing page is archived because publisher automation is blocked.",
            parsing_status="full_paper_download_blocked",
        ),
        "10.1126/science.aav1002": _PaperSourceSpec(
            doi="10.1126/science.aav1002",
            article_source_url="https://pubmed.ncbi.nlm.nih.gov/31296769/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.aav1002/article.html",
            article_kind="article_html",
            article_note="PubMed landing page is archived because publisher automation is blocked.",
            parsing_status="full_paper_download_blocked",
        ),
        "10.1126/science.adt2642": _PaperSourceSpec(
            doi="10.1126/science.adt2642",
            article_source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC7618505/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.adt2642/article.html",
            article_kind="article_html",
            article_note="PMC full-text HTML is archived for the cat dispersal paper.",
        ),
        "10.1073/pnas.1901169116": _PaperSourceSpec(
            doi="10.1073/pnas.1901169116",
            article_source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6717267/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1073-pnas.1901169116/article.html",
            article_kind="article_html",
            article_note="PMC full-text HTML is archived for the pig turnover paper.",
        ),
        "10.1016/j.cell.2019.03.049": _PaperSourceSpec(
            doi="10.1016/j.cell.2019.03.049",
            article_source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6547883/",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.cell.2019.03.049/article.html",
            article_kind="article_html",
            article_note="PMC full-text HTML is archived for the horse time-series paper.",
        ),
        "10.1016/j.isci.2025.113771": _PaperSourceSpec(
            doi="10.1016/j.isci.2025.113771",
            article_source_url="https://linkinghub.elsevier.com/retrieve/pii/S2589004225020322",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.isci.2025.113771/article.html",
            article_kind="article_html",
            article_note="Elsevier article landing page is archived as the accessible paper surface.",
        ),
        "10.1016/j.xgen.2025.101099": _PaperSourceSpec(
            doi="10.1016/j.xgen.2025.101099",
            article_source_url="https://linkinghub.elsevier.com/retrieve/pii/S2666979X25003556",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.xgen.2025.101099/article.html",
            article_kind="article_html",
            article_note="Elsevier article landing page is archived as the accessible paper surface.",
        ),
        "10.24272/j.issn.2095-8137.2025.080": _PaperSourceSpec(
            doi="10.24272/j.issn.2095-8137.2025.080",
            article_source_url="https://www.zoores.ac.cn/en/article/doi/10.24272/j.issn.2095-8137.2025.080",
            article_local_path=f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.24272-j.issn.2095-8137.2025.080/article.html",
            article_kind="article_html",
            article_note="Publisher article page is archived for the goat paper.",
        ),
    }


def _paper_source_spec(doi: str) -> _PaperSourceSpec:
    try:
        return _paper_source_specs()[doi]
    except KeyError as exc:
        raise KeyError(f"Missing paper source spec for DOI: {doi}") from exc


def _expand_remote_assets(
    spec: _PaperSourceSpec,
    catalog: tuple[object, ...],
) -> tuple[_RemoteArtifactSpec, ...]:
    article_relative = spec.article_local_path.split(f"{ADNA_SOURCE_LIBRARY_DIR}/", 1)[1]
    assets = [
        _RemoteArtifactSpec(
            artifact_kind=spec.article_kind,
            label="article source",
            source_url=spec.article_source_url,
            relative_path=article_relative,
            remote_note=spec.article_note,
        ),
        _RemoteArtifactSpec(
            artifact_kind="paper_metadata_json",
            label="crossref metadata",
            source_url=f"https://api.crossref.org/works/{spec.doi}",
            relative_path=f"papers/{_doi_slug(spec.doi)}/crossref.json",
            remote_note="Crossref metadata snapshot preserves DOI and title even when publisher downloads are blocked.",
        ),
    ]
    project = next(
        (
            item
            for item in catalog
            if item.paper_linkage is not None and item.paper_linkage.doi == spec.doi and item.paper_linkage.pubmed_id is not None
        ),
        None,
    )
    if project is not None:
        assets.append(
            _RemoteArtifactSpec(
                artifact_kind="paper_metadata_json",
                label="pubmed abstract",
                source_url=(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                    f"?db=pubmed&id={project.paper_linkage.pubmed_id}&retmode=xml"
                ),
                relative_path=f"papers/{_doi_slug(spec.doi)}/pubmed.xml",
                remote_note="PubMed XML snapshot provides publisher-independent citation and abstract metadata.",
            )
        )
    assets.extend(spec.supplementary_assets)
    return tuple(assets)


def _paper_required(archive_status: str) -> bool:
    return archive_status in {"paper_pinned_core", "archive_verified_needs_paper_pinning", "comparator_only"}


def _supplement_required(project: object) -> bool:
    if project.paper_linkage is None or project.paper_linkage.doi is None:
        return False
    return bool(_paper_source_spec(project.paper_linkage.doi).supplementary_assets)


def _derive_ingestion_status(bundle: AdnaSourceBundleManifest) -> str:
    if bundle.blockers:
        return "blocked"
    if bundle.supplement_required:
        return "paper_and_supplement_archived"
    if bundle.paper_required:
        return "paper_source_archived"
    return "archive_metadata_sufficient"


def _fold_fetch_status(artifacts: tuple[AdnaSourceArtifact, ...]) -> str:
    if not artifacts:
        return "missing"
    statuses = {item.fetch_status for item in artifacts}
    if statuses == {"archived"}:
        return "archived"
    if "archived" in statuses:
        return "partial"
    return "missing"


def _artifact_id(doi: str, filename: str) -> str:
    return f"{_doi_slug(doi)}:{filename}"


def _doi_slug(doi: str) -> str:
    return doi.lower().replace("/", "-")


def _render_csv(rows: list[dict[str, object]]) -> str:
    if not rows:
        return ""
    headers = tuple(rows[0].keys())
    lines = [",".join(headers)]
    for row in rows:
        rendered = []
        for key in headers:
            value = row[key]
            if isinstance(value, list):
                text = ";".join(str(item) for item in value)
            else:
                text = "" if value is None else str(value)
            if any(token in text for token in [",", "\"", "\n"]):
                text = '"' + text.replace('"', '""') + '"'
            rendered.append(text)
        lines.append(",".join(rendered))
    return "\n".join(lines) + "\n"


def _download_url(url: str) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": _USER_AGENT})
    with urlopen(request, timeout=60) as response:
        payload = response.read()
        content_type = response.headers.get("Content-Type", "application/octet-stream")
    return payload, content_type
