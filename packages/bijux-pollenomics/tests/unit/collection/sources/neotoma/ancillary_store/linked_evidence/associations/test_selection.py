"""A later native witness binds the retained entity without another GET."""

from pathlib import Path
from typing import Any

import pytest

from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)


def test_selected_later_native_pointer_and_original_body(
    association_products: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        publish_neotoma_linked_associations,
        read_neotoma_linked_association_source,
    )

    from .native_products import pin

    p = association_products
    document = build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    output = tmp_path / "associations"
    publish_neotoma_linked_associations(
        output, document=document, evidence=p["evidence"], inputs=p["inputs"]
    )
    row = document["targets"][0]
    result = read_neotoma_linked_association_source(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        target_key="taxon-11",
        occurrence_locator=row["later_example_locator"],
        evidence=p["evidence"],
        inputs=p["inputs"],
    )
    assert result["source_payload"]["data"] == [p["native_payload"]]
    assert result["selected_occurrence_native_field_verified"] is True
    assert result["original_preget_scope_reconstructed"] is False


def test_selected_source_opens_exactly_one_witness_and_old_detail(
    association_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        publish_neotoma_linked_associations,
        read_neotoma_linked_association_source,
    )

    from .native_products import pin

    p = association_products
    document = build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    output = tmp_path / "published"
    publish_neotoma_linked_associations(
        output, document=document, evidence=p["evidence"], inputs=p["inputs"]
    )
    opened = []
    original = capture_opening()

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and p["capsule"] in path.parents:
            opened.append(path)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    read_neotoma_linked_association_source(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        target_key="taxon-11",
        occurrence_locator=document["targets"][0]["later_example_locator"],
        evidence=p["evidence"],
        inputs=p["inputs"],
    )
    assert len(opened) == len(set(opened)) == 2
    assert sum(path.name == "taxon-11-current-attempt-1.body" for path in opened) == 1
    assert (
        sum(
            path.name == "dataset-203-facet-taxa-current-attempt-1.body"
            for path in opened
        )
        == 1
    )


def test_foreign_occurrence_refuses_before_any_entity(
    association_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    import pytest

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        publish_neotoma_linked_associations,
        read_neotoma_linked_association_source,
    )

    from .native_products import pin

    p = association_products
    document = build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    output = tmp_path / "published"
    publish_neotoma_linked_associations(
        output, document=document, evidence=p["evidence"], inputs=p["inputs"]
    )
    locator = {**document["targets"][0]["later_example_locator"], "row_offset": 99999}
    original = capture_opening()
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and p["capsule"] in path.parents:
            opened.append(path)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    with pytest.raises(ValueError, match="occurrence locator"):
        read_neotoma_linked_association_source(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            target_key="taxon-11",
            occurrence_locator=locator,
            evidence=p["evidence"],
            inputs=p["inputs"],
        )
    assert opened == []


def test_lower_caller_byte_budget_refuses_before_source_body(
    association_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from dataclasses import replace

    import pytest

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        publish_neotoma_linked_associations,
        read_neotoma_linked_association_source,
    )

    from .native_products import pin

    p = association_products
    document = build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    output = tmp_path / "published"
    publish_neotoma_linked_associations(
        output, document=document, evidence=p["evidence"], inputs=p["inputs"]
    )
    inputs = replace(
        p["inputs"], limits=replace(p["inputs"].limits, max_response_bytes=1)
    )
    original = capture_opening()
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and p["capsule"] in path.parents:
            opened.append(path)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    with pytest.raises(ValueError, match="budget"):
        read_neotoma_linked_association_source(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            target_key="taxon-11",
            occurrence_locator=document["targets"][0]["later_example_locator"],
            evidence=p["evidence"],
            inputs=inputs,
        )
    assert opened == []


