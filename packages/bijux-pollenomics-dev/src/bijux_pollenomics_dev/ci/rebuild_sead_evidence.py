"""Prove governed SEAD evidence is a stable, offline, byte-exact fixed point."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import time
from typing import Final, cast
from xml.sax.saxutils import escape

from bijux_pollenomics_dev.trusted_process import run_text

JsonObject = dict[str, object]

_GOVERNED_RUN_ID: Final = "sead-full-evidence-39bfff6a-ce80714e"
_MANIFEST_NAME: Final = "evidence_materialization_manifest.json"
_EXPECTED_FILE_COUNT: Final = 54
_GENERATOR_MODULE: Final = "bijux_pollenomics.collection.sources.sead.evidence.rebuild"
_INPUT_GROUPS: Final[dict[str, tuple[str, ...]]] = {
    "configuration": (
        "Makefile",
        "makes/pollenomics-verification.mk",
        "pyproject.toml",
        "packages/bijux-pollenomics/pyproject.toml",
        "packages/bijux-pollenomics-dev/pyproject.toml",
        "uv.lock",
    ),
    "data": (
        "data/boundaries",
        f"data/sead/raw/acquisitions/{_GOVERNED_RUN_ID}",
    ),
    "producer": (
        "packages/bijux-pollenomics/src/bijux_pollenomics",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev",
    ),
    "tracked_evidence": (f"data/sead/normalized/acquisitions/{_GOVERNED_RUN_ID}",),
}


class ReproducibleSeadEvidenceError(RuntimeError):
    """Raised when the fixed-point invocation is unsafe or incomplete."""


@dataclass(frozen=True)
class InventoryEntry:
    """Content identity for one regular file."""

    path: str
    byte_count: int
    sha256: str

    def as_json(self) -> JsonObject:
        """Return the canonical evidence representation."""
        return {
            "path": self.path,
            "byte_count": self.byte_count,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class CommandResult:
    """Captured result from one isolated generator process."""

    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class GitIdentity:
    """Commit, tree, and relevant-path state for one checkpoint."""

    commit: str
    tree: str
    dirty_paths: tuple[str, ...]

    def as_json(self) -> JsonObject:
        """Return the canonical evidence representation."""
        return {
            "commit": self.commit,
            "tree": self.tree,
            "dirty_paths": list(self.dirty_paths),
        }


Runner = Callable[[Sequence[str], Path], CommandResult]
GitIdentityReader = Callable[[Path, Sequence[str]], GitIdentity]


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256_file(path: Path) -> tuple[int, str]:
    before = path.stat()
    digest = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            byte_count += len(chunk)
            digest.update(chunk)
    after = path.stat()
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if before_identity != after_identity or byte_count != after.st_size:
        raise ReproducibleSeadEvidenceError(f"file changed while hashing: {path}")
    return byte_count, digest.hexdigest()


def _reject_symlink_ancestors(path: Path) -> None:
    for candidate in (path, *path.parents):
        if candidate.exists() and candidate.is_symlink():
            raise ReproducibleSeadEvidenceError(
                f"fixed-point path traverses a symlink: {candidate}"
            )


def _validated_repository_root(path: Path) -> Path:
    root = Path(path)
    if not root.is_absolute() or root == Path(root.anchor):
        raise ReproducibleSeadEvidenceError(
            "repository root must be a safe absolute path"
        )
    _reject_symlink_ancestors(root)
    if root.is_symlink() or not root.is_dir():
        raise ReproducibleSeadEvidenceError(
            "repository root must be a regular directory"
        )
    return root.resolve()


def _validated_evidence_root(path: Path, *, repository_root: Path) -> Path:
    evidence = Path(path)
    if not evidence.is_absolute() or evidence == Path(evidence.anchor):
        raise ReproducibleSeadEvidenceError(
            "evidence root must be a safe absolute path"
        )
    _reject_symlink_ancestors(evidence.parent)
    artifacts = (repository_root / "artifacts").resolve()
    resolved_parent = evidence.parent.resolve()
    try:
        resolved_parent.relative_to(artifacts)
    except ValueError as error:
        raise ReproducibleSeadEvidenceError(
            "evidence root must be below repository artifacts"
        ) from error
    if evidence.exists() or evidence.is_symlink():
        raise ReproducibleSeadEvidenceError(f"evidence root already exists: {evidence}")
    return resolved_parent / evidence.name


def _runtime_cache_member(path: Path) -> bool:
    return "__pycache__" in path.parts or path.suffix == ".pyc"


def _inventory_path(
    path: Path,
    *,
    prefix: str,
    ignore_runtime_cache: bool,
) -> tuple[InventoryEntry, ...]:
    if path.is_symlink():
        raise ReproducibleSeadEvidenceError(f"input is a symlink: {prefix}")
    if path.is_file():
        byte_count, digest = _sha256_file(path)
        return (InventoryEntry(prefix, byte_count, digest),)
    if not path.is_dir():
        raise ReproducibleSeadEvidenceError(f"required input is missing: {prefix}")
    entries: list[InventoryEntry] = []
    for directory, directory_names, file_names in os.walk(path, followlinks=False):
        directory_path = Path(directory)
        directory_names[:] = sorted(
            name
            for name in directory_names
            if not ignore_runtime_cache or name != "__pycache__"
        )
        for name in directory_names:
            child = directory_path / name
            if child.is_symlink():
                relative = (Path(prefix) / child.relative_to(path)).as_posix()
                raise ReproducibleSeadEvidenceError(f"input is a symlink: {relative}")
        for name in sorted(file_names):
            child = directory_path / name
            if ignore_runtime_cache and _runtime_cache_member(child):
                continue
            relative = (Path(prefix) / child.relative_to(path)).as_posix()
            mode = child.lstat().st_mode
            if not stat.S_ISREG(mode):
                raise ReproducibleSeadEvidenceError(
                    f"input is not a regular file: {relative}"
                )
            byte_count, digest = _sha256_file(child)
            entries.append(InventoryEntry(relative, byte_count, digest))
    return tuple(sorted(entries, key=lambda entry: entry.path))


def inventory_input_groups(
    repository_root: Path,
    groups: Mapping[str, Sequence[str]],
) -> dict[str, tuple[InventoryEntry, ...]]:
    """Inventory every configured input group in deterministic path order."""
    result: dict[str, tuple[InventoryEntry, ...]] = {}
    for group_name in sorted(groups):
        entries: list[InventoryEntry] = []
        for relative in sorted(groups[group_name]):
            candidate = Path(relative)
            if (
                candidate.is_absolute()
                or not candidate.parts
                or ".." in candidate.parts
            ):
                raise ReproducibleSeadEvidenceError(
                    f"unsafe input path in {group_name}: {relative}"
                )
            entries.extend(
                _inventory_path(
                    repository_root / candidate,
                    prefix=candidate.as_posix(),
                    ignore_runtime_cache=True,
                )
            )
        paths = [entry.path for entry in entries]
        if len(paths) != len(set(paths)):
            raise ReproducibleSeadEvidenceError(
                f"overlapping input paths in group: {group_name}"
            )
        result[group_name] = tuple(sorted(entries, key=lambda entry: entry.path))
    return result


def _group_digests(
    inventories: Mapping[str, Sequence[InventoryEntry]],
) -> dict[str, str]:
    return {
        name: hashlib.sha256(
            _canonical_bytes([entry.as_json() for entry in inventories[name]])
        ).hexdigest()
        for name in sorted(inventories)
    }


def _combined_input_digest(group_digests: Mapping[str, str]) -> str:
    return hashlib.sha256(
        _canonical_bytes(dict(sorted(group_digests.items())))
    ).hexdigest()


def inventory_bundle(root: Path) -> tuple[InventoryEntry, ...]:
    """Inventory a candidate or tracked evidence tree without ignoring files."""
    if root.is_symlink() or not root.is_dir():
        raise ReproducibleSeadEvidenceError(
            f"evidence bundle is missing or unsafe: {root}"
        )
    entries = _inventory_path(root, prefix="", ignore_runtime_cache=False)
    normalized = tuple(
        InventoryEntry(entry.path.removeprefix("/"), entry.byte_count, entry.sha256)
        for entry in entries
    )
    if any(not entry.path for entry in normalized):
        raise ReproducibleSeadEvidenceError("evidence bundle contains an empty path")
    return normalized


def compare_inventories(
    left: Sequence[InventoryEntry],
    right: Sequence[InventoryEntry],
    *,
    comparison: str,
) -> list[JsonObject]:
    """Return deterministic exact path, size, and digest differences."""
    left_by_path = {entry.path: entry for entry in left}
    right_by_path = {entry.path: entry for entry in right}
    differences: list[JsonObject] = []
    for path in sorted(set(left_by_path) | set(right_by_path)):
        left_entry = left_by_path.get(path)
        right_entry = right_by_path.get(path)
        if left_entry is None:
            differences.append(
                {"comparison": comparison, "kind": "additional", "path": path}
            )
            continue
        if right_entry is None:
            differences.append(
                {"comparison": comparison, "kind": "missing", "path": path}
            )
            continue
        if left_entry.byte_count != right_entry.byte_count:
            differences.append(
                {
                    "comparison": comparison,
                    "kind": "byte_count_mismatch",
                    "path": path,
                    "left": left_entry.byte_count,
                    "right": right_entry.byte_count,
                }
            )
        if left_entry.sha256 != right_entry.sha256:
            differences.append(
                {
                    "comparison": comparison,
                    "kind": "sha256_mismatch",
                    "path": path,
                    "left": left_entry.sha256,
                    "right": right_entry.sha256,
                }
            )
    return differences


def _run_generator(command: Sequence[str], cwd: Path) -> CommandResult:
    completed = run_text(command, cwd=cwd, check=False, capture_output=True)
    return CommandResult(
        completed.returncode,
        completed.stdout or "",
        completed.stderr or "",
    )


def _read_git_identity(
    repository_root: Path, input_paths: Sequence[str]
) -> GitIdentity:
    git = shutil.which("git")
    if git is None:
        raise ReproducibleSeadEvidenceError("git is required for input identity")

    def invoke(arguments: Sequence[str]) -> str:
        completed = run_text(
            [git, *arguments], cwd=repository_root, check=False, capture_output=True
        )
        if completed.returncode != 0:
            raise ReproducibleSeadEvidenceError(
                f"git identity command failed: {' '.join(arguments)}"
            )
        return (completed.stdout or "").strip()

    top_level = Path(invoke(("rev-parse", "--show-toplevel"))).resolve()
    if top_level != repository_root:
        raise ReproducibleSeadEvidenceError(
            "repository root is not the Git worktree root"
        )
    commit = invoke(("rev-parse", "HEAD"))
    tree = invoke(("rev-parse", "HEAD^{tree}"))
    dirty = invoke(
        (
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *input_paths,
        )
    )
    return GitIdentity(
        commit=commit,
        tree=tree,
        dirty_paths=tuple(line for line in dirty.splitlines() if line),
    )


def _generator_command(
    *,
    repository_root: Path,
    output_root: Path,
    pycache_root: Path,
) -> tuple[str, ...]:
    return (
        sys.executable,
        "-I",
        "-B",
        "-X",
        f"pycache_prefix={pycache_root}",
        "-m",
        _GENERATOR_MODULE,
        "--repository-root",
        str(repository_root),
        "--output-root",
        str(output_root),
    )


def _parse_generator_summary(result: CommandResult, label: str) -> JsonObject:
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise ReproducibleSeadEvidenceError(
            f"{label} generator must emit exactly one JSON line"
        )
    try:
        payload = json.loads(lines[0])
    except json.JSONDecodeError as error:
        raise ReproducibleSeadEvidenceError(
            f"{label} generator summary is not JSON"
        ) from error
    if not isinstance(payload, dict) or not all(
        isinstance(key, str) for key in payload
    ):
        raise ReproducibleSeadEvidenceError(
            f"{label} generator summary must be an object"
        )
    return cast(JsonObject, payload)


def _load_tracked_manifest(path: Path) -> JsonObject:
    if path.is_symlink() or not path.is_file():
        raise ReproducibleSeadEvidenceError("tracked evidence manifest is unsafe")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReproducibleSeadEvidenceError(
            "tracked evidence manifest is invalid"
        ) from error
    if not isinstance(payload, dict):
        raise ReproducibleSeadEvidenceError(
            "tracked evidence manifest must be an object"
        )
    return cast(JsonObject, payload)


def _validate_generator_summary(
    summary: Mapping[str, object],
    *,
    tracked_manifest: Mapping[str, object],
    tracked_manifest_sha256: str,
    output_root: Path,
) -> None:
    expected = {
        "schema_version": "sead-governed-evidence-rebuild.v1",
        "status": "PASS",
        "source_run_id": tracked_manifest.get("source_run_id"),
        "build_id": tracked_manifest.get("build_id"),
        "acquisition_manifest_sha256": tracked_manifest.get(
            "acquisition_manifest_sha256"
        ),
        "evidence_manifest_sha256": tracked_manifest_sha256,
        "file_count": _EXPECTED_FILE_COUNT,
        "network_policy": "forbidden",
        "output_root": str(output_root),
    }
    for field, expected_value in expected.items():
        if summary.get(field) != expected_value:
            raise ReproducibleSeadEvidenceError(
                f"generator summary {field} does not match governed identity"
            )


def _write_text(path: Path, content: str) -> None:
    staging = path.with_name(f".{path.name}.staging-{os.getpid()}")
    staging.write_text(content, encoding="utf-8")
    os.replace(staging, path)


def _write_json(path: Path, payload: object) -> None:
    staging = path.with_name(f".{path.name}.staging-{os.getpid()}")
    staging.write_bytes(_canonical_bytes(payload))
    os.replace(staging, path)


def _write_run_evidence(evidence_root: Path, report: JsonObject) -> None:
    _write_json(evidence_root / "evidence.json", report)
    differences = cast(list[JsonObject], report.get("differences", []))
    diff_text = (
        "PASS\n"
        if not differences
        else "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in differences
        )
    )
    _write_text(evidence_root / "diff.txt", diff_text)
    status = str(report.get("status", "FAIL"))
    failure = "" if status == "PASS" else '<failure message="fixed-point mismatch"/>'
    junit = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuite name="sead-evidence-fixed-point" tests="1" failures="{int(status != "PASS")}">\n'
        f'  <testcase classname="sead.evidence" name="fixed_point">{failure}</testcase>\n'
        f"  <system-out>{escape(diff_text)}</system-out>\n"
        "</testsuite>\n"
    )
    _write_text(evidence_root / "results.junit.xml", junit)


def _remove_proven_candidates(candidates_root: Path, *, evidence_root: Path) -> None:
    if candidates_root.parent != evidence_root or candidates_root.name != "candidates":
        raise ReproducibleSeadEvidenceError("candidate cleanup target is unsafe")
    if candidates_root.is_symlink():
        raise ReproducibleSeadEvidenceError("candidate cleanup target is a symlink")
    if candidates_root.exists():
        shutil.rmtree(candidates_root)


def verify_governed_sead_evidence_fixed_point(
    *,
    repository_root: Path,
    evidence_root: Path,
    runner: Runner = _run_generator,
    git_identity_reader: GitIdentityReader = _read_git_identity,
    input_groups: Mapping[str, Sequence[str]] = _INPUT_GROUPS,
) -> JsonObject:
    """Build twice and prove replay and tracked evidence are byte-identical."""
    started_at = datetime.now(UTC)
    started_clock = time.monotonic()
    root = _validated_repository_root(repository_root)
    evidence = _validated_evidence_root(evidence_root, repository_root=root)
    evidence.mkdir()
    logs_root = evidence / "logs"
    logs_root.mkdir()
    candidates_root = evidence / "candidates"
    candidates_root.mkdir()
    all_input_paths = tuple(
        sorted({path for paths in input_groups.values() for path in paths})
    )
    differences: list[JsonObject] = []
    commands: list[list[str]] = []
    summaries: dict[str, JsonObject] = {}
    bundle_inventories: dict[str, tuple[InventoryEntry, ...]] = {}
    before_groups: dict[str, tuple[InventoryEntry, ...]] = {}
    after_groups: dict[str, tuple[InventoryEntry, ...]] = {}
    before_git: GitIdentity | None = None
    after_git: GitIdentity | None = None
    tracked_manifest: JsonObject = {}
    tracked_manifest_sha256 = ""
    execution_error: str | None = None

    try:
        before_git = git_identity_reader(root, all_input_paths)
        if before_git.dirty_paths:
            differences.append(
                {
                    "comparison": "input_checkpoint",
                    "kind": "relevant_input_not_committed",
                    "paths": list(before_git.dirty_paths),
                }
            )
            raise ReproducibleSeadEvidenceError(
                "governed inputs must be committed before fixed-point verification"
            )
        before_groups = inventory_input_groups(root, input_groups)
        tracked_root = (
            root / "data" / "sead" / "normalized" / "acquisitions" / _GOVERNED_RUN_ID
        )
        tracked_manifest_path = tracked_root / _MANIFEST_NAME
        tracked_manifest = _load_tracked_manifest(tracked_manifest_path)
        _, tracked_manifest_sha256 = _sha256_file(tracked_manifest_path)
        bundle_inventories["tracked"] = inventory_bundle(tracked_root)
        if len(bundle_inventories["tracked"]) != _EXPECTED_FILE_COUNT:
            differences.append(
                {
                    "comparison": "tracked",
                    "kind": "file_count_mismatch",
                    "expected": _EXPECTED_FILE_COUNT,
                    "observed": len(bundle_inventories["tracked"]),
                }
            )

        for label in ("reference", "replay"):
            output = candidates_root / label
            command = _generator_command(
                repository_root=root,
                output_root=output,
                pycache_root=evidence / "pycache" / label,
            )
            commands.append(list(command))
            try:
                result = runner(command, root)
            except Exception as error:
                _write_text(logs_root / f"{label}.stdout.log", "")
                _write_text(logs_root / f"{label}.stderr.log", f"{error}\n")
                differences.append(
                    {
                        "comparison": label,
                        "kind": "generator_execution_error",
                        "message": str(error),
                    }
                )
                raise ReproducibleSeadEvidenceError(
                    f"{label} generator could not execute"
                ) from error
            _write_text(logs_root / f"{label}.stdout.log", result.stdout)
            _write_text(logs_root / f"{label}.stderr.log", result.stderr)
            if result.returncode != 0:
                differences.append(
                    {
                        "comparison": label,
                        "kind": "generator_failed",
                        "returncode": result.returncode,
                    }
                )
                raise ReproducibleSeadEvidenceError(
                    f"{label} generator exited {result.returncode}"
                )
            summary = _parse_generator_summary(result, label)
            _validate_generator_summary(
                summary,
                tracked_manifest=tracked_manifest,
                tracked_manifest_sha256=tracked_manifest_sha256,
                output_root=output,
            )
            summaries[label] = summary
            bundle_inventories[label] = inventory_bundle(output)
            if len(bundle_inventories[label]) != _EXPECTED_FILE_COUNT:
                differences.append(
                    {
                        "comparison": label,
                        "kind": "file_count_mismatch",
                        "expected": _EXPECTED_FILE_COUNT,
                        "observed": len(bundle_inventories[label]),
                    }
                )

        differences.extend(
            compare_inventories(
                bundle_inventories["reference"],
                bundle_inventories["replay"],
                comparison="reference_vs_replay",
            )
        )
        differences.extend(
            compare_inventories(
                bundle_inventories["tracked"],
                bundle_inventories["reference"],
                comparison="tracked_vs_reference",
            )
        )
    except (OSError, ReproducibleSeadEvidenceError, TypeError, ValueError) as error:
        execution_error = str(error)
        if not differences:
            differences.append(
                {
                    "comparison": "execution",
                    "kind": "execution_error",
                    "message": execution_error,
                }
            )
    finally:
        try:
            after_groups = inventory_input_groups(root, input_groups)
            after_git = git_identity_reader(root, all_input_paths)
        except (OSError, ReproducibleSeadEvidenceError, TypeError, ValueError) as error:
            differences.append(
                {
                    "comparison": "input_checkpoint",
                    "kind": "final_inventory_failed",
                    "message": str(error),
                }
            )

    before_digests = _group_digests(before_groups) if before_groups else {}
    after_digests = _group_digests(after_groups) if after_groups else {}
    if before_digests and before_digests != after_digests:
        for group in sorted(set(before_digests) | set(after_digests)):
            if before_digests.get(group) != after_digests.get(group):
                differences.append(
                    {
                        "comparison": "input_checkpoint",
                        "kind": "input_changed_during_build",
                        "group": group,
                        "before": before_digests.get(group),
                        "after": after_digests.get(group),
                    }
                )
    if before_git is not None and after_git is not None:
        if before_git.commit != after_git.commit or before_git.tree != after_git.tree:
            differences.append(
                {
                    "comparison": "input_checkpoint",
                    "kind": "git_identity_changed_during_build",
                    "before": before_git.as_json(),
                    "after": after_git.as_json(),
                }
            )
        if after_git.dirty_paths:
            differences.append(
                {
                    "comparison": "input_checkpoint",
                    "kind": "relevant_input_dirty_after_build",
                    "paths": list(after_git.dirty_paths),
                }
            )

    differences.sort(
        key=lambda row: (
            str(row.get("comparison", "")),
            str(row.get("path", row.get("group", ""))),
            str(row.get("kind", "")),
        )
    )
    status = "PASS" if not differences else "FAIL"
    candidate_retention = "retained_for_failure"
    if status == "PASS":
        try:
            _remove_proven_candidates(candidates_root, evidence_root=evidence)
            candidate_retention = "deleted_after_complete_proof"
        except (OSError, ReproducibleSeadEvidenceError) as error:
            status = "FAIL"
            candidate_retention = "cleanup_failed"
            differences.append(
                {
                    "comparison": "candidate_cleanup",
                    "kind": "cleanup_failed",
                    "message": str(error),
                }
            )

    differences.sort(
        key=lambda row: (
            str(row.get("comparison", "")),
            str(row.get("path", row.get("group", ""))),
            str(row.get("kind", "")),
        )
    )

    ended_at = datetime.now(UTC)
    report: JsonObject = {
        "schema_version": "sead-evidence-fixed-point-proof.v1",
        "status": status,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "duration_seconds": round(time.monotonic() - started_clock, 6),
        "repository_root": str(root),
        "evidence_root": str(evidence),
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "executable_sha256": _sha256_file(Path(sys.executable).resolve())[1],
        },
        "generator_module": _GENERATOR_MODULE,
        "network_policy": "forbidden_in_generator_process",
        "expected_file_count": _EXPECTED_FILE_COUNT,
        "candidate_retention": candidate_retention,
        "commands": commands,
        "git_identity": {
            "before": before_git.as_json() if before_git else None,
            "after": after_git.as_json() if after_git else None,
        },
        "input_identity": {
            "before": before_digests,
            "after": after_digests,
            "combined_before": _combined_input_digest(before_digests)
            if before_digests
            else None,
            "combined_after": _combined_input_digest(after_digests)
            if after_digests
            else None,
        },
        "input_inventories": {
            checkpoint: {
                group: [entry.as_json() for entry in inventories[group]]
                for group in sorted(inventories)
            }
            for checkpoint, inventories in (
                ("before", before_groups),
                ("after", after_groups),
            )
        },
        "tracked_manifest": tracked_manifest,
        "tracked_manifest_sha256": tracked_manifest_sha256 or None,
        "generator_summaries": dict(sorted(summaries.items())),
        "bundle_inventories": {
            label: [entry.as_json() for entry in bundle_inventories[label]]
            for label in sorted(bundle_inventories)
        },
        "differences": differences,
        "execution_error": execution_error,
    }
    _write_run_evidence(evidence, report)
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prove governed SEAD evidence is an offline byte-exact fixed point."
    )
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the governed SEAD evidence fixed-point verifier."""
    args = _parser().parse_args(argv)
    try:
        report = verify_governed_sead_evidence_fixed_point(
            repository_root=args.repo_root,
            evidence_root=args.evidence_root,
        )
    except ReproducibleSeadEvidenceError as error:
        print(f"SEAD evidence fixed-point invocation failed: {error}", flush=True)
        return 2
    print(f"{report['status']}: {args.evidence_root}", flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
