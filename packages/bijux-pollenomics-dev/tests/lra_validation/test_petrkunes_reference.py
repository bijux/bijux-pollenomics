"""Metadata-only R checks preserve the tagged-reference execution boundary."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "docs/report/method-certification/petrkunes-r-comparison/replay.R"
LIBRARY = ROOT / "artifacts/qualification/native-reference/library"


def metadata_prefix() -> str:
    """Use the maintained preflight, stopping before either reference is read."""
    prefix, marker, _ = SOURCE.read_text().partition("reference <- file.path(author,")
    assert marker
    return prefix


def run_metadata(
    directory: Path,
    *,
    source_version: str = "0.1.2",
    available_library: bool = True,
    existing_output: bool = False,
    trailer: str = "",
) -> tuple[subprocess.CompletedProcess[str], Path]:
    rscript = shutil.which("Rscript")
    if not rscript:
        pytest.skip("R metadata checks need Rscript; no source-R parity is inferred")
    if not (LIBRARY / "zipfR/DESCRIPTION").is_file():
        pytest.skip("R metadata checks need the qualified shared zipfR installation")
    author = directory / "author"
    tagged = directory / "tagged"
    author.mkdir()
    tagged.mkdir()
    # This controlled metadata is not a copied package or reference function.
    (tagged / "DESCRIPTION").write_text(f"Version: {source_version}\n")
    library = LIBRARY
    if not available_library:
        library = directory / "empty-library"
        library.mkdir()
    output = directory / "result"
    if existing_output:
        output.mkdir()
        (output / "preserved.txt").write_text("original output")
    script = metadata_prefix() + trailer
    environment = dict(os.environ, TMPDIR=str(directory))
    process = subprocess.run(
        [
            rscript,
            "--vanilla",
            "-e",
            script,
            str(author),
            str(tagged),
            str(library),
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=15,
        env=environment,
        check=False,
    )
    return process, output


def test_same_process_records_literal_version_namespace_and_runtime_without_models(
    tmp_path: Path,
) -> None:
    process, output = run_metadata(
        tmp_path,
        trailer="set.seed(750225)\nseed_before <- .Random.seed\n"
        'record_runtime("controlled_metadata_after", append = TRUE)\n'
        "stopifnot(identical(.Random.seed, seed_before))\n",
    )
    assert process.returncode == 0, process.stderr
    text = (output / "runtime.txt").read_text()
    assert text.count("zipfR_DESCRIPTION_Version=0.6-70") == 2
    assert text.count(f"zipfR_namespace={LIBRARY / 'zipfR'}") == 2
    assert "capture=before_source_calls" in text
    assert "capture=controlled_metadata_after" in text
    assert text.count("R version 4.6.0") == 2
    assert text.count("RNGkind=") == 2
    assert "BLAS:" in text and "LAPACK:" in text
    assert sorted(path.name for path in output.iterdir()) == ["runtime.txt"]


@pytest.mark.parametrize("version", ["0.1.3", "0.1-2"])
def test_changed_literal_tagged_source_version_refuses_before_reference_read(
    tmp_path: Path, version: str
) -> None:
    process, output = run_metadata(tmp_path, source_version=version)
    assert process.returncode != 0
    assert "Pinned R dependency or secondary LRA version changed" in process.stderr
    assert not (output / "runtime.txt").exists()
    assert not list(output.glob("*.csv"))


def test_missing_qualified_dependency_refuses_without_numeric_output(
    tmp_path: Path,
) -> None:
    process, output = run_metadata(tmp_path, available_library=False)
    assert process.returncode != 0
    assert not list(output.glob("*.csv"))
    assert not (output / "runtime.txt").exists()


def test_existing_output_is_preserved_before_loading_or_running_sources(
    tmp_path: Path,
) -> None:
    process, output = run_metadata(tmp_path, existing_output=True)
    assert process.returncode != 0
    assert "Output directory must be absent" in process.stderr
    assert (output / "preserved.txt").read_text() == "original output"
    assert sorted(path.name for path in output.iterdir()) == ["preserved.txt"]


def test_changed_expected_namespace_refuses_recording_after_source_boundary(
    tmp_path: Path,
) -> None:
    process, output = run_metadata(
        tmp_path,
        trailer=f"zipfr_namespace <- {json.dumps(str(tmp_path / 'foreign'))}\n"
        'record_runtime("controlled_metadata_after", append = TRUE)\n',
    )
    assert process.returncode != 0
    assert "Loaded zipfR namespace changed" in process.stderr
    assert "controlled_metadata_after" not in (output / "runtime.txt").read_text()
    assert not list(output.glob("*.csv"))
