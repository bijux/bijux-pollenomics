"""Keep source custody usable without loading scientific report execution."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.source_paths import safe_source_file


def test_source_helpers_import_without_the_scientific_runtime() -> None:
    import bijux_pollenomics_dev

    source_root = Path(bijux_pollenomics_dev.__file__).resolve().parents[1]
    program = """
import importlib.abc
import sys
sys.path.insert(0, sys.argv[1])
class RefuseScientificRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'bijux_pollenomics', 'numpy', 'pyproj'}:
            raise AssertionError('source helper loaded execution: ' + fullname)
sys.meta_path.insert(0, RefuseScientificRuntime())
import bijux_pollenomics_dev.ci.report_rebuild as public
from bijux_pollenomics_dev.ci.report_rebuild import artifact_paths
from bijux_pollenomics_dev.ci.report_rebuild.source_paths import safe_source_file
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import validated_external_report_sources
assert public.ReportRebuildError.__name__ == 'ReportRebuildError'
assert set(public.__all__) <= set(dir(public))
try:
    public.unrecognized_workflow
except AttributeError:
    pass
else:
    raise AssertionError('unknown public attribute accepted')
assert 'bijux_pollenomics_dev.ci.report_rebuild.workflow' not in sys.modules
assert 'bijux_pollenomics_dev.ci.report_rebuild.configured_owner' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", program, str(source_root)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_lazy_exports_preserve_actual_workflow_function_identity() -> None:
    import bijux_pollenomics_dev.ci.report_rebuild as public
    from bijux_pollenomics_dev.ci.report_rebuild import source_paths, workflow

    for name in public.__all__:
        if name != "ReportRebuildError":
            assert getattr(public, name) is getattr(workflow, name)
    assert source_paths.safe_source_file is safe_source_file


def test_source_guard_preserves_regular_file_and_symlink_refusals(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    source = repository / "source.json"
    source.write_text("{}\n", encoding="utf-8")
    assert safe_source_file(repository, "source.json", "source") == source
    (repository / "linked.json").symlink_to(source)
    (repository / "linked-directory").symlink_to(repository, target_is_directory=True)
    for relative in ("linked.json", "linked-directory/source.json", "missing.json"):
        with pytest.raises(ReportRebuildError):
            safe_source_file(repository, relative, "source")
    with pytest.raises(ReportRebuildError):
        safe_source_file(repository, "../source.json", "source")
