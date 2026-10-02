"""Compile source-pinned report PDFs in one isolated artifacts directory."""

from __future__ import annotations

import json
import os
import re
import subprocess
from importlib.metadata import version
from pathlib import Path
from typing import Any

from .render import ReportRenderer, document_latex
from .source import (
    Paper,
    file_sha256,
    load_inventory,
    output_directory,
    repository_root,
    sha256_bytes,
)


class ExportError(RuntimeError):
    """A bounded external compile failed or an input changed during export."""


def _command(
    arguments: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    timeout: int,
    log_prefix: Path,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            arguments,
            cwd=cwd,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        log_prefix.with_suffix(".timeout.log").write_text(
            f"command: {arguments!r}\ntimeout_seconds: {timeout}\n", encoding="utf-8"
        )
        raise ExportError(f"timed out after {timeout}s: {arguments[0]}") from error
    log_prefix.with_suffix(".stdout.log").write_text(result.stdout, encoding="utf-8")
    log_prefix.with_suffix(".stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        tail = (result.stderr or result.stdout)[-1200:]
        raise ExportError(f"{arguments[0]} exited {result.returncode}: {tail}")
    return result


def _revision(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    revision = result.stdout.strip()
    if result.returncode or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ExportError("cannot identify repository HEAD revision")
    return revision


def _epoch(value: str | None) -> str:
    selected = value if value is not None else os.environ.get("SOURCE_DATE_EPOCH", "0")
    if not re.fullmatch(r"[0-9]{1,10}", selected) or int(selected) > 4_102_444_800:
        raise ExportError(
            "SOURCE_DATE_EPOCH must be a nonnegative UTC timestamp through 2100"
        )
    return selected


def _verify_revision_input(
    root: Path, revision: str, path: Path, expected_sha256: str
) -> None:
    relative = path.relative_to(root).as_posix()
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=root,
        capture_output=True,
        timeout=10,
        check=False,
    )
    if result.returncode or sha256_bytes(result.stdout) != expected_sha256:
        raise ExportError(
            f"source does not match repository revision {revision}: {relative}"
        )


def _versions(root: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    for tool, args in (
        ("latexmk", ["latexmk", "-v"]),
        ("xelatex", ["xelatex", "--version"]),
        ("dot", ["dot", "-V"]),
    ):
        try:
            result = subprocess.run(
                args, cwd=root, capture_output=True, text=True, timeout=5, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ExportError(f"required tool unavailable: {tool}") from error
        if result.returncode:
            raise ExportError(f"required tool failed: {tool}")
        versions[tool] = (result.stdout or result.stderr).splitlines()[0]
    return versions


def _compile_paper(
    root: Path,
    paper: Paper,
    output: Path,
    revision: str,
    epoch: str,
    environment: dict[str, str],
) -> dict[str, Any]:
    directory = output / paper.paper_id
    directory.mkdir()
    source_bytes = paper.path.read_bytes()
    if sha256_bytes(source_bytes) != paper.source_sha256:
        raise ExportError(f"source changed before render: {paper.relative_path}")
    rendered = ReportRenderer(root, paper.path, revision).render(
        source_bytes.decode("utf-8")
    )
    title = source_bytes.decode("utf-8").splitlines()[0].removeprefix("# ").strip()
    latex = document_latex(
        rendered.latex, title, paper.relative_path.as_posix(), paper.source_sha256
    )
    tex_path = directory / "report.tex"
    tex_path.write_text(latex, encoding="utf-8")
    asset_receipts: list[dict[str, str]] = []
    for asset in rendered.assets:
        path = directory / asset.name
        path.write_text(asset.content, encoding="utf-8")
        asset_receipts.append(
            {"path": asset.name, "kind": asset.kind, "sha256": file_sha256(path)}
        )
        if asset.kind == "diagram":
            pdf = path.with_suffix(".pdf")
            _command(
                ["dot", "-Tpdf", path.name, "-o", pdf.name],
                cwd=directory,
                environment=environment,
                timeout=25,
                log_prefix=directory / path.stem,
            )
            asset_receipts.append(
                {"path": pdf.name, "kind": "diagram_pdf", "sha256": file_sha256(pdf)}
            )
    _command(
        [
            "latexmk",
            "-pdfxe",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            "report.tex",
        ],
        cwd=directory,
        environment=environment,
        timeout=180,
        log_prefix=directory / "latexmk",
    )
    pdf = directory / "report.pdf"
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise ExportError(f"latexmk succeeded without PDF: {paper.paper_id}")
    if file_sha256(paper.path) != paper.source_sha256:
        raise ExportError(f"source changed during render: {paper.relative_path}")
    return {
        "paper_id": paper.paper_id,
        "canonical_report": paper.relative_path.as_posix(),
        "source_sha256": paper.source_sha256,
        "citation": paper.citation,
        "account_status": paper.account_status,
        "latex_sha256": file_sha256(tex_path),
        "pdf": f"{paper.paper_id}/report.pdf",
        "pdf_sha256": file_sha256(pdf),
        "pdf_bytes": pdf.stat().st_size,
        "local_repository_links": rendered.local_link_count,
        "external_links": rendered.external_link_count,
        "diagrams": rendered.diagram_count,
        "code_blocks": rendered.code_block_count,
        "assets": asset_receipts,
    }


def export_reports(
    repository: Path,
    inventory_value: str | Path,
    output_value: str | Path,
    *,
    paper_id: str | None = None,
    source_date_epoch: str | None = None,
) -> Path:
    root = repository_root(repository)
    inventory, inventory_hash, papers = load_inventory(root, inventory_value)
    output = output_directory(root, output_value)
    if paper_id is not None:
        papers_to_export = [paper for paper in papers if paper.paper_id == paper_id]
        if not papers_to_export:
            raise ExportError(f"paper_id not in inventory: {paper_id}")
    else:
        papers_to_export = papers
    revision = _revision(root)
    _verify_revision_input(root, revision, inventory, inventory_hash)
    for paper in papers:
        _verify_revision_input(root, revision, paper.path, paper.source_sha256)
    epoch = _epoch(source_date_epoch)
    versions = _versions(root)
    producer_hashes = {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted(Path(__file__).parent.glob("*.py"))
    }
    output.mkdir(parents=True)
    environment = dict(os.environ)
    environment.update(
        {
            "SOURCE_DATE_EPOCH": epoch,
            "FORCE_SOURCE_DATE": "1",
            "TZ": "UTC",
            "TEXMFOUTPUT": str(output),
            "XDG_CACHE_HOME": str(output / ".cache"),
        }
    )
    receipts: list[dict[str, Any]] = []
    for paper in papers_to_export:
        receipts.append(
            _compile_paper(root, paper, output, revision, epoch, environment)
        )
    if file_sha256(inventory) != inventory_hash:
        raise ExportError("inventory changed during export")
    for paper in papers:
        if file_sha256(paper.path) != paper.source_sha256:
            raise ExportError(
                f"inventory report changed during export: {paper.relative_path}"
            )
    for relative, expected in producer_hashes.items():
        if file_sha256(root / relative) != expected:
            raise ExportError(f"producer changed during export: {relative}")
    receipt = {
        "schema_version": "reader-report-pdf-export.1",
        "repository_revision": revision,
        "repository_link_base": f"https://github.com/bijux/bijux-pollenomics/blob/{revision}/",
        "repository_links_verified_online": False,
        "repository_link_status": "Local source paths are resolved and encoded; remote availability awaits authorized publication.",
        "diagram_layout": "Source flowchart edges and labels retained; layout reflowed top-to-bottom for A4 readability.",
        "inventory": inventory.relative_to(root).as_posix(),
        "inventory_sha256": inventory_hash,
        "inventory_report_hashes": {
            paper.relative_path.as_posix(): paper.source_sha256 for paper in papers
        },
        "source_date_epoch": int(epoch),
        "tools": versions,
        "python_dependencies": {"markdown-it-py": version("markdown-it-py")},
        "producer_sha256": producer_hashes,
        "papers": receipts,
    }
    result = output / "receipt.json"
    result.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result
