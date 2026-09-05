from __future__ import annotations

import inspect

from bijux_pollenomics.collection.sources.sead.acquisition import full


def test_full_acquisition_import_path_is_a_package_facade() -> None:
    assert full.__file__ is not None
    assert full.__file__.endswith("acquisition/full/__init__.py")
    assert full.__all__ == [
        "NORDIC_COUNTRY_CODES",
        "SeadAcquisitionError",
        "SeadTableAcquisition",
        "acquire_sead_table",
        "assert_sead_join_complete",
        "materialize_sead_acquisition",
        "reconcile_sead_countries",
        "reconcile_sead_join",
    ]


def test_public_call_signatures_remain_stable() -> None:
    assert str(inspect.signature(full.reconcile_sead_countries)) == (
        "(rows: 'Iterable[Mapping[str, object]]', *, "
        "country_by_site_id: 'Mapping[str, str]') -> 'dict[str, object]'"
    )
    assert str(inspect.signature(full.materialize_sead_acquisition)) == (
        "(output_root: 'Path', *, acquisitions: 'Sequence[SeadTableAcquisition]', "
        "required_tables: 'Sequence[str]', "
        "country_reconciliation: 'Mapping[str, object]', "
        "join_reconciliations: 'Sequence[Mapping[str, object]]') -> 'Path'"
    )


def test_legacy_private_helpers_remain_reachable() -> None:
    for name in (
        "_build_result",
        "_canonical_bytes",
        "_child_identity",
        "_observed_schema",
        "_payload_bytes",
        "_publish_directory",
        "_safe_output_root",
        "_utc_text",
        "_validate_request",
        "_validate_table_name",
    ):
        assert callable(getattr(full, name))
