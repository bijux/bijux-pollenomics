"""Only an active exact source-owned lifetime can replace complete proof replay."""

from pathlib import Path
import shutil
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
    _full_evidence_inputs,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    NeotomaLinkedEvidence,
    NeotomaLinkedResourcePlan,
    NeotomaLinkedTarget,
    capture_neotoma_linked_resources,
)

from .native_products import observe
from .test_qualification import session_options


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
@pytest.mark.parametrize("fake", [True, {}, object()])
def test_fabricated_session_is_not_complete_evidence_authority(
    linked_inputs: dict[str, Any], monkeypatch: Any, fake: Any
) -> None:
    prepared = prepare_capsule_metadata(**linked_inputs)
    work = observe(monkeypatch)
    control = next(iter(prepared.controls.values()))
    with pytest.raises(ValueError, match="source-owned"):
        _full_evidence_inputs(
            control,
            prepared.context,
            linked_inputs["evidence_sources"],
            linked_inputs["predecessor_facets"],
            _session=fake,
            _operation=object(),
        )
    assert work["complete_validations"] == 0
    assert work["detail_body_opens"] == 0


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
@pytest.mark.parametrize("change", ["operation", "physical_resolver", "closed"])
def test_session_scope_changes_refuse_before_any_detail_body(
    linked_inputs: dict[str, Any], tmp_path: Path, monkeypatch: Any, change: str
) -> None:
    prepared = prepare_capsule_metadata(**linked_inputs)
    work = observe(monkeypatch)
    pin = next(iter(prepared.linked_sources))
    control = prepared.controls[pin]
    with context_seals(linked_inputs) as guard:
        with _evidence_sessions(
            prepared, **session_options(linked_inputs), before_body_read=guard.check
        ) as (sessions, operation):
            selected = linked_inputs["evidence_sources"]
            if change == "operation":
                operation = object()
            elif change == "physical_resolver":
                digest, original = next(iter(selected.items()))
                copied = tmp_path / "equal-pin-other-evidence"
                shutil.copytree(original, copied)
                selected = {digest: copied}
            if change != "closed":
                with pytest.raises(ValueError):
                    _full_evidence_inputs(
                        control,
                        prepared.context,
                        selected,
                        linked_inputs["predecessor_facets"],
                        _session=sessions[pin],
                        _operation=operation,
                    )
        if change == "closed":
            with pytest.raises(ValueError, match="inactive"):
                _full_evidence_inputs(
                    control,
                    prepared.context,
                    selected,
                    linked_inputs["predecessor_facets"],
                    _session=sessions[pin],
                    _operation=operation,
                )
    assert work["complete_validations"] == 1
    assert work["detail_body_opens"] == 0


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
def test_protected_shared_pi_remains_unrequested_and_unread(
    linked_inputs: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    prepared = prepare_capsule_metadata(**linked_inputs)
    evidence_pin, evidence_root = next(iter(linked_inputs["evidence_sources"].items()))
    calls: list[str] = []
    protected = tmp_path / "protected-contact"

    def forbidden(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        pytest.fail("Protected principal-investigator detail was requested")

    captured = capture_neotoma_linked_resources(
        protected,
        plan=NeotomaLinkedResourcePlan(
            tuple(sorted(linked_inputs["predecessor_facets"])),
            (NeotomaLinkedTarget("contact", 900),),
        ),
        source_facets=linked_inputs["predecessor_facets"],
        scope_inputs=prepared.context.current_scope_inputs,
        evidence=NeotomaLinkedEvidence(evidence_root, evidence_pin),
        fetch=forbidden,
    )
    work = observe(monkeypatch)
    _, _, _, index = prepare_capsule(
        **{**linked_inputs, "linked_captures": {captured.manifest_sha256: protected}}
    )
    assert calls == []
    assert index["observations"][0]["terminal_status"] == "not_attempted_exposure_role"
    assert (
        index["observations"][0]["identity"]["exposure_role"]
        == "heldout_no_numerical_access"
    )
    assert work["complete_validations"] == 1
    assert work["detail_body_opens"] == 0


def test_declared_oversized_owner_resolver_refuses_before_iteration() -> None:
    from collections.abc import Iterator, Mapping

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts.ownership import (
        _LinkedEvidenceSources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts.session import (
        _LinkedEvidenceSession,
    )

    class Oversized(Mapping[str, Path]):
        def __len__(self) -> int:
            return 40961

        def __iter__(self) -> Iterator[str]:
            raise AssertionError("Oversized source resolver was iterated")

        def __getitem__(self, key: str) -> Path:
            raise AssertionError("Oversized source resolver was resolved")

    owner = _LinkedEvidenceSources(
        NeotomaLinkedEvidence(Path("."), "a" * 64),
        {},
        Oversized(),
        Path("."),
        "b" * 64,
        Path("."),
        "c" * 64,
    )
    with pytest.raises(ValueError, match="resolver"):
        _LinkedEvidenceSession(
            source_owner=owner, scope_inputs={}, legacy_rosters={}, operation=object()
        )


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
@pytest.mark.parametrize(
    "invalid",
    [
        "fake",
        "subclass",
        "operation",
        "closed",
        "context",
        "roster",
        "metadata",
        "evidence_resolver",
        "missing_facet",
        "scope_resolver",
        "oversized",
    ],
)
def test_owned_lifecycle_refuses_before_native_metadata_without_extra_callback(
    linked_inputs: dict[str, Any], tmp_path: Path, monkeypatch: Any, invalid: str
) -> None:
    import os

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts.session import (
        _LinkedEvidenceSession,
    )

    prepared = prepare_capsule_metadata(**linked_inputs)
    pin = next(iter(prepared.linked_sources))
    scope = next(iter(prepared.context.current_scope_inputs.values()))
    original_open = os.open
    late: list[str] = []

    def opened(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        fd = original_open(path, flags, *args, **kwargs)
        if str(path).endswith(".body") and not flags & os.O_DIRECTORY:
            late.append(str(path))
        return fd

    with (
        pytest.raises(ValueError),
        context_seals(linked_inputs) as guard,
        _evidence_sessions(
            prepared, **session_options(linked_inputs), before_body_read=guard.check
        ) as (sessions, operation),
    ):
        session: Any = sessions[pin]
        if invalid == "fake":
            session = object()
        elif invalid == "subclass":
            derived = type("DerivedSession", (_LinkedEvidenceSession,), {})
            session = object.__new__(derived)
        elif invalid == "operation":
            operation = object()
        elif invalid == "closed":
            session._close()
        elif invalid == "evidence_resolver":
            evidence_pin, original = next(
                iter(linked_inputs["evidence_sources"].items())
            )
            copied = tmp_path / "equal-pin-evidence"
            shutil.copytree(original, copied)
            linked_inputs["evidence_sources"][evidence_pin] = copied
        elif invalid == "missing_facet":
            linked_inputs["predecessor_facets"] = {}
        elif invalid == "scope_resolver":
            from dataclasses import replace

            copied_roster = tmp_path / "equal-pin-roster.json"
            shutil.copyfile(scope.roster_path, copied_roster)
            roster = next(iter(prepared.context.current_scope_inputs))
            prepared.context.current_scope_inputs[roster] = replace(
                scope, roster_path=copied_roster
            )
        elif invalid == "oversized":
            from collections.abc import Iterator, Mapping

            class Oversized(Mapping[str, Path]):
                def __len__(self) -> int:
                    return 40961

                def __iter__(self) -> Iterator[str]:
                    raise AssertionError("Oversized resolver was iterated")

                def __getitem__(self, key: str) -> Path:
                    raise AssertionError("Oversized resolver was resolved")

            linked_inputs["predecessor_facets"] = Oversized()
        else:
            permission = {
                "context": linked_inputs["context_directory"] / "manifest.json",
                "roster": scope.roster_path,
                "metadata": next(iter(scope.metadata_captures.values()))
                / "capture-manifest.json",
            }[invalid]
            permission.write_bytes(permission.read_bytes())
        monkeypatch.setattr(os, "open", opened)
        monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {opened})
        try:
            _full_evidence_inputs(
                prepared.controls[pin],
                prepared.context,
                linked_inputs["evidence_sources"],
                linked_inputs["predecessor_facets"],
                _session=session,
                _operation=operation,
            )
        finally:
            assert not late, "Owned lifecycle must precede native metadata resolution"


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
def test_valid_private_metadata_handoff_uses_its_stored_current_guard(
    linked_inputs: dict[str, Any], monkeypatch: Any
) -> None:
    prepared = prepare_capsule_metadata(**linked_inputs)
    calls = 0
    with context_seals(linked_inputs) as guard:

        def current() -> None:
            nonlocal calls
            calls += 1
            guard.check()

        with _evidence_sessions(
            prepared, **session_options(linked_inputs), before_body_read=current
        ) as (sessions, operation):
            pin = next(iter(sessions))
            calls = 0
            work = observe(monkeypatch)
            inputs = _full_evidence_inputs(
                prepared.controls[pin],
                prepared.context,
                linked_inputs["evidence_sources"],
                linked_inputs["predecessor_facets"],
                _session=sessions[pin],
                _operation=operation,
            )
            assert (
                inputs["evidence"].manifest_sha256 in linked_inputs["evidence_sources"]
            )
            assert calls >= 1
            assert work["complete_validations"] == 0
            assert work["detail_body_opens"] == 0
