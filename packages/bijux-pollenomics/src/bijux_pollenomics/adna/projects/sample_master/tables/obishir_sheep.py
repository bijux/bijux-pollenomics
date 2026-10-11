"""Source-owned specimen aliases and site evidence for Obishir V genomes."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

from bijux_pollenomics.adna.projects.registry.archive_samples import (
    read_archive_project_samples,
)
from bijux_pollenomics.adna.sources.library import ADNA_SOURCE_LIBRARY_DIR
from bijux_pollenomics.adna.workflow.source_artifacts import (
    read_source_artifact_bytes,
)
from bijux_pollenomics.core.xml_security import parse_hardened_xml

from ..models import AdnaProjectSampleMasterRow

_ALIASES = {
    "SAMEA8022720": ("OB20-01", "Ovis aries"),
    "SAMEA8022721": ("OB20-06", "Ovis aries"),
    "SAMEA8022722": ("OB21-04", "Capra hircus"),
    "SAMEA8022723": ("OB21-06", "Ovis aries"),
    "SAMEA8022724": ("OB20-04", "Ovis aries"),
}
_REPORTING_SUMMARY = (
    f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41562-021-01083-y/"
    "supplementary/41562_2021_1083_MOESM2_ESM.pdf"
)
_REPORTING_SUMMARY_SHA256 = (
    "f99a65b2b80618c64bff71f29f415de9207ba4f2775127b5e752168bd8fb440f"
)
_RADIOCARBON_SUPPLEMENT = (
    f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41562-021-01083-y/"
    "supplementary/41562_2021_1083_MOESM1_ESM.pdf"
)
_RADIOCARBON_SUPPLEMENT_SHA256 = (
    "d6fcdfae2d835883c68585aa6ff87ad197cc8561c434f654099322fefeb156a9"
)
# Table 2 identifies these teeth by the specimen number inside the context label.
# The starred 20.4 measurement is stratigraphically inconsistent in the source.
_DIRECT_DATES = {
    "SAMEA8022721": ("20.6", "7012 ± 45 14C BP", "5991-5771 cal BCE", "AA-114606"),
    "SAMEA8022722": ("21.4", "2796 ± 34 14C BP", "1045-835 cal BCE", "AA-114608"),
    "SAMEA8022724": ("20.4", "4260 ± 36 14C BP*", "3003-2701 cal BCE", "AA-114607"),
}


def obishir_chronology_evidence(
    accession: str,
) -> tuple[str, str, str] | None:
    """Return the exact Table 2 provenance for a directly dated specimen."""
    date = _DIRECT_DATES.get(accession)
    if date is None:
        return None
    specimen, radiocarbon, calibrated, lab = date
    warning = (
        "; source marks the measurement stratigraphically inconsistent"
        if specimen == "20.4"
        else ""
    )
    return (
        _RADIOCARBON_SUPPLEMENT,
        f"Supplementary Table 2 p. 11, context ({specimen}), lab {lab}",
        f"Obishir V tooth ({specimen}): {radiocarbon}; {calibrated} (2 sigma){warning}.",
    )


def parse_obishir_ena_sample(payload: bytes, *, accession: str) -> tuple[str, str]:
    """Refuse any BioSample whose source-owned alias or species changes."""
    if accession not in _ALIASES:
        raise ValueError(f"Unexpected Obishir V BioSample: {accession}")
    alias, species = _ALIASES[accession]
    root = parse_hardened_xml(payload)
    samples = root.findall("./SAMPLE")
    if root.tag != "SAMPLE_SET" or len(samples) != 1:
        raise ValueError(f"Obishir V ENA sample count changed: {accession}")
    sample = samples[0]
    taxonomy = {
        attribute.findtext("TAG"): attribute.findtext("VALUE")
        for attribute in sample.findall("./SAMPLE_ATTRIBUTES/SAMPLE_ATTRIBUTE")
    }
    if (
        sample.get("accession") != accession
        or sample.get("alias") != alias
        or sample.findtext("TITLE") != alias
        or taxonomy.get("scientific_name") != species
    ):
        raise ValueError(f"Obishir V sample identity changed: {accession}")
    return alias, species


def build_obishir_sample_rows(
    output_root: Path,
    archive_rows: tuple[AdnaProjectSampleMasterRow, ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Join the five ENA BioSamples to paper specimen aliases and site scope."""
    output_root = Path(output_root)
    report_path = output_root / _REPORTING_SUMMARY.removeprefix("data/")
    if sha256(report_path.read_bytes()).hexdigest() != _REPORTING_SUMMARY_SHA256:
        raise ValueError("Obishir V specimen-provenance supplement changed")
    date_path = output_root / _RADIOCARBON_SUPPLEMENT.removeprefix("data/")
    if sha256(date_path.read_bytes()).hexdigest() != _RADIOCARBON_SUPPLEMENT_SHA256:
        raise ValueError("Obishir V radiocarbon supplement changed")
    archive_path = (
        output_root
        / "adna/governance/source_library/projects/PRJEB41594/archive_metadata.html"
    )
    archive_samples = read_archive_project_samples(archive_path)
    if {row.archive_native_sample_id for row in archive_samples} != set(_ALIASES):
        raise ValueError("Obishir V archive sample population changed")
    if {row.archive_native_sample_id for row in archive_rows} != set(_ALIASES):
        raise ValueError("Obishir V sample-master population changed")

    result = []
    for row in archive_rows:
        accession = row.archive_native_sample_id
        relative = (
            f"{ADNA_SOURCE_LIBRARY_DIR}/projects/PRJEB41594/ena_samples/{accession}.xml"
        )
        logical_path = output_root / relative.removeprefix("data/")
        payload = read_source_artifact_bytes(logical_path)
        receipt_path = logical_path.with_suffix(".xml.metadata.json")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if (
            receipt.get("content_sha256") != sha256(payload).hexdigest()
            or receipt.get("sample_accession") != accession
            or receipt.get("source_url")
            != f"https://www.ebi.ac.uk/ena/browser/api/xml/{accession}"
        ):
            raise ValueError(f"Obishir V ENA receipt changed: {accession}")
        alias, species = parse_obishir_ena_sample(payload, accession=accession)
        if row.source_native_scientific_name != species:
            raise ValueError(f"Obishir V sample identity changed: {accession}")
        direct_date = _DIRECT_DATES.get(accession)
        result.append(
            replace(
                row,
                species_latin_name=species,
                species_common_name="goat" if species == "Capra hircus" else "sheep",
                paper_native_sample_label=alias,
                preferred_sample_label=alias,
                sample_lineage_path=f"{relative} || {_REPORTING_SUMMARY}",
                sample_lineage_locator=(
                    f"SAMPLE[@accession='{accession}']/@alias || "
                    "Reporting Summary p. 3, Specimen provenance"
                ),
                sample_lineage_excerpt=(
                    f"ENA BioSample {accession} has specimen alias {alias}; "
                    "the paper reporting summary assigns all study specimens "
                    "to Obishir V."
                ),
                locality_text="Obishir V",
                political_entity="Kyrgyzstan",
                chronology_text="" if direct_date is None else direct_date[2],
                chronology_dating_basis="" if direct_date is None else "radiocarbon",
                chronology_evidence_class=(
                    "" if direct_date is None else "direct_radiocarbon_date"
                ),
                chronology_precision_posture=(
                    "" if direct_date is None else "sample_precise_interval"
                ),
            )
        )
    return tuple(result)
