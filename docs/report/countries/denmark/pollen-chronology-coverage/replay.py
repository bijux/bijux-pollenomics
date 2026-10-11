"""Reconcile Danish pollen-screen refusals with retained Neotoma source rows."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


SCREEN_SHA256 = "ffecf23d5f1eb9e7287b418b70a140daa1d30d8c9648672f32b37a47dbbf7b31"
MANIFEST_SHA256 = "6f6777a40b67bd0704eb1a982f19e6d451cad0d6e4a41dfebf5e3f28be33105b"
SURFACES = ("sites", "collection_units", "datasets", "samples", "age_claims")


def _read_rows(
    root: Path, manifest: dict[str, Any], surface: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for part in manifest["surfaces"][surface]["parts"]:
        path = root / part["path"]
        data = path.read_bytes()
        if sha256(data).hexdigest() != part["sha256"]:
            raise ValueError(f"Neotoma {surface} part differs from source manifest")
        parsed = json.loads(data)
        if len(parsed["rows"]) != part["row_count"]:
            raise ValueError(f"Neotoma {surface} part row count changed")
        rows.extend(parsed["rows"])
    return rows


def run(repository: Path) -> dict[str, Any]:
    root = repository / "data/neotoma/relational"
    manifest_bytes = (root / "manifest.json").read_bytes()
    if sha256(manifest_bytes).hexdigest() != MANIFEST_SHA256:
        raise ValueError("Neotoma relational manifest identity changed")
    manifest = json.loads(manifest_bytes)
    screen_path = (
        repository / "docs/report/source-relations/neotoma/pollen-screen/report.json"
    )
    screen_bytes = screen_path.read_bytes()
    if sha256(screen_bytes).hexdigest() != SCREEN_SHA256:
        raise ValueError("Neotoma pollen screen identity changed")
    screen = json.loads(screen_bytes)
    if (
        screen["normalized_manifest_sha256"] != MANIFEST_SHA256
        or screen["source_snapshot_id"] != manifest["source_snapshot_id"]
        or screen["normalized_build_id"] != manifest["build_id"]
    ):
        raise ValueError("Pollen screen and relational source identities disagree")

    source = {name: _read_rows(root, manifest, name) for name in SURFACES}
    sites = {
        row["site_id"]: row for row in source["sites"] if row["country_code"] == "DK"
    }
    units = {row["collection_unit_id"]: row for row in source["collection_units"]}
    datasets = {row["dataset_id"]: row for row in source["datasets"]}
    samples = {
        row["sample_id"]: row
        for row in source["samples"]
        if row["country_code"] == "DK"
    }
    decisions = {
        row["sample_id"]: row
        for row in screen["sample_decisions"]
        if row["country_code"] == "DK"
    }
    if set(samples) != set(decisions) or len(samples) != 279:
        raise ValueError("Danish sample decisions do not cover the source samples")
    claims: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source["age_claims"]:
        if row["country_code"] == "DK" and row["subject_type"] == "sample":
            claims[row["subject_id"]].append(row)
    if set(claims) != set(samples):
        raise ValueError("Danish sample age-claim ownership changed")

    per_site: list[dict[str, Any]] = []
    all_claim_classes: Counter[tuple[str | None, str | None, str]] = Counter()
    for site_id in sorted(sites, key=lambda value: int(value.rsplit(":", 1)[1])):
        rows = [
            decisions[sid]
            for sid, sample in samples.items()
            if sample["site_id"] == site_id
        ]
        if not rows:
            raise ValueError("Danish site has no pollen-screen sample")
        statuses = Counter(row["screen_status"] for row in rows)
        owned_claims = [claim for row in rows for claim in claims[row["sample_id"]]]
        claim_classes = Counter(
            (
                claim["source_age_type"],
                claim["admission_reason"],
                claim["comparability_status"],
            )
            for claim in owned_claims
        )
        all_claim_classes.update(claim_classes)
        units_at_site = sorted({row["collection_unit_id"] for row in rows})
        datasets_at_site = sorted({row["dataset_id"] for row in rows})
        if any(units[uid]["site_id"] != site_id for uid in units_at_site) or any(
            datasets[did]["site_id"] != site_id for did in datasets_at_site
        ):
            raise ValueError("Danish source ownership changed")
        per_site.append(
            {
                "site_id": site_id,
                "site_name": sites[site_id]["source_payload"]["sitename"],
                "source_site_description": sites[site_id]["source_payload"][
                    "sitedescription"
                ],
                "samples_with_pollen_count": len(rows),
                "comparable_age_candidates": statuses["necessary_candidate"],
                "refused_samples": statuses["refused"],
                "sample_age_claims": len(owned_claims),
                "age_claim_classes": [
                    {
                        "source_age_type": age_type,
                        "admission_reason": reason,
                        "comparability_status": status,
                        "claims": count,
                    }
                    for (age_type, reason, status), count in sorted(
                        claim_classes.items(), key=lambda item: str(item[0])
                    )
                ],
                "collection_units": [
                    {"id": uid, "source_handle": units[uid]["source_payload"]["handle"]}
                    for uid in units_at_site
                ],
                "datasets": [
                    {"id": did, "source_doi": datasets[did]["source_payload"]["doi"]}
                    for did in datasets_at_site
                ],
            }
        )

    if (
        len(per_site) != 5
        or sum(row["comparable_age_candidates"] for row in per_site) != 91
        or sum(row["refused_samples"] for row in per_site) != 188
        or sum(row["sample_age_claims"] for row in per_site) != 371
        or all_claim_classes
        != {
            (None, "missing_age_type", "unresolved"): 187,
            ("Radiocarbon years BP", "uncalibrated_radiocarbon", "context_only"): 92,
            ("Calibrated radiocarbon years BP", None, "comparable"): 91,
            ("Calibrated radiocarbon years BP", "negative_bp", "refused"): 1,
        }
        or screen["country_denominators"]["DK"]["screen_candidate_samples"] != 91
        or screen["country_denominators"]["DK"]["screen_refused_samples"] != 188
    ):
        raise ValueError("Danish chronology denominator changed")
    return {
        "schema_version": "denmark-pollen-chronology-coverage.v1",
        "source_snapshot_id": manifest["source_snapshot_id"],
        "normalized_build_id": manifest["build_id"],
        "normalized_manifest_sha256": MANIFEST_SHA256,
        "pollen_screen_sha256": SCREEN_SHA256,
        "sites": per_site,
        "totals": {
            "sites": len(per_site),
            "samples_with_pollen_count": len(samples),
            "comparable_age_candidates": 91,
            "refused_samples": 188,
            "age_type_missing_claims": 187,
            "negative_bp_claims": 1,
            "lra_admitted_samples": 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.repository.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("Danish chronology coverage: 5 sites, 91 candidates, 188 refusals")


if __name__ == "__main__":
    main()
