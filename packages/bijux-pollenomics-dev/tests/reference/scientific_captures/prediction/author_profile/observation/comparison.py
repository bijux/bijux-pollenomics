"""Separate current code-origin metadata from exact retained author numerical values."""

import copy
import hashlib
from pathlib import Path
from typing import Any


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def exact(left: Any, right: Any) -> None:
    if type(left) is not type(right):
        raise ValueError("Original author JSON type changed")
    if isinstance(left, dict):
        if set(left) != set(right):
            raise ValueError("Original author JSON keys changed")
        for key in left:
            exact(left[key], right[key])
    elif isinstance(left, list):
        if len(left) != len(right):
            raise ValueError("Original author JSON length changed")
        for a, b in zip(left, right, strict=True):
            exact(a, b)
    elif left != right:
        raise ValueError("Original author scientific value changed")


def compare_report(
    name: str,
    current: dict[str, Any],
    original: dict[str, Any],
    code: list[dict[str, Any]],
    documents: list[dict[str, Any]] | None = None,
) -> None:
    current = copy.deepcopy(current)
    original = copy.deepcopy(original)
    if name == "author-site-uncertainty":
        exact(current.pop("repository_code_inputs"), code)
        original.pop("repository_code_inputs")
    elif name == "author-site-profile-comparison":
        current_rows = current.pop("input_identities")
        original_rows = original.pop("input_identities")
        exact([row for row in current_rows if row["path"].endswith(".py")], code)
        expected = [row for row in original_rows if not row["path"].endswith(".py")]
        if documents is not None:
            paths = {
                "docs/report/method-certification/author-site-uncertainty/report.json",
                "docs/report/method-certification/author-site-uncertainty/draws.json",
            }
            if len(documents) != 2 or {row["path"] for row in documents} != paths:
                raise ValueError(
                    "Only the two declared upstream documentation inputs may differ"
                )
            actual = {row["path"]: row for row in documents}
            if len([row for row in expected if row["path"] in paths]) != 2:
                raise ValueError("Original profile document membership changed")
            expected = [actual.get(row["path"], row) for row in expected]
        exact(
            [row for row in current_rows if not row["path"].endswith(".py")], expected
        )
    else:
        raise ValueError("Unknown bounded author replay")
    exact(current, original)
