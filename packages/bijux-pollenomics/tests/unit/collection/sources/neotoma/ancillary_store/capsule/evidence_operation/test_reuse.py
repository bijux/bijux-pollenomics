"""Evidence reuse never replaces independent preparations or selected source reads."""

from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
    write_neotoma_ancillary_capsule,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule.validation import (
    prepare_capsule,
)

from .native_products import observe


def test_twenty_four_captures_share_one_complete_evidence_validation(
    linked_inputs: dict[str, Any], monkeypatch: Any
) -> None:
    work = observe(monkeypatch)
    manifest, _, _, index = prepare_capsule(**linked_inputs)
    assert len(manifest["captures"]) == 24
    assert len(index["observations"]) == 24
    assert work["detail_body_opens"] == 24
    assert work["complete_validations"] == 1


def test_publisher_keeps_three_independent_complete_evidence_operations(
    linked_inputs: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    work = observe(monkeypatch)
    manifest = write_neotoma_ancillary_capsule(tmp_path / "published", **linked_inputs)
    assert len(manifest["captures"]) == 24
    assert work["detail_body_opens"] >= 96
    assert work["complete_validations"] == 3
