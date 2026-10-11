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


@pytest.mark.parametrize(
    "profile",
    ["synthetic-withheld-site-baselines-v1", "synthetic-forward-time-persistence-v1"],
)
def test_phase_publication_reopens_and_never_overwrites(
    tmp_path: Path, profile: str
) -> None:
    target = tmp_path / "product"
    stage = stage_directory(target)
    write_json(stage, "predictions.json", [])
    product = publish_phase(
        stage,
        target,
        phase="predictions",
        scientific={"predictions": []},
        profile=profile,
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


@pytest.mark.parametrize(
    "name", ["batches/fold-0000/receipt.json", "batches/fold-0000/manifest.json"]
)
def test_owned_nested_json_members_are_read_after_inventory_admission(
    tmp_path: Path, name: str
) -> None:
    stage = stage_directory(tmp_path / "product")
    member = stage / name
    member.parent.mkdir(parents=True)
    member.write_text('{"status":"retained"}\n')
    product = publish_phase(
        stage, tmp_path / "product", phase="predictions", scientific={}
    )
    assert read_member(product, name) == {"status": "retained"}


@pytest.mark.parametrize(
    "name",
    [
        "/tmp/outside.json",
        "../outside.json",
        "batches/../receipt.json",
        "./receipt.json",
        "batches//receipt.json",
        "manifest.json",
        "unlisted.json",
        "batches/receipt.json/",
    ],
)
def test_member_names_must_be_normalized_inventoried_relative_json(
    tmp_path: Path, name: str
) -> None:
    stage = stage_directory(tmp_path / "product")
    product = publish_phase(
        stage, tmp_path / "product", phase="predictions", scientific={}
    )
    with pytest.raises(ValidationRefusal):
        read_member(product, name)


@pytest.mark.parametrize(
    "mutation", ["symlink", "duplicate_key", "changed_during_read"]
)
def test_nested_members_refuse_links_ambiguous_json_and_read_races(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    stage = stage_directory(tmp_path / "product")
    (stage / "batches").mkdir()
    member = stage / "batches" / "receipt.json"
    member.write_text(
        '{"value":1,"value":2}\n' if mutation == "duplicate_key" else '{"value":1}\n'
    )
    product = publish_phase(
        stage, tmp_path / "product", phase="predictions", scientific={}
    )
    member = product.directory / "batches" / "receipt.json"
    if mutation == "symlink":
        member.unlink()
        member.symlink_to(product.directory / "manifest.json")
    elif mutation == "changed_during_read":
        original = Path.read_bytes
        reads = 0

        def changed(path: Path) -> bytes:
            nonlocal reads
            result = original(path)
            if path == member:
                reads += 1
                if reads == 2:
                    member.write_text('{"value":2}\n')
            return result

        monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(ValidationRefusal):
        read_member(product, "batches/receipt.json")
