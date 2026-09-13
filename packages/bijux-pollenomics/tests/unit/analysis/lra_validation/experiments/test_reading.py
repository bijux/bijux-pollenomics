"""The public retained reader preserves singleton keys and owned copies."""

from pathlib import Path

from bijux_pollenomics.analysis.lra_validation.experiments import (
    read_withheld_predictions,
)

from .test_scoring import prediction_product


def test_retained_reader_extraction_preserves_public_key_shape(tmp_path: Path) -> None:
    product, _ = prediction_product(tmp_path)
    _, _, folds, rows, methods = read_withheld_predictions(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    assert len(rows) == len(folds) * len(methods)
    assert all(len(key) == 2 for key in rows)
