"""Keep bounded process execution independent of scientific host dependencies."""

from __future__ import annotations

import importlib
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]


def test_cold_bounded_execution_uses_only_standard_library(tmp_path: Path) -> None:
    program = """
import importlib.abc
from pathlib import Path
import sys

sys.path[:0] = sys.argv[1:3]
class RefuseScientificHost(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'bijux_pollenomics','numpy','scipy','pyproj'}:
            raise AssertionError('unexpected scientific dependency: ' + fullname)
sys.meta_path.insert(0, RefuseScientificHost())
from bijux_pollenomics_dev.ci.atlas_media import AtlasMediaError, process_execution
import bijux_pollenomics_dev.ci.atlas_media as media
assert 'select_stories' in dir(media)
assert 'bijux_pollenomics_dev.ci.atlas_media.storyboards' not in sys.modules
assert 'bijux_pollenomics_dev.ci.atlas_media.run_evidence' not in sys.modules
assert not any(name.startswith('bijux_pollenomics.') for name in sys.modules)
done = process_execution.run_bounded_argv(
    (sys.executable, '-I', '-B', '-c', "print('bounded',end='')"),
    cwd=Path(sys.argv[3]), timeout_seconds=5, max_output_bytes=7,
)
assert done.returncode == 0 and done.stdout == b'bounded' and done.stderr == b''
assert not done.timed_out and done.termination == 'not_required'
for command, limit in [
    ((sys.executable, '-I', '-B', '-c', "print('overflow',end='')"), 7),
    ((sys.executable, 'bad\\0argument'), 7),
]:
    try:
        process_execution.run_bounded_argv(command,cwd=Path(sys.argv[3]),
                                           timeout_seconds=5,max_output_bytes=limit)
    except process_execution.BoundedProcessError:
        pass
    else:
        raise AssertionError('invalid or over-limit execution accepted')
stdout = Path(sys.argv[3]) / 'logged.stdout.log'
stderr = Path(sys.argv[3]) / 'logged.stderr.log'
process_execution._run_logged(
    (sys.executable, '-I', '-B', '-c', "print('receipt')"),
    cwd=Path(sys.argv[3]),stdout_path=stdout,stderr_path=stderr,timeout_seconds=5,
)
assert stdout.read_bytes() == b'receipt\\n'
assert stdout.with_name('logged.execution.json').is_file()
"""
    subprocess.run(
        (
            sys.executable,
            "-I",
            "-B",
            "-S",
            "-c",
            program,
            str(ROOT / "packages/bijux-pollenomics-dev/src"),
            str(ROOT / "packages/bijux-pollenomics/src"),
            str(tmp_path),
        ),
        check=True,
        timeout=20,
        capture_output=True,
    )


@pytest.mark.parametrize(
    "name,module",
    [
        ("build_gallery_manifest", "gallery"),
        ("write_gallery_manifest", "gallery"),
        ("build_run_evidence_index", "run_evidence"),
        ("write_run_evidence_index", "run_evidence"),
        ("load_storyboard_manifest", "storyboards"),
        ("select_stories", "storyboards"),
    ],
)
def test_lazy_media_exports_preserve_function_identity(name: str, module: str) -> None:
    media = importlib.import_module("bijux_pollenomics_dev.ci.atlas_media")
    source = importlib.import_module(f"{media.__name__}.{module}")
    assert name in media.__all__ and name in dir(media)
    assert getattr(media, name) is getattr(source, name)
    assert getattr(media, name) is getattr(media, name)


def test_unknown_media_export_remains_an_attribute_error() -> None:
    media = importlib.import_module("bijux_pollenomics_dev.ci.atlas_media")
    name = "unowned_export"
    with pytest.raises(AttributeError, match="has no attribute"):
        getattr(media, name)


@pytest.mark.parametrize(
    "entry",
    [
        "bijux_pollenomics_dev.ci.atlas_media.contracts",
        "bijux_pollenomics_dev.ci.scientific_reading.runner",
    ],
)
def test_reader_cli_and_media_contracts_do_not_import_scientific_host(
    tmp_path: Path, entry: str
) -> None:
    program = """
import importlib.abc
import runpy
import sys

sys.path[:0] = sys.argv[1:3]
entry = sys.argv[3]
class RefuseScientificHost(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'bijux_pollenomics', 'numpy', 'scipy', 'pyproj'}:
            raise AssertionError('unexpected scientific dependency: ' + fullname)
sys.meta_path.insert(0, RefuseScientificHost())
if entry.endswith('.runner'):
    sys.argv = [entry, '--help']
    try:
        runpy.run_module(entry, run_name='__main__')
    except SystemExit as error:
        assert error.code == 0
    else:
        raise AssertionError('reader CLI did not complete its help request')
else:
    importlib.import_module(entry)
assert not any(name == 'bijux_pollenomics' or name.startswith('bijux_pollenomics.')
               for name in sys.modules)
"""
    subprocess.run(
        (
            sys.executable,
            "-I",
            "-B",
            "-S",
            "-c",
            program,
            str(ROOT / "packages/bijux-pollenomics-dev/src"),
            str(ROOT / "packages/bijux-pollenomics/src"),
            entry,
        ),
        cwd=tmp_path,
        check=True,
        timeout=20,
        capture_output=True,
    )
