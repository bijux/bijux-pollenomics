from pathlib import Path

from bijux_pollenomics_dev.source_completion.swedish_direct_pollen import _write_csv


def test_report_tables_use_lf_line_endings(tmp_path: Path) -> None:
    destination = tmp_path / "table.csv"

    _write_csv(destination, ["label", "count"], [{"label": "Alnus", "count": 2}])

    assert destination.read_bytes() == b"label,count\nAlnus,2\n"
