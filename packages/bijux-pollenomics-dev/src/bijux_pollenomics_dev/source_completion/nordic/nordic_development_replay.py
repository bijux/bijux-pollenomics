"""Replay the current original development producer on exact historical inputs."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import shutil
import stat
import sys
from typing import Any

SOURCE = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/nordic_pollen_development.py"
)
PACKET = Path("data/neotoma/pollen-development")
HISTORICAL_PUBLICATION = Path("docs/report/regions/nordic/direct-pollen/manifest.json")
ORIGINAL_INPUT_HASHES = {
    "publication-manifest.json": "3e7814bf9697783397cdce11639ebc861620a6a3c9d9295d1357ab69bc7b5edf",
    "prepared/input-manifest.json": "d1e20733eeabde12ab8ab2ee3ff687cd854c2fee4269fb20fe175365267d99d5",
    "prepared/inputs/training-DK.json": "def96acd422e9a4975ee8fff3b79a2127c4d1747b3345d2d24296b9670070700",
    "prepared/inputs/training-FI.json": "908f2868c5b8020878119329cb0de3c941ac680f54fdb4ca073a83776920793f",
    "prepared/inputs/training-NO.json": "c16fd213650f022076ad157a4b3f09c96c4c9d6bfd889c06180e068dceae305f",
}
OUTPUT_FILES = {"report.json", "trial-scores.csv.gz"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _real_file(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("historical development input outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("historical development input uses symlink")
    if not stat.S_ISREG(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("historical development input is not a real regular file")
    return path


def _destination(repository: Path, output: Path) -> Path:
    if (
        not repository.is_absolute()
        or repository.is_symlink()
        or repository.resolve() != repository
    ):
        raise ValueError("repository must be a real absolute path")
    artifacts = repository / "artifacts"
    if artifacts.is_symlink() or not stat.S_ISDIR(artifacts.lstat().st_mode):
        raise ValueError("repository artifacts directory is not real")
    if not output.is_absolute() or output.is_symlink():
        raise ValueError("output must be real and absolute")
    for ancestor in output.parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("output ancestor uses symlink")
    else:
        raise ValueError("output is outside repository")
    if (
        output.exists()
        or output.resolve() == artifacts
        or not output.resolve().is_relative_to(artifacts)
    ):
        raise ValueError("absent artifact output required")
    return artifacts


def _packet(repository: Path) -> Path:
    packet = repository / PACKET
    if packet.is_symlink() or packet.resolve() != packet or not packet.is_dir():
        raise ValueError("historical input packet root must be a real directory")
    expected_files = set(ORIGINAL_INPUT_HASHES) | {"custody.json"}
    expected_dirs = {"prepared", "prepared/inputs"}
    actual_files = set()
    actual_dirs = set()
    for path in packet.rglob("*"):
        relative = path.relative_to(packet).as_posix()
        if path.is_symlink():
            raise ValueError("historical input packet uses symlink")
        if path.is_dir():
            actual_dirs.add(relative)
        else:
            actual_files.add(relative)
    if actual_files != expected_files or actual_dirs != expected_dirs:
        raise ValueError("historical input packet population differs")
    custody = json.loads(_real_file(packet / "custody.json", repository).read_bytes())
    if (
        custody.get("schema_version") != "nordic-development-retained-input-custody.v1"
        or custody.get("historical_creation_commit")
        != "27ff47c4a829f59ae37b6a0e85b136b01a36cfa9"
        or custody.get("publication_git_blob")
        != "7c61600e883f2603a75d7287d6071a99485c56da"
        or custody.get("files_sha256") != ORIGINAL_INPUT_HASHES
    ):
        raise ValueError("historical input packet custody differs")
    for relative, digest in ORIGINAL_INPUT_HASHES.items():
        if _sha(_real_file(packet / relative, repository)) != digest:
            raise ValueError(f"historical input byte differs: {relative}")
    publication = json.loads((packet / "publication-manifest.json").read_bytes())
    prepared = json.loads((packet / "prepared/input-manifest.json").read_bytes())
    if (
        publication.get("input_identity") != prepared
        or prepared.get("runner_sha256")
        != "65fd5dd1fd55390360ce118ff137f6fba6e43803074e21d23159fe340292f97b"
    ):
        raise ValueError("historical publication/prepared relation differs")
    return packet


def _source_module(repository: Path) -> str:
    source = _real_file(repository / SOURCE, repository)
    module = ".".join(
        SOURCE.relative_to(Path("packages/bijux-pollenomics-dev/src"))
        .with_suffix("")
        .parts
    )
    spec = importlib.util.find_spec(module)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != source:
        raise ValueError("current development source module origin differs")
    return module


def _invoke(module: str, source: Path, args: list[str]) -> None:
    original = sys.argv
    try:
        sys.argv = [str(source), *args]
        runpy.run_module(module, run_name="__main__")
    finally:
        sys.argv = original


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Keep original historical inputs distinct from the current source stage."""
    artifacts = _destination(repository, output)
    packet = _packet(repository)
    module = _source_module(repository)
    stage_id = hashlib.sha256(
        output.relative_to(artifacts).as_posix().encode()
    ).hexdigest()
    stage_root = (
        artifacts / "jobs/retained-pollen-development/historical-inputs" / stage_id
    )
    if (
        stage_root.exists()
        or stage_root.is_symlink()
        or stage_root.resolve() != stage_root
    ):
        raise ValueError("historical input stage must be absent and real")
    stage_root.mkdir(parents=True, exist_ok=False)
    data_root = stage_root / "data-root"
    publication = data_root / HISTORICAL_PUBLICATION
    publication.parent.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(packet / "publication-manifest.json", publication)
    inputs = stage_root / "prepared"
    shutil.copytree(packet / "prepared", inputs)
    if _sha(publication) != ORIGINAL_INPUT_HASHES["publication-manifest.json"]:
        raise ValueError("staged historical publication differs")
    for relative, digest in ORIGINAL_INPUT_HASHES.items():
        if relative == "publication-manifest.json":
            continue
        if _sha(inputs / relative.removeprefix("prepared/")) != digest:
            raise ValueError("staged historical prepared input differs")
    _invoke(
        module,
        repository / SOURCE,
        [
            "--repository",
            str(data_root),
            "--inputs",
            str(inputs),
            "--output",
            str(output),
        ],
    )
    if {path.name for path in output.iterdir()} != OUTPUT_FILES:
        raise ValueError("development output population differs")
    for name in OUTPUT_FILES:
        _real_file(output / name, repository)
    report = json.loads((output / "report.json").read_bytes())
    if (
        report.get("schema_version") != "nordic-observed-pollen-development.v1"
        or report.get("trial_score_rows") != 40932
        or report.get("outer_target_outcome_files_read") != 0
        or report.get("lra_or_vegetation_validation") is not False
        or report.get("trial_scores_sha256") != _sha(output / "trial-scores.csv.gz")
        or {row["path"]: row["sha256"] for row in report.get("inputs", [])}
        != {
            str(HISTORICAL_PUBLICATION): ORIGINAL_INPUT_HASHES[
                "publication-manifest.json"
            ],
            "input-manifest.json": ORIGINAL_INPUT_HASHES[
                "prepared/input-manifest.json"
            ],
            **{
                f"inputs/training-{country}.json": ORIGINAL_INPUT_HASHES[
                    f"prepared/inputs/training-{country}.json"
                ]
                for country in ("DK", "FI", "NO")
            },
        }
    ):
        raise ValueError("historical development report identity differs")
    receipt: dict[str, Any] = {
        "schema_version": "nordic-development-historical-input-replay.v1",
        "complete_input_stage_path": stage_root.relative_to(repository).as_posix(),
        "current_source_module": module,
        "historical_publication_sha256": ORIGINAL_INPUT_HASHES[
            "publication-manifest.json"
        ],
        "output_sha256": {name: _sha(output / name) for name in sorted(OUTPUT_FILES)},
        "scope": "original development producer on separately retained historical inputs",
    }
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return receipt


def main(argv: list[str] | None = None) -> int:
    """Replay the current original development producer on exact historical inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
