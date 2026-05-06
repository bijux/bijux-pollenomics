from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .species import resolve_species_definition

__all__ = [
    "ADNA_ENA_RESULT_KINDS",
    "AdnaArchiveProject",
    "AdnaEnaQuery",
    "AdnaEnaRecord",
    "build_archive_project_catalog",
    "build_ena_filereport_url",
    "build_species_archive_projects",
    "parse_ena_filereport_tsv",
]

ADNA_ENA_RESULT_KINDS: Final[tuple[str, ...]] = ("read_run", "analysis")
_ENA_API_BASE = "https://www.ebi.ac.uk/ena/portal/api/filereport"


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
            raise ValueError("Provide at least one ENA project, sample, or accession selector")
        for accession in accessions:
            if not _valid_selector(accession):
                raise ValueError(f"Invalid ENA selector: {accession}")

    def sample_allowed(self, sample_accession: str) -> bool:
        sample_filter = set(_normalize_values(self.samples))
        if not sample_filter:
            return True
        return sample_accession in sample_filter


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


@dataclass(frozen=True)
class AdnaArchiveProject:
    """Species-aware archive project catalog entry for domesticated-animal aDNA."""

    species_latin_name: str
    project_accession: str
    result_kind: str
    metadata_url: str
    source_family: str
    archive_status: str
    notes: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "project_accession": self.project_accession,
            "result_kind": self.result_kind,
            "metadata_url": self.metadata_url,
            "source_family": self.source_family,
            "archive_status": self.archive_status,
            "notes": self.notes,
        }


def build_ena_filereport_url(accession: str, result_kind: str = "read_run") -> str:
    """Build the canonical ENA filereport URL for one accession."""
    if result_kind not in ADNA_ENA_RESULT_KINDS:
        raise ValueError(f"Unsupported ENA result kind: {result_kind}")
    fields = ",".join(_filereport_fields(result_kind))
    return (
        f"{_ENA_API_BASE}?accession={accession}&result={result_kind}&fields={fields}"
        "&format=tsv&download=true&limit=0"
    )


def parse_ena_filereport_tsv(
    tsv: str,
    query: AdnaEnaQuery,
) -> tuple[AdnaEnaRecord, ...]:
    """Decode an ENA filereport TSV payload into typed records."""
    query.validate()
    lines = tsv.splitlines()
    if not lines:
        raise ValueError("ENA filereport response is empty")
    headers = lines[0].split("\t")
    _validate_headers(headers, query.result_kind)

    rows: list[AdnaEnaRecord] = []
    for line_number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        values = line.split("\t")
        if len(values) != len(headers):
            raise ValueError(
                f"ENA filereport row {line_number} has {len(values)} columns, expected {len(headers)}"
            )
        row = dict(zip(headers, values, strict=True))
        sample_accession = _opt_field(row.get("sample_accession", ""))
        if sample_accession is not None and not query.sample_allowed(sample_accession):
            continue
        rows.append(
            AdnaEnaRecord(
                study_accession=_opt_field(row.get("study_accession", "")),
                sample_accession=sample_accession,
                experiment_accession=_opt_field(row.get("experiment_accession", "")),
                run_accession=_opt_field(row.get("run_accession", "")),
                analysis_accession=_opt_field(row.get("analysis_accession", "")),
                analysis_type=_opt_field(row.get("analysis_type", "")),
                tax_id=_opt_field(row.get("tax_id", "")),
                scientific_name=_opt_field(row.get("scientific_name", "")),
                library_layout=_opt_field(row.get("library_layout", "")),
                library_source=_opt_field(row.get("library_source", "")),
                library_strategy=_opt_field(row.get("library_strategy", "")),
                instrument_model=_opt_field(row.get("instrument_model", "")),
                base_count=_parse_optional_int(row.get("base_count", ""), "base_count", line_number),
                read_count=_parse_optional_int(row.get("read_count", ""), "read_count", line_number),
                fastq_bytes=_parse_int_list(row.get("fastq_bytes", ""), "fastq_bytes", line_number),
                fastq_ftp=_split_field(row.get("fastq_ftp", "")),
                submitted_ftp=_split_field(row.get("submitted_ftp", "")),
                sra_ftp=_split_field(row.get("sra_ftp", "")),
                bam_ftp=_split_field(row.get("bam_ftp", "")),
            )
        )
    return tuple(rows)


