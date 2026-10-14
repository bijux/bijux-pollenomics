"""Authenticate one actual local counting capture without inventing retrieval or rights."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ..contracts import ReportRebuildError, require_relative_path
from ..qualified_sources import (
    QualifiedReportSources,
    _checked_file,
    _object,
    _regular_path,
)

SCHEMA = "qualified-swedish-literal-pair-counting-capture.v1"
SOURCE_ID = "science/swedish-literal-pair-counting"
PLAN_SHA256 = "c0e52eeac4ca792f2d41211d63780d9a67c53e7dee003b1b42d440cae8ef2e4d"
MEMBERS = [
    {
        "path": "independent-verification.json",
        "sha256": "ece762411f867b852ab20b3182ebad2c7521dddd8a1431d0bf9541a50fbd0a84",
        "size": 452,
    },
    {
        "path": "method.md",
        "sha256": "dfbe9950d9ce41f79131354960367d5d3434fbca1261bf17b2279a9c251d4583",
        "size": 3607,
    },
    {
        "path": "protocol.json",
        "sha256": "0a93de9e717f584d143b1d36fa34ab33a8c812fc5337ee37dfd11e019f23fc9f",
        "size": 4539,
    },
    {
        "path": "report.json",
        "sha256": "5d7752d21f0d17b81991f35c0f52095b8f66a3510ec64bb6e7dfb0a6ab077f4b",
        "size": 27703,
    },
    {
        "path": "terminal.json",
        "sha256": "50066bd9c4176e1492c6404a73aaeb48683c66062ca6c57006332017a23e5599",
        "size": 19084,
    },
]


def expected_descriptor() -> dict[str, Any]:
    """Declare only actual local native execution and exact retained byte identities."""
    return {
        "schema_version": SCHEMA,
        "source_id": SOURCE_ID,
        "files": MEMBERS,
        "native_plan_sha256": PLAN_SHA256,
        "custody": "retained-local-native-execution",
        "http_retrieval_claim": False,
        "scientific_admission": False,
        "rights_admission": False,
        "release_admission": False,
    }


def validated_pair_counting_capture(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    """Bind all five private inputs, native success and observer/report correspondence."""
    repository = _regular_path(repository, directory=True)
    relative = require_relative_path(
        descriptor_path.as_posix(), "pair capture descriptor"
    )
    if relative.startswith("external/"):
        raise ReportRebuildError("Pair descriptor overlaps external inputs")
    descriptor_file = _regular_path(repository / relative)
    payload = descriptor_file.read_bytes()
    descriptor = _object(payload)
    if (
        descriptor != expected_descriptor()
        or any(
            descriptor[key] is not False
            for key in (
                "http_retrieval_claim",
                "scientific_admission",
                "rights_admission",
                "release_admission",
            )
        )
        or any(
            type(spec.get("size")) is not int for spec in descriptor.get("files", [])
        )
    ):
        raise ReportRebuildError("Pair capture descriptor identity or limits differ")
    root = _regular_path(source_root, directory=True)
    if repository.is_relative_to(root) or (
        root.is_relative_to(repository)
        and not root.is_relative_to(repository / "artifacts")
    ):
        raise ReportRebuildError(
            "Pair capture store must be an explicit artifact or external source root"
        )
    directory = _regular_path(root / SOURCE_ID, directory=True)
    files = {spec["path"]: _checked_file(directory, spec) for spec in MEMBERS}
    terminal = _object(files["terminal.json"].read_bytes())
    observer = _object(files["independent-verification.json"].read_bytes())
    report = _object(files["report.json"].read_bytes())
    if (
        type(terminal.get("native_exit")) is not int
        or terminal["native_exit"] != 0
        or terminal.get("plan_sha256") != PLAN_SHA256
        or type(observer.get("native_exit")) is not int
        or observer["native_exit"] != 0
        or observer.get("report_sha256")
        != next(spec["sha256"] for spec in MEMBERS if spec["path"] == "report.json")
        or observer.get("all_native_samples")
        != report.get("family_native_sample_population")
    ):
        raise ReportRebuildError(
            "Pair native success or observer/report correspondence differs"
        )
    stages = terminal.get("stages")
    if (
        not isinstance(stages, list)
        or len(stages) != 5
        or any(
            not isinstance(stage, dict)
            or type(stage.get("native_exit")) is not int
            or stage["native_exit"] != 0
            or stage.get("timeout") is not False
            for stage in stages
        )
    ):
        raise ReportRebuildError(
            "Pair capture must retain all five actual native stages"
        )
    for spec in MEMBERS:
        _checked_file(directory, spec)
    if descriptor_file.read_bytes() != payload:
        raise ReportRebuildError("Pair descriptor changed during validation")
    return QualifiedReportSources(
        directory,
        {
            relative: descriptor_file,
            **{f"external/{SOURCE_ID}/{name}": path for name, path in files.items()},
        },
        hashlib.sha256(payload).hexdigest(),
    )
