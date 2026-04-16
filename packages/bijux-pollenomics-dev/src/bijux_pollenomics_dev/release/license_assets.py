"""Synchronize package license assets from repository root sources."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil
import tomllib
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[5]
MANAGED_FILENAMES: tuple[str, str] = ("LICENSE", "NOTICE")


@dataclass(frozen=True)
class ManagedAsset:
    """One root-to-package file mapping managed by this synchronizer."""

    source: Path
    target: Path


def _workspace_metadata(root: Path = REPO_ROOT) -> dict[str, Any]:
    """Load workspace metadata from the repository pyproject file."""
    with (root / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return cast(dict[str, Any], data["tool"]["bijux_pollenomics"])


def managed_assets(root: Path = REPO_ROOT) -> tuple[ManagedAsset, ...]:
    """Enumerate package license assets generated from root source files."""
    packages = cast(list[str], _workspace_metadata(root)["packages"])
    assets: list[ManagedAsset] = []
    for package_slug in packages:
        package_dir = root / "packages" / package_slug
        for filename in MANAGED_FILENAMES:
            assets.append(
                ManagedAsset(
                    source=root / filename,
                    target=package_dir / filename,
                )
            )
    return tuple(assets)


def _files_equal(source: Path, target: Path) -> bool:
    """Return whether source and target currently have identical bytes."""
    if not target.exists():
        return False
    return source.read_bytes() == target.read_bytes()


def synchronize_license_assets(*, check: bool = False) -> list[Path]:
    """Sync root license assets into package directories or report drift."""
    changed: list[Path] = []
    for asset in managed_assets():
        if _files_equal(asset.source, asset.target):
            continue
        changed.append(asset.target)
        if not check:
            asset.target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(asset.source, asset.target)
    return changed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the license asset synchronizer."""
    parser = argparse.ArgumentParser(
        prog="license-assets",
        description="Synchronize package license assets from repository root files.",
    )
    parser.add_argument(
        "command",
        choices=("sync", "check"),
        help="`sync` writes package files, `check` reports drift only.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entrypoint."""
    args = parse_args(argv)
    changed = synchronize_license_assets(check=args.command == "check")
    if changed:
        for path in changed:
            print(path.relative_to(REPO_ROOT))
        if args.command == "check":
            return 1
    return 0


__all__ = [
    "ManagedAsset",
    "managed_assets",
    "parse_args",
    "synchronize_license_assets",
    "main",
]
