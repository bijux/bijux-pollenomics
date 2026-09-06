"""Parse official ENA and article evidence for the Baltic ancient sheep."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import TypeVar
from xml.etree import ElementTree

from bijux_pollenomics.adna.workflow.source_artifacts import (
    read_source_artifact_bytes,
    resolve_source_artifact_path,
    source_artifact_exists,
)

PROJECT_ACCESSION = "PRJEB59481"
ENA_SAMPLE_SOURCE_DIRECTORY = (
    "data/adna/governance/source_library/projects/PRJEB59481/ena_samples"
)
ARTICLE_SOURCE_PATH = (
    "data/adna/governance/source_library/papers/10.1093-gbe-evae114/"
    "article_full_text.xml"
)
ARTICLE_TABLE_LOCATOR = ".//table-wrap[@id='evae114-T1']"
EXPECTED_SAMPLE_COUNT = 5
ARTICLE_DOI = "10.1093/gbe/evae114"
ARTICLE_PMCID = "PMC11162877"
ARTICLE_SOURCE_URL = (
    f"https://www.ebi.ac.uk/europepmc/webservices/rest/{ARTICLE_PMCID}/fullTextXML"
)
ARTICLE_LICENSE_NAME = "Creative Commons Attribution 4.0 International"
ARTICLE_LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
ENA_LICENSE_NAME = "EMBL-EBI Terms of Use"
ENA_LICENSE_URL = "https://www.ebi.ac.uk/about/terms-of-use/"
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

_EXPECTED_IDENTITIES = {
    "AKAS001": ("SAMEA112960291", "Kastelholm", "Åland", "Finland"),
    "AKAS002": ("SAMEA112960292", "Kastelholm", "Åland", "Finland"),
    "ASTF001": ("SAMEA112960293", "Stora Förvar", "Gotland", "Sweden"),
    "ASTF002": ("SAMEA112960294", "Stora Förvar", "Gotland", "Sweden"),
    "ASTF003": ("SAMEA112960295", "Stora Förvar", "Gotland", "Sweden"),
}
_EXPECTED_BY_ACCESSION = {
    accession: (sample_label, site_name, region_name, country_name)
    for sample_label, (
        accession,
        site_name,
        region_name,
        country_name,
    ) in _EXPECTED_IDENTITIES.items()
}
_EXPECTED_ENA_SOURCE_CLAIMS = {
    "SAMEA112960291": ("60.23", "20.08", "Sheep humerus excavated in Kastelholm"),
    "SAMEA112960292": ("60.23", "20.08", "Sheep humerus excavated in Kastelholm"),
    "SAMEA112960293": ("57.29", "17.97", "Sheep humerus excavated in Stora Förvar"),
    "SAMEA112960294": ("57.29", "17.97", "Sheep humerus excavated in Stora Förvar"),
    "SAMEA112960295": ("57.29", "17.97", "Sheep humerus excavated in Stora Förvar"),
}
_LAT_LON_RE = re.compile(
    r"(?P<latitude>[+-]?(?:\d+(?:\.\d+)?|\.\d+)),\s*"
    r"(?P<longitude>[+-]?(?:\d+(?:\.\d+)?|\.\d+))"
)
_DESCRIPTION_RE = re.compile(
    r"Sheep\s+(?P<material>.+?)\s+excavated\s+in\s+(?P<site>.+)",
    re.IGNORECASE,
)
_CAL_BP_RE = re.compile(
    r"(?P<older>\d{1,5})\s+to\s+(?P<younger>\d{1,5})\s+cal\s+BP"
    r"(?:\s+\((?P<laboratory_id>[^)]+)\))?",
    re.IGNORECASE,
)
_CE_RANGE_RE = re.compile(
    r"CE\s+(?P<start>\d{1,4})\s+to\s+(?P<end>\d{1,4})", re.IGNORECASE
)
_EXPECTED_ARTICLE_HEADER = (
    "Sample",
    "Site",
    "Autosomal coverage",
    "Median read length (bp)",
    "Sex",
    "Age (2σ, 95.4% probability)",
    "Mitochondrial haplotype",
)
_RowT = TypeVar("_RowT")


@dataclass(frozen=True)
class BalticSheepArchiveEvidence:
    """One ENA sample identity, coordinate pair, and material statement."""

    accession: str
    sample_label: str
    site_name: str
    latitude_text: str
    longitude_text: str
    material_claim: str
    description: str
    source_path: str
    source_locator: str
    description_source_locator: str


@dataclass(frozen=True)
class BalticSheepChronologyEvidence:
    """One article Table 1 chronology with explicit interval semantics."""

    sample_label: str
    site_name: str
    region_name: str
    source_text: str
    chronology_text: str
    younger_bp: int | None
    older_bp: int | None
    dating_basis: str
    evidence_class: str
    precision_posture: str
    contextual: bool
    source_path: str
    source_locator: str
    source_excerpt: str


@dataclass(frozen=True)
class BalticSheepMaterialEvidenceConflict:
    """Typed preservation of conflicting archive and supplement anatomy claims."""

    accession: str
    sample_label: str
    status: str
    archive_claim: str
    supplement_claim: str
    archive_source_path: str
    archive_source_locator: str
    supplement_source_path: str
    supplement_source_locator: str

    def as_dict(self) -> dict[str, str]:
        """Return the unresolved two-source claim without collapsing either side."""
        return {
            "accession": self.accession,
            "sample_label": self.sample_label,
            "status": self.status,
            "archive_claim": self.archive_claim,
            "supplement_claim": self.supplement_claim,
            "archive_source_path": self.archive_source_path,
            "archive_source_locator": self.archive_source_locator,
            "supplement_source_path": self.supplement_source_path,
            "supplement_source_locator": self.supplement_source_locator,
        }

    @property
    def note(self) -> str:
        """Render both claims without selecting or rewriting either source."""
        return (
            "material_evidence_conflict: ENA states "
            f"{self.archive_claim!r}; the paper supplement states "
            f"{self.supplement_claim!r}; neither claim supersedes the other."
        )


@dataclass(frozen=True)
class BalticSheepOfficialSampleEvidence:
    """One exact identity join across ENA sample XML and article Table 1."""

    archive: BalticSheepArchiveEvidence
    chronology: BalticSheepChronologyEvidence
    region_name: str
    country_name: str
    jurisdiction_basis: str
    jurisdiction_registry_id: str
    jurisdiction_registry_version: str
    jurisdiction_registry_path: str
    jurisdiction_registry_locator: str


@dataclass(frozen=True)
class BalticSheepEvidenceDenominator:
    """Evidence denominators proving a complete one-to-one five-sample join."""

    expected_sample_count: int
    ena_sample_count: int
    article_sample_count: int
    joined_sample_count: int


@dataclass(frozen=True)
class BalticSheepOfficialEvidenceBundle:
    """Validated official evidence plus its explicit completeness denominator."""

    samples: tuple[BalticSheepOfficialSampleEvidence, ...]
    denominator: BalticSheepEvidenceDenominator

    def by_accession(self) -> dict[str, BalticSheepOfficialSampleEvidence]:
        """Index samples by their exact ENA biological-sample accession."""
        return {row.archive.accession: row for row in self.samples}


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


def parse_baltic_sheep_ena_sample(
    payload: bytes,
    *,
    source_path: str,
    expected_accession: str,
) -> BalticSheepArchiveEvidence:
    """Parse one ENA XML record and enforce its immutable identity binding."""
    expected = _EXPECTED_BY_ACCESSION.get(expected_accession)
    if expected is None:
        raise ValueError(f"Unexpected Baltic sheep accession: {expected_accession}")
    sample_label, expected_site, _, _ = expected
    root = _parse_xml(payload, source_path=source_path)
    samples = root.findall("./SAMPLE")
    if len(samples) != 1:
        raise ValueError(
            f"Baltic sheep ENA source must contain exactly one SAMPLE: {source_path}"
        )
    sample = samples[0]
    accession = sample.attrib.get("accession", "").strip()
    alias = sample.attrib.get("alias", "").strip()
    primary_id = _required_text(sample, "./IDENTIFIERS/PRIMARY_ID", source_path)
    submitter_id = _required_text(sample, "./IDENTIFIERS/SUBMITTER_ID", source_path)
    title = _required_text(sample, "./TITLE", source_path)
    if {
        accession,
        primary_id,
    } != {expected_accession} or {alias, submitter_id, title} != {sample_label}:
        raise ValueError(
            "Baltic sheep ENA identity drift: "
            f"expected {expected_accession}/{sample_label}, observed "
            f"{accession}/{alias}/{primary_id}/{submitter_id}/{title}"
        )
    tax_id = _required_text(sample, "./SAMPLE_NAME/TAXON_ID", source_path)
    scientific_name = _required_text(
        sample, "./SAMPLE_NAME/SCIENTIFIC_NAME", source_path
    )
    if tax_id != "9940" or scientific_name != "Ovis aries":
        raise ValueError(f"Baltic sheep ENA taxonomy drift: {expected_accession}")
    description = _required_text(sample, "./DESCRIPTION", source_path)
    expected_latitude, expected_longitude, expected_description = (
        _EXPECTED_ENA_SOURCE_CLAIMS[expected_accession]
    )
    description_match = _DESCRIPTION_RE.fullmatch(description)
    if description_match is None:
        raise ValueError(
            f"Baltic sheep ENA description contract drift: {expected_accession}"
        )
    material_claim = description_match.group("material").strip()
    described_site = description_match.group("site").strip()
    if described_site != expected_site:
        raise ValueError(
            f"Baltic sheep ENA locality drift for {sample_label}: "
            f"{described_site!r} != {expected_site!r}"
        )
    if description != expected_description:
        raise ValueError(f"Baltic sheep ENA description drift: {expected_accession}")
    attributes = _sample_attributes(sample, source_path=source_path)
    lat_lon_values = attributes.get("lat_lon", ())
    if len(lat_lon_values) != 1:
        raise ValueError(
            f"Baltic sheep ENA lat_lon must occur exactly once: {expected_accession}"
        )
    coordinate_match = _LAT_LON_RE.fullmatch(lat_lon_values[0])
    if coordinate_match is None:
        raise ValueError(f"Baltic sheep ENA lat_lon is malformed: {expected_accession}")
    latitude_text = coordinate_match.group("latitude")
    longitude_text = coordinate_match.group("longitude")
    if (latitude_text, longitude_text) != (expected_latitude, expected_longitude):
        raise ValueError(f"Baltic sheep ENA coordinate drift: {expected_accession}")
    _validate_coordinate(latitude_text, minimum=Decimal(-90), maximum=Decimal(90))
    _validate_coordinate(longitude_text, minimum=Decimal(-180), maximum=Decimal(180))
    return BalticSheepArchiveEvidence(
        accession=accession,
        sample_label=sample_label,
        site_name=expected_site,
        latitude_text=latitude_text,
        longitude_text=longitude_text,
        material_claim=material_claim,
        description=description,
        source_path=source_path,
        source_locator=(
            f"./SAMPLE[@accession='{accession}']/SAMPLE_ATTRIBUTES/"
            "SAMPLE_ATTRIBUTE[TAG='lat_lon']"
        ),
        description_source_locator=f"./SAMPLE[@accession='{accession}']/DESCRIPTION",
    )


def parse_baltic_sheep_article_chronology(
    payload: bytes,
    *,
    source_path: str,
) -> tuple[BalticSheepChronologyEvidence, ...]:
    """Parse the five Table 1 chronology claims without broad-period invention."""
    root = _parse_xml(payload, source_path=source_path)
    doi = _required_text(
        root,
        "./front/article-meta/article-id[@pub-id-type='doi']",
        source_path,
    )
    pmcid = _required_text(
        root,
        "./front/article-meta/article-id[@pub-id-type='pmcid']",
        source_path,
    )
    if doi != ARTICLE_DOI or pmcid != ARTICLE_PMCID:
        raise ValueError(
            "Baltic sheep article identity drift: "
            f"observed DOI {doi!r} and PMCID {pmcid!r}"
        )
    licenses = root.findall("./front/article-meta/permissions/license")
    if len(licenses) != 1:
        raise ValueError("Baltic sheep article license statement is ambiguous")
    license_refs = [
        element
        for element in licenses[0].iter()
        if _xml_local_name(element.tag) == "license_ref"
    ]
    if (
        len(license_refs) != 1
        or _element_text(license_refs[0]) != ARTICLE_LICENSE_URL
        or license_refs[0].attrib.get("content-type") != "ccbylicense"
    ):
        raise ValueError("Baltic sheep article CC BY 4.0 license drift")
    availability_sections = root.findall(".//sec[@sec-type='data-availability']")
    if len(availability_sections) != 1:
        raise ValueError("Baltic sheep article data-availability statement is missing")
    availability_text = _element_text(availability_sections[0])
    if (
        "five new ancient individuals" not in availability_text
        or PROJECT_ACCESSION not in availability_text
    ):
        raise ValueError(
            "Baltic sheep article does not bind five individuals to PRJEB59481"
        )
    tables = root.findall(ARTICLE_TABLE_LOCATOR)
    if len(tables) != 1:
        raise ValueError("Baltic sheep article must contain Table 1 exactly once")
    table_wrap = tables[0]
    header = tuple(
        _element_text(cell) for cell in table_wrap.findall("./table/thead/tr/th")
    )
    if header != _EXPECTED_ARTICLE_HEADER:
        raise ValueError("Baltic sheep article Table 1 header drift")
    footnotes = {
        footnote.attrib.get("id", ""): _element_text(footnote)
        for footnote in table_wrap.findall("./table-wrap-foot/fn")
    }
    if footnotes.get("tblfn1") != "BP, before present (1950 CE).":
        raise ValueError("Baltic sheep article BP reference epoch is unavailable")
    if footnotes.get("tblfn2") != "aContextual dates.":
        raise ValueError("Baltic sheep article contextual-date footnote is unavailable")

    observed: dict[str, list[BalticSheepChronologyEvidence]] = {
        label: [] for label in _EXPECTED_IDENTITIES
    }
    for row_number, table_row in enumerate(
        table_wrap.findall("./table/tbody/tr"), start=1
    ):
        cells = table_row.findall("./td")
        if len(cells) != len(_EXPECTED_ARTICLE_HEADER):
            raise ValueError(
                f"Baltic sheep article Table 1 row {row_number} has column drift"
            )
        source_label = _element_text(cells[0])
        sample_label = _normalize_sample_label(source_label)
        if sample_label not in observed:
            raise ValueError(
                f"Baltic sheep article Table 1 has unexpected sample {source_label!r}"
            )
        _, expected_site, region_name, _ = _EXPECTED_IDENTITIES[sample_label]
        site_text = _element_text(cells[1])
        expected_site_text = f"{expected_site}, {region_name}"
        if site_text != expected_site_text:
            raise ValueError(
                f"Baltic sheep article locality drift for {sample_label}: "
                f"{site_text!r} != {expected_site_text!r}"
            )
        age_cell = cells[5]
        contextual_xrefs = [
            xref
            for xref in age_cell.findall(".//xref")
            if xref.attrib.get("ref-type") == "table-fn"
            and xref.attrib.get("rid") == "tblfn2"
        ]
        contextual = bool(contextual_xrefs)
        source_text = _chronology_cell_text(age_cell, contextual_xrefs)
        observed[sample_label].append(
            _parse_article_chronology_claim(
                sample_label=sample_label,
                site_name=expected_site,
                region_name=region_name,
                source_text=source_text,
                contextual=contextual,
                source_path=source_path,
                row_number=row_number,
            )
        )
    malformed = {label: len(rows) for label, rows in observed.items() if len(rows) != 1}
    if malformed:
        raise ValueError(
            f"Baltic sheep article identities must occur exactly once: {malformed}"
        )
    return tuple(observed[label][0] for label in _EXPECTED_IDENTITIES)


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


def _parse_article_chronology_claim(
    *,
    sample_label: str,
    site_name: str,
    region_name: str,
    source_text: str,
    contextual: bool,
    source_path: str,
    row_number: int,
) -> BalticSheepChronologyEvidence:
    younger_bp: int | None
    older_bp: int | None
    dating_basis: str
    evidence_class: str
    precision_posture: str
    chronology_text: str
    if match := _CAL_BP_RE.fullmatch(source_text):
        if contextual:
            raise ValueError(
                f"Direct Baltic sheep date unexpectedly marked contextual: {sample_label}"
            )
        older_bp = int(match.group("older"))
        younger_bp = int(match.group("younger"))
        if younger_bp > older_bp:
            raise ValueError(
                f"Baltic sheep BP interval direction is inverted: {sample_label}"
            )
        chronology_text = f"{younger_bp}-{older_bp} BP"
        dating_basis = "radiocarbon"
        evidence_class = "direct_radiocarbon_date"
        precision_posture = "sample_precise_interval"
    elif source_text == "Late Neolithic":
        if sample_label != "ASTF003" or not contextual:
            raise ValueError(
                "Broad Baltic sheep chronology is not bound to ASTF003 context"
            )
        younger_bp = older_bp = None
        chronology_text = source_text
        dating_basis = "archaeological_period_assignment"
        evidence_class = "broad_period_label"
        precision_posture = "broad_period_only"
    elif match := _CE_RANGE_RE.fullmatch(source_text):
        if sample_label != "AKAS002" or not contextual:
            raise ValueError(
                "CE Baltic sheep chronology is not bound to AKAS002 context"
            )
        start_ce = int(match.group("start"))
        end_ce = int(match.group("end"))
        if start_ce > end_ce or end_ce > 1950:
            raise ValueError(f"Baltic sheep CE interval is invalid: {sample_label}")
        younger_bp = 1950 - end_ce
        older_bp = 1950 - start_ce
        chronology_text = f"{younger_bp}-{older_bp} BP"
        dating_basis = "archaeological_context"
        evidence_class = "archaeological_context_date"
        precision_posture = "contextual_interval"
    else:
        raise ValueError(
            f"Unsupported Baltic sheep chronology wording for {sample_label}: "
            f"{source_text!r}"
        )
    return BalticSheepChronologyEvidence(
        sample_label=sample_label,
        site_name=site_name,
        region_name=region_name,
        source_text=source_text,
        chronology_text=chronology_text,
        younger_bp=younger_bp,
        older_bp=older_bp,
        dating_basis=dating_basis,
        evidence_class=evidence_class,
        precision_posture=precision_posture,
        contextual=contextual,
        source_path=source_path,
        source_locator=(f"{ARTICLE_TABLE_LOCATOR}/table/tbody/tr[{row_number}]/td[6]"),
        source_excerpt=f"{sample_label} | {site_name}, {region_name} | {source_text}",
    )


def _parse_xml(payload: bytes, *, source_path: str) -> ElementTree.Element:
    try:
        return ElementTree.fromstring(payload)
    except ElementTree.ParseError as error:
        raise ValueError(f"Malformed XML source: {source_path}") from error


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
        raise ValueError(
            f"Official source receipt must be an object: {repository_path}"
        )

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


def _required_text(
    element: ElementTree.Element, selector: str, source_path: str
) -> str:
    matches = element.findall(selector)
    if len(matches) != 1:
        raise ValueError(f"Required XML field is missing or ambiguous: {source_path}")
    value = _element_text(matches[0])
    if not value:
        raise ValueError(f"Required XML field is empty: {source_path}")
    return value


def _sample_attributes(
    sample: ElementTree.Element, *, source_path: str
) -> dict[str, tuple[str, ...]]:
    values: dict[str, list[str]] = {}
    for attribute in sample.findall("./SAMPLE_ATTRIBUTES/SAMPLE_ATTRIBUTE"):
        tag = _required_text(attribute, "./TAG", source_path)
        value = _required_text(attribute, "./VALUE", source_path)
        values.setdefault(tag, []).append(value)
    return {tag: tuple(items) for tag, items in values.items()}


def _validate_coordinate(value: str, *, minimum: Decimal, maximum: Decimal) -> None:
    try:
        coordinate = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"Invalid Baltic sheep coordinate: {value!r}") from error
    if coordinate < minimum or coordinate > maximum:
        raise ValueError(f"Baltic sheep coordinate outside WGS84 bounds: {value!r}")


def _element_text(element: ElementTree.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _xml_local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]


def _chronology_cell_text(
    age_cell: ElementTree.Element,
    contextual_xrefs: list[ElementTree.Element],
) -> str:
    text = _element_text(age_cell)
    for xref in contextual_xrefs:
        marker = _element_text(xref)
        if not marker or not text.endswith(marker):
            raise ValueError("Baltic sheep contextual marker cannot be isolated")
        text = text[: -len(marker)].rstrip()
    return text


def _normalize_sample_label(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


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
