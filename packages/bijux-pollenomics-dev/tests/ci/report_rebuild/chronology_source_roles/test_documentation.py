"""Reject executable drift and non-documentation edits at named insertion boundaries."""

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    sample_chronology_capture as capture,
)

from .fixtures import (
    DOCS,
    DOCUMENTATION,
    MULTI_DOC_PATH,
    ROOT_SOURCE,
    source_pair,
)
from .fixtures import (
    literal_authority as literal_authority,
)


@pytest.mark.parametrize("name", sorted(DOCS))
def test_named_literal_insertions_and_adjacent_blank_line_are_supported(
    name: str,
) -> None:
    captured, current = source_pair(name, adjacent_blank=True)
    assert capture._documented_source_matches(name, captured, current)


@pytest.mark.parametrize(
    "damage",
    [
        "missing_named_doc",
        "empty_doc",
        "fstring_doc",
        "bytes_doc",
        "computed_doc",
        "existing_doc",
        "wrong_scope",
        "new_definition",
        "import",
        "number",
        "string",
        "comment",
        "whitespace",
        "spacing",
        "annotation",
        "inline_doc_comment",
    ],
)
def test_no_broad_ast_or_documentation_waiver(damage: str) -> None:
    captured, current = source_pair(MULTI_DOC_PATH)
    if damage == "missing_named_doc":
        current = current.replace((DOCUMENTATION + "\n").encode(), b"", 1)
    elif damage == "empty_doc":
        current = current.replace(DOCUMENTATION.encode(), b'""""""', 1)
    elif damage == "fstring_doc":
        current = current.replace(DOCUMENTATION.encode(), b'f"Own {1}"', 1)
    elif damage == "bytes_doc":
        current = current.replace(DOCUMENTATION.encode(), b'b"Own bytes"', 1)
    elif damage == "computed_doc":
        current = current.replace(DOCUMENTATION.encode(), b'"Own" + " statement"', 1)
    elif damage == "existing_doc":
        captured = b'"""Existing captured documentation."""\n' + captured
    elif damage == "wrong_scope":
        current = captured.replace(
            b"def untouched():\n", b'def untouched():\n    """Wrong scope."""\n'
        )
    elif damage == "new_definition":
        current += b"\ndef new_program():\n    return 8\n"
    elif damage == "import":
        current += b"\nimport math\n"
    elif damage == "number":
        current = current.replace(b"VALUE = 7", b"VALUE = 8")
    elif damage == "string":
        current = current.replace(b"'own stable'", b"'changed scientific string'")
    elif damage == "comment":
        current += b"\n# Unapproved current comment\n"
    elif damage == "whitespace":
        current += b"\n"
    elif damage == "spacing":
        current = current.replace(b"VALUE = 7", b"VALUE  = 7")
    elif damage == "annotation":
        current = current.replace(b"VALUE = 7", b"VALUE: int = 7")
    else:
        current = current.replace(
            DOCUMENTATION.encode(),
            (DOCUMENTATION + " # unapproved insertion").encode(),
            1,
        )
    assert not capture._documented_source_matches(MULTI_DOC_PATH, captured, current)


def test_duplicate_qualified_definition_is_not_a_named_insertion() -> None:
    captured, current = source_pair(MULTI_DOC_PATH)
    captured += b"\ndef overlapping_geojson_context():\n    return VALUE\n"
    current += b'\ndef overlapping_geojson_context():\n    """Duplicate scope."""\n    return VALUE\n'
    assert not capture._documented_source_matches(MULTI_DOC_PATH, captured, current)


def test_unnamed_documentation_insertion_is_refused() -> None:
    captured, current = source_pair(MULTI_DOC_PATH)
    current = current.replace(
        b"def untouched():\n",
        b'def untouched():\n    """Unapproved new documentation scope."""\n',
    )
    assert not capture._documented_source_matches(MULTI_DOC_PATH, captured, current)


def test_documentation_role_does_not_expand_to_neighboring_source_path() -> None:
    captured, current = source_pair(MULTI_DOC_PATH)
    name = ROOT_SOURCE + "analysis/fieldwork/land_use/unlisted.py"
    assert not capture._documented_source_matches(name, captured, current)


@pytest.mark.parametrize("damage", ["invalid_utf8", "syntax"])
def test_malformed_source_refuses_documentation_correspondence(damage: str) -> None:
    captured, current = source_pair(MULTI_DOC_PATH)
    current += b"\xff" if damage == "invalid_utf8" else b"\ndef broken(:\n"
    assert not capture._documented_source_matches(MULTI_DOC_PATH, captured, current)


@pytest.mark.parametrize("name", sorted(DOCS))
def test_unicode_documentation_uses_utf8_byte_offsets(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured, current = source_pair(name)
    current = current.replace(
        DOCUMENTATION.encode(), '"""Own λ café documentation."""'.encode()
    )
    monkeypatch.setattr(
        capture,
        "DOCUMENTED_CAPTURE_STRINGS",
        {
            **capture.DOCUMENTED_CAPTURE_STRINGS,
            name: dict.fromkeys(DOCS[name], "Own λ café documentation."),
        },
    )
    assert capture._documented_source_matches(name, captured, current)


@pytest.mark.parametrize("suffix", [b" # outside Unicode literal", b"; OTHER = 9"])
def test_unicode_doc_offsets_do_not_admit_comments_or_code(
    suffix: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured, current = source_pair(MULTI_DOC_PATH)
    unicode_doc = '"""Own λ café documentation."""'.encode()
    monkeypatch.setattr(
        capture,
        "DOCUMENTED_CAPTURE_STRINGS",
        {
            **capture.DOCUMENTED_CAPTURE_STRINGS,
            MULTI_DOC_PATH: {
                **capture.DOCUMENTED_CAPTURE_STRINGS[MULTI_DOC_PATH],
                "<module>": "Own λ café documentation.",
            },
        },
    )
    current = current.replace(DOCUMENTATION.encode(), unicode_doc + suffix, 1)
    assert not capture._documented_source_matches(MULTI_DOC_PATH, captured, current)


def test_whitespace_only_documentation_is_not_documentation() -> None:
    captured, current = source_pair(MULTI_DOC_PATH)
    current = current.replace(DOCUMENTATION.encode(), b'"""   \t """', 1)
    assert not capture._documented_source_matches(MULTI_DOC_PATH, captured, current)


def test_nul_source_is_a_refusal_not_an_uncaught_parser_error() -> None:
    captured, current = source_pair(MULTI_DOC_PATH)
    assert not capture._documented_source_matches(
        MULTI_DOC_PATH, captured, current + b"\x00"
    )


def test_changed_named_doc_content_is_not_an_approved_literal() -> None:
    captured, current = source_pair(MULTI_DOC_PATH)
    current = current.replace(
        DOCUMENTATION.encode(), b'"""Unapproved changed documentation."""', 1
    )
    assert not capture._documented_source_matches(MULTI_DOC_PATH, captured, current)
