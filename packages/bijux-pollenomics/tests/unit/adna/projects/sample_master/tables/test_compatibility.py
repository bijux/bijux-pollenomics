"""Compatibility and ownership boundaries for sample-master table adapters."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from bijux_pollenomics.adna.projects.sample_master import tables

_LEGACY_FUNCTIONS = (
    "_build_goat_canary_rows",
    "_build_goat_imputation_rows",
    "_build_goat_qinghai_rows",
    "_build_horse_comparative_panel_rows",
    "_build_horse_lab_anchor_rows",
    "_build_horse_nature_rows",
    "_build_horse_panel_context_rows",
    "_build_horse_time_series_rows",
    "_build_sheep_table_rows",
    "_cached_xlsx_member_rows",
    "_cached_xlsx_rows",
    "_read_xlsx_member_rows",
    "_read_xlsx_rows",
    "_xlsx_shared_strings",
    "_xlsx_sheet_targets",
)

_ROW_BUILDER_PARAMETERS = ("species", "project", "source_path", "rows")


def test_facade_preserves_legacy_function_inventory_and_signatures() -> None:
    assert tuple(tables.__all__) == _LEGACY_FUNCTIONS
    assert all(callable(getattr(tables, name)) for name in _LEGACY_FUNCTIONS)

    parameters = {
        name: tuple(inspect.signature(getattr(tables, name)).parameters)
        for name in _LEGACY_FUNCTIONS
    }
    assert parameters == {
        "_build_goat_canary_rows": _ROW_BUILDER_PARAMETERS,
        "_build_goat_imputation_rows": _ROW_BUILDER_PARAMETERS,
        "_build_goat_qinghai_rows": _ROW_BUILDER_PARAMETERS,
        "_build_horse_comparative_panel_rows": _ROW_BUILDER_PARAMETERS,
        "_build_horse_lab_anchor_rows": _ROW_BUILDER_PARAMETERS,
        "_build_horse_nature_rows": (
            *_ROW_BUILDER_PARAMETERS,
            "archive_sample_labels",
        ),
        "_build_horse_panel_context_rows": _ROW_BUILDER_PARAMETERS,
        "_build_horse_time_series_rows": _ROW_BUILDER_PARAMETERS,
        "_build_sheep_table_rows": (
            "species",
            "project",
            "source_path",
            "table_locator_prefix",
            "header_row_index",
            "rows",
            "sample_label_key",
            "locality_key",
            "chronology_key",
        ),
        "_cached_xlsx_member_rows": ("cache_key",),
        "_cached_xlsx_rows": ("cache_key",),
        "_read_xlsx_member_rows": ("bundle_path", "member_name", "sheet_name"),
        "_read_xlsx_rows": ("workbook_path", "sheet_name"),
        "_xlsx_shared_strings": ("workbook",),
        "_xlsx_sheet_targets": ("workbook",),
    }

    row_builder_names = _LEGACY_FUNCTIONS[:9]
    assert all(
        all(
            parameter.kind is inspect.Parameter.KEYWORD_ONLY
            for parameter in inspect.signature(
                getattr(tables, name)
            ).parameters.values()
        )
        for name in row_builder_names
    )
    for name in ("_read_xlsx_member_rows", "_read_xlsx_rows"):
        function_parameters = tuple(
            inspect.signature(getattr(tables, name)).parameters.values()
        )
        assert function_parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        assert all(
            parameter.kind is inspect.Parameter.KEYWORD_ONLY
            for parameter in function_parameters[1:]
        )


def test_legacy_functions_have_one_intent_named_implementation_owner() -> None:
    package_root = Path(tables.__file__).parent
    owners: dict[str, list[str]] = {name: [] for name in _LEGACY_FUNCTIONS}
    for module_path in package_root.glob("*.py"):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in owners:
                owners[node.name].append(module_path.name)

    assert owners == {
        "_build_goat_canary_rows": ["goat_canary.py"],
        "_build_goat_imputation_rows": ["goat_imputation.py"],
        "_build_goat_qinghai_rows": ["goat_qinghai.py"],
        "_build_horse_comparative_panel_rows": ["horse_chronology.py"],
        "_build_horse_lab_anchor_rows": ["horse_panels.py"],
        "_build_horse_nature_rows": ["horse_nature.py"],
        "_build_horse_panel_context_rows": ["horse_panels.py"],
        "_build_horse_time_series_rows": ["horse_chronology.py"],
        "_build_sheep_table_rows": ["sheep.py"],
        "_cached_xlsx_member_rows": ["workbook.py"],
        "_cached_xlsx_rows": ["workbook.py"],
        "_read_xlsx_member_rows": ["workbook.py"],
        "_read_xlsx_rows": ["workbook.py"],
        "_xlsx_shared_strings": ["workbook.py"],
        "_xlsx_sheet_targets": ["workbook.py"],
    }


def test_table_adapter_package_is_bounded_by_durable_responsibility() -> None:
    package_root = Path(tables.__file__).parent
    modules = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in package_root.glob("*.py")
        if path.name != "__init__.py"
    }

    assert frozenset(modules) == {
        "goat_canary.py",
        "goat_imputation.py",
        "goat_qinghai.py",
        "horse_chronology.py",
        "horse_nature.py",
        "horse_panels.py",
        "sheep.py",
        "workbook.py",
    }
    assert len(modules) <= 10
    assert max(modules.values()) <= 220
