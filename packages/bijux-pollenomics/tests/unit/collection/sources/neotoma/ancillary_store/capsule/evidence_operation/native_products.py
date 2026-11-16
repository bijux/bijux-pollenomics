"""Twenty-four original source captures share one externally anchored evidence set."""

from copy import deepcopy
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
    load_neotoma_ancillary_context,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    NeotomaLinkedResourcePlan,
    NeotomaLinkedTarget,
    capture_neotoma_linked_resources,
)

from ....acquisition.resources.native_payloads import response


@pytest.fixture
def linked_inputs(
    ancestry_products: dict[str, Any], tmp_path: Path, request: pytest.FixtureRequest
) -> dict[str, Any]:
    """Retain distinct genuine transport receipts without provider access."""
    original = ancestry_products["sources"]
    context = load_neotoma_ancillary_context(
        original.context_directory,
        expected_manifest_sha256=original.expected_context_sha256,
        native_archive_directory=original.native_archive_directory,
    )
    count = getattr(request, "param", 24)
    captures = {}
    for position in range(count):
        native = deepcopy(ancestry_products["native"]["taxon-11"])
        native["message"] = f"Literal generated source response {position}"
        raw = json.dumps(native).encode()
        directory = tmp_path / f"recorded-source-{position}"
        result = capture_neotoma_linked_resources(
            directory,
            plan=NeotomaLinkedResourcePlan(
                tuple(sorted(original.source_facets)),
                (NeotomaLinkedTarget("taxon", 11),),
                include_higher_taxa=True,
            ),
            source_facets=original.source_facets,
            scope_inputs=context.current_scope_inputs,
            evidence=original.evidence,
            fetch=lambda url, response_body=raw, **kwargs: response(url, response_body),
        )
        captures[result.manifest_sha256] = directory
    assert len(captures) == count
    return {
        "context_directory": original.context_directory,
        "expected_context_sha256": original.expected_context_sha256,
        "native_archive_directory": original.native_archive_directory,
        "facet_captures": {},
        "linked_captures": captures,
        "predecessor_facets": original.source_facets,
        "evidence_sources": {
            original.evidence.manifest_sha256: original.evidence.directory,
        },
    }


def observe(monkeypatch: Any) -> dict[str, int]:
    """Count the real complete validator and selected detail descriptor opens."""
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts import (
        validation,
    )

    work = {"complete_validations": 0, "detail_body_opens": 0}
    complete, opened = validation._load_linked_evidence, os.open

    def validate(*args: Any, **kwargs: Any) -> Any:
        work["complete_validations"] += 1
        return complete(*args, **kwargs)

    def open_source(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = opened(path, flags, *args, **kwargs)
        if (
            Path(path).name.startswith("taxon-11-")
            and str(path).endswith(".body")
            and not flags & os.O_DIRECTORY
        ):
            work["detail_body_opens"] += 1
        return descriptor

    monkeypatch.setattr(validation, "_load_linked_evidence", validate)
    monkeypatch.setattr(os, "open", open_source)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {open_source})
    return work
