"""Other cohorts' numerical payloads remain opaque during selected-core access."""

from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.source_reading import (
    read_dataset,
)


def test_only_selected_dataset_is_numerically_decoded(tmp_path: Path) -> None:
    p = tmp_path / "part.json"
    p.write_bytes(
        b'{"rows":[{"site":{"dataset":{"datasetid":99},"samples":[{"value":DO_NOT_DECODE}]}},{"site":{"dataset":{"datasetid":54001},"samples":[{"value":3,"note":"quoted } and \\" brace"}]}}]}'
    )
    result = read_dataset(p, 54001)
    assert len(result["rows"]) == 1
    assert result["rows"][0]["site"]["samples"][0]["value"] == 3


@pytest.mark.parametrize(
    "rows",
    [
        b"",
        b'{"site":{"dataset":{"datasetid":99},"samples":[]}}',
        b'{"site":{"dataset":{"datasetid":54001},"samples":[]}}, {"site":{"dataset":{"datasetid":54001},"samples":[]}}',
    ],
)
def test_missing_or_duplicate_selected_dataset_refuses(
    tmp_path: Path, rows: bytes
) -> None:
    p = tmp_path / "part.json"
    p.write_bytes(b'{"rows":[' + rows + b"]}")
    with pytest.raises(ValueError, match="selected dataset"):
        read_dataset(p, 54001)


def test_related_dataset_id_cannot_expose_another_sites_values(tmp_path: Path) -> None:
    p = tmp_path / "part.json"
    p.write_bytes(
        b'{"rows":[{"related":{"datasetid":54001},"site":{"dataset":{"datasetid":99},"samples":[{"value":DO_NOT_DECODE}]}},{"site":{"dataset":{"datasetid":54001},"samples":[]}}]}'
    )
    assert read_dataset(p, 54001)["rows"][0]["site"]["dataset"]["datasetid"] == 54001
