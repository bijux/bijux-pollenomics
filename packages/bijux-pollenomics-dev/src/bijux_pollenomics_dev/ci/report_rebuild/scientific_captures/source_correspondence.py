"""Bind finite source custody roles without relabelling historical numerical execution."""

from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path

from ..contracts import JsonObject, ReportRebuildError
from ..ownership import _regular_confined_file
from ..retained_source import SourceCapsule
from ..retained_source.generated import reconstruct
from .presentation_source_roles import HISTORICAL_RENDERING_SOURCES
from .source_roles.documentation import (
    DOCUMENTED_SOURCE_STRINGS,
    _documented_source_matches,
)
from .source_roles.readers import _historical_custody_source_role, _unique_function
from .spatial_source_exports import spatial_export_extension_matches

HISTORICAL_PRESENTATION_SOURCES = frozenset(
    (
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/markdown.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/narrative_quality.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/publication.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/scientific_accounts.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/scientific_qualifications.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/surfaces.py",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/docs/report_portal_check.py",
    )
)

RETIRED_PRIVATE_CONTROL_SOURCE = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/field_decisions.py"

RETIRED_PRIVATE_CONTROL_IDENTITY = {
    "bytes": 11058,
    "sha256": "7ca655179be6415c740d8e17f4e356ae9ab8786aa0047e9d1c429a79578f03f9",
}


def _historical_metadata_source_role(
    repository: Path,
    historical: JsonObject,
    captured: bytes,
    logical: str,
    detached: frozenset[str],
) -> JsonObject | None:
    """Separate fixed historical presentation or an absent retired private controller."""
    name = historical.get("path")
    if not isinstance(name, str):
        raise ReportRebuildError("Historical metadata source path differs")
    if (
        name not in HISTORICAL_PRESENTATION_SOURCES
        and name not in HISTORICAL_RENDERING_SOURCES
        and name != RETIRED_PRIVATE_CONTROL_SOURCE
    ):
        return None
    if (
        not isinstance(name, str)
        or set(historical) != {"path", "bytes", "sha256"}
        or type(historical.get("bytes")) is not int
        or len(captured) != historical["bytes"]
        or hashlib.sha256(captured).hexdigest() != historical.get("sha256")
        or logical not in detached
        or not logical.endswith("/" + name)
    ):
        raise ReportRebuildError("Historical metadata source binding differs")
    if name == RETIRED_PRIVATE_CONTROL_SOURCE:
        if historical != {"path": name, **RETIRED_PRIVATE_CONTROL_IDENTITY}:
            raise ReportRebuildError("Retired private control identity differs")
        # Absence is a deliberate role, including dangling aliases and special entries.
        current = repository / name
        if (
            repository.resolve() != repository
            or any(
                parent.is_symlink() or not parent.is_dir()
                for parent in (repository, *current.parents)
            )
            or os.path.lexists(current)
        ):
            raise ReportRebuildError("Retired private control must remain absent")
        return {
            "path": name,
            "historical": dict(RETIRED_PRIVATE_CONTROL_IDENTITY),
            "classification": "historical_private_control_current_absence",
            "current_execution_or_authority_claimed": False,
        }
    current = _regular_confined_file(
        repository, name, "current historical-presentation counterpart"
    )
    if current.stat().st_nlink != 1:
        raise ReportRebuildError(
            "Historical presentation counterpart must be single-link"
        )
    return {
        "path": name,
        "historical": {"bytes": historical["bytes"], "sha256": historical["sha256"]},
        "classification": (
            "historical_rendering_source_metadata"
            if name in HISTORICAL_RENDERING_SOURCES
            else "historical_presentation_metadata"
        ),
        "fresh_current_browser_observation_claimed": False,
        "current_semantic_reader_qualification_required_separately": True,
        "old_current_source_equality_claimed": False,
        "native_execution_claimed": False,
    }


VERSION_SOURCE = (
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
)

VERSION_IDENTITY = {
    "bytes": 539,
    "sha256": "84040f998392398c91779befcbac6807d107b3d1c62a57e4b440dbf1fcc680c5",
}

SPATIAL_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra_validation/spatial/__init__.py"


