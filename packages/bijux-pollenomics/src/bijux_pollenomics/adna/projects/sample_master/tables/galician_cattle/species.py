"""Preserve ENA-owned domestic cattle and aurochs BioSample identities."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
import csv
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.adna.projects.registry.archive_samples import (
    AdnaArchiveProjectSample,
)

PROJECT = "PRJNA705960"
_EXPECTED_ACCESSIONS = frozenset(f"SAMN181068{number:02d}" for number in range(27, 38))
_EXPECTED_TAXA = {"Bos primigenius": 3, "Bos taurus": 8}
_NATIVE_TAXA: dict[tuple[tuple[str, ...], tuple[str, ...]], tuple[str, str]] = {
    (("9909",), ("Bos primigenius",)): ("Bos primigenius", "aurochs"),
    (("9913",), ("Bos taurus",)): ("Bos taurus", "cattle"),
}
_PINNED_PAPER_REVIEW_SHA256 = (
    "2a4d441163c5b30d0fd8c89a44a4a641f5cd7f2f2d1b0506f4d3af0798c2dacd"
)
_CSV_FIELDS = (
    "biosample_accession",
    "repo_stable_sample_id",
    "source_native_tax_id",
    "source_native_scientific_name",
    "sample_species_latin_name",
    "sample_species_common_name",
    "project_species_latin_name",
    "taxon_alignment_status",
    "paper_sample_label",
    "paper_specimen_code",
    "paper_row",
    "locality_status",
    "chronology_status",
)


def resolve_galician_sample_species(
    sample: AdnaArchiveProjectSample,
) -> tuple[str, str]:
    """Resolve only a reviewed ENA BioSample taxon pair, with no project fallback."""
    if (
        sample.source_native_identity_kind != "biological_sample_accession"
        or sample.archive_native_sample_id not in _EXPECTED_ACCESSIONS
    ):
        raise ValueError(
            "Galician cattle BioSample identity differs from reviewed capture"
        )
    pair = (sample.source_native_tax_ids, sample.source_native_scientific_names)
    result = _NATIVE_TAXA.get(pair)
    if result is None:
        raise ValueError(
            f"Galician cattle BioSample taxon unreviewed: {sample.archive_native_sample_id}"
        )
    return result


def validate_galician_archive_samples(
    samples: Sequence[AdnaArchiveProjectSample],
) -> None:
    """Require complete, unique, sample-owned 8/3 taxonomy before materialization."""
    accessions = [sample.archive_native_sample_id for sample in samples]
    if (
        len(accessions) != len(_EXPECTED_ACCESSIONS)
        or set(accessions) != _EXPECTED_ACCESSIONS
    ):
        raise ValueError(
            "Galician cattle BioSample population differs from reviewed capture"
        )
    counts = Counter(resolve_galician_sample_species(sample)[0] for sample in samples)
    if dict(counts) != _EXPECTED_TAXA:
        raise ValueError("Galician cattle BioSample taxon denominator changed")


def _verified_paper_review(repository: Path) -> tuple[dict[str, Any], str]:
    path = (
        repository / "docs/report/source-relations/dna-scope/galician-cattle-paper.json"
    )
    payload = path.read_bytes()
    digest = sha256(payload).hexdigest()
    if digest != _PINNED_PAPER_REVIEW_SHA256:
        raise ValueError("Galician paper crosswalk digest changed")
    review: dict[str, Any] = json.loads(payload)
    if (
        review.get("source_project") != PROJECT
        or review.get("paper_doi") != "10.1371/journal.pone.0249537"
        or review.get("sample_label_to_biosample_crosswalk_status")
        != "resolved_by_source_owned_ena_biosample_alias"
        or review.get("paper_sequenced_species_counts") != _EXPECTED_TAXA
        or review.get("archive_species_counts") != _EXPECTED_TAXA
        or review.get("source_paper_linkage_status")
        != "primary_paper_identified_not_promoted"
    ):
        raise ValueError("Galician paper crosswalk posture changed")
    return review, digest


def build_galician_sample_species_review(
    repository: Path,
) -> tuple[dict[str, Any], list[dict[str, object]]]:
    """Bind public sample-master ownership to pinned ENA and paper alias evidence."""
    from bijux_pollenomics.adna.projects.sample_master import (
        build_project_sample_master,
    )
    from bijux_pollenomics.adna.projects.registry.samples import (
        build_species_curated_sample_rows,
    )
    from bijux_pollenomics.adna.species.tracked_data.csv_exports import (
        _render_sample_records_csv,
    )
    from bijux_pollenomics.adna.species.tracked_data.payloads import (
        _sample_records_payload,
    )
    from bijux_pollenomics.adna.workflow.normalization import (
        build_species_normalization_bundle,
    )
    from bijux_pollenomics.core.tabular import render_csv_rows

    repository = Path(repository)
    paper_review, paper_digest = _verified_paper_review(repository)
    source_hashes: dict[str, dict[str, object]] = {}
    for key, identity in paper_review["sources"].items():
        relative = Path(identity["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Galician paper source path escapes repository")
        payload = (repository / relative).read_bytes()
        digest = sha256(payload).hexdigest()
        if digest != identity["sha256"] or len(payload) != identity["bytes"]:
            raise ValueError(f"Galician source capture differs: {key}")
        source_hashes[key] = {
            "path": relative.as_posix(),
            "sha256": digest,
            "bytes": len(payload),
        }
    master = build_project_sample_master(repository / "data", PROJECT)
    if master.species_latin_name != "Bos taurus" or len(master.rows) != 11:
        raise ValueError("Galician project identity or sample count changed")
    by_accession = {row.archive_native_sample_id: row for row in master.rows}
    if set(by_accession) != _EXPECTED_ACCESSIONS:
        raise ValueError(
            "Galician sample-master accession set differs from ENA capture"
        )
    crosswalk = paper_review["sample_label_to_biosample_crosswalk"]
    if not isinstance(crosswalk, list) or len(crosswalk) != len(_EXPECTED_ACCESSIONS):
        raise ValueError("Galician paper sample crosswalk cardinality changed")
    rows: list[dict[str, object]] = []
    for item in sorted(crosswalk, key=lambda value: value["biosample_accession"]):
        accession = item["biosample_accession"]
        sample = by_accession.get(accession)
        if (
            sample is None
            or sample.species_latin_name != item["source_species"]
            or sample.source_native_scientific_name != item["source_species"]
            or sample.source_native_tax_id
            != ("9909" if item["source_species"] == "Bos primigenius" else "9913")
            or sample.repo_stable_sample_id != f"{PROJECT}:{accession}".casefold()
            or sample.locality_text
            or sample.political_entity
            or sample.latitude_text
            or sample.longitude_text
            or sample.chronology_text
            or sample.chronology_time_mean_bp is not None
        ):
            raise ValueError(
                f"Galician paper/ENA sample ownership differs: {accession}"
            )
        rows.append(
            {
                "biosample_accession": accession,
                "repo_stable_sample_id": sample.repo_stable_sample_id,
                "source_native_tax_id": sample.source_native_tax_id,
                "source_native_scientific_name": sample.source_native_scientific_name,
                "sample_species_latin_name": sample.species_latin_name,
                "sample_species_common_name": sample.species_common_name,
                "project_species_latin_name": master.species_latin_name,
                "taxon_alignment_status": sample.taxon_alignment_status,
                "paper_sample_label": item["paper_sample_label"],
                "paper_specimen_code": item["paper_specimen_code"],
                "paper_row": item["paper_row"],
                "locality_status": "unresolved",
                "chronology_status": "unresolved",
            }
        )
    if len({row["biosample_accession"] for row in rows}) != len(_EXPECTED_ACCESSIONS):
        raise ValueError("Galician paper crosswalk repeats a BioSample")
    sample_counts = dict(
        sorted(Counter(row["sample_species_latin_name"] for row in rows).items())
    )
    if sample_counts != _EXPECTED_TAXA:
        raise ValueError("Galician sample-master taxon denominator changed")
    source_root = repository / "data/adna/governance/source_library/projects" / PROJECT
    governed_outputs = {
        "sample_master.json": json.dumps(
            {"schema_version": "animal-project-sample-master.v1", **master.as_dict()},
            indent=2,
            ensure_ascii=False,
        ).encode(),
        "sample_master.csv": render_csv_rows(
            [sample.as_dict() for sample in master.rows]
        ).encode(),
    }
    output_hashes: dict[str, dict[str, object]] = {}
    for name, expected in governed_outputs.items():
        target = source_root / name
        if target.read_bytes() != expected:
            raise ValueError(f"Galician governed sample master differs: {name}")
        output_hashes[name] = {
            "path": f"data/adna/governance/source_library/projects/{PROJECT}/{name}",
            "sha256": sha256(expected).hexdigest(),
            "bytes": len(expected),
        }
    curated = tuple(
        row
        for row in build_species_curated_sample_rows(
            "cattle", output_root=repository / "data"
        )
        if row.project_accession == PROJECT
    )
    if (
        len(curated) != len(rows)
        or dict(Counter(row.species_latin_name for row in curated)) != _EXPECTED_TAXA
        or any(row.inclusion_status != "sample_context_blocked" for row in curated)
    ):
        raise ValueError(
            "Galician curated sample consumer differs from native taxonomy"
        )
    normalized_bundle = build_species_normalization_bundle("cattle")
    normalized = tuple(
        row for row in normalized_bundle.sample_records if row.group_id == PROJECT
    )
    if (
        len(normalized) != len(rows)
        or dict(Counter(row.species_latin_name for row in normalized)) != _EXPECTED_TAXA
        or any(
            row.locality is not None
            or row.coordinates.latitude is not None
            or row.coordinates.longitude is not None
            or row.chronology.time_start_bp is not None
            or row.chronology.time_end_bp is not None
            for row in normalized
        )
    ):
        raise ValueError(
            "Galician normalized sample consumer differs from source posture"
        )
    normalized_outputs = {
        "sample_records.json": json.dumps(
            _sample_records_payload(normalized_bundle), indent=2, ensure_ascii=False
        ).encode(),
        "sample_records.csv": _render_sample_records_csv(normalized_bundle).encode(),
    }
    normalized_root = repository / "data/adna/species/bos_taurus/normalized"
    normalized_hashes: dict[str, dict[str, object]] = {}
    for name, expected in normalized_outputs.items():
        if (normalized_root / name).read_bytes() != expected:
            raise ValueError(f"Galician governed normalized samples differ: {name}")
        normalized_hashes[name] = {
            "path": f"data/adna/species/bos_taurus/normalized/{name}",
            "sha256": sha256(expected).hexdigest(),
            "bytes": len(expected),
        }
    report: dict[str, Any] = {
        "schema_version": "galician-cattle-sample-species-review.v1",
        "project_accession": PROJECT,
        "project_species_latin_name": master.species_latin_name,
        "sample_species_counts": sample_counts,
        "sample_count": len(rows),
        "paper_specimen_count": paper_review["paper_specimen_rows"],
        "source_hashes": {
            "paper_crosswalk_report": {
                "path": "docs/report/source-relations/dna-scope/galician-cattle-paper.json",
                "sha256": paper_digest,
                "bytes": (
                    repository
                    / "docs/report/source-relations/dna-scope/galician-cattle-paper.json"
                )
                .stat()
                .st_size,
            },
            "primary_captures": source_hashes,
        },
        "governed_sample_master": output_hashes,
        "governed_normalized_samples": normalized_hashes,
        "curated_consumer": {
            "sample_count": len(curated),
            "species_counts": sample_counts,
            "inclusion_status": "sample_context_blocked",
        },
        "admission_posture": {
            "sample_species_resolved": True,
            "project_paper_linkage_promoted": False,
            "sample_site_resolved": False,
            "sample_chronology_resolved": False,
            "atlas_point_admitted": False,
            "nordic_relevance": "none_galician_source_context",
        },
    }
    return report, rows


def write_galician_sample_species_review(
    repository: Path, output: Path
) -> dict[str, Any]:
    """Write a deterministic row-level record without changing source admission."""
    if output.exists():
        raise ValueError("Galician species review output must be absent")
    report, rows = build_galician_sample_species_review(repository)
    output.mkdir(parents=True)
    with (output / "samples.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=_CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    report["sample_review_csv"] = {
        "path": "samples.csv",
        "sha256": sha256((output / "samples.csv").read_bytes()).hexdigest(),
        "row_count": len(rows),
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    return report
