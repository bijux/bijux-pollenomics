from __future__ import annotations

from dataclasses import dataclass
from typing import Final


ADNA_ENA_RESULT_KINDS: Final[tuple[str, ...]] = ("read_run", "analysis")


@dataclass(frozen=True)
class AdnaEnaQuery:
    """Typed ENA selector contract for species-aware ancient-DNA metadata fetches."""

    projects: tuple[str, ...]
    samples: tuple[str, ...]
    extra_accessions: tuple[str, ...]
    result_kind: str = "read_run"

    def normalized_accessions(self) -> tuple[str, ...]:
        normalized = {
            *_normalize_values(self.projects),
            *_normalize_values(self.samples),
            *_normalize_values(self.extra_accessions),
        }
        return tuple(sorted(normalized))

    def validate(self) -> None:
        if self.result_kind not in ADNA_ENA_RESULT_KINDS:
            raise ValueError(f"Unsupported ENA result kind: {self.result_kind}")
        accessions = self.normalized_accessions()
        if not accessions:
            raise ValueError(
                "Provide at least one ENA project, sample, or accession selector"
            )
        for accession in accessions:
            if not _valid_selector(accession):
                raise ValueError(f"Invalid ENA selector: {accession}")

    def sample_allowed(self, sample_accession: str) -> bool:
        sample_filter = set(_normalize_values(self.samples))
        if not sample_filter:
            return True
        return sample_accession in sample_filter

    def record_allowed(self, *accessions: str | None) -> bool:
        """Return whether one response row belongs to the requested selectors."""
        row_accessions = {value for value in accessions if value is not None}
        extra_filter = set(_normalize_values(self.extra_accessions))
        if extra_filter & row_accessions:
            return True

        project_filter = set(_normalize_values(self.projects))
        if project_filter and not project_filter.intersection(row_accessions):
            return False

        sample_filter = set(_normalize_values(self.samples))
        if sample_filter and not sample_filter.intersection(row_accessions):
            return False
        return bool(project_filter or sample_filter)


@dataclass(frozen=True)
class AdnaEnaRecord:
    """Decoded ENA filereport row for ancient-DNA archive intake review."""

    study_accession: str | None
    sample_accession: str | None
    experiment_accession: str | None
    run_accession: str | None
    analysis_accession: str | None
    analysis_type: str | None
    tax_id: str | None
    scientific_name: str | None
    library_layout: str | None
    library_source: str | None
    library_strategy: str | None
    instrument_model: str | None
    base_count: int | None
    read_count: int | None
    fastq_bytes: tuple[int, ...]
    fastq_ftp: tuple[str, ...]
    submitted_ftp: tuple[str, ...]
    sra_ftp: tuple[str, ...]
    bam_ftp: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "study_accession": self.study_accession,
            "sample_accession": self.sample_accession,
            "experiment_accession": self.experiment_accession,
            "run_accession": self.run_accession,
            "analysis_accession": self.analysis_accession,
            "analysis_type": self.analysis_type,
            "tax_id": self.tax_id,
            "scientific_name": self.scientific_name,
            "library_layout": self.library_layout,
            "library_source": self.library_source,
            "library_strategy": self.library_strategy,
            "instrument_model": self.instrument_model,
            "base_count": self.base_count,
            "read_count": self.read_count,
            "fastq_bytes": list(self.fastq_bytes),
            "fastq_ftp": list(self.fastq_ftp),
            "submitted_ftp": list(self.submitted_ftp),
            "sra_ftp": list(self.sra_ftp),
            "bam_ftp": list(self.bam_ftp),
        }


def _normalize_values(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(value.strip() for value in values if value.strip())


def _valid_selector(value: str) -> bool:
    return all(ch.isascii() and (ch.isalnum() or ch in {"_", "-", "."}) for ch in value)
