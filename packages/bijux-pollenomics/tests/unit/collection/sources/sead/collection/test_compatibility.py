from __future__ import annotations

import inspect

from bijux_pollenomics.collection.sources.sead import collection


def test_collection_import_path_remains_a_package_facade() -> None:
    assert collection.__file__ is not None
    assert collection.__file__.endswith("collection/__init__.py")
    assert set(collection.__all__) >= {
        "SeadDataReport",
        "collect_sead_data",
        "fetch_sead_rows",
        "fetch_sead_rows_by_ids",
        "fetch_sead_site_inventory",
        "fetch_sead_site_rows",
        "materialize_sead_repository_surfaces",
        "normalize_sead_rows",
        "normalize_sead_temporal_evidence",
        "populate_sead_site_inventory_fields",
        "refresh_sead_repository_rows",
    }


def test_public_call_signatures_remain_stable() -> None:
    assert str(inspect.signature(collection.fetch_sead_rows)) == (
        "(table_name: 'str', *, select: 'str', "
        "filters: 'tuple[tuple[str, str], ...] | None' = None, "
        "order_by: 'tuple[str, ...]' = ()) -> 'list[dict[str, object]]'"
    )
    assert str(inspect.signature(collection.collect_sead_data)) == (
        "(output_root: 'Path', "
        "country_boundaries: 'Mapping[str, Mapping[str, object]]', "
        "bbox: 'tuple[float, float, float, float]') -> 'SeadDataReport'"
    )


def test_legacy_private_seams_remain_available() -> None:
    assert callable(getattr(collection, "_load_sead_acquisition_rows"))
    assert callable(getattr(collection, "_attach_sead_country_decisions"))
    assert callable(getattr(collection, "_write_sead_site_archive"))
    assert callable(getattr(collection, "_validate_sead_rows"))
