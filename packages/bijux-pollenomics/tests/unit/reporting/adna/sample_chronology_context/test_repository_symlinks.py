"""Refuse symlinked source roots and governed input files."""

from pathlib import Path

import pytest

from bijux_pollenomics.reporting.adna.sample_chronology_context.repository import (
    load_animal_sample_chronology_corpus,
)

from .support import PROJECT, write_source_repository


def test_symlinked_project_directory_fails_closed(tmp_path: Path) -> None:
    write_source_repository(tmp_path)
    project_root = tmp_path / "adna" / "governance" / "source_library" / "projects"
    project_path = project_root / PROJECT
    target = tmp_path / "project-source"
    project_path.rename(target)
    project_path.symlink_to(target, target_is_directory=True)

    with pytest.raises(ValueError, match="project inventory does not reconcile"):
        load_animal_sample_chronology_corpus(tmp_path)


def test_symlinked_governed_input_is_refused(tmp_path: Path) -> None:
    write_source_repository(tmp_path)
    chronology_path = (
        tmp_path
        / "adna"
        / "governance"
        / "source_library"
        / "projects"
        / PROJECT
        / "sample_chronology.json"
    )
    target = tmp_path / "chronology-source.json"
    chronology_path.rename(target)
    chronology_path.symlink_to(target)

    with pytest.raises(ValueError, match="input is unavailable"):
        load_animal_sample_chronology_corpus(tmp_path)
