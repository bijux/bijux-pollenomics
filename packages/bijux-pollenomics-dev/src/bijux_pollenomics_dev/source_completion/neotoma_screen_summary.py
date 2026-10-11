"""Export the compact view of a retained refusal-only Neotoma pollen screen."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra.materialization.models import canonical_bytes
from bijux_pollenomics.analysis.lra.materialization.reading import json_object

_SUMMARY_FIELDS = (
    "schema_version",
    "source_snapshot_id",
    "normalized_build_id",
    "raw_manifest_sha256",
    "normalized_manifest_sha256",
    "source_denominators",
    "screen_denominators",
    "country_denominators",
    "candidate_sample_ids_sha256",
    "screen_status",
    "lra_accepted_samples",
    "claims_not_made",
)
_REFUSED_CLAIMS = frozenset(
    {
        "reviewed_taxa_or_ppe",
        "selected_chronology",
        "compatible_pollen_denominator",
        "admitted_basin_geometry",
        "numerical_lra_input",
        "measured_vegetation_truth",
        "four_country_lra_admission",
    }
)


def summary_bytes(screen: dict[str, Any]) -> bytes:
    """Preserve parent values and refusal scope without inspecting source rows."""
    if any(field not in screen for field in _SUMMARY_FIELDS):
        raise ValueError("Pollen screen lacks a compact summary field")
    if (
        screen["schema_version"] != "neotoma-pollen-prerequisite-screen.v1"
        or screen["screen_status"] != "prerequisite_only"
        or type(screen["lra_accepted_samples"]) is not int
        or screen["lra_accepted_samples"] != 0
        or "executable_request" not in screen
        or screen["executable_request"] is not None
        or not isinstance(screen["claims_not_made"], list)
        or any(not isinstance(value, str) for value in screen["claims_not_made"])
        or not _REFUSED_CLAIMS.issubset(screen["claims_not_made"])
    ):
        raise ValueError("Compact summary requires a refusal-only pollen screen")
    candidates = screen.get("candidate_sample_ids")
    decisions = screen.get("sample_decisions")
    if (
        not isinstance(candidates, list)
        or any(not isinstance(value, str) for value in candidates)
        or sorted(set(candidates)) != candidates
        or hashlib.sha256(canonical_bytes(candidates)).hexdigest()
        != screen["candidate_sample_ids_sha256"]
        or not isinstance(decisions, list)
        or any(not isinstance(row, dict) for row in decisions)
    ):
        raise ValueError("Pollen screen candidate population identity differs")
    sample_ids = [row.get("sample_id") for row in decisions]
    if (
        any(not isinstance(value, str) for value in sample_ids)
        or len(set(sample_ids)) != len(sample_ids)
        or any(
            row.get("lra_admission_status") != "refused"
            or not isinstance(row.get("screen_status"), str)
            or row["screen_status"] not in {"necessary_candidate", "refused"}
            for row in decisions
        )
        or sorted(
            row["sample_id"]
            for row in decisions
            if row["screen_status"] == "necessary_candidate"
        )
        != candidates
    ):
        raise ValueError("Pollen screen sample decisions differ from candidate IDs")
    source = screen["source_denominators"]
    counts = screen["screen_denominators"]
    countries = screen["country_denominators"]
    if (
        not isinstance(source, dict)
        or not isinstance(counts, dict)
        or not isinstance(countries, dict)
        or any(not isinstance(value, dict) for value in countries.values())
        or type(source.get("available_samples")) is not int
        or type(counts.get("necessary_candidate_samples")) is not int
        or type(counts.get("refused_samples")) is not int
        or any(
            type(row.get(field)) is not int
            for row in countries.values()
            for field in (
                "samples",
                "screen_candidate_samples",
                "screen_refused_samples",
            )
        )
        or source.get("available_samples") != len(decisions)
        or counts.get("necessary_candidate_samples") != len(candidates)
        or counts.get("refused_samples") != len(decisions) - len(candidates)
        or sum(row.get("samples", 0) for row in countries.values()) != len(decisions)
        or sum(row.get("screen_candidate_samples", 0) for row in countries.values())
        != len(candidates)
        or sum(row.get("screen_refused_samples", 0) for row in countries.values())
        != len(decisions) - len(candidates)
    ):
        raise ValueError("Pollen screen sample denominators differ")
    return (
        json.dumps({field: screen[field] for field in _SUMMARY_FIELDS}, indent=2) + "\n"
    ).encode()


def main() -> None:
    """Write only to an absent repository artifact output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--screen", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    output = args.output.absolute()
    if any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError("Summary output must not traverse symlinks")
    output = output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact output required")
    content = summary_bytes(json_object(args.screen.read_bytes()))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(content)


if __name__ == "__main__":
    main()