def test_metadata_access_preserves_unverified_pointer_flags(
    association_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        publish_neotoma_linked_associations,
        read_neotoma_linked_association,
    )

    from .native_products import pin

    p = association_products
    document = build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    output = tmp_path / "published"
    publish_neotoma_linked_associations(
        output, document=document, evidence=p["evidence"], inputs=p["inputs"]
    )
    original = capture_opening()
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and p["capsule"] in path.parents:
            opened.append(path)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    row = read_neotoma_linked_association(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        target_key="taxon-11",
        evidence=p["evidence"],
        inputs=p["inputs"],
    )
    assert (
        row["native_field_value_verified"]
        is row["native_entity_owner_verified"]
        is False
    )
    assert row["later_associations"] == 1
    assert opened == []


@pytest.mark.parametrize("association_products", ["contact"], indirect=True)
def test_later_current_protected_pi_blocks_legacy_contact(
    association_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        publish_neotoma_linked_associations,
        read_neotoma_linked_association_source,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        read_neotoma_linked_evidence_target,
    )

    from .native_products import pin

    p = association_products
    document = build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    row = document["targets"][0]
    assert row["current_use_role"] == "heldout_no_numerical_access"
    assert row["retained_entity"] is not None
    selected = read_neotoma_linked_evidence_target(
        p["evidence"].directory,
        expected_manifest_sha256=p["evidence"].manifest_sha256,
        kind="contact",
        native_id=900,
    )
    assert all(
        proof["root_dataset_id"] in (201, 203) for proof in selected["source_proofs"]
    )
    output = tmp_path / "published"
    publish_neotoma_linked_associations(
        output, document=document, evidence=p["evidence"], inputs=p["inputs"]
    )
    opened = []
    original = capture_opening()

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and p["capsule"] in path.parents:
            opened.append(path)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    with pytest.raises(ValueError, match="protected"):
        read_neotoma_linked_association_source(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            target_key="contact-900",
            occurrence_locator=row["later_example_locator"],
            evidence=p["evidence"],
            inputs=p["inputs"],
        )
    assert opened == []


def test_bodyless_state_claim_cannot_verify_native_pointer(
    association_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        publish_neotoma_linked_associations,
        read_neotoma_linked_association_source,
    )

    from .native_products import false_native_pointer_state, pin

    p = association_products
    evidence = false_native_pointer_state(p["evidence"], tmp_path / "false-state")
    document = build_neotoma_linked_associations(evidence, inputs=p["inputs"])
    output = tmp_path / "published"
    publish_neotoma_linked_associations(
        output, document=document, evidence=evidence, inputs=p["inputs"]
    )
    assert document["targets"][0]["native_field_value_verified"] is False
    original = capture_opening()
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and p["capsule"] in path.parents:
            opened.append(path)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    with pytest.raises(ValueError, match="native field target"):
        read_neotoma_linked_association_source(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            target_key="taxon-11",
            occurrence_locator=document["targets"][0]["later_example_locator"],
            evidence=evidence,
            inputs=p["inputs"],
        )
    assert len(opened) == 1
    assert opened[0].name.endswith("facet-taxa-current-attempt-1.body")


@pytest.mark.parametrize("association_products", ["unavailable"], indirect=True)
def test_unsuccessful_retained_response_refuses_before_witness(
    association_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.associations import (
        build_neotoma_linked_associations,
        publish_neotoma_linked_associations,
        read_neotoma_linked_association_source,
    )

    from .native_products import pin

    p = association_products
    document = build_neotoma_linked_associations(p["evidence"], inputs=p["inputs"])
    output = tmp_path / "published"
    publish_neotoma_linked_associations(
        output, document=document, evidence=p["evidence"], inputs=p["inputs"]
    )
    assert document["targets"][0]["retained_entity"]["http_status"] == 503
    original = capture_opening()
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and p["capsule"] in path.parents:
            opened.append(path)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    with pytest.raises(ValueError, match="complete and successful"):
        read_neotoma_linked_association_source(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            target_key="taxon-11",
            occurrence_locator=document["targets"][0]["later_example_locator"],
            evidence=p["evidence"],
            inputs=p["inputs"],
        )
    assert opened == []
