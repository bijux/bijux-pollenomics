"""Prove that the tracked report tree is reproducible from governed inputs."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import time
from typing import cast

from bijux_pollenomics_dev.trusted_process import run_text

JsonObject = dict[str, object]


class ReproducibleReportError(RuntimeError):
    """Raised when policy, inputs, or report outputs are unsafe or invalid."""


@dataclass(frozen=True)
class CommandResult:
    """Captured result of one report generator invocation."""

    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class InventoryEntry:
    """One content-bound file or governed input symlink."""

    path: str
    kind: str
    size: int
    sha256: str
    canonical_sha256: str
    symlink_target: str | None = None

    def as_json(self) -> JsonObject:
        """Return the stable evidence representation."""
        value: JsonObject = {
            "path": self.path,
            "kind": self.kind,
            "size": self.size,
            "sha256": self.sha256,
            "canonical_sha256": self.canonical_sha256,
        }
        if self.symlink_target is not None:
            value["symlink_target"] = self.symlink_target
        return value


Runner = Callable[[Sequence[str], Path], CommandResult]


def _sha256(payload: bytes) -> str:
    """Return the lowercase SHA-256 digest of a byte payload."""
    return hashlib.sha256(payload).hexdigest()


def _mapping(value: object, label: str) -> JsonObject:
    """Return a string-keyed JSON object or reject the labeled value."""
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ReproducibleReportError(f"{label} must be an object")
    return cast(JsonObject, value)


def _string_list(value: object, label: str) -> tuple[str, ...]:
    """Return a unique tuple of non-empty strings from a policy field."""
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ReproducibleReportError(f"{label} must be a non-empty string list")
    items = cast(list[str], value)
    if len(items) != len(set(items)):
        raise ReproducibleReportError(f"{label} must be unique")
    return tuple(items)


def load_policy(path: Path) -> JsonObject:
    """Load and structurally validate the repository-owned policy."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReproducibleReportError(f"cannot load policy: {path}") from error
    policy = _mapping(value, "policy")
    expected = {
        "schema_version",
        "generator",
        "input_paths",
        "allowed_input_symlinks",
        "excluded_input_globs",
        "require_clean_repository",
        "tracked_report_root",
        "volatile_text_rules",
    }
    if set(policy) != expected:
        raise ReproducibleReportError("policy fields are not exact")
    if policy["schema_version"] != "reproducible-report-build-policy.v1":
        raise ReproducibleReportError("unsupported policy schema_version")
    _string_list(policy["input_paths"], "input_paths")
    _mapping(policy["allowed_input_symlinks"], "allowed_input_symlinks")
    _string_list(policy["excluded_input_globs"], "excluded_input_globs")
    if not isinstance(policy["require_clean_repository"], bool):
        raise ReproducibleReportError("require_clean_repository must be boolean")
    generator = _mapping(policy["generator"], "generator")
    if set(generator) != {"module", "arguments"} or not isinstance(
        generator["module"], str
    ):
        raise ReproducibleReportError("generator policy is invalid")
    _string_list(generator["arguments"], "generator.arguments")
    if not isinstance(policy["tracked_report_root"], str):
        raise ReproducibleReportError("tracked_report_root must be a string")
    rules = policy["volatile_text_rules"]
    if not isinstance(rules, list):
        raise ReproducibleReportError("volatile_text_rules must be a list")
    for raw_rule in rules:
        rule = _mapping(raw_rule, "volatile rule")
        if set(rule) != {"id", "path_globs", "pattern", "replacement"}:
            raise ReproducibleReportError("volatile rule fields are not exact")
        if not all(
            isinstance(rule[key], str) for key in ("id", "pattern", "replacement")
        ):
            raise ReproducibleReportError("volatile rule strings are invalid")
        _string_list(rule["path_globs"], "volatile rule path_globs")
        try:
            re.compile(cast(str, rule["pattern"]))
        except re.error as error:
            raise ReproducibleReportError("volatile rule regex is invalid") from error
    return policy


