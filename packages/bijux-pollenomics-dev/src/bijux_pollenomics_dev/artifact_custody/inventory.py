"""Bounded artifact accounting and evidence-preserving retention review."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time
from typing import Any

CAP_BYTES = 800_000_000_000
OUTPUT_RESERVE_BYTES = 10_000_000
_SELECTED_PREFIXES = (
    "v2/validation/live-r-integration/acquire-001/sources",
    "v2/linux-r-runtime/build001",
    "v2/linux-r-runtime/provision001",
    "jobs/linux-r-oracle/source-closed-run",
    "jobs/linux-r-oracle/run",
    "jobs/linux-r-oracle/mypy-cache",
    "jobs/linux-r-oracle/test-run",
    "jobs/neotoma-first-observed/mypy-cache",
)
_CACHE_CANDIDATES = (
    (
        "jobs/linux-r-oracle/mypy-cache",
        "jobs/linux-r-oracle/terminal-checks.log",
        "--cache-dir",
    ),
    (
        "jobs/linux-r-oracle/test-run",
        "jobs/linux-r-oracle/terminal-checks.log",
        "--basetemp",
    ),
    (
        "jobs/neotoma-first-observed/mypy-cache",
        "jobs/neotoma-first-observed/terminal-checks.log",
        "--cache-dir",
    ),
)
_REFERENCE_RE = re.compile(r"artifacts/[A-Za-z0-9._+/:-]+")
_TEXT_SUFFIXES = frozenset(
    {".md", ".json", ".py", ".toml", ".yml", ".yaml", ".mk", ".sh", ".mjs"}
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _empty_size() -> dict[str, int]:
    return {"apparent_bytes": 0, "allocated_bytes": 0, "entries": 0, "files": 0}


def _add_size(row: dict[str, int], size: int, blocks: int, regular: bool) -> None:
    row["apparent_bytes"] += size
    row["allocated_bytes"] += blocks * 512
    row["entries"] += 1
    row["files"] += int(regular)


def scan_artifacts(
    root: Path,
    *,
    max_entries: int = 2_000_000,
    max_seconds: float = 180,
    selected_prefixes: tuple[str, ...] = _SELECTED_PREFIXES,
) -> dict[str, Any]:
    """Count lstat bytes once; never traverse links or hash ordinary contents."""
    if not root.is_dir() or root.is_symlink():
        raise ValueError("Artifact root must be a real directory")
    started = time.monotonic()
    stack = [root]
    seen_inodes: set[tuple[int, int]] = set()
    summary = _empty_size()
    top: dict[str, dict[str, int]] = defaultdict(_empty_size)
    selected: dict[str, dict[str, int]] = {
        prefix: _empty_size() for prefix in selected_prefixes
    }
    symlinks: list[dict[str, str]] = []
    hardlinks: list[dict[str, str]] = []
    first_inode_path: dict[tuple[int, int], str] = {}
    process_records: list[str] = []
    errors: list[str] = []
    unique_inode_apparent_bytes = 0
    unique_inode_allocated_bytes = 0
    symlink_count = 0
    hardlink_path_count = 0
    special_count = 0
    limit_reason: str | None = None
    while stack:
        if summary["entries"] >= max_entries:
            limit_reason = "entry_limit"
            break
        if time.monotonic() - started > max_seconds:
            limit_reason = "time_limit"
            break
        directory = stack.pop()
        try:
            with os.scandir(directory) as listing:
                entries = list(listing)
        except OSError as error:
            errors.append(f"{directory.relative_to(root)}: {type(error).__name__}")
            continue
        for entry in entries:
            if summary["entries"] >= max_entries:
                limit_reason = "entry_limit"
                break
            if (
                summary["entries"] % 4096 == 0
                and time.monotonic() - started > max_seconds
            ):
                limit_reason = "time_limit"
                break
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as error:
                errors.append(f"{relative}: {type(error).__name__}")
                continue
            regular = stat.S_ISREG(info.st_mode)
            directory_entry = stat.S_ISDIR(info.st_mode)
            link = stat.S_ISLNK(info.st_mode)
            _add_size(summary, info.st_size, info.st_blocks, regular)
            _add_size(
                top[relative.split("/", 1)[0]], info.st_size, info.st_blocks, regular
            )
            for prefix, group in selected.items():
                if relative == prefix or relative.startswith(prefix + "/"):
                    _add_size(group, info.st_size, info.st_blocks, regular)
            inode = (info.st_dev, info.st_ino)
            if inode not in seen_inodes:
                seen_inodes.add(inode)
                unique_inode_apparent_bytes += info.st_size
                unique_inode_allocated_bytes += info.st_blocks * 512
                if info.st_nlink > 1 and len(first_inode_path) < 1000:
                    first_inode_path[inode] = relative
            elif regular:
                hardlink_path_count += 1
                if len(hardlinks) < 100:
                    hardlinks.append(
                        {
                            "path": relative,
                            "first_seen": first_inode_path.get(inode, "not_retained"),
                        }
                    )
            if link:
                symlink_count += 1
                if len(symlinks) < 100:
                    try:
                        target = os.readlink(path)
                    except OSError:
                        target = "unreadable"
                    symlinks.append({"path": relative, "target": target})
            elif directory_entry:
                stack.append(path)
            elif not regular:
                special_count += 1
            if (
                regular
                and path.name == "process.json"
                and info.st_size <= 65_536
                and len(process_records) < 5000
            ):
                process_records.append(relative)
        if limit_reason is not None:
            break
    return {
        "complete": not stack and limit_reason is None and not errors,
        "limit_reason": limit_reason,
        "errors": errors[:100],
        "error_count": len(errors),
        "elapsed_seconds": time.monotonic() - started,
        "bytes": summary,
        "unique_inode_apparent_bytes": unique_inode_apparent_bytes,
        "unique_inode_allocated_bytes": unique_inode_allocated_bytes,
        "unique_inode_count": len(seen_inodes),
        "top_level": dict(sorted(top.items())),
        "selected_prefixes": selected,
        "symlink_count": symlink_count,
        "symlink_examples": symlinks,
        "hardlink_path_count": hardlink_path_count,
        "hardlink_examples": hardlinks,
        "special_entry_count": special_count,
        "process_record_paths": process_records,
    }


def cap_decision(scan: dict[str, Any]) -> dict[str, Any]:
    """Use apparent bytes conservatively and refuse incomplete measurements."""
    apparent = int(scan["bytes"]["apparent_bytes"])
    complete = bool(scan["complete"])
    if not complete:
        status = "indeterminate_incomplete_scan"
    elif apparent + OUTPUT_RESERVE_BYTES < CAP_BYTES:
        status = "observed_below_cap"
    else:
        status = "at_or_above_reserved_cap_boundary"
    return {
        "threshold_bytes": CAP_BYTES,
        "output_reserve_bytes": OUTPUT_RESERVE_BYTES,
        "observed_apparent_bytes": apparent,
        "remaining_to_threshold_bytes": CAP_BYTES - apparent,
        "status": status,
        "deletion_required_now": status == "at_or_above_reserved_cap_boundary",
        "deletion_authorized_by_this_report": False,
    }


def scan_references(
    repository: Path,
    *,
    max_files: int = 30_000,
    max_total_bytes: int = 250_000_000,
    max_file_bytes: int = 8_000_000,
    max_seconds: float = 45,
) -> dict[str, Any]:
    """Find durable artifact path mentions without reading unbounded reports."""
    started = time.monotonic()
    roots = (
        repository / "docs/report",
        repository / "configs",
        repository / "makes",
        repository / ".github/workflows",
        repository / "packages/bijux-pollenomics-dev/src",
        repository / "packages/bijux-pollenomics/src",
        repository / "packages/bijux-pollenomics-lra/src",
    )
    stack = [path for path in roots if path.is_dir()]
    references: dict[str, list[str]] = defaultdict(list)
    files_seen = 0
    bytes_read = 0
    skipped_large = 0
    errors: list[str] = []
    limit_reason: str | None = None
    while stack:
        if files_seen >= max_files or bytes_read >= max_total_bytes:
            limit_reason = "file_or_byte_limit"
            break
        if time.monotonic() - started > max_seconds:
            limit_reason = "time_limit"
            break
        directory = stack.pop()
        try:
            with os.scandir(directory) as listing:
                entries = list(listing)
        except OSError as error:
            errors.append(
                f"{directory.relative_to(repository)}: {type(error).__name__}"
            )
            continue
        for entry in entries:
            path = Path(entry.path)
            if entry.is_symlink():
                continue
            if entry.is_dir(follow_symlinks=False):
                stack.append(path)
                continue
            if (
                not entry.is_file(follow_symlinks=False)
                or path.suffix not in _TEXT_SUFFIXES
            ):
                continue
            files_seen += 1
            size = entry.stat(follow_symlinks=False).st_size
            if size > max_file_bytes or bytes_read + size > max_total_bytes:
                skipped_large += 1
                continue
            try:
                value = path.read_bytes()
            except OSError as error:
                errors.append(f"{path.relative_to(repository)}: {type(error).__name__}")
                continue
            bytes_read += len(value)
            origin = path.relative_to(repository).as_posix()
            for match in _REFERENCE_RE.finditer(
                value.decode("utf-8", errors="replace")
            ):
                literal = match.group().rstrip(".,:;)]}>\"'`")
                parts = Path(literal).parts
                if ".." in parts or not literal.startswith("artifacts/"):
                    continue
                if len(references[literal]) < 10 and origin not in references[literal]:
                    references[literal].append(origin)
            if files_seen >= max_files or bytes_read >= max_total_bytes:
                limit_reason = "file_or_byte_limit"
                break
    return {
        "complete": not stack
        and limit_reason is None
        and not errors
        and skipped_large == 0,
        "limit_reason": limit_reason,
        "files_seen": files_seen,
        "bytes_read": bytes_read,
        "skipped_large_files": skipped_large,
        "error_count": len(errors),
        "errors": errors[:100],
        "references": dict(sorted(references.items())),
    }


def _proofs(repository: Path) -> list[dict[str, Any]]:
    lock = json.loads((repository / "configs/ci/lra-r-source-lock.v1.json").read_text())
    linux = json.loads(
        (
            repository / "docs/report/method-certification/linux-r-oracle/report.json"
        ).read_text()
    )
    selected = (
        (
            "artifacts/v2/validation/live-r-integration/acquire-001/sources/R-4.6.0.tar.xz",
            lock["r"]["sha256"],
            "private_source_custody",
        ),
        (
            "artifacts/v2/linux-r-runtime/build001/receipt/report.json",
            linux["source_lock"]["runtime_receipt_sha256"],
            "source_built_runtime_proof",
        ),
        (
            "artifacts/v2/linux-r-runtime/provision001/receipt/report.json",
            linux["source_lock"]["provision_receipt_sha256"],
            "private_library_proof",
        ),
        (
            "artifacts/jobs/linux-r-oracle/source-closed-run/receipt.json",
            _sha(
                repository
                / "docs/report/method-certification/linux-r-oracle/report.json"
            ),
            "raw_numerical_result_proof",
        ),
        (
            "artifacts/jobs/linux-r-oracle/run/receipt.json",
            None,
            "unique_source_drift_refusal",
        ),
        (
            "artifacts/jobs/linux-r-oracle/image-build.log",
            None,
            "unique_container_build_log",
        ),
    )
    result: list[dict[str, Any]] = []
    for relative, expected, role in selected:
        path = repository / relative
        row: dict[str, Any] = {
            "path": relative,
            "role": role,
            "expected_sha256": expected,
        }
        try:
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode):
                row["status"] = "not_regular_file"
            else:
                observed = _sha(path)
                row.update(
                    status=(
                        "content_recorded_without_prior_digest"
                        if expected is None
                        else "matched_declared_digest"
                        if expected == observed
                        else "digest_mismatch"
                    ),
                    byte_count=info.st_size,
                    sha256=observed,
                )
        except OSError as error:
            row.update(status="unavailable", error=type(error).__name__)
        result.append(row)
    return result


def _active_process_receipts(root: Path, paths: list[str]) -> dict[str, Any]:
    try:
        listing = subprocess.check_output(
            ["ps", "-axo", "pid=,command="], text=True, timeout=10
        )
        running = {
            int(line.strip().split(None, 1)[0])
            for line in listing.splitlines()
            if line.strip() and line.strip().split(None, 1)[0].isdigit()
        }
    except (OSError, subprocess.SubprocessError):
        return {
            "status": "process_snapshot_unavailable",
            "checked": 0,
            "pid_running": [],
        }
    observed: list[dict[str, Any]] = []
    checked = 0
    for relative in paths:
        try:
            row = json.loads((root / relative).read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(row, dict) or type(row.get("pid")) is not int:
            continue
        checked += 1
        if row["pid"] in running:
            observed.append({"receipt": relative, "pid": row["pid"]})
    return {
        "status": "pid_snapshot_only; reuse cannot establish job identity or inactivity",
        "checked": checked,
        "pid_running": observed[:100],
        "pid_running_count": len(observed),
    }


def _candidates(
    root: Path, scan: dict[str, Any], references: dict[str, Any]
) -> list[dict[str, Any]]:
    result = []
    for relative, receipt, marker in _CACHE_CANDIDATES:
        path = root / relative
        log = root / receipt
        cited = "artifacts/" + relative
        durable_refs = [
            key for key in references if key == cited or key.startswith(cited + "/")
        ]
        text = (
            log.read_text() if log.is_file() and log.stat().st_size < 2_000_000 else ""
        )
        basis = (
            marker in text and cited in text and path.is_dir() and not path.is_symlink()
        )
        result.append(
            {
                "path": cited,
                "metadata": scan["selected_prefixes"].get(relative),
                "receipt": "artifacts/" + receipt,
                "regeneration_command_recorded": basis,
                "durable_reference_mentions": durable_refs,
                "classification": "exact_regenerable_cache_for_review"
                if basis and not durable_refs
                else "not_established",
                "inactive_independently_verified": False,
                "deletion_authorized": False,
            }
        )
    return result


def build_inventory(
    repository: Path,
    output: Path,
    *,
    max_entries: int = 2_000_000,
    max_seconds: float = 180,
) -> dict[str, Any]:
    repository = repository.resolve(strict=True)
    artifact_root = repository / "artifacts"
    if output.exists():
        raise ValueError("Artifact inventory output must be absent")
    started = datetime.now(UTC).isoformat()
    scan = scan_artifacts(
        artifact_root, max_entries=max_entries, max_seconds=max_seconds
    )
    reference_scan = scan_references(repository)
    proofs = _proofs(repository)
    liveness = _active_process_receipts(artifact_root, scan["process_record_paths"])
    report: dict[str, Any] = {
        "schema_version": "artifact-retention-inventory.v1",
        "requirement_id": "V3-26",
        "observed_at_utc": started,
        "scope": "repository_root_artifacts_only",
        "method": "bounded_lstat_metadata; no_symlink_follow; selected_proof_hashes_only",
        "scan_limits": {"max_entries": max_entries, "max_seconds": max_seconds},
        "artifact_scan": scan,
        "reference_scan": reference_scan,
        "selected_proofs": proofs,
        "process_liveness": liveness,
        "cap_decision": cap_decision(scan),
        "regenerable_candidates": _candidates(
            artifact_root, scan, reference_scan["references"]
        ),
        "retention_decision": {
            "delete_anything": False,
            "reason": "Current cap decision and exact evidence review do not authorize deletion; unclassified bytes, unique proofs, private sources, and live/unknown jobs remain protected.",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def bind_native_cap_check(
    repository: Path,
    metadata_report: Path,
    native_receipt: Path,
    output: Path,
    *,
    concurrent_artifact_writes_observed: bool = False,
) -> dict[str, Any]:
    """Bind a completed native traversal without upgrading an incomplete inode scan."""
    if output.exists():
        raise ValueError("Combined artifact inventory output must be absent")
    report: dict[str, Any] = json.loads(metadata_report.read_text())
    receipt = json.loads(native_receipt.read_text())
    if report.get("requirement_id") != "V3-26":
        raise ValueError("Metadata inventory requirement identity differs")
    if (
        receipt.get("exit_code") != 0
        or receipt.get("threshold_bytes") != CAP_BYTES
        or receipt.get("display_unit_bytes") != 512
        or receipt.get("command")
        != [
            "du",
            "-A",
            "-B",
            "1",
            "-l",
            "-s",
            str((repository / "artifacts").resolve()),
        ]
    ):
        raise ValueError("Native apparent-byte command or result differs")
    raw_stdout = (repository / receipt["stdout_path"]).read_text()
    raw_stderr = (repository / receipt["stderr_path"]).read_text()
    if raw_stderr or len(raw_stdout.splitlines()) != 1:
        raise ValueError("Native apparent-byte output is ambiguous")
    units = int(raw_stdout.split(None, 1)[0])
    upper = units * 512
    lower = max(0, upper - 511)
    if (
        receipt.get("reported_512_byte_units") != units
        or receipt.get("apparent_byte_upper_bound") != upper
        or receipt.get("apparent_byte_lower_bound") != lower
    ):
        raise ValueError("Native apparent-byte receipt differs from raw stdout")
    if upper + OUTPUT_RESERVE_BYTES < CAP_BYTES:
        status = "observed_below_cap_non_atomic"
    elif lower >= CAP_BYTES:
        status = "at_or_above_cap_non_atomic"
    else:
        status = "indeterminate_boundary_rounding"
    if receipt.get("status") != status.removesuffix("_non_atomic"):
        raise ValueError("Native receipt cap classification differs")
    report["native_cap_check"] = {
        "receipt_path": native_receipt.relative_to(repository).as_posix(),
        "receipt_sha256": _sha(native_receipt),
        "status": status,
        "apparent_byte_lower_bound": lower,
        "apparent_byte_upper_bound": upper,
        "remaining_to_threshold_lower_bound": CAP_BYTES - upper,
        "traversal_is_atomic_snapshot": False,
        "concurrent_artifact_writes_observed": concurrent_artifact_writes_observed,
    }
    references = report["reference_scan"]["references"]
    for proof in report["selected_proofs"]:
        origins = {
            origin
            for cited, cited_origins in references.items()
            if proof["path"] == cited
            or proof["path"].startswith(cited.rstrip("/") + "/")
            for origin in cited_origins
            if "artifact_custody/inventory.py" not in origin
        }
        proof["independent_reference_origins"] = sorted(origins)
        proof["retention_classification"] = "protected_source_or_unique_evidence"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-entries", type=int, default=2_000_000)
    parser.add_argument("--max-seconds", type=float, default=180)
    args = parser.parse_args()
    if args.max_entries <= 0 or args.max_seconds <= 0:
        parser.error("scan limits must be positive")
    report = build_inventory(
        args.repository,
        args.output,
        max_entries=args.max_entries,
        max_seconds=args.max_seconds,
    )
    print(
        json.dumps(
            {
                "cap_status": report["cap_decision"]["status"],
                "artifact_apparent_bytes": report["artifact_scan"]["bytes"][
                    "apparent_bytes"
                ],
                "entries": report["artifact_scan"]["bytes"]["entries"],
                "reference_paths": len(report["reference_scan"]["references"]),
                "delete_anything": False,
            },
            sort_keys=True,
        )
    )
    return 0 if report["artifact_scan"]["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
