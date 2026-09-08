from __future__ import annotations

import inspect
from pathlib import Path

from bijux_pollenomics.collection.sources.neotoma import production

EXPECTED_SIGNATURES = {
    "NeotomaProductionConfig": "(producer_id: 'str' = 'bijux-pollenomics.neotoma-relational-production', producer_version: 'str' = '1', config_schema: 'str' = 'neotoma-relational-production-config.v1', rows_per_part: 'int' = 50000, proximity_tolerance: 'float' = 0.15, raw_country_aliases: 'tuple[tuple[str, str], ...]' = ()) -> None",
    "NeotomaProductionReport": "(manifest_path: 'str', source_snapshot_id: 'str', boundary_authority_id: 'str', build_id: 'str', raw_part_count: 'int', raw_row_count: 'int', site_count: 'int', country_counts: 'dict[str, int]', country_decision_counts: 'dict[str, int]') -> None",
    "_RawArchive": "(rows: 'tuple[dict[str, object], ...]', source_snapshot_id: 'str', part_digests: 'tuple[str, ...]') -> None",
    "_BoundaryAuthority": "(boundaries: 'dict[str, dict[str, object]]', artifact_digest: 'str', version: 'str', authority_id: 'str') -> None",
    "run_neotoma_relational_production": "(*, raw_archive_root: 'Path', boundary_root: 'Path', output_root: 'Path', approved_output_parent: 'Path', config: 'NeotomaProductionConfig | None' = None) -> 'NeotomaProductionReport'",
    "load_validated_neotoma_raw_archive": "(raw_archive_root: 'Path') -> 'tuple[list[dict[str, object]], str]'",
    "_load_validated_raw_archive": "(raw_archive_root: 'Path') -> '_RawArchive'",
    "_load_validated_boundary_authority": "(boundary_root: 'Path') -> '_BoundaryAuthority'",
    "_build_id": "(*, source_snapshot_id: 'str', boundary_authority_id: 'str', config: 'NeotomaProductionConfig') -> 'str'",
    "_validated_output_target": "(output_root: 'Path', approved_parent: 'Path') -> 'Path'",
    "_validated_input_directory": "(path: 'Path', label: 'str') -> 'Path'",
    "_read_regular_file": "(path: 'Path') -> 'bytes'",
    "_json_object": "(content: 'bytes', path: 'Path') -> 'dict[str, object]'",
    "_download_dataset_id": "(row: 'Mapping[str, object]', filename: 'str') -> 'int'",
    "_mapping": "(value: 'object', label: 'str') -> 'Mapping[str, object]'",
    "_integer": "(value: 'object', label: 'str') -> 'int'",
    "_positive_integer": "(value: 'object', label: 'str') -> 'int'",
    "_non_negative_integer": "(value: 'object', label: 'str') -> 'int'",
    "_integer_list": "(value: 'object', label: 'str') -> 'list[int]'",
    "_expect_equal": "(actual: 'object', expected: 'object', label: 'str') -> 'None'",
    "_canonical_digest": "(payload: 'object') -> 'str'",
    "_parse_alias": "(value: 'str') -> 'tuple[str, str]'",
    "_parser": "() -> 'argparse.ArgumentParser'",
    "main": "(argv: 'Sequence[str] | None' = None) -> 'int'",
}


def test_facade_preserves_every_monolith_signature() -> None:
    assert {
        name: str(inspect.signature(getattr(production, name)))
        for name in EXPECTED_SIGNATURES
    } == EXPECTED_SIGNATURES


def test_facade_preserves_exports_and_constants() -> None:
    assert production.__all__ == [
        "NeotomaProductionConfig",
        "NeotomaProductionReport",
        "load_validated_neotoma_raw_archive",
        "main",
        "run_neotoma_relational_production",
    ]
    namespace = vars(production)
    assert (
        namespace["EXPECTED_RAW_PART_COUNT"],
        namespace["RAW_SOURCE"],
        namespace["RAW_DATASET_TYPE"],
        namespace["RAW_ENDPOINT"],
        namespace["RAW_ARCHIVE_LABEL"],
        namespace["PRODUCTION_DRIVER_ID"],
        namespace["PRODUCTION_DRIVER_VERSION"],
        namespace["PRODUCTION_CONFIG_SCHEMA"],
    ) == (
        9,
        "Neotoma",
        "pollen",
        "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}",
        "raw/neotoma_pollen_dataset_downloads",
        "bijux-pollenomics.neotoma-relational-production",
        "1",
        "neotoma-relational-production-config.v1",
    )


def test_package_has_small_intent_owned_modules() -> None:
    package_root = Path(production.__file__).parent
    assert {path.name for path in package_root.glob("*.py")} == {
        "__init__.py",
        "boundary_authority.py",
        "command_line.py",
        "constants.py",
        "execution_api.py",
        "identity.py",
        "models.py",
        "raw_archive.py",
        "validation.py",
        "validation_api.py",
        "workflow.py",
    }
    assert (
        max(
            len(path.read_text(encoding="utf-8").splitlines())
            for path in package_root.glob("*.py")
        )
        <= 220
    )
