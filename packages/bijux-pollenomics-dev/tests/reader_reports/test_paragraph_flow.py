"""Keep scientific operands intact while arranging long formulas and citations."""

from pathlib import Path

from bijux_pollenomics_dev.reader_reports.render import (
    ReportRenderer,
    _inline_code,
    escape_latex,
)


def renderer(tmp_path: Path) -> ReportRenderer:
    report = tmp_path / "reports/science/paper.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# Paper\n")
    return ReportRenderer(tmp_path, report, "a" * 40)


def test_compound_formula_gets_own_line_with_unchanged_function_and_operands(
    tmp_path: Path,
) -> None:
    value = "sum((sqrt(predicted) - sqrt(mapped))²) / 2"
    result = renderer(tmp_path).render(
        f"Prediction loss is `{value}`; all outcomes remain."
    )
    assert r"\linebreak[4]" + _inline_code(value) + r";\linebreak[4]" in result.latex
    assert "sum((sqrt(predicted)" in result.latex
    assert result.latex.replace(r"\linebreak[4]", "").replace(r"\allowbreak{}", "") == (
        "Prediction loss is "
        r"\texttt{" + escape_latex(value) + "}; all outcomes remain.\\par\n"
    )


def test_numeric_atom_is_never_fragmented_to_hide_overflow(tmp_path: Path) -> None:
    atom = "-1." + "1234567890" * 20 + "e-16"
    value = f"sqrt({atom})"
    result = renderer(tmp_path).render(f"Unbreakable operand: `{value}`.")
    assert value in result.latex
    assert r"\seqsplit" not in result.latex
    assert atom in result.latex


def test_evidence_citations_get_separate_paragraphs_without_removing_comma_or_url(
    tmp_path: Path,
) -> None:
    markdown = (
        "Retained evidence: [one](https://example.org/first), "
        "[two](https://example.org/second)."
    )
    result = renderer(tmp_path).render(markdown)
    assert r"{one}, \par\noindent\href{https://example.org/second}{two}" in result.latex
    assert result.external_link_count == 2
    ordinary = renderer(tmp_path).render(
        markdown.replace("Retained evidence:", "Read:")
    )
    assert r"}, \href" in ordinary.latex and r"\noindent" not in ordinary.latex


def test_heading_and_table_formulas_keep_inline_context(tmp_path: Path) -> None:
    value = "sum((sqrt(predicted) - sqrt(mapped))²) / 2"
    markdown = f"## `{value}`\n\n| Loss | Scope |\n| --- | --- |\n| `{value}` | conditional |\n"
    result = renderer(tmp_path).render(markdown)
    assert r"\linebreak[4]" not in result.latex
    assert result.latex.count(_inline_code(value)) == 2
