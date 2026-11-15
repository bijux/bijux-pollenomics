"""Bind one strict native geography refusal protocol to four fixed original epochs."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule

NEOTOMA_COUNTRY_JSON_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/neotoma/country/site_geometry.py"
_ORIGINAL_IDENTITY = {
    "bytes": 1390,
    "sha256": "d505b30b823ecfa8f039a5154e6382ec46ee9174f9134026b7d71616574b4040",
}
_CAPTURE_CONTEXTS = {
    "data/atlas/sample-chronology-source-view-capture": (
        "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62",
        ("source/",),
    ),
    "data/method-certification/author-optimizer-diagnostic-source-capture": (
        "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
        ("executions/optimizer-diagnostics/first-party-inputs/",),
    ),
    "data/method-certification/constrained-author-source-capture": (
        "fa46f5757af2acfb647f82162314b11c5e9401fbd7ecdbff585b70a687b9080c",
        ("executions/complete-constrained/first-party-inputs/",),
    ),
    "data/method-certification/author-radius-source-capture": (
        "e7d813c70f4a15befd4d99cd5ca02aa062075cad5e28081aed9aa28ec56b7e41",
        (
            "executions/paired-comparison/first-party-inputs/",
            "executions/radius-forward/first-party-inputs/",
        ),
    ),
}
_COUNTRY_JSON_SPANS = (
    (
        b"from collections.abc import Mapping\nimport json\n\nfrom bijux_pollenomics.collection.spatial import (\n    classify_country,\n    geometry_to_representative_point,\n    point_in_bbox,\n)\nfrom bijux_pollenomics.core.text import clean_optional_text\n",
        b"from collections.abc import Mapping\n\nfrom bijux_pollenomics.collection.spatial import (\n    classify_country,\n    geometry_to_representative_point,\n    point_in_bbox,\n)\nfrom bijux_pollenomics.core.text import clean_optional_text\n\nfrom ..client import decode_neotoma_json_object\n",
    ),
    (
        b"    try:\n        geography = json.loads(geography_text)\n    except json.JSONDecodeError:\n        return None\n    if not isinstance(geography, dict):\n        return None\n",
        b"    try:\n        geography = decode_neotoma_json_object(geography_text)\n    except ValueError:\n        return None\n",
    ),
)


def country_json_protocol_matches(name: str, captured: bytes, current: bytes) -> bool:
    """Restore only two literal spans to the complete authenticated old module."""
    if (
        name != NEOTOMA_COUNTRY_JSON_SOURCE
        or {"bytes": len(captured), "sha256": hashlib.sha256(captured).hexdigest()}
        != _ORIGINAL_IDENTITY
    ):
        return False
    restored = current
    for old, new in _COUNTRY_JSON_SPANS:
        if restored.count(new) != 1:
            return False
        restored = restored.replace(new, old, 1)
    return restored == captured and all(
        restored.count(old) == 1 for old, _ in _COUNTRY_JSON_SPANS
    )


def validated_neotoma_country_json_source(
    repository: Path, historical: JsonObject, logical: str, source_buffer: SourceCapsule
) -> JsonObject:
    """Authenticate original custody and current source separately, without execution."""
    context = _CAPTURE_CONTEXTS.get(source_buffer.prefix)
    if context is None:
        raise ReportRebuildError("Unknown Neotoma country source context")
    capture_sha, prefixes = context
    name = NEOTOMA_COUNTRY_JSON_SOURCE
    aliases = tuple(prefix + name for prefix in prefixes)
    if (
        repository != repository.resolve()
        or source_buffer.repository != repository
        or historical != {"path": name, **_ORIGINAL_IDENTITY}
        or type(historical.get("bytes")) is not int
        or logical not in aliases
        or source_buffer.descriptor.capture_name != "capture.json"
        or source_buffer.descriptor.capture.get("sha256") != capture_sha
        or {
            member
            for member in source_buffer.descriptor.members
            if member.endswith("/" + name)
        }
        != set(aliases)
        or {
            member
            for group in source_buffer.descriptor.groups
            for member, path in group["resolved_paths"]
            if path == name
        }
        != set(aliases)
    ):
        raise ReportRebuildError("Neotoma country original context binding differs")
    source_buffer.fresh()
    originals = []
    for alias in aliases:
        if (
            alias not in source_buffer.detached
            or source_buffer.descriptor.members.get(alias) != _ORIGINAL_IDENTITY
            or [
                path
                for group in source_buffer.descriptor.groups
                for member, path in group["resolved_paths"]
                if member == alias
            ]
            != [name]
        ):
            raise ReportRebuildError("Neotoma country original member binding differs")
        originals.append(source_buffer.read_source(alias))
    if any(body != originals[0] for body in originals):
        raise ReportRebuildError("Neotoma country original aliases differ")
    path = _regular_confined_file(repository, name, "current Neotoma country source")
    before = path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 8192:
        raise ReportRebuildError(
            "Neotoma country current source is linked or unbounded"
        )
    current = path.read_bytes()
    if not country_json_protocol_matches(name, originals[0], current):
        raise ReportRebuildError(
            "Neotoma country source exceeds its exact refusal protocol"
        )
    source_buffer.fresh()
    again = _regular_confined_file(repository, name, "current Neotoma country source")
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
        raise ReportRebuildError("Neotoma country source changed during verification")
    return {
        "path": name,
        "classification": "strict_neotoma_country_json_refusal",
        "original_member": logical,
        "original_members": list(aliases),
        "historical": dict(_ORIGINAL_IDENTITY),
        "current": {
            "bytes": len(current),
            "sha256": hashlib.sha256(current).hexdigest(),
        },
        "whole_old_module_reconstructed": True,
        "current_regular_single_link_and_stable": True,
        "historical_execution_epoch_changed": False,
        "current_country_or_numerical_equivalence_claimed": False,
        "historical_program_execution_claimed": False,
        "current_malformed_geometry_qualification_required_separately": True,
    }
