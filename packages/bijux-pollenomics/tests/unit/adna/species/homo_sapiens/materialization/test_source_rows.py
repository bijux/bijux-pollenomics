"""Lossless AADR source-row loading tests."""

from hashlib import sha256
from pathlib import Path

import pytest

from bijux_pollenomics.adna.species.homo_sapiens.materialization import (
    load_aadr_source_table,
)

_HEADER = "\t".join(
    (
        "Genetic ID (source annotation)",
        "Method for Determining Date; source policy",
        "Date mean in BP in years before 1950 CE",
        "Date standard deviation in BP",
        "Full Date One of two formats",
        "Latitude",
        "Longitude",
        "Unmodeled Source Field",
    )
)


def _write_source(path: Path, data_rows: list[str]) -> bytes:
    source_bytes = (_HEADER + "\n" + "\n".join(data_rows) + "\n").encode()
    path.write_bytes(source_bytes)
    return source_bytes


def test_loader_preserves_every_row_raw_tokens_and_source_identity(
    tmp_path: Path,
) -> None:
    path = tmp_path / "panel.anno"
    source_bytes = _write_source(
        path,
        [
            " ID-1 \tDirect (AMS)\t100\t20\t120-80 BP\t0\t0\t  source text  ",
            "ID-1\tContext\tunknown\t\tarchaeological range\t\t\tsecond",
            "\tOther\t\t\t\tbad\t18\tthird\textra-token",
            "",
        ],
    )

    table = load_aadr_source_table(
        path,
        source_release="v66",
        dataset_name="ho",
        expected_sha256=sha256(source_bytes).hexdigest(),
    )

    assert table.source.source_path == str(path)
    assert table.source.source_sha256 == sha256(source_bytes).hexdigest()
    assert table.source.source_byte_count == len(source_bytes)
    assert len(table.rows) == 4
    assert [row.source_record_number for row in table.rows] == [1, 2, 3, 4]
    first, second, third, blank = table.rows
    assert first.genetic_id_raw == " ID-1 "
    assert first.raw_value("Unmodeled Source Field") == "  source text  "
    assert first.coordinates.latitude == 0.0
    assert first.coordinates.longitude == 0.0
    assert first.chronology.date_mean_bp_raw == "100"
    assert first.chronology.date_stddev_bp_raw == "20"
    assert first.chronology.full_date_raw == "120-80 BP"
    assert first.chronology.evaluation_status == "not_evaluated"
    assert second.coordinates.status == "missing"
    assert second.chronology.date_mean_bp_raw == "unknown"
    assert third.genetic_id_raw == ""
    assert third.coordinates.status == "invalid_numeric"
    assert third.unmatched_raw_tokens == ("extra-token",)
    assert blank.raw_tokens == ()
    assert blank.coordinates.status == "missing"
    assert all(row.taxon_scope_status == "not_asserted_by_source" for row in table.rows)
    assert all(row.source is table.source for row in table.rows)


def test_loader_does_not_assert_species_membership(tmp_path: Path) -> None:
    path = tmp_path / "panel.anno"
    _write_source(path, ["ID-1\tModern\t0\t0\tmodern\t59\t18\tvalue"])

    [row] = load_aadr_source_table(
        path, source_release="v66", dataset_name="1240k"
    ).rows

    assert row.taxon_scope_status == "not_asserted_by_source"
    assert not hasattr(row, "species_latin_name")
    assert not hasattr(row, "taxon_name")


def test_loader_preserves_short_rows_instead_of_dropping_them(tmp_path: Path) -> None:
    path = tmp_path / "panel.anno"
    _write_source(path, ["ID-only"])

    [row] = load_aadr_source_table(path, source_release="v66", dataset_name="ho").rows

    assert row.raw_tokens == ("ID-only",)
    assert row.genetic_id_raw == "ID-only"
    assert row.coordinates.status == "missing"
    assert row.chronology.evaluation_status == "not_evaluated"


def test_loader_refuses_a_source_digest_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "panel.anno"
    _write_source(path, ["ID-1"])

    with pytest.raises(ValueError, match="source digest mismatch"):
        load_aadr_source_table(
            path,
            source_release="v66",
            dataset_name="ho",
            expected_sha256="0" * 64,
        )


def test_loader_refuses_ambiguous_source_columns(tmp_path: Path) -> None:
    path = tmp_path / "panel.anno"
    path.write_text("Latitude\tLatitude\n59\t18\n", encoding="utf-8")

    with pytest.raises(ValueError, match="source columns are ambiguous"):
        load_aadr_source_table(
            path,
            source_release="v66",
            dataset_name="ho",
        )
