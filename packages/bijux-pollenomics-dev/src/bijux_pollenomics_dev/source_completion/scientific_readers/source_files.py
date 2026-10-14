"""Export the finite first-party source attachments linked by scientific readers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

MANIFEST = "configs/docs/scientific-source-files.json"
ROUTES: tuple[tuple[str, str], ...] = (
    (
        "data/atlas/source-view-capture/capture.json",
        "docs/report/atlas/source-files/capture.json",
    ),
    (
        "data/synthetic-validation/finite-count-coverage/execution-custody.json",
        "docs/report/synthetic-validation/recovery-evidence/source-files/finite-count-coverage/execution-custody.json",
    ),
    (
        "data/synthetic-validation/finite-count-coverage/independent-review.json",
        "docs/report/synthetic-validation/recovery-evidence/source-files/finite-count-coverage/independent-review.json",
    ),
    (
        "data/synthetic-validation/finite-count-coverage/manifest.json",
        "docs/report/synthetic-validation/recovery-evidence/source-files/finite-count-coverage/manifest.json",
    ),
    (
        "data/synthetic-validation/two-taxon-counting/manifest.json",
        "docs/report/synthetic-validation/recovery-evidence/source-files/two-taxon-counting/manifest.json",
    ),
    (
        "reports/science/krageholm-static-geometry-sensitivity/counting-protocol.json",
        "docs/report/pollen-reconstruction/krageholm-static-geometry-sensitivity/source-files/counting-protocol.json",
    ),
    (
        "reports/science/krageholm-static-geometry-sensitivity/paired-covariance-protocol.json",
        "docs/report/pollen-reconstruction/krageholm-static-geometry-sensitivity/source-files/paired-covariance-protocol.json",
    ),
    (
        "reports/science/krageholm-static-geometry-sensitivity/source-custody.json",
        "docs/report/pollen-reconstruction/krageholm-static-geometry-sensitivity/source-files/source-custody.json",
    ),
    (
        "reports/science/krageholm-static-geometry-sensitivity/wind-protocol.json",
        "docs/report/pollen-reconstruction/krageholm-static-geometry-sensitivity/source-files/wind-protocol.json",
    ),
    (
        "reports/science/swedish-native-chronology-contrast/aliquot-protocol.json",
        "docs/report/pollen-reconstruction/swedish-native-chronology-contrast/source-files/aliquot-protocol.json",
    ),
    (
        "reports/science/swedish-native-chronology-contrast/paired_uncertainty.py",
        "docs/report/pollen-reconstruction/swedish-native-chronology-contrast/source-files/paired_uncertainty.py.txt",
    ),
    (
        "reports/science/swedish-native-chronology-contrast/protocol.json",
        "docs/report/pollen-reconstruction/swedish-native-chronology-contrast/source-files/protocol.json",
    ),
    (
        "reports/science/swedish-native-chronology-contrast/qualify.py",
        "docs/report/pollen-reconstruction/swedish-native-chronology-contrast/source-files/qualify.py.txt",
    ),
    (
        "reports/science/vegetation-reference/pyrenees-botanical-projection/input-custody.json",
        "docs/report/vegetation-reference/pyrenees-botanical-projection/source-files/input-custody.json",
    ),
    (
        "reports/science/vegetation-reference/pyrenees-botanical-projection/replay.py",
        "docs/report/vegetation-reference/pyrenees-botanical-projection/source-files/replay.py.txt",
    ),
)


class ScientificSourceFileError(ValueError):
    """A finite public attachment differs from its maintained source contract."""


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ScientificSourceFileError("Duplicate source attachment JSON key")
        result[key] = value
    return result


def _read(repository: Path, relative: str) -> bytes:
    parts = relative.split("/")
    if relative.startswith("/") or any(p in {"", ".", ".."} for p in parts):
        raise ScientificSourceFileError("Canonical source attachment path required")
    path = repository
    try:
        for index, part in enumerate(parts):
            path /= part
            mode = path.lstat().st_mode
            if not (
                stat.S_ISREG(mode) if index == len(parts) - 1 else stat.S_ISDIR(mode)
            ):
                raise ScientificSourceFileError("Regular source attachment required")
        if path.stat().st_nlink != 1:
            raise ScientificSourceFileError("Hardlinked source attachment forbidden")
        return path.read_bytes()
    except OSError as error:
        raise ScientificSourceFileError("Source attachment unavailable") from error


def source_files(repository: Path) -> dict[str, bytes]:
    """Validate all sources before exposing any of the fifteen fixed attachments."""
    payload = json.loads(_read(repository, MANIFEST), object_pairs_hook=_object)
    if (
        not isinstance(payload, dict)
        or set(payload) != {"schema_version", "scope", "files"}
        or payload["schema_version"] != "scientific-source-files.v1"
        or not isinstance(payload["scope"], str)
        or not isinstance(payload["files"], list)
        or len(payload["files"]) != len(ROUTES)
    ):
        raise ScientificSourceFileError("Finite source attachment manifest required")
    result: dict[str, bytes] = {}
    for row, (source, destination) in zip(payload["files"], ROUTES, strict=True):
        if (
            not isinstance(row, dict)
            or set(row)
            != {
                "source",
                "destination",
                "sha256",
                "bytes",
                "git_blob",
            }
            or row["source"] != source
            or row["destination"] != destination
            or type(row["bytes"]) is not int
            or not 0 < row["bytes"] <= 524288
            or any(
                not isinstance(row[key], str)
                or len(row[key]) != size
                or any(c not in "0123456789abcdef" for c in row[key])
                for key, size in (
                    ("sha256", 64),
                    ("git_blob", 40),
                )
            )
        ):
            raise ScientificSourceFileError(
                "Exact maintained source attachment route required"
            )
        data = _read(repository, source)
        blob = hashlib.sha1(
            b"blob " + str(len(data)).encode() + b"\0" + data, usedforsecurity=False
        ).hexdigest()
        if (
            len(data) != row["bytes"]
            or hashlib.sha256(data).hexdigest() != row["sha256"]
            or blob != row["git_blob"]
        ):
            raise ScientificSourceFileError("Source attachment byte identity differs")
        result[destination.removeprefix("docs/report/")] = data
    return result


def export_source_files(repository: Path, output: Path) -> tuple[str, ...]:
    """Use the configured-owner artifact boundary; copy metadata/code without execution."""
    if ".." in repository.parts or any(
        p.is_symlink() for p in (repository, *repository.parents)
    ):
        raise ScientificSourceFileError("Regular canonical repository required")
    repository = repository.absolute()
    output = require_absent_artifact_output(repository, output)
    files = source_files(repository)
    output.mkdir()
    for relative, data in files.items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    return tuple(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    paths = export_source_files(args.repository, args.output)
    print(
        json.dumps({"exported_source_files": len(paths), "scientific_admission": False})
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
