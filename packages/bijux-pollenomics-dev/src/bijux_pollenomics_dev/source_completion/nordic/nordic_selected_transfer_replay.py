"""Run the current selected-pollen producer on exact historical prepared inputs."""

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
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/nordic_pollen_transfer.py"
)
CURRENT_SOURCE_SHA = "3d74eb864b08304a7a5d0cdcb59a2049260e504459b4982d32f8c1e8c89fb166"
HISTORICAL_SOURCE_SHA = (
    "6c39a1e50f385c540e27ba3eebcae064041a01c77d21f3d75faa0c8b02f55cb6"
)
DEVELOPMENT_PACKET = Path("data/neotoma/pollen-development")
TRANSFER_PACKET = Path("data/neotoma/selected-pollen-transfer")
DIRECT = Path("docs/report/regions/nordic/direct-pollen")
DEVELOPMENT = Path("docs/report/regions/nordic/pollen-development/report.json")
RELATIONAL = Path("data/neotoma/relational")
COUNTRIES = ("DK", "FI", "NO")
HISTORICAL_PREPARED = {
    "input-manifest.json": "d1e20733eeabde12ab8ab2ee3ff687cd854c2fee4269fb20fe175365267d99d5",
    "training-DK.json": "def96acd422e9a4975ee8fff3b79a2127c4d1747b3345d2d24296b9670070700",
    "training-FI.json": "908f2868c5b8020878119329cb0de3c941ac680f54fdb4ca073a83776920793f",
    "training-NO.json": "c16fd213650f022076ad157a4b3f09c96c4c9d6bfd889c06180e068dceae305f",
    "metadata-DK.json": "b4a5a7a9b51e9e47f936d4a8acdc0311a3ee377e75217ac22bb427adc14ca6b1",
    "metadata-FI.json": "c6faf842ea9163737e6b10233dd34195187219f7e8931a67f56ddcbe739b000a",
    "metadata-NO.json": "5ec869fc2876b1a05862bdeee911de1457922076e63e1f1b40b1ee7976f6b3a4",
}
HISTORICAL_MANIFEST_SHA = (
    "3e7814bf9697783397cdce11639ebc861620a6a3c9d9295d1357ab69bc7b5edf"
)
HISTORICAL_DEVELOPMENT_SHA = (
    "3189271a721554e9384b70b9ff9ca9f183de4a593e37cb84f2b519cb2a112dde"
)
HISTORICAL_FREEZE_SHA = (
    "785148abb60b1b76a9568f3e723af1c449150534e2352d005dd8fe8864adae72"
)
HISTORICAL_REPORT_SHA = (
    "d1067f6a584de13db619a1e2227c6116015c79deaa0194669a2309242326bef1"
)
DEVELOPMENT_CUSTODY_SHA = (
    "202db4446ecff61c3c70c70b7fdd24419ce1b58ed27da0cdc5c0157144e23263"
)
TRANSFER_CUSTODY_SHA = (
    "49d619c4559587b8bd59c47061a176da43bfaa60b1dd8640528b0de7e474fe90"
)
OUTPUTS = {
    "freeze.json",
    "predictions-DK.json",
    "predictions-FI.json",
    "predictions-NO.json",
    "paired-scores.csv",
    "report.json",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _regular(path: Path, repository: Path) -> Path:
    if not path.is_relative_to(repository):
        raise ValueError("selected-transfer source outside repository")
    for ancestor in (path, *path.parents):
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("selected-transfer source uses symlink")
    if not stat.S_ISREG(path.lstat().st_mode) or path.resolve() != path:
        raise ValueError("selected-transfer source must be a real regular file")
    return path


def _absent_output(repository: Path, output: Path) -> Path:
    if (
        not repository.is_absolute()
        or repository.is_symlink()
        or repository.resolve() != repository
    ):
        raise ValueError("repository must be a real absolute directory")
    artifacts = repository / "artifacts"
    if artifacts.is_symlink() or not stat.S_ISDIR(artifacts.lstat().st_mode):
        raise ValueError("artifact root must be a real directory")
    if not output.is_absolute() or output.exists() or output.is_symlink():
        raise ValueError(
            "selected-transfer output must be an absent absolute directory"
        )
    for ancestor in output.parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("selected-transfer output parent uses symlink")
    else:
        raise ValueError("selected-transfer output outside repository")
    if output.resolve() == artifacts or not output.resolve().is_relative_to(artifacts):
        raise ValueError("selected-transfer output outside artifacts")
    return artifacts


def _packet(repository: Path) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    development = repository / DEVELOPMENT_PACKET
    transfer = repository / TRANSFER_PACKET
    if any(
        root.is_symlink() or root.resolve() != root or not root.is_dir()
        for root in (development, transfer)
    ):
        raise ValueError("historical packet roots must be real directories")
    expected_dev = {
        "custody.json",
        "publication-manifest.json",
        "prepared/input-manifest.json",
        *(f"prepared/inputs/training-{country}.json" for country in COUNTRIES),
    }
    expected_transfer = {
        "custody.json",
        "historical-freeze.json",
        "historical-report.json",
        *(f"metadata-{country}.json" for country in COUNTRIES),
    }
    for root, names, expected_dirs in (
        (development, expected_dev, {"prepared", "prepared/inputs"}),
        (transfer, expected_transfer, set()),
    ):
        files = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() or path.is_symlink()
        }
        directories = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_dir() and not path.is_symlink()
        }
        if (
            files != names
            or directories != expected_dirs
            or any(path.is_symlink() for path in root.rglob("*"))
        ):
            raise ValueError("historical packet population differs")
        for name in names:
            _regular(root / name, repository)
    if (
        _sha(development / "custody.json") != DEVELOPMENT_CUSTODY_SHA
        or _sha(transfer / "custody.json") != TRANSFER_CUSTODY_SHA
    ):
        raise ValueError("historical packet custody byte differs")
    dev_custody = json.loads((development / "custody.json").read_bytes())
    trans_custody = json.loads((transfer / "custody.json").read_bytes())
    if (
        dev_custody.get("schema_version")
        != "nordic-development-retained-input-custody.v1"
        or dev_custody.get("historical_creation_commit")
        != "27ff47c4a829f59ae37b6a0e85b136b01a36cfa9"
        or trans_custody.get("schema_version")
        != "nordic-selected-transfer-retained-input-custody.v1"
        or trans_custody.get("historical_source_commit")
        != "f0c18dff1403d358448f872baa1e76dfd4b8939a"
    ):
        raise ValueError("historical packet custody differs")
    source_files = {
        "input-manifest.json": development / "prepared/input-manifest.json",
        **{
            f"training-{country}.json": development
            / f"prepared/inputs/training-{country}.json"
            for country in COUNTRIES
        },
        **{
            f"metadata-{country}.json": transfer / f"metadata-{country}.json"
            for country in COUNTRIES
        },
    }
    if any(
        _sha(path) != HISTORICAL_PREPARED[name] for name, path in source_files.items()
    ):
        raise ValueError("historical prepared byte differs")
    if (
        _sha(development / "publication-manifest.json") != HISTORICAL_MANIFEST_SHA
        or _sha(transfer / "historical-freeze.json") != HISTORICAL_FREEZE_SHA
        or _sha(transfer / "historical-report.json") != HISTORICAL_REPORT_SHA
    ):
        raise ValueError("historical publication/result receipt differs")
    if dev_custody.get("files_sha256") != {
        "publication-manifest.json": HISTORICAL_MANIFEST_SHA,
        "prepared/input-manifest.json": HISTORICAL_PREPARED["input-manifest.json"],
        **{
            f"prepared/inputs/training-{country}.json": HISTORICAL_PREPARED[
                f"training-{country}.json"
            ]
            for country in COUNTRIES
        },
    } or trans_custody.get("file_sha256") != {
        **{
            f"metadata-{country}.json": HISTORICAL_PREPARED[f"metadata-{country}.json"]
            for country in COUNTRIES
        },
        "historical-freeze.json": HISTORICAL_FREEZE_SHA,
        "historical-report.json": HISTORICAL_REPORT_SHA,
    }:
        raise ValueError("historical custody file map differs")
    published = json.loads((development / "publication-manifest.json").read_bytes())
    prepared = json.loads((development / "prepared/input-manifest.json").read_bytes())
    if (
        published.get("input_identity") != prepared
        or prepared.get("runner_sha256")
        != "65fd5dd1fd55390360ce118ff137f6fba6e43803074e21d23159fe340292f97b"
    ):
        raise ValueError("historical publication and prepared identity differ")
    freeze = json.loads((transfer / "historical-freeze.json").read_bytes())
    report = json.loads((transfer / "historical-report.json").read_bytes())
    if (
        freeze.get("producer_sha256") != HISTORICAL_SOURCE_SHA
        or freeze.get("selection_report_sha256") != HISTORICAL_DEVELOPMENT_SHA
        or freeze.get("published_fixed_manifest_sha256") != HISTORICAL_MANIFEST_SHA
        or freeze.get("prepared_manifest_sha256")
        != HISTORICAL_PREPARED["input-manifest.json"]
        or freeze.get("prepared_file_sha256")
        != {
            country: {
                "training": HISTORICAL_PREPARED[f"training-{country}.json"],
                "metadata": HISTORICAL_PREPARED[f"metadata-{country}.json"],
            }
            for country in COUNTRIES
        }
        or freeze.get("target_outcomes_read") is not False
        or report.get("freeze_sha256") != HISTORICAL_FREEZE_SHA
        or report.get("prediction_sha256") != freeze.get("prediction_sha256")
        or report.get("lra_or_vegetation_validation") is not False
    ):
        raise ValueError("historical freeze/report dependency identity differs")
    return development, transfer, freeze, report


