"""Imputation-study goat sample projection."""

from __future__ import annotations

import csv
from dataclasses import replace
from hashlib import sha256
import io
import json
from typing import Any

from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition

from ..identity import (
    _cell_value,
    _clean_coordinate_text,
    _clean_sample_chronology_text,
    _first_accession,
    _join_distinct,
    _taxon_alignment_status,
)
from ..models import AdnaProjectSampleMasterRow

GOAT_NATIVE_CONTEXT = (
    "data/adna/governance/source_library/projects/PRJEB90141/native_sample_context.json"
)
_NATIVE_CONTEXT_SHA256 = (
    "05e596fda368e6eee16d6f1b68ec249324b697341ee1645fe7f1f9193c5098a7"
)
_NATIVE_WORKBOOK_SHA256 = (
    "da5eeb7f8f63110b572621df8d66fa06ffbaa2291df018a01656c93350f5010f"
)


def _build_goat_imputation_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 2:
        return ()
    headers = rows[0]
    header_map = {
        value.strip(): index for index, value in enumerate(headers) if value.strip()
    }
    sample_index = header_map.get("Sample")
    locality_index = header_map.get("Site")
    country_index = header_map.get("Geographic Origin")
    latitude_index = header_map.get("Latitude")
    longitude_index = header_map.get("Longitude")
    chronology_index = header_map.get("C14 range, 2σ calibrated")
    accession_index = header_map.get("Accession")
    if sample_index is None or locality_index is None or chronology_index is None:
        return ()

    built_rows: list[AdnaProjectSampleMasterRow] = []
    for row_number, row in enumerate(rows[1:], start=2):
        sample_label = _cell_value(row, sample_index)
        chronology_text = (
            ""
            if chronology_index is None
            else _clean_sample_chronology_text(_cell_value(row, chronology_index))
        )
        if not sample_label or not chronology_text:
            continue
        archive_accession = (
            ""
            if accession_index is None
            else _first_accession(_cell_value(row, accession_index))
        )
        accession_literal = (
            ""
            if accession_index is None or accession_index >= len(row)
            else row[accession_index]
        )
        excerpt = " | ".join(value for value in row if value)[:300]
        built_rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=f"{project.project_accession}:{archive_accession or sample_label}".casefold(),
                archive_native_sample_id=archive_accession,
                paper_native_sample_label=sample_label,
                supplementary_table_sample_label=sample_label,
                preferred_sample_label=sample_label,
                sample_basis="supplementary_table_sample_label_anchor",
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=source_path,
                sample_lineage_locator=f"Table S2 downsampled samples!row{row_number}",
                sample_lineage_excerpt=excerpt,
                sample_identity_resolution="ambiguous",
                sample_ambiguity_note=(
                    f"Table S2 Accession cell (literal): {accession_literal!r}. "
                    "The recorded archive ID and existing stable key are retained "
                    "for trace only; neither selects a unique biological specimen "
                    "nor establishes ownership by the configured project. "
                    "Project membership and accession-to-specimen binding remain "
                    "unqualified."
                ),
                locality_text=_cell_value(row, locality_index),
                political_entity=""
                if country_index is None
                else _cell_value(row, country_index),
                latitude_text=""
                if latitude_index is None
                else _clean_coordinate_text(_cell_value(row, latitude_index)),
                longitude_text=""
                if longitude_index is None
                else _clean_coordinate_text(_cell_value(row, longitude_index)),
                chronology_text=chronology_text,
                source_native_identity_kind="supplementary_sample_label",
            )
        )
    return tuple(built_rows)


