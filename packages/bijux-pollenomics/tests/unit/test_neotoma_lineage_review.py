from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.lineage import (
    LINEAGE_SCHEMA_VERSION,
    build_neotoma_compact_lineage,
    write_neotoma_compact_lineage,
)
from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.production import (
    load_validated_neotoma_raw_archive,
)
from bijux_pollenomics.collection.sources.neotoma.refresh_review import (
    BASELINE_SCHEMA_VERSION,
    build_neotoma_refresh_baseline,
    build_neotoma_refresh_review,
    write_neotoma_refresh_baseline,
    write_neotoma_refresh_review,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)


def _write_json(path: Path, payload: object) -> bytes:
    content = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return content


def _download_row(dataset_id: int) -> dict[str, object]:
    return {
        "site": {
            "siteid": dataset_id,
            "sitename": f"Site {dataset_id}",
            "geopolitical": ["Sweden"],
            "collectionunit": {
                "collectionunitid": 100 + dataset_id,
                "defaultchronology": None,
                "chronologies": [],
                "dataset": {
                    "datasetid": dataset_id,
                    "datasettype": "pollen",
                    "samples": [
                        {
                            "sampleid": 1_000 + dataset_id,
                            "analysisunitid": 2_000 + dataset_id,
                            "depth": dataset_id,
                            "ages": [
                                {
                                    "age": 100 + dataset_id,
                                    "ageyounger": 90 + dataset_id,
                                    "ageolder": 110 + dataset_id,
                                    "agetype": "Calibrated radiocarbon years BP",
                                }
                            ],
                            "datum": [
                                {
                                    "taxonid": 1947,
                                    "variablename": "Poaceae (Cerealia-type)",
                                    "taxongroup": "Vascular plants",
                                    "ecologicalgroup": "UPHE",
                                    "element": "pollen",
                                    "elementtype": "pollen",
                                    "units": "NISP",
                                    "value": 0,
                                    "context": None,
                                }
                            ],
                        }
                    ],
                },
            },
            "dataset": {"datasetid": dataset_id, "datasettype": "pollen"},
        }
    }


def _raw_archive(root: Path) -> None:
    parts: list[dict[str, object]] = []
    for part_number in range(1, 10):
        filename = f"part-{part_number:03d}.json"
        payload = {
            "generated_on": "2026-04-01",
            "source": "Neotoma",
            "endpoint_template": (
                "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}"
            ),
            "datasettype": "pollen",
            "part_number": part_number,
            "part_count": 9,
            "row_count": 1,
            "downloaded_dataset_count": 1,
            "downloaded_dataset_ids": [part_number],
            "rows": [_download_row(part_number)],
        }
        content = _write_json(root / filename, payload)
        parts.append(
            {
                "filename": filename,
                "part_number": part_number,
                "row_count": 1,
                "downloaded_dataset_count": 1,
                "downloaded_dataset_ids": [part_number],
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    _write_json(
        root / "manifest.json",
        {
            "generated_on": "2026-04-01",
            "source": "Neotoma",
            "archive_dir": "raw/neotoma_pollen_dataset_downloads",
            "endpoint_template": (
                "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}"
            ),
            "datasettype": "pollen",
            "requested_dataset_count": 9,
            "requested_dataset_ids": list(range(1, 10)),
            "downloaded_dataset_count": 9,
            "downloaded_dataset_ids": list(range(1, 10)),
            "row_count": 9,
            "rows_per_part": 1,
            "part_count": 9,
            "parts": parts,
        },
    )


def _fixture(root: Path) -> tuple[Path, Path, Path, Path]:
    raw_root = root / "raw"
    relational_root = root / "relational"
    compact_path = root / "compact.geojson"
    lineage_path = root / "lineage.json"
    _raw_archive(raw_root)
    raw_rows, source_snapshot_id = load_validated_neotoma_raw_archive(raw_root)
    snapshot = build_neotoma_relational_snapshot(
        raw_rows,
        source_snapshot_id=source_snapshot_id,
        build_id="fixture-build",
        country_by_site_id={index: "Sweden" for index in range(1, 10)},
    )
    materialize_neotoma_relational_snapshot(
        relational_root.resolve(), snapshot, rows_per_part=3
    )
    _write_json(
        compact_path,
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [1.0, 1.0]},
                    "properties": {
                        "source": "Neotoma",
                        "record_id": str(index),
                        "name": f"Site {index}",
                    },
                }
                for index in range(1, 10)
            ],
        },
    )
    write_neotoma_compact_lineage(
        lineage_path,
        compact_geojson_path=compact_path,
        relational_root=relational_root,
        compact_public_path="data/neotoma/normalized/fixture.geojson",
        relational_public_root="data/neotoma/relational",
    )
    return raw_root, relational_root, compact_path, lineage_path


