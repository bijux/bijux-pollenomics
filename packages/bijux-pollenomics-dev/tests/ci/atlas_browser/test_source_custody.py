"""Physical source closure cannot borrow modules from another checkout."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.atlas_browser.source_custody import _owned_source_inputs


def test_observed_modules_pin_owned_domain_helpers_and_ignore_external_runtime(
    tmp_path: Path,
) -> None:
    source = tmp_path / "packages/host/src/owned.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n")
    assert _owned_source_inputs(
        tmp_path,
        [
            ("bijux_pollenomics.adna.domain.locality", str(source)),
            ("numpy", "/other/runtime/numpy.py"),
            ("pollenomics.namespace", None),
        ],
    ) == {"packages/host/src/owned.py": hashlib.sha256(source.read_bytes()).hexdigest()}


def test_another_checkout_cannot_supply_owned_source(tmp_path: Path) -> None:
    source = tmp_path / "other/owned.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n")
    with pytest.raises(ValueError, match="outside its frozen source repository"):
        _owned_source_inputs(
            tmp_path, [("bijux_pollenomics.adna.domain.locality", str(source))]
        )


def test_symlink_source_ancestor_is_refused(tmp_path: Path) -> None:
    source = tmp_path / "real/owned.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n")
    (tmp_path / "packages").symlink_to(source.parent, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        _owned_source_inputs(
            tmp_path, [("bijux_pollenomics.owned", str(tmp_path / "packages/owned.py"))]
        )
