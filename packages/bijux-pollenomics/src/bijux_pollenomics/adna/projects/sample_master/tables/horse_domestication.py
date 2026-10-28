"""Recover the Berel horse omitted from the later comparative workbook."""

from __future__ import annotations

import csv
from hashlib import sha256
from io import StringIO
from pathlib import Path, PurePosixPath

from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition
from bijux_pollenomics.adna.workflow.source_artifacts import (
    read_source_artifact_bytes,
    source_artifact_exists,
)

from ..identity import _resolve_data_relative_path
from ..models import AdnaProjectSampleMasterRow

HORSE_DOMESTICATION_SUPPLEMENT = (
    "data/adna/governance/source_library/papers/10.1126-science.aam5298/"
    "supplementary/aam5298_librado.sm.pdf"
)
HORSE_DOMESTICATION_ARCHIVE = (
    "data/adna/governance/source_library/projects/PRJEB19970/archive_metadata.html"
)
_SUPPLEMENT_SHA256 = "c5e3a9c1802eb507203ba3ec6508a679e7b618a2709a67e0be6751f8249c504f"
_ARCHIVE_SHA256 = "f3d09d2e0c6388edd1f057470b77f9e79a2e7bad1c697fd456780aaf00ec072b"
_BEREL_SAMPLE = "SAMEA103910520"
_BEREL_RUNS = frozenset(
    {
        *(f"ERR{number}" for number in range(1885586, 1885597)),
        "ERR1892229",
        "ERR1892230",
    }
)


def _berel_archive_locator(archive_text: str) -> str:
    """Join complete filename labels to one BioSample without CGG inference."""
    reader = csv.DictReader(StringIO(archive_text), delimiter="\t")
    required = (
        "run_accession",
        "study_accession",
        "sample_accession",
        "experiment_accession",
        "tax_id",
        "scientific_name",
        "submitted_ftp",
    )
    if reader.fieldnames is None or any(
        reader.fieldnames.count(name) != 1 for name in required
    ):
        raise ValueError("PRJEB19970 archive identity columns are missing or ambiguous")
    matched_runs: set[str] = set()
    lines: list[int] = []
    for line, row in enumerate(reader, start=2):
        if None in row or any(row[name] is None for name in required):
            raise ValueError(f"PRJEB19970 archive row {line} is malformed")
        names = tuple(
            PurePosixPath(part).name for part in row["submitted_ftp"].split(";") if part
        )
        labels_match = tuple(
            name.startswith(("BER11_L__", "BER11_L.")) for name in names
        )
        owns_sample = row["sample_accession"] == _BEREL_SAMPLE
        if not owns_sample and not any(labels_match):
            continue
        if not owns_sample or not labels_match or not all(labels_match):
            raise ValueError("PRJEB19970 BER11_L filename-to-BioSample conflict")
        if (
            row["study_accession"] != "PRJEB19970"
            or row["tax_id"] != "9796"
            or row["scientific_name"] != "Equus caballus"
            or not row["experiment_accession"].startswith("ERX")
        ):
            raise ValueError("PRJEB19970 BER11_L archive project or taxonomy conflict")
        run = row["run_accession"]
        if run in matched_runs:
            raise ValueError("PRJEB19970 BER11_L duplicate run identity")
        matched_runs.add(run)
        lines.append(line)
    if frozenset(matched_runs) != _BEREL_RUNS:
        raise ValueError("PRJEB19970 BER11_L thirteen-run population drift")
    return (
        f"sample_accession:{_BEREL_SAMPLE};submitted_filename_label:BER11_L;"
        "tsv_lines:" + ",".join(map(str, lines))
    )


def _horse_domestication_primary_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Admit the pinned primary-table identity while retaining text-only dating."""
    paths = tuple(
        _resolve_data_relative_path(output_root, name)
        for name in (HORSE_DOMESTICATION_SUPPLEMENT, HORSE_DOMESTICATION_ARCHIVE)
    )
    if not all(source_artifact_exists(path) for path in paths):
        return ()
    if (
        project.project_accession != "PRJEB19970"
        or species.latin_name != "Equus caballus"
    ):
        raise ValueError(
            "Berel horse evidence belongs only to PRJEB19970 Equus caballus"
        )
    supplement, archive = (read_source_artifact_bytes(path) for path in paths)
    if sha256(supplement).hexdigest() != _SUPPLEMENT_SHA256:
        raise ValueError("PRJEB19970 primary supplement source drift")
    if sha256(archive).hexdigest() != _ARCHIVE_SHA256:
        raise ValueError("PRJEB19970 retained archive source drift")
    archive_locator = _berel_archive_locator(archive.decode("utf-8"))
    return (
        AdnaProjectSampleMasterRow(
            species_latin_name=species.latin_name,
            species_common_name=species.common_name,
            project_accession=project.project_accession,
            repo_stable_sample_id=f"prjeb19970:{_BEREL_SAMPLE.casefold()}",
            archive_native_sample_id=_BEREL_SAMPLE,
            paper_native_sample_label="BER11_L",
            supplementary_table_sample_label="BER11_L",
            preferred_sample_label="BER11_L",
            sample_basis="primary_supplement_archive_filename_join",
            sample_evidence_status="pdf_text_extracted",
            sample_lineage_path=f"{HORSE_DOMESTICATION_SUPPLEMENT} | {HORSE_DOMESTICATION_ARCHIVE}",
            sample_lineage_locator=f"PDF p.78, Table S12, ID BER11_L; PDF p.2, data availability | {archive_locator}",
            sample_lineage_excerpt=(
                "Table S12: BER11_L | Berel' | 2,300 yBP | coverage 1.665. "
                "The caption defines yBP as years Before Present. PDF p.2 assigns "
                "shotgun data to PRJEB19970. Thirteen distinct archive runs "
                "(eleven FASTQ and two aligned BAM records) bind BER11_L filenames "
                "to SAMEA103910520, tax_id 9796, Equus caballus. The selected "
                "table does not supply a calibrated interval, dating method or "
                "explicit reference year; no precise numeric chronology is admitted."
            ),
            sample_identity_resolution="final",
            sample_ambiguity_note="",
            locality_text="Berel'",
            political_entity="",
            latitude_text="",
            longitude_text="",
            chronology_text="2,300 yBP",
            chronology_dating_basis="unknown",
            chronology_evidence_class="unresolved",
            chronology_precision_posture="unresolved",
            source_native_tax_id="9796",
            source_native_scientific_name="Equus caballus",
            taxon_alignment_status="project_species_match",
            source_native_identity_kind="biological_sample_accession",
        ),
    )
