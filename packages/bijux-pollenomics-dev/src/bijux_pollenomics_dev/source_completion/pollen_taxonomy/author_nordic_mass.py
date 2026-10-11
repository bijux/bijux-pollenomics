"""Reproduce Nordic source-native count mass with qualified author lookup custody."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
from pathlib import Path
import shutil
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
    require_mapping,
    require_string,
)
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.source_completion.nordic_author_taxonomy_mass import publish
from bijux_pollenomics_dev.source_completion.pollen_taxonomy.author_mass import (
    DESCRIPTOR,
    _require_author_lookup,
)

REPOSITORY_INPUTS = (
    Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/manifest.json"),
    Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-001.json"),
    Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-002.json"),
    Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-003.json"),
    Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json"),
    Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-005.json"),
    Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-006.json"),
    Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-007.json"),
    Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json"),
    Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-009.json"),
    Path("data/neotoma/relational/manifest.json"),
    Path("data/neotoma/relational/reconciliation.json"),
    Path("data/neotoma/relational/surfaces/age_claims/part-00001.json"),
    Path("data/neotoma/relational/surfaces/chronologies/part-00001.json"),
    Path("data/neotoma/relational/surfaces/chronology_controls/part-00001.json"),
    Path("data/neotoma/relational/surfaces/collection_units/part-00001.json"),
    Path("data/neotoma/relational/surfaces/conflicts/part-00001.json"),
    Path("data/neotoma/relational/surfaces/datasets/part-00001.json"),
    Path("data/neotoma/relational/surfaces/observations/part-00001.json"),
    Path("data/neotoma/relational/surfaces/observations/part-00002.json"),
    Path("data/neotoma/relational/surfaces/observations/part-00003.json"),
    Path("data/neotoma/relational/surfaces/observations/part-00004.json"),
    Path("data/neotoma/relational/surfaces/observations/part-00005.json"),
    Path("data/neotoma/relational/surfaces/observations/part-00006.json"),
    Path("data/neotoma/relational/surfaces/observations/part-00007.json"),
    Path("data/neotoma/relational/surfaces/observations/part-00008.json"),
    Path("data/neotoma/relational/surfaces/orphans/part-00001.json"),
    Path("data/neotoma/relational/surfaces/samples/part-00001.json"),
    Path("data/neotoma/relational/surfaces/sites/part-00001.json"),
    Path("data/neotoma/relational/surfaces/variables/part-00001.json"),
    Path("docs/report/regions/nordic/direct-pollen/cohort.csv"),
    Path("docs/report/regions/nordic/direct-pollen/manifest.json"),
)
SCHEMA = "nordic-held-out-author-taxonomy-mass.v1"
SCOPE = (
    "source-owned selected EPD pollen NISP from the published DK/FI/NO "
    "country-held-out cohorts"
)
INTERPRETATION = (
    "Exact author LUT coverage is source-taxonomy feasibility only; exclusions "
    "and unmapped mass remain outside the 31-target assignment, and no country "
    "basin or historical model is admitted."
)
SITE_FIELDS = (
    "country",
    "site_id",
    "site_name",
    "selected_samples",
    "all_native_nisp",
    "author_assigned_nisp",
    "author_excluded_nisp",
    "unmapped_nisp",
    "size_variant_candidate_nisp",
    "assigned_fraction",
    "author_targets_present",
    "lra_admitted_samples",
)
# These are retained source-account denominators, not fitted or admitted samples.
COUNTRY_COUNTS = {
    "DK": (1, 91, 129768, 122998, 6699, 71),
    "FI": (28, 1797, 1260281, 1229019, 28847, 2415),
    "NO": (52, 3544, 2286020, 2018295, 233598, 34127),
}
COUNT_FIELDS = (
    "selected_samples",
    "all_native_nisp",
    "author_assigned_nisp",
    "author_excluded_nisp",
    "unmapped_nisp",
)


def _count(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ReportRebuildError(
            f"Nordic taxonomy {label} must be a non-negative integer"
        )
    return value


def _records(value: object, label: str) -> list[JsonObject]:
    if not isinstance(value, list):
        raise ReportRebuildError(f"Nordic taxonomy {label} must be an object list")
    return [require_mapping(item, f"Nordic taxonomy {label}") for item in value]


def _bound_sites(report: JsonObject) -> list[JsonObject]:
    if (
        report.get("schema_version") != SCHEMA
        or report.get("scope") != SCOPE
        or report.get("interpretation") != INTERPRETATION
        or any(
            _count(report.get(field), field) != expected
            for field, expected in (
                ("author_lookup_rows", 10788),
                ("selected_site_count", 81),
                ("selected_sample_count", 5432),
                ("selected_pollen_observation_rows", 116727),
                ("lra_admitted_samples", 0),
            )
        )
    ):
        raise ReportRebuildError("Nordic taxonomy account scope changed")
    sites = _records(report.get("sites"), "sites")
    countries = _records(report.get("countries"), "countries")
    if len(sites) != 81 or [row.get("country") for row in countries] != list(
        COUNTRY_COUNTS
    ):
        raise ReportRebuildError("Nordic taxonomy country/site coverage differs")
    keys: list[tuple[str, str]] = []
    for site in sites:
        if tuple(site) != SITE_FIELDS:
            raise ReportRebuildError("Nordic taxonomy site fields differ")
        country = require_string(site["country"], "Nordic taxonomy country")
        site_id = require_string(site["site_id"], "Nordic taxonomy site identity")
        require_string(site["site_name"], "Nordic taxonomy site name")
        if country not in COUNTRY_COUNTS:
            raise ReportRebuildError("Nordic taxonomy site country differs")
        keys.append((country, site_id))
        counts = {field: _count(site[field], field) for field in COUNT_FIELDS}
        targets = _count(site["author_targets_present"], "author targets")
        if (
            counts["selected_samples"] == 0
            or counts["all_native_nisp"] == 0
            or counts["all_native_nisp"]
            != sum(counts[field] for field in COUNT_FIELDS[2:])
            or _count(site["size_variant_candidate_nisp"], "size variants") != 0
            or _count(site["lra_admitted_samples"], "site admission") != 0
            or not 1 <= targets <= 31
            or site["assigned_fraction"]
            != round(counts["author_assigned_nisp"] / counts["all_native_nisp"], 6)
        ):
            raise ReportRebuildError("Nordic taxonomy site mass/admission differs")
    if keys != sorted(set(keys)):
        raise ReportRebuildError("Nordic taxonomy site identity/order differs")
    for country_record in countries:
        name = require_string(country_record["country"], "Nordic taxonomy country")
        expected = COUNTRY_COUNTS[name]
        members = [row for row in sites if row["country"] == name]
        observed = tuple(
            _count(country_record.get(field), field)
            for field in ("site_count", *COUNT_FIELDS)
        )
        summed = (
            len(members),
            *(
                sum(_count(row[field], field) for row in members)
                for field in COUNT_FIELDS
            ),
        )
        if (
            observed != expected
            or summed != expected
            or _count(
                country_record.get("size_variant_candidate_nisp"),
                "country size variants",
            )
            != 0
            or country_record.get("assigned_fraction")
            != round(expected[3] / expected[2], 6)
            or country_record.get("top_size_variant_candidates") != []
        ):
            raise ReportRebuildError("Nordic taxonomy country denominators differ")
    return sites


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> JsonObject:
    """Publish the original count ledger with exact input identity before and after.

    Full snapshot qualification establishes custody only. It grants neither
    source use rights nor scientific or LRA admission.
    """
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    _require_author_lookup(qualified, source_descriptor)
    inputs = {
        **qualified.inputs,
        **{
            relative.as_posix(): _regular_path(repository / relative)
            for relative in REPOSITORY_INPUTS
        },
    }
    before = producer_input_identity(inputs, repository)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    try:
        report: JsonObject = publish(repository, qualified.directory, stage)
        sites = _bound_sites(report)
        if {path.name for path in stage.iterdir()} != {"report.json", "sites.csv"}:
            raise ReportRebuildError("Nordic taxonomy output coverage differs")
        expected = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode(
            "utf-8"
        )
        if _regular_path(stage / "report.json").read_bytes() != expected:
            raise ReportRebuildError("Nordic taxonomy JSON bytes differ from account")
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=SITE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sites)
        if _regular_path(stage / "sites.csv").read_bytes() != stream.getvalue().encode(
            "utf-8"
        ):
            raise ReportRebuildError("Nordic taxonomy CSV bytes differ from account")
        after = validated_external_report_sources(
            repository, source_root, source_descriptor
        )
        if (
            after.directory != qualified.directory
            or after.inputs != qualified.inputs
            or after.descriptor_sha256 != qualified.descriptor_sha256
            or producer_input_identity(inputs, repository) != before
        ):
            raise ReportRebuildError(
                "Nordic taxonomy inputs changed during publication"
            )
        require_absent_artifact_output(repository, destination)
        os.replace(stage, destination)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return report


def main(argv: list[str] | None = None) -> int:
    """Run the original Nordic author taxonomy account into absent artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-descriptor", type=Path, default=DESCRIPTOR)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.source_root, args.source_descriptor, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
