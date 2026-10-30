"""Controlled exact-depth and all-reported-pair preconditions for source support."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_source_counts.comparison import (
    compare_tables,
    scaled_depth,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_source_counts.sources import (
    OriginalTable,
    read_native,
    read_original,
)

from .test_sources import native_document, original_text


def test_complete_depth_and_reported_count_match_exposes_only_source_literal() -> None:
    original = read_original(
        original_text(
            [("6.50", "1", "2", "3", "4", "5"), ("6.52", "2", "3", "4", "5", "0")]
        )
    )
    result = compare_tables(
        original,
        read_native(native_document()),
        expected_samples=2,
        expected_reported=9,
    )
    assert result["status"] == "reported_counts_match"
    assert result["comparison"]["total_slots"] == 10
    assert result["comparison"]["reported_count_matches"] == 9
    assert result["comparison"]["native_absent_slots"] == 1
    assert result["absence_candidates"][0]["original_status"] == "explicit_zero"
    assert result["absence_candidates"][0]["native_value"] is None
    assert result["absence_candidates"][0]["native_sample_id"] == 20


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("0", "explicit_zero"),
        ("7", "explicit_positive_integer"),
        ("", "blank"),
        ("0.5", "invalid"),
    ],
)
def test_absent_native_measurement_retains_every_original_state(
    token: str, expected: str
) -> None:
    text = original_text(
        [("6.50", "1", "2", "3", "4", "5"), ("6.52", "2", "3", "4", "5", token)]
    )
    result = compare_tables(read_original(text), read_native(native_document()))
    assert result["absence_candidates"][0]["original_token"] == token
    assert result["absence_candidates"][0]["original_status"] == expected


def test_one_reported_disagreement_blocks_all_absence_candidate_conclusions() -> None:
    text = original_text(
        [("6.50", "99", "2", "3", "4", "5"), ("6.52", "2", "3", "4", "5", "0")]
    )
    result = compare_tables(read_original(text), read_native(native_document()))
    assert result["status"] == "refused_reported_count_correspondence"
    assert result["comparison"]["reported_count_matches"] == 8
    assert result["comparison"]["reported_count_disagreements"] == 1
    assert result["absence_candidates"] == []
    assert (
        result["candidate_classification_status"] == "withheld_reported_count_conflict"
    )


@pytest.mark.parametrize("side", ["original", "native", "unmatched", "population"])
def test_ambiguous_or_incomplete_depth_axes_refuse(side: str) -> None:
    original = read_original(
        original_text(
            [("6.50", "1", "2", "3", "4", "5"), ("6.52", "2", "3", "4", "5", "0")]
        )
    )
    native = read_native(native_document())
    if side == "original":
        original = OriginalTable(
            original.columns,
            (original.rows[0], replace(original.rows[1], depth_m=Decimal("6.50"))),
        )
    elif side == "native":
        native = (native[0], replace(native[1], depth=Decimal(650)))
    elif side == "unmatched":
        native = (native[0], replace(native[1], depth=Decimal(651)))
    result = compare_tables(
        original, native, expected_samples=3 if side == "population" else 2
    )
    assert result["status"] == "refused_depth_binding"
    assert result["comparison"] is None and result["absence_candidates"] == []


def test_decimal_depth_scaling_preserves_more_than_default_context_precision() -> None:
    assert scaled_depth(Decimal("0." + "1" * 50)) == Decimal("11." + "1" * 48)


def test_row_reordering_is_visible_without_changing_the_exact_scientific_join() -> None:
    original = read_original(
        original_text(
            [("6.52", "2", "3", "4", "5", "0"), ("6.50", "1", "2", "3", "4", "5")]
        )
    )
    result = compare_tables(original, tuple(reversed(read_native(native_document()))))
    assert result["status"] == "reported_counts_match"
    assert result["depth_binding"]["original_order_strictly_increasing"] is False
    assert result["depth_binding"]["native_order_strictly_increasing"] is False


@pytest.mark.parametrize(
    "mutation",
    [None, "original.tsv", "native.json", "metadata.json", "protocol", "HEAD"],
)
def test_mutable_consumed_inputs_refuse_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str | None,
) -> None:
    """Mutate only controlled artifacts after authentication, never repository Git."""
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_source_counts import (
        comparison,
    )
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_source_counts.sources import (
        AXES,
    )

    repository = tmp_path / "repository"
    source = tmp_path / "source"
    source.mkdir()
    package = repository / "package"
    package.mkdir(parents=True)
    for filename in ("sources.py", "comparison.py", "__main__.py"):
        (package / filename).write_text("# Controlled source guard fixture.\n")
    monkeypatch.setattr(comparison, "__file__", str(package / "comparison.py"))
    inputs = {
        "original.tsv": b"controlled-original",
        "native.json": b"{}",
        "metadata.json": b"{}",
    }
    for filename, body in inputs.items():
        (source / filename).write_bytes(body)
    protocol_path = repository / comparison.PROTOCOL
    protocol_path.parent.mkdir(parents=True)
    protocol = {
        "axis_fields": [
            {
                "taxon": a.name,
                "original_column": a.column,
                "original_epd_comment": a.epd_comment,
                "native_taxon_id": a.native_id,
            }
            for a in AXES
        ],
        "join": {"required_original_rows": 107, "required_native_samples": 107},
        "count_comparison": {
            "required_reported_pairs": 527,
            "all_slots": 535,
            "expected_absent_native_slots": 8,
        },
        "original_table": "original.tsv",
        "current_native": "native.json",
        "source_store_files": {
            name: {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
            for name, body in inputs.items()
        },
    }
    protocol_path.write_text(json.dumps(protocol))
    revision = ["a" * 40]
    monkeypatch.setattr(
        comparison,
        "subprocess",
        SimpleNamespace(
            check_output=lambda *a, **kw: revision[0], run=lambda *a, **kw: None
        ),
    )
    monkeypatch.setattr(
        comparison,
        "read_original",
        lambda text: OriginalTable(tuple(map(str, range(95))), ()),
    )
    monkeypatch.setattr(comparison, "read_native", lambda document: ())

    def controlled_comparison(*args: Any, **kwargs: Any) -> dict[str, Any]:
        if mutation in inputs:
            (source / str(mutation)).write_bytes(inputs[str(mutation)] + b" ")
        elif mutation == "protocol":
            protocol_path.write_text(protocol_path.read_text() + "\n")
        elif mutation == "HEAD":
            revision[0] = "b" * 40
        return {"status": "controlled_source_guard"}

    monkeypatch.setattr(comparison, "compare_tables", controlled_comparison)
    output = repository / "artifacts" / "result.json"
    if mutation is None:
        assert (
            comparison.run(repository, source, output)["status"]
            == "controlled_source_guard"
        )
        assert output.is_file()
    else:
        with pytest.raises(ValueError, match="changed during comparison"):
            comparison.run(repository, source, output)
        assert not output.exists()
