from __future__ import annotations

from collections.abc import Mapping
import importlib
from pathlib import Path
from types import ModuleType
from typing import cast


def _surface() -> ModuleType:
    return importlib.import_module(__package__ or "")


def build_neotoma_refresh_baseline(
    *,
    raw_archive_root: Path,
    relational_root: Path,
    compact_geojson_path: Path,
    lineage_path: Path,
    raw_public_root: str = "data/neotoma/raw/neotoma_pollen_dataset_downloads",
    relational_public_root: str = "data/neotoma/relational",
    compact_public_path: str = "data/neotoma/normalized/nordic_pollen_sites.geojson",
    lineage_public_path: str = "data/neotoma/review/compact_relational_lineage.json",
) -> dict[str, object]:
    surface = _surface()
    return cast(
        dict[str, object],
        surface.build_baseline(
            raw_archive_root=raw_archive_root,
            relational_root=relational_root,
            compact_geojson_path=compact_geojson_path,
            lineage_path=lineage_path,
            raw_public_root=raw_public_root,
            relational_public_root=relational_public_root,
            compact_public_path=compact_public_path,
            lineage_public_path=lineage_public_path,
            baseline_schema_version=surface.BASELINE_SCHEMA_VERSION,
            lineage_schema_version=surface.LINEAGE_SCHEMA_VERSION,
            safe_public_path=surface._safe_public_path,
            load_raw_archive=surface.load_validated_neotoma_raw_archive,
            read_file=surface._read_regular_file,
            parse_object=surface._json_object,
            parse_mapping=surface._mapping,
            safe_filename=surface._safe_filename,
            required_text=surface._required_text,
            validate_materialization=surface.validate_neotoma_relational_materialization,
            non_negative_integer=surface._non_negative_integer,
            canonical_json=surface._canonical_json,
            hashlib_module=surface.hashlib,
        ),
    )


def build_neotoma_refresh_review(
    prior: Mapping[str, object] | None,
    candidate: Mapping[str, object] | None,
    *,
    explanations: Mapping[str, str] | None = None,
    missing_reasons: list[str] | None = None,
) -> dict[str, object]:
    surface = _surface()
    return cast(
        dict[str, object],
        surface.build_review(
            prior,
            candidate,
            explanations=explanations,
            missing_reasons=missing_reasons,
            schema_version=surface.REFRESH_REVIEW_SCHEMA_VERSION,
            optional_baseline_id=surface._optional_baseline_id,
            validate_baseline=surface._validate_baseline,
            parse_mapping=surface._mapping,
            collect_changes=surface._collect_changes,
        ),
    )


def write_neotoma_refresh_baseline(
    output_path: Path,
    *,
    raw_archive_root: Path,
    relational_root: Path,
    compact_geojson_path: Path,
    lineage_path: Path,
) -> Path:
    surface = _surface()
    return cast(
        Path,
        surface.write_baseline(
            output_path,
            raw_archive_root=raw_archive_root,
            relational_root=relational_root,
            compact_geojson_path=compact_geojson_path,
            lineage_path=lineage_path,
            build_baseline=surface.build_neotoma_refresh_baseline,
            canonical_json=surface._canonical_json,
            read_file=surface._read_regular_file,
            write_atomic=surface._write_atomic,
        ),
    )


def write_neotoma_refresh_review(
    output_path: Path,
    *,
    baseline_path: Path,
    raw_archive_root: Path,
    relational_root: Path,
    compact_geojson_path: Path,
    lineage_path: Path,
    explanations: Mapping[str, str] | None = None,
    markdown_path: Path | None = None,
) -> Path:
    surface = _surface()
    return cast(
        Path,
        surface.write_review(
            output_path,
            baseline_path=baseline_path,
            raw_archive_root=raw_archive_root,
            relational_root=relational_root,
            compact_geojson_path=compact_geojson_path,
            lineage_path=lineage_path,
            explanations=explanations,
            markdown_path=markdown_path,
            parse_object=surface._json_object,
            read_file=surface._read_regular_file,
            build_baseline=surface.build_neotoma_refresh_baseline,
            build_review=surface.build_neotoma_refresh_review,
            write_atomic=surface._write_atomic,
            canonical_json=surface._canonical_json,
            render_markdown=surface.render_neotoma_refresh_review_markdown,
        ),
    )


def render_neotoma_refresh_review_markdown(payload: Mapping[str, object]) -> str:
    return str(_surface().render_markdown(payload))


def _collect_changes(
    changes: list[dict[str, object]],
    *,
    section: str,
    prior: Mapping[str, object],
    candidate: Mapping[str, object],
    explanations: Mapping[str, str],
    prefix: str = "",
) -> None:
    surface = _surface()
    surface.collect_changes(
        changes,
        section=section,
        prior=prior,
        candidate=candidate,
        explanations=explanations,
        prefix=prefix,
        classify_change=surface._change_kind,
        recurse=surface._collect_changes,
    )


def _change_kind(*, section: str, prior: object, candidate: object) -> str:
    return str(
        _surface().change_kind(section=section, prior=prior, candidate=candidate)
    )


def _validate_baseline(value: Mapping[str, object], label: str) -> None:
    surface = _surface()
    surface.validate_baseline(
        value,
        label,
        baseline_schema_version=surface.BASELINE_SCHEMA_VERSION,
        required_text=surface._required_text,
        canonical_json=surface._canonical_json,
        parse_mapping=surface._mapping,
        hashlib_module=surface.hashlib,
    )


def _optional_baseline_id(value: Mapping[str, object] | None) -> str | None:
    return cast(str | None, _surface().optional_baseline_id(value))