def _safe_relative_path(value: str, label: str) -> Path:
    """Return a path confined to the repository-relative namespace."""
    path = Path(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ReproducibleReportError(f"{label} is not a safe relative path: {value}")
    return path


def _canonical_bytes(path: str, payload: bytes, policy: JsonObject) -> bytes:
    """Normalize only policy-declared volatile text before comparison."""
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return payload
    for raw_rule in cast(list[object], policy["volatile_text_rules"]):
        rule = _mapping(raw_rule, "volatile rule")
        globs = _string_list(rule["path_globs"], "volatile rule path_globs")
        if any(_matches_glob(path, pattern) for pattern in globs):
            text = re.sub(
                cast(str, rule["pattern"]), cast(str, rule["replacement"]), text
            )
    return text.encode("utf-8")


def _matches_glob(path: str, pattern: str) -> bool:
    """Match a POSIX path while supporting leading recursive globs."""
    candidate = PurePosixPath(path)
    return candidate.match(pattern) or (
        pattern.startswith("**/") and candidate.match(pattern.removeprefix("**/"))
    )


def _regular_entry(path: Path, relative: str, policy: JsonObject) -> InventoryEntry:
    """Content-bind one regular file as an inventory entry."""
    mode = path.lstat().st_mode
    if not stat.S_ISREG(mode):
        raise ReproducibleReportError(f"inventory member is not regular: {relative}")
    payload = path.read_bytes()
    return InventoryEntry(
        path=relative,
        kind="file",
        size=len(payload),
        sha256=_sha256(payload),
        canonical_sha256=_sha256(_canonical_bytes(relative, payload, policy)),
    )


def _inventory_tree(
    root: Path,
    *,
    prefix: str,
    policy: JsonObject,
    allowed_symlinks: Mapping[str, str],
    exclude_inputs: bool,
) -> tuple[InventoryEntry, ...]:
    """Inventory a tree deterministically without following symlinks."""
    entries: list[InventoryEntry] = []
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        directory_names.sort()
        file_names.sort()
        for name in tuple(directory_names):
            child = directory_path / name
            relative = (Path(prefix) / child.relative_to(root)).as_posix()
            if exclude_inputs and _input_is_excluded(relative, policy):
                directory_names.remove(name)
                continue
            if child.is_symlink():
                directory_names.remove(name)
                entries.append(_symlink_entry(child, relative, allowed_symlinks))
        for name in file_names:
            child = directory_path / name
            relative = (Path(prefix) / child.relative_to(root)).as_posix()
            if exclude_inputs and _input_is_excluded(relative, policy):
                continue
            if child.is_symlink():
                entries.append(_symlink_entry(child, relative, allowed_symlinks))
            else:
                entries.append(_regular_entry(child, relative, policy))
    return tuple(entries)


def _input_is_excluded(path: str, policy: JsonObject) -> bool:
    """Return whether policy explicitly excludes an input inventory path."""
    return any(
        _matches_glob(path, pattern)
        for pattern in _string_list(
            policy["excluded_input_globs"], "excluded_input_globs"
        )
    )


def _symlink_entry(
    path: Path, relative: str, allowed_symlinks: Mapping[str, str]
) -> InventoryEntry:
    """Content-bind an explicitly allowlisted input symlink."""
    target = os.readlink(path)
    if allowed_symlinks.get(relative) != target:
        raise ReproducibleReportError(f"unapproved input symlink: {relative}")
    payload = target.encode("utf-8")
    return InventoryEntry(
        path=relative,
        kind="symlink",
        size=len(payload),
        sha256=_sha256(payload),
        canonical_sha256=_sha256(payload),
        symlink_target=target,
    )


def inventory_inputs(repo_root: Path, policy: JsonObject) -> tuple[InventoryEntry, ...]:
    """Inventory every policy-owned input without following symlinks."""
    allowed_raw = _mapping(policy["allowed_input_symlinks"], "allowed_input_symlinks")
    if not all(isinstance(value, str) for value in allowed_raw.values()):
        raise ReproducibleReportError("allowed symlink targets must be strings")
    allowed = cast(dict[str, str], allowed_raw)
    entries: list[InventoryEntry] = []
    for configured in _string_list(policy["input_paths"], "input_paths"):
        relative_path = _safe_relative_path(configured, "input path")
        absolute = repo_root / relative_path
        if absolute.is_symlink():
            entries.append(_symlink_entry(absolute, relative_path.as_posix(), allowed))
        elif absolute.is_dir():
            entries.extend(
                _inventory_tree(
                    absolute,
                    prefix=relative_path.as_posix(),
                    policy=policy,
                    allowed_symlinks=allowed,
                    exclude_inputs=True,
                )
            )
        elif absolute.is_file():
            entries.append(_regular_entry(absolute, relative_path.as_posix(), policy))
        else:
            raise ReproducibleReportError(f"configured input is missing: {configured}")
    paths = [entry.path for entry in entries]
    if len(paths) != len(set(paths)):
        raise ReproducibleReportError("configured input inventory overlaps")
    return tuple(sorted(entries, key=lambda entry: entry.path))


def inventory_reports(root: Path, policy: JsonObject) -> tuple[InventoryEntry, ...]:
    """Inventory a report tree and reject links or non-regular members."""
    if root.is_symlink() or not root.is_dir():
        raise ReproducibleReportError(f"report root is not a regular directory: {root}")
    return _inventory_tree(
        root,
        prefix="",
        policy=policy,
        allowed_symlinks={},
        exclude_inputs=False,
    )


def _compare(
    expected: Sequence[InventoryEntry],
    observed: Sequence[InventoryEntry],
    *,
    canonical: bool,
) -> list[JsonObject]:
    """Return path and content differences between two inventories."""
    expected_by_path = {entry.path: entry for entry in expected}
    observed_by_path = {entry.path: entry for entry in observed}
    differences: list[JsonObject] = []
    for path in sorted(expected_by_path.keys() | observed_by_path.keys()):
        left = expected_by_path.get(path)
        right = observed_by_path.get(path)
        if left is None or right is None:
            differences.append(
                {"path": path, "kind": "additional" if left is None else "missing"}
            )
            continue
        left_digest = left.canonical_sha256 if canonical else left.sha256
        right_digest = right.canonical_sha256 if canonical else right.sha256
        if left.kind != right.kind or left_digest != right_digest:
            differences.append(
                {
                    "path": path,
                    "kind": "content",
                    "expected_sha256": left_digest,
                    "observed_sha256": right_digest,
                }
            )
    return differences


def _default_runner(command: Sequence[str], cwd: Path) -> CommandResult:
    """Run one generator command and capture its complete text result."""
    completed = run_text(command, cwd=cwd, check=False, capture_output=True)
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _repository_identity(repo_root: Path, *, required: bool) -> JsonObject:
    """Bind evidence to a clean Git commit and tree when policy requires it."""
    if not required:
        return {"mode": "fixture"}
    git = shutil.which("git")
    if git is None:
        raise ReproducibleReportError("Git is required to bind repository identity")

    def run(*arguments: str) -> str:
        """Run a repository identity probe and return its standard output."""
        completed = run_text(
            (git, "-C", str(repo_root), *arguments),
            check=False,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise ReproducibleReportError(
                f"Git repository identity probe failed: {arguments[0]}"
            )
        return completed.stdout

    top_level = Path(run("rev-parse", "--show-toplevel").strip()).resolve()
    if top_level != repo_root:
        raise ReproducibleReportError("repository root is not the Git worktree root")
    status = run("status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise ReproducibleReportError(
            "reproducible report verification requires a clean repository"
        )
    return {
        "mode": "git",
        "head_commit": run("rev-parse", "HEAD").strip(),
        "head_tree": run("rev-parse", "HEAD^{tree}").strip(),
        "status_sha256": _sha256(status.encode()),
    }


def _timing(started_at: datetime, started_monotonic: float) -> JsonObject:
    """Return UTC timestamps and monotonic elapsed duration for evidence."""
    return {
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "finished_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "duration_seconds": round(time.monotonic() - started_monotonic, 6),
    }


def _command(
    policy: JsonObject,
    repo_root: Path,
    output_root: Path,
    import_cache_root: Path,
) -> tuple[str, ...]:
    """Build an isolated generator command from the governed policy."""
    generator = _mapping(policy["generator"], "generator")
    module = cast(str, generator["module"])
    values = {"repo_root": str(repo_root), "output_root": str(output_root)}
    arguments = tuple(
        argument.format_map(values)
        for argument in _string_list(generator["arguments"], "generator.arguments")
    )
    if import_cache_root.exists() or import_cache_root.is_symlink():
        raise ReproducibleReportError(
            f"isolated import cache already exists: {import_cache_root}"
        )
    return (
        sys.executable,
        "-I",
        "-B",
        "-X",
        f"pycache_prefix={import_cache_root}",
        "-m",
        module,
        *arguments,
    )


def _atomic_write(path: Path, payload: bytes) -> None:
    """Persist evidence through an exclusive sibling staging file."""
    staging = path.with_name(f".{path.name}.writing")
    if staging.exists() or staging.is_symlink():
        raise ReproducibleReportError(f"staging output already exists: {staging}")
    with staging.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    staging.replace(path)


def _write_evidence(root: Path, report: JsonObject) -> None:
    """Write JSON, JUnit, and plain-text views of one verification report."""
    differences = cast(list[JsonObject], report["differences"])
    status = cast(str, report["status"])
    lines = [f"status: {status}", f"difference_count: {len(differences)}"]
    lines.extend(
        f"{row['comparison']}: {row['path']} ({row['kind']})" for row in differences
    )

    def escaped(value: object) -> str:
        """Escape evidence text for its XML element context."""
        return (
            str(value).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
        )

    failure = (
        ""
        if status == "PASS"
        else f'<failure message="{len(differences)} differences"/>'
    )
    junit = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuite name="reproducible-report-build" tests="1" failures="{int(status != "PASS")}">'
        f'<testcase name="two-build-and-tracked-equivalence">{failure}</testcase>'
        f"<system-out>{escaped(os.linesep.join(lines))}</system-out></testsuite>\n"
    )
    _atomic_write(
        root / "evidence.json",
        (json.dumps(report, indent=2, sort_keys=True) + "\n").encode(),
    )
    _atomic_write(root / "results.junit.xml", junit.encode())
    _atomic_write(root / "diff.txt", ("\n".join(lines) + "\n").encode())


def verify_reproducible_reports(
    *,
    repo_root: Path,
    policy_path: Path,
    evidence_root: Path,
    runner: Runner = _default_runner,
) -> JsonObject:
    """Build twice, compare exact outputs, and compare tracked canonical content."""
    started_at = datetime.now(UTC)
    started_monotonic = time.monotonic()
    repo_root = repo_root.resolve()
    policy = load_policy(policy_path)
    repository_before = _repository_identity(
        repo_root, required=cast(bool, policy["require_clean_repository"])
    )
    allowed_evidence_root = (repo_root / "artifacts").resolve()
    resolved_evidence_root = evidence_root.resolve()
    try:
        resolved_evidence_root.relative_to(allowed_evidence_root)
    except ValueError as error:
        raise ReproducibleReportError(
            "evidence root must be within the repository artifacts directory"
        ) from error
    evidence_root = resolved_evidence_root
    if evidence_root.exists() or evidence_root.is_symlink():
        raise ReproducibleReportError(f"evidence root already exists: {evidence_root}")
    evidence_root.mkdir(parents=True)
    reference_root = evidence_root / "reference-build"
    replay_root = evidence_root / "replay-build"
    import_cache_root = evidence_root / "isolated-import-cache"
    inputs_before = inventory_inputs(repo_root, policy)
    command_results: list[JsonObject] = []
    for output_root in (reference_root, replay_root):
        command = _command(policy, repo_root, output_root, import_cache_root)
        command_started = time.monotonic()
        result = runner(command, repo_root)
        command_results.append(
            {
                "command": list(command),
                "returncode": result.returncode,
                "duration_seconds": round(time.monotonic() - command_started, 6),
            }
        )
        _atomic_write(
            evidence_root / f"{output_root.name}.stdout.log", result.stdout.encode()
        )
        _atomic_write(
            evidence_root / f"{output_root.name}.stderr.log", result.stderr.encode()
        )
        if result.returncode != 0:
            failure_report: JsonObject = {
                "schema_version": "reproducible-report-build-evidence.v1",
                "status": "FAIL",
                "policy_path": policy_path.resolve().relative_to(repo_root).as_posix(),
                "policy_sha256": _sha256(policy_path.read_bytes()),
                "repository": repository_before,
                "timing": _timing(started_at, started_monotonic),
                "commands": command_results,
                "inputs": [entry.as_json() for entry in inputs_before],
                "inventories": {},
                "differences": [
                    {
                        "comparison": "generator",
                        "path": output_root.name,
                        "kind": "nonzero_exit",
                        "returncode": result.returncode,
                    }
                ],
            }
            _write_evidence(evidence_root, failure_report)
            return failure_report
    reference = inventory_reports(reference_root, policy)
    replay = inventory_reports(replay_root, policy)
    tracked_path = repo_root / _safe_relative_path(
        cast(str, policy["tracked_report_root"]), "tracked_report_root"
    )
    tracked = inventory_reports(tracked_path, policy)
    inputs_after = inventory_inputs(repo_root, policy)
    repository_after = _repository_identity(
        repo_root, required=cast(bool, policy["require_clean_repository"])
    )
    differences: list[JsonObject] = []
    if inputs_before != inputs_after:
        differences.append(
            {"comparison": "inputs", "path": "*", "kind": "changed_during_build"}
        )
    if repository_before != repository_after:
        differences.append(
            {"comparison": "repository", "path": "*", "kind": "changed_during_build"}
        )
    for row in _compare(reference, replay, canonical=False):
        differences.append({"comparison": "reference_vs_replay", **row})
    for row in _compare(tracked, reference, canonical=True):
        differences.append({"comparison": "tracked_vs_reference", **row})
    report: JsonObject = {
        "schema_version": "reproducible-report-build-evidence.v1",
        "status": "PASS" if not differences else "FAIL",
        "policy_path": policy_path.resolve().relative_to(repo_root).as_posix(),
        "policy_sha256": _sha256(policy_path.read_bytes()),
        "repository": repository_before,
        "timing": _timing(started_at, started_monotonic),
        "runtime": {
            "python": sys.version.split()[0],
            "executable": sys.executable,
            "executable_sha256": _sha256(Path(sys.executable).resolve().read_bytes()),
        },
        "commands": command_results,
        "inputs": [entry.as_json() for entry in inputs_before],
        "inventories": {
            "tracked": [entry.as_json() for entry in tracked],
            "reference": [entry.as_json() for entry in reference],
            "replay": [entry.as_json() for entry in replay],
        },
        "differences": differences,
    }
    _write_evidence(evidence_root, report)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    """Run the deterministic report-build verifier."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = verify_reproducible_reports(
            repo_root=args.repo_root,
            policy_path=args.policy,
            evidence_root=args.evidence_root,
        )
    except ReproducibleReportError as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
