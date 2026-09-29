"""Replay source-bound Neotoma review priorities and captured citation leads."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra.materialization.neotoma.pollen_screen import (
    assess_neotoma_pollen_screen,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma.publication_intake import (
    build_candidate_publication_report,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma.taxon_priority import (
    prioritize_neotoma_candidate_taxa,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma.taxon_provenance import (
    attribute_neotoma_priority_datasets,
)
from bijux_pollenomics.analysis.lra.materialization.reading import read_neotoma_evidence

from .workflow import read_review


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode()


def _captured_responses(
    capture_root: Path, attribution_bytes: bytes, expected_ids: set[int]
) -> tuple[dict[int, bytes], str]:
    manifest_path = capture_root / "capture-manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    rows = manifest.get("responses")
    if (
        manifest.get("schema_version") != "neotoma-candidate-publication-capture.v1"
        or manifest.get("attribution_sha256")
        != hashlib.sha256(attribution_bytes).hexdigest()
        or not isinstance(rows, list)
        or manifest.get("response_count") != len(rows)
    ):
        raise ValueError("Publication capture does not bind this candidate attribution")
    responses: dict[int, bytes] = {}
    for row in rows:
        dataset_id = row["dataset_id"]
        relative = Path(row["path"])
        member = capture_root / relative
        path = member.resolve()
        if (
            not isinstance(dataset_id, int)
            or isinstance(dataset_id, bool)
            or dataset_id in responses
            or relative.is_absolute()
            or relative.as_posix()
            != f"responses/dataset-{dataset_id}-publications.json"
            or not path.is_relative_to(capture_root)
            or member.is_symlink()
            or row["http_status"] != 200
        ):
            raise ValueError("Publication response identity or path is invalid")
        content = path.read_bytes()
        if (
            len(content) != row["bytes"]
            or hashlib.sha256(content).hexdigest() != row["sha256"]
        ):
            raise ValueError(f"Publication response changed: {dataset_id}")
        responses[dataset_id] = content
    if set(responses) != expected_ids:
        raise ValueError("Publication capture does not cover all candidate datasets")
    return responses, hashlib.sha256(manifest_bytes).hexdigest()


def replay(
    repository: Path, review_directory: Path, capture_root: Path, output: Path
) -> dict[str, Any]:
    """Write a complete private replay only after all source checks pass."""
    repository, output = repository.resolve(), output.resolve()
    capture_root = capture_root.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact destination required")
    evidence = read_neotoma_evidence(
        repository / "data/neotoma/raw/neotoma_pollen_dataset_downloads",
        repository / "data/neotoma/relational",
    )
    review = read_review(review_directory)
    screen = assess_neotoma_pollen_screen(evidence).as_dict()
    priority = prioritize_neotoma_candidate_taxa(evidence, screen, review)
    attribution = attribute_neotoma_priority_datasets(
        evidence, screen, review, priority
    )
    documents = {
        "screen.json": _json_bytes(screen),
        "priority.json": _json_bytes(priority),
        "attribution.json": _json_bytes(attribution),
    }
    responses, capture_sha = _captured_responses(
        capture_root,
        documents["attribution.json"],
        {row["source_dataset_id"] for row in attribution["dataset_rows"]},
    )
    publication = build_candidate_publication_report(attribution, responses)
    publication["capture_manifest_sha256"] = capture_sha
    documents["publication.json"] = _json_bytes(publication)
    receipt = {
        "review_bundle_sha256": review["bundle_sha256"],
        "capture_manifest_sha256": capture_sha,
        "candidate_sample_count": priority["candidate_sample_count"],
        "candidate_review_row_count": priority["candidate_review_row_count"],
        "candidate_dataset_count": attribution["candidate_dataset_count"],
        "publication_record_count": publication["publication_record_count"],
        "outputs": {
            name: hashlib.sha256(content).hexdigest()
            for name, content in sorted(documents.items())
        },
        "scientific_admission_allowed": False,
        "publication_allowed": False,
    }
    output.mkdir(parents=True)
    for name, content in documents.items():
        (output / name).write_bytes(content)
    (output / "receipt.json").write_bytes(_json_bytes(receipt))
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--review-directory", required=True, type=Path)
    parser.add_argument("--capture-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            replay(
                args.repository,
                args.review_directory,
                args.capture_root,
                args.output,
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
