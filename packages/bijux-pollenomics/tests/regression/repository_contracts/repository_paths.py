"""Stable repository paths and shared documentation contract constants."""

from pathlib import Path
import re

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = Path(__file__).resolve().parents[5]
WORKFLOW_URL_RE = re.compile(
    r"https://github\.com/(?P<repo>[^/\s]+/[^/\s]+)/actions/workflows/"
    r"(?P<workflow>[A-Za-z0-9_.-]+)"
)
MERMAID_RESERVED_IDS = {
    "class", "classdef", "click", "default", "end", "graph",
    "linkstyle", "style", "subgraph",
}

__all__ = [
    "MERMAID_RESERVED_IDS", "PACKAGE_ROOT", "REPO_ROOT", "WORKFLOW_URL_RE"
]
