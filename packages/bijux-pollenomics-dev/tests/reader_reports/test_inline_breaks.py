"""Keep numerical operands and safe escaping intact while breaking compound code."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[4]


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "bijux_pollenomics_dev.reader_reports.render",
        ROOT
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/render.py",
    )
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def test_long_compound_expression_breaks_after_closed_operands() -> None:
    api = module()
    value = "sum((sqrt(predicted) - sqrt(mapped))²) / 2"
    rendered: str = api._inline_code(value)
    assert r"(\allowbreak{}" not in rendered and r")\allowbreak{}" in rendered
    assert (
        rendered.replace(r"\allowbreak{}", "")
        == r"\texttt{" + api.escape_latex(value) + "}"
    )
    assert "predicted" in rendered and "mapped" in rendered and "²" in rendered


@pytest.mark.parametrize(
    "atom",
    [
        "1.234567890123456789012345678901e-12",
        "-1.234567890123456789012345678901e+12",
        "0.000000000000000000000000000001",
        "1e-12",
    ],
)
def test_compound_code_keeps_long_and_short_numeric_atoms_unsplit(atom: str) -> None:
    api = module()
    value = f"sqrt({atom}) / denominator"
    rendered: str = api._inline_code(value)
    assert atom in rendered
    assert (
        rendered.replace(r"\allowbreak{}", "")
        == r"\texttt{" + api.escape_latex(value) + "}"
    )
    assert r"\seqsplit" not in rendered


def test_plain_source_paths_get_delimiter_breaks_and_prose_numbers_remain_atomic() -> (
    None
):
    api = module()
    value = "reports/science/publication-correspondence/author-example-site-replay.md"
    rendered: str = api._inline_text(value)
    assert r"-\allowbreak{}" in rendered
    assert rendered.replace(r"\allowbreak{}", "") == api.escape_latex(value)
    prose = "The source-bound estimate is -1e-12, with 2007a citation and 0.10518 percentage points."
    assert api._inline_text(prose) == api.escape_latex(prose)


def test_path_delimiters_and_compound_code_keep_tex_metacharacters_escaped() -> None:
    api = module()
    path = r"reports/science/source_hash-{x}.md"
    rendered: str = api._inline_text(path)
    assert rendered.replace(r"\allowbreak{}", "") == api.escape_latex(path)
    expression = r"sqrt(\input{unexpected}) / source_hash"
    code: str = api._inline_code(expression)
    assert r"\input{" not in code
    assert r"\textbackslash{}input\{unexpected\}" in code
    assert (
        code.replace(r"\allowbreak{}", "")
        == r"\texttt{" + api.escape_latex(expression) + "}"
    )


@pytest.mark.parametrize(
    "value", ["-1.0/-2.0", "-1.0e-12/-2.0e+12", "0.123/-0.456", "-1.0/-2.0,"]
)
def test_numeric_ratios_gain_only_existing_slash_breaks(value: str) -> None:
    api = module()
    assert api._inline_text(value) == api.escape_latex(value).replace(
        "/", r"/\allowbreak{}"
    )
    assert r"-\allowbreak{}" not in api._inline_text(value)


def test_terminal_path_extension_allows_normal_sentence_punctuation() -> None:
    api = module()
    value = "docs/report/source_hash/source-account.json)."
    result: str = api._inline_text(value)
    assert r"-\allowbreak{}" in result and r"\_\allowbreak{}" in result
    assert result.replace(r"\allowbreak{}", "") == api.escape_latex(value)
