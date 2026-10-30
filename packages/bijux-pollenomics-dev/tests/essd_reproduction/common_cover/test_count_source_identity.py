"""Keep every new count ingress and its reused numeric source in current custody."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics_dev.essd_reproduction.common_cover import (
    conditional_adequacy,
    count_admission,
    sample_dependence_bounds,
    within_site_homogeneity,
)
from bijux_pollenomics_lra.models.errors import ValidationError

_DEV = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
_LRA = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/"
_LOCAL = _DEV + "essd_reproduction/common_cover/count_admission.py"
_OWNED = _LRA + "reconstruction/likelihood/multisite_likelihood.py"
_COMMON = (
    _DEV + "essd_reproduction/common_cover/cohort.py",
    _DEV + "essd_reproduction/physical_forward/inputs.py",
    _DEV + "source_completion/pollen_reconstruction/swedish_static_basin/sources.py",
    _LRA + "models/validation.py",
)


@pytest.mark.parametrize("name", ("adequacy", "homogeneity", "bounds"))
def test_current_source_gate_binds_both_added_modules_and_all_old_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """Observe real origins with fake Git, without materializing source bodies."""
    repository = Path(__file__).resolve().parents[5]
    functions: dict[str, Callable[[Path], str]] = {
        "adequacy": conditional_adequacy._revision,
        "homogeneity": within_site_homogeneity._revision,
        "bounds": sample_dependence_bounds._revision,
    }
    own_name = {
        "adequacy": "conditional_adequacy.py",
        "homogeneity": "within_site_homogeneity.py",
        "bounds": "sample_dependence_bounds.py",
    }[name]
    expected = set(_COMMON) | {
        _LOCAL,
        _OWNED,
        _DEV + "essd_reproduction/common_cover/" + own_name,
    }
    if name == "homogeneity":
        expected.add(_LRA + "reconstruction/uncertainty/two_taxon_counting.py")
    if name == "bounds":
        expected.add(_DEV + "essd_reproduction/common_cover/within_site_homogeneity.py")
    calls: list[list[str]] = []
    damage = ""

    def git(argv: list[str], **_: object) -> bytes:
        assert argv[:3] == ["git", "-C", str(repository)]
        calls.append(argv.copy())
        command = argv[3]
        if command == "rev-parse":
            assert argv[4:] == ["HEAD"]
            return b"1" * 40
        paths = argv[argv.index("--") + 1 :]
        assert len(paths) == len(expected) and set(paths) == expected
        if command == "ls-files":
            assert argv[4:6] == ["--error-unmatch", "--"]
            if damage in {"untracked_local", "untracked_owned"}:
                wanted = _LOCAL if damage == "untracked_local" else _OWNED
                assert wanted in paths
                raise subprocess.CalledProcessError(1, argv)
        else:
            assert command == "diff" and argv[4:7] == ["--exit-code", "1" * 40, "--"]
            if damage in {"dirty_local", "dirty_owned"}:
                wanted = _LOCAL if damage == "dirty_local" else _OWNED
                assert wanted in paths
                raise subprocess.CalledProcessError(1, argv)
        return b""

    monkeypatch.setattr(subprocess, "check_output", git)
    assert not tuple(tmp_path.iterdir())
    for damaged in (
        "untracked_local",
        "untracked_owned",
        "dirty_local",
        "dirty_owned",
        "local_origin",
        "owned_origin",
    ):
        damage = ""
        calls.clear()
        assert functions[name](repository) == "1" * 40
        assert [call[3] for call in calls] == ["rev-parse", "ls-files", "diff"]
        with monkeypatch.context() as patch:
            damage = damaged
            if damaged == "local_origin":
                patch.setattr(
                    count_admission, "__file__", conditional_adequacy.__file__
                )
            elif damaged == "owned_origin":
                patch.setattr(
                    count_admission.multisite_likelihood,
                    "__file__",
                    conditional_adequacy.__file__,
                )
            error = (
                ValidationError
                if damaged.endswith("origin")
                else subprocess.CalledProcessError
            )
            with pytest.raises(error):
                functions[name](repository)
    assert not tuple(tmp_path.iterdir())
