from __future__ import annotations

from ...core.text import slugify as shared_slugify


def clean_text(value: str) -> str:
    """Normalize placeholder values from AADR."""
    value = value.strip()
    return "" if value in {"", ".", ".."} else value


def slugify(value: str) -> str:
    """Reuse the shared project slugifier for reporting paths."""
    return shared_slugify(value)


def escape_pipes(value: str) -> str:
    """Escape markdown pipe characters in table cells."""
    return value.replace("|", "\\|")


def escape_html(value: str) -> str:
    """Escape HTML text used in generated markup."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


__all__ = ["clean_text", "escape_html", "escape_pipes", "slugify"]
