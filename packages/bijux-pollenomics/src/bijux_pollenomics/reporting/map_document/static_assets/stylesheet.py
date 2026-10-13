"""Compact stylesheet layout while preserving CSS lexical boundaries."""

from __future__ import annotations

import re

_CSS_WHITESPACE = " \t\n\r\f"
_HEX_DIGITS = "0123456789abcdefABCDEF"
_LAYOUT_FUNCTIONS = frozenset(
    {
        "rgb",
        "rgba",
        "hsl",
        "hsla",
        "linear-gradient",
        "radial-gradient",
        "conic-gradient",
        "repeating-linear-gradient",
        "repeating-radial-gradient",
        "repeating-conic-gradient",
    }
)


def _escape_end(stylesheet: str, start: int) -> int:
    """Retain an entire CSS escape, including its hex terminator whitespace."""
    end = start + 1
    if end == len(stylesheet):
        return end
    if stylesheet[end] in _HEX_DIGITS:
        limit = min(end + 6, len(stylesheet))
        while end < limit and stylesheet[end] in _HEX_DIGITS:
            end += 1
        if end < len(stylesheet) and stylesheet[end] in _CSS_WHITESPACE:
            end += 1
            if stylesheet[end - 1] == "\r" and stylesheet[end : end + 1] == "\n":
                end += 1
        return end
    if stylesheet[end : end + 2] == "\r\n":
        return end + 2
    return end + 1


def compact_stylesheet(stylesheet: str) -> str:
    """Remove block layout whitespace, retaining selectors and literal values.

    Strings, comments, escapes and bracketed content remain verbatim.
    Outside those boundaries whitespace keeps a single separator;
    braces and declaration terminators do not need a following separator.
    Ordinary declaration colons also omit separator whitespace; custom-property
    token streams retain it for substitution and CSSOM consumers. Ordinary color
    and gradient functions omit layout at commas and parenthesis boundaries;
    other functions and literal boundaries remain verbatim.
    """
    chunks: list[str] = []
    nesting: list[str] = []
    functions: list[str | None] = []
    ordinary_value = False
    curly_depth = 0
    index = 0
    pending_space = False
    previous_boundary = False
    declaration_start = 0
    compact_colon = False
    while index < len(stylesheet):
        char = stylesheet[index]
        if char in _CSS_WHITESPACE and not nesting:
            pending_space = True
            index += 1
            continue
        if (
            char in _CSS_WHITESPACE
            and nesting
            and ordinary_value
            and functions[-1] in _LAYOUT_FUNCTIONS
        ):
            end = index + 1
            while end < len(stylesheet) and stylesheet[end] in _CSS_WHITESPACE:
                end += 1
            if chunks[-1] in {",", "("} or stylesheet[end : end + 1] in {",", ")"}:
                index = end
                continue
        start = index
        boundary = not nesting and char in "{};"
        if (
            pending_space
            and chunks
            and not previous_boundary
            and not compact_colon
            and char not in "{}"
        ):
            chunks.append(" ")
        pending_space = False
        compact_colon = False
        if stylesheet.startswith("/*", index):
            closing = stylesheet.find("*/", index + 2)
            index = len(stylesheet) if closing < 0 else closing + 2
            boundary = False
        elif char in "\"'":
            index += 1
            while index < len(stylesheet):
                if stylesheet[index] == "\\":
                    index = _escape_end(stylesheet, index)
                elif stylesheet[index] == char:
                    index += 1
                    break
                else:
                    index += 1
            boundary = False
        elif char == "\\":
            index = _escape_end(stylesheet, index)
            boundary = False
        else:
            if char in "([":
                nesting.append(")" if char == "(" else "]")
                function = (
                    re.search(r"[A-Za-z-]+$", stylesheet[:index])
                    if char == "("
                    else None
                )
                functions.append(function.group(0).lower() if function else None)
            elif nesting and char == nesting[-1]:
                nesting.pop()
                functions.pop()
            index += 1
        if not nesting and char == ":":
            property_name = "".join(chunks[declaration_start:]).strip()
            compact_colon = (
                re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", property_name) is not None
            )
        if not nesting and char == ":":
            ordinary_value = compact_colon and curly_depth > 0
        chunks.append(stylesheet[start:index])
        if boundary:
            if char == "{":
                curly_depth += 1
            elif char == "}":
                curly_depth = max(0, curly_depth - 1)
            ordinary_value = False
            declaration_start = len(chunks)
        previous_boundary = boundary
    return "".join(chunks)


__all__ = ["compact_stylesheet"]
