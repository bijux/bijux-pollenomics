"""Publish byte custody for the retained ESSD uncertainty products, without math."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any

TARGET = Path("docs/report/publication-replay/landclim-published-window-uncertainty")
PROVENANCE = Path("docs/report/publication-replay/landclim-published-window-provenance")
HISTORY = TARGET / "source/retained-custody.json"
HISTORY_SHA256 = "02be1738a20737a9c8ec2b9de065fd88e67162f92223d9ef4417bb4be4f48137"
CORE = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/published_window_uncertainty.py"
)
WRITER = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/essd/uncertainty_custody.py"
)
OUTPUTS = ("REPORT.md", "report.json", "taxon-envelopes.csv")
PROVENANCE_OUTPUTS = ("REPORT.md", "report.json", "paper-correspondence.csv")
INPUTS = (
    CORE,
    HISTORY,
    *(PROVENANCE / name for name in (*PROVENANCE_OUTPUTS, "manifest.json")),
    *(TARGET / name for name in OUTPUTS),
)
SCOPE = "Current input/output byte accounting; original execution and historical raw inputs not established by this manifest."


def _regular(path: Path) -> Path:
    path = path.absolute()
    if any(parent.is_symlink() for parent in (path, *path.parents)) or not stat.S_ISREG(
        path.stat().st_mode
    ):
        raise ValueError("Real regular custody input required")
    return path


def _identity(path: Path) -> dict[str, Any]:
    content = _regular(path).read_bytes()
    return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def _entry(value: object, actual: dict[str, Any]) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != {"bytes", "sha256"}
        or type(value["bytes"]) is not int
        or value != actual
    ):
        raise ValueError("Custody byte count or digest mismatch")


def build_manifest(repository: Path) -> dict[str, Any]:
    """Authenticate the fixed retained profile and record current metadata only."""
    identities = {name.as_posix(): _identity(repository / name) for name in INPUTS}
    if identities[HISTORY.as_posix()]["sha256"] != HISTORY_SHA256:
        raise ValueError("Retained historical custody capsule differs")
    history = json.loads((repository / HISTORY).read_bytes())
    if history.get(
        "schema_version"
    ) != "landclim-published-window-uncertainty-custody.v1" or set(
        history.get("outputs", {})
    ) != set(OUTPUTS):
        raise ValueError("Unsupported retained uncertainty custody population")
    if set(history.get("inputs", {})) != {
        CORE.as_posix(),
        (PROVENANCE / "paper-correspondence.csv").as_posix(),
        (PROVENANCE / "report.json").as_posix(),
    }:
        raise ValueError("Retained uncertainty input population differs")
    for name, expected in history["inputs"].items():
        if name != CORE.as_posix():
            _entry(expected, identities[name])
    for name, expected in history["outputs"].items():
        _entry(expected, identities[(TARGET / name).as_posix()])
    provenance = json.loads((repository / PROVENANCE / "manifest.json").read_bytes())
    if provenance.get(
        "schema_version"
    ) != "landclim-published-window-provenance-custody.v1" or set(
        provenance.get("outputs", {})
    ) != set(PROVENANCE_OUTPUTS):
        raise ValueError("Unsupported provenance custody population")
    for name, expected in provenance["outputs"].items():
        _entry(expected, identities[(PROVENANCE / name).as_posix()])
    return {
        "schema_version": "landclim-published-window-uncertainty-custody.v1",
        "inputs": identities,
        "outputs": {name: identities[(TARGET / name).as_posix()] for name in OUTPUTS},
        "historical_comparison": history["historical_comparison"],
        "historical_producer_identity": {
            "path": CORE.as_posix(),
            **history["inputs"][CORE.as_posix()],
        },
        "admission": history["admission"],
        "custody_scope": SCOPE,
        "custody_writer": {"path": WRITER.as_posix(), **_identity(repository / WRITER)},
    }


def run(repository: Path, output: Path) -> None:
    """Publish one absent artifact manifest after unchanged-input verification."""
    repository = repository.absolute()
    if (
        any(parent.is_symlink() for parent in (repository, *repository.parents))
        or not repository.is_dir()
    ):
        raise ValueError("Real repository directory required")
    output = output.absolute()
    artifacts = repository / "artifacts"
    if (
        ".." in output.parts
        or output == artifacts
        or not output.is_relative_to(artifacts)
        or output.exists()
        or output.is_symlink()
    ):
        raise ValueError("Absent repository artifact destination required")
    for parent in output.parents:
        if parent == repository:
            break
        if not parent.is_dir() or parent.is_symlink():
            raise ValueError("Real existing artifact ancestors required")
    before = {
        name.as_posix(): _identity(repository / name) for name in (*INPUTS, WRITER)
    }
    manifest = build_manifest(repository)
    with tempfile.TemporaryDirectory(
        prefix=".uncertainty-custody-", dir=output.parent
    ) as staging:
        staged = Path(staging) / "products"
        staged.mkdir()
        (staged / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        after = {
            name.as_posix(): _identity(repository / name) for name in (*INPUTS, WRITER)
        }
        if before != after:
            raise ValueError("Custody inputs changed during publication")
        if output.exists() or output.is_symlink():
            raise ValueError("Custody destination appeared during publication")
        try:
            output.mkdir()
        except FileExistsError as error:
            raise ValueError(
                "Custody destination appeared during publication"
            ) from error
        reserved = output.stat(follow_symlinks=False)
        descriptor = os.open(output, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            opened = os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino) != (reserved.st_dev, reserved.st_ino):
                raise ValueError("Reserved custody destination changed")
            current = output.stat(follow_symlinks=False)
            if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
                raise ValueError("Reserved custody destination changed")
            # Linking the complete staged file publishes without replacing a competitor.
            os.link(
                staged / "manifest.json",
                "manifest.json",
                dst_dir_fd=descriptor,
                follow_symlinks=False,
            )
            current = output.stat(follow_symlinks=False)
            if (current.st_dev, current.st_ino) != (opened.st_dev, opened.st_ino):
                raise ValueError("Reserved custody destination changed")
        finally:
            os.close(descriptor)


def main(argv: list[str] | None = None) -> int:
    """Publish the fixed-profile uncertainty byte manifest without comparisons."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
