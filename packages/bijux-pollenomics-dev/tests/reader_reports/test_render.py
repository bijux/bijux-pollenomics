from pathlib import Path

import pytest

from bijux_pollenomics_dev.reader_reports.diagram import DiagramError, mermaid_to_dot
from bijux_pollenomics_dev.reader_reports.render import (
    ReportRenderer,
    RenderError,
    _inline_code,
    document_latex,
    escape_latex,
)
from bijux_pollenomics_dev.reader_reports.source import SourceError


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repository"
    (root / "reports" / "science").mkdir(parents=True)
    (root / "docs" / "report").mkdir(parents=True)
    (root / "docs" / "report" / "evidence.csv").write_text(
        "a,b\n1,2\n", encoding="utf-8"
    )
    report = root / "reports" / "science" / "paper.md"
    report.write_text("# Paper\n", encoding="utf-8")
    return root, report


def test_render_keeps_unicode_table_links_and_code_without_latex_execution(
    tmp_path: Path,
) -> None:
    root, report = _repository(tmp_path)
    source = r"""# A 1° account

Skåne **α** and `x_y` cite [data](../../docs/report/evidence.csv) and
[publisher](https://example.org/paper?q=a%20b&view=1). \input{outside}

| Denominator | Status |
| --- | --- |
| 1,128 sites | **Open**: 0/1,128 |

```sh
printf '\end{Verbatim}\input{outside}'
```
"""
    result = ReportRenderer(root, report, "a" * 40).render(source)
    assert "Skåne" in result.latex
    assert r"\textbf{α}" in result.latex
    assert r"\texttt{x\_y}" in result.latex
    assert r"\textbackslash{}input\{outside\}" in result.latex
    assert "https://github.com/bijux/bijux-pollenomics/blob/" in result.latex
    assert "docs/report/evidence.csv" in result.latex
    assert r"\begin{longtable}" in result.latex
    assert "1,128 sites" in result.latex
    assert result.assets[0].kind == "code"
    assert r"\end{Verbatim}\input{outside}" in result.assets[0].content
    assert r"\VerbatimInput" in result.latex
    assert result.local_link_count == 1
    assert result.external_link_count == 1


def test_unsupported_markdown_and_unsafe_links_refuse(tmp_path: Path) -> None:
    root, report = _repository(tmp_path)
    for content in ("<script>unsafe</script>", "![missing](x.png)"):
        with pytest.raises(RenderError):
            ReportRenderer(root, report, "a" * 40).render(content)
    blocked = ReportRenderer(root, report, "a" * 40).render(
        "[bad](javascript:alert(1))"
    )
    assert "javascript" in blocked.latex
    assert "\\href{" not in blocked.latex
    with pytest.raises(SourceError):
        ReportRenderer(root, report, "a" * 40).render("[bad](../../../../outside.txt)")


def test_mermaid_subset_retains_nodes_edges_and_label_but_refuses_extensions() -> None:
    dot = mermaid_to_dot(
        'flowchart LR\nA["Regional 31-taxon count"] --> B["Cover"]\n'
        'B -. "requires validation" .-> C["Claim"]\n'
    )
    assert "rankdir=TB" in dot
    assert 'B -> C [style=dashed, label="requires validation"]' in dot
    assert "Regional 31-taxon count" in dot
    for content in (
        "flowchart LR\nA --> B\nclassDef bad fill:red",
        "graph TD\nA --> B",
        'flowchart LR\nA["first"] --> B\nA["other"] --> C',
    ):
        with pytest.raises(DiagramError):
            mermaid_to_dot(content)


def test_latex_escaper_covers_command_and_alignment_characters() -> None:
    assert escape_latex(r"\input{bad}_x & 90%") == (
        r"\textbackslash{}input\{bad\}\_x \& 90\%"
    )
    assert r"\allowbreak{}" in _inline_code("1013.872200/26255.796823=0.038615175416")
    assert r"\seqsplit{" in _inline_code("a" * 64)


def test_numbered_steps_keep_their_declared_start(tmp_path: Path) -> None:
    root, report = _repository(tmp_path)
    result = ReportRenderer(root, report, "a" * 40).render(
        "3. Acquire lawful input\n4. Verify source\n"
    )
    assert r"\setcounter{enumi}{2}" in result.latex
    assert "Acquire lawful input" in result.latex


def test_export_identity_note_precedes_content_instead_of_orphan_endpage() -> None:
    document = document_latex("CANONICAL BODY", "Title", "paper.md", "a" * 64)
    assert document.index("Source SHA-256") < document.index("CANONICAL BODY")
    assert document.count("Source SHA-256") == 1


def test_flowchart_label_can_follow_first_unlabelled_reference() -> None:
    dot = mermaid_to_dot('flowchart LR\nA --> B\nB["Cover"] --> C')
    assert 'B [label="Cover"]' in dot