def _qualify_goat_imputation_rows(
    *,
    rows: tuple[AdnaProjectSampleMasterRow, ...],
    table_rows: tuple[tuple[str, ...], ...],
    archive_text: str | None,
    archive_source_path: str,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Retain source rows without turning publication reuse into project ownership."""
    headers = table_rows[0] if table_rows else ()
    accession_index = next(
        (index for index, value in enumerate(headers) if value.strip() == "Accession"),
        None,
    )
    accession_cells = {
        f"Table S2 downsampled samples!row{row_number}": (
            source_row[accession_index]
            if accession_index is not None and accession_index < len(source_row)
            else ""
        )
        for row_number, source_row in enumerate(table_rows[1:], start=2)
    }
    memberships: set[tuple[str, str]] = set()
    archive_status = "retained archive capture unavailable"
    archive_inspected = False
    if archive_text is not None:
        reader = csv.DictReader(io.StringIO(archive_text), delimiter="\t")
        if {"study_accession", "sample_accession"} <= set(reader.fieldnames or ()):
            memberships = {
                (record["study_accession"].strip(), record["sample_accession"].strip())
                for record in reader
                if record.get("study_accession") and record.get("sample_accession")
            }
            archive_status = "retained archive study/sample membership inspected"
            archive_inspected = True
        else:
            archive_status = "retained archive study/sample columns unavailable"

    qualified_rows = []
    for row in rows:
        literal = accession_cells.get(row.sample_lineage_locator, "")
        candidates = tuple(
            dict.fromkeys(
                value.strip() for value in literal.split(";") if value.strip()
            )
        )
        matching = tuple(
            accession
            for accession in candidates
            if (row.project_accession, accession) in memberships
        )
        missing = tuple(
            accession for accession in candidates if accession not in matching
        )
        target_present = (
            any(study == row.project_accession for study, _ in memberships)
            if archive_inspected
            else None
        )
        note = (
            f"{row.sample_ambiguity_note} {archive_status}; "
            f"requested study {row.project_accession} present in capture: {target_present}; "
            f"all accession alternatives: {candidates!r}; "
            f"requested-study matches: {matching!r}; "
            f"alternatives without requested-study support: {missing!r}. "
            "Capture absence does not establish absence from the live archive. "
            "Study membership alone does not resolve a unique specimen, "
            "technical dependence, taxonomy or selected chronology."
        )
        qualified_rows.append(
            replace(
                row,
                sample_identity_resolution="ambiguous",
                sample_ambiguity_note=note,
                sample_lineage_path=f"{row.sample_lineage_path} || {archive_source_path}",
                sample_lineage_locator=(
                    f"{row.sample_lineage_locator} || retained TSV study_accession "
                    "and sample_accession"
                ),
                sample_lineage_excerpt=f"{row.sample_lineage_excerpt} || {note}",
            )
        )
    return tuple(qualified_rows)


def _current_run_association_note(
    *, native_accession: str, secondary_accession: str, association: dict[str, Any]
) -> str:
    """Describe capture-bound technical associations without selecting ownership."""
    if (
        association["observed_sample_accession"] != native_accession
        or association["query_secondary_accession"] != secondary_accession
    ):
        raise ValueError("Goat current run association sample binding differs")
    # The complete reviewed context is digest-bound; retain every reported study.
    studies = sorted(
        association["study_associations"], key=lambda study: study["study_accession"]
    )
    observed = (
        "; ".join(
            f"{study['study_accession']}: {study['returned_row_count']} returned technical rows, "
            f"{study['distinct_run_count']} distinct run IDs and "
            f"{study['distinct_experiment_count']} distinct experiment IDs"
            for study in studies
        )
        or "no study rows returned"
    )
    return (
        f"Current read_run capture for SAMPLE {native_accession} / "
        f"{secondary_accession} reports {observed} "
        f"(row limit {association['row_limit']}; "
        f"limit reached: {association['limit_reached']})."
    )


def _matched_direkli_study_note(
    *,
    accessions: tuple[str, ...],
    natives: dict[str, Any],
    associations: dict[str, Any],
    study: dict[str, Any],
) -> str:
    """Attribute the paired source assertion only to its two matched native records."""
    pair = {"SAMEA4453841", "SAMEA4453842"}
    if set(accessions) != pair:
        return ""
    members = study["direkli_assertion"]["native_records"]
    if (
        study["native"]["primary_id"] != "PRJEB26011"
        or study["native"]["secondary_id"] != "ERP107983"
        or len(members) != 2
        or {member["primary_id"] for member in members} != pair
        or any(
            natives[member["primary_id"]][field] != member[field]
            for member in members
            for field in ("primary_id", "secondary_id", "title", "alias")
        )
    ):
        raise ValueError("Direkli native study assertion binding differs")
    if not all(
        any(
            group["study_accession"] == "PRJEB26011"
            for group in associations[a]["study_associations"]
        )
        for a in accessions
    ):
        return ""
    return (
        " Current native PROJECT PRJEB26011 / ERP107983 "
        f"({study['native']['title']}; PubMed {', '.join(study['native']['pubmed_ids'])}) "
        "reports Direkli1 and 2 as identified from the same individual, and "
        "cautions that the same PCR reactions sometimes span several runs. "
        "This is an attributed source assertion for both matched native records, "
        "not a selected physical-specimen identity, pooling instruction or "
        "biological admission. Both records and the ambiguous author row are retained."
    )


def _original_paper_reference_correspondence(
    *, natives: dict[str, Any], paper: dict[str, Any]
) -> dict[str, Any]:
    """Bind reported paper references to all native labels without choosing specimens."""
    entries = paper["reported_references"]
    references = {entry["native"]["primary_id"]: entry for entry in entries}
    if len(references) != len(entries) or set(references) != set(natives):
        raise ValueError("Goat original-paper reference coverage differs")
    for accession, entry in references.items():
        if entry["paper_label"] != natives[accession]["title"] or any(
            entry["native"][field] != natives[accession][field]
            for field in ("primary_id", "secondary_id", "title", "alias")
        ):
            raise ValueError("Goat original-paper native label binding differs")
    return references


def _bind_goat_comparator_native_context(
    rows: tuple[AdnaProjectSampleMasterRow, ...],
    *,
    context: bytes,
    workbook_sha256: str,
    table_rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Retain all native assertions without selecting a pooled specimen identity."""
    if sha256(context).hexdigest() != _NATIVE_CONTEXT_SHA256:
        raise ValueError("Goat comparator native source context changed")
    if workbook_sha256 != _NATIVE_WORKBOOK_SHA256:
        raise ValueError("Goat comparator supplementary source changed")
    document = json.loads(context)
    native_records = document["native_records"]
    natives = {
        record["native"]["accession"]: record["native"] for record in native_records
    }
    if len(natives) != len(native_records):
        raise ValueError("Goat comparator native record duplicated")
    for accession, native in natives.items():
        if any(native[field] != accession for field in ("primary_id", "biosample_id")):
            raise ValueError("Goat comparator native accession assertions disagree")
    association_notes = {
        record["native"]["accession"]: _current_run_association_note(
            native_accession=record["native"]["accession"],
            secondary_accession=record["native"]["secondary_id"],
            association=record["current_run_associations"],
        )
        for record in native_records
    }
    paper = document["original_paper_context"]
    paper_references = _original_paper_reference_correspondence(
        natives=natives, paper=paper
    )
    benchmarks = document["benchmarks"]
    by_label = {row.preferred_sample_label: row for row in rows}
    labels = [benchmark["sample_label"] for benchmark in benchmarks]
    if (
        len(by_label) != len(rows)
        or len(set(labels)) != len(labels)
        or set(by_label) != set(labels)
    ):
        raise ValueError("Goat comparator requires one owner per author row")
    if not table_rows or any(
        table_rows[0].count(name) != 1 for name in ("Sample", "Accession")
    ):
        raise ValueError("Goat comparator source metadata columns changed")
    sample_column = table_rows[0].index("Sample")
    accession_column = table_rows[0].index("Accession")
    updated: dict[str, AdnaProjectSampleMasterRow] = {}
    covered: set[str] = set()
    for benchmark in benchmarks:
        label = benchmark["sample_label"]
        accessions = tuple(benchmark["native_accessions"])
        literal = benchmark["accession_cell"]
        if (
            not accessions
            or len(set(accessions)) != len(accessions)
            or accessions != tuple(value.strip() for value in literal.split(";"))
            or set(accessions) & covered
            or not set(accessions) <= set(natives)
        ):
            raise ValueError(
                "Goat comparator missing, repeated or swapped native accession"
            )
        source_row_number = benchmark["row"]
        if not 2 <= source_row_number <= len(table_rows):
            raise ValueError("Goat comparator source row changed")
        source_row = table_rows[source_row_number - 1]
        if (
            _cell_value(source_row, sample_column) != label
            or _cell_value(source_row, accession_column) != literal
        ):
            raise ValueError("Goat comparator author label/accession cell changed")
        row = by_label[label]
        # The original adapter's scalar accession remains a trace, not a selected
        # unique identity for a row whose literal cell names multiple records.
        if (
            row.project_accession != "PRJEB90141"
            or row.archive_native_sample_id != accessions[0]
            or row.paper_native_sample_label != label
            or row.supplementary_table_sample_label != label
            or row.sample_identity_resolution != "ambiguous"
            or row.source_native_identity_kind != "supplementary_sample_label"
            or row.source_native_tax_id
            or row.source_native_scientific_name
            or row.taxon_alignment_status != "not_reported"
        ):
            raise ValueError("Goat comparator owner or unselected scope changed")
        assertions = tuple(natives[accession] for accession in accessions)
        source_names = tuple(
            dict.fromkeys(native["scientific_name"] for native in assertions)
        )
        note = (
            f"Original author label {label!r}; Accession cell {literal!r}. "
            + " ".join(
                f"Native SAMPLE {native['primary_id']} / {native['secondary_id']}; "
                f"title {native['title']!r}; alias {native['alias']!r}; "
                f"taxon {native['taxon_id']} / {native['scientific_name']}; "
                f"description {native['description']!r}."
                for native in assertions
            )
        )
        note += (
            " Separate native records do not select a scalar specimen, establish "
            "specimen independence or project membership, or select coordinates "
            "or chronology. Native scientific-name agreement/difference is a "
            "computational comparison, not biological or taxonomic validation."
        )
        note += " " + " ".join(association_notes[accession] for accession in accessions)
        note += (
            " These are only observed current technical associations, not complete "
            "or historical study membership, configured-project ownership, "
            "physical-specimen identity or biological independence."
        )
        note += _matched_direkli_study_note(
            accessions=accessions,
            natives=natives,
            associations={
                r["native"]["accession"]: r["current_run_associations"]
                for r in native_records
            },
            study=document["native_study_context"],
        )
        references = tuple(paper_references[accession] for accession in accessions)
        paper_locator = "; ".join(
            f"{reference['paper_label']} {reference['reported_sample_reference']!r} "
            f"(PDF page {reference['methods_pdf_page']})"
            for reference in references
        )
        note += (
            " Retained accepted-manuscript Methods (Daly et al. 2018; DOI "
            "10.1126/science.aas9411) reports "
            + paper_locator
            + ". Exact native TITLE/alias correspondence supports document-label "
            "correspondence only; no native accession field carries these reported "
            "references. They do not select physical-specimen, extraction or library "
            "identifiers, project ownership, coordinates or chronology."
        )
        if label == "Blagotin3":
            note += " " + paper["blagotin_reference_caution"]
        updated[label] = replace(
            row,
            source_native_tax_id=_join_distinct(
                *(native["taxon_id"] for native in assertions)
            ),
            source_native_scientific_name=_join_distinct(*source_names),
            taxon_alignment_status=_taxon_alignment_status(
                configured_species=row.species_latin_name,
                source_native_scientific_names=source_names,
            ),
            sample_lineage_path=f"{GOAT_NATIVE_CONTEXT} || {row.sample_lineage_path}",
            sample_lineage_locator=f"{row.sample_lineage_locator} || Native SAMPLE assertions: "
            + "; ".join(
                f"{native['primary_id']}/TITLE:{native['title']}"
                for native in assertions
            )
            + " || current_run_associations: "
            + "; ".join(accessions)
            + " || Daly2018 AM Methods reported references: "
            + paper_locator,
            sample_lineage_excerpt=f"{row.sample_lineage_excerpt} || {note}",
            sample_ambiguity_note=f"{row.sample_ambiguity_note} {note}",
        )
        covered.update(accessions)
    if covered != set(natives):
        raise ValueError("Goat comparator native record has no author-row owner")
    return tuple(updated[row.preferred_sample_label] for row in rows)
