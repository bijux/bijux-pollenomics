"""Rebuild two comparison records from an authenticated native R source capture."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import stat
from typing import Any, TypedDict

from bijux_pollenomics_dev.lra_validation.live_reference_comparison import summarize
from bijux_pollenomics_dev.lra_validation.native_reference.capture_selection import (
    CaptureProfile,
    validated_current_capture,
)

_OWNER = "method-certification/current-r-oracle/report-products"
_POLICY = "configs/ci/report-ownership.json"
# These are declared consumer source and authenticated witness roles, rather than
# a claim about every module that Python imports incidentally.
_LAYOUT_CODE_INPUTS = frozenset(
    [
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/source_layout_adoption.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/uncertainty/joint_site_draws.py",
    ]
)
_LAYOUT_STATIC_DATA = frozenset(
    [
        "configs/ci/report-capture-projections/lra-uncertainty-source-layout.json",
        "data/source-custody/lra-uncertainty-layout/api-before-relocation.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/uncertainty/joint_aliquot_covariance.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/uncertainty/two_taxon_counting.py",
    ]
)
_OUTPUTS = {
    "docs/report/method-certification/current-r-oracle/report.json",
    "docs/report/method-certification/current-r-oracle/source-replay.json",
}


class _DigestInputs(TypedDict):
    code_sha256: dict[str, str]
    data_sha256: dict[str, str]
    owner_row_sha256: str
    capture_manifest_sha256: str
    capture_profile: CaptureProfile


class _ConsumerInputs(_DigestInputs):
    sha256: str


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _physical_digest(repository: Path, name: str) -> str:
    relative = Path(name)
    if (
        not name
        or "\\" in name
        or relative.is_absolute()
        or any(part in {"", ".", ".."} for part in name.split("/"))
    ):
        raise ValueError("Consumer source path must be confined")
    path = repository / relative
    for current in (path, *path.parents):
        if current == repository:
            break
        if current.is_symlink():
            raise ValueError("Consumer source aliases are refused")
    if not path.is_file() or path.stat().st_nlink != 1:
        raise ValueError("Consumer input requires an independently owned regular file")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _consumer_inputs(
    repository: Path, capture_manifest: str, capture_profile: CaptureProfile
) -> _ConsumerInputs:
    """Bind the declared code and data bytes without self-referential Git metadata."""
    policy_sha = _physical_digest(repository, _POLICY)
    payload = (repository / _POLICY).read_bytes()
    if hashlib.sha256(payload).hexdigest() != policy_sha:
        raise ValueError("Native consumer policy changed during input collection")
    policy = json.loads(payload)
    rows = [row for row in policy["owners"] if row["owner_id"] == _OWNER]
    if len(rows) != 1:
        raise ValueError("Exactly one native comparison owner is required")
    row = rows[0]
    code, data = row["producer_paths"], row["producer_inputs"]
    selected_manifest = (
        f"data/method-certification/native-r-{capture_profile}/capture/capture.json"
    )
    if (
        row["role"] != "generated_owner"
        or set(row["paths"]) != _OUTPUTS
        or len(row["paths"]) != len(_OUTPUTS)
        or not isinstance(code, list)
        or not isinstance(data, list)
        or any(not isinstance(name, str) for name in code + data)
        or len(code) != 100
        or not set(code) >= _LAYOUT_CODE_INPUTS
        or len(set(code)) != len(code)
        or len(data) != 291
        or not set(data) >= _LAYOUT_STATIC_DATA
        or len(set(data)) != len(data)
        or _POLICY not in data
        or selected_manifest not in data
        or set(code) & set(data)
        or _OUTPUTS & set(code + data)
        or any(
            not name.startswith("packages/") or not name.endswith((".py", ".R"))
            for name in code
        )
    ):
        raise ValueError(
            "Exact disjoint native consumer code/data declaration required"
        )
    inputs: _DigestInputs = {
        "code_sha256": {
            name: _physical_digest(repository, name) for name in sorted(code)
        },
        "data_sha256": {
            name: _physical_digest(repository, name) for name in sorted(data)
        },
        "owner_row_sha256": _canonical_digest(row),
        "capture_manifest_sha256": capture_manifest,
        "capture_profile": capture_profile,
    }
    if inputs["data_sha256"][_POLICY] != policy_sha:
        raise ValueError("Native consumer policy changed during input collection")
    return {**inputs, "sha256": _canonical_digest(inputs)}


def _evidence_destination(repository: Path, output: Path) -> Path:
    """Keep raw comparison evidence outside the exact configured output namespace."""
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("native R comparison output must be absent")
    if output != output.resolve():
        raise ValueError(
            "native comparison output route must be physical and canonical"
        )
    artifacts = repository / "artifacts"
    if (
        not output.is_relative_to(artifacts)
        or output.parent.name != "producer-output"
        or output.name != "source-products"
    ):
        raise ValueError(
            "native comparison requires the configured artifact output route"
        )
    for ancestor in (output.parent, *output.parent.parents):
        if ancestor == repository:
            break
        if not stat.S_ISDIR(ancestor.lstat().st_mode):
            raise ValueError("native comparison output has a non-real ancestor")
    evidence = output.parent.parent / "native-comparison"
    if (
        output.exists()
        or output.is_symlink()
        or evidence.exists()
        or evidence.is_symlink()
    ):
        raise ValueError("native R comparison output and evidence must be absent")
    return evidence


def build(
    repository: Path, output: Path, *, capture_profile: CaptureProfile = "annulus"
) -> dict[str, Any]:
    """Recompute original-R comparisons without implying a new native R execution."""
    repository = repository.resolve(strict=True)
    evidence = _evidence_destination(repository, output)
    before = validated_current_capture(repository, profile=capture_profile)
    consumer = _consumer_inputs(repository, before.manifest_sha256, capture_profile)
    report = summarize(
        repository,
        before.directory,
        repository
        / "docs/report/method-certification/original-r-reference/reference-bundle",
        evidence,
        before.source_archives,
    )
    after = validated_current_capture(repository, profile=capture_profile)
    if (
        before != after
        or _consumer_inputs(repository, after.manifest_sha256, capture_profile)
        != consumer
    ):
        raise ValueError("native R source changed during comparison")
    replay = json.loads((evidence / "source-replay.json").read_text())
    report = copy.deepcopy(report)
    report.pop("private_source_custody", None)
    replay.pop("source_revision")
    report["schema_version"] = "retained-native-r-comparison-report.v1"
    replay["schema_version"] = "retained-native-r-comparison-source-replay.v1"
    capture_scope = {
        "native_capture_profile": capture_profile,
        "native_capture_source_revision": before.source_revision,
        "native_capture_manifest_sha256": before.manifest_sha256,
        "native_capture_source_context": before.source_context,
        "fresh_R_executed_for_this_comparison": False,
        "current_python_expectations_regenerated_for_this_comparison": False,
        "consumer_inputs": consumer,
        "scope": "retained native R capture against original R vectors; current consumer code and data bytes are independently identified, protected captured science inputs match, and neither R nor Python expectations are newly executed",
        "native_source_acquisition": "retained_public_locked_archive_acquisition",
    }
    report.update(capture_scope)
    replay.update(capture_scope)
    output.mkdir()
    for name, value in (("report.json", report), ("source-replay.json", replay)):
        payload = json.dumps(value, indent=2, allow_nan=False) + "\n"
        (output / name).write_text(payload)
    return report


def main() -> None:
    """Expose the ordinary configured report-owner invocation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--capture-profile",
        choices=("annulus", "count-domain", "finite-covariance"),
        default="annulus",
    )
    args = parser.parse_args()
    build(args.repository, args.output, capture_profile=args.capture_profile)


if __name__ == "__main__":
    main()
