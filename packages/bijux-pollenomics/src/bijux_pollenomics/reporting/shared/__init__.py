"""Shared reporting text and value-selection compatibility surface."""

from ..assembly.value_selection import pick_value
from ..presentation.text import clean_text, escape_html, escape_pipes, slugify

__all__ = ["clean_text", "escape_html", "escape_pipes", "pick_value", "slugify"]
