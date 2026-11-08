"""Source provenance remains literal in the supported seven-column Markdown table."""

from __future__ import annotations

from html.parser import HTMLParser

from markdown_it import MarkdownIt
import pytest

from bijux_pollenomics.adna.projects.evidence.chronology.rendering import (
    _render_sample_chronology_provenance_markdown,
)


class TableCells(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self.row: list[str] = []
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.row = []
        elif tag in {"td", "th"}:
            self.cell = []
        elif tag == "br" and self.cell is not None:
            self.cell.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"}:
            assert self.cell is not None
            self.row.append("".join(self.cell))
            self.cell = None
        elif tag == "tr":
            self.rows.append(self.row)

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)


@pytest.mark.parametrize(
    "value",
    [
        "a | b || c",
        r"a\|b",
        r"a\\|b",
        "a\nb",
        "a\r\nb",
        "a\rb",
        "trailing\\",
        "**literal** _source_ `code` [name](url)",
        "literal <br> &nbsp; <em>source</em>",
    ],
)
def test_every_provenance_cell_round_trips_as_literal_text(value: str) -> None:
    fields = (
        "project_accession",
        "repo_stable_sample_id",
        "published_wording",
        "provenance_surface",
        "provenance_locator",
        "normalization_rule",
        "uncertainty_note",
    )
    row = dict.fromkeys(fields, value)
    markdown = _render_sample_chronology_provenance_markdown([row])
    parser = TableCells()
    parser.feed(MarkdownIt("commonmark").enable("table").render(markdown))
    assert len(parser.rows) == 2
    assert [len(cells) for cells in parser.rows] == [7, 7]
    expected = value.replace("\r\n", "\n").replace("\r", "\n")
    assert parser.rows[1] == [expected] * 7
    assert row == dict.fromkeys(fields, value)


def test_empty_provenance_retains_the_owned_no_packets_message() -> None:
    markdown = _render_sample_chronology_provenance_markdown([])
    assert "No chronology provenance packets are currently published." in markdown
    assert "| Project accession" not in markdown
