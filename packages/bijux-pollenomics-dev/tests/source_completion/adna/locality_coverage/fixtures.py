"""Artificial source packets and disjoint specimen intervals, without builders."""

from __future__ import annotations

from copy import deepcopy
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
from typing import Any

CSV_FIELDS = [
    "schema_version",
    "chronology_role",
    "sample_ids",
    "sample_chronologies",
    "locality_token",
    "species_latin_name",
    "species_common_name",
    "project_accessions",
    "source_family",
    "source_releases",
    "record_modalities",
    "review_strengths",
    "provenance_qualities",
    "original_location_text",
    "locality",
    "political_entity",
    "latitude",
    "longitude",
    "latitude_text",
    "longitude_text",
    "coordinate_confidence",
    "chronology_text",
    "time_start_bp",
    "time_end_bp",
    "time_mean_bp",
    "dating_basis",
    "chronology_evidence_class",
    "chronology_precision_posture",
    "nordic_inclusion",
    "nordic_inclusion_reason",
    "interpretation_note",
]


def body(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


def csv_body(localities: list[dict[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for record in localities:
        chronology, coordinates = record["chronology"], record["coordinates"]
        row = {
            key: record[key]
            for key in (
                "chronology_role",
                "species_latin_name",
                "species_common_name",
                "source_family",
                "original_location_text",
                "locality",
                "nordic_inclusion",
                "nordic_inclusion_reason",
                "interpretation_note",
            )
        }
        row.update(
            nordic_inclusion="true" if record["nordic_inclusion"] else "false",
            schema_version="adna-locality-summary-export.v2",
            locality_token=record["identity"]["stable_token"],
            political_entity=record["identity"]["political_entity"],
            sample_chronologies=json.dumps(
                record["sample_chronologies"], ensure_ascii=False, separators=(",", ":")
            ),
            latitude=coordinates["latitude"],
            longitude=coordinates["longitude"],
            latitude_text=coordinates["latitude_text"],
            longitude_text=coordinates["longitude_text"],
            coordinate_confidence=coordinates["confidence"],
            chronology_text=chronology["original_text"],
            time_start_bp=chronology["time_start_bp"],
            time_end_bp=chronology["time_end_bp"],
            time_mean_bp=chronology["time_mean_bp"],
            dating_basis=chronology["dating_basis"],
            chronology_evidence_class=chronology["evidence_class"],
            chronology_precision_posture=chronology["precision_posture"],
        )
        row.update(
            {
                key: ";".join(record[key])
                for key in (
                    "sample_ids",
                    "project_accessions",
                    "source_releases",
                    "record_modalities",
                    "review_strengths",
                    "provenance_qualities",
                )
            }
        )
        writer.writerow(row)
    return stream.getvalue().encode()


def fixture() -> tuple[dict[str, Any], dict[str, bytes], dict[str, bytes], bytes]:
    labels = {
        "dating_basis": "locality_sample_coverage",
        "evidence_class": "locality_sample_coverage_hull",
        "precision_posture": "display_coverage_only",
    }
    normalization = {
        "species_name": "Capra hircus",
        "sample_count": 78,
        "locality_count": 23,
        "sample_support_count": 78,
        "refusal_count": 8,
        "sample_refusal_count": 4,
        "locality_refusal_count": 4,
        "allowed_aggregate_chronology_changes": labels,
    }
    samples: list[dict[str, Any]] = []
    for index in range(78):
        group = index % 23
        project = "PRJEB90261" if group < 12 else "PRJNA1328209"
        owner = project.lower() + f":specimen-{index}"
        chronology = {
            "original_text": f"{100 * index}-{100 * index + 10} BP",
            "time_start_bp": 100 * index,
            "time_end_bp": 100 * index + 10,
            "time_mean_bp": 100 * index + 5,
            "date_stddev_bp": "",
            "source_mean_bp_text": "",
            "dating_basis": "archaeological_period_assignment",
            "evidence_class": "direct_radiocarbon_date",
            "precision_posture": "sample_precise_interval",
            "refusal_reason_code": "",
        }
        samples.append(
            {
                "identity": {"stable_token": "sample:" + owner},
                "locality_identity": {"stable_token": f"locality:{group}"},
                "master_id": owner,
                "project_accession": project,
                "chronology": chronology,
                "source_release": project,
                "chronology_provenance_path": "synthetic-source.tsv",
                "chronology_provenance_locator": f"row{index + 1}",
                "chronology_provenance_text": f"literal specimen {index}",
                "chronology_provenance_kind": "synthetic_source_row",
                "chronology_strength": "sample_owned_interval",
                "chronology_normalization_status": "normalized_interval",
                "chronology_conflict_note": "",
            }
        )
    localities: list[dict[str, Any]] = []
    for group in range(23):
        own = [
            s
            for s in samples
            if s["locality_identity"]["stable_token"] == f"locality:{group}"
        ]
        lo = min(s["chronology"]["time_start_bp"] for s in own)
        hi = max(s["chronology"]["time_end_bp"] for s in own)
        supports = [
            {
                "schema_version": "adna-sample-chronology-support.v1",
                "sample_id": sample["master_id"],
                "chronology": deepcopy(sample["chronology"]),
                "source_release": sample["source_release"],
                "provenance_path": sample["chronology_provenance_path"],
                "provenance_locator": sample["chronology_provenance_locator"],
                "provenance_excerpt": sample["chronology_provenance_text"],
                "provenance_kind": sample["chronology_provenance_kind"],
                "chronology_strength": sample["chronology_strength"],
                "normalization_status": sample["chronology_normalization_status"],
                "conflict_note": sample["chronology_conflict_note"],
                "reference_epoch": "not_separately_declared",
                "age_type": "not_separately_declared",
                "calibration_status": "not_separately_declared",
                "model": "not_separately_declared",
            }
            for sample in own
        ]
        localities.append(
            {
                "identity": {
                    "stable_token": f"locality:{group}",
                    "political_entity": "Synthetic country",
                },
                "species_latin_name": "Capra hircus",
                "species_common_name": "goat",
                "source_family": "synthetic",
                "source_releases": [own[0]["project_accession"]],
                "record_modalities": ["archive_reads"],
                "review_strengths": ["synthetic"],
                "provenance_qualities": ["synthetic"],
                "locality": f"Synthetic site {group}",
                "coordinates": {
                    "latitude": 50.0 + group / 100,
                    "longitude": None,
                    "latitude_text": "native latitude",
                    "longitude_text": "",
                    "confidence": "unknown",
                },
                "sample_count": len(own),
                "sample_ids": [s["master_id"] for s in own],
                "datasets": ["synthetic"],
                "chronology": {
                    "original_text": f"{lo}-{hi} BP",
                    "time_start_bp": lo,
                    "time_end_bp": hi,
                    "time_mean_bp": (lo + hi) // 2,
                    "date_stddev_bp": "",
                    "source_mean_bp_text": "",
                    "dating_basis": "archaeological_period_assignment",
                    "evidence_class": "direct_radiocarbon_date",
                    "precision_posture": "sample_precise_interval",
                    "refusal_reason_code": "",
                },
                "chronology_role": "locality_sample_coverage_hull",
                "sample_chronologies": supports,
                "sample_namespace": "synthetic",
                "project_accessions": [own[0]["project_accession"]],
                "original_location_text": f"Literal site {group}",
                "nordic_inclusion": False,
                "nordic_inclusion_reason": "synthetic",
                "interpretation_note": "No field claim",
            }
        )
    refusals = [
        {
            "record_kind": kind,
            "source_token": f"refused:{kind}:{i}",
            "reason": "source_identity_not_admitted",
        }
        for kind in ("sample_record", "locality_records")
        for i in range(4)
    ]
    baseline_bundle: dict[str, Any] = {
        "schema_version": "adna-nonhuman-normalization-bundle.v1",
        "sample_records": samples,
        "locality_records": localities,
        "refusals": refusals,
        "coordinate_provenance_records": [{"source": "synthetic-coordinate"}],
        "site_evidence_records": [{"source": "synthetic-site"}],
        "project_summaries": [
            {"project_accession": p}
            for p in ("PRJEB90141", "PRJEB90261", "PRJNA1328209")
        ],
        "study_summaries": [{"source": "synthetic-study"}],
        "lineage_records": [{"source": "synthetic-lineage"}],
        "normalization_scope": "source-owned specimens; no new admission",
    }
    baseline_json: dict[str, Any] = {
        "schema_version": "adna-locality-summary-export.v2",
        "species_latin_name": "Capra hircus",
        "localities": localities,
    }
    candidate_bundle = deepcopy(baseline_bundle)
    for locality in candidate_bundle["locality_records"]:
        locality["chronology"].update(labels)
    candidate_json = {
        **baseline_json,
        "localities": candidate_bundle["locality_records"],
    }
    canonical = {
        "schema_version": "adna-sample-record-export.v1",
        "admitted_sample_count": 78,
        "refused_sample_count": 4,
        "samples": samples,
        "sample_refusals": refusals[:4],
    }
    return (
        normalization,
        {
            "locality_json": body(baseline_json),
            "locality_csv": csv_body(localities),
            "bundle": body(baseline_bundle),
        },
        {
            "locality_json": body(candidate_json),
            "locality_csv": csv_body(candidate_json["localities"]),
            "bundle": body(candidate_bundle),
        },
        body(canonical),
    )


def closed_fixture(
    root: Path,
) -> tuple[Path, Path, Path, dict[str, Any], dict[str, Any]]:
    """Build an artificial closed export and custody records without a normalizer."""
    repository = root / "repository"
    products = repository / "artifacts/producer"
    products.mkdir(parents=True)
    normalization, baseline, candidate, canonical = fixture()

    def put(path: Path, raw: bytes) -> dict[str, Any]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {
            "path": str(path.relative_to(repository)),
            "bytes": len(raw),
            "sha256": sha256(raw).hexdigest(),
        }

    names = {
        "locality_json": "locality_summaries.json",
        "locality_csv": "locality_summaries.csv",
        "bundle": "normalization_bundle.json",
    }
    baselines = {
        role: put(repository / "data/adna/capra" / name, baseline[role])
        for role, name in names.items()
    }
    sample_pin = put(repository / "data/adna/capra/sample_records.json", canonical)
    normalization.update(baseline_products=baselines, canonical_samples=sample_pin)
    protocol = {
        "schema_version": "adna-locality-support-protocol.v1",
        "normalization": normalization,
        "input_guards": {"product_data_root": "data/adna"},
        "limits": {
            "producer_wall_seconds": 60,
            "producer_max_rss_bytes": 1024**3,
            "producer_max_output_bytes": 16 * 1024**2,
            "observer_wall_seconds": 60,
            "observer_max_rss_bytes": 512 * 1024**2,
            "observer_max_output_bytes": 8 * 1024**2,
        },
    }
    protocol_path = repository / "reports/protocol.json"
    protocol_pin = put(protocol_path, body(protocol))
    runner = put(
        repository / "artifacts/runner.py",
        b'"""Artificial, unexecuted runner identity."""\n',
    )
    extras = [
        put(repository / name, b"[project]\nname='synthetic'\n")
        for name in ("pyproject.toml", "packages/bijux-pollenomics/pyproject.toml")
    ]
    state = {
        "head": "a" * 40,
        "index_sha256": "b" * 64,
        "python_files": {"packages/source.py": "c" * 64},
    }
    external = root / "reference.txt"
    external.write_text("synthetic external resource")
    external_pin = {
        "path": str(external),
        "bytes": external.stat().st_size,
        "sha256": sha256(external.read_bytes()).hexdigest(),
        "storage": "external",
    }
    stash = {
        "environment_value": "",
        "candidates": [
            {"path": str(root / "absent-stash"), "is_dir": False, "is_symlink": False}
        ],
        "selected_root": None,
        "entries": [],
    }
    sourcepins = sorted([*baselines.values(), sample_pin], key=lambda pin: pin["path"])
    inputs = {
        "product_data_files": sourcepins,
        "python_files": state["python_files"],
        "extra_repository_files": extras,
    }
    readset = {
        "files": sorted(
            [external_pin, *[{**pin, "storage": "repository"} for pin in sourcepins]],
            key=lambda pin: (pin["storage"], pin["path"]),
        ),
        "directory_discoveries": [str(repository / "data/adna")],
    }

    def product(name: str, raw: bytes) -> dict[str, Any]:
        pin = put(products / name, raw)
        pin["path"] = name
        return pin

    productpins = {role: product(name, candidate[role]) for role, name in names.items()}
    guards = {
        role: product(name, body(value))
        for role, name, value in (
            ("input_manifest", "input-manifest.json", inputs),
            ("readset", "readset.json", readset),
            ("reference_stash", "reference-stash.json", stash),
        )
    }
    result = {
        "schema_version": "adna-locality-support-result.v1",
        "status": "produced_awaiting_independent_verification",
        "source_commit": state["head"],
        "index_sha256": state["index_sha256"],
        "python_files_checked": 1,
        "protocol_sha256": protocol_pin["sha256"],
        "source_guards_passed": True,
        "products": productpins,
        "baselinepins": {**baselines, "samples": sample_pin},
        "runner": runner,
        **guards,
        "resources": {
            "elapsed_seconds": 1.0,
            "peak_rss_bytes": 1024,
            "output_bytes": sum(path.stat().st_size for path in products.iterdir()),
        },
    }
    product("result.json", body(result))
    return repository, protocol_path, products, state, stash
