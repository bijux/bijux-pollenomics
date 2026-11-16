"""Different evidence anchors and public defaults never become shared authority."""

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule.evidence import (
    _evidence_sessions,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule.inventory import (
    prepare_capsule_metadata,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule.validation import (
    prepare_capsule,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.seals import (
    context_seals,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.sources import (
    _evidence_inputs,
)
from bijux_pollenomics.collection.sources.neotoma.capture.facets.replay import _control
from bijux_pollenomics.collection.sources.neotoma.capture.facets.workflow import (
    capture_neotoma_dataset_facets,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    NeotomaLinkedEvidence,
    NeotomaLinkedResourcePlan,
    NeotomaLinkedTarget,
    capture_neotoma_linked_resources,
    publish_neotoma_linked_evidence,
    qualification,
)

from ....acquisition.linked_resources.evidence.native_products import payload
from ....acquisition.resources.native_payloads import response
from .native_products import observe
from .test_qualification import session_options


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
def test_batched_qualification_preserves_public_native_results(
    linked_inputs: dict[str, Any],
) -> None:
    prepared = prepare_capsule_metadata(**linked_inputs)
    public = {}
    for pin, directory in prepared.linked_sources.items():
        inputs = _evidence_inputs(
            prepared.controls[pin],
            prepared.context,
            linked_inputs["evidence_sources"],
            linked_inputs["predecessor_facets"],
        )
        public[pin] = qualification.qualify_neotoma_linked_capture(
            directory, expected_manifest_sha256=pin, **inputs
        )
    with (
        context_seals(linked_inputs) as guard,
        _evidence_sessions(
            prepared, **session_options(linked_inputs), before_body_read=guard.check
        ) as (sessions, operation),
    ):
        for pin, directory in prepared.linked_sources.items():
            inputs = _evidence_inputs(
                prepared.controls[pin],
                prepared.context,
                linked_inputs["evidence_sources"],
                linked_inputs["predecessor_facets"],
            )
            batched = qualification._qualify_linked_capture(
                directory,
                expected_manifest_sha256=pin,
                **inputs,
                _session=sessions[pin],
                _operation=operation,
                _before_body_read=guard.check,
            )
            assert batched == public[pin]
            assert batched["partitions"] == {"parsed_linked_source": 1}
            assert batched["scientific_admission"] == "not_asserted"


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
def test_independent_evidence_anchors_require_independent_complete_validation(
    linked_inputs: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    prepared = prepare_capsule_metadata(**linked_inputs)
    roster, scope = next(iter(prepared.context.current_scope_inputs.items()))
    facets = {}
    for pin, root in linked_inputs["predecessor_facets"].items():
        _, plan, _, _ = _control(root, pin)
        if not any(
            row.exposure_role
            in {"development_resource_discovery", "exposed_development"}
            for row in plan.resources
        ):
            facets[pin] = root
            continue
        fresh = tmp_path / "independent-facets"

        def fetch(url: str, **kwargs: Any) -> Any:
            dataset, facet = url.rsplit("/", 2)[-2:]
            body = payload(int(dataset), facet)
            body["message"] = "Independent recorded source response"
            return response(url, json.dumps(body).encode())

        facet_result = capture_neotoma_dataset_facets(
            fresh, plan=plan, scope=scope, fetch=fetch
        )
        facets[facet_result.manifest_sha256] = fresh
    evidence = publish_neotoma_linked_evidence(
        tmp_path / "independent-evidence",
        expected_roster_sha256=roster,
        scope=scope,
        source_facets=facets,
    )
    original_pin, original_root = next(iter(linked_inputs["linked_captures"].items()))
    raw = next(original_root.glob("*.body")).read_bytes()
    directory = tmp_path / "independent-detail"
    linked_result = capture_neotoma_linked_resources(
        directory,
        plan=NeotomaLinkedResourcePlan(
            tuple(sorted(facets)),
            (NeotomaLinkedTarget("taxon", 11),),
            include_higher_taxa=True,
        ),
        source_facets=facets,
        scope_inputs=prepared.context.current_scope_inputs,
        evidence=NeotomaLinkedEvidence(evidence.directory, evidence.manifest_sha256),
        fetch=lambda url, **kwargs: response(url, raw),
    )
    inputs = {
        **linked_inputs,
        "linked_captures": {
            original_pin: original_root,
            linked_result.manifest_sha256: directory,
        },
        "predecessor_facets": {**linked_inputs["predecessor_facets"], **facets},
        "evidence_sources": {
            **linked_inputs["evidence_sources"],
            evidence.manifest_sha256: evidence.directory,
        },
    }
    assert len(inputs["evidence_sources"]) == 2
    work = observe(monkeypatch)
    manifest, _, _, index = prepare_capsule(**inputs)
    assert len(manifest["captures"]) == 2 and len(index["observations"]) == 2
    assert work["complete_validations"] == 2
    assert work["detail_body_opens"] == 2
