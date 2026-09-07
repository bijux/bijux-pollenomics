"""Parse official ENA and article evidence for the Baltic ancient sheep."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import TypeVar

from bijux_pollenomics.adna.workflow.source_artifacts import (
    read_source_artifact_bytes,
    resolve_source_artifact_path,
    source_artifact_exists,
)

from .evidence_models import (
    BalticSheepArchiveEvidence as BalticSheepArchiveEvidence,
)
from .evidence_models import (
    BalticSheepChronologyEvidence as BalticSheepChronologyEvidence,
)
from .evidence_models import (
    BalticSheepEvidenceDenominator as BalticSheepEvidenceDenominator,
)
from .evidence_models import (
    BalticSheepMaterialEvidenceConflict as BalticSheepMaterialEvidenceConflict,
)
from .evidence_models import (
    BalticSheepOfficialEvidenceBundle as BalticSheepOfficialEvidenceBundle,
)
from .evidence_models import (
    BalticSheepOfficialSampleEvidence as BalticSheepOfficialSampleEvidence,
)
from .source_parsing import (
    _CAL_BP_RE as _CAL_BP_RE,
)
from .source_parsing import (
    _CE_RANGE_RE as _CE_RANGE_RE,
)
from .source_parsing import (
    _DESCRIPTION_RE as _DESCRIPTION_RE,
)
from .source_parsing import (
    _EXPECTED_ARTICLE_HEADER as _EXPECTED_ARTICLE_HEADER,
)
from .source_parsing import (
    _EXPECTED_BY_ACCESSION as _EXPECTED_BY_ACCESSION,
)
from .source_parsing import (
    _EXPECTED_ENA_SOURCE_CLAIMS as _EXPECTED_ENA_SOURCE_CLAIMS,
)
from .source_parsing import (
    _EXPECTED_IDENTITIES as _EXPECTED_IDENTITIES,
)
from .source_parsing import (
    _LAT_LON_RE as _LAT_LON_RE,
)
from .source_parsing import (
    ARTICLE_DOI as ARTICLE_DOI,
)
from .source_parsing import (
    ARTICLE_LICENSE_NAME as ARTICLE_LICENSE_NAME,
)
from .source_parsing import (
    ARTICLE_LICENSE_URL as ARTICLE_LICENSE_URL,
)
from .source_parsing import (
    ARTICLE_PMCID as ARTICLE_PMCID,
)
from .source_parsing import (
    ARTICLE_SOURCE_PATH as ARTICLE_SOURCE_PATH,
)
from .source_parsing import (
    ARTICLE_SOURCE_URL as ARTICLE_SOURCE_URL,
)
from .source_parsing import (
    ARTICLE_TABLE_LOCATOR as ARTICLE_TABLE_LOCATOR,
)
from .source_parsing import (
    ENA_LICENSE_NAME as ENA_LICENSE_NAME,
)
from .source_parsing import (
    ENA_LICENSE_URL as ENA_LICENSE_URL,
)
from .source_parsing import (
    ENA_SAMPLE_SOURCE_DIRECTORY as ENA_SAMPLE_SOURCE_DIRECTORY,
)
from .source_parsing import (
    EXPECTED_SAMPLE_COUNT as EXPECTED_SAMPLE_COUNT,
)
from .source_parsing import (
    PROJECT_ACCESSION as PROJECT_ACCESSION,
)
from .source_parsing import (
    _chronology_cell_text as _chronology_cell_text,
)
from .source_parsing import (
    _element_text as _element_text,
)
from .source_parsing import (
    _normalize_sample_label as _normalize_sample_label,
)
from .source_parsing import (
    _parse_article_chronology_claim as _parse_article_chronology_claim,
)
from .source_parsing import (
    _parse_xml as _parse_xml,
)
from .source_parsing import (
    _required_text as _required_text,
)
from .source_parsing import (
    _sample_attributes as _sample_attributes,
)
from .source_parsing import (
    _validate_coordinate as _validate_coordinate,
)
from .source_parsing import (
    _xml_local_name as _xml_local_name,
)
from .source_parsing import (
    _XmlElement as _XmlElement,
)
from .source_parsing import (
    parse_baltic_sheep_article_chronology as parse_baltic_sheep_article_chronology,
)
from .source_parsing import (
    parse_baltic_sheep_ena_sample as parse_baltic_sheep_ena_sample,
)

for _compatibility_object in (
    BalticSheepArchiveEvidence,
    BalticSheepChronologyEvidence,
    BalticSheepEvidenceDenominator,
    BalticSheepMaterialEvidenceConflict,
    BalticSheepOfficialEvidenceBundle,
    BalticSheepOfficialSampleEvidence,
    parse_baltic_sheep_article_chronology,
    parse_baltic_sheep_ena_sample,
    _parse_xml,
):
    _compatibility_object.__module__ = __name__
del _compatibility_object

_SOURCE_LIBRARY_SCHEMA_VERSION = "adna-source-library.v1"
BALTIC_SHEEP_JURISDICTION_REGISTRY_ID = "baltic-sheep-region-country.v1"
BALTIC_SHEEP_JURISDICTION_REGISTRY_VERSION = "1.0.0"
BALTIC_SHEEP_JURISDICTION_REGISTRY_PATH = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/adna/projects/"
    "sample_master/tables/baltic_sheep/official_evidence.py"
)
BALTIC_SHEEP_JURISDICTION_ASSIGNMENTS: Mapping[str, str] = MappingProxyType(
    {"Åland": "Finland", "Gotland": "Sweden"}
)

_RowT = TypeVar("_RowT")


def load_baltic_sheep_official_evidence(
    output_root: Path,
) -> BalticSheepOfficialEvidenceBundle:
    """Load and reconcile the five pinned official source records."""
    output_root = Path(output_root)
    archive_rows: list[BalticSheepArchiveEvidence] = []
    for accession in _EXPECTED_BY_ACCESSION:
        repository_path = f"{ENA_SAMPLE_SOURCE_DIRECTORY}/{accession}.xml"
        payload = read_receipted_baltic_sheep_official_source(
            output_root, repository_path=repository_path
        )
        archive_rows.append(
            parse_baltic_sheep_ena_sample(
                payload,
                source_path=repository_path,
                expected_accession=accession,
            )
        )
    article_payload = read_receipted_baltic_sheep_official_source(
        output_root, repository_path=ARTICLE_SOURCE_PATH
    )
    chronology_rows = parse_baltic_sheep_article_chronology(
        article_payload,
        source_path=ARTICLE_SOURCE_PATH,
    )
    return reconcile_baltic_sheep_official_evidence(
        tuple(archive_rows), chronology_rows
    )


def baltic_sheep_official_evidence_available(output_root: Path) -> bool:
    """Return whether every pinned XML source needed for the join is present."""
    output_root = Path(output_root)
    paths = (
        _data_path(output_root, ARTICLE_SOURCE_PATH),
        *(
            _data_path(
                output_root,
                f"{ENA_SAMPLE_SOURCE_DIRECTORY}/{accession}.xml",
            )
            for accession in _EXPECTED_BY_ACCESSION
        ),
    )
    return all(source_artifact_exists(path) for path in paths)


def reconcile_baltic_sheep_official_evidence(
    archive_rows: tuple[BalticSheepArchiveEvidence, ...],
    chronology_rows: tuple[BalticSheepChronologyEvidence, ...],
) -> BalticSheepOfficialEvidenceBundle:
    """Require an exact one-to-one accession, label, site, region, and country join."""
    if len(archive_rows) != EXPECTED_SAMPLE_COUNT:
        raise ValueError("Baltic sheep ENA evidence denominator drift")
    if len(chronology_rows) != EXPECTED_SAMPLE_COUNT:
        raise ValueError("Baltic sheep article evidence denominator drift")
    archive_by_label = _unique_by_label(archive_rows, source_name="ENA")
    chronology_by_label = _unique_by_label(chronology_rows, source_name="article")
    if set(archive_by_label) != set(_EXPECTED_IDENTITIES):
        raise ValueError("Baltic sheep ENA sample identity set drift")
    if set(chronology_by_label) != set(_EXPECTED_IDENTITIES):
        raise ValueError("Baltic sheep article sample identity set drift")
    joined: list[BalticSheepOfficialSampleEvidence] = []
    site_coordinates: dict[tuple[str, str, str], tuple[str, str]] = {}
    for sample_label, (expected_accession, _, _, _) in _EXPECTED_IDENTITIES.items():
        archive = archive_by_label[sample_label]
        chronology = chronology_by_label[sample_label]
        if archive.accession != expected_accession:
            raise ValueError(f"Baltic sheep accession drift for {sample_label}")
        _, expected_site, expected_region, expected_country = _EXPECTED_IDENTITIES[
            sample_label
        ]
        governed_country = BALTIC_SHEEP_JURISDICTION_ASSIGNMENTS.get(expected_region)
        if governed_country is None or governed_country != expected_country:
            raise ValueError(
                f"Baltic sheep jurisdiction registry drift for {sample_label}"
            )
        if (
            archive.site_name != chronology.site_name
            or archive.site_name != expected_site
        ):
            raise ValueError(
                f"Baltic sheep source locality conflict for {sample_label}"
            )
        if chronology.region_name != expected_region:
            raise ValueError(f"Baltic sheep article region conflict for {sample_label}")
        governed_place = (expected_site, expected_region, expected_country)
        coordinate = (archive.latitude_text, archive.longitude_text)
        prior_coordinate = site_coordinates.setdefault(governed_place, coordinate)
        if prior_coordinate != coordinate:
            raise ValueError(
                f"Baltic sheep samples disagree on coordinates for {archive.site_name}"
            )
        joined.append(
            BalticSheepOfficialSampleEvidence(
                archive=archive,
                chronology=chronology,
                region_name=expected_region,
                country_name=governed_country,
                jurisdiction_basis="governed_region_to_country_assignment",
                jurisdiction_registry_id=BALTIC_SHEEP_JURISDICTION_REGISTRY_ID,
                jurisdiction_registry_version=(
                    BALTIC_SHEEP_JURISDICTION_REGISTRY_VERSION
                ),
                jurisdiction_registry_path=BALTIC_SHEEP_JURISDICTION_REGISTRY_PATH,
                jurisdiction_registry_locator=(
                    f"BALTIC_SHEEP_JURISDICTION_ASSIGNMENTS[{expected_region!r}]"
                ),
            )
        )
    denominator = BalticSheepEvidenceDenominator(
        expected_sample_count=EXPECTED_SAMPLE_COUNT,
        ena_sample_count=len(archive_rows),
        article_sample_count=len(chronology_rows),
        joined_sample_count=len(joined),
    )
    if len(joined) != EXPECTED_SAMPLE_COUNT:
        raise ValueError("Baltic sheep official evidence join denominator drift")
    return BalticSheepOfficialEvidenceBundle(tuple(joined), denominator)


def build_baltic_sheep_material_conflict(
    *,
    official_evidence: BalticSheepOfficialSampleEvidence,
    supplement_claim: str,
    supplement_source_path: str,
    supplement_source_locator: str,
) -> BalticSheepMaterialEvidenceConflict:
    """Preserve source disagreement rather than silently selecting one anatomy."""
    archive_claim = official_evidence.archive.material_claim.strip()
    supplement_claim = supplement_claim.strip()
    if not archive_claim or not supplement_claim:
        raise ValueError("Baltic sheep material comparison requires both source claims")
    if "humerus" not in archive_claim.casefold():
        raise ValueError("Baltic sheep ENA material claim is no longer humerus")
    if "right radius" not in supplement_claim.casefold():
        raise ValueError(
            "Baltic sheep supplement material claim is no longer right radius"
        )
    return BalticSheepMaterialEvidenceConflict(
        accession=official_evidence.archive.accession,
        sample_label=official_evidence.archive.sample_label,
        status="source_disagreement_unresolved",
        archive_claim=archive_claim,
        supplement_claim=supplement_claim,
        archive_source_path=official_evidence.archive.source_path,
        archive_source_locator=official_evidence.archive.description_source_locator,
        supplement_source_path=supplement_source_path,
        supplement_source_locator=supplement_source_locator,
    )


def _data_path(output_root: Path, repository_path: str) -> Path:
    return Path(output_root) / repository_path.removeprefix("data/")


def read_receipted_baltic_sheep_official_source(
    output_root: Path, *, repository_path: str
) -> bytes:
    """Validate one governed Baltic-sheep receipt before returning source bytes."""
    if repository_path == ARTICLE_SOURCE_PATH:
        return _read_receipted_official_source(
            output_root,
            repository_path=repository_path,
            expected_source_url=ARTICLE_SOURCE_URL,
            expected_artifact_kind="article_full_text_xml",
            expected_identity={"paper_doi": ARTICLE_DOI, "pmcid": ARTICLE_PMCID},
            expected_license_name=ARTICLE_LICENSE_NAME,
            expected_license_url=ARTICLE_LICENSE_URL,
        )
    source_prefix = f"{ENA_SAMPLE_SOURCE_DIRECTORY}/"
    if repository_path.startswith(source_prefix) and repository_path.endswith(".xml"):
        accession = Path(repository_path).stem
        if accession in _EXPECTED_BY_ACCESSION:
            return _read_receipted_official_source(
                output_root,
                repository_path=repository_path,
                expected_source_url=(
                    f"https://www.ebi.ac.uk/ena/browser/api/xml/{accession}"
                ),
                expected_artifact_kind="ena_sample_xml",
                expected_identity={
                    "project_accession": PROJECT_ACCESSION,
                    "sample_accession": accession,
                },
                expected_license_name=ENA_LICENSE_NAME,
                expected_license_url=ENA_LICENSE_URL,
            )
    raise ValueError(f"Unexpected Baltic sheep official source: {repository_path}")


def _read_receipted_official_source(
    output_root: Path,
    *,
    repository_path: str,
    expected_source_url: str,
    expected_artifact_kind: str,
    expected_identity: dict[str, str],
    expected_license_name: str,
    expected_license_url: str,
) -> bytes:
    """Read official bytes only after their adjacent receipt reconciles exactly."""
    logical_path = _data_path(output_root, repository_path)
    payload = read_source_artifact_bytes(logical_path)
    stored_path = resolve_source_artifact_path(logical_path)
    receipt_path = logical_path.with_suffix(logical_path.suffix + ".metadata.json")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise ValueError(
            f"Official source receipt is missing or invalid: {repository_path}"
        ) from error
    if not isinstance(receipt, dict):
        raise TypeError(f"Official source receipt must be an object: {repository_path}")

    expected_receipt_values: dict[str, object] = {
        "schema_version": _SOURCE_LIBRARY_SCHEMA_VERSION,
        "source_url": expected_source_url,
        "artifact_kind": expected_artifact_kind,
        "byte_size": len(payload),
        "content_sha256": hashlib.sha256(payload).hexdigest(),
        "storage_byte_size": stored_path.stat().st_size,
        "storage_sha256": hashlib.sha256(stored_path.read_bytes()).hexdigest(),
        "storage_path": str(stored_path.relative_to(output_root)),
        "content_encoding": "gzip" if stored_path.suffix == ".gz" else None,
        "license_name": expected_license_name,
        "license_url": expected_license_url,
        **expected_identity,
    }
    mismatches = {
        field: (expected, receipt.get(field))
        for field, expected in expected_receipt_values.items()
        if receipt.get(field) != expected
    }
    content_type = receipt.get("content_type")
    if not isinstance(content_type, str) or "xml" not in content_type.casefold():
        mismatches["content_type"] = ("XML media type", content_type)
    retrieved_at_utc = receipt.get("retrieved_at_utc")
    if not isinstance(retrieved_at_utc, str) or not retrieved_at_utc.strip():
        mismatches["retrieved_at_utc"] = (
            "nonempty retrieval timestamp",
            retrieved_at_utc,
        )
    if mismatches:
        details = ", ".join(
            f"{field}: expected {expected!r}, observed {observed!r}"
            for field, (expected, observed) in sorted(mismatches.items())
        )
        raise ValueError(
            f"Official source receipt does not reconcile for {repository_path}: {details}"
        )
    return payload


def _unique_by_label(rows: tuple[_RowT, ...], *, source_name: str) -> dict[str, _RowT]:
    indexed: dict[str, _RowT] = {}
    for row in rows:
        label = str(getattr(row, "sample_label", ""))
        if not label or label in indexed:
            raise ValueError(
                f"Baltic sheep {source_name} sample labels are missing or duplicated"
            )
        indexed[label] = row
    return indexed
