from __future__ import annotations

import argparse
import importlib
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import cast

from .models import (
    NeotomaProductionConfig,
    NeotomaProductionReport,
    _BoundaryAuthority,
    _RawArchive,
)


def _surface() -> ModuleType:
    return importlib.import_module(__package__ or "")


def run_neotoma_relational_production(
    *,
    raw_archive_root: Path,
    boundary_root: Path,
    output_root: Path,
    approved_output_parent: Path,
    config: NeotomaProductionConfig | None = None,
) -> NeotomaProductionReport:
    """Validate all authorities, build the snapshot, and atomically publish it."""
    surface = _surface()
    return cast(
        NeotomaProductionReport,
        surface.run_production(
            raw_archive_root=raw_archive_root,
            boundary_root=boundary_root,
            output_root=output_root,
            approved_output_parent=approved_output_parent,
            config=config,
            validate_output=surface._validated_output_target,
            load_raw_archive=surface._load_validated_raw_archive,
            load_boundary_authority=surface._load_validated_boundary_authority,
            build_id=surface._build_id,
            build_country_decisions=surface.build_neotoma_site_country_decisions,
            build_snapshot=surface.build_neotoma_relational_snapshot,
            materialize_snapshot=surface.materialize_neotoma_relational_snapshot,
            parse_mapping=surface._mapping,
            parse_integer=surface._integer,
        ),
    )


def load_validated_neotoma_raw_archive(
    raw_archive_root: Path,
) -> tuple[list[dict[str, object]], str]:
    """Load a checked-in nine-part archive and return rows plus its content ID."""
    archive = _surface()._load_validated_raw_archive(raw_archive_root)
    return list(archive.rows), archive.source_snapshot_id


def _load_validated_raw_archive(raw_archive_root: Path) -> _RawArchive:
    surface = _surface()
    return cast(
        _RawArchive,
        surface.load_raw_archive(
            raw_archive_root,
            expected_part_count=surface.EXPECTED_RAW_PART_COUNT,
            raw_source=surface.RAW_SOURCE,
            archive_label=surface.RAW_ARCHIVE_LABEL,
            endpoint=surface.RAW_ENDPOINT,
            dataset_type=surface.RAW_DATASET_TYPE,
            sha256_pattern=surface._SHA256_PATTERN,
            validate_directory=surface._validated_input_directory,
            read_file=surface._read_regular_file,
            parse_object=surface._json_object,
            parse_mapping=surface._mapping,
            parse_positive_integer=surface._positive_integer,
            parse_non_negative_integer=surface._non_negative_integer,
            parse_integer_list=surface._integer_list,
            expect_equal=surface._expect_equal,
            download_dataset_id=surface._download_dataset_id,
            canonical_digest=surface._canonical_digest,
        ),
    )


def _load_validated_boundary_authority(boundary_root: Path) -> _BoundaryAuthority:
    surface = _surface()
    return cast(
        _BoundaryAuthority,
        surface.load_boundary_authority(
            boundary_root,
            boundary_codes=surface.BOUNDARY_CODES,
            natural_earth_version=surface.NATURAL_EARTH_VERSION,
            admin0_url=surface.NATURAL_EARTH_ADMIN0_URL,
            terms_url=surface.NATURAL_EARTH_TERMS_URL,
            release_page_url=surface.NATURAL_EARTH_RELEASE_PAGE_URL,
            sha256_pattern=surface._SHA256_PATTERN,
            validate_directory=surface._validated_input_directory,
            read_file=surface._read_regular_file,
            parse_object=surface._json_object,
            parse_mapping=surface._mapping,
            expect_equal=surface._expect_equal,
            load_boundaries=surface.load_country_boundaries,
            canonical_digest=surface._canonical_digest,
        ),
    )


def _build_id(
    *,
    source_snapshot_id: str,
    boundary_authority_id: str,
    config: NeotomaProductionConfig,
) -> str:
    surface = _surface()
    return str(
        surface.build_id(
            source_snapshot_id=source_snapshot_id,
            boundary_authority_id=boundary_authority_id,
            config=config,
            canonical_digest=surface._canonical_digest,
        )
    )


def _parser() -> argparse.ArgumentParser:
    surface = _surface()
    return cast(
        argparse.ArgumentParser,
        surface.parser(
            alias_parser=surface._parse_alias,
            producer_version=surface.PRODUCTION_DRIVER_VERSION,
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the production gate and emit one machine-readable result line."""
    surface = _surface()
    return int(
        surface.run_cli(
            argv,
            build_parser=surface._parser,
            config_type=surface.NeotomaProductionConfig,
            run_production=surface.run_neotoma_relational_production,
            json_module=surface.json,
            error_stream=surface.sys.stderr,
        )
    )
