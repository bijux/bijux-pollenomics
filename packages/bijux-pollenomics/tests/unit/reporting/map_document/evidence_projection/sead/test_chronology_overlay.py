"""Controls for opt-in SEAD derived chronology in Atlas details."""

from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.evidence_projection.sead.chronology_overlay import (
    apply_overlay,
)
from bijux_pollenomics.reporting.map_document.evidence_projection.sead.models import (
    ClaimIndex,
)


def claims() -> ClaimIndex:
    rows: list[Mapping[str, object]] = [
        {
            "chronology_claim_id": "a",
            "source_site_id": "1",
            "source_age_value": {"age": 42, "time_start_bp": 10, "time_end_bp": 20},
            "original_interval_orientation": "younger_to_older",
            "chronology_eligibility": "refused",
            "observation_relation_id": "entity",
            "linked_source_native_observation_count": 1,
            "observation_link_status": "linked",
            "propagation_reason_codes": ["refused"],
        },
        {
            "chronology_claim_id": "b",
            "source_site_id": "1",
            "source_age_value": {"age": 0, "time_start_bp": 0, "time_end_bp": 0},
            "original_interval_orientation": "point",
            "chronology_eligibility": "refused",
        },
    ]
    return ClaimIndex(
        rows=rows, by_site={"1": list(rows)}, country_counts=Counter({"SE": 2})
    )


def overlay() -> dict[str, Any]:
    return {
        "claim_count": 2,
        "claim_id_set_sha256": hashlib.sha256(
            json.dumps(["a", "b"], separators=(",", ":")).encode()
        ).hexdigest(),
        "changed_claim_count": 1,
        "changes": [
            {
                "chronology_claim_id": "a",
                "time_start_bp": None,
                "time_end_bp": None,
                "original_interval_orientation": "unavailable",
            }
        ],
    }


def test_apply_overlay_copies_claims_and_preserves_relation_fields() -> None:
    original = claims()
    before = deepcopy(original)
    revised = apply_overlay(original, overlay())
    assert original == before
    first = revised.by_site["1"][0]
    assert first["source_age_value"] == {
        "age": 42,
        "time_start_bp": None,
        "time_end_bp": None,
    }
    assert first["chronology_eligibility"] == "refused"
    assert first["observation_relation_id"] == "entity"
    assert first["linked_source_native_observation_count"] == 1
    assert first["observation_link_status"] == "linked"
    assert first["propagation_reason_codes"] == ["refused"]
    assert revised.rows[1] == original.rows[1]


@pytest.mark.parametrize(
    "corruption", ["foreign", "duplicate", "extra", "count", "set_digest", "missing"]
)
def test_refuse_bad_overlay(corruption: str) -> None:
    value = overlay()
    if corruption == "foreign":
        value["changes"][0]["chronology_claim_id"] = "unknown"
    elif corruption == "duplicate":
        value["changes"].append(deepcopy(value["changes"][0]))
        value["changed_claim_count"] = 2
    elif corruption == "extra":
        value["changes"][0]["chronology_eligibility"] = "eligible"
    elif corruption == "count":
        value["claim_count"] = 1
    elif corruption == "set_digest":
        value["claim_id_set_sha256"] = "0" * 64
    else:
        del value["changes"][0]["time_start_bp"]
    with pytest.raises(ValueError):
        apply_overlay(claims(), value)


