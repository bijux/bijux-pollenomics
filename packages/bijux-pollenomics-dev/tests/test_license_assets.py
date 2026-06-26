"""License asset synchronization coverage."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from bijux_pollenomics_dev.release.license_assets import managed_assets, synchronize_license_assets


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
