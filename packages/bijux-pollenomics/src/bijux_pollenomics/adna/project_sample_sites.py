from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess  # nosec B404

from ..core.files import write_json, write_text
from .catalogs import render_csv_rows
from .coordinate_provenance import resolve_project_coordinate_provenance
from .ena import build_archive_project_catalog
from .sample_master import build_project_sample_master_rows
from .site_evidence import resolve_project_site_evidence

__all__ = [
    "ADNA_LOCALITY_RESOLUTION_STATUSES",
    "AdnaProjectSampleSiteRow",
    "build_project_sample_site_rows",
    "build_project_sample_site_review_rows",
    "build_sample_site_ambiguity_ledger",
    "build_sample_site_manual_curation_queue",
    "materialize_project_sample_site_library",
]

ADNA_LOCALITY_RESOLUTION_STATUSES = (
    "direct_sample_site",
    "sample_group_site",
    "project_level_site_only",
    "named_place_inferred",
    "region_only",
    "unresolved",
)
_SINGLE_COUNTRY_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]+$")


@dataclass(frozen=True)
class AdnaProjectSampleSiteRow:
    species_latin_name: str
    species_common_name: str
    project_accession: str
    repo_stable_sample_id: str
    preferred_sample_label: str
    sample_basis: str
    sample_evidence_status: str
    sample_identity_resolution: str
    sample_ambiguity_note: str
    locality_text: str
    locality_resolution_status: str
    location_evidence_artifact_path: str
    location_evidence_artifact_kind: str
    location_evidence_locator: str
    location_evidence_text: str
    site_name: str
    municipality_name: str
    region_name: str
    country_name: str
    broader_geography: str
    coordinate_basis: str
    coordinate_mapping_posture: str
    coordinate_confidence: str
    chronology_text: str
    review_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "project_accession": self.project_accession,
            "repo_stable_sample_id": self.repo_stable_sample_id,
            "preferred_sample_label": self.preferred_sample_label,
            "sample_basis": self.sample_basis,
            "sample_evidence_status": self.sample_evidence_status,
            "sample_identity_resolution": self.sample_identity_resolution,
            "sample_ambiguity_note": self.sample_ambiguity_note,
            "locality_text": self.locality_text,
            "locality_resolution_status": self.locality_resolution_status,
            "location_evidence_artifact_path": self.location_evidence_artifact_path,
            "location_evidence_artifact_kind": self.location_evidence_artifact_kind,
            "location_evidence_locator": self.location_evidence_locator,
            "location_evidence_text": self.location_evidence_text,
            "site_name": self.site_name,
            "municipality_name": self.municipality_name,
            "region_name": self.region_name,
            "country_name": self.country_name,
            "broader_geography": self.broader_geography,
            "coordinate_basis": self.coordinate_basis,
            "coordinate_mapping_posture": self.coordinate_mapping_posture,
            "coordinate_confidence": self.coordinate_confidence,
            "chronology_text": self.chronology_text,
            "review_note": self.review_note,
        }


