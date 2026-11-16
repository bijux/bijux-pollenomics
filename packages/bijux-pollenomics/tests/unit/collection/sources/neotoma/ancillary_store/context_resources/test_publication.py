"""Literal portable sources retain capture claims and separate profile refusals."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.publication import ownership
from bijux_pollenomics.core.owned_tree import publish_new_output_tree

from .native_products import pin


def test_archive_retains_foreign_environment_forensic_and_modern_lake_shapes(
    site_context_products: Any, tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        load_neotoma_context_resource_archive,
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    manifest = write_neotoma_context_resource_archive(output, **inputs["writer"])
    assert manifest["capture_manifest_sha256"] == inputs["capture_sha256"]
    assert manifest["native_body_copies"] == 0
    assert {p.name: p.read_bytes() for p in inputs["capture"].iterdir()} == {
        p.name: p.read_bytes() for p in (output / "capture").iterdir()
    }
    result = load_neotoma_context_resource_archive(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        **inputs["reader"],
    )
    assert result["native_profile_partitions"] == {
        "refused_foreign_native_parent": 4,
        "qualified_modern_lake_candidates": 2,
        "qualified_empty_lake_candidate_query": 2,
    }
    assert result["scientific_admission"] == "not_asserted"


def test_late_stage_change_cannot_return_publication_success(
    site_context_products: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    actual = publish_new_output_tree

    def changed(**kwargs: Any) -> None:
        target = (
            kwargs["staging_output_root"]
            / "capture/site-12-lake_candidates-current-attempt-1.body"
        )
        target.write_bytes(b'{"foreign_stage":true}')
        actual(**kwargs)

    monkeypatch.setattr(ownership, "publish_new_output_tree", changed)
    with pytest.raises(ValueError):
        write_neotoma_context_resource_archive(output, **inputs["writer"])
    assert (
        output / "capture/site-12-lake_candidates-current-attempt-1.body"
    ).read_bytes() == b'{"foreign_stage":true}'
    assert (
        b"foreign_stage"
        not in (
            inputs["capture"] / "site-12-lake_candidates-current-attempt-1.body"
        ).read_bytes()
    )


def test_existing_destination_is_preserved(
    site_context_products: Any, tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    output.mkdir()
    (output / "foreign").write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        write_neotoma_context_resource_archive(output, **inputs["writer"])
    assert (output / "foreign").read_bytes() == b"preserve"
