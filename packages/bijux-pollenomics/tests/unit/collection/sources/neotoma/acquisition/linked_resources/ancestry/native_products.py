"""Receipt-captured taxonomy seeds and their independent complete native context."""

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
    NeotomaLinkedResourcePlan,
    NeotomaLinkedTarget,
    capture_neotoma_linked_resources,
)

from ...resources.native_payloads import response
from ..evidence.native_products import payload


@pytest.fixture
def ancestry_products(
    scoped_inputs: dict[str, Any], tmp_path: Path, request: pytest.FixtureRequest
) -> dict[str, Any]:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        NeotomaLinkedEvidence,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.profiles import (
        _PUBLICATION_FIELDS,
    )

    inputs = scoped_inputs
    state_pin, state = next(iter(inputs["evidence_sources"].items()))
    evidence = NeotomaLinkedEvidence(state, state_pin)
    capture = tmp_path / "complete-global-details"
    options = getattr(request, "param", {})
    native = {}
    for identity, parent in [(11, 12), (12, 15)]:
        row = {
            **payload(201, "taxa")["data"][0],
            "taxonid": identity,
            "taxoncode": "Native",
            "highertaxonid": parent,
            "taxagroupid": "VPL",
        }
        row["highertaxonid"] = options.get(f"parent{identity}", parent)
        row["taxonid"] = options.get(f"child{identity}", identity)
        if options.get("missing_parent") == identity:
            row.pop("highertaxonid")
        rows = [row]
        if options.get("ecological_rows") == identity:
            rows.append({**row, "ecolgroup": "TRSH"})
        native[f"taxon-{identity}"] = {
            "status": "success",
            "data": rows,
            "message": "Literal detail",
        }
    publication: dict[str, Any] = dict.fromkeys(_PUBLICATION_FIELDS)
    publication.update(
        publicationid=13, pubtypeid=1, pubtype="Source type", author=[], datasets=[]
    )
    native["publication-13"] = {
        "status": "success",
        "data": [{"publication": publication}],
        "message": "Literal citation",
    }
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
        load_neotoma_ancillary_context,
    )

    context = load_neotoma_ancillary_context(
        inputs["context_directory"],
        expected_manifest_sha256=inputs["expected_context_sha256"],
        native_archive_directory=inputs["native_archive_directory"],
    )

    def fetch(url: str, **_: Any) -> Any:
        route, identifier = url.rsplit("/", 2)[-2:]
        key = ("taxon" if route == "taxa" else "publication") + "-" + identifier
        assert key in native, "Protected or unrequested detail transport"
        return response(url, json.dumps(native[key]).encode())

    result = capture_neotoma_linked_resources(
        capture,
        plan=NeotomaLinkedResourcePlan(
            tuple(sorted(inputs["predecessor_facets"])),
            (
                NeotomaLinkedTarget("taxon", 11),
                NeotomaLinkedTarget("taxon", 12),
                NeotomaLinkedTarget("publication", 13),
                NeotomaLinkedTarget("contact", 900),
            ),
            include_higher_taxa=True,
        ),
        source_facets=inputs["predecessor_facets"],
        scope_inputs=context.current_scope_inputs,
        evidence=evidence,
        fetch=fetch,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        NeotomaTaxonAncestrySources,
    )

    sources = NeotomaTaxonAncestrySources(
        evidence=evidence,
        capture_sources={result.manifest_sha256: capture},
        source_facets=inputs["predecessor_facets"],
        context_directory=inputs["context_directory"],
        expected_context_sha256=inputs["expected_context_sha256"],
        native_archive_directory=inputs["native_archive_directory"],
        expected_native_archive_sha256=sha256(
            (inputs["native_archive_directory"] / "manifest.json").read_bytes()
        ).hexdigest(),
    )
    return {"sources": sources, "capture": capture, "native": native}
