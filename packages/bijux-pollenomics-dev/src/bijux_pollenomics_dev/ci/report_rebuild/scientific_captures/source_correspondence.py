"""Authenticate one reviewed report-owner validator change beside immutable science."""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

from ..contracts import JsonObject, ReportRebuildError
from ..ownership import ReportOwnershipError, _regular_confined_file

NORDIC_SOURCE = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/nordic_static_basin.py"
HISTORICAL = {
    "sha256": "a6e61374431cfb1c8678238b8e6b61b81f7235cd26b472927c8182485706a953",
    "bytes": 5593,
}
CURRENT = {
    "sha256": "eec38b9950f06b0af567a081bb2732f19ce6bc24c1768e939b80044091ed388e",
    "bytes": 5715,
    "Git_blob": "baf185b3af91f30d67b93b0926a879ca7ffb7df7",
}
BOUNDARY_REVIEW_SHA256 = (
    "0dd900772ceea759cfa760dac6b8f6e0c887b67710cfe78e5d08541a43c45ec3"
)


def _head_source(repository: Path) -> tuple[bytes, str]:
    """Read actual committed bytes; caller-supplied approval flags are not accepted."""
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(repository), "show", "HEAD:" + NORDIC_SOURCE],
            timeout=20,
            stderr=subprocess.PIPE,
        )
        revision = (
            subprocess.check_output(
                ["git", "-C", str(repository), "rev-parse", "HEAD"],
                timeout=20,
                stderr=subprocess.PIPE,
            )
            .decode()
            .strip()
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ReportRebuildError(
            "Reviewed metadata source has no current Git identity"
        ) from error
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ReportRebuildError("Reviewed metadata source Git identity differs")
    return raw, revision


def validated_metadata_source_correspondence(
    repository: Path, historical: JsonObject, retained_source: Path
) -> JsonObject:
    """Admit only the exact Nordic22 ownership predicate correction, never math drift."""
    if historical != {"path": NORDIC_SOURCE, **HISTORICAL}:
        raise ReportRebuildError(
            "Scientific source mismatch has no reviewed metadata correspondence"
        )
    try:
        current = _regular_confined_file(
            repository, NORDIC_SOURCE, "reviewed metadata source"
        )
        name = retained_source.relative_to(repository).as_posix()
        retained = _regular_confined_file(
            repository, name, "original retained metadata source"
        )
        old, new = retained.read_bytes(), current.read_bytes()
    except (ValueError, OSError, ReportOwnershipError) as error:
        raise ReportRebuildError(
            "Reviewed metadata source is absent, linked or unconfined"
        ) from error
    if (
        len(old) != HISTORICAL["bytes"]
        or hashlib.sha256(old).hexdigest() != HISTORICAL["sha256"]
    ):
        raise ReportRebuildError("Original retained metadata source bytes changed")
    blob = hashlib.sha1(b"blob " + str(len(new)).encode() + b"\0" + new).hexdigest()
    if (
        len(new) != CURRENT["bytes"]
        or hashlib.sha256(new).hexdigest() != CURRENT["sha256"]
        or blob != CURRENT["Git_blob"]
    ):
        raise ReportRebuildError(
            "Current metadata source is not the exact reviewed correction"
        )
    committed, revision = _head_source(repository)
    if committed != new:
        raise ReportRebuildError("Reviewed metadata source differs from current Git")
    return {
        "path": NORDIC_SOURCE,
        "historical": dict(HISTORICAL),
        "current": dict(CURRENT),
        "current_Git_commit": revision,
        "boundary_review_sha256": BOUNDARY_REVIEW_SHA256,
        "classification": "exact-report-owner-validation-correspondence",
        "original_source_member_retained_byteexact": True,
        "numerical_reexecution_claimed": False,
        "scope": "Only the sealed Nordic22 CI capture-owner selection changes: disjoint sibling ownership is allowed, all selected22 role/hash/size/path authority and overlap refusals remain. Original numerical execution source custody is unchanged. This authenticates current metadata validation, not mathematical implementation equivalence for arbitrary source edits or a whole-current-tree replay.",
    }
