"""Stylesheet transport preserves lexical values and inline boundaries."""

from __future__ import annotations

import re

import pytest

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            ".a .b {\n color: red;\n display: none;\n }",
            ".a .b{color:red;display:none;}",
        ),
        (
            '[data-label="a  b"] .child { content: " } ;  { "; }',
            '[data-label="a  b"] .child{content:" } ;  { ";}',
        ),
        (".a { width: calc(100% -  2px); }", ".a{width:calc(100% -  2px);}"),
        (
            ".a { background: url(data:image/svg+xml;a  b); }",
            ".a{background:url(data:image/svg+xml;a  b);}",
        ),
        (
            ".a /* { ; } \n retained */ .b { color: red; }",
            ".a /* { ; } \n retained */ .b{color:red;}",
        ),
        (r".\31 a { color: red; }", r".\31 a{color:red;}"),
        (r".a\;b .c { color: red; }", r".a\;b .c{color:red;}"),
        ('.a { content: "a\\\n  b"; }', '.a{content:"a\\\n  b";}'),
        (
            "@media (min-width:  300px) { .a > .b { margin: 0; } }",
            "@media (min-width:  300px){.a > .b{margin:0;}}",
        ),
        (
            ".a { --empty: ; --word: red blue; color: var(--word); }",
            ".a{--empty: ;--word: red blue;color:var(--word);}",
        ),
        ('.a { content: "unfinished  ', '.a{content:"unfinished  '),
        (".a { color: red; /* unfinished  ", ".a{color:red;/* unfinished  "),
    ],
)
def test_stylesheet_layout_preserves_lexical_values(source: str, expected: str) -> None:
    from bijux_pollenomics.reporting.map_document.static_assets.stylesheet import (
        compact_stylesheet,
    )

    assert compact_stylesheet(source) == expected


def test_stylesheet_compaction_changes_only_the_inline_style_boundary() -> None:
    from bijux_pollenomics.reporting.map_document.render import (
        _compact_inline_stylesheet,
    )

    prefix = (
        '<script>const literal = "a  b ; {";</script>'
        '<script type="application/json">{"label":"a:  b"}</script><style>'
    )
    suffix = '</style><p data-label="a  b">  retained  </p>'
    document = prefix + ".a .b { color: red; }" + suffix
    assert _compact_inline_stylesheet(document) == prefix + ".a .b{color:red;}" + suffix


def test_stylesheet_preserves_lexical_atoms_and_is_idempotent() -> None:
    from bijux_pollenomics.reporting.map_document.static_assets.stylesheet import (
        compact_stylesheet,
    )

    stylesheet = MAP_DOCUMENT_TEMPLATE.split("<style>", 1)[1].split("</style>", 1)[0]
    compact = compact_stylesheet(stylesheet)
    # Segment complete lexical literals independently of the transport scanner.
    escape = r"\\(?:[0-9a-fA-F]{1,6}(?:\r\n|[ \t\n\r\f])?|\r\n|[\s\S])"
    quoted = r'"(?:' + escape + r'|[^"\\])*"|\'(?:' + escape + r"|[^'\\])*\'"
    atoms = re.compile(
        r"/\*[\s\S]*?\*/|" + quoted + "|" + escape + r"|[ \t\n\r\f]+|[^\s\\\"']+"
    )

    def tokens(value: str) -> list[str]:
        segments = atoms.findall(value)
        assert "".join(segments) == value
        result = []
        for segment in segments:
            if segment.isspace():
                continue
            if segment.startswith(("/*", '"', "'", "\\")):
                result.append(segment)
            else:
                result.extend(
                    re.findall(r"[a-zA-Z0-9_#.%+-]+|[^a-zA-Z0-9_#.%+-]", segment)
                )
        return result

    assert tokens(compact) == tokens(stylesheet)
    assert compact_stylesheet(compact) == compact


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (".a:hover, .b :focus { color: red; }", ".a:hover, .b :focus{color:red;}"),
        (
            ".a { --tone:  red; --empty: ; color: var(--tone); }",
            ".a{--tone: red;--empty: ;color:var(--tone);}",
        ),
        (
            "@supports (color: red) { @media (min-width: 2px) { .a { width: calc(1px +  2px); } } }",
            "@supports (color: red){@media (min-width: 2px){.a{width:calc(1px +  2px);}}}",
        ),
        (
            '.a { content: "a:  b"; background: url(data:x:a  b); /* a:  b */ color: red; }',
            '.a{content:"a:  b";background:url(data:x:a  b);/* a:  b */ color: red;}',
        ),
    ],
)
def test_declaration_separators_preserve_selectors_and_literal_boundaries(
    source: str,
    expected: str,
) -> None:
    from bijux_pollenomics.reporting.map_document.static_assets.stylesheet import (
        compact_stylesheet,
    )

    assert compact_stylesheet(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "a:hover, b:hover { color: rgba(1, 2, 3, 0.2); }",
            "a:hover, b:hover{color:rgba(1,2,3,0.2);}",
        ),
        (
            ".a { --palette: rgba(1, 2, 3, 0.2); background:linear-gradient( red , rgba(1, 2, 3, 0.2) , blue ); }",
            ".a{--palette: rgba(1, 2, 3, 0.2);background:linear-gradient(red,rgba(1,2,3,0.2),blue);}",
        ),
        (
            "@supports (color: rgba(1, 2, 3, 0.2)) { .a { color:rgba( calc(1 +  2), 3, 4, 0.2 ); } }",
            "@supports (color: rgba(1, 2, 3, 0.2)){.a{color:rgba(calc(1 +  2),3,4,0.2);}}",
        ),
        (
            '.a { background:linear-gradient("a , b", url("a , b"), var(--colors, red , blue), calc(1px +  2px)); }',
            '.a{background:linear-gradient("a , b",url("a , b"),var(--colors, red , blue),calc(1px +  2px));}',
        ),
        (
            ".a { background:linear-gradient(red, /* comma , spaces */  blue); }",
            ".a{background:linear-gradient(red,/* comma , spaces */  blue);}",
        ),
        (
            r".a { background:linear-gradient(\31 red,blue); }",
            r".a{background:linear-gradient(\31 red,blue);}",
        ),
    ],
)
def test_color_and_gradient_layout_preserves_nonlayout_tokens(
    source: str,
    expected: str,
) -> None:
    from bijux_pollenomics.reporting.map_document.static_assets.stylesheet import (
        compact_stylesheet,
    )

    assert compact_stylesheet(source) == expected
