"""Retain immediate scientific formula punctuation on its dedicated line."""

from pathlib import Path

import pytest

from bijux_pollenomics_dev.reader_reports.render import ReportRenderer, _inline_code


def renderer(tmp_path: Path) -> ReportRenderer:
    report = tmp_path / "reports/science/paper.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# Paper\n")
    return ReportRenderer(tmp_path, report, "a" * 40)


@pytest.mark.parametrize("punctuation", [",", ".", ";", ":", "!", "?"])
def test_immediate_punctuation_precedes_formula_line_break(
    tmp_path: Path, punctuation: str
) -> None:
    formula = "sum((sqrt(predicted) - sqrt(mapped))²) / 2"
    result = renderer(tmp_path).render(
        f"Loss is `{formula}`{punctuation} Following prose."
    )
    assert (
        _inline_code(formula) + punctuation + r"\linebreak[4] Following" in result.latex
    )
    assert r"\linebreak[4]" + punctuation not in result.latex
    assert result.latex.replace(r"\linebreak[4]", "") == (
        "Loss is " + _inline_code(formula) + punctuation + " Following prose.\\par\n"
    )


@pytest.mark.parametrize(
    ("formula", "continuation"),
    [
        (
            "sqrt(sum((sqrt(p_i) - sqrt(v_i))²) / 2)",
            ", with p the conditional composition.",
        ),
        (
            "sum((sqrt(predicted) - sqrt(mapped))²) / 2",
            ". This prediction loss differs.",
        ),
    ],
)
def test_actual_namibia_formula_continuations_keep_punctuation_with_formula(
    tmp_path: Path, formula: str, continuation: str
) -> None:
    result = renderer(tmp_path).render(f"The calculation is `{formula}`{continuation}")
    assert _inline_code(formula) + continuation[0] + r"\linebreak[4]" in result.latex
    assert result.latex.replace(r"\linebreak[4]", "") == (
        "The calculation is " + _inline_code(formula) + continuation + "\\par\n"
    )