def build_archive_project_catalog() -> tuple[AdnaArchiveProject, ...]:
    """Return the curated ENA project inventory for domesticated-animal aDNA intake."""
    catalog: list[AdnaArchiveProject] = []

    catalog.extend(
        _build_species_projects(
            "Equus caballus",
            (
                "PRJEB22390",
                "PRJEB44430",
                "PRJEB7537",
                "PRJEB10854",
                "PRJEB31613",
                "PRJEB19970",
                "PRJEB9799",
                "PRJEB56293",
            ),
            notes="Horse archive-backed aDNA studies identified for metadata-first intake review.",
        )
    )
    catalog.extend(
        _build_species_projects(
            "Ovis aries",
            (
                "PRJEB61808",
                "PRJEB69690",
                "PRJEB81145",
                "PRJEB59481",
                "PRJEB5933",
                "PRJEB43881",
                "PRJEB41594",
            ),
            notes="Sheep archive-backed aDNA studies identified for metadata-first intake review.",
        )
    )
    catalog.extend(
        _build_species_projects(
            "Sus scrofa domesticus",
            (
                "PRJEB30282",
                "PRJNA788987",
                "PRJNA878488",
                "PRJNA322309",
                "PRJNA1147173",
                "PRJNA994173",
                "PRJNA255085",
                "PRJEB79254",
                "PRJNA421430",
            ),
            notes="Pig archive-backed aDNA studies identified for metadata-first intake review.",
        )
    )
    catalog.extend(
        _build_species_projects(
            "Equus asinus",
            (
                "PRJEB50952",
                "PRJEB52849",
                "PRJNA143771",
                "PRJEB52590",
                "PRJEB43564",
            ),
            notes="Donkey comparator projects kept separate from horse support.",
        )
    )
    catalog.append(
        AdnaArchiveProject(
            species_latin_name="Equus asinus",
            project_accession="PRJEB55549",
            result_kind="analysis",
            metadata_url=build_ena_filereport_url("PRJEB55549", "analysis"),
            source_family="ENA",
            archive_status="curated_candidate",
            notes="Analysis-level donkey archive entry; requires explicit review before download-oriented use.",
        )
    )

    return tuple(catalog)


def build_species_archive_projects(species_name: str) -> tuple[AdnaArchiveProject, ...]:
    """Return the curated archive projects for one registered species."""
    species = resolve_species_definition(species_name)
    return tuple(
        row for row in build_archive_project_catalog() if row.species_latin_name == species.latin_name
    )


def _build_species_projects(
    species_latin_name: str,
    accessions: tuple[str, ...],
    *,
    notes: str,
) -> tuple[AdnaArchiveProject, ...]:
    return tuple(
        AdnaArchiveProject(
            species_latin_name=species_latin_name,
            project_accession=accession,
            result_kind="read_run",
            metadata_url=build_ena_filereport_url(accession, "read_run"),
            source_family="ENA",
            archive_status="curated_candidate",
            notes=notes,
        )
        for accession in accessions
    )


def _normalize_values(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(value.strip() for value in values if value.strip())


def _valid_selector(value: str) -> bool:
    return all(ch.isascii() and (ch.isalnum() or ch in {"_", "-", "."}) for ch in value)


def _filereport_fields(result_kind: str) -> tuple[str, ...]:
    if result_kind == "read_run":
        return (
            "study_accession",
            "sample_accession",
            "experiment_accession",
            "run_accession",
            "tax_id",
            "scientific_name",
            "library_layout",
            "library_source",
            "library_strategy",
            "instrument_model",
            "base_count",
            "read_count",
            "fastq_bytes",
            "fastq_ftp",
            "submitted_ftp",
            "sra_ftp",
        )
    return (
        "study_accession",
        "sample_accession",
        "experiment_accession",
        "analysis_accession",
        "analysis_type",
        "tax_id",
        "scientific_name",
        "submitted_ftp",
        "bam_ftp",
    )


def _required_headers(result_kind: str) -> tuple[str, ...]:
    if result_kind == "read_run":
        return (
            "study_accession",
            "sample_accession",
            "experiment_accession",
            "run_accession",
        )
    return (
        "study_accession",
        "sample_accession",
        "experiment_accession",
        "analysis_accession",
    )


def _validate_headers(headers: list[str], result_kind: str) -> None:
    missing = [name for name in _required_headers(result_kind) if name not in headers]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"ENA filereport payload is missing required columns: {names}")


def _opt_field(value: str) -> str | None:
    normalized = value.strip()
    if not normalized:
        return None
    return normalized


def _parse_optional_int(value: str, field_name: str, line_number: int) -> int | None:
    normalized = _opt_field(value)
    if normalized is None:
        return None
    try:
        return int(normalized)
    except ValueError as error:
        raise ValueError(
            f"ENA filereport row {line_number} has invalid {field_name} value {normalized!r}: {error}"
        ) from error


def _parse_int_list(value: str, field_name: str, line_number: int) -> tuple[int, ...]:
    out: list[int] = []
    for token in value.split(";"):
        normalized = token.strip()
        if not normalized:
            continue
        try:
            out.append(int(normalized))
        except ValueError as error:
            raise ValueError(
                f"ENA filereport row {line_number} has invalid {field_name} value {normalized!r}: {error}"
            ) from error
    return tuple(out)


def _split_field(value: str) -> tuple[str, ...]:
    return tuple(token.strip() for token in value.split(";") if token.strip())
