"""Verify private SVAR export custody against the governed lake-review refusal."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

EXPORT = Path("svar/normalized-export-2026-09-08")
SOURCES = {
    "sweden_lake_registry.geojson": (
        261041034,
        "d9a1943d1a35e7ab6d48e06156fef625e7c62c8bc410cecf9d8f592ccb07dfd8",
    ),
    "svar_summary.json": (
        111,
        "fb3addf3ad3cebf5e92fab98143673d62132741dd12e98d3b22b83b48cc25106",
    ),
    "svar_lake_registry_manifest.json": (
        284,
        "5f565f792b98f2afce301192645a8dd5102dbe731e1ad061034e244bf8a929be",
    ),
}
REVIEW = Path("data/svar/review/lake_candidate_registry_review.json")
SUBSET = Path("data/svar/review/sweden_lake_candidate_registry.geojson")
CURRENT = Path("docs/report/countries/sweden/sweden_lake_evidence_richness_v66.json")


def identity(path: Path) -> dict[str, object]:
    digest = sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return {"bytes": size, "sha256": digest.hexdigest()}


def verify(repository: Path, source_root: Path) -> dict[str, object]:
    """Bind the recovered bytes while retaining their publication refusal."""
    inputs: list[dict[str, object]] = []
    for name, expected in SOURCES.items():
        source = source_root / EXPORT / name
        observed = identity(source)
        if (observed["bytes"], observed["sha256"]) != expected:
            raise ValueError(f"Recovered SVAR export identity changed: {name}")
        inputs.append(
            {
                "source_root_role": "external_svar_source_store",
                "path": (EXPORT / name).as_posix(),
                **observed,
            }
        )
    summary = json.loads((source_root / EXPORT / "svar_summary.json").read_text())
    manifest = json.loads(
        (source_root / EXPORT / "svar_lake_registry_manifest.json").read_text()
    )
    review = json.loads((repository / REVIEW).read_text())
    subset = json.loads((repository / SUBSET).read_text())
    current = json.loads((repository / CURRENT).read_text())
    if (
        summary.get("lake_count") != 40565
        or manifest.get("normalized_lake_count") != 40565
        or manifest.get("matched_lake_count") != 40565
        or summary.get("generated_on") != "2026-09-08"
        or manifest.get("generated_on") != "2026-09-08"
        or review.get("source_lake_count") != 40523
        or len(subset.get("features", [])) != 99
        or current.get("candidate_count") != 0
        or current["methodology"].get("refusal_reason")
        != "governing_svar_registry_missing"
    ):
        raise ValueError("SVAR source or governed refusal scope changed")
    for relative in (REVIEW, SUBSET, CURRENT):
        inputs.append({"path": relative.as_posix(), **identity(repository / relative)})
    return {
        "schema_version": "svar-normalized-export-custody.v1",
        "export_generated_on": "2026-09-08",
        "export_lake_count_claim": 40565,
        "review_source_lake_count_claim": 40523,
        "review_subset_feature_count": 99,
        "current_ranked_candidate_count": 0,
        "source_population_reconciled": False,
        "raw_wfs_capture_bound_to_export": False,
        "qualified_review_accepted": False,
        "ranking_admitted": False,
        "inputs": inputs,
        "interpretation": (
            "Exact recovered normalized bytes are privately retained. The source "
            "population differs from the current candidate review, the raw WFS "
            "capture is absent, and qualified source review is outstanding. "
            "Neither the export nor the derived subset restores a lake ranking."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.repository.resolve(), args.source_root.resolve())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("SVAR export preserved; current lake ranking remains refused")


if __name__ == "__main__":
    main()
