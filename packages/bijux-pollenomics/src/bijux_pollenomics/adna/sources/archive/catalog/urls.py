from __future__ import annotations

from ..ena import build_ena_filereport_url


def _metadata_url_for(
    *,
    accession: str,
    source_family: str,
    accession_scope: str,
    result_kind: str,
) -> str:
    if source_family == "ENA":
        return build_ena_filereport_url(accession, result_kind)
    if source_family == "SRA":
        return f"https://www.ncbi.nlm.nih.gov/sra?term={accession}"
    if source_family == "BioProject":
        return f"https://www.ncbi.nlm.nih.gov/bioproject/{accession}"
    if source_family == "GenBank":
        anchor = (
            accession.split("-", 1)[0]
            if accession_scope == "accession_range"
            else accession
        )
        return f"https://www.ncbi.nlm.nih.gov/nuccore/{anchor}"
    raise ValueError(f"Unsupported archive source family: {source_family}")
