"""Bind SRA camel experiments to official ENA biological sample accessions."""

from __future__ import annotations

import csv
from dataclasses import replace
from hashlib import sha256
from io import StringIO
from pathlib import Path

from bijux_pollenomics.adna.projects.sample_master.models import (
    AdnaProjectSampleMasterRow,
)

_SOURCE = "data/adna/governance/source_library/projects/SRP073444/ena_run_samples.tsv"
_SOURCE_SHA256 = "e732170881351bb3199b250c60fa1c2b53c5e7cde6ccb30db5ee00d84ffbf99a"
_COLUMNS = (
    "run_accession",
    "study_accession",
    "sample_accession",
    "experiment_accession",
)


def build_camel_sample_rows(
    output_root: Path, archive_rows: tuple[AdnaProjectSampleMasterRow, ...]
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Use exact experiment joins; retain separate sequencing and sample identities."""
    source_path = output_root / _SOURCE.removeprefix("data/")
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
        accession = link["sample_accession"]
        result.append(
            replace(
                row,
                repo_stable_sample_id=f"srp073444:{accession}".casefold(),
                archive_native_sample_id=accession,
                sample_basis="official_archive_experiment_sample_join",
                sample_evidence_status="archive_native",
                sample_lineage_path=f"{row.sample_lineage_path} || {_SOURCE}",
                sample_lineage_locator=(
                    f"{row.sample_lineage_locator};"
                    f"run_accession:{link['run_accession']};"
                    f"sample_accession:{accession}"
                ),
                sample_lineage_excerpt=(
                    f"NCBI SRA experiment {row.archive_native_experiment_id} and "
                    f"official ENA run {link['run_accession']} identify biological "
                    f"sample {accession}; specimen label {row.preferred_sample_label}."
                ),
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                source_native_identity_kind="biological_sample_accession",
            )
        )
    return tuple(result)
