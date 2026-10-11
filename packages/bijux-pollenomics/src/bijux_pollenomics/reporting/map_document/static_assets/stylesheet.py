"""Compact stylesheet layout while preserving CSS lexical boundaries."""

from __future__ import annotations

_CSS_WHITESPACE = " \t\n\r\f"
_HEX_DIGITS = "0123456789abcdefABCDEF"


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

    Strings, comments, escapes and parenthesized or bracketed content remain
    verbatim. Outside those boundaries whitespace keeps a single separator;
    braces and declaration terminators do not need a following separator.
    """
    chunks: list[str] = []
    nesting: list[str] = []
    index = 0
    pending_space = False
    previous_boundary = False
    while index < len(stylesheet):
        char = stylesheet[index]
        if char in _CSS_WHITESPACE and not nesting:
            pending_space = True
            index += 1
            continue
        start = index
        boundary = not nesting and char in "{};"
        if pending_space and chunks and not previous_boundary and char not in "{}":
            chunks.append(" ")
        pending_space = False
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
            elif nesting and char == nesting[-1]:
                nesting.pop()
            index += 1
        chunks.append(stylesheet[start:index])
        previous_boundary = boundary
    return "".join(chunks)


__all__ = ["compact_stylesheet"]
