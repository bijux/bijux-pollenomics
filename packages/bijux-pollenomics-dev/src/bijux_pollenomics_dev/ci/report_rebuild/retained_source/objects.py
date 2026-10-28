"""Authenticate historical source identities through exact reachable Git objects."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import select
import shutil
import subprocess
import time
from typing import IO

from ..contracts import ReportRebuildError, require_relative_path
from .canonical_paths import CANONICAL_CAPTURE_SOURCE_PATHS

MAX_MEMBERS = 8192
MAX_MEMBER_BYTES = 32 * 1024**2
MAX_TOTAL_BYTES = 256 * 1024**2
MAX_PATH_BYTES = 1024
DOC_SOURCES = frozenset(
    {
        "docs/report/pollen-reconstruction/author-buffered-pollen/replay.py",
        "configs/docs/publication/admission.py",
        "configs/docs/publication/controls.py",
        "configs/docs/publish_site_assets.py",
        "configs/docs/report_provenance.py",
        "configs/docs/science_downloads.py",
    }
)
RETAINED_METADATA_PATHS = frozenset(
    {
        "configs/ci/report-ownership.json",
        "reports/needed/field-decisions.json",
        "data/source-custody/neotoma/lakeparameters/runtime-authority/plan.json",
        "data/method-certification/source-locked-linux-r/reference-bundle/"
        "generated-sources/packages/bijux-pollenomics-lra/src/"
        "bijux_pollenomics_lra/_build_version.py",
        "pyproject.toml",
    }
)
WHOLE_SECONDS = 180


def require(value: object, reason: str) -> None:
    """Reject unverifiable retained-source custody."""
    if not value:
        raise ReportRebuildError("Retained Git source: " + reason)


def hexadecimal(value: str, width: int) -> bool:
    """Check one exact lowercase object or payload digest."""
    return (
        type(value) is str
        and len(value) == width
        and all(c in "0123456789abcdef" for c in value)
    )


@dataclass(frozen=True)
class GitSourceMember:
    """An original logical identity and its separately declared reachable storage."""

    member: str
    repository_path: str
    source_revision: str
    git_blob: str
    sha256: str
    bytes: int
    storage_role: str = "canonical_source"
    capsule_prefix: str | None = None

    def validate(self) -> None:
        """Require the declared source role, exact paths and finite body bounds."""
        for name in (self.member, self.repository_path):
            require_relative_path(name, "retained source path")
            require(
                len(name.encode()) <= MAX_PATH_BYTES
                and not any(ord(c) < 32 for c in name),
                "source path has control characters or exceeds bound",
            )
        if self.storage_role == "historical_code_witness":
            require(
                type(self.capsule_prefix) is str,
                "historical code witness requires authenticated capsule context",
            )
            assert self.capsule_prefix is not None
            require_relative_path(self.capsule_prefix, "historical witness capsule")
            require(
                (
                    self.member in {"payloads/" + self.sha256, "members/" + self.sha256}
                    or Path(self.member).suffix == ".R"
                )
                and self.repository_path == self.capsule_prefix + "/" + self.member,
                "historical witness must retain its exact capsule member path",
            )
        else:
            require(
                self.storage_role == "canonical_source" and self.capsule_prefix is None,
                "unknown or inconsistent source storage role",
            )
            require(
                self.repository_path.startswith("packages/")
                or self.repository_path in DOC_SOURCES
                or self.repository_path in RETAINED_METADATA_PATHS
                or self.repository_path in CANONICAL_CAPTURE_SOURCE_PATHS,
                "Git storage must be canonical source or exact retained metadata",
            )
        require(
            hexadecimal(self.source_revision, 40)
            and hexadecimal(self.git_blob, 40)
            and hexadecimal(self.sha256, 64),
            "exact commit/blob/SHA256 required",
        )
        require(
            type(self.bytes) is int and 0 <= self.bytes <= MAX_MEMBER_BYTES,
            "source member exceeds declared body bound",
        )


def physical(path: Path) -> None:
    """Reject raw aliases before using a declared repository or tool."""
    require(
        path.is_absolute()
        and ".." not in path.parts
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "physical normalized ancestry required",
    )


def environment() -> dict[str, str]:
    """Use the same seven-key, noninteractive Git environment as source correspondence."""
    return {
        "PATH": os.defpath,
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    }


def git_executable() -> Path:
    """Select ordinary Git portably; execution qualification owns host tool fingerprints."""
    selected = shutil.which("git")
    require(selected is not None, "Git executable unavailable")
    assert selected is not None
    executable = Path(selected).resolve(strict=True)
    physical(executable)
    require(
        executable.is_file() and os.access(executable, os.X_OK),
        "regular executable Git required",
    )
    return executable


class GitPipe:
    """Read bounded protocol bytes from one owned Git child without writing payloads."""

    def __init__(
        self,
        repository: Path,
        arguments: list[str],
        deadline: float,
        executable: Path | None = None,
    ) -> None:
        """Own one isolated Git process and its bounded protocol streams."""
        self.deadline = deadline
        self.error = bytearray()
        self.stderr_open = True
        self.process = subprocess.Popen(
            [
                str(executable or git_executable()),
                "--no-replace-objects",
                "-C",
                str(repository),
                *arguments,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment(),
        )
        assert (
            self.process.stdin is not None
            and self.process.stdout is not None
            and self.process.stderr is not None
        )
        self.stdin: IO[bytes] = self.process.stdin
        self.stdout: IO[bytes] = self.process.stdout
        self.stderr: IO[bytes] = self.process.stderr
        self.buffer = bytearray()

    def _fill(self) -> bool:
        remaining = self.deadline - time.monotonic()
        require(remaining > 0, "whole Git source read budget exhausted")
        readable, _, _ = select.select(
            [self.stdout, *([self.stderr] if self.stderr_open else [])],
            [],
            [],
            remaining,
        )
        require(bool(readable), "Git source read timed out")
        if self.stderr in readable:
            raw = os.read(self.stderr.fileno(), 4096)
            self.stderr_open = bool(raw)
            self.error.extend(raw)
            require(len(self.error) <= 8192, "Git stderr exceeded bound")
            if raw:
                raise ReportRebuildError(
                    "Retained Git source: Git reported an object error"
                )
        if self.stdout in readable:
            raw = os.read(self.stdout.fileno(), 65536)
            self.buffer.extend(raw)
            return bool(raw)
        return True

    def exact(self, size: int) -> bytes:
        """Read exactly a bounded fragment or refuse an early EOF."""
        require(
            type(size) is int and 0 <= size <= 65536, "bounded Git fragment required"
        )
        while len(self.buffer) < size:
            require(self._fill(), "truncated Git object stream")
        raw = bytes(self.buffer[:size])
        del self.buffer[:size]
        return raw

    def line(self) -> bytes:
        """Read only a short Git object header, never an arbitrary body line."""
        while b"\n" not in self.buffer:
            require(
                len(self.buffer) <= 256 and self._fill(),
                "missing or oversized Git object header",
            )
        head, _, tail = self.buffer.partition(b"\n")
        require(len(head) <= 256, "oversized Git object header")
        self.buffer = bytearray(tail)
        return bytes(head)

    def finish(self) -> None:
        """Refuse unsolicited bytes and wait for the same child within the whole budget."""
        self.stdin.close()
        require(not self.buffer, "unrequested Git stream bytes")
        while self._fill():
            require(not self.buffer, "unrequested Git stream bytes")
        status = self.process.wait(timeout=max(0.001, self.deadline - time.monotonic()))
        require(status == 0 and not self.error, "Git source query failed")

    def close(self) -> None:
        """Reap any failed reader child; never leave a source query running."""
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait()
        for stream in (self.stdin, self.stdout, self.stderr):
            stream.close()


def query(
    repository: Path,
    arguments: list[str],
    cap: int,
    deadline: float,
    executable: Path | None = None,
) -> bytes:
    """Read a small metadata query through the same bounded pipe."""
    pipe = GitPipe(repository, arguments, deadline, executable)
    try:
        pipe.stdin.close()
        result = bytearray()
        while pipe._fill():
            result.extend(pipe.buffer)
            pipe.buffer.clear()
            require(len(result) <= cap, "Git metadata query exceeded declared bound")
        status = pipe.process.wait(timeout=max(0.001, deadline - time.monotonic()))
        require(status == 0 and not pipe.error, "Git metadata query failed")
        return bytes(result)
    finally:
        pipe.close()


def _validate_objects(
    repository: Path, members: list[GitSourceMember], selected_bodies: frozenset[str]
) -> dict[str, bytes]:
    """Authenticate all declared rows and optionally return one selected body in memory."""
    physical(repository)
    require(repository.is_dir(), "repository root must be a physical directory")
    physical(repository / ".git")
    require(
        (repository / ".git").is_dir(), "physical repository Git directory required"
    )
    grafts = repository / ".git/info/grafts"
    physical(grafts)
    require(not grafts.exists(), "legacy Git graft ancestry is not supported")
    require(len(members) <= MAX_MEMBERS, "retained source member count exceeds bound")
    require(
        len({row.member for row in members}) == len(members),
        "duplicate logical source member",
    )
    require(
        sum(row.bytes for row in members) <= MAX_TOTAL_BYTES,
        "retained source byte forecast exceeds bound",
    )
    for row in members:
        row.validate()
    if not members:
        require(not selected_bodies, "cannot read an undeclared source body")
        return {}
    require(
        selected_bodies.issubset({row.member for row in members}),
        "selected body is undeclared",
    )
    require(
        len({row.source_revision for row in members}) <= 256,
        "source epoch count exceeds bounded query forecast",
    )
    retained: dict[str, bytes] = {}
    executable = git_executable()
    deadline = time.monotonic() + WHOLE_SECONDS
    try:
        for revision in sorted({row.source_revision for row in members}):
            require(
                query(
                    repository, ["cat-file", "-t", revision], 64, deadline, executable
                )
                == b"commit\n",
                "declared source revision is not an existing commit",
            )
            require(
                query(
                    repository,
                    ["merge-base", "--is-ancestor", revision, "HEAD"],
                    0,
                    deadline,
                    executable,
                )
                == b"",
                "source revision is not in current reachable history",
            )
            selected = [row for row in members if row.source_revision == revision]
            identities: dict[str, tuple[str, str, int]] = {}
            for row in selected:
                identity = (row.git_blob, row.sha256, row.bytes)
                require(
                    row.repository_path not in identities
                    or identities[row.repository_path] == identity,
                    "conflicting identities for shared canonical Git path",
                )
                identities[row.repository_path] = identity
            selected = list({row.repository_path: row for row in selected}.values())
            for start in range(0, len(selected), 64):
                group = selected[start : start + 64]
                tree = query(
                    repository,
                    [
                        "ls-tree",
                        "-r",
                        "-z",
                        revision,
                        "--",
                        *[row.repository_path for row in group],
                    ],
                    128 * 1024,
                    deadline,
                    executable,
                )
                entries: dict[str, tuple[str, str, str]] = {}
                for record in tree.split(b"\0"):
                    if not record:
                        continue
                    meta, name = record.split(b"\t", 1)
                    mode, kind, blob = meta.decode("ascii").split()
                    logical = name.decode("utf-8")
                    require(logical not in entries, "duplicate Git tree path")
                    entries[logical] = mode, kind, blob
                require(
                    set(entries) == {row.repository_path for row in group},
                    "missing or extra declared Git source paths",
                )
                for row in group:
                    mode, kind, blob = entries[row.repository_path]
                    require(
                        mode in {"100644", "100755"}
                        and kind == "blob"
                        and blob == row.git_blob,
                        "Git member is linked, special, wrong type or wrong blob",
                    )
        pipe = GitPipe(repository, ["cat-file", "--batch"], deadline, executable)
        try:
            for row in members:
                pipe.stdin.write(
                    f"{row.source_revision}:{row.repository_path}\n".encode()
                )
                pipe.stdin.flush()
                require(
                    pipe.line() == f"{row.git_blob} blob {row.bytes}".encode(),
                    "Git body header differs from exact declared object",
                )
                digest = hashlib.sha256()
                blob_digest = hashlib.sha1(
                    f"blob {row.bytes}\0".encode(), usedforsecurity=False
                )
                remaining = row.bytes
                body_buffer = bytearray() if row.member in selected_bodies else None
                while remaining:
                    chunk = pipe.exact(min(65536, remaining))
                    digest.update(chunk)
                    if body_buffer is not None:
                        body_buffer.extend(chunk)
                    blob_digest.update(chunk)
                    remaining -= len(chunk)
                require(pipe.exact(1) == b"\n", "Git body terminator differs")
                require(
                    digest.hexdigest() == row.sha256
                    and blob_digest.hexdigest() == row.git_blob,
                    "retained source SHA256/size/Git blob mismatch",
                )
                if body_buffer is not None:
                    retained[row.member] = bytes(body_buffer)
            pipe.finish()
        finally:
            pipe.close()
    except (OSError, subprocess.SubprocessError, ValueError, UnicodeError) as error:
        raise ReportRebuildError(
            "Retained Git source could not be authenticated"
        ) from error
    finally:
        physical(repository)
        physical(repository / ".git")
        physical(grafts)
        require(not grafts.exists(), "legacy Git graft ancestry appeared during reads")
        require(
            git_executable() == executable,
            "selected Git executable changed during reads",
        )
    return retained


def validate_blobs(repository: Path, members: list[GitSourceMember]) -> None:
    """Verify every detached source body without retaining or writing payloads."""
    _validate_objects(repository, members, frozenset())


def read_blob(repository: Path, member: GitSourceMember) -> bytes:
    """Read one independently authenticated declared body into bounded memory only."""
    result = _validate_objects(repository, [member], frozenset({member.member}))
    require(member.member in result, "selected source body was not authenticated")
    return result[member.member]


def read_blobs(repository: Path, members: list[GitSourceMember]) -> dict[str, bytes]:
    """Batch-authenticate one capsule and retain at most its declared source-byte ceiling in memory."""
    return _validate_objects(
        repository, members, frozenset(row.member for row in members)
    )


def read_historical_python_correspondence(
    repository: Path,
    member: GitSourceMember,
    *,
    function_docstring: str | None = None,
) -> bytes:
    """Authenticate historical Python bytes and reject current executable drift.

    The returned body retains its original source identity. Current source is
    checked separately for syntax correspondence; it is never assigned the
    historical byte digest or presented as a new scientific execution.
    """
    require(
        member.member == member.repository_path
        and Path(member.repository_path).suffix == ".py"
        and function_docstring in {None, "main"}
        and type(member.bytes) is int
        and 0 <= member.bytes <= 128 * 1024,
        "Python correspondence requires one exact source path and document scope",
    )
    historical = read_blob(repository, member)
    current_path = repository / member.repository_path
    physical(current_path)
    require(
        current_path.is_file()
        and current_path.stat().st_nlink == 1
        and current_path.stat().st_size <= 128 * 1024
        and len(historical) <= 128 * 1024,
        "Python correspondence requires bounded regular source bodies",
    )
    current = current_path.read_bytes()

    def syntax(raw: bytes) -> str:
        tree = ast.parse(raw)
        if function_docstring is not None:
            functions = [
                node
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == function_docstring
            ]
            require(len(functions) == 1, "documented source function is ambiguous")
            body = functions[0].body
            require(
                bool(body)
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str),
                "declared source function lacks its literal docstring",
            )
            body.pop(0)
        return ast.dump(tree, include_attributes=False)

    try:
        require(
            syntax(current) == syntax(historical),
            "current Python executable source differs from historical witness",
        )
    except (SyntaxError, UnicodeError, RecursionError) as error:
        raise ReportRebuildError("Retained Python source syntax is invalid") from error
    physical(current_path)
    return historical