def test_site_binding_refuses_mismatched_layer_and_source(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.map_document.evidence_projection.sead.site_custody import (
        validate_site_binding,
    )

    source: dict[str, Any] = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [12.0, 55.0]},
                "properties": {
                    "record_id": "1",
                    "layer_key": "sead-sites",
                    "layer_label": "SEAD sites",
                    "site_uuid": "uuid",
                    "country": "Sweden",
                    "time_start_bp": None,
                    "time_end_bp": None,
                },
            }
        ],
    }
    normalized = tmp_path / "sead/normalized"
    normalized.mkdir(parents=True)
    payload = json.dumps(source).encode()
    (normalized / "nordic_environmental_sites.geojson").write_bytes(payload)
    lineage = {
        "normalized_surface_sha256": {
            "normalized/nordic_environmental_sites.geojson": hashlib.sha256(
                payload
            ).hexdigest()
        }
    }
    lineage_bytes = json.dumps(lineage).encode()
    (normalized / "source_lineage.json").write_bytes(lineage_bytes)
    rows = {"1": source["features"][0]["properties"]}
    from bijux_pollenomics.reporting.context.points.external import (
        build_external_point_layer,
    )

    layers: list[dict[str, Any]] = [
        build_external_point_layer(
            source, source_path=normalized / "nordic_environmental_sites.geojson"
        )
    ]
    pin = hashlib.sha256(lineage_bytes).hexdigest()
    validate_site_binding(tmp_path, pin, rows, layers)
    original_title = layers[0]["features"][0]["title"]
    layers[0]["features"][0]["title"] = "tampered"
    with pytest.raises(ValueError, match="site"):
        validate_site_binding(tmp_path, pin, rows, layers)
    layers[0]["features"][0]["title"] = original_title
    layers[0]["default_enabled"] = not layers[0]["default_enabled"]
    with pytest.raises(ValueError, match="site"):
        validate_site_binding(tmp_path, pin, rows, layers)
    layers[0]["default_enabled"] = not layers[0]["default_enabled"]
    layers[0]["features"][0]["longitude"] = 12.1
    with pytest.raises(ValueError, match="site"):
        validate_site_binding(tmp_path, pin, rows, layers)
    layers[0]["features"][0]["longitude"] = 12.0
    layers[0]["features"][0]["time_start_bp"] = 0
    with pytest.raises(ValueError, match="site"):
        validate_site_binding(tmp_path, pin, rows, layers)


