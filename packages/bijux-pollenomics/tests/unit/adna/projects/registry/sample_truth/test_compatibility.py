from __future__ import annotations

import inspect
import pickle

from bijux_pollenomics.adna.projects.registry import sample_truth


EXPECTED_EXPORTS = [
    "build_animal_sample_aggregation_warnings",
    "build_animal_sample_foundation_truth",
    "build_animal_sample_product_contract",
    "build_project_locality_count_drift",
    "build_species_sample_count_drift",
    "render_animal_sample_aggregation_warnings_markdown",
    "render_animal_sample_foundation_truth_markdown",
    "render_animal_sample_product_contract_markdown",
]

EXPECTED_SIGNATURES = {
    "_build_project_truth_row": "(*, species_latin_name: 'str', species_common_name: 'str', project_accession: 'str', sample_rows: 'list[dict[str, object]]', locality_rows: 'list[dict[str, object]]') -> 'dict[str, object]'",
    "_load_sample_rows": "(species_root: 'Path') -> 'list[dict[str, object]]'",
    "_sample_truth_status": "(sample_row: 'dict[str, object]') -> 'str'",
    "build_animal_sample_aggregation_warnings": "(data_root: 'Path', report_root: 'Path') -> 'dict[str, object]'",
    "build_animal_sample_foundation_truth": "(data_root: 'Path') -> 'dict[str, object]'",
    "build_project_locality_count_drift": "(data_root: 'Path') -> 'tuple[dict[str, object], ...]'",
}


def test_facade_preserves_exports_and_callable_shapes() -> None:
    assert sample_truth.__all__ == EXPECTED_EXPORTS
    assert {
        name: str(inspect.signature(getattr(sample_truth, name)))
        for name in EXPECTED_SIGNATURES
    } == EXPECTED_SIGNATURES


def test_public_functions_retain_pickle_import_identity() -> None:
    for name in EXPECTED_EXPORTS:
        function = getattr(sample_truth, name)
        assert pickle.loads(pickle.dumps(function, protocol=5)) is function
        assert function.__module__ == sample_truth.__name__
