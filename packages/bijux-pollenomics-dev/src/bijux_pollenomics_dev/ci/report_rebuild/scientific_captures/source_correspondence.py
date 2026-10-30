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
from .presentation_source_roles import (
    HISTORICAL_RENDERING_SOURCES,
    atlas_extension_matches,
)
from .source_roles.documentation import (
    DOCUMENTED_SOURCE_STRINGS,
    _documented_source_matches,
)
from .source_roles.native_reference_transport import (
    NATIVE_REFERENCE_TRANSPORT_SOURCES,
    validated_native_reference_transport_source,
)
from .source_roles.numerical_precision import (
    METRICS_SOURCE,
    validated_hellinger_precision_source,
)
from .source_roles.readers import (
    SWEDISH_REFERENCE_READER_SOURCE,
    _historical_custody_source_role,
    _unique_function,
    validated_swedish_reference_reader_source,
)
from .source_roles.scoring_protocols import (
    SCORING_PROTOCOL_SOURCES,
    validated_scoring_protocol_source,
)
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


_COLLECTOR_SOURCE_IDENTITIES: dict[str, tuple[str, int]] = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/rootsi_input_closure.py": (
        "68de0c8e7da6f5e265ba27e30ae99c92378b8529ef538ce1242b9540ffb4816e",
        37541,
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/classification/neotoma/__init__.py": (
        "cdf755312d22f0b6e1a3edc8f7bd7fac0a8c9bd41b180273d6b22f16c7e47974",
        3711,
    ),
}
_ROOTSI_INDEX_INITIALIZATION = b"    if not inputs.rootsi:\n        return {row.worksheet_row: ((), ()) for row in inputs.publication.records}\n    sequences: dict[str, set[int]] = {}\n    sites: dict[tuple[str, str], set[int]] = {}\n    for index, rootsi in enumerate(inputs.rootsi):\n        sequences.setdefault(_normalized(rootsi.site_label), set()).add(index)\n        if rootsi.sample_count_claim is not None:\n            key = (_normalized(rootsi.site_name), str(rootsi.sample_count_claim))\n            sites.setdefault(key, set()).add(index)\n"
_ROOTSI_INDEX_LOOKUP = b'        # Validate the same three columns even when no indexed candidate matches.\n        sequence = _raw(publication, "csvfilename")\n        site = _raw(publication, "SiteName")\n        samples = _raw(publication, "nPollenSamples")\n        indexes = set(sequences.get(_normalized(_sequence_stem(sequence)), ()))\n        if samples is not None:\n            indexes.update(sites.get((_normalized(site), samples), ()))\n        # Original indices preserve duplicates and source order; the original\n        # predicate owns reasons, exact sample text, and lazy country validation.\n'


def collector_source_extension_matches(
    name: str, captured: bytes, current: bytes
) -> bool:
    """Invert only the declared index or qualifier spans to every original byte."""
    if (
        name
        == "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/classification/neotoma/__init__.py"
    ):
        added = b're.compile(r"(?:^|\\s)cf\\.?\\s", re.IGNORECASE)'
        original = b're.compile(r"(?:^|\\s)cf\\.\\s", re.IGNORECASE)'
        return (
            current.count(added) == 1
            and current.replace(added, original, 1) == captured
        )
    if (
        name
        != "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/rootsi_input_closure.py"
    ):
        return False
    body = current
    spans = (
        (_ROOTSI_INDEX_INITIALIZATION, b""),
        (_ROOTSI_INDEX_LOOKUP, b""),
        (
            b"            for index in sorted(indexes)\n",
            b"            for rootsi in inputs.rootsi\n",
        ),
        (b"_match(inputs.rootsi[index], publication)", b"_match(rootsi, publication)"),
    )
    for inserted, original in spans:
        if body.count(inserted) != 1:
            return False
        body = body.replace(inserted, original, 1)
    return body == captured


