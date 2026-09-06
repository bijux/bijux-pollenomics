from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from pathlib import Path

from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_text

__all__ = [
    "AdnaArchiveProjectSample",
    "read_archive_project_samples",
]

_NCBI_EXPERIMENT_LINK = re.compile(
    r'<a\s+[^>]*href="/sra/(?P<accession>SRX\d+)\[accn\]"[^>]*>'
    r"(?P<label>.*?)</a>",
    flags=re.IGNORECASE | re.DOTALL,
)
_HTML_TAG = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class AdnaArchiveProjectSample:
    """One source-native sample or experiment identity from an archive capture."""

    archive_native_sample_id: str
    archive_native_experiment_id: str
    source_native_identity_kind: str
    source_native_sample_label: str
    source_native_tax_ids: tuple[str, ...]
    source_native_scientific_names: tuple[str, ...]
    source_locator: str
    source_excerpt: str


def read_archive_project_samples(
    archive_path: Path,
) -> tuple[AdnaArchiveProjectSample, ...]:
    """Read supported ENA TSV or NCBI SRA-result captures without inference."""
    archive_text = read_source_artifact_text(
        Path(archive_path), encoding="utf-8", errors="ignore"
    )
    tsv_rows = _read_ena_tsv_samples(archive_text)
    if tsv_rows:
        return tsv_rows
    return _read_ncbi_sra_experiments(archive_text)


def _read_ena_tsv_samples(
    archive_text: str,
) -> tuple[AdnaArchiveProjectSample, ...]:
    lines = archive_text.splitlines()
    if not lines:
        return ()
    header = lines[0].split("\t")
    if "sample_accession" not in header:
        return ()
    sample_index = header.index("sample_accession")
    tax_id_index = header.index("tax_id") if "tax_id" in header else None
    scientific_name_index = (
        header.index("scientific_name") if "scientific_name" in header else None
    )
    grouped: dict[str, set[tuple[str, str]]] = {}
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) <= sample_index:
            continue
        accession = fields[sample_index].strip()
        if not accession:
            continue
        tax_id = (
            ""
            if tax_id_index is None or len(fields) <= tax_id_index
            else fields[tax_id_index].strip()
        )
        scientific_name = (
            ""
            if scientific_name_index is None or len(fields) <= scientific_name_index
            else fields[scientific_name_index].strip()
        )
        grouped.setdefault(accession, set()).add((tax_id, scientific_name))

    rows = []
    for accession, taxa in sorted(grouped.items()):
        tax_ids = tuple(sorted({tax_id for tax_id, _ in taxa if tax_id}))
        scientific_names = tuple(
            sorted({name for _, name in taxa if name}, key=str.casefold)
        )
        taxon_text = ", ".join(
            f"{name} (tax_id {tax_id})"
            for tax_id, name in sorted(taxa, key=lambda item: item[1].casefold())
            if tax_id or name
        )
        rows.append(
            AdnaArchiveProjectSample(
                archive_native_sample_id=accession,
                archive_native_experiment_id="",
                source_native_identity_kind="biological_sample_accession",
                source_native_sample_label="",
                source_native_tax_ids=tax_ids,
                source_native_scientific_names=scientific_names,
                source_locator=f"sample_accession:{accession}",
                source_excerpt=(
                    f"ENA archive metadata identifies sample {accession}"
                    + (f" as {taxon_text}." if taxon_text else ".")
                ),
            )
        )
    return tuple(rows)


def _read_ncbi_sra_experiments(
    archive_text: str,
) -> tuple[AdnaArchiveProjectSample, ...]:
    rows: dict[str, AdnaArchiveProjectSample] = {}
    for match in _NCBI_EXPERIMENT_LINK.finditer(archive_text):
        accession = match.group("accession").upper()
        label = unescape(_HTML_TAG.sub("", match.group("label"))).strip()
        if not label:
            continue
        rows[accession] = AdnaArchiveProjectSample(
            archive_native_sample_id="",
            archive_native_experiment_id=accession,
            source_native_identity_kind="sequencing_experiment_accession",
            source_native_sample_label=label,
            source_native_tax_ids=(),
            source_native_scientific_names=(),
            source_locator=f"experiment_accession:{accession}",
            source_excerpt=(
                f"NCBI SRA results identify experiment {accession} with source-native "
                f"label {label}."
            ),
        )
    return tuple(rows[accession] for accession in sorted(rows))