def _rehash_baseline(payload: dict[str, object]) -> None:
    payload.pop("baseline_id", None)
    content = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode()
    payload["baseline_id"] = "sha256:" + hashlib.sha256(content).hexdigest()


def test_compact_lineage_provides_complete_forward_and_reverse_traces(
    tmp_path: Path,
) -> None:
    _, relational_root, compact_path, lineage_path = _fixture(tmp_path)

    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    assert lineage["schema_version"] == LINEAGE_SCHEMA_VERSION
    assert lineage["status"] == "complete"
    assert lineage["summary"]["compact_record_count"] == 9
    assert lineage["summary"]["linked_compact_record_count"] == 9
    assert lineage["summary"]["sites_with_sample_evidence_count"] == 9
    assert lineage["summary"]["representative_sample_reverse_trace_count"] == 9
    assert len(lineage["compact_to_relational"]) == 9
    assert len(lineage["relational_to_compact"]) == 9
    assert len(lineage["representative_sample_to_compact"]) == 9

    forward = lineage["compact_to_relational"][0]
    assert forward["relational_site_id"] == "neotoma:site:1"
    assert forward["detail_row_counts"]["samples"] == 1
    assert forward["detail_row_counts"]["observations"] == 1
    assert forward["sample_evidence_status"] == "linked"
    assert forward["sample_evidence_locator"]["identity_value"] == (
        "neotoma:sample:1001"
    )
    assert forward["observation_evidence_locator"]["identity_value"].startswith(
        "neotoma:observation:1001:"
    )
    reverse = lineage["relational_to_compact"][0]
    assert reverse["compact_record_id"] == "1"
    assert reverse["compact_locator"]["json_pointer"] == "/features/0/properties"
    sample_reverse = lineage["representative_sample_to_compact"][0]
    assert sample_reverse["sample_id"] == "neotoma:sample:1001"
    assert sample_reverse["compact_record_id"] == "1"
    assert (relational_root / "surfaces/samples/part-00001.json").is_file()

    second = build_neotoma_compact_lineage(
        compact_geojson_path=compact_path,
        relational_root=relational_root,
        compact_public_path="data/neotoma/normalized/fixture.geojson",
    )
    assert second == lineage


def test_compact_lineage_refuses_absent_or_unmatched_inputs(tmp_path: Path) -> None:
    refusal = build_neotoma_compact_lineage(
        compact_geojson_path=tmp_path / "missing.geojson",
        relational_root=tmp_path / "missing-relational",
    )
    assert refusal["status"] == "refused"
    assert refusal["refusal_reasons"] == [
        "missing_compact_site_layer",
        "missing_relational_detail",
    ]

    _, relational_root, compact_path, _ = _fixture(tmp_path / "unmatched")
    compact = json.loads(compact_path.read_text(encoding="utf-8"))
    compact["features"][0]["properties"]["record_id"] = "999"
    _write_json(compact_path, compact)
    unmatched = build_neotoma_compact_lineage(
        compact_geojson_path=compact_path,
        relational_root=relational_root,
    )
    assert unmatched["status"] == "refused"
    unmatched_summary = unmatched["summary"]
    assert isinstance(unmatched_summary, dict)
    assert unmatched_summary["compact_without_relational_count"] == 1
    assert unmatched_summary["relational_without_compact_count"] == 1


