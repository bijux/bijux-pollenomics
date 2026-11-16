"""Selected graph metadata never grants native-body or strongest-current authority."""

from pathlib import Path
from typing import Any

import pytest

from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)

from .native_products import capture_parent, publish_chain


def test_selected_chain_edges_are_recorded_metadata_not_body_authority(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        read_neotoma_taxon_chain_target,
    )

    sources, capture = capture_parent(chain_products, tmp_path / "detail")
    sources, pin, _ = publish_chain(
        tmp_path / "delta", sources=sources, captures=(capture,)
    )
    original, opened = capture_opening(), []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            opened.append(path)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    result = read_neotoma_taxon_chain_target(
        tmp_path / "delta",
        expected_manifest_sha256=pin,
        kind="taxon",
        native_id=16,
        chain_sources={
            **sources.chain_sources,
            chain_products["baseline_sha256"]: chain_products["baseline"],
        },
    )
    assert opened == []
    assert result["current_roles_revalidated"] is False
    assert result["native_source_fields_revalidated"] is False
    assert result["GET_authorized"] is False
    assert all(
        row["native_field_value_verified"] is False for row in result["recorded_edges"]
    )


@pytest.mark.parametrize("alias", ["directory", "leaf"])
def test_selected_part_alias_refuses_before_actual_descriptor_open(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, alias: str
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        read_neotoma_taxon_chain_target,
    )

    from .native_products import observe_native_body_opens

    sources, capture = capture_parent(chain_products, tmp_path / "detail")
    sources, pin, _ = publish_chain(
        tmp_path / "delta", sources=sources, captures=(capture,)
    )
    manifest = json.loads((tmp_path / "delta/manifest.json").read_bytes())
    part = next(row for row in manifest["parts"] if row["collection"] == "taxa")
    path = tmp_path / "delta" / part["path"]
    selected = path.parent if alias == "directory" else path
    foreign = tmp_path / "foreign-part"
    selected.rename(foreign)
    selected.symlink_to(foreign, target_is_directory=alias == "directory")
    opened = observe_native_body_opens(monkeypatch, path.name)
    with pytest.raises(ValueError, match="symlink"):
        read_neotoma_taxon_chain_target(
            tmp_path / "delta",
            expected_manifest_sha256=pin,
            kind="taxon",
            native_id=16,
            chain_sources={
                **sources.chain_sources,
                chain_products["baseline_sha256"]: chain_products["baseline"],
            },
        )
    assert opened == [] and foreign.exists()
