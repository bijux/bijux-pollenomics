"""Current source obligations survive preparation and body-copy boundaries."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


@pytest.mark.parametrize("stage", ["after_prepare", "during_prepare", "during_copy"])
def test_capsule_context_drift_refuses_before_another_body(
    capsule_inputs: dict[str, Any], tmp_path: Path, monkeypatch: Any, stage: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        publication,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule.validation import (
        prepare_capsule,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import replay
    from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _read

    permission = capsule_inputs["context_directory"] / "manifest.json"
    prepare, copied, replayed = (
        prepare_capsule,
        _read,
        _read,
    )
    preparing = False
    mutated = False
    after_drift: list[Path] = []
    roots = {
        *capsule_inputs["facet_captures"].values(),
        *capsule_inputs["linked_captures"].values(),
    }

    def revoke() -> None:
        nonlocal mutated
        permission.write_bytes(permission.read_bytes() + b"\n")
        mutated = True

    def prepared(**kwargs: Any) -> Any:
        nonlocal preparing
        preparing = True
        result = prepare(**kwargs)
        preparing = False
        if stage == "after_prepare":
            revoke()
        return result

    def observe(
        path: Path, bound: int, original: Callable[[Path, int], bytes], active: bool
    ) -> bytes:
        if path.parent in roots and path.suffix == ".body" and mutated:
            after_drift.append(path)
        raw = original(path, bound)
        if active and path.parent in roots and path.suffix == ".body" and not mutated:
            revoke()
        return raw

    monkeypatch.setattr(publication, "prepare_capsule", prepared)
    monkeypatch.setattr(
        publication,
        "_read",
        lambda path, bound: observe(
            path, bound, copied, stage == "during_copy" and not preparing
        ),
    )
    monkeypatch.setattr(
        replay,
        "_read",
        lambda path, bound: observe(
            path, bound, replayed, stage == "during_prepare" and preparing
        ),
    )
    with pytest.raises(ValueError):
        publication.write_neotoma_ancillary_capsule(
            tmp_path / "refused-capsule", **capsule_inputs
        )
    assert mutated
    assert after_drift == []
