"""License asset synchronization coverage."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bijux_pollenomics_dev.release.license_assets import (
    managed_assets,
    synchronize_license_assets,
)


def test_managed_assets_cover_every_workspace_package() -> None:
    package_targets = {asset.target.parent.name for asset in managed_assets()}
    assert package_targets == {
        "bijux-pollenomics",
        "pollenomics",
        "bijux-pollenomics-dev",
    }


def test_license_assets_match_repository_root_sources() -> None:
    failures: list[str] = []

    for asset in managed_assets():
        if asset.target.is_symlink():
            failures.append(f"{asset.target}: expected regular file")
            continue
        if not asset.target.is_file():
            failures.append(f"{asset.target}: expected file")
            continue
        if asset.target.read_bytes() != asset.source.read_bytes():
            failures.append(f"{asset.target}: file contents drifted from root source")

    assert not failures, "managed legal asset synchronization failed:\n" + "\n".join(
        failures
    )


def test_license_assets_are_synchronized() -> None:
    assert synchronize_license_assets(check=True) == []


def test_independent_license_is_never_replaced_by_repository_license(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.bijux_pollenomics]\npackages = ["host", "engine"]\n'
        'package_owned_legal_assets = ["engine"]\n'
    )
    engine = tmp_path / "packages" / "engine"
    engine.mkdir(parents=True)
    (engine / "LICENSE").write_text("Independent source license")
    (engine / "NOTICE").write_text("Original source attribution")
    assets = managed_assets(tmp_path)
    assert {asset.target.parent.name for asset in assets} == {"host"}
    assert (engine / "LICENSE").read_text() == "Independent source license"
    (engine / "NOTICE").unlink()
    with pytest.raises(ValueError, match="package-owned legal asset"):
        managed_assets(tmp_path)


@pytest.mark.parametrize("owned", ['["typo"]', '["host", "host"]', '"host"'])
def test_independent_license_policy_rejects_unknown_or_ambiguous_owners(
    tmp_path: Path, owned: str
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.bijux_pollenomics]\npackages = ["host"]\n'
        f"package_owned_legal_assets = {owned}\n"
    )
    with pytest.raises(ValueError, match="unique workspace packages"):
        managed_assets(tmp_path)
