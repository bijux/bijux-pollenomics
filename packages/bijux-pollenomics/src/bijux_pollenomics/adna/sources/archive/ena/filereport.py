from __future__ import annotations

from .models import ADNA_ENA_RESULT_KINDS, AdnaEnaQuery, AdnaEnaRecord


_ENA_API_BASE = "https://www.ebi.ac.uk/ena/portal/api/filereport"


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
                base_count=_parse_optional_int(
                    row.get("base_count", ""), "base_count", line_number
                ),
                read_count=_parse_optional_int(
                    row.get("read_count", ""), "read_count", line_number
                ),
                fastq_bytes=_parse_int_list(
                    row.get("fastq_bytes", ""), "fastq_bytes", line_number
                ),
                fastq_ftp=_split_field(row.get("fastq_ftp", "")),
                submitted_ftp=_split_field(row.get("submitted_ftp", "")),
                sra_ftp=_split_field(row.get("sra_ftp", "")),
                bam_ftp=_split_field(row.get("bam_ftp", "")),
            )
        )
    return tuple(rows)


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