def test_opt_in_projects_copied_chronology_and_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.sead.evidence import (
        chronology_overlay as owner,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection import (
        sead as projection,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection.sead.chronology_overlay import (
        HistoricalChronologyRequest,
    )
    from tests.support.sead_evidence import (
        install_sead_projection_fixture,
        sead_projection_layers,
    )

    from ..fixtures.common import _decode_sead_claim_table

    root = tmp_path.absolute()
    install_sead_projection_fixture(root, monkeypatch)
    from bijux_pollenomics.reporting.map_document.evidence_projection import service

    for name in (
        "SEAD_GOVERNED_EVIDENCE_RUN_ID",
        "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
        "SEAD_GOVERNED_ADMISSION_SHA256",
    ):
        monkeypatch.setattr(service, name, vars(projection)[name])
    base_records, _ = projection._project_sead(root, sead_projection_layers()[1:])
    tabs = cast(
        dict[str, Any],
        next(r["tabs"] for r in base_records if r["record_id"] == "sead:site:2"),
    )
    old = cast(dict[str, Any], _decode_sead_claim_table(tabs["chronology"])[0])
    claim_id = old["chronology_claim_id"]
    patch = {
        "schema_version": "sead-historical-derived-chronology-overlay.v1",
        "source_run_id": vars(projection)["SEAD_GOVERNED_EVIDENCE_RUN_ID"],
        "admission_sha256": vars(projection)["SEAD_GOVERNED_ADMISSION_SHA256"],
        "evidence_manifest_sha256": vars(projection)[
            "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256"
        ],
        "lineage_sha256": "placeholder",
        "claim_count": 1,
        "claim_id_set_sha256": hashlib.sha256(
            json.dumps([claim_id], separators=(",", ":")).encode()
        ).hexdigest(),
        "changed_claim_count": 1,
        "changes": [
            {
                "chronology_claim_id": claim_id,
                "time_start_bp": None,
                "time_end_bp": None,
                "original_interval_orientation": "unavailable",
            }
        ],
        "producer_code_identity": "external_execution_receipt_required",
    }
    site = root / "sead/normalized/nordic_environmental_sites.geojson"
    lineage = {
        "normalized_surface_sha256": {
            "normalized/nordic_environmental_sites.geojson": hashlib.sha256(
                site.read_bytes()
            ).hexdigest()
        }
    }
    lineage_bytes = json.dumps(lineage).encode()
    (root / "sead/normalized/source_lineage.json").write_bytes(lineage_bytes)
    pin = hashlib.sha256(lineage_bytes).hexdigest()
    patch["lineage_sha256"] = pin
    monkeypatch.setattr(
        owner, "build_historical_chronology_overlay", lambda *a, **kw: patch
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection import (
        build_map_evidence_projection,
    )

    selected_layers = sead_projection_layers()[1:]
    from bijux_pollenomics.reporting.context.points.external import (
        build_external_point_layer,
    )

    selected_layers[0] = build_external_point_layer(
        json.loads(site.read_bytes()), source_path=site
    )
    projection_result = build_map_evidence_projection(
        root,
        selected_layers,
        historical_chronology=HistoricalChronologyRequest(tmp_path, pin),
    )
    result = projection_result.detail_records
    accounting = cast(
        dict[str, Any],
        cast(dict[str, Any], projection_result.reconciliation["sources"])["sead"],
    )
    new_tabs = cast(
        dict[str, Any],
        next(r["tabs"] for r in result if r["record_id"] == "sead:site:2"),
    )
    new = cast(dict[str, Any], _decode_sead_claim_table(new_tabs["chronology"])[0])
    assert new["source_age_value"]["time_start_bp"] is None
    assert {
        k: v
        for k, v in new["source_age_value"].items()
        if k not in {"time_start_bp", "time_end_bp"}
    } == {
        k: v
        for k, v in old["source_age_value"].items()
        if k not in {"time_start_bp", "time_end_bp"}
    }
    assert new["chronology_eligibility"] == old["chronology_eligibility"]
    assert new["observation_relation_id"] == old["observation_relation_id"]
    assert new_tabs["provenance"]["derived_chronology"]["lineage_sha256"] == pin
    assert accounting["derived_chronology"]["changed_claim_count"] == 1


def test_public_projection_refuses_opt_in_without_sead_layer(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.map_document.evidence_projection import (
        build_map_evidence_projection,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection.sead.chronology_overlay import (
        HistoricalChronologyRequest,
    )

    with pytest.raises(ValueError, match="SEAD"):
        build_map_evidence_projection(
            tmp_path.absolute(),
            [],
            historical_chronology=HistoricalChronologyRequest(
                tmp_path.absolute(), "0" * 64
            ),
        )


def test_staged_site_copy_requires_exact_selected_bytes(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.map_document.evidence_projection.sead.site_custody import (
        validate_staged_site_copy,
    )

    normalized = tmp_path / "data/sead/normalized"
    normalized.mkdir(parents=True)
    staged = tmp_path / "atlas"
    staged.mkdir()
    content = b'{"type":"FeatureCollection","features":[]}'
    (normalized / "nordic_environmental_sites.geojson").write_bytes(content)
    (staged / "nordic_environmental_sites.geojson").write_bytes(content)
    lineage = json.dumps(
        {
            "normalized_surface_sha256": {
                "normalized/nordic_environmental_sites.geojson": hashlib.sha256(
                    content
                ).hexdigest()
            }
        }
    ).encode()
    (normalized / "source_lineage.json").write_bytes(lineage)
    pin = hashlib.sha256(lineage).hexdigest()
    validate_staged_site_copy(tmp_path / "data", staged, pin)
    (staged / "nordic_environmental_sites.geojson").write_bytes(content + b" ")
    with pytest.raises(ValueError, match="staged SEAD site"):
        validate_staged_site_copy(tmp_path / "data", staged, pin)


def test_public_map_refuses_mutated_staged_site_before_attachment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    from bijux_pollenomics.reporting import service
    from bijux_pollenomics.reporting.map_document.evidence_projection.sead.chronology_overlay import (
        HistoricalChronologyRequest,
    )

    root = tmp_path / "data"
    normalized = root / "sead/normalized"
    normalized.mkdir(parents=True)
    site = b'{"type":"FeatureCollection","features":[]}'
    (normalized / "nordic_environmental_sites.geojson").write_bytes(site)
    lineage = json.dumps(
        {
            "normalized_surface_sha256": {
                "normalized/nordic_environmental_sites.geojson": hashlib.sha256(
                    site
                ).hexdigest()
            }
        }
    ).encode()
    (normalized / "source_lineage.json").write_bytes(lineage)
    request = HistoricalChronologyRequest(root, hashlib.sha256(lineage).hexdigest())
    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(
            country_sample_counts={"Sweden": 0}, all_samples=()
        ),
    )

    def publish(staging: Path, **kwargs: Any) -> None:
        assert kwargs["historical_chronology"] is request
        (staging / "nordic_environmental_sites.geojson").write_bytes(site + b" ")

    monkeypatch.setattr(service, "publish_multi_country_map_bundle", publish)
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="staged SEAD site"):
        service.generate_multi_country_map(
            tmp_path / "v66",
            ("Sweden",),
            output,
            "Map",
            "nordic",
            context_root=root,
            historical_chronology=request,
        )
    assert not output.exists()
