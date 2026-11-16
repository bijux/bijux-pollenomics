"""Current source relationships do not rewrite original global acquisitions."""

from hashlib import sha256
from pathlib import Path
from typing import Any


def test_later_occurrence_preserves_original_capture(
    association_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
    )

    products = association_products
    before = {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in products["legacy"].iterdir()
        if path.is_file()
    }
    document = build_neotoma_linked_associations(
        products["evidence"], inputs=products["inputs"]
    )
    assert document["summary"] == {
        "targets": 1,
        "current_occurrences": 2,
        "old_inline_occurrences": 1,
        "exact_old_current_overlaps": 1,
        "later_associations": 1,
    }
    row = document["targets"][0]
    assert row["capture_preget_scope"] == "not_recorded_legacy_capture"
    assert row["native_field_value_verified"] is False
    assert (
        row["retained_entity"]["capture_manifest_sha256"]
        == before["capture-manifest.json"]
    )
    assert before == {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in products["legacy"].iterdir()
        if path.is_file()
    }


def test_projection_opens_no_native_entity_buffers(
    association_products: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
    )

    p = association_products
    opened = []
    original = Path.open

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and p["capsule"] in path.parents:
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    result = build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    assert result["summary"]["later_associations"] == 1
    assert opened == []
