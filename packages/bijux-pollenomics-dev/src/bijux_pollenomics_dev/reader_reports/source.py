"""Read the canonical report inventory without crossing repository boundaries."""

from __future__ import annotations

from collections.abc import Mapping
import csv
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any
from urllib.parse import unquote, urlsplit

PAPER_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
REPORT_PREFIX = PurePosixPath("reports/science")
MAINTAINED_REPORT_ENTRYPOINTS = frozenset({"makes/pollenomics-verification.mk"})
MAINTAINED_PRESENTATION_INPUTS = frozenset(
    {
        "presentation/big-picture.tex",
        "presentation/developer.tex",
        "presentation/scientific-evidence.tex",
        "presentation/shared.tex",
        "presentation/build.py",
    }
)
MAINTAINED_READER_BOOKKEEPING = frozenset(
    {
        ".github/workflows/scientific-verification.yml",
        "mkdocs.yml",
        "packages/bijux-pollenomics-dev/pyproject.toml",
        "packages/bijux-pollenomics-lra/pyproject.toml",
        "packages/bijux-pollenomics/pyproject.toml",
        "packages/pollenomics/pyproject.toml",
        "presentation/source-lock.json",
        "pyproject.toml",
        "reports/exports/site-downloads.json",
        "uv.lock",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/"
        "report_portal/scientific_accounts.json",
        "docs/report/report_surface_registry.json",
        "docs/report/report_narrative_quality_review.json",
    }
)


class SourceError(ValueError):
    """An inventory value or report reference is outside the declared source set."""


@dataclass(frozen=True)
class Paper:
    """Bind one canonical report to its source identity and inventory account."""

    paper_id: str
    relative_path: PurePosixPath
    path: Path
    source_sha256: str
    citation: str
    account_status: str


def sha256_bytes(data: bytes) -> str:
    """Return the SHA-256 digest of the exact supplied bytes."""
    return hashlib.sha256(data).hexdigest()


def exported_content(source: bytes) -> bytes:
    """Remove only historical metadata lines suppressed by the paper renderer."""
    return re.sub(
        rb"^<!-- scientific-(?:claim-semantic|authored-source)-sha256: "
        rb"[0-9a-f]{64} -->\n",
        b"",
        source,
        flags=re.MULTILINE,
    )


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of a repository file's current bytes."""
    return sha256_bytes(path.read_bytes())


