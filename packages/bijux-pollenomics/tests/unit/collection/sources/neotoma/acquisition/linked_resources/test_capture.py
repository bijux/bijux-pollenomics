"""Finite detail requests require authenticated native references before transport."""

from __future__ import annotations

from dataclasses import replace
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
    NeotomaFacetPlan,
    capture_neotoma_dataset_facets,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
    NeotomaResourceLimits,
)
from bijux_pollenomics.collection.sources.neotoma.capture.transport import (
    NeotomaHttpResponse,
)

from ..facets.test_profiles import capture as facet_capture
from ..facets.test_profiles import payload, resource
from ..resources.native_payloads import response


def owner() -> ModuleType:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources"
    )


def plan(source: str, *, higher: bool = False, targets: Any = None) -> Any:
    api = owner()
    return api.NeotomaLinkedResourcePlan(
        (source,),
        tuple(
            api.NeotomaLinkedTarget(kind, identity)
            for kind, identity in (
                [("contact", 8720), ("publication", 9435), ("taxon", 1)]
                if targets is None
                else targets
            )
        ),
        include_higher_taxa=higher,
    )


def source(root: Path) -> tuple[str, dict[str, Path]]:
    captured = facet_capture(root)
    return captured.manifest_sha256, {captured.manifest_sha256: root}


def limits(requests: int = 3) -> NeotomaResourceLimits:
    return NeotomaResourceLimits(
        max_requests=requests,
        max_attempts=1,
        max_response_bytes=4096,
        max_total_bytes=16384,
        timeout_seconds=5,
        wall_seconds=20,
        retry_delay_seconds=0,
    )


def test_three_exact_routes_preserve_all_root_proofs_and_original_sources(
    tmp_path: Path,
) -> None:
    digest, sources = source(tmp_path / "facets")
    before = {p.name: p.read_bytes() for p in sources[digest].iterdir()}
    calls = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        assert kwargs["max_bytes"] <= 4096 and kwargs["timeout"] <= 5
        return response(url, b'{"status":"success","data":[{"foreign_native_id":999}]}')

    result = owner().capture_neotoma_linked_resources(
        tmp_path / "linked",
        plan=plan(digest),
        source_facets=sources,
        limits=limits(),
        fetch=fetch,
    )
    assert calls == [
        "https://api.neotomadb.org/v2.0/data/contacts/8720",
        "https://api.neotomadb.org/v2.0/data/publications/9435",
        "https://api.neotomadb.org/v2.0/data/taxa/1",
    ]
    assert result.request_count == 3
    assert result.partitions == {"received_complete_unqualified_linked_resource": 3}
    for entry in result.resources:
        assert entry["summary"]["payload_owner_status"] == "not_established"
        assert entry["scientific_admission"] == "not_asserted"
        assert entry["identity"]["source_proofs"]
        assert all(
            row["source_capture_manifest_sha256"] == digest
            for row in entry["identity"]["source_proofs"]
        )
    assert before == {p.name: p.read_bytes() for p in sources[digest].iterdir()}


@pytest.mark.parametrize(
    "target",
    [
        ("contact", True),
        ("taxon", "1"),
        ("taxon", 1.1),
        ("taxon", 0),
        ("taxa/1/occurrences", 1),
        ("publication", 999999),
    ],
)
def test_invalid_or_unproved_targets_fail_before_get(
    tmp_path: Path, target: Any
) -> None:
    digest, sources = source(tmp_path / "facets")
    with pytest.raises(ValueError):
        owner().capture_neotoma_linked_resources(
            tmp_path / "linked",
            plan=plan(digest, targets=[target]),
            source_facets=sources,
            limits=limits(),
            fetch=lambda *a, **k: pytest.fail("unproved request reached HTTP"),
        )
    assert not (tmp_path / "linked").exists()


