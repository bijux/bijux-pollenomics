"""Published inventories refuse changed bytes, links and overwrites."""

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    publish_phase,
    read_experiment_product,
    read_member,
    stage_directory,
    write_json,
)


def test_phase_publication_reopens_and_never_overwrites(tmp_path: Path) -> None:
    target = tmp_path / "product"
    stage = stage_directory(target)
    write_json(stage, "predictions.json", [])
    product = publish_phase(
        stage, target, phase="predictions", scientific={"predictions": []}
    )
    reopened, manifest = read_experiment_product(
        target, expected_manifest_sha256=product.manifest_sha256
    )
    assert reopened == product
    assert manifest["scientific_acceptance"] == "not_evaluated"
    assert read_member(product, "predictions.json") == []
    with pytest.raises(ValidationRefusal):
        stage_directory(target)
    (target / "predictions.json").write_text("[1]\n")
    with pytest.raises(ValidationRefusal):
        read_member(product, "predictions.json")


@pytest.mark.parametrize("mutation", ["unlisted", "symlink", "manifest"])
def test_inventory_closes_all_product_bytes(tmp_path: Path, mutation: str) -> None:
    target = tmp_path / "product"
    stage = stage_directory(target)
    write_json(stage, "predictions.json", [])
    product = publish_phase(stage, target, phase="predictions", scientific={})
    if mutation == "unlisted":
        (target / "hidden").write_text("extra")
    elif mutation == "symlink":
        (target / "linked").symlink_to(target / "predictions.json")
    else:
        (target / "manifest.json").write_text("{}")
    with pytest.raises(ValidationRefusal):
        read_experiment_product(
            target, expected_manifest_sha256=product.manifest_sha256
        )
