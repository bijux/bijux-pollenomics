"""Association publication is anchored to its source projection."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest


def test_writer_refuses_fabricated_later_count(
    association_products: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        publish_neotoma_linked_associations,
    )

    p = association_products
    document = deepcopy(
        build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    )
    document["summary"]["later_associations"] = 99
    with pytest.raises(ValueError, match="projection"):
        publish_neotoma_linked_associations(
            tmp_path / "associations",
            document=document,
            evidence=p["evidence"],
            inputs=p["inputs"],
        )


@pytest.mark.parametrize(
    "mutation", ["role", "receipt", "utc", "proof_range", "preget", "native_claim"]
)
def test_source_projection_refuses_rehashed_metadata_claims(
    association_products: dict[str, Any], tmp_path: Path, mutation: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        publish_neotoma_linked_associations,
    )

    p = association_products
    document = build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    row = document["targets"][0]
    if mutation == "role":
        row["current_use_role"] = "heldout_no_numerical_access"
    elif mutation == "receipt":
        row["retained_entity"]["receipt_sha256"] = "0" * 64
    elif mutation == "utc":
        row["retained_entity"]["utc_end"] = "1900-01-01T00:00:00+00:00"
    elif mutation == "proof_range":
        row["source_proof_reference"]["proof_ranges"][0]["count"] = 900
    elif mutation == "preget":
        row["capture_preget_scope"] = "authenticated_source_inputs"
    else:
        row["native_field_value_verified"] = True
    with pytest.raises(ValueError, match="projection"):
        publish_neotoma_linked_associations(
            tmp_path / "refused",
            document=document,
            evidence=p["evidence"],
            inputs=p["inputs"],
        )
    assert not (tmp_path / "refused").exists()


def test_published_loader_rederives_all_claims(
    association_products: dict[str, Any], tmp_path: Path
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        load_neotoma_linked_associations,
        publish_neotoma_linked_associations,
    )

    from .native_products import pin

    p = association_products
    document = build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    root = tmp_path / "published"
    publish_neotoma_linked_associations(
        root, document=document, evidence=p["evidence"], inputs=p["inputs"]
    )
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["summary"]["later_associations"] = 999
    (root / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="projection"):
        load_neotoma_linked_associations(
            root,
            expected_manifest_sha256=pin(root / "manifest.json"),
            evidence=p["evidence"],
            inputs=p["inputs"],
        )


def test_existing_output_refuses_before_source_resolution(tmp_path: Path) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        publish_neotoma_linked_associations,
    )

    root = tmp_path / "foreign"
    root.mkdir()
    invalid: Any = None
    with pytest.raises(FileExistsError):
        publish_neotoma_linked_associations(
            root, document={}, evidence=invalid, inputs=invalid
        )
    assert list(root.iterdir()) == []


def test_postpublication_swap_is_retained_and_refused(
    association_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        publication,
    )

    p = association_products
    document = build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    output = tmp_path / "published"
    publish = vars(publication)["publish_new_output_tree"]

    def corrupt(**kwargs: Any) -> None:
        publish(**kwargs)
        (output / "manifest.json").write_bytes(b"{}")

    monkeypatch.setattr(publication, "publish_new_output_tree", corrupt)
    with pytest.raises(ValueError, match="digest"):
        publication.publish_neotoma_linked_associations(
            output, document=document, evidence=p["evidence"], inputs=p["inputs"]
        )
    assert (output / "manifest.json").read_bytes() == b"{}"


@pytest.mark.parametrize("boundary", ["prepublish", "postpublish", "postreadback"])
def test_equal_byte_root_replacement_preserves_and_refuses_foreign_tree(
    association_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    import shutil

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        publication,
    )

    p = association_products
    document = build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    final = tmp_path / "published"
    retained = tmp_path / "retained-owned-tree"
    load = publication.load_neotoma_linked_associations
    publish = vars(publication)["publish_new_output_tree"]
    published = []
    replaced = []

    def replace_root(root: Path) -> None:
        root.rename(retained)
        shutil.copytree(retained, root)
        replaced.append(root)

    def observe_load(root: Path, **kwargs: Any) -> Any:
        result = load(root, **kwargs)
        if not replaced and (
            boundary == "prepublish"
            and root != final
            or boundary == "postreadback"
            and root == final
        ):
            replace_root(root)
        return result

    def observe_publish(**kwargs: Any) -> None:
        published.append(kwargs)
        publish(**kwargs)
        if boundary == "postpublish":
            replace_root(final)

    monkeypatch.setattr(publication, "load_neotoma_linked_associations", observe_load)
    monkeypatch.setattr(publication, "publish_new_output_tree", observe_publish)
    with pytest.raises(ValueError, match="identity|inode"):
        publication.publish_neotoma_linked_associations(
            final, document=document, evidence=p["evidence"], inputs=p["inputs"]
        )
    assert len(replaced) == 1
    assert len(published) == (0 if boundary == "prepublish" else 1)
    assert final.exists() is (boundary != "prepublish")
    foreign = replaced[0]
    assert retained.stat().st_ino != foreign.stat().st_ino
    owned_bytes = {
        path.relative_to(retained): path.read_bytes()
        for path in retained.rglob("*")
        if path.is_file()
    }
    foreign_bytes = {
        path.relative_to(foreign): path.read_bytes()
        for path in foreign.rglob("*")
        if path.is_file()
    }
    assert owned_bytes == foreign_bytes