def build_project_sample_site_rows(
    output_root: Path,
    project_accession: str,
) -> tuple[AdnaProjectSampleSiteRow, ...]:
    output_root = Path(output_root)
    master_rows = build_project_sample_master_rows(output_root, project_accession)
    site_rows = resolve_project_site_evidence(project_accession)
    site_row = site_rows[0] if site_rows else None
    provenance_rows = resolve_project_coordinate_provenance(project_accession)
    provenance_row = provenance_rows[0] if provenance_rows else None
    hierarchy_profiles = _project_hierarchy_profiles(output_root, project_accession)

    rows: list[AdnaProjectSampleSiteRow] = []
    for master_row in master_rows:
        locality_text = master_row.locality_text.strip()
        chronology_text = master_row.chronology_text.strip()
        if locality_text:
            hierarchy = _resolve_hierarchy(
                hierarchy_profiles=hierarchy_profiles,
                locality_text=locality_text,
                political_entity=master_row.political_entity,
            )
            rows.append(
                AdnaProjectSampleSiteRow(
                    species_latin_name=master_row.species_latin_name,
                    species_common_name=master_row.species_common_name,
                    project_accession=master_row.project_accession,
                    repo_stable_sample_id=master_row.repo_stable_sample_id,
                    preferred_sample_label=master_row.preferred_sample_label,
                    sample_basis=master_row.sample_basis,
                    sample_evidence_status=master_row.sample_evidence_status,
                    sample_identity_resolution=master_row.sample_identity_resolution,
                    sample_ambiguity_note=master_row.sample_ambiguity_note,
                    locality_text=locality_text,
                    locality_resolution_status="direct_sample_site",
                    location_evidence_artifact_path=master_row.sample_lineage_path,
                    location_evidence_artifact_kind=_artifact_kind_from_path(master_row.sample_lineage_path),
                    location_evidence_locator=master_row.sample_lineage_locator,
                    location_evidence_text=master_row.sample_lineage_excerpt,
                    site_name=hierarchy.site_name,
                    municipality_name=hierarchy.municipality_name,
                    region_name=hierarchy.region_name,
                    country_name=hierarchy.country_name,
                    broader_geography=hierarchy.broader_geography,
                    coordinate_basis=(
                        "supplementary_table_coordinates"
                        if master_row.latitude_text and master_row.longitude_text
                        else ""
                        if provenance_row is None
                        else provenance_row.coordinate_basis
                    ),
                    coordinate_mapping_posture=(
                        "mappable_point"
                        if master_row.latitude_text and master_row.longitude_text
                        else ""
                        if provenance_row is None
                        else provenance_row.mapping_posture
                    ),
                    coordinate_confidence=(
                        "exact"
                        if master_row.latitude_text and master_row.longitude_text
                        else ""
                        if provenance_row is None
                        else provenance_row.coordinate_confidence
                    ),
                    chronology_text=chronology_text,
                    review_note="Sample-level locality comes directly from the recovered sample source row.",
                )
            )
            continue

        status = _project_level_locality_status(provenance_row)
        hierarchy = _resolve_hierarchy(
            hierarchy_profiles=hierarchy_profiles,
            locality_text="" if site_row is None else site_row.site_label,
            political_entity="" if site_row is None or site_row.political_entity is None else site_row.political_entity,
        )
        review_note = _review_note_for(status=status, site_row=site_row)
        rows.append(
            AdnaProjectSampleSiteRow(
                species_latin_name=master_row.species_latin_name,
                species_common_name=master_row.species_common_name,
                project_accession=master_row.project_accession,
                repo_stable_sample_id=master_row.repo_stable_sample_id,
                preferred_sample_label=master_row.preferred_sample_label,
                sample_basis=master_row.sample_basis,
                sample_evidence_status=master_row.sample_evidence_status,
                sample_identity_resolution=master_row.sample_identity_resolution,
                sample_ambiguity_note=master_row.sample_ambiguity_note,
                locality_text="" if site_row is None else site_row.site_label,
                locality_resolution_status=status,
                location_evidence_artifact_path="" if site_row is None else site_row.source_artifact_path,
                location_evidence_artifact_kind="" if site_row is None else site_row.source_artifact_kind,
                location_evidence_locator="" if site_row is None else site_row.source_locator,
                location_evidence_text="" if site_row is None else site_row.exact_source_text,
                site_name=hierarchy.site_name,
                municipality_name=hierarchy.municipality_name,
                region_name=hierarchy.region_name,
                country_name=hierarchy.country_name,
                broader_geography=hierarchy.broader_geography,
                coordinate_basis="" if provenance_row is None else provenance_row.coordinate_basis,
                coordinate_mapping_posture="" if provenance_row is None else provenance_row.mapping_posture,
                coordinate_confidence="" if provenance_row is None else provenance_row.coordinate_confidence,
                chronology_text=chronology_text or ("" if site_row is None else site_row.chronology_text),
                review_note=review_note,
            )
        )
    rows.sort(key=lambda row: (row.project_accession, row.repo_stable_sample_id))
    return tuple(rows)


def build_project_sample_site_review_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        sample_site_rows = build_project_sample_site_rows(output_root, project.project_accession)
        counts = _counts_by_status(sample_site_rows)
        lacking_count = (
            counts["project_level_site_only"]
            + counts["region_only"]
            + counts["unresolved"]
        )
        missing_reasons = [
            key for key in ("project_level_site_only", "region_only", "unresolved") if counts[key]
        ]
        rows.append(
            {
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "recovered_sample_row_count": len(sample_site_rows),
                "direct_sample_site_count": counts["direct_sample_site"],
                "sample_group_site_count": counts["sample_group_site"],
                "project_level_site_only_count": counts["project_level_site_only"],
                "named_place_inferred_count": counts["named_place_inferred"],
                "region_only_count": counts["region_only"],
                "unresolved_count": counts["unresolved"],
                "lacking_defensible_site_assignment_count": lacking_count,
                "missing_reasons": missing_reasons,
            }
        )
    return tuple(rows)