def _source_module(repository: Path) -> str:
    source = _regular(repository / SOURCE, repository)
    if _sha(source) != CURRENT_SOURCE_SHA:
        raise ValueError("current selected-transfer source changed")
    module = ".".join(
        SOURCE.relative_to(Path("packages/bijux-pollenomics-dev/src"))
        .with_suffix("")
        .parts
    )
    spec = importlib.util.find_spec(module)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != source:
        raise ValueError("current selected-transfer module origin differs")
    return module


def _invoke(module: str, source: Path, args: list[str]) -> None:
    original = sys.argv
    try:
        sys.argv = [str(source), *args]
        runpy.run_module(module, run_name="__main__")
    finally:
        sys.argv = original


def _copy_file(
    source: Path, destination: Path, repository: Path, expected: str | None = None
) -> None:
    _regular(source, repository)
    if expected is not None and _sha(source) != expected:
        raise ValueError(
            f"selected-transfer source byte differs: {source.relative_to(repository)}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if _sha(destination) != _sha(source):
        raise ValueError("selected-transfer staged source differs")


def _relational_files(repository: Path) -> list[tuple[Path, str]]:
    root = repository / RELATIONAL
    manifest_path = _regular(root / "manifest.json", repository)
    manifest = json.loads(manifest_path.read_bytes())
    expected_counts = {"samples": 1, "age_claims": 1, "observations": 8}
    result = [(RELATIONAL / "manifest.json", _sha(manifest_path))]
    for surface, count in expected_counts.items():
        parts = manifest["surfaces"][surface]["parts"]
        if len(parts) != count:
            raise ValueError("Neotoma relational selected surface population differs")
        for part in parts:
            relative = Path(part["path"])
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or relative.parts[:1] != ("surfaces",)
            ):
                raise ValueError("Neotoma relational part path differs")
            path = RELATIONAL / relative
            if _sha(_regular(repository / path, repository)) != part["sha256"]:
                raise ValueError("Neotoma relational part digest differs")
            result.append((path, part["sha256"]))
    if len({str(path) for path, _ in result}) != len(result):
        raise ValueError("Neotoma selected relational part duplicate")
    return result


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Keep retained historical receipts separate from current-source products."""
    artifacts = _absent_output(repository, output)
    development, transfer, old_freeze, old_report = _packet(repository)
    module = _source_module(repository)
    published = json.loads((development / "publication-manifest.json").read_bytes())
    if (
        _sha(_regular(repository / DEVELOPMENT, repository))
        != HISTORICAL_DEVELOPMENT_SHA
    ):
        raise ValueError("retained development selection report differs")
    for name, field in (
        ("cohort.csv", "cohort_sha256"),
        ("scores.csv", "scores_sha256"),
    ):
        if _sha(_regular(repository / DIRECT / name, repository)) != published[field]:
            raise ValueError("retained direct-pollen source differs")
    relational = _relational_files(repository)
    stage_id = hashlib.sha256(
        output.relative_to(artifacts).as_posix().encode()
    ).hexdigest()
    stage = artifacts / "jobs/retained-pollen-transfer/historical-inputs" / stage_id
    if stage.exists() or stage.is_symlink() or stage.resolve() != stage:
        raise ValueError("retained transfer stage must be absent")
    stage.mkdir(parents=True, exist_ok=False)
    data_root = stage / "data-root"
    inputs = stage / "inputs"
    _copy_file(
        development / "publication-manifest.json",
        data_root / DIRECT / "manifest.json",
        repository,
        HISTORICAL_MANIFEST_SHA,
    )
    for name in ("cohort.csv", "scores.csv"):
        _copy_file(
            repository / DIRECT / name,
            data_root / DIRECT / name,
            repository,
            published[f"{name.removesuffix('.csv')}_sha256"],
        )
    _copy_file(
        repository / DEVELOPMENT,
        data_root / DEVELOPMENT,
        repository,
        HISTORICAL_DEVELOPMENT_SHA,
    )
    _copy_file(
        development / "prepared/input-manifest.json",
        inputs / "input-manifest.json",
        repository,
        HISTORICAL_PREPARED["input-manifest.json"],
    )
    for country in COUNTRIES:
        for kind in ("training", "metadata"):
            name = f"{kind}-{country}.json"
            source = (
                development / "prepared/inputs" if kind == "training" else transfer
            ) / name
            _copy_file(
                source, inputs / "inputs" / name, repository, HISTORICAL_PREPARED[name]
            )
    for relative, digest in relational:
        _copy_file(repository / relative, data_root / relative, repository, digest)
    frozen = stage / "frozen"
    scored = stage / "scored"
    _invoke(
        module,
        repository / SOURCE,
        [
            "predict",
            "--repository",
            str(data_root),
            "--inputs",
            str(inputs),
            "--output",
            str(frozen),
        ],
    )
    expected_frozen = {
        "freeze.json",
        *(f"predictions-{country}.json" for country in COUNTRIES),
    }
    if {path.name for path in frozen.iterdir()} != expected_frozen:
        raise ValueError("selected-transfer frozen output population differs")
    freeze = json.loads(_regular(frozen / "freeze.json", repository).read_bytes())
    expected_freeze = {**old_freeze, "producer_sha256": CURRENT_SOURCE_SHA}
    if freeze != expected_freeze or freeze["producer_sha256"] == HISTORICAL_SOURCE_SHA:
        raise ValueError("current freeze differs beyond producer identity")
    for country in COUNTRIES:
        if (
            _sha(_regular(frozen / f"predictions-{country}.json", repository))
            != old_freeze["prediction_sha256"][country]
        ):
            raise ValueError(
                "selected-transfer prediction differs from historical receipt"
            )
    freeze_sha = _sha(frozen / "freeze.json")
    _invoke(
        module,
        repository / SOURCE,
        [
            "score",
            "--repository",
            str(data_root),
            "--inputs",
            str(inputs),
            "--frozen",
            str(frozen),
            "--freeze-sha256",
            freeze_sha,
            "--output",
            str(scored),
        ],
    )
    if {path.name for path in scored.iterdir()} != {"paired-scores.csv", "report.json"}:
        raise ValueError("selected-transfer scored output population differs")
    if (
        _sha(_regular(scored / "paired-scores.csv", repository))
        != old_report["paired_scores_sha256"]
    ):
        raise ValueError("selected-transfer paired score bytes differ")
    report = json.loads(_regular(scored / "report.json", repository).read_bytes())
    if report != {**old_report, "freeze_sha256": freeze_sha}:
        raise ValueError(
            "selected-transfer score report differs beyond freeze identity"
        )
    output.mkdir(parents=True, exist_ok=False)
    for name in expected_frozen:
        _copy_file(frozen / name, output / name, repository)
    for name in ("paired-scores.csv", "report.json"):
        _copy_file(scored / name, output / name, repository)
    if {path.name for path in output.iterdir()} != OUTPUTS:
        raise ValueError("selected-transfer final output population differs")
    result: dict[str, Any] = {
        "schema_version": "nordic-selected-transfer-current-source-replay.v1",
        "retained_stage_path": stage.relative_to(repository).as_posix(),
        "current_module": module,
        "historical_freeze_sha256": HISTORICAL_FREEZE_SHA,
        "current_freeze_sha256": freeze_sha,
        "historical_report_sha256": HISTORICAL_REPORT_SHA,
        "current_report_sha256": _sha(output / "report.json"),
        "unchanged_numeric_output_sha256": {
            name: _sha(output / name)
            for name in sorted(OUTPUTS - {"freeze.json", "report.json"})
        },
        "relational_source_files": {str(path): digest for path, digest in relational},
        "metadata_differences": [
            "freeze.json:producer_sha256",
            "report.json:freeze_sha256",
        ],
        "scope": "current original producer on retained historical preparation and publication; development evidence only",
    }
    print(json.dumps(result, sort_keys=True), flush=True)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