def test_higher_taxa_are_explicit_nonrecursive_and_proofs_are_not_deduplicated(
    tmp_path: Path,
) -> None:
    digest, sources = source(tmp_path / "facets")
    selected = [("publication", 1), ("taxon", 1000)]
    with pytest.raises(ValueError):
        owner().capture_neotoma_linked_resources(
            tmp_path / "blocked",
            plan=plan(digest, targets=selected),
            source_facets=sources,
            limits=limits(),
            fetch=lambda *a, **k: pytest.fail("implicit higher taxon GET"),
        )
    result = owner().capture_neotoma_linked_resources(
        tmp_path / "linked",
        plan=plan(digest, higher=True, targets=selected),
        source_facets=sources,
        limits=limits(),
        fetch=lambda url, **k: response(url, b"{}"),
    )
    publication = next(
        row for row in result.resources if row["identity"]["kind"] == "publication"
    )
    assert len(publication["identity"]["source_proofs"]) == 4
    assert (
        len({row["json_pointer"] for row in publication["identity"]["source_proofs"]})
        == 4
    )
    assert result.request_count == 2


def test_protected_source_cannot_be_opened_to_supply_a_link(tmp_path: Path) -> None:
    root = tmp_path / "facets"
    captured = capture_neotoma_dataset_facets(
        root,
        plan=NeotomaFacetPlan((resource("heldout_no_numerical_access"),), "b" * 64),
        fetch=lambda *a, **k: pytest.fail("protected facet GET"),
    )
    with pytest.raises(ValueError, match="proof|role"):
        owner().capture_neotoma_linked_resources(
            tmp_path / "linked",
            plan=plan(captured.manifest_sha256),
            source_facets={captured.manifest_sha256: root},
            limits=limits(),
            fetch=lambda *a, **k: pytest.fail("protected linked GET"),
        )
    assert not list(root.glob("*.body"))


def test_native_foreign_dataset_cannot_supply_contact_proof(tmp_path: Path) -> None:
    root = tmp_path / "facets"

    def fetch(url: str, **_: Any) -> Any:
        value = payload(url.rsplit("/", 1)[-1])
        if url.endswith("/chronologies"):
            value["data"][0]["chronology"]["datasets"][0]["datasetid"] = 999
        return response(url, json.dumps(value).encode())

    captured = capture_neotoma_dataset_facets(
        root, plan=NeotomaFacetPlan((resource(),), "b" * 64), fetch=fetch
    )
    with pytest.raises(ValueError, match="proof"):
        owner().capture_neotoma_linked_resources(
            tmp_path / "linked",
            plan=plan(captured.manifest_sha256, targets=[("contact", 8720)]),
            source_facets={captured.manifest_sha256: root},
            limits=limits(),
            fetch=lambda *a, **k: pytest.fail("foreign source contact GET"),
        )


@pytest.mark.parametrize("status", [404, 429, 500])
def test_http_failure_states_are_retained_without_absence_claim(
    tmp_path: Path, status: int
) -> None:
    digest, sources = source(tmp_path / "facets")
    result = owner().capture_neotoma_linked_resources(
        tmp_path / "linked",
        plan=plan(digest, targets=[("contact", 8720)]),
        source_facets=sources,
        limits=limits(),
        fetch=lambda url, **k: response(
            url, b'{"error":"source failure"}', status=status
        ),
    )
    assert result.partitions == {"unavailable_http": 1}
    assert result.resources[0]["absence_certified"] is False
    assert len(list((tmp_path / "linked").glob("*.body"))) == 1


def test_budget_and_transport_failure_have_exact_partitions(tmp_path: Path) -> None:
    digest, sources = source(tmp_path / "facets")

    def fetch(*args: Any, **kwargs: Any) -> Any:
        raise TimeoutError("bounded timeout")

    result = owner().capture_neotoma_linked_resources(
        tmp_path / "linked",
        plan=plan(digest),
        source_facets=sources,
        limits=limits(1),
        fetch=fetch,
    )
    assert result.partitions == {"transport_failure": 1, "not_attempted_budget": 2}
    assert result.request_count == 1 and result.response_bytes == 0


