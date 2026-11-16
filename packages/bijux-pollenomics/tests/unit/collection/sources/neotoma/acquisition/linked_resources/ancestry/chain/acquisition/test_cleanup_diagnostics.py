"""Finite generated frontier failures outlive refusal diagnostic failures."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.acquisition import (
    workflow,
)

from ..native_products import bindings
from .test_capture import capture_api


@pytest.mark.parametrize("diagnostics", ["ordinary", "notes", "annotation", "format"])
def test_refusal_receipt_diagnostic_preserves_primary(
    chain_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    diagnostics: str,
) -> None:
    """A failed generated request plan never grants even one transport call."""

    class Primary(OSError):
        def add_note(self, note: str) -> None:
            if diagnostics == "annotation":
                raise RuntimeError("generated annotation failure")
            super().add_note(note)

    class Unprintable(OSError):
        def __str__(self) -> str:
            raise RuntimeError("generated formatting failure")

    primary = Primary("generated plan refusal")
    if diagnostics == "notes":
        primary.__notes__ = ()  # type: ignore[assignment]
    calls: list[str] = []

    def control(path: Path, payload: Any, writer: Any) -> str:
        calls.append(path.name)
        if path.name == "request-plan.json":
            raise primary
        assert path.name == "refusal.json"
        if diagnostics == "format":
            raise Unprintable()
        raise OSError("generated receipt failure")

    monkeypatch.setattr(workflow, "_control", control)
    destination = tmp_path / "capture"
    with pytest.raises(Primary) as caught:
        capture_api()(
            destination,
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=lambda *args, **kwargs: pytest.fail("No transport permitted"),
        )
    assert caught.value is primary
    assert calls == ["request-plan.json", "refusal.json"]
    assert not destination.exists()
    if diagnostics == "ordinary":
        assert any(
            "Frontier refusal receipt failed" in note for note in primary.__notes__
        )
    elif diagnostics == "notes":
        assert vars(primary)["__notes__"] == ()