def build_sample_site_ambiguity_ledger(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    ambiguous_statuses = {
        "sample_group_site",
        "project_level_site_only",
        "region_only",
        "unresolved",
    }
    for project in build_archive_project_catalog():
        for row in build_project_sample_site_rows(output_root, project.project_accession):
            if row.locality_resolution_status not in ambiguous_statuses:
                continue
            rows.append(
                {
                    "project_accession": row.project_accession,
                    "species_latin_name": row.species_latin_name,
                    "repo_stable_sample_id": row.repo_stable_sample_id,
                    "preferred_sample_label": row.preferred_sample_label,
                    "locality_resolution_status": row.locality_resolution_status,
                    "locality_text": row.locality_text,
                    "review_note": row.review_note,
                    "location_evidence_artifact_path": row.location_evidence_artifact_path,
                    "location_evidence_locator": row.location_evidence_locator,
                }
            )
    return tuple(rows)


def build_sample_site_manual_curation_queue(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    source_root = (
        Path(output_root) / "adna" / "governance" / "source_library" / "projects"
    )
    for project in build_archive_project_catalog():
        dossier_path = source_root / project.project_accession / "intake_dossier.json"
        sample_site_rows = build_project_sample_site_rows(output_root, project.project_accession)
        counts = _counts_by_status(sample_site_rows)
        if not dossier_path.is_file():
            continue
        import json

        dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
        queue_reasons = []
        if counts["project_level_site_only"]:
            queue_reasons.append("project_level_site_only_rows_require_sample_owned_site_extraction")
        if counts["region_only"]:
            queue_reasons.append("region_only_rows_require_finer_location_evidence")
        if counts["unresolved"]:
            queue_reasons.append("recovered_sample_rows_still_lack_any_location_claim")
        if not queue_reasons:
            continue
        rows.append(
            {
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "queued_sample_count": (
                    counts["project_level_site_only"] + counts["region_only"] + counts["unresolved"]
                ),
                "queue_reasons": queue_reasons,
                "sample_site_targets": list(dossier.get("sample_site_targets", [])),
                "expected_supplementary_artifacts": list(
                    dossier.get("expected_supplementary_artifacts", [])
                ),
                "local_artifact_paths": list(dossier.get("local_artifact_paths", [])),
                "recommended_next_surface": _recommended_next_surface(dossier),
            }
        )
    return tuple(rows)


def materialize_project_sample_site_library(output_root: Path) -> None:
    output_root = Path(output_root)
    source_root = output_root / "adna" / "governance" / "source_library"
    source_root.mkdir(parents=True, exist_ok=True)

    review_rows = list(build_project_sample_site_review_rows(output_root))
    ambiguity_rows = list(build_sample_site_ambiguity_ledger(output_root))
    queue_rows = list(build_sample_site_manual_curation_queue(output_root))

    for project in build_archive_project_catalog():
        project_root = source_root / "projects" / project.project_accession
        project_root.mkdir(parents=True, exist_ok=True)
        sample_site_rows = [row.as_dict() for row in build_project_sample_site_rows(output_root, project.project_accession)]
        write_json(
            project_root / "sample_sites.json",
            {
                "schema_version": "animal-project-sample-sites.v1",
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "row_count": len(sample_site_rows),
                "rows": sample_site_rows,
            },
        )
        write_text(
            project_root / "sample_sites.csv",
            render_csv_rows(tuple(sample_site_rows) if sample_site_rows else (_empty_sample_site_row(project),)),
        )

    write_json(
        source_root / "project_sample_site_review.json",
        {
            "schema_version": "animal-project-sample-site-review.v1",
            "rows": review_rows,
        },
    )
    write_text(
        source_root / "project_sample_site_review.csv",
        render_csv_rows(tuple(review_rows)),
    )
    write_json(
        source_root / "sample_site_ambiguity_ledger.json",
        {
            "schema_version": "animal-sample-site-ambiguity-ledger.v1",
            "rows": ambiguity_rows,
        },
    )
    write_text(
        source_root / "sample_site_ambiguity_ledger.md",
        _render_sample_site_ambiguity_markdown(ambiguity_rows),
    )
    write_json(
        source_root / "sample_site_manual_curation_queue.json",
        {
            "schema_version": "animal-sample-site-manual-curation-queue.v1",
            "rows": queue_rows,
        },
    )
    write_text(
        source_root / "sample_site_manual_curation_queue.md",
        _render_sample_site_manual_queue_markdown(queue_rows),
    )


@dataclass(frozen=True)
class _Hierarchy:
    site_name: str
    municipality_name: str
    region_name: str
    country_name: str
    broader_geography: str


def _project_by_accession(project_accession: str) -> object:
    for project in build_archive_project_catalog():
        if project.project_accession == project_accession:
            return project
    raise KeyError(project_accession)


def _artifact_kind_from_path(path: str) -> str:
    if "#Supplementary_Data_" in path:
        return "supplementary_spreadsheet_row"
    if path.endswith(".xlsx"):
        return "supplementary_spreadsheet_row"
    if path.endswith(".pdf"):
        return "supplementary_pdf_text"
    if path.endswith(".html"):
        return "article_or_archive_text"
    return "tracked_source_artifact"


def _project_level_locality_status(provenance_row: object | None) -> str:
    if provenance_row is None:
        return "unresolved"
    if provenance_row.mapping_posture == "refused_region_only":
        return "region_only"
    if provenance_row.coordinate_basis == "named_site_geocoding":
        return "named_place_inferred"
    return "project_level_site_only"


def _review_note_for(*, status: str, site_row: object | None) -> str:
    if status == "project_level_site_only":
        return (
            "Current evidence names only a project-level locality context, not a sample-owned site row."
        )
    if status == "named_place_inferred":
        return (
            "Current evidence names a place that can be resolved, but the mapped point still depends on place-name inference."
        )
    if status == "region_only":
        return (
            "Current evidence stays at region or transect scale and must not masquerade as exact sample-site truth."
        )
    if site_row is None:
        return "No location evidence has been extracted yet for this recovered sample row."
    return "Recovered sample row still lacks a defensible sample-owned site assignment."


def _counts_by_status(rows: tuple[AdnaProjectSampleSiteRow, ...]) -> dict[str, int]:
    counts = {key: 0 for key in ADNA_LOCALITY_RESOLUTION_STATUSES}
    for row in rows:
        counts[row.locality_resolution_status] += 1
    return counts


def _recommended_next_surface(dossier: dict[str, object]) -> str:
    sample_site_targets = [str(item) for item in dossier.get("sample_site_targets", []) if str(item).strip()]
    if sample_site_targets:
        return sample_site_targets[0]
    supplementary = [
        str(item)
        for item in dossier.get("expected_supplementary_artifacts", [])
        if str(item).strip()
    ]
    if supplementary:
        return supplementary[0]
    local_artifacts = [
        str(item) for item in dossier.get("local_artifact_paths", []) if str(item).strip()
    ]
    if local_artifacts:
        return local_artifacts[0]
    return ""


def _empty_sample_site_row(project: object) -> dict[str, object]:
    return {
        "species_latin_name": project.species_latin_name,
        "species_common_name": "",
        "project_accession": project.project_accession,
        "repo_stable_sample_id": "",
        "preferred_sample_label": "",
        "sample_basis": "",
        "sample_evidence_status": "not_yet_recoverable",
        "sample_identity_resolution": "provisional",
        "sample_ambiguity_note": "",
        "locality_text": "",
        "locality_resolution_status": "unresolved",
        "location_evidence_artifact_path": "",
        "location_evidence_artifact_kind": "",
        "location_evidence_locator": "",
        "location_evidence_text": "",
        "site_name": "",
        "municipality_name": "",
        "region_name": "",
        "country_name": "",
        "broader_geography": "",
        "coordinate_basis": "",
        "coordinate_mapping_posture": "",
        "coordinate_confidence": "",
        "chronology_text": "",
        "review_note": "No recovered sample rows are published yet for this project.",
    }


def _render_sample_site_ambiguity_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Sample site ambiguity ledger",
        "",
        f"- Ambiguous or weak site rows: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No weak sample-site rows are currently published.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Sample id | Status | Locality | Note |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['locality_resolution_status']} | {row['locality_text']} | {row['review_note']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_site_manual_queue_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Sample site manual curation queue",
        "",
        f"- Queued projects: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No project currently requires manual sample-site extraction.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Queued sample rows | Recommended next surface | Reasons |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['queued_sample_count']} | "
            f"{row['recommended_next_surface']} | {', '.join(row['queue_reasons'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def _project_hierarchy_profiles(
    output_root: Path,
    project_accession: str,
) -> dict[str, _Hierarchy]:
    if project_accession != "PRJEB36540":
        return {}
    text = _ghostscript_text(
        output_root
        / "adna"
        / "governance"
        / "source_library"
        / "papers"
        / "10.1038-s42003-021-02794-8"
        / "supplementary"
        / "42003_2021_2794_MOESM2_ESM.pdf"
    )
    if not text:
        return {}
    profiles = {
        "Ulucak Höyük": _Hierarchy(
            site_name="Ulucak Höyük",
            municipality_name="Izmir area",
            region_name="West Central Turkey",
            country_name="Turkey",
            broader_geography="Western Anatolia",
        ),
        "Barcın Höyük": _Hierarchy(
            site_name="Barcın Höyük",
            municipality_name="Yenişehir Plain",
            region_name="Bursa Province",
            country_name="Turkey",
            broader_geography="Northwestern Anatolia",
        ),
        "Tepecik-Çiftlik Höyük": _Hierarchy(
            site_name="Tepecik-Çiftlik Höyük",
            municipality_name="Çiftlik district",
            region_name="Niğde Province",
            country_name="Turkey",
            broader_geography="Central Anatolian Plateau",
        ),
        "Tepecik-Çiftlik": _Hierarchy(
            site_name="Tepecik-Çiftlik Höyük",
            municipality_name="Çiftlik district",
            region_name="Niğde Province",
            country_name="Turkey",
            broader_geography="Central Anatolian Plateau",
        ),
        "Barcın": _Hierarchy(
            site_name="Barcın Höyük",
            municipality_name="Yenişehir Plain",
            region_name="Bursa Province",
            country_name="Turkey",
            broader_geography="Northwestern Anatolia",
        ),
    }
    if "Barcın Höyük, a seventh millennium Neolithic site" not in text:
        profiles.pop("Barcın Höyük", None)
        profiles.pop("Barcın", None)
    if "Ulucak Höyük, lies 25 km east of İzmir" not in text:
        profiles.pop("Ulucak Höyük", None)
    if "Tepecik-Çiftlik mound is located in the Çiftlik district of Niğde province" not in text:
        profiles.pop("Tepecik-Çiftlik Höyük", None)
        profiles.pop("Tepecik-Çiftlik", None)
    return profiles


def _resolve_hierarchy(
    *,
    hierarchy_profiles: dict[str, _Hierarchy],
    locality_text: str,
    political_entity: str,
) -> _Hierarchy:
    if locality_text in hierarchy_profiles:
        return hierarchy_profiles[locality_text]
    if locality_text.endswith(" context") and locality_text.removesuffix(" context") in hierarchy_profiles:
        return hierarchy_profiles[locality_text.removesuffix(" context")]
    country_name = political_entity if _SINGLE_COUNTRY_RE.fullmatch(political_entity or "") else ""
    broader_geography = ""
    if political_entity and not country_name:
        broader_geography = political_entity
    elif locality_text and not country_name:
        broader_geography = locality_text
    return _Hierarchy(
        site_name=locality_text,
        municipality_name="",
        region_name="",
        country_name=country_name,
        broader_geography=broader_geography,
    )


def _ghostscript_text(path: Path) -> str:
    if not path.is_file():
        return ""
    gs = shutil.which("gs")
    if gs is None:
        return ""
    pdf_path = path.resolve()
    # Ghostscript is invoked without a shell against one checked-in local PDF path.
    result = subprocess.run(
        [
            gs,
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=txtwrite",
            "-sOutputFile=-",
            str(pdf_path),
        ],
        capture_output=True,
        check=False,
        text=True,
    )  # nosec B603
    if result.returncode != 0:
        return ""
    return result.stdout
