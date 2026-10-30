"""Authenticate the explicit optional Galician literal-context extension."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule

GALICIAN_REVIEW_SOURCE = (
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
    "source_completion/adna/galician_sample_review.py"
)
_CAPTURE_PREFIX = "data/method-certification/author-optimizer-diagnostic-source-capture"
_CAPTURE_SHA256 = "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93"
_OLD_SOURCE_BYTES = 4312
_OLD_SOURCE_SHA256 = "284847d0e77c2bf6b1592ea028f92296f9f6565943c8fe6deb1116f51ac04d07"
_OPTIONAL_CONTEXT_SPANS: tuple[tuple[bytes, bytes], ...] = (
    (
        b'from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity\nfrom bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path\n\nfrom .galician_sample_inputs import REPOSITORY_INPUTS\n\nCORE = "bijux_pollenomics.adna.projects.sample_master.tables.galician_cattle.species"\n',
        b'from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity\nfrom bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path\n\nfrom .galician_literal_context import SCHEMA, TABLE, write_literal_context\nfrom .galician_sample_inputs import REPOSITORY_INPUTS\n\nCORE = "bijux_pollenomics.adna.projects.sample_master.tables.galician_cattle.species"\n',
    ),
    (
        b'    return core\n\n\ndef run(repository: Path, output: Path) -> None:\n    """Preserve original sample taxonomy and publish only a complete immutable account."""\n    repository = _regular_path(repository, directory=True)\n    destination = require_absent_artifact_output(repository, output)\n',
        b'    return core\n\n\ndef run(repository: Path, output: Path, *, literal_context: bool = False) -> None:\n    """Preserve original sample taxonomy and publish only a complete immutable account."""\n    repository = _regular_path(repository, directory=True)\n    destination = require_absent_artifact_output(repository, output)\n',
    ),
    (
        b'    ) as staging:\n        produced = Path(staging) / "products"\n        write_galician_sample_species_review(repository, produced)\n        if {path.name for path in produced.iterdir()} != set(OUTPUTS):\n            raise ValueError("Galician review output population differs")\n        for name in OUTPUTS:\n            _regular_path(produced / name)\n        report = load_json(produced / "report.json", "Galician sample review")\n        if (\n',
        b'    ) as staging:\n        produced = Path(staging) / "products"\n        write_galician_sample_species_review(repository, produced)\n        if literal_context:\n            write_literal_context(repository, produced)\n        expected_outputs = OUTPUTS | {TABLE} if literal_context else OUTPUTS\n        if {path.name for path in produced.iterdir()} != set(expected_outputs):\n            raise ValueError("Galician review output population differs")\n        for name in expected_outputs:\n            _regular_path(produced / name)\n        report = load_json(produced / "report.json", "Galician sample review")\n        if (\n',
    ),
    (
        b'            or report.get("admission_posture") != ADMISSION\n        ):\n            raise ValueError("Galician review sample accounting or admission differs")\n        for path in inputs.values():\n            _regular_path(path)\n        if (\n',
        b'            or report.get("admission_posture") != ADMISSION\n        ):\n            raise ValueError("Galician review sample accounting or admission differs")\n        if literal_context:\n            context = report.get("literal_context", {})\n            if (\n                not isinstance(context, dict)\n                or context.get("schema_version") != SCHEMA\n                or context.get("table") != TABLE\n                or context.get("biosample_count") != 11\n                or context.get("selected_cell_count") != 110\n                or any(\n                    context.get(key) is not False\n                    for key in (\n                        "date_conversion_performed",\n                        "site_assignment_performed",\n                        "scientific_admission",\n                        "atlas_point_admitted",\n                    )\n                )\n            ):\n                raise ValueError(\n                    "Galician literal context accounting or admission differs"\n                )\n        for path in inputs.values():\n            _regular_path(path)\n        if (\n',
    ),
    (
        b'    parser = argparse.ArgumentParser(description=__doc__)\n    parser.add_argument("--repository", type=Path, required=True)\n    parser.add_argument("--output", type=Path, required=True)\n    args = parser.parse_args()\n    run(args.repository, args.output)\n    return 0\n\n\n',
        b'    parser = argparse.ArgumentParser(description=__doc__)\n    parser.add_argument("--repository", type=Path, required=True)\n    parser.add_argument("--output", type=Path, required=True)\n    parser.add_argument("--literal-context", action="store_true")\n    args = parser.parse_args()\n    if args.literal_context:\n        run(args.repository, args.output, literal_context=True)\n    else:\n        run(args.repository, args.output)\n    return 0\n\n\n',
    ),
)


def galician_literal_context_extension_matches(captured: bytes, current: bytes) -> bool:
    """Reverse only the known optional spans to the complete original source bytes."""
    if (
        len(captured) != _OLD_SOURCE_BYTES
        or hashlib.sha256(captured).hexdigest() != _OLD_SOURCE_SHA256
        or not 0 < len(current) <= 32 * 1024
    ):
        return False
    restored = current
    for previous, extended in reversed(_OPTIONAL_CONTEXT_SPANS):
        if captured.count(previous) != 1 or restored.count(extended) != 1:
            return False
        restored = restored.replace(extended, previous, 1)
    return restored == captured


def validated_galician_literal_context_source(
    repository: Path,
    historical: JsonObject,
    logical: str,
    source_buffer: SourceCapsule,
) -> JsonObject:
    """Bind one original optimizer member to the finite optional annotation feature."""
    expected = {"bytes": _OLD_SOURCE_BYTES, "sha256": _OLD_SOURCE_SHA256}
    member = (
        "executions/optimizer-diagnostics/first-party-inputs/" + GALICIAN_REVIEW_SOURCE
    )
    if (
        repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.prefix != _CAPTURE_PREFIX
        or source_buffer.descriptor.capture.get("sha256") != _CAPTURE_SHA256
        or set(historical) != {"path", "bytes", "sha256"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": GALICIAN_REVIEW_SOURCE, **expected}
        or logical != member
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for original, path in group["resolved_paths"]
            if original == logical
        ]
        != [GALICIAN_REVIEW_SOURCE]
    ):
        raise ReportRebuildError("Galician optional-context source binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    path = _regular_confined_file(repository, GALICIAN_REVIEW_SOURCE, "Galician source")
    before = path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 32 * 1024:
        raise ReportRebuildError("Galician source must be bounded and single-link")
    current = path.read_bytes()
    if not galician_literal_context_extension_matches(captured, current):
        raise ReportRebuildError("Galician source differs beyond its optional context")
    source_buffer.fresh()
    again = _regular_confined_file(
        repository, GALICIAN_REVIEW_SOURCE, "Galician source"
    )
    after = again.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if (
        any(getattr(before, field) != getattr(after, field) for field in fields)
        or again.read_bytes() != current
    ):
        raise ReportRebuildError("Galician source changed during correspondence")
    return {
        "path": GALICIAN_REVIEW_SOURCE,
        "classification": "finite_optional_galician_literal_context_extension",
        "original_member": logical,
        "original_sha256": _OLD_SOURCE_SHA256,
        "original_bytes": _OLD_SOURCE_BYTES,
        "whole_old_module_reconstructed": True,
        "old_default_successful_input_path_preserved": True,
        "optional_literal_annotation_feature_added": True,
        "new_date_site_or_point_admission_claimed": False,
        "historical_native_equal_current_claimed": False,
        "new_native_or_model_execution_claimed": False,
    }
