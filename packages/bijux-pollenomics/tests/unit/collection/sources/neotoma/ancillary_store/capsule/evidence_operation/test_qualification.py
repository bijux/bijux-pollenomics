"""Batch qualification retains native statuses under one explicit live proof owner."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule.evidence import (
    _evidence_sessions,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule.inventory import (
    prepare_capsule_metadata,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.seals import (
    context_seals,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.sources import (
    _evidence_inputs,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    qualification,
    replay,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.replay import (
    _read_linked_entry_body,
)
from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _read

from .native_products import observe


def session_options(inputs: dict[str, Any]) -> dict[str, Any]:
    """Resolve independent metadata anchors from the explicit capsule inputs."""
    return {
        key: inputs[key]
        for key in (
            "context_directory",
            "expected_context_sha256",
            "native_archive_directory",
            "predecessor_facets",
            "evidence_sources",
        )
    }


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
def test_batch_qualification_authenticates_complete_evidence_once(
    linked_inputs: dict[str, Any], monkeypatch: Any
) -> None:
    prepared = prepare_capsule_metadata(**linked_inputs)
    work = observe(monkeypatch)
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
            report = qualification._qualify_linked_capture(
                directory,
                expected_manifest_sha256=pin,
                **inputs,
                _session=sessions[pin],
                _operation=operation,
                _before_body_read=guard.check,
            )
            assert report["partitions"] == {"parsed_linked_source": 1}
            assert report["source_capture_relabelled"] is False
            assert report["scientific_admission"] == "not_asserted"
    assert work["complete_validations"] == 1
    assert work["detail_body_opens"] == 6


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
def test_qualification_receipt_drift_refuses_before_parse_body(
    linked_inputs: dict[str, Any], monkeypatch: Any
) -> None:
    prepared = prepare_capsule_metadata(**linked_inputs)
    work = observe(monkeypatch)
    permission = linked_inputs["context_directory"] / "manifest.json"
    parsing = changed = False
    original_entry, original_read = _read_linked_entry_body, _read

    def entry(*args: Any, **kwargs: Any) -> Any:
        nonlocal parsing
        parsing = True
        return original_entry(*args, **kwargs)

    def read(path: Path, bound: int) -> bytes:
        nonlocal changed
        raw = original_read(path, bound)
        if parsing and path.name.endswith(".receipt.json") and not changed:
            permission.write_bytes(permission.read_bytes())
            changed = True
        return raw

    monkeypatch.setattr(qualification, "_read_linked_entry_body", entry)
    monkeypatch.setattr(replay, "_read", read)
    with (
        pytest.raises(ValueError, match="changed"),
        context_seals(linked_inputs) as guard,
        _evidence_sessions(
            prepared, **session_options(linked_inputs), before_body_read=guard.check
        ) as (sessions, operation),
    ):
        pin, directory = next(iter(prepared.linked_sources.items()))
        inputs = _evidence_inputs(
            prepared.controls[pin],
            prepared.context,
            linked_inputs["evidence_sources"],
            linked_inputs["predecessor_facets"],
        )
        qualification._qualify_linked_capture(
            directory,
            expected_manifest_sha256=pin,
            **inputs,
            _session=sessions[pin],
            _operation=operation,
            _before_body_read=guard.check,
        )
    assert changed
    assert work["detail_body_opens"] == 1


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
def test_legacy_and_scoped_qualifications_share_the_same_owned_lifetime(
    linked_inputs: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        NeotomaLinkedResourcePlan,
        NeotomaLinkedTarget,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts.ownership import (
        _LinkedEvidenceSources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts.session import (
        _LinkedEvidenceSession,
    )

    from ....acquisition.linked_resources.evidence.native_products import (
        capture_legacy_linked_fixture,
    )
    from ....acquisition.resources.native_payloads import response

    prepared = prepare_capsule_metadata(**linked_inputs)
    first = next(iter(prepared.linked_sources))
    inputs = _evidence_inputs(
        prepared.controls[first],
        prepared.context,
        linked_inputs["evidence_sources"],
        linked_inputs["predecessor_facets"],
    )
    native = next(prepared.linked_sources[first].glob("*.body")).read_bytes()
    legacy_root = tmp_path / "legacy-source"
    legacy = capture_legacy_linked_fixture(
        legacy_root,
        plan=NeotomaLinkedResourcePlan(
            tuple(sorted(inputs["source_facets"])),
            (NeotomaLinkedTarget("taxon", 11),),
            include_higher_taxa=True,
        ),
        source_facets=inputs["source_facets"],
        scope_inputs=inputs["scope_inputs"],
        fetch=lambda url, **kwargs: response(url, native),
    )
    captures = {**prepared.linked_sources, legacy.manifest_sha256: legacy_root}
    owner = _LinkedEvidenceSources(
        evidence=inputs["evidence"],
        source_facets=inputs["source_facets"],
        capture_sources=captures,
        context_directory=linked_inputs["context_directory"],
        expected_context_sha256=linked_inputs["expected_context_sha256"],
        native_archive_directory=linked_inputs["native_archive_directory"],
        expected_native_archive_sha256=prepared.context.manifest["native_archive"][
            "manifest_sha256"
        ],
    )
    operation = object()
    work = observe(monkeypatch)
    with (
        context_seals(linked_inputs) as guard,
        _LinkedEvidenceSession(
            source_owner=owner,
            scope_inputs=inputs["scope_inputs"],
            legacy_rosters=inputs["legacy_rosters"],
            operation=operation,
            _before_body_read=guard.check,
        ) as session,
    ):
        for pin, root in captures.items():
            evidence = None if pin == legacy.manifest_sha256 else inputs["evidence"]
            report = qualification._qualify_linked_capture(
                root,
                expected_manifest_sha256=pin,
                source_facets=inputs["source_facets"],
                scope_inputs=inputs["scope_inputs"],
                legacy_rosters=inputs["legacy_rosters"],
                evidence=evidence,
                _session=session,
                _operation=operation,
                _before_body_read=guard.check,
            )
            assert report["partitions"] == {"parsed_linked_source": 1}
            assert report["source_capture_relabelled"] is False
            assert report["scientific_admission"] == "not_asserted"
    assert work["complete_validations"] == 1
    assert work["detail_body_opens"] == 9