def _inside(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def _require_plain_path(root: Path, candidate: Path) -> Path:
    candidate = Path(os.path.abspath(candidate))
    if not _inside(candidate, root):
        raise SourceError(f"path outside repository: {candidate}")
    current = root
    for part in candidate.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise SourceError(f"symlink in source path: {current}")
    return candidate.resolve(strict=True)


def repository_root(path: Path) -> Path:
    """Require a real repository root before resolving report sources."""
    root = path.resolve(strict=True)
    if not root.is_dir() or not (root / ".git").exists():
        raise SourceError(f"not a repository root: {path}")
    return root


def repository_file(root: Path, value: str | Path) -> Path:
    """Resolve a repository file while refusing symlinks and path escape."""
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = _require_plain_path(root, candidate)
    if not resolved.is_file() or not _inside(resolved, root):
        raise SourceError(f"not a repository file: {value}")
    return resolved


def load_inventory(root: Path, value: str | Path) -> tuple[Path, str, list[Paper]]:
    """Read the canonical paper inventory and pin each report's source bytes."""
    inventory = repository_file(root, value)
    if inventory.suffix != ".csv":
        raise SourceError("inventory must be a CSV file")
    raw = inventory.read_bytes()
    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise SourceError("inventory must be UTF-8") from error
    reader = csv.DictReader(decoded.splitlines())
    if not reader.fieldnames or not {"paper_id", "canonical_report"}.issubset(
        reader.fieldnames
    ):
        raise SourceError("inventory needs paper_id and canonical_report columns")
    papers: list[Paper] = []
    ids: set[str] = set()
    paths: set[PurePosixPath] = set()
    for row in reader:
        paper_id = (row.get("paper_id") or "").strip()
        source_name = (row.get("canonical_report") or "").strip()
        if not PAPER_ID.fullmatch(paper_id):
            raise SourceError(f"invalid paper_id: {paper_id!r}")
        relative = PurePosixPath(source_name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.parent != REPORT_PREFIX
            or relative.suffix != ".md"
        ):
            raise SourceError(f"invalid canonical_report: {source_name!r}")
        if paper_id in ids or relative in paths:
            raise SourceError(f"duplicate paper id or report: {paper_id}")
        ids.add(paper_id)
        paths.add(relative)
        report = repository_file(root, str(relative))
        try:
            report.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise SourceError(f"report must be UTF-8: {relative}") from error
        papers.append(
            Paper(
                paper_id=paper_id,
                relative_path=relative,
                path=report,
                source_sha256=file_sha256(report),
                citation=(row.get("citation") or "").strip(),
                account_status=(row.get("account_status") or "").strip(),
            )
        )
    if not papers:
        raise SourceError("inventory contains no canonical reports")
    return inventory, sha256_bytes(raw), papers


def check_retained_sources(
    root: Path, inventory_value: str | Path, manifest: Mapping[str, Any]
) -> dict[str, str]:
    """Refuse stale canonical accounts without compilers, PDFs or historical Git."""
    _, _, papers = load_inventory(root, inventory_value)
    if manifest.get("schema_version") != "canonical-paper-pdf-library.v1":
        raise SourceError("unknown retained paper manifest")
    rows = manifest.get("papers")
    if not isinstance(rows, list) or len(rows) != len(papers):
        raise SourceError("retained paper source population differs")
    declared: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise SourceError("retained paper source record must be an object")
        path, digest = row.get("canonical_report"), row.get("canonical_source_sha256")
        if (
            not isinstance(path, str)
            or path in declared
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            raise SourceError("retained paper needs one exact canonical source digest")
        declared[path] = digest
    current = {paper.relative_path.as_posix(): paper.source_sha256 for paper in papers}
    if set(current) != set(declared):
        raise SourceError("retained paper canonical source membership differs")
    for path, digest in current.items():
        if digest != declared[path]:
            raise SourceError(f"retained PDF canonical source is stale: {path}")
    return current


def output_directory(root: Path, value: str | Path) -> Path:
    """Require an absent output directory below repository artifacts."""
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = Path(os.path.abspath(candidate))
    artifacts = root / "artifacts"
    if not _inside(candidate, artifacts) or candidate == artifacts:
        raise SourceError(
            "output must be an absent directory under repository artifacts/"
        )
    if candidate.exists() or candidate.is_symlink():
        raise SourceError(f"output directory already exists: {candidate}")
    current = root
    for part in candidate.relative_to(root).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise SourceError(f"symlink in output path: {current}")
    return candidate


def _committed_target(root: Path, relative: str, revision: str) -> str:
    """Identify a citation's Git mode without opening its referenced payload."""
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise SourceError("citation requires an exact commit revision")
    base = ["git", "--no-replace-objects", "--literal-pathspecs", "-C", str(root)]
    try:
        kind = subprocess.run(
            [*base, "cat-file", "-t", revision],
            capture_output=True,
            check=True,
            timeout=5,
        ).stdout
        if kind != b"commit\n":
            raise SourceError("citation revision must identify a commit")
        if not relative:
            return "tree"
        records = subprocess.run(
            [*base, "ls-tree", "-z", "--full-tree", revision, "--", relative],
            capture_output=True,
            check=True,
            timeout=5,
        ).stdout.split(b"\0")
    except (OSError, subprocess.SubprocessError) as error:
        raise SourceError("committed citation metadata is unavailable") from error
    entries = [record for record in records if record]
    if len(entries) != 1:
        raise SourceError("citation path is absent from its declared commit")
    metadata, name = entries[0].split(b"\t", 1)
    mode, object_kind, _ = metadata.split()
    if name.decode("utf-8") != relative or (mode, object_kind) not in {
        (b"100644", b"blob"),
        (b"100755", b"blob"),
        (b"040000", b"tree"),
    }:
        raise SourceError("citation requires a regular committed file or tree")
    return "tree" if object_kind == b"tree" else "blob"


def portable_link(root: Path, source: Path, destination: str, revision: str) -> str:
    """Bind a portable URL to committed path metadata, not source-body intake."""
    if any(ord(char) < 32 for char in destination):
        raise SourceError("control character in Markdown link")
    parsed = urlsplit(destination)
    if parsed.scheme in {"https", "http"} and parsed.netloc:
        return destination
    if parsed.scheme == "mailto" and parsed.path:
        return destination
    if parsed.scheme or parsed.netloc:
        raise SourceError(f"unsupported link scheme: {destination}")
    if parsed.path.startswith("/"):
        raise SourceError(f"absolute local link is unsupported: {destination}")
    if parsed.query:
        raise SourceError(f"local query link has no portable meaning: {destination}")
    decoded = unquote(parsed.path)
    if (
        decoded.startswith("/")
        or "\\" in decoded
        or any(ord(character) < 32 for character in decoded)
    ):
        raise SourceError("local citation path must be literal and relative")
    try:
        parts = list(source.relative_to(root).parent.parts)
    except ValueError as error:
        raise SourceError("citation source leaves repository") from error
    components = decoded.split("/") if decoded else [source.name]
    intermediate: set[str] = set()
    for index, component in enumerate(components):
        if component == "..":
            if not parts:
                raise SourceError(f"link leaves repository: {destination}")
            parts.pop()
        elif component not in {"", "."}:
            parts.append(component)
            if index < len(components) - 1:
                intermediate.add(PurePosixPath(*parts).as_posix())
        if root.joinpath(*parts).is_symlink():
            raise SourceError(f"symlink in citation path: {destination}")
    relative = PurePosixPath(*parts).as_posix() if parts else ""
    for prefix in sorted(intermediate):
        if _committed_target(root, prefix, revision) != "tree":
            raise SourceError("citation traverses a non-tree Git path")
    for depth in range(1, len(parts) + 1):
        if root.joinpath(*parts[:depth]).is_symlink():
            raise SourceError(f"symlink in citation path: {destination}")
    route = _committed_target(root, relative, revision)
    from urllib.parse import quote

    url = f"https://github.com/bijux/bijux-pollenomics/{route}/{revision}/{quote(relative)}"
    if parsed.fragment:
        url += "#" + quote(parsed.fragment, safe="-._~")
    return url
