"""Boundary and ancient-DNA country evidence derivation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

from ..constants import INPUT_PATHS, CountryCoverageError
from ..decoding import _country_code, _integer, _required_text, _rows
from .partitions import EvidenceMap, _empty_counts, _record_partition


def add_boundary_evidence(
    evidence: EvidenceMap, boundary_counts: Mapping[str, int]
) -> None:
    _record_partition(evidence, "boundaries", "source_reported", boundary_counts)
    _record_partition(evidence, "boundaries", "governed_assignment", boundary_counts)
    _record_partition(
        evidence, "boundaries", "publication", boundary_counts, published=True
    )


def add_aadr_evidence(
    evidence: EvidenceMap, documents: Mapping[str, Mapping[str, object]]
) -> None:
    for country, path in (
        ("SE", INPUT_PATHS[10]),
        ("DK", INPUT_PATHS[11]),
        ("NO", INPUT_PATHS[12]),
        ("FI", INPUT_PATHS[13]),
    ):
        summary = documents[path]
        if _country_code(summary.get("country")) != country:
            raise CountryCoverageError(
                f"AADR summary country identity does not match partition: {country}"
            )
        evidence[("aadr", "publication", country)] = {
            **_empty_counts(),
            "published_records": _integer(
                summary.get("total_unique_samples"), "AADR samples"
            ),
            "sites": _integer(
                summary.get("total_unique_localities"), "AADR localities"
            ),
            "samples": _integer(summary.get("total_unique_samples"), "AADR samples"),
        }


def add_animal_adna_evidence(
    evidence: EvidenceMap, documents: Mapping[str, Mapping[str, object]]
) -> None:
    animal_document = documents[INPUT_PATHS[14]]
    if animal_document.get("schema_version") != "animal-country-species-coverage.v2":
        raise CountryCoverageError("animal coverage schema version is unsupported")
    animal_rows = _rows(animal_document, "animal coverage")
    animal_counts: Counter[str] = Counter()
    animal_sites: Counter[str] = Counter()
    animal_identities: set[tuple[str, str, str]] = set()
    for row in animal_rows:
        country = _country_code(row.get("country"))
        identity = (
            country,
            _required_text(row, "species_latin_name"),
            _required_text(row, "animal_scope"),
        )
        if identity in animal_identities:
            raise CountryCoverageError(
                "animal coverage contains duplicate evidence row"
            )
        animal_identities.add(identity)
        mapped_samples = _integer(
            row.get("mapped_sample_count"), "animal mapped samples"
        )
        sample_rows = _integer(row.get("sample_row_count"), "animal sample rows")
        unresolved_samples = _integer(
            row.get("unresolved_sample_count"), "animal unresolved samples"
        )
        exact_samples = _integer(
            row.get("exact_coordinate_sample_count"), "animal exact samples"
        )
        approximate_samples = _integer(
            row.get("approximate_coordinate_sample_count"),
            "animal approximate samples",
        )
        direct_coordinate_samples = _integer(
            row.get("direct_coordinate_sample_count"),
            "animal direct-coordinate samples",
        )
        geocoded_coordinate_samples = _integer(
            row.get("geocoded_coordinate_sample_count"),
            "animal geocoded-coordinate samples",
        )
        mapped_localities = _integer(
            row.get("mapped_locality_count"), "animal mapped localities"
        )
        if sample_rows != mapped_samples + unresolved_samples:
            raise CountryCoverageError("animal sample disposition does not reconcile")
        if mapped_samples != exact_samples + approximate_samples:
            raise CountryCoverageError("animal coordinate evidence does not reconcile")
        if mapped_samples != (direct_coordinate_samples + geocoded_coordinate_samples):
            raise CountryCoverageError(
                "animal mapped coordinate-basis evidence does not reconcile"
            )
        for field in (
            "sample_lineage_backed_sample_count",
            "site_evidence_backed_sample_count",
            "chronology_provenance_backed_sample_count",
            "coordinate_provenance_backed_sample_count",
        ):
            if _integer(row.get(field), f"animal {field}") != mapped_samples:
                raise CountryCoverageError("animal provenance totals do not reconcile")
        animal_counts[country] += mapped_samples
        animal_sites[country] += mapped_localities
    animal_partitions = ("SE", "DK", "NO", "FI") + tuple(
        country
        for country in ("UNASSIGNED", "OUTSIDE")
        if country in animal_counts or country in animal_sites
    )
    for country in animal_partitions:
        evidence[("animal_adna", "publication", country)] = {
            **_empty_counts(),
            "published_records": animal_counts[country],
            "samples": animal_counts[country],
            "sites": animal_sites[country],
        }
