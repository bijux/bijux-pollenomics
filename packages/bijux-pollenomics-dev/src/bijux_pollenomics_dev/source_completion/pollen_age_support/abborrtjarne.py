"""Expose the owned ABBO age-preparation files from a checked complete stage."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import sys
from typing import Any

REPLAY = Path("docs/report/pollen-reconstruction/age-interval-sensitivity/replay.py")
PARENT = Path("docs/report/pollen-reconstruction/swedish-direct-pollen/prepared")
OWNED = (
    "age-bin-support.csv",
    "input-manifest.json",
    "prepared/dataset-19913.json",
)
COPIES = ("prepared/dataset-53995.json", "prepared/dataset-54001.json")
STAGE_FILES = frozenset((*OWNED, *COPIES))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _invoke_core(repository: Path, stage: Path) -> None:
    replay = repository / REPLAY
    if not replay.is_file() or replay.is_symlink() or replay.resolve() != replay:
        raise ValueError("ABBO preparation source is not a real repository file")
    argv = sys.argv
    try:
        sys.argv = [
            str(replay),
            "prepare",
            "--repository",
            str(repository),
            "--output",
            str(stage),
        ]
        runpy.run_path(str(replay), run_name="__main__")
    finally:
        sys.argv = argv


def _stage_files(stage: Path) -> dict[str, str]:
    if stage.is_symlink() or not stage.is_dir() or stage.resolve() != stage:
        raise ValueError("ABBO preparation stage must be a real directory")
    rows: dict[str, str] = {}
    directories: set[str] = set()
    for path in stage.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("ABBO preparation created an unsafe path")
        if path.is_file():
            rows[path.relative_to(stage).as_posix()] = _sha(path)
        else:
            directories.add(path.relative_to(stage).as_posix())
    if sorted(rows) != sorted(STAGE_FILES) or directories != {"prepared"}:
        raise ValueError("ABBO preparation file population differs")
    return dict(sorted(rows.items()))


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Verify all five stage products; expose exactly three owned report files."""
    repository = repository.resolve(strict=True)
    artifacts = repository / "artifacts"
    if not artifacts.is_dir() or artifacts.is_symlink():
        raise ValueError("repository artifact root must be real")
    destination = output.resolve()
    if (
        output.is_symlink()
        or destination == artifacts
        or not destination.is_relative_to(artifacts)
        or destination.exists()
    ):
        raise ValueError("an absent repository artifact output is required")
    for ancestor in output.parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("ABBO output ancestor may not be a symlink")
    else:
        raise ValueError("ABBO output lies outside repository")
    stage_id = hashlib.sha256(
        destination.relative_to(artifacts).as_posix().encode("utf-8")
    ).hexdigest()
    stage_root = artifacts / "jobs/report-preparation/abborrtjarne" / stage_id
    if stage_root.exists() or stage_root.is_symlink():
        raise ValueError("ABBO preparation stage already exists")
    if stage_root.resolve() != stage_root:
        raise ValueError("ABBO preparation stage ancestor may not be a symlink")
    stage_root.mkdir(parents=True, exist_ok=False)
    stage = stage_root / "complete-stage"
    _invoke_core(repository, stage)
    stage_hashes = _stage_files(stage)
    for relative in COPIES:
        source = repository / PARENT / Path(relative).name
        if (
            not source.is_file()
            or source.is_symlink()
            or source.resolve() != source
            or _sha(source) != stage_hashes[relative]
        ):
            raise ValueError(f"ABBO copied source profile differs: {relative}")
    destination.mkdir(parents=True, exist_ok=False)
    for relative in OWNED:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(stage / relative, target)
        if _sha(target) != stage_hashes[relative]:
            raise ValueError(f"ABBO owned output copy differs: {relative}")
    receipt: dict[str, Any] = {
        "schema_version": "abbo-age-preparation-products.v1",
        "complete_stage_path": stage.relative_to(repository).as_posix(),
        "complete_stage_sha256": stage_hashes,
        "owned_files": list(OWNED),
        "copied_upstream_profiles": list(COPIES),
    }
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