def _historical_version_source_role(
    historical: JsonObject, captured: bytes, logical: str, source_buffer: SourceCapsule
) -> JsonObject:
    """Authenticate only the declared historical version member, never a current file."""
    if (
        historical != {"path": VERSION_SOURCE, **VERSION_IDENTITY}
        or type(historical.get("bytes")) is not int
    ):
        raise ReportRebuildError("Historical version source identity differs")
    aliases = {
        name
        for name in source_buffer.descriptor.members
        if name.endswith("/" + VERSION_SOURCE)
    }
    rows = source_buffer.descriptor.generated
    if not (
        1 <= len(aliases) <= 2
        and logical in aliases
        and len(rows) == len(aliases)
        and {row["member"] for row in rows} == aliases
    ):
        raise ReportRebuildError("Historical version aliases differ")
    expected_generator = {
        "provider": "vcs-versioning.default-python",
        "sha256": "dd7ded849d3bacc8e13b0b675ed991904eb896fc79b4607f4f70ee32e47171d9",
        "bytes": 4479,
    }
    expected_scalars = {
        "version": "0.1.9.dev1462",
        "version_tuple": [0, 1, 9, "dev1462"],
        "short_node": None,
    }
    for row in rows:
        if (
            row.get("generator") != expected_generator
            or row.get("scalars") != expected_scalars
        ):
            raise ReportRebuildError("Historical version generator/scalars differ")
        identity = source_buffer.descriptor.members[row["member"]]
        if (
            identity != VERSION_IDENTITY
            or reconstruct(row, identity) != captured
            or source_buffer.read_source(row["member"]) != captured
        ):
            raise ReportRebuildError("Historical version reconstruction differs")
    return {
        "path": VERSION_SOURCE,
        "classification": "historical_generated_version_metadata",
        "historical": dict(VERSION_IDENTITY),
        "declared_aliases": len(aliases),
        "current_file_equality_claimed": False,
        "original_generation_claimed": False,
    }


def validated_current_scientific_source(
    repository: Path,
    historical: JsonObject,
    logical: str,
    source_buffer: SourceCapsule,
) -> JsonObject | None:
    """Preserve default current bytes, with only the explicitly named custody roles."""
    name = historical.get("path")
    if (
        not isinstance(name, str)
        or set(historical) != {"path", "sha256", "bytes"}
        or type(historical.get("bytes")) is not int
    ):
        raise ReportRebuildError("Scientific source identity schema differs")
    captured = source_buffer.read_source(logical)
    if (
        len(captured) != historical["bytes"]
        or hashlib.sha256(captured).hexdigest() != historical["sha256"]
    ):
        raise ReportRebuildError("Original scientific source member differs")
    if name == VERSION_SOURCE:
        return _historical_version_source_role(
            historical, captured, logical, source_buffer
        )
    role = _historical_metadata_source_role(
        repository, historical, captured, logical, source_buffer.detached
    )
    if role is not None:
        return role
    custody_role = _historical_custody_source_role(
        repository, historical, captured, logical, source_buffer
    )
    if custody_role is not None:
        return custody_role
    current = _regular_confined_file(repository, name, "current scientific source")
    if current.stat().st_nlink != 1:
        raise ReportRebuildError("Current scientific source must be single-link")
    body = current.read_bytes()
    if (
        len(body) == historical["bytes"]
        and hashlib.sha256(body).hexdigest() == historical["sha256"]
    ):
        return None
    if (
        name in DOCUMENTED_SOURCE_STRINGS
        and logical in source_buffer.detached
        and _documented_source_matches(name, captured, body)
    ):
        return {
            "path": name,
            "classification": "exact_named_documentation_only",
            "old_noninserted_bytes_exact": True,
            "native_execution_claimed": False,
        }
    if (
        name == SPATIAL_SOURCE
        and logical in source_buffer.detached
        and 0 < len(body) <= 4096
        and len(captured) == 497
        and hashlib.sha256(captured).hexdigest()
        == "3403cfda5c5791b95312b0293e87d20b8fe3d6f89e9a9814d405d80fb339e6ac"
        and spatial_export_extension_matches(captured, body)
    ):
        return {
            "path": name,
            "classification": "finite_spatial_package_export_extension",
            "historical_noninserted_bytes_exact": True,
            "old_bindings_preserved": True,
            "native_execution_claimed": False,
        }
    if name == INTAKE_SOURCE:
        return _intake_guard_correspondence(historical, captured, body)
    if name == NORDIC_SOURCE:
        return _nordic_owner_correction_correspondence(historical, captured, body)
    raise ReportRebuildError(
        "Scientific source differs without an explicit reviewed role: " + name
    )


