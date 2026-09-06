from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from .model import NORDIC_COUNTRY_CODES

_SAFE_TABLE_NAME = re.compile(r"tbl_[a-z0-9_]+\Z")


def validate_request(
    *,
    table: str,
    select: str,
    order_by: Sequence[str],
    country_scope: Sequence[str],
    parent_run_id: str,
    build_id: str,
    page_size: int,
    max_pages: int,
    request_retries: int,
    request_timeout_seconds: float,
) -> None:
    validate_table_name(table)
    if not select.strip() or not order_by:
        raise ValueError("SEAD acquisition requires an explicit projection and order")
    if list(country_scope) != list(NORDIC_COUNTRY_CODES[:-1]):
        raise ValueError("SEAD country scope must be exactly SE, DK, NO, FI")
    if not parent_run_id.strip() or not build_id.strip():
        raise ValueError("SEAD acquisition requires parent run and build IDs")
    if page_size < 1 or max_pages < 1 or request_retries < 1:
        raise ValueError("SEAD pagination and retry bounds must be positive")
    if request_timeout_seconds <= 0:
        raise ValueError("SEAD request timeout must be positive")


def validate_table_name(table: str) -> None:
    if not _SAFE_TABLE_NAME.fullmatch(table):
        raise ValueError(f"Unsafe SEAD table name: {table}")


def safe_output_root(output_root: Path) -> Path:
    root = Path(output_root)
    if not root.is_absolute() or root == Path(root.anchor):
        raise ValueError("SEAD acquisition output root must be a safe absolute path")
    if ".." in root.parts or root.is_symlink():
        raise ValueError("Unsafe SEAD acquisition output root")
    for ancestor in root.parents:
        if ancestor.exists() and ancestor.is_symlink():
            raise ValueError("SEAD acquisition output cannot traverse a symlink")
    root.parent.mkdir(parents=True, exist_ok=True)
    if root.parent.is_symlink():
        raise ValueError("SEAD acquisition output parent cannot be a symlink")
    return root
