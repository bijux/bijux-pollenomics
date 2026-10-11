"""Compare official DOI registry records for used Nordic Neotoma datasets."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

ATTRIBUTION = Path(
    "docs/report/regions/nordic/source-capability/neotoma-attribution/report.json"
)


def _sha(data: bytes) -> str:
    return sha256(data).hexdigest()


def _dataset_target(url: str) -> int | None:
    parsed = urlsplit(url)
    final = parsed.path.rstrip("/").rsplit("/", 1)[-1]
    if parsed.hostname != "data.neotomadb.org" or not final.isdecimal():
        return None
    return int(final)


def build(repository: Path, capture_root: Path) -> dict[str, Any]:
    """Retain DOI names and classify only explicit registry identity relations."""
    repository, capture_root = repository.resolve(), capture_root.resolve()
    attribution_bytes = (repository / ATTRIBUTION).read_bytes()
    attribution = json.loads(attribution_bytes)
    if (
        attribution.get("schema_version") != "nordic-neotoma-publication-readiness.v1"
        or attribution.get("used_dataset_count") != 85
    ):
        raise ValueError("The governed used-dataset attribution ledger changed")
    selected = [
        row
        for row in attribution["decisions"]
        if row["dataset_doi_status"] == "distinct_source_dois"
    ]
    if len(selected) != 13 or any(len(row["dataset_dois"]) != 2 for row in selected):
        raise ValueError("The distinct-DOI review denominator changed")

    manifest_bytes = (capture_root / "capture-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    responses = manifest.get("responses")
    if (
        manifest.get("schema_version") != "neotoma-nordic-distinct-doi-capture.v1"
        or not isinstance(responses, list)
        or manifest.get("response_count") != 26
        or len(responses) != 26
    ):
        raise ValueError("The official registry capture manifest changed")
    by_key = {(row["dataset_id"], row["source_doi"].lower()): row for row in responses}
    if len(by_key) != 26:
        raise ValueError("Duplicate registry response identity")

    decisions = []
    for selected_row in sorted(selected, key=lambda row: row["dataset_id"]):
        dataset_id = int(selected_row["dataset_id"].rsplit(":", 1)[-1])
        doi_names = selected_row["dataset_dois"]
        registry_records = []
        for position, doi in enumerate(doi_names, 1):
            response_row = by_key.get((dataset_id, doi.lower()))
            relative = f"responses/dataset-{dataset_id}-doi-{position}.json"
            expected_url = "https://api.datacite.org/dois/" + quote(doi, safe="")
            if (
                response_row is None
                or response_row["path"] != relative
                or response_row["url"] != expected_url
                or response_row["http_status"] != 200
            ):
                raise ValueError(f"Missing exact registry capture for {doi}")
            path = capture_root / relative
            if path.is_symlink():
                raise ValueError(f"Symbolic registry response for {doi}")
            raw = path.read_bytes()
            if len(raw) != response_row["bytes"] or _sha(raw) != response_row["sha256"]:
                raise ValueError(f"Registry response bytes changed for {doi}")
            payload = json.loads(raw)
            attributes = payload["data"]["attributes"]
            if (
                payload["data"]["type"] != "dois"
                or attributes["doi"].lower() != doi.lower()
            ):
                raise ValueError(f"Registry DOI identity changed for {doi}")
            registry_records.append(
                {
                    "source_doi": doi,
                    "registry_doi": attributes["doi"],
                    "registry_created": attributes["created"],
                    "publication_year": attributes["publicationYear"],
                    "titles": attributes["titles"],
                    "landing_url": attributes["url"],
                    "landing_dataset_id": _dataset_target(attributes["url"]),
                    "version": attributes.get("version"),
                    "related_identifiers": attributes.get("relatedIdentifiers", []),
                    "response_sha256": _sha(raw),
                }
            )
        first, second = registry_records
        declared = [
            record["source_doi"]
            for record, counterpart in ((first, second), (second, first))
            if any(
                relation.get("relationType") == "IsIdenticalTo"
                and relation.get("relatedIdentifierType") == "DOI"
                and relation.get("relatedIdentifier", "").lower()
                == counterpart["source_doi"].lower()
                for relation in record["related_identifiers"]
            )
        ]
        targets_match = all(
            record["landing_dataset_id"] == dataset_id for record in registry_records
        )
        status = (
            "registry_declared_identical"
            if declared
            else "same_dataset_target_without_declared_equivalence"
            if targets_match
            else "registry_target_mismatch"
        )
        decisions.append(
            {
                "dataset_id": selected_row["dataset_id"],
                "site_id": selected_row["site_id"],
                "country_code": selected_row["country_code"],
                "source_doi_names": doi_names,
                "registry_records": registry_records,
                "same_neotoma_dataset_target": targets_match,
                "identity_relation_declared_by": declared,
                "doi_pair_status": status,
                "citation_selection": "source_owner_review_required"
                if status != "registry_declared_identical"
                else "equivalence_supported_citation_format_pending",
            }
        )
    counts = Counter(row["doi_pair_status"] for row in decisions)
    return {
        "schema_version": "nordic-neotoma-distinct-doi-review.v1",
        "attribution_ledger_sha256": _sha(attribution_bytes),
        "registry_capture_manifest_sha256": _sha(manifest_bytes),
        "registry_relation_guidance": "https://support.datacite.org/docs/when-should-i-use-isidenticalto",
        "reviewed_dataset_count": len(decisions),
        "reviewed_doi_count": sum(len(row["source_doi_names"]) for row in decisions),
        "doi_pair_status_counts": dict(sorted(counts.items())),
        "decisions": decisions,
        "lra_accepted_samples": 0,
    }


def main() -> None:
    """Run the CLI to compare official DOI registry records for used Nordic Neotoma datasets."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--capture-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.repository, args.capture_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