def test_refresh_baseline_is_immutable_and_fixed_point_is_zero_diff(
    tmp_path: Path,
) -> None:
    raw_root, relational_root, compact_path, lineage_path = _fixture(tmp_path)
    baseline = build_neotoma_refresh_baseline(
        raw_archive_root=raw_root,
        relational_root=relational_root,
        compact_geojson_path=compact_path,
        lineage_path=lineage_path,
        compact_public_path="data/neotoma/normalized/fixture.geojson",
        lineage_public_path="data/neotoma/review/fixture-lineage.json",
    )
    assert baseline["schema_version"] == BASELINE_SCHEMA_VERSION
    baseline_counts = baseline["counts"]
    assert isinstance(baseline_counts, dict)
    assert baseline_counts["raw_download_rows"] == 9
    assert baseline_counts["relational_observations"] == 9

    review = build_neotoma_refresh_review(baseline, copy.deepcopy(baseline))
    assert review["status"] == "fixed_point"
    assert review["fixed_point"] is True
    assert review["change_count"] == 0
    zero_diff_proof = review["zero_diff_proof"]
    assert isinstance(zero_diff_proof, dict)
    assert all(zero_diff_proof.values())

    baseline_path = tmp_path / "baseline.json"
    write_neotoma_refresh_baseline(
        baseline_path,
        raw_archive_root=raw_root,
        relational_root=relational_root,
        compact_geojson_path=compact_path,
        lineage_path=lineage_path,
    )
    first = baseline_path.read_bytes()
    write_neotoma_refresh_baseline(
        baseline_path,
        raw_archive_root=raw_root,
        relational_root=relational_root,
        compact_geojson_path=compact_path,
        lineage_path=lineage_path,
    )
    assert baseline_path.read_bytes() == first
    baseline_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="review drift before replacing"):
        write_neotoma_refresh_baseline(
            baseline_path,
            raw_archive_root=raw_root,
            relational_root=relational_root,
            compact_geojson_path=compact_path,
            lineage_path=lineage_path,
        )

    compact = json.loads(compact_path.read_text(encoding="utf-8"))
    compact["features"][0]["properties"]["name"] = "Changed site label"
    _write_json(compact_path, compact)
    with pytest.raises(ValueError, match="does not bind the candidate compact layer"):
        build_neotoma_refresh_baseline(
            raw_archive_root=raw_root,
            relational_root=relational_root,
            compact_geojson_path=compact_path,
            lineage_path=lineage_path,
        )


def test_refresh_diff_reports_counts_and_requires_explanation_review(
    tmp_path: Path,
) -> None:
    raw_root, relational_root, compact_path, lineage_path = _fixture(tmp_path)
    prior = build_neotoma_refresh_baseline(
        raw_archive_root=raw_root,
        relational_root=relational_root,
        compact_geojson_path=compact_path,
        lineage_path=lineage_path,
    )
    candidate = copy.deepcopy(prior)
    candidate_counts = candidate["counts"]
    assert isinstance(candidate_counts, dict)
    candidate_counts["relational_observations"] = 11
    with pytest.raises(ValueError, match="baseline_id does not match its content"):
        build_neotoma_refresh_review(prior, candidate)
    _rehash_baseline(candidate)

    unexplained = build_neotoma_refresh_review(prior, candidate)
    assert unexplained["status"] == "review_required"
    assert unexplained["baseline_update_permitted"] is False
    assert unexplained["unexplained_change_count"] == 1
    assert unexplained["changes"] == [
        {
            "change_id": "counts:relational_observations",
            "section": "counts",
            "field": "relational_observations",
            "change_kind": "increased",
            "prior": 9,
            "candidate": 11,
            "explanation": None,
            "delta": 2,
        }
    ]
    explained = build_neotoma_refresh_review(
        prior,
        candidate,
        explanations={"counts:relational_observations": "documented source refresh"},
    )
    assert explained["unexplained_change_count"] == 0
    assert explained["status"] == "review_required"
    assert explained["baseline_update_permitted"] is False

    refused_path = tmp_path / "refused.json"
    write_neotoma_refresh_review(
        refused_path,
        baseline_path=tmp_path / "missing-baseline.json",
        raw_archive_root=tmp_path / "missing-raw",
        relational_root=tmp_path / "missing-relational",
        compact_geojson_path=tmp_path / "missing-compact",
        lineage_path=tmp_path / "missing-lineage",
    )
    refusal = json.loads(refused_path.read_text(encoding="utf-8"))
    assert refusal["status"] == "refused"
    assert refusal["baseline_update_permitted"] is False
    assert "missing_prior_baseline" in refusal["refusal_reasons"]
    assert "missing_candidate_raw_archive" in refusal["refusal_reasons"]
