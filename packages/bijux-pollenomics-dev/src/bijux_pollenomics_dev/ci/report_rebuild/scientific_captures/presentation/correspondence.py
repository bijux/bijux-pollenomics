"""Bind one reviewed atlas presentation change beside immutable numerical sources."""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import ReportOwnershipError, _regular_confined_file

PRESENTATION_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/document.html"
HISTORICAL = {
    "sha256": "9d8c34561c6655a31757eccb3b7349acf47687a571140181ec5b7d353cf2bc50",
    "bytes": 463440,
}
CURRENT = {
    "sha256": "9ae82cb1affdd08256d6181d922601433c9aa8441ca9b1444785f5d923131bf2",
    "bytes": 463747,
    "Git_blob": "9308575531dd0528442620c5b605589e173386e4",
}
SOURCE_PROPOSAL_SHA256 = (
    "a135fb04095ddc43a3acf422df0440f458a1f5c43be97274bed24cd1db382e98"
)
SOURCE_QUALIFICATION_SHA256 = (
    "cd214229739ab7b05c9860d2709424104dc8a27d4a5999f67c8cb7c2e67d5d4e"
)
INDEPENDENT_REVIEW_SHA256 = (
    "333eee7402898766fde62d4d401f59256ab9c247ec3cc199450dcdb1470d43ff"
)


def _head_template(repository: Path) -> tuple[bytes, str]:
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(repository), "show", "HEAD:" + PRESENTATION_SOURCE],
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
            "Reviewed presentation source has no current Git identity"
        ) from error
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ReportRebuildError("Reviewed presentation source Git identity differs")
    return raw, revision


def validated_presentation_source_correspondence(
    repository: Path, historical: JsonObject, retained_source: Path
) -> JsonObject:
    """Preserve original numerical capture; require new browser qualification separately."""
    if (
        historical != {"path": PRESENTATION_SOURCE, **HISTORICAL}
        or type(historical.get("bytes")) is not int
    ):
        raise ReportRebuildError(
            "Scientific source mismatch has no reviewed presentation correspondence"
        )
    try:
        current = _regular_confined_file(
            repository, PRESENTATION_SOURCE, "reviewed atlas presentation source"
        )
        original = _regular_confined_file(
            repository,
            retained_source.relative_to(repository).as_posix(),
            "original retained atlas presentation source",
        )
        old, new = original.read_bytes(), current.read_bytes()
    except (OSError, ValueError, ReportOwnershipError) as error:
        raise ReportRebuildError(
            "Reviewed presentation source is absent, linked or unconfined"
        ) from error
    if (
        len(old) != HISTORICAL["bytes"]
        or hashlib.sha256(old).hexdigest() != HISTORICAL["sha256"]
    ):
        raise ReportRebuildError("Original retained presentation source bytes changed")
    blob = hashlib.sha1(b"blob " + str(len(new)).encode() + b"\0" + new).hexdigest()
    if (
        len(new) != CURRENT["bytes"]
        or hashlib.sha256(new).hexdigest() != CURRENT["sha256"]
        or blob != CURRENT["Git_blob"]
    ):
        raise ReportRebuildError(
            "Current presentation source is not the exact reviewed correction"
        )
    committed, revision = _head_template(repository)
    if committed != new:
        raise ReportRebuildError(
            "Reviewed presentation source differs from current Git"
        )
    return {
        "path": PRESENTATION_SOURCE,
        "historical": dict(HISTORICAL),
        "current": dict(CURRENT),
        "current_Git_commit": revision,
        "source_proposal_sha256": SOURCE_PROPOSAL_SHA256,
        "source_qualification_sha256": SOURCE_QUALIFICATION_SHA256,
        "independent_review_sha256": INDEPENDENT_REVIEW_SHA256,
        "classification": "exact-atlas-presentation-source-correspondence",
        "original_source_member_retained_byteexact": True,
        "numerical_reexecution_claimed": False,
        "fresh_browser_capture_required": True,
        "historical_browser_capture_qualified_for_current_HTML": False,
        "scope": "Only offline native ReadableStream construction and detail-paging sequential focus change in this exact atlas template. Gzip/CRC/UTF8/length/base64/refusal and temporal/scientific source admission semantics remain. Original numerical source/resources are retained unchanged. This is a presentation correspondence, not a numerical replay, current browser certificate, historical native-footprint waiver or whole-current-tree equivalence. Fresh source-owned exports/native browser/capture admission remain required.",
    }
