"""One ancestry operation validates complete evidence once across native captures."""

import json
from pathlib import Path
from typing import Any

from .native_products import observe_work


def test_multi_capture_derivation_validates_complete_evidence_once(
    session_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
    )

    work = observe_work(monkeypatch)
    document = derive_neotoma_taxon_ancestry(session_products["sources"])
    (tmp_path / "derivation-work.json").write_text(json.dumps(work, indent=2))
    (tmp_path / "reference-document.json").write_text(
        json.dumps(document, sort_keys=True, indent=2)
    )
    sources = session_products["sources"]
    (tmp_path / "source-bindings.json").write_text(
        json.dumps(
            {
                "evidence": {
                    "directory": str(sources.evidence.directory),
                    "manifest_sha256": sources.evidence.manifest_sha256,
                },
                "capture_sources": {
                    k: str(v) for k, v in sources.capture_sources.items()
                },
                "source_facets": {k: str(v) for k, v in sources.source_facets.items()},
                "context_directory": str(sources.context_directory),
                "expected_context_sha256": sources.expected_context_sha256,
                "native_archive_directory": str(sources.native_archive_directory),
                "expected_native_archive_sha256": sources.expected_native_archive_sha256,
            },
            indent=2,
        )
    )
    assert document["summary"]["declared_seed_taxa"] == 2
    assert work["native_detail_opens"] == 11
    assert work["loader_calls"] == 1
