"""Bind camel archive identities to primary-paper specimen evidence."""

from __future__ import annotations

import csv
from dataclasses import replace
from hashlib import sha256
from io import StringIO
from pathlib import Path

from bijux_pollenomics.adna.projects.sample_master.models import (
    AdnaProjectSampleMasterRow,
)
from bijux_pollenomics.adna.projects.sample_master.identity import (
    _taxon_alignment_status,
)

_SOURCE = "data/adna/governance/source_library/projects/SRP073444/ena_run_samples.tsv"
_SOURCE_SHA256 = "fda2ea49e06d0380110fc846cd99ae6274259dfb91c7e8a414e1157e6542d384"
_TABLE_SOURCE = (
    "data/adna/governance/source_library/projects/SRP073444/"
    "paper_table_s1_sample_bridge.csv"
)
_TABLE_SHA256 = "7f42433a4a046874217ba6eb9d8d5d31e093c78e3240ce725be65f3b1d619e5d"
_COLUMNS = (
    "run_accession",
    "study_accession",
    "sample_accession",
    "experiment_accession",
    "sample_alias",
    "sample_title",
    "scientific_name",
    "tax_id",
)
_TABLE_COLUMNS = (
    "experiment_accession",
    "sample_accession",
    "archive_alias",
    "paper_sample_label",
    "table_row",
    "political_entity",
    "locality_text",
    "find_number",
    "paper_age_text",
    "chronology_text",
)


def build_camel_sample_rows(
    output_root: Path, archive_rows: tuple[AdnaProjectSampleMasterRow, ...]
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Keep BioSamples separate while joining each to one paper specimen row."""
    source_path = output_root / _SOURCE.removeprefix("data/")
    table_path = output_root / _TABLE_SOURCE.removeprefix("data/")
    if not archive_rows and not source_path.exists() and not table_path.exists():
        return ()
    payload = source_path.read_bytes()
    if sha256(payload).hexdigest() != _SOURCE_SHA256:
        raise ValueError("SRP073444 official ENA run report changed")
    reader = csv.DictReader(StringIO(payload.decode("utf-8")), delimiter="\t")
    if tuple(reader.fieldnames or ()) != _COLUMNS:
        raise ValueError("SRP073444 ENA run report columns changed")
    rows = list(reader)
    if len(rows) != 107 or any(None in row for row in rows):
        raise ValueError("SRP073444 ENA run report denominator changed")
    if any(row["study_accession"] != "PRJNA317727" for row in rows):
        raise ValueError("SRP073444 ENA study identity changed")
    if any(
        len({row[key] for row in rows}) != len(rows)
        for key in ("run_accession", "experiment_accession", "sample_accession")
    ):
        raise ValueError("SRP073444 ENA sample/experiment relation is ambiguous")
    by_experiment = {row["experiment_accession"]: row for row in rows}
    table_payload = table_path.read_bytes()
    if sha256(table_payload).hexdigest() != _TABLE_SHA256:
        raise ValueError("SRP073444 paper Table S1 bridge changed")
    table_reader = csv.DictReader(StringIO(table_payload.decode("utf-8")))
    if tuple(table_reader.fieldnames or ()) != _TABLE_COLUMNS:
        raise ValueError("SRP073444 paper Table S1 bridge columns changed")
    table_rows = list(table_reader)
    if (
        len(table_rows) != 20
        or any(None in row for row in table_rows)
        or len({row["experiment_accession"] for row in table_rows}) != 20
        or len({row["paper_sample_label"] for row in table_rows}) != 19
    ):
        raise ValueError("SRP073444 paper Table S1 bridge denominator changed")
    table_by_experiment = {row["experiment_accession"]: row for row in table_rows}
    if (
        len(archive_rows) != 20
        or len({row.archive_native_experiment_id for row in archive_rows}) != 20
    ):
        raise ValueError("SRP073444 admitted experiment population changed")
    result = []
    for row in archive_rows:
        link = by_experiment.get(row.archive_native_experiment_id)
        if link is None or not link["sample_accession"].startswith("SAMN"):
            raise ValueError("SRP073444 experiment lacks official BioSample linkage")
        table = table_by_experiment.get(row.archive_native_experiment_id)
        if table is None or (
            table["sample_accession"] != link["sample_accession"]
            or table["archive_alias"] != link["sample_alias"]
            or link["sample_alias"] != row.preferred_sample_label
            or link["sample_title"].partition("_DSL_")[0] != table["paper_sample_label"]
            or "_DSL_" not in link["sample_title"]
        ):
            raise ValueError(
                "SRP073444 BioSample-to-paper specimen bridge is ambiguous"
            )
        if (
            link["scientific_name"] != row.species_latin_name
            or link["tax_id"] != "9838"
        ):
            raise ValueError("SRP073444 BioSample source taxon conflicts with cohort")
        accession = link["sample_accession"]
        result.append(
            replace(
                row,
                repo_stable_sample_id=f"srp073444:{accession}".casefold(),
                archive_native_sample_id=accession,
                sample_basis="official_archive_experiment_sample_join",
                sample_evidence_status="archive_native",
                paper_native_sample_label=table["paper_sample_label"],
                supplementary_table_sample_label=table["paper_sample_label"],
                sample_lineage_path=(
                    f"{row.sample_lineage_path} || {_SOURCE} || {_TABLE_SOURCE}"
                ),
                sample_lineage_locator=(
                    f"{row.sample_lineage_locator};"
                    f"run_accession:{link['run_accession']};"
                    f"sample_accession:{accession};"
                    f"Table S1:row {table['table_row']};"
                    f"paper_sample_label:{table['paper_sample_label']}"
                ),
                sample_lineage_excerpt=(
                    f"NCBI SRA experiment {row.archive_native_experiment_id} and "
                    f"official ENA run {link['run_accession']} identify biological "
                    f"sample {accession}; author Table S1 assigns paper label "
                    f"{table['paper_sample_label']} to {table['locality_text']}, "
                    f"{table['political_entity']}, age {table['paper_age_text']}."
                ),
                sample_identity_resolution="final",
                sample_ambiguity_note=(
                    "Distinct BioSample accessions share paper specimen label "
                    "Palm143; physical specimen independence is not established."
                    if table["paper_sample_label"] == "Palm143"
                    else ""
                ),
                locality_text=table["locality_text"],
                political_entity=table["political_entity"],
                chronology_text=table["chronology_text"],
                chronology_dating_basis="historical_and_archaeological_context",
                chronology_evidence_class=(
                    "archaeological_context_date" if table["chronology_text"] else ""
                ),
                chronology_precision_posture=(
                    "contextual_interval" if table["chronology_text"] else ""
                ),
                source_native_tax_id=link["tax_id"],
                source_native_scientific_name=link["scientific_name"],
                taxon_alignment_status=_taxon_alignment_status(
                    configured_species=row.species_latin_name,
                    source_native_scientific_names=(link["scientific_name"],),
                ),
                source_native_identity_kind="biological_sample_accession",
            )
        )
    return tuple(result)
