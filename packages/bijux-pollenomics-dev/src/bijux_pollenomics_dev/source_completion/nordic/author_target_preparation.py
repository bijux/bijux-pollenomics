"""Qualify source custody for original Nordic author-target input preparation."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zlib

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
    load_json,
    require_mapping,
    require_string,
    require_string_sequence,
)
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.source_completion.landclim_taxonomy_mass import LOOKUP
from bijux_pollenomics_dev.source_completion.nordic_author_target_pollen import (
    AUTHOR_MASS,
    NORDIC,
    prepare,
)
from bijux_pollenomics_dev.source_completion.nordic_direct_pollen import (
    RELATIONAL_BUILD,
    SOURCE_SNAPSHOT,
)
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
    Path("docs/report/pollen-reconstruction/swedish-direct-pollen/exclusions.csv"),
    Path(
        "docs/report/pollen-reconstruction/swedish-direct-pollen/prepared/dataset-19913.json"
    ),
    Path(
        "docs/report/pollen-reconstruction/swedish-direct-pollen/prepared/dataset-53995.json"
    ),
    Path(
        "docs/report/pollen-reconstruction/swedish-direct-pollen/prepared/dataset-54001.json"
    ),
    Path("docs/report/regions/nordic/author-taxonomy-mass/report.json"),
    Path("docs/report/regions/nordic/direct-pollen/manifest.json"),
)
COUNTRIES = ("DK", "FI", "NO")
PRODUCTS = tuple(
    f"{directory}/{role}-{country}.json.gz"
    for country in COUNTRIES
    for directory, role in (
        ("inputs", "training"),
        ("inputs", "metadata"),
        ("sealed-outcomes", "outcomes"),
    )
)
COUNTRY_COUNTS = {
    "DK": (1, 91, 24, 129768, 122998, 6699, 71),
    "FI": (28, 1797, 435, 1260281, 1229019, 28847, 2415),
    "NO": (52, 3544, 1178, 2286020, 2018295, 233598, 34127),
}
BIN_FIELDS = (
    "all_pollen_nisp",
    "closed_nisp",
    "author_excluded_nisp",
    "unmapped_nisp",
    "sample_count",
)


def _count(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ReportRebuildError(
            f"Nordic prepared {label} must be a non-negative integer"
        )
    return value


def _records(value: object, label: str) -> list[JsonObject]:
    if not isinstance(value, list):
        raise ReportRebuildError(f"Nordic prepared {label} must be an object list")
    return [require_mapping(item, f"Nordic prepared {label}") for item in value]


def _compressed_object(path: Path) -> JsonObject:
    try:
        return require_mapping(
            json.loads(gzip.decompress(_regular_path(path).read_bytes())),
            "Nordic prepared compressed object",
        )
    except (OSError, EOFError, UnicodeError, json.JSONDecodeError, zlib.error) as error:
        raise ReportRebuildError("Nordic prepared compressed source differs") from error


def _bin_account(value: object, axis: tuple[str, ...]) -> tuple[int, ...]:
    cell = require_mapping(value, "Nordic prepared source bin")
    if set(cell) != {"counts", *BIN_FIELDS}:
        raise ReportRebuildError("Nordic prepared bin fields differ")
    counts = require_mapping(cell["counts"], "Nordic prepared taxon counts")
    mass = tuple(_count(cell[field], field) for field in BIN_FIELDS)
    if (
        set(counts) != set(axis)
        or sum(_count(value, "taxon count") for value in counts.values()) != mass[1]
        or mass[0] != sum(mass[1:4])
        or mass[0] == 0
        or mass[4] == 0
    ):
        raise ReportRebuildError("Nordic prepared source mass/axis differs")
    return mass


def _bound_products(
    repository: Path, source_directory: Path, output: Path
) -> JsonObject:
    if {p.name for p in output.iterdir()} != {
        "input-manifest.json",
        "inputs",
        "sealed-outcomes",
    }:
        raise ReportRebuildError("Nordic prepared output coverage differs")
    for directory in ("inputs", "sealed-outcomes"):
        root = _regular_path(output / directory, directory=True)
        if {p.name for p in root.iterdir()} != {
            Path(p).name for p in PRODUCTS if Path(p).parent.name == directory
        }:
            raise ReportRebuildError("Nordic prepared output coverage differs")
    manifest = load_json(
        _regular_path(output / "input-manifest.json"), "Nordic prepared manifest"
    )
    if set(manifest) != {
        "schema_version",
        "axis",
        "lookup_rows",
        "age_bin_width_bp",
        "source_snapshot_id",
        "relational_build_id",
        "direct_manifest_sha256",
        "author_mass_report_sha256",
        "author_lookup_sha256",
        "swedish_source_sha256",
        "swedish_prepared_sha256",
        "neotoma_relational_sha256",
        "observation_part_sha256",
        "produced_file_sha256",
        "target_outcomes_in_prediction_inputs",
    }:
        raise ReportRebuildError("Nordic prepared manifest fields differ")
    expected_manifest = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    if (output / "input-manifest.json").read_bytes() != expected_manifest:
        raise ReportRebuildError("Nordic prepared manifest serialization differs")
    axis = require_string_sequence(manifest["axis"], "Nordic prepared taxon axis")
    if (
        manifest["schema_version"] != "nordic-author-target-pollen-inputs.v1"
        or len(axis) != 31
        or axis != tuple(sorted(axis))
        or _count(manifest["lookup_rows"], "lookup rows") != 10788
        or _count(manifest["age_bin_width_bp"], "age width") != 500
        or manifest["source_snapshot_id"] != SOURCE_SNAPSHOT
        or manifest["relational_build_id"] != RELATIONAL_BUILD
        or manifest["target_outcomes_in_prediction_inputs"] is not False
    ):
        raise ReportRebuildError("Nordic prepared source/axis/separation scope differs")
    for field, path in (
        ("direct_manifest_sha256", repository / NORDIC / "manifest.json"),
        ("author_mass_report_sha256", repository / AUTHOR_MASS),
        ("author_lookup_sha256", source_directory / LOOKUP),
    ):
        if (
            manifest[field]
            != hashlib.sha256(_regular_path(path).read_bytes()).hexdigest()
        ):
            raise ReportRebuildError("Nordic prepared upstream identity differs")
    produced = require_mapping(
        manifest["produced_file_sha256"], "Nordic prepared product hashes"
    )
    if set(produced) != set(PRODUCTS):
        raise ReportRebuildError("Nordic prepared product hash coverage differs")
    for relative in PRODUCTS:
        if (
            produced[relative]
            != hashlib.sha256(_regular_path(output / relative).read_bytes()).hexdigest()
        ):
            raise ReportRebuildError("Nordic prepared product bytes differ")
    outcomes = {
        country: _compressed_object(
            output / f"sealed-outcomes/outcomes-{country}.json.gz"
        )
        for country in COUNTRIES
    }
    site_ids: dict[str, set[str]] = {}
    sample_ids: set[str] = set()
    for country in COUNTRIES:
        expected = COUNTRY_COUNTS[country]
        metadata = _compressed_object(output / f"inputs/metadata-{country}.json.gz")
        sites = _records(metadata.get("sites"), "target sites")
        if (
            metadata.get("country") != country
            or _count(metadata.get("candidate_samples"), "candidate samples")
            != expected[1]
            or len(sites) != expected[0]
        ):
            raise ReportRebuildError(
                "Nordic prepared target country/sample scope differs"
            )
        keys: set[str] = set()
        selected: set[str] = set()
        totals = [0] * len(BIN_FIELDS)
        bin_count = 0
        for site in sites:
            site_id = require_string(
                site.get("site_id"), "Nordic prepared site identity"
            )
            key = f"{country}:{site_id}"
            if site.get("country") != country or key in keys:
                raise ReportRebuildError("Nordic prepared target site identity differs")
            keys.add(key)
            samples = require_string_sequence(
                site.get("candidate_sample_ids"),
                "Nordic prepared target sample identities",
            )
            if selected.intersection(samples):
                raise ReportRebuildError(
                    "Nordic prepared target sample ownership differs"
                )
            selected.update(samples)
            bins = require_mapping(
                outcomes[country].get(key), "Nordic prepared sealed site bins"
            )
            if set(bins) != set(
                require_string_sequence(
                    site.get("candidate_bin_ids"), "Nordic prepared target bins"
                )
            ):
                raise ReportRebuildError(
                    "Nordic prepared target bin membership differs"
                )
            bin_count += len(bins)
            site_samples = 0
            for value in bins.values():
                mass = _bin_account(value, axis)
                totals = [
                    left + right for left, right in zip(totals, mass, strict=True)
                ]
                site_samples += mass[4]
            if site_samples != len(samples):
                raise ReportRebuildError(
                    "Nordic prepared site sample denominator differs"
                )
        if (
            set(outcomes[country]) != keys
            or len(selected) != expected[1]
            or bin_count != expected[2]
            or tuple(totals) != (*expected[3:], expected[1])
            or sample_ids.intersection(selected)
            or set(
                require_mapping(
                    metadata.get("selected_age_claim_ids"),
                    "Nordic prepared selected age claims",
                )
            )
            != selected
        ):
            raise ReportRebuildError(
                "Nordic prepared sealed count/sample closure differs"
            )
        site_ids[country] = keys
        sample_ids.update(selected)
    for held_out in COUNTRIES:
        training = _compressed_object(output / f"inputs/training-{held_out}.json.gz")
        expected_keys = set().union(
            *(keys for country, keys in site_ids.items() if country != held_out)
        )
        actual_nordic: set[str] = set()
        swedish_keys: set[str] = set()
        for key, value in training.items():
            profile = require_mapping(value, "Nordic prepared training profile")
            country = require_string(
                profile.get("country"), "Nordic prepared training country"
            )
            if country == held_out or country not in {*COUNTRIES, "SE"}:
                raise ReportRebuildError(
                    "Nordic prepared held-out country leaked into training"
                )
            if (
                key
                != f"{country}:{require_string(profile.get('site_id'), 'Nordic prepared training site')}"
            ):
                raise ReportRebuildError(
                    "Nordic prepared training site identity differs"
                )
            bins = require_mapping(profile.get("bins"), "Nordic prepared training bins")
            for cell in bins.values():
                _bin_account(cell, axis)
            if country == "SE":
                swedish_keys.add(key)
            else:
                actual_nordic.add(key)
                if bins != outcomes[country].get(key):
                    raise ReportRebuildError(
                        "Nordic prepared shared source count bins differ"
                    )
        if actual_nordic != expected_keys or len(swedish_keys) != 3:
            raise ReportRebuildError(
                "Nordic prepared training country membership differs"
            )
    return manifest


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> JsonObject:
    """Prepare original source counts without executing prediction or scoring.

    Snapshot qualification establishes custody only; it supplies neither source
    rights nor scientific admission. Sealed target counts stay outside their
    country's training products.
    """
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    _require_author_lookup(qualified, source_descriptor)
    inputs = {
        **qualified.inputs,
        **{p.as_posix(): _regular_path(repository / p) for p in REPOSITORY_INPUTS},
    }
    before = producer_input_identity(inputs, repository)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    products = stage / "source-products"
    try:
        prepare(repository, qualified.directory, products)
        manifest = _bound_products(repository, qualified.directory, products)
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
                "Nordic prepared inputs changed during publication"
            )
        require_absent_artifact_output(repository, destination)
        os.replace(products, destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return manifest


def main(argv: list[str] | None = None) -> int:
    """Prepare qualified Nordic source inputs into absent repository artifacts."""
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