def _collector_source_extension_correspondence(
    repository: Path,
    historical: JsonObject,
    logical: str,
    source_buffer: SourceCapsule,
) -> JsonObject:
    """Bind two finite collector extensions to the original optimizer source only."""
    name = historical.get("path")
    if not isinstance(name, str) or name not in _COLLECTOR_SOURCE_IDENTITIES:
        raise ReportRebuildError("Unknown collector source extension")
    checksum, size = _COLLECTOR_SOURCE_IDENTITIES[name]
    expected = {"sha256": checksum, "bytes": size}
    if (
        repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.prefix
        != "data/method-certification/author-optimizer-diagnostic-source-capture"
        or source_buffer.descriptor.capture.get("sha256")
        != "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93"
        or set(historical) != {"path", "sha256", "bytes"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": name, **expected}
        or logical != "executions/optimizer-diagnostics/first-party-inputs/" + name
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for member, path in group["resolved_paths"]
            if member == logical
        ]
        != [name]
    ):
        raise ReportRebuildError("Original collector source extension binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    if len(captured) != size or hashlib.sha256(captured).hexdigest() != checksum:
        raise ReportRebuildError("Original collector source extension bytes differ")
    source = _regular_confined_file(repository, name, "current collector source")
    before = source.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 128 * 1024**2:
        raise ReportRebuildError("Current collector source must be bounded single-link")
    current = source.read_bytes()
    if not collector_source_extension_matches(name, captured, current):
        raise ReportRebuildError(
            "Collector source differs beyond its finite original-byte law"
        )
    source_buffer.fresh()
    again = _regular_confined_file(repository, name, "current collector source")
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
        raise ReportRebuildError(
            "Current collector source changed during correspondence"
        )
    return {
        "path": name,
        "classification": "finite_collector_source_extension",
        "extension": "source_qualifier_annotation"
        if name.endswith("/neotoma/__init__.py")
        else "typed_rootsi_indexed_join",
        "original_member": logical,
        "original_sha256": checksum,
        "original_bytes": size,
        "old_noninserted_bytes_exact": True,
        "current_regular_single_link_and_stable": True,
        "current_classifier_native_or_browser_equivalence_claimed": False,
        "scope": "Exact source-span correspondence only; the qualifier annotation extension and indexed typed-record software have separate constructed controls. Original optimizer observations and all other source predicates remain unchanged.",
    }


_COUNTING_API_IDENTITIES: dict[str, tuple[str, int]] = {
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py": (
        "223555bc7b778fbe4fa79a8bcdf4c2d5324aa9635cdf07c4d6450e0359b49692",
        6085,
    ),
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/__init__.py": (
        "4b8438dee8e9bed9a8ddbd5b875cb115eb5a91b5085dcc305323d6dfbe6acea1",
        1979,
    ),
}
_COUNTING_API_CAPTURE_BINDINGS: dict[str, tuple[str, str]] = {
    "data/publication-replay/landclim-author-example-capture": (
        "9d6c4821ea1ba2a1216272d9691017e88ad96a66cf5820271b76442e617e3eec",
        "numerical-source/",
    ),
    "data/method-certification/author-optimizer-diagnostic-source-capture": (
        "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
        "executions/optimizer-diagnostics/first-party-inputs/",
    ),
    "data/method-certification/linux-r-source-capture": (
        "fa6e9a4fa9c12013a04cc461fef52d0fd54044d517e132e802a9c176def2a913",
        "source/",
    ),
    "data/surface-reference/swedish-direct-pollen-source-capture": (
        "fed646a3620b7266f8ab87dd44cdbfac72461179d74df29410460deb81672449",
        "original-source/source/",
    ),
    "data/atlas/sample-chronology-source-view-capture": (
        "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62",
        "source/",
    ),
}


