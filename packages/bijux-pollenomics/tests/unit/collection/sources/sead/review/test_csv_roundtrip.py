import csv
import io
import json

from bijux_pollenomics.collection.sources.sead.review.publication import (
    render_review_csv,
)


def test_review_csv_roundtrips_lists_and_literal_controls() -> None:
    rows = [
        {
            "id": 7,
            "labels": ["oak, ash", '"pine"', "å"],
            "text": "a,b\r\nc\rd\ne",
            "plain": None,
        },
        {"id": 8, "labels": [], "text": "=literal", "plain": "unchanged"},
    ]
    output = render_review_csv(rows)
    parsed = list(csv.DictReader(io.StringIO(output, newline="")))
    assert parsed == [
        {
            "id": "7",
            "labels": json.dumps(rows[0]["labels"], ensure_ascii=False),
            "text": rows[0]["text"],
            "plain": "None",
        },
        {"id": "8", "labels": "[]", "text": "=literal", "plain": "unchanged"},
    ]
    assert render_review_csv(rows) == output
    assert output.endswith("\n")


def test_review_csv_handles_special_header_and_empty_rows() -> None:
    assert render_review_csv([]) == "row_count\n"
    rows: list[dict[str, object]] = [
        {'header,\r"\n': "single\rcarriage", "other": "ok"}
    ]
    assert (
        list(csv.DictReader(io.StringIO(render_review_csv(rows), newline=""))) == rows
    )
