"""Selected access entrypoints import independently of prior package loading."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

import bijux_pollenomics


@pytest.mark.parametrize(
    "entrypoint", ["selection", "linked_evidence.preflight", "selection.preflight"]
)
def test_selected_access_cold_import(entrypoint: str) -> None:
    """Load each entrypoint in a fresh interpreter using the tested source tree."""
    source_root = Path(bijux_pollenomics.__file__).resolve().parents[1]
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": os.pathsep.join([str(source_root), *sys.path]),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            (
                "from importlib import import_module; from pathlib import Path; "
                "import sys; module = import_module(sys.argv[1]); "
                "assert Path(sys.argv[2]) in Path(module.__file__).resolve().parents"
            ),
            "bijux_pollenomics.collection.sources.neotoma.ancillary_store."
            + entrypoint,
            str(source_root),
        ],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "order",
    [
        ("linked_evidence.preflight", "selection.batch", "selection"),
        ("selection.batch", "linked_evidence.preflight", "selection"),
        ("selection", "linked_evidence.preflight", "selection.batch"),
    ],
)
def test_public_batch_identity_across_fresh_import_orders(
    order: tuple[str, ...],
) -> None:
    """The public batch function remains its implementation across import orders."""
    source_root = Path(bijux_pollenomics.__file__).resolve().parents[1]
    prefix = "bijux_pollenomics.collection.sources.neotoma.ancillary_store."
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": os.pathsep.join([str(source_root), *sys.path]),
    }
    script = (
        "from importlib import import_module; import sys; "
        "[import_module(sys.argv[1] + name) for name in sys.argv[2:]]; "
        "api=import_module(sys.argv[1] + 'selection'); "
        "impl=import_module(sys.argv[1] + 'selection.typed_batch'); "
        "assert api.read_neotoma_ancillary_facets is impl.read_neotoma_ancillary_facets"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", script, prefix, *order],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_facet_and_linked_operations_after_linked_first_import(tmp_path: Path) -> None:
    """Run both real guarded operations after the previously failing cold import."""
    source_root = Path(bijux_pollenomics.__file__).resolve().parents[1]
    repository = source_root.parents[2]
    test_file = (
        repository / "packages/bijux-pollenomics/tests/unit/collection/sources/neotoma/"
        "ancillary_store/selection/batch/test_operations.py"
    )
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": os.pathsep.join(
            [str(source_root), str(source_root.parent), *sys.path]
        ),
    }
    script = (
        "import sys; "
        "import bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.preflight; "
        "import pytest; sys.exit(pytest.main(sys.argv[1:]))"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            script,
            "-q",
            "-o",
            f"cache_dir={tmp_path / 'cache'}",
            f"--basetemp={tmp_path / 'run'}",
            f"{test_file}::test_actual_guards_return_immutable_metadata_without_any_entity",
            f"{test_file}::test_distinct_targets_share_each_same_verified_evidence_part_once",
        ],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