def test_existing_destination_and_caller_limit_are_preserved(tmp_path: Path) -> None:
    digest, sources = source(tmp_path / "facets")
    destination = tmp_path / "linked"
    destination.mkdir()
    (destination / "owned.txt").write_text("existing bytes")
    with pytest.raises(FileExistsError):
        owner().capture_neotoma_linked_resources(
            destination,
            plan=plan(digest),
            source_facets=sources,
            limits=limits(),
            fetch=lambda *a, **k: pytest.fail("existing destination GET"),
        )
    assert (destination / "owned.txt").read_text() == "existing bytes"
    with pytest.raises(ValueError):
        owner().capture_neotoma_linked_resources(
            tmp_path / "invalid",
            plan=plan(digest),
            source_facets=sources,
            limits=replace(limits(), max_requests=True),
            fetch=lambda *a, **k: pytest.fail("invalid budget GET"),
        )


@pytest.mark.parametrize(
    "body", [b'{"id":1,"id":2}', b'{"number":1e999}', b'{"number":1e-999}', b"[]"]
)
def test_ambiguous_or_lossy_json_is_retained_unqualified_as_refusal(
    tmp_path: Path, body: bytes
) -> None:
    digest, sources = source(tmp_path / "facets")
    result = owner().capture_neotoma_linked_resources(
        tmp_path / "linked",
        plan=plan(digest, targets=[("contact", 8720)]),
        source_facets=sources,
        limits=limits(),
        fetch=lambda url, **k: response(url, body),
    )
    assert result.partitions == {"refused_native_json": 1}
    assert next((tmp_path / "linked").glob("*.body")).read_bytes() == body


def test_incomplete_body_and_foreign_callback_destination_are_preserved(
    tmp_path: Path,
) -> None:
    digest, sources = source(tmp_path / "facets")
    result = owner().capture_neotoma_linked_resources(
        tmp_path / "partial",
        plan=plan(digest, targets=[("contact", 8720)]),
        source_facets=sources,
        limits=limits(),
        fetch=lambda url, **k: NeotomaHttpResponse(url, 200, (), b'{"partial":', False),
    )
    assert result.partitions == {"refused_incomplete_body": 1}
    with pytest.raises(ValueError, match="identity"):
        owner().capture_neotoma_linked_resources(
            tmp_path / "foreign",
            plan=plan(digest, targets=[("contact", 8720)]),
            source_facets=sources,
            limits=limits(),
            fetch=lambda url, **k: response(
                "https://foreign.invalid/contacts/8720", b"{}"
            ),
        )
    assert not (tmp_path / "foreign").exists()
    assert next((tmp_path / ".foreign.staging").glob("*.body")).read_bytes() == b"{}"
    assert (tmp_path / ".foreign.staging/refusal.json").is_file()


def test_shared_target_preserves_all_source_roots_and_restrictive_role(
    tmp_path: Path,
) -> None:
    digest, sources = source(tmp_path / "facets")
    second_root = tmp_path / "exposed"
    second = capture_neotoma_dataset_facets(
        second_root,
        plan=NeotomaFacetPlan((resource("exposed_development"),), "b" * 64),
        fetch=lambda url, **k: response(
            url, json.dumps(payload(url.rsplit("/", 1)[-1])).encode()
        ),
    )
    sources[second.manifest_sha256] = second_root
    selected = owner().NeotomaLinkedResourcePlan(
        (digest, second.manifest_sha256),
        (owner().NeotomaLinkedTarget("publication", 1),),
    )
    result = owner().capture_neotoma_linked_resources(
        tmp_path / "linked",
        plan=selected,
        source_facets=sources,
        limits=limits(1),
        fetch=lambda url, **k: response(url, b"{}"),
    )
    identity = result.resources[0]["identity"]
    assert identity["exposure_role"] == "exposed_development"
    assert len(identity["source_proofs"]) == 8
    assert {
        p["source_capture_manifest_sha256"] for p in identity["source_proofs"]
    } == set(sources)
    assert result.request_count == 1
