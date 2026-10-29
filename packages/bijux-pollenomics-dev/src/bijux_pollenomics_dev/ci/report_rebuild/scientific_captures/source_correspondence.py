"""Authenticate exact reviewed report-owner changes beside immutable science."""

from __future__ import annotations

import hashlib
import os
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
AUTHOR_PROFILE_SOURCE = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/author_site_evaluations.py"
AUTHOR_PROFILE_HISTORICAL = {
    "sha256": "a62cf71600143f1a64f19fb28f3d6d6a4dce54872779d8f65fa15c5802a9174f",
    "bytes": 14691,
}
AUTHOR_PROFILE_CURRENT = {
    "sha256": "196f6aa27e40655f28cf537d4ac4a1463741da54407469097fe00113a3f2d2a2",
    "bytes": 20514,
    "Git_blob": "1c3a3c8efe1b012f186e39323cce8aabc43e3939",
}
AUTHOR_PROFILE_PROPOSAL_SHA256 = (
    "ae8f7410d014f60d986180328142eb750389eca5b272ee84489228464a27c4ea"
)
AUTHOR_PROFILE_QUALIFICATION_SHA256 = (
    "9184a85dd597cf72febf8e54f01ab24fd7ee6a39f16a9c171067ccb041852c4c"
)
AUTHOR_PROFILE_REVIEW_SHA256 = (
    "d77886dda34620be21498d64721cf2275694088f93f0a82e3885d15868f3df63"
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


def _head_author_profile_source(repository: Path) -> tuple[bytes, str]:
    """Bind current committed helper bytes through Git without repository overrides."""
    if any(
        key.startswith("DYLD_")
        or key in {"LD_PRELOAD", "LD_LIBRARY_PATH", "__PYVENV_LAUNCHER__"}
        for key in os.environ
    ):
        raise ReportRebuildError("Author profile Git loader override refused")
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    env.update(
        GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_OPTIONAL_LOCKS="0"
    )
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(repository), "show", "HEAD:" + AUTHOR_PROFILE_SOURCE],
            timeout=20,
            stderr=subprocess.PIPE,
            env=env,
        )
        revision = (
            subprocess.check_output(
                ["git", "-C", str(repository), "rev-parse", "HEAD"],
                timeout=20,
                stderr=subprocess.PIPE,
                env=env,
            )
            .decode()
            .strip()
        )
    except (OSError, subprocess.SubprocessError, UnicodeError) as error:
        raise ReportRebuildError(
            "Author profile source has no current Git identity"
        ) from error
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ReportRebuildError("Author profile current Git identity differs")
    return raw, revision


def validated_author_profile_source_correspondence(
    repository: Path, historical: JsonObject, retained_source: Path
) -> JsonObject:
    """Recognize only the reviewed custody prerequisite and strict member guard change."""
    if (
        historical != {"path": AUTHOR_PROFILE_SOURCE, **AUTHOR_PROFILE_HISTORICAL}
        or type(historical.get("bytes")) is not int
    ):
        raise ReportRebuildError(
            "Scientific source mismatch has no reviewed author-profile correspondence"
        )
    try:
        current = _regular_confined_file(
            repository, AUTHOR_PROFILE_SOURCE, "reviewed author-profile owner source"
        )
        retained = _regular_confined_file(
            repository,
            retained_source.relative_to(repository).as_posix(),
            "original retained author-profile owner source",
        )
        old, new = retained.read_bytes(), current.read_bytes()
    except (ValueError, OSError, ReportOwnershipError) as error:
        raise ReportRebuildError(
            "Author-profile source is absent, linked or unconfined"
        ) from error
    if (
        len(old) != AUTHOR_PROFILE_HISTORICAL["bytes"]
        or hashlib.sha256(old).hexdigest() != AUTHOR_PROFILE_HISTORICAL["sha256"]
    ):
        raise ReportRebuildError("Original author-profile source bytes changed")
    blob = hashlib.sha1(b"blob " + str(len(new)).encode() + b"\0" + new).hexdigest()
    if (
        len(new) != AUTHOR_PROFILE_CURRENT["bytes"]
        or hashlib.sha256(new).hexdigest() != AUTHOR_PROFILE_CURRENT["sha256"]
        or blob != AUTHOR_PROFILE_CURRENT["Git_blob"]
    ):
        raise ReportRebuildError(
            "Current author-profile source is not the exact reviewed correction"
        )
    committed, revision = _head_author_profile_source(repository)
    if committed != new:
        raise ReportRebuildError(
            "Reviewed author-profile source differs from current Git"
        )
    return {
        "path": AUTHOR_PROFILE_SOURCE,
        "historical": dict(AUTHOR_PROFILE_HISTORICAL),
        "current": dict(AUTHOR_PROFILE_CURRENT),
        "current_Git_commit": revision,
        "source_proposal_sha256": AUTHOR_PROFILE_PROPOSAL_SHA256,
        "source_qualification_sha256": AUTHOR_PROFILE_QUALIFICATION_SHA256,
        "independent_review_sha256": AUTHOR_PROFILE_REVIEW_SHA256,
        "classification": "exact-author-profile-owner-criterion-correspondence",
        "original_source_member_retained_byteexact": True,
        "numerical_reexecution_claimed": False,
        "all_eight_scientific_product_checks_preserved": True,
        "profile_original_lawful_custody_criterion_preserved": True,
        "profile_owner_admission_claimed": False,
        "scope": "Only the original author-profile lawful-custody prerequisite, disclosed byte-identical producer relocation, seven other retained entries after validating all eight scientific products, and stricter FIFO/special-file refusal. Scientific/native helper functions and the complete scientific body remain unchanged. Original constrained numerical execution/source custody remains literal. This is neither arbitrary implementation equivalence, source permission, new numerical evidence nor whole-current-tree replay.",
    }
