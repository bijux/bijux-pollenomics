"""Selected native resource source custody controls."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import resource_catalogue as api


@pytest.mark.parametrize(
    "mutation", ["body_drift", "missing_resolver", "receipt_drift"]
)
def test_selected_source_custody_is_mandatory(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    mutation: str,
    resource_reader: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[[dict[str, Any]], tuple[Path, str, dict[str, Path]]],
) -> None:
    read = resource_reader
    inputs = catalogue_sources()
    output, digest, sources = publish_catalogue(inputs)
    root = next(iter(inputs["resource_captures"].values()))
    if mutation == "body_drift":
        path = root / "dataset-201-current-attempt-1.body"
        payload = json.loads(path.read_bytes())
        payload["data"][0]["site"]["collectionunit"]["dataset"]["datasetid"] = 999
        path.write_text(json.dumps(payload))
    elif mutation == "missing_resolver":
        sources = {}
    else:
        next(
            output.glob("captures/*/dataset-201-current-attempt-1.receipt.json")
        ).write_text("{}")
    with pytest.raises(ValueError, match="identity|resolver|source"):
        read(
            output,
            expected_manifest_sha256=digest,
            dataset_id=201,
            version="current",
            capture_sources=sources,
        )


@pytest.mark.parametrize("corrupt_provenance", [False, True])
def test_original_retained_source_keeps_exact_qualified_provenance_scope(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
    corrupt_provenance: bool,
    resource_reader: Callable[..., dict[str, Any]],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
        NeotomaRetainedSource,
        capture_neotoma_resources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.protocol import (
        plan_from_json,
    )

    read = resource_reader
    inputs = catalogue_sources()
    ancestors = inputs["resource_captures"]
    original = next(iter(ancestors.values()))
    plan, _ = plan_from_json(json.loads((original / "request-plan.json").read_bytes()))
    body = original / "dataset-202-current-attempt-1.body"
    body_sha = sha256(body.read_bytes()).hexdigest()
    provenance = tmp_path / "public-source.json"
    retrieved = "2026-11-14T17:32:38.790438+00:00"
    provenance.write_text(
        json.dumps(
            {
                "schema_version": "bokesjon-public-core-sources.v1",
                "sources": [
                    {
                        "source_url": "https://api.neotomadb.org/v2.0/data/downloads/202",
                        "final_url": "https://api.neotomadb.org/v2.0/data/downloads/202",
                        "status": 200,
                        "bytes": body.stat().st_size,
                        "sha256": body_sha,
                        "retrieved_at": retrieved,
                    }
                ],
            }
        )
    )
    retained = {
        "dataset-202-current": NeotomaRetainedSource(
            body, provenance, sha256(provenance.read_bytes()).hexdigest(), body_sha
        )
    }
    reused_root = tmp_path / "retained-capture"
    captured = capture_neotoma_resources(
        reused_root,
        plan=plan,
        reuse_from=ancestors,
        retained_sources=retained,
        fetch=lambda *args, **kwargs: pytest.fail("Retained source performed GET"),
    )
    inputs.update(
        resource_captures={captured.manifest_sha256: reused_root},
        source_captures=ancestors,
        retained_sources=retained,
    )
    catalogue = api.build_neotoma_resource_catalogue(**inputs)
    sources = {
        **inputs["metadata_captures"],
        **inputs["resource_captures"],
        **ancestors,
    }
    output = tmp_path / "public"
    api.write_neotoma_resource_catalogue(
        output,
        catalogue=catalogue,
        roster_path=inputs["roster_path"],
        capture_sources=sources,
        retained_sources=retained,
    )
    digest = sha256((output / "manifest.json").read_bytes()).hexdigest()
    if corrupt_provenance:
        provenance.write_text("{}")
        with pytest.raises(ValueError, match="provenance identity"):
            read(
                output,
                expected_manifest_sha256=digest,
                dataset_id=202,
                version="current",
                capture_sources={},
                retained_sources=retained,
            )
    else:
        result = read(
            output,
            expected_manifest_sha256=digest,
            dataset_id=202,
            version="current",
            capture_sources={},
            retained_sources=retained,
        )
        assert result["native_payload"] == json.loads(body.read_bytes())
        assert result["epoch_kind"] == "original_timed_public_response"
        assert result["source"]["retrieved_at"] == retrieved
        assert "tls_mode" not in result["source"]
        assert (
            result["source"]["http_evidence_scope"]
            == "original recorded fields only; no new request, headers or TLS history invented"
        )
