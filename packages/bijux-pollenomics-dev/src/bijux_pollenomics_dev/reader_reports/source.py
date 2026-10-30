"""Read the canonical report inventory without crossing repository boundaries."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
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


def portable_link(root: Path, source: Path, destination: str, revision: str) -> str:
    """Resolve a report link to its pinned portable repository destination."""
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
    target = source if not parsed.path else source.parent / unquote(parsed.path)
    resolved = _require_plain_path(root, target)
    if not _inside(resolved, root):
        raise SourceError(f"link leaves repository: {destination}")
    if not resolved.exists():
        raise SourceError(f"local link target is missing: {destination}")
    from urllib.parse import quote

    route = "tree" if resolved.is_dir() else "blob"
    relative = resolved.relative_to(root).as_posix()
    url = f"https://github.com/bijux/bijux-pollenomics/{route}/{revision}/{quote(relative)}"
    if parsed.fragment:
        url += "#" + quote(parsed.fragment, safe="-._~")
    return url