INTAKE_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/quarantine/extraction.py"

NORDIC_SOURCE = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/nordic_static_basin.py"


def _intake_guard_correspondence(
    historical: JsonObject, old: bytes, current: bytes
) -> JsonObject:
    """Retain every original intake predicate except the added ancestor refusal."""
    expected = {
        "path": INTAKE_SOURCE,
        "bytes": 4342,
        "sha256": "571cf20de71449b2d0c878418b5d14a99cbcc5ded021b2973a5c859eac71474b",
    }
    if historical != expected or type(historical.get("bytes")) is not int:
        raise ReportRebuildError("Archive intake historical source identity differs")
    try:
        before = ast.parse(old)
        after = ast.parse(current)
        function = _unique_function(after, "extract_zip_members")
        guard = next(node for node in function.body if isinstance(node, ast.If))
        predicate = ast.parse(
            "destination.is_symlink() or not destination.is_dir() or any(parent.is_symlink() for parent in destination.absolute().parents)",
            mode="eval",
        ).body
        if ast.dump(guard.test, include_attributes=False) != ast.dump(
            predicate, include_attributes=False
        ) or not isinstance(guard.test, ast.BoolOp):
            raise ReportRebuildError("Archive intake ancestor predicate differs")
        guard.test.values.pop()
        if ast.dump(before, include_attributes=False) != ast.dump(
            after, include_attributes=False
        ):
            raise ReportRebuildError(
                "Archive intake differs beyond the one ancestor refusal"
            )
    except (SyntaxError, StopIteration, ValueError) as error:
        raise ReportRebuildError(
            "Archive intake guard cannot be authenticated"
        ) from error
    return {
        "path": INTAKE_SOURCE,
        "classification": "finite_extraction_ancestor_refusal",
        "historical": expected,
        "entire_other_module_AST_preserved": True,
        "current_extraction_or_native_execution_claimed": False,
    }


def _nordic_owner_correction_correspondence(
    historical: JsonObject, old: bytes, current: bytes
) -> JsonObject:
    """Recognize only the original sealed22 owner selection correction."""
    expected = {
        "path": NORDIC_SOURCE,
        "bytes": 5593,
        "sha256": "a6e61374431cfb1c8678238b8e6b61b81f7235cd26b472927c8182485706a953",
    }
    if historical != expected or type(historical.get("bytes")) is not int:
        raise ReportRebuildError("Nordic owner historical source identity differs")
    pairs = (
        (
            b"    CAPTURE_PINS,\n    PUBLICATION_AUTHORITY,\n",
            b"    CAPTURE_PINS,\n    FAMILY,\n    PUBLICATION_AUTHORITY,\n",
        ),
        (
            b"    if not rows and not set(CAPTURE_PINS).intersection(tracked_by_path):\n",
            b'    if not rows and not any(name.startswith(FAMILY + "/") for name in tracked_by_path):\n',
        ),
        (
            b'        # This transport owns its sealed capture paths, not every report in the family.\n        if set(CAPTURE_PINS).intersection(paths):\n            if owner.get("role") != "retained_source":\n                raise ReportRebuildError("Nordic static-basin capture owner differs")\n',
            b'        if owner.get("role") == "retained_source" and any(\n            name.startswith(FAMILY + "/") for name in paths\n        ):\n',
        ),
    )
    reduced = current
    for new, previous in pairs:
        if reduced.count(new) != 1:
            raise ReportRebuildError("Nordic owner correction seam differs")
        reduced = reduced.replace(new, previous, 1)
    if reduced != old:
        raise ReportRebuildError(
            "Nordic source differs beyond its original owner correction"
        )
    return {
        "path": NORDIC_SOURCE,
        "classification": "finite_sealed_nordic_capture_owner_selection",
        "all_other_source_bytes_exact": True,
        "numerical_or_source_admission_claimed": False,
    }
