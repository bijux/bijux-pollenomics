"""Local reference stash discovery and cached availability records."""

from __future__ import annotations

from functools import cache
import os
from pathlib import Path

from .models import _ReferenceStashDraft, _ReferenceStashRecord


def _resolve_reference_stash_root(output_root: Path) -> Path | None:
    env_root = os.environ.get("BIJUX_POLLENOMICS_REFERENCE_STASH_ROOT", "").strip()
    candidates: list[Path] = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(
        Path(output_root).resolve().parent.parent
        / "bijan-references"
        / "bijux-pollenomics"
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def _reference_stash_records(output_root: Path) -> dict[str, _ReferenceStashRecord]:
    return _reference_stash_records_cached(str(Path(output_root).resolve()))


def _reference_stash_records_uncached(
    output_root: Path,
) -> dict[str, _ReferenceStashRecord]:
    stash_root = _resolve_reference_stash_root(output_root)
    if stash_root is None:
        return {}
    records: dict[str, _ReferenceStashDraft] = {}
    for article_path in stash_root.glob("*.pdf"):
        slug = article_path.stem
        records.setdefault(
            slug,
            {
                "stash_slug": slug,
                "article_formats": set(),
                "supplementary_assets": [],
                "structured_table_count": 0,
                "archive_bundle_count": 0,
            },
        )
        records[slug]["article_formats"].add(
            article_path.suffix.lower().removeprefix(".")
        )
    for doi_dir in sorted(
        path
        for path in stash_root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    ):
        record = records.setdefault(
            doi_dir.name,
            {
                "stash_slug": doi_dir.name,
                "article_formats": set(),
                "supplementary_assets": [],
                "structured_table_count": 0,
                "archive_bundle_count": 0,
            },
        )
        for asset in sorted(path for path in doi_dir.rglob("*") if path.is_file()):
            if (
                asset.name.startswith(".")
                or asset.name == ".DS_Store"
                or asset.suffix.lower() == ".md"
            ):
                continue
            record["supplementary_assets"].append(str(asset.relative_to(doi_dir)))
            suffix = asset.suffix.lower()
            if suffix in {".csv", ".tsv", ".xls", ".xlsx", ".json"}:
                record["structured_table_count"] += 1
            if suffix == ".zip":
                record["archive_bundle_count"] += 1
    payload: dict[str, _ReferenceStashRecord] = {}
    for slug, record in records.items():
        payload[slug] = {
            "stash_slug": slug,
            "article_formats": tuple(sorted(record["article_formats"])),
            "supplementary_assets": tuple(record["supplementary_assets"]),
            "structured_table_count": int(record["structured_table_count"]),
            "archive_bundle_count": int(record["archive_bundle_count"]),
        }
    return payload


@cache
def _reference_stash_records_cached(
    output_root_key: str,
) -> dict[str, _ReferenceStashRecord]:
    return _reference_stash_records_uncached(Path(output_root_key))


def _local_reference_article_status(stash_record: _ReferenceStashRecord) -> str:
    if stash_record.get("article_formats"):
        return "local_reference_staged"
    return "missing"


def _local_reference_supplement_status(stash_record: _ReferenceStashRecord) -> str:
    if stash_record.get("supplementary_assets"):
        return "local_reference_staged"
    return "missing"