_COUNTING_API_AUTHOR_BINDINGS: dict[str, tuple[str, tuple[str, ...]]] = {
    "data/method-certification/author-native-comparison-source-capture": (
        "b5c8e7cb4a1f7a12b99b8d79c9230d0d2b1ba1f7e52cda6ab2afe31622cb95d0",
        ("native-comparison",),
    ),
    "data/method-certification/author-site-evaluation-source-capture": (
        "76617093d6c0802273453bd9c4cdc68d2486e04baa146c4893ae7e441a090f7b",
        ("uncertainty", "profile", "holdout"),
    ),
}


def _counting_api_source_correspondence(
    repository: Path,
    historical: JsonObject,
    logical: str,
    source_buffer: SourceCapsule,
) -> JsonObject:
    """Bind the four counting exports to exact historical API and capture bytes."""
    from bijux_pollenomics_dev.lra_validation.native_reference.source_layout_adoption import (
        counting_api_extension_matches,
    )

    name = historical.get("path")
    if not isinstance(name, str) or name not in _COUNTING_API_IDENTITIES:
        raise ReportRebuildError("Unknown counting API source")
    checksum, size = _COUNTING_API_IDENTITIES[name]
    identity = {"sha256": checksum, "bytes": size}
    binding = _COUNTING_API_CAPTURE_BINDINGS.get(source_buffer.prefix)
    author_binding = _COUNTING_API_AUTHOR_BINDINGS.get(source_buffer.prefix)
    aliases = {logical}
    if author_binding is not None:
        aliases = {
            "executions/" + lane + "/first-party-inputs/" + name
            for lane in author_binding[1]
        }
        if logical not in aliases:
            raise ReportRebuildError("Original author counting API lane differs")
        binding = (author_binding[0], logical.removesuffix(name))
    if (
        repository != repository.resolve()
        or source_buffer.repository != repository
        or binding is None
        or source_buffer.descriptor.capture.get("sha256") != binding[0]
        or set(historical) != {"path", "bytes", "sha256"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": name, **identity}
        or logical != binding[1] + name
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != identity
        or [
            path
            for group in source_buffer.descriptor.groups
            for member, path in group["resolved_paths"]
            if member == logical
        ]
        != [name]
    ):
        raise ReportRebuildError("Original counting API capture binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    if len(captured) != size or hashlib.sha256(captured).hexdigest() != checksum:
        raise ReportRebuildError("Original counting API bytes differ")
    for alias in aliases:
        if (
            alias not in source_buffer.detached
            or source_buffer.descriptor.members.get(alias) != identity
            or [
                path
                for group in source_buffer.descriptor.groups
                for member, path in group["resolved_paths"]
                if member == alias
            ]
            != [name]
            or source_buffer.read_source(alias) != captured
        ):
            raise ReportRebuildError("Original author counting API aliases differ")
    source = _regular_confined_file(repository, name, "current counting API")
    before = source.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 32768:
        raise ReportRebuildError("Current counting API must be bounded single-link")
    current = source.read_bytes()
    if not counting_api_extension_matches(name, captured, current):
        raise ReportRebuildError(
            "Counting API differs beyond its exact named additions"
        )
    source_buffer.fresh()
    again = _regular_confined_file(repository, name, "current counting API")
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
        raise ReportRebuildError("Current counting API changed during correspondence")
    return {
        "path": name,
        "classification": "finite_counting_api_addition",
        "historical": identity,
        "original_member": logical,
        "original_aliases": sorted(aliases),
        "old_noninserted_bytes_and_bindings_exact": True,
        "added_capability": "lra.love.two-taxon.fixed-background-binomial-set",
        "new_counting_api_requires_separate_current_qualification": True,
        "whole_current_descriptor_equal_old_claimed": False,
        "native_execution_or_browser_equivalence_claimed": False,
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
    if name in SCORING_PROTOCOL_SOURCES:
        return validated_scoring_protocol_source(
            repository, historical, logical, source_buffer
        )
    if name in NATIVE_REFERENCE_TRANSPORT_SOURCES:
        return validated_native_reference_transport_source(
            repository, historical, logical, source_buffer
        )
    if name in _COUNTING_API_IDENTITIES:
        return _counting_api_source_correspondence(
            repository, historical, logical, source_buffer
        )
    if name == METRICS_SOURCE:
        return validated_hellinger_precision_source(
            repository, historical, logical, source_buffer
        )
    if name == SWEDISH_REFERENCE_READER_SOURCE:
        return validated_swedish_reference_reader_source(
            repository, historical, logical, source_buffer
        )
    if (
        logical == "source/" + name
        and logical in source_buffer.detached
        and atlas_extension_matches(name, captured, body)
    ):
        return {
            "path": name,
            "classification": "finite_atlas_asset_or_provider_extension",
            "old_noninserted_bytes_exact": True,
            "current_browser_or_native_equivalence_claimed": False,
            "new_provider_api_qualified_by_historical_source": False,
        }
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
    if name in _COLLECTOR_SOURCE_IDENTITIES:
        return _collector_source_extension_correspondence(
            repository, historical, logical, source_buffer
        )
    if name == AUTHOR_DEFAULT_SOURCE:
        return _author_default_source_correspondence(
            repository, historical, captured, body, logical, source_buffer
        )
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


AUTHOR_DEFAULT_SOURCE = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/author_lra_development.py"
AUTHOR_WINDOW_SOURCE = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/author_lra_windows.py"
AUTHOR_DEFAULT_IDENTITY = {
    "bytes": 12752,
    "sha256": "347031982e8ced89fd886c44005cd000537b080d6e4d9c28ab05112a0e0c9353",
}

# Only these complete source spans may specialize the authenticated default.
_AUTHOR_DEFAULT_SOURCE_REPLACEMENTS = (
    (
        b"from typing import Any\n\nfrom .author_lra_windows import selected_counts, source_window\nfrom .author_pollen_spatial.source import _study\n\n",
        b"from typing import Any\n\nfrom .author_pollen_spatial.source import _study\n\n",
    ),
    (
        b'\n\ndef materialize_author_lra_development(\n    source_root: Path, output: Path, *, window: int = WINDOW\n) -> Path:\n    """Keep author counts private and expose source-bound local experiment inputs."""\n    selection = source_window(window)\n    source_root, output = source_root.resolve(), output.resolve()\n    if output.exists() or output.is_symlink():\n',
        b'\n\ndef materialize_author_lra_development(source_root: Path, output: Path) -> Path:\n    """Keep author counts private and expose source-bound local experiment inputs."""\n    source_root, output = source_root.resolve(), output.resolve()\n    if output.exists() or output.is_symlink():\n',
    ),
    (
        b'    if (\n        len(boundaries) != 26\n        or (boundaries[window - 1], boundaries[window])\n        != (selection.younger_bp, selection.older_bp)\n        or lookup[window] != [str(window), selection.label_bp]\n    ):\n        raise ValueError("Author time-window support changed")\n',
        b'    if (\n        len(boundaries) != 26\n        or (boundaries[WINDOW - 1], boundaries[WINDOW]) != (YOUNGER_BP, OLDER_BP)\n        or lookup[WINDOW] != [str(WINDOW), LABEL_BP]\n    ):\n        raise ValueError("Author time-window support changed")\n',
    ),
    (
        b'        relative = "run.REVEALS.files/" + site.count_filename\n        rows = checked(relative)\n        selected = selected_counts(\n            rows, study.prepared_taxa, site.site_id, site.radius_m, selection\n        )\n        if selected is None:\n            unavailable.append(site.site_id)\n            continue\n        radius, counts = selected\n        observations.append((site, radius, counts))\n    if (\n        len(observations) != selection.eligible_count\n        or set(unavailable) != set(selection.unavailable_sites)\n        or sum(sum(counts) for _, _, counts in observations)\n        != selection.source_count_total\n    ):\n        raise ValueError("Author source window eligible denominator changed")\n\n    output.parent.mkdir(parents=True, exist_ok=True)\n',
        b'        relative = "run.REVEALS.files/" + site.count_filename\n        rows = checked(relative)\n        if (\n            len(rows) != 34\n            or rows[1][0] != "radius"\n            or rows[2][0] != "model"\n            or [row[0] for row in rows[3:]] != study.prepared_taxa\n        ):\n            raise ValueError(f"Author prepared taxon axis changed: {site.site_id}")\n        column = rows[0].index(LABEL_BP)\n        radius = float(rows[1][column])\n        model = int(rows[2][column])\n        counts = [int(row[column]) for row in rows[3:]]\n        if any(count < 0 for count in counts):\n            raise ValueError("Author prepared pollen count changed")\n        if sum(counts) == 0:\n            if radius != 0 or model != 0:\n                raise ValueError("Empty author window has positive basin metadata")\n            unavailable.append(site.site_id)\n            continue\n        if radius != site.radius_m or model != 2:\n            raise ValueError("Author lake radius or model disagrees with site metadata")\n        observations.append((site, radius, counts))\n    if len(observations) != 15 or len(unavailable) != 2:\n        raise ValueError("Author TW5 eligible denominator changed")\n\n    output.parent.mkdir(parents=True, exist_ok=True)\n',
    ),
    (
        b'            {\n                "source": "author bins.csv/TWlookup.csv",\n                "window": window,\n                "bounds_cal_bp": [selection.younger_bp, selection.older_bp],\n                "label_bp": selection.label_bp,\n            },\n        )\n',
        b'            {\n                "source": "author bins.csv/TWlookup.csv",\n                "window": WINDOW,\n                "bounds_cal_bp": [YOUNGER_BP, OLDER_BP],\n                "label_bp": LABEL_BP,\n            },\n        )\n',
    ),
    (
        b'            metadata = {\n                "site_id": site.site_id,\n                "sample_id": site.site_id + ":TW" + str(window),\n                "coordinate": int(selection.label_bp),\n                "bin_id": "author-TW" + str(window),\n                "age_type": "calendar_bp",\n                "age_support_bp": [[selection.younger_bp, selection.older_bp]],\n                "chronology_evidence_id": "chronology",\n            }\n',
        b'            metadata = {\n                "site_id": site.site_id,\n                "sample_id": site.site_id + ":TW5",\n                "coordinate": 1500,\n                "bin_id": "author-TW5",\n                "age_type": "calendar_bp",\n                "age_support_bp": [[YOUNGER_BP, OLDER_BP]],\n                "chronology_evidence_id": "chronology",\n            }\n',
    ),
    (
        b'                    "rule": "declared_bin_stationarity",\n                    "decision_evidence_id": "decision",\n                    "bins": [selection.temporal_bin],\n                },\n                "versions": dict.fromkeys(\n',
        b'                    "rule": "declared_bin_stationarity",\n                    "decision_evidence_id": "decision",\n                    "bins": [\n                        {\n                            "bin_id": "author-TW5",\n                            "younger_bp": YOUNGER_BP,\n                            "older_bp": OLDER_BP,\n                        }\n                    ],\n                },\n                "versions": dict.fromkeys(\n',
    ),
    (
        b'                "eligible_sites": [site["site_id"] for site in sites],\n                "zero_count_sites": sorted(unavailable),\n                **(\n                    {\n                        "source_window_availability": {\n                            "unavailable_sites": sorted(unavailable),\n                            "meaning": "Source formatter merges absent windows and fills NA with zero, including radius/model; no observed ecological-zero claim.",\n                            "age_scale": "Source-declared age.cal.BP; epoch/calibration/uncertainty not requalified.",\n                            "interval": "left-closed/right-open from source findInterval defaults",\n                            "source_taxa": 31,\n                            "input_scope": "Native author-prepared31taxon inputs. Any30taxon constrained projection requires its own declared identity and window-specific excluded-count denominator.",\n                        }\n                    }\n                    if window != WINDOW\n                    else {}\n                ),\n                "total_count": sum(sum(counts) for _, _, counts in observations),\n                "selected_window": window,\n                "age_support_bp": [selection.younger_bp, selection.older_bp],\n                "ring_geometry": "declared circular/homogeneous modeling assumption",\n                "scientific_posture": "prior-exposed exploratory development; no vegetation truth",\n',
        b'                "eligible_sites": [site["site_id"] for site in sites],\n                "zero_count_sites": sorted(unavailable),\n                "total_count": sum(sum(counts) for _, _, counts in observations),\n                "selected_window": WINDOW,\n                "age_support_bp": [YOUNGER_BP, OLDER_BP],\n                "ring_geometry": "declared circular/homogeneous modeling assumption",\n                "scientific_posture": "prior-exposed exploratory development; no vegetation truth",\n',
    ),
    (
        b'    parser.add_argument("--author-source-root", type=Path, required=True)\n    parser.add_argument("--output", type=Path, required=True)\n    parser.add_argument("--window", type=int, choices=(4, 5, 6), default=WINDOW)\n    args = parser.parse_args()\n    output = materialize_author_lra_development(\n        args.author_source_root, args.output, window=args.window\n    )\n    print(output / "source-report.json")\n\n',
        b'    parser.add_argument("--author-source-root", type=Path, required=True)\n    parser.add_argument("--output", type=Path, required=True)\n    args = parser.parse_args()\n    output = materialize_author_lra_development(args.author_source_root, args.output)\n    print(output / "source-report.json")\n\n',
    ),
)

# The complete selector contract constrains declarations, imports and refusal paths.


_AUTHOR_SELECTOR_IMPORTS = (
    "from __future__ import annotations",
    "from dataclasses import dataclass",
    "import math",
    "import re",
)
_AUTHOR_WINDOW_FIELDS = (
    "index: int",
    "label_bp: str",
    "younger_bp: int",
    "older_bp: int",
    "source_count_total: int",
    "unavailable_sites: tuple[str, ...]",
)
_AUTHOR_WINDOW_ROWS = (
    (4, "1000", 750, 1250, 22582, ("COMERSLA", "EXEBRID", "WHH05", "WHH11")),
    (5, "1500", 1250, 1750, 20732, ("EXEBRID", "WHH11")),
    (6, "2000", 1750, 2250, 23009, ("EXEBRID", "WHH05", "WHH11")),
)
_AUTHOR_WINDOW_PROPERTIES = (
    (
        "@property\ndef temporal_bin(self) -> dict[str, str | int]:\n    pass",
        "Use the same bounds for the request template and source chronology.",
        "return {'bin_id': 'author-TW' + str(self.index), 'younger_bp': self.younger_bp, 'older_bp': self.older_bp}",
    ),
    (
        "@property\ndef eligible_count(self) -> int:\n    pass",
        "Count records eligible under the declared author-window membership rules.",
        "return 17 - len(self.unavailable_sites)",
    ),
)
_AUTHOR_LOOKUP_STATEMENTS = (
    "if type(index) is not int:\n    raise ValueError('Integer author window identity required')",
    "for window in WINDOWS:\n    if window.index == index:\n        return window",
    "raise ValueError('Only source windows 4, 5 and 6 are admitted')",
)
_AUTHOR_COUNT_STATEMENTS = (
    "if window not in WINDOWS or len(rows) != 34 or any(len(row) != 26 for row in rows) or len(taxa) != 31 or len(set(taxa)) != 31 or rows[1][0] != 'radius' or rows[2][0] != 'model' or [row[0] for row in rows[3:]] != taxa or rows[0][0] != 'TW' or len(set(rows[0])) != 26 or rows[0].count(window.label_bp) != 1:\n    raise ValueError('Author prepared time/taxon axis changed: ' + site_id)",
    "column = rows[0].index(window.label_bp)",
    "if column != window.index:\n    raise ValueError('Author source window index/label differs')",
    "cells = [row[column] for row in rows[3:]]",
    "if any(re.fullmatch('[0-9]+', value) is None for value in cells):\n    raise ValueError('Explicit nonnegative integer source counts required')",
    "radius = float(rows[1][column])",
    "model = rows[2][column]",
    "counts = [int(value) for value in cells]",
    "if not math.isfinite(radius) or not math.isfinite(expected_radius_m) or expected_radius_m <= 0:\n    raise ValueError('Finite positive source site geometry required')",
    "if not any(counts):\n    if radius != 0 or model != '0' or site_id not in window.unavailable_sites:\n        raise ValueError('Source-filled unavailable window disagrees with its native mask')\n    return None",
    "if radius != expected_radius_m or model != '2' or site_id in window.unavailable_sites:\n    raise ValueError('Author positive lake window disagrees with source site metadata')",
    "return radius, counts",
)


def _author_window_selector_contract() -> ast.Module:
    """Describe each permitted declaration and ordered dataflow or refusal statement."""
    nodes: list[ast.stmt] = [
        ast.Expr(
            value=ast.Constant(
                value="Select authenticated author time columns without treating missing windows as ecology."
            )
        )
    ]
    nodes.extend(ast.parse(statement).body[0] for statement in _AUTHOR_SELECTOR_IMPORTS)
    window_class = ast.parse(
        "@dataclass(frozen=True)\nclass AuthorWindow:\n    pass"
    ).body[0]
    if not isinstance(window_class, ast.ClassDef):
        raise ReportRebuildError("Author window class contract differs")
    window_class.body = [
        ast.Expr(
            value=ast.Constant(
                value="One finite source-declared calibrated-BP interval and its availability mask."
            )
        )
    ]
    window_class.body.extend(
        ast.parse(statement).body[0] for statement in _AUTHOR_WINDOW_FIELDS
    )
    for signature, documentation, expression in _AUTHOR_WINDOW_PROPERTIES:
        function = ast.parse(signature).body[0]
        if not isinstance(function, ast.FunctionDef):
            raise ReportRebuildError("Author window property contract differs")
        function.body = [
            ast.Expr(value=ast.Constant(value=documentation)),
            ast.parse(expression).body[0],
        ]
        window_class.body.append(function)
    nodes.append(window_class)
    nodes.append(
        ast.Assign(
            targets=[ast.Name(id="WINDOWS", ctx=ast.Store())],
            value=ast.Tuple(
                elts=[
                    ast.Call(
                        func=ast.Name(id="AuthorWindow", ctx=ast.Load()),
                        args=[
                            ast.parse(repr(value), mode="eval").body for value in row
                        ],
                        keywords=[],
                    )
                    for row in _AUTHOR_WINDOW_ROWS
                ],
                ctx=ast.Load(),
            ),
        )
    )
    functions = (
        (
            "def source_window(index: int) -> AuthorWindow:\n    pass",
            "Refuse undeclared windows rather than reinterpret an existing input set.",
            _AUTHOR_LOOKUP_STATEMENTS,
        ),
        (
            "def selected_counts(rows: list[list[str]], taxa: list[str], site_id: str, expected_radius_m: float, window: AuthorWindow) -> tuple[float, list[int]] | None:\n    pass",
            "Read one source column; unavailable source-filled zero is not an observation.",
            _AUTHOR_COUNT_STATEMENTS,
        ),
    )
    for signature, documentation, statements in functions:
        function = ast.parse(signature).body[0]
        if not isinstance(function, ast.FunctionDef):
            raise ReportRebuildError("Author selector function contract differs")
        function.body = [ast.Expr(value=ast.Constant(value=documentation))]
        function.body.extend(ast.parse(statement).body[0] for statement in statements)
        nodes.append(function)
    return ast.Module(body=nodes, type_ignores=[])


def _author_window_selector_matches(selector: bytes) -> bool:
    """Close imports, headers and every ordered selector statement without execution."""
    if not selector or len(selector) > 16384:
        return False
    try:
        return ast.dump(ast.parse(selector), include_attributes=False) == ast.dump(
            _author_window_selector_contract(), include_attributes=False
        )
    except (SyntaxError, UnicodeError, ValueError, RecursionError):
        return False


def _restore_author_default_source(old: bytes, current: bytes) -> bool:
    """Invert each complete declared span and retain every unclassified byte."""
    if not old or len(old) > 32768 or not current or len(current) > 32768:
        return False
    reduced = current
    for inserted, previous in _AUTHOR_DEFAULT_SOURCE_REPLACEMENTS:
        if reduced.count(inserted) != 1:
            return False
        reduced = reduced.replace(inserted, previous, 1)
    return reduced == old


def _author_default_source_matches(old: bytes, current: bytes, selector: bytes) -> bool:
    """Reconstruct every old byte and close the finite selector syntax contract."""
    if not _author_window_selector_matches(selector):
        return False
    try:
        ast.parse(current)
    except (SyntaxError, UnicodeError, ValueError, RecursionError):
        return False
    return _restore_author_default_source(old, current)


def _author_default_source_correspondence(
    repository: Path,
    historical: JsonObject,
    old: bytes,
    current: bytes,
    logical: str,
    source_buffer: SourceCapsule,
) -> JsonObject:
    """Keep default author-window input semantics separate from new-window admission."""
    if (
        historical != {"path": AUTHOR_DEFAULT_SOURCE, **AUTHOR_DEFAULT_IDENTITY}
        or type(historical.get("bytes")) is not int
        or len(old) != AUTHOR_DEFAULT_IDENTITY["bytes"]
        or hashlib.sha256(old).hexdigest() != AUTHOR_DEFAULT_IDENTITY["sha256"]
        or logical not in source_buffer.detached
        or not logical.endswith("/" + AUTHOR_DEFAULT_SOURCE)
        or source_buffer.repository != repository
    ):
        raise ReportRebuildError("Author default historical source binding differs")
    if source_buffer.descriptor.members.get(logical) != AUTHOR_DEFAULT_IDENTITY:
        raise ReportRebuildError("Author default detached member identity differs")
    if source_buffer.read_source(logical) != old:
        raise ReportRebuildError("Author default detached member bytes differ")
    wrapper = _regular_confined_file(
        repository, AUTHOR_DEFAULT_SOURCE, "current author default source"
    )
    selector = _regular_confined_file(
        repository, AUTHOR_WINDOW_SOURCE, "author source-window selector"
    )
    if (
        wrapper.stat().st_nlink != 1
        or selector.stat().st_nlink != 1
        or not 0 < selector.stat().st_size <= 16384
        or wrapper.read_bytes() != current
    ):
        raise ReportRebuildError("Author source counterpart custody differs")
    wrapper_stat = wrapper.stat()
    selector_stat = selector.stat()
    selector_body = selector.read_bytes()
    if not _author_default_source_matches(old, current, selector_body):
        raise ReportRebuildError(
            "Author source differs beyond finite default specialization"
        )
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    for path, before, expected in (
        (wrapper, wrapper_stat, current),
        (selector, selector_stat, selector_body),
    ):
        checked = _regular_confined_file(
            repository,
            path.relative_to(repository).as_posix(),
            "fresh author source counterpart",
        )
        after = checked.stat()
        if (
            any(getattr(before, field) != getattr(after, field) for field in fields)
            or checked.read_bytes() != expected
        ):
            raise ReportRebuildError(
                "Author source counterpart changed during verification"
            )
    return {
        "path": AUTHOR_DEFAULT_SOURCE,
        "classification": "finite_author_default_window_specialization",
        "historical": dict(AUTHOR_DEFAULT_IDENTITY),
        "default_window": 5,
        "old_whole_source_reconstructed_exact": True,
        "selector_complete_syntax_contract_checked": True,
        "default_input_arrays_qualified_separately": True,
        "additional_malformed_input_refusals": True,
        "other_window_or_materializer_execution_admitted": False,
        "native_execution_claimed": False,
    }
