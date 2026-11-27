"""Scoped source declarations are opt-in and remain owner-bound."""

from typing import Any

import pytest

from ..native_products import facet_row

PROFILE = "neotoma-scoped-facet-declarations.v1"


def request(
    products: dict[str, Any], *, legacy: bool = False
) -> tuple[tuple[str, int, str], ...]:
    row = facet_row(products, legacy=legacy)
    return ((row["observation_id"], 201, "taxa"),)


def test_declarations_are_opt_in_and_match_pinned_source(
    selected_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facets,
    )

    p = selected_products
    row = facet_row(p)
    requests = request(p)
    base = read_neotoma_ancillary_facets(
        p["directory"], requests=requests, **p["kwargs"]
    )
    got = read_neotoma_ancillary_facets(
        p["directory"],
        requests=requests,
        source_declarations_profile=PROFILE,
        **p["kwargs"],
    )
    result = dict(got[0])
    declarations = result.pop("source_declarations")
    assert (result,) == base
    import json

    root = p["capsule"] / "captures" / row["source_capture_manifest_sha256"]
    capture = json.loads((root / "capture-manifest.json").read_bytes())
    receipt = json.loads((root / row["attempts"][-1]["receipt_file"]).read_bytes())
    assert declarations == {
        "schema_version": PROFILE,
        "capture_utc_start": capture["capture_utc_start"],
        "capture_utc_end": capture["capture_utc_end"],
        "request_utc_start": receipt["utc_start"],
        "request_utc_end": receipt["utc_end"],
        "request_url": receipt["requested_url"],
        "original_parent_scope": "authenticated_original_parent_scope",
        "original_scope_role": row["parent_scope_role"],
        "current_scope_role": row["current_use_role"],
        "scientific_admission": "not_asserted",
    }


def test_legacy_capture_is_refused_only_for_declarations(
    selected_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facets,
    )

    p = selected_products
    requests = request(p, legacy=True)
    assert read_neotoma_ancillary_facets(
        p["directory"], requests=requests, **p["kwargs"]
    )
    with pytest.raises(ValueError, match="scoped"):
        read_neotoma_ancillary_facets(
            p["directory"],
            requests=requests,
            source_declarations_profile=PROFILE,
            **p["kwargs"],
        )


@pytest.mark.parametrize("profile", ["unknown", True, [], 1])
def test_unknown_profile_refused(
    selected_products: dict[str, Any], profile: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        read_neotoma_ancillary_facets,
    )

    p = selected_products
    with pytest.raises(ValueError, match="profile"):
        read_neotoma_ancillary_facets(
            p["directory"],
            requests=request(p),
            source_declarations_profile=profile,
            **p["kwargs"],
        )


@pytest.mark.parametrize(
    "change",
    [
        "current_role",
        "original_role",
        "original_posture",
        "capture_schema",
        "request_url",
        "request_order",
    ],
)
def test_inconsistent_owner_declarations_are_refused(
    selected_products: dict[str, Any], monkeypatch: Any, change: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        typed_batch,
    )

    original = typed_batch._prepared_facet_access

    def prepare(*args: Any, **kwargs: Any) -> Any:
        access = original(*args, **kwargs)
        if change == "current_role":
            access.parents[201]["effective_scope_role"] = "heldout_no_numerical_access"
        elif change == "original_role":
            access.entry["parent_scope_role"] = "heldout_no_numerical_access"
        elif change == "original_posture":
            access.row["capture_parent_scope_verification"] = (
                "not_recorded_legacy_capture"
            )
        elif change == "capture_schema":
            access.capture["document"]["schema_version"] = (
                "neotoma-dataset-facet-http-capture.v1"
            )
        elif change == "request_url":
            access.response[0]["requested_url"] = "https://example.test/"
        else:
            access.response[0]["utc_start"] = "9999-01-01T00:00:00+00:00"
        return access

    monkeypatch.setattr(typed_batch, "_prepared_facet_access", prepare)
    p = selected_products
    with pytest.raises(ValueError):
        typed_batch.read_neotoma_ancillary_facets(
            p["directory"],
            requests=request(p),
            source_declarations_profile=PROFILE,
            **p["kwargs"],
        )


def test_mixed_legacy_batch_refuses_before_any_body(
    selected_products: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        typed_batch,
    )

    p = selected_products
    read = []
    original = typed_batch._read

    def observed(*args: Any, **kwargs: Any) -> bytes:
        read.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(typed_batch, "_read", observed)
    with pytest.raises(ValueError, match="scoped"):
        typed_batch.read_neotoma_ancillary_facets(
            p["directory"],
            requests=request(p) + request(p, legacy=True),
            source_declarations_profile=PROFILE,
            **p["kwargs"],
        )
    assert read == []


def test_scope_mutation_during_qualification_refuses_profile(
    selected_products: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.selection import (
        typed_batch,
    )

    p = selected_products
    original = typed_batch.qualify_neotoma_facet_body
    path = p["kwargs"]["context_directory"] / "manifest.json"

    def qualify(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        path.write_bytes(path.read_bytes() + b"\n")
        return result

    monkeypatch.setattr(typed_batch, "qualify_neotoma_facet_body", qualify)
    with pytest.raises(ValueError):
        typed_batch.read_neotoma_ancillary_facets(
            p["directory"],
            requests=request(p),
            source_declarations_profile=PROFILE,
            **p["kwargs"],
        )
