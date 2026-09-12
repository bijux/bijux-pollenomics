"""Build a reproducible review projection from existing source authorities."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any

import yaml

from ..source_completion.evidence import EvidenceReader, digest
from .context import adna_rows, landclim_rows, parameter_rows
from .decisions import load_review_json
from .neotoma import neotoma_rows
from .quarantine import rootsi_rows
from .sead import sead_rows

CONTRACT_PATH = "configs/scientific-contracts/ecological-classification.v1.yaml"


def assemble(
    rows: list[dict[str, Any]],
    *,
    inputs: list[dict[str, Any]],
    contract: dict[str, Any],
    summaries: dict[str, Any],
) -> dict[str, Any]:
    """Close the projection without promoting review intent into scientific admission."""
    identities = [row["review_row_id"] for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("Duplicate review row identity")
    occurrence_totals: Counter[str] = Counter()
    country_totals: dict[str, Counter[str]] = {}
    for row in rows:
        count = row["observation_count"]
        if count is not None:
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise ValueError("Invalid source occurrence count")
            country_counts = row["country_counts"]
            if sum(country_counts.values()) != count:
                raise ValueError("Country occurrence counts do not reconcile")
            source = row["source_family"]
            occurrence_totals[source] += count
            country_totals.setdefault(source, Counter()).update(country_counts)
    for source, expected in (
        (
            "neotoma",
            summaries.get("neotoma", {})
            .get("reconciliation", {})
            .get("input_observation_row_count"),
        ),
        ("sead", summaries.get("sead", {}).get("observation_count")),
    ):
        if expected is not None and occurrence_totals[source] != expected:
            raise ValueError(
                f"Review occurrence total differs from source authority: {source}"
            )
    payload: dict[str, Any] = {
        "schema_version": "bijux-pollenomics.taxa-review-projection.v1",
        "authority_role": "review_projection_not_canonical_classification",
        "publication_allowed": False,
        "scientific_admission_allowed": False,
        "canonical_import_supported": False,
        "row_count": len(rows),
        "rows": sorted(rows, key=lambda row: row["review_row_id"]),
        "source_row_counts": dict(
            sorted(Counter(row["source_family"] for row in rows).items())
        ),
        "source_observation_counts": dict(sorted(occurrence_totals.items())),
        "source_country_observation_counts": {
            source: dict(sorted(counts.items()))
            for source, counts in sorted(country_totals.items())
        },
        "mapping_status_counts": dict(
            sorted(Counter(row["current_mapping_status"] for row in rows).items())
        ),
        "source_summaries": summaries,
        "classification_contract": contract,
        "input_files": sorted(inputs, key=lambda entry: entry["path"]),
        "completeness_scope": "All concepts/lookup candidates in consumed authorities; private Rootsi columns retain unresolved headers. No claim that unavailable sources have complete taxonomy.",
    }
    payload["bundle_sha256"] = digest(payload)
    return payload


def build_review(root: Path, *, rootsi_inventory: str | None = None) -> dict[str, Any]:
    reader = EvidenceReader(root)
    contract_bytes = reader.read_bytes(CONTRACT_PATH)
    if contract_bytes is None:
        raise ValueError("Classification authority is missing")
    contract = yaml.safe_load(contract_bytes)
    if not isinstance(contract, dict):
        raise ValueError("Classification authority must be an object")
    rows, neotoma = neotoma_rows(reader)
    sead_result, sead = sead_rows(reader)
    context, adna = adna_rows(reader)
    rows.extend(sead_result + context + landclim_rows(reader) + parameter_rows(reader))
    summaries = {
        "neotoma": neotoma,
        "sead": sead,
        "adna": adna,
        "other_source_scope": {
            "raa": "archaeological context; no governed pollen taxonomy authority",
            "svar": "SMHI SVAR Swedish lake/water geometry context; no pollen taxonomy",
            "modern_boundaries": "geographic support; no pollen taxonomy",
            "hyde": "user native assets absent; no provider class admission",
        },
    }
    if rootsi_inventory is not None:
        private_rows, private_summary = rootsi_rows(reader, rootsi_inventory)
        rows.extend(private_rows)
        summaries["rootsi"] = private_summary
    else:
        summaries["rootsi"] = {"status": "private_header_inventory_not_supplied"}
    for relative in list(reader.files):
        reader.read_bytes(relative)
    if reader.issues:
        raise ValueError(f"Input evidence verification failed: {reader.issues}")
    return assemble(
        rows, inputs=list(reader.files.values()), contract=contract, summaries=summaries
    )


def csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    """Encode nested provenance as JSON; CSV is machine review text, not a spreadsheet formula interface."""
    keys = sorted({key for row in rows for key in row})
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=keys, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                key: json.dumps(value, ensure_ascii=False, sort_keys=True)
                for key, value in row.items()
            }
        )
    return stream.getvalue().encode("utf-8")


def write_review(payload: dict[str, Any], output: Path) -> None:
    """Reserve a new directory exclusively; a final receipt marks complete flushed outputs."""
    actual_hash = digest(
        {key: value for key, value in payload.items() if key != "bundle_sha256"}
    )
    if actual_hash != payload.get("bundle_sha256"):
        raise ValueError("Review bundle digest does not match content")
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    documents = {
        "taxa-review.json": (
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        ).encode(),
        "taxa-review.csv": csv_bytes(payload["rows"]),
        "REVIEW-INSTRUCTIONS.md": INSTRUCTIONS.encode(),
    }
    receipt = {
        "bundle_sha256": payload["bundle_sha256"],
        "files": {
            name: {
                "sha256": hashlib.sha256(content).hexdigest(),
                "byte_count": len(content),
            }
            for name, content in documents.items()
        },
    }
    documents["completion.json"] = (
        json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    ).encode()
    output.mkdir(exist_ok=False)
    for name, content in documents.items():
        with (output / name).open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())


def read_review(output: Path) -> dict[str, Any]:
    """Read only a complete receipt-bound private review directory."""
    receipt_path = output / "completion.json"
    if output.is_symlink() or receipt_path.is_symlink() or not receipt_path.is_file():
        raise ValueError("Review completion receipt is missing or unsafe")
    receipt = load_review_json(receipt_path.read_bytes())
    expected_names = {"taxa-review.json", "taxa-review.csv", "REVIEW-INSTRUCTIONS.md"}
    if set(receipt.get("files", {})) != expected_names:
        raise ValueError("Review receipt file inventory is invalid")
    contents = {}
    for name in sorted(expected_names):
        path = output / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Review receipt member is missing or unsafe")
        content = path.read_bytes()
        expected = receipt["files"][name]
        if hashlib.sha256(content).hexdigest() != expected.get("sha256") or len(
            content
        ) != expected.get("byte_count"):
            raise ValueError("Review receipt member digest or size differs")
        contents[name] = content
    payload = load_review_json(contents["taxa-review.json"])
    actual = digest(
        {key: value for key, value in payload.items() if key != "bundle_sha256"}
    )
    if payload.get("bundle_sha256") != actual or receipt.get("bundle_sha256") != actual:
        raise ValueError("Review bundle digest does not match receipt")
    return payload


INSTRUCTIONS = """# Private taxa review for Anneli

This generated projection is not an approved classification. Keep this package private: Rootsi quarantine permits inspection only; scientific analysis and publication remain refused. Nothing has been sent to a reviewer. A directory is complete only when completion.json exists and every listed file matches its SHA-256 and byte count; a reserved directory without that final marker is a failed or running build, not a review bundle.

Review every source identity independently, including rare, unidentified, qualified, unused lookup, non-pollen, animal and unresolved-unit rows. Source spellings and contradictory source family/order assertions remain verbatim. A blank proposal means no accepted mapping exists; it is not an invitation to infer a narrower rank. Review Neotoma source qualifiers and SEAD source ecocodes and citation anomalies before grouping. Source PFT/LCT and parameter rows are provenance, not approved substitutions. LandClim currently has 12 PFT labels in the crosswalk and 13 in result headers (ISTS is unmatched); resolve this before reproduction.

CSV fields use JSON values, including quoted strings and null, so missing and empty remain distinct. JSON is the complete authority for this projection. Occurrence counts count source observations, not abundance. Sums are partitioned by exact source unit and country and do not constitute retained-pollen mass. Country dimensions differ by source. No pollen-mass coverage is claimed without reviewed eligibility and compatible denominators. Rootsi rows preserve first-six-row text candidates for every column; header selection and identification as taxa versus metadata remain unresolved.

For each reviewed row, prepare a JSON decision with review_row_id, source_identity_sha256, review_state (proposed, needs_discussion, accepted, rejected, superseded), reviewer_id, decision_date (ISO date), rationale, evidence_reference_ids, proposed_primary_group_id, proposed_primary_subgroup_id, and proposed_role_ids. The return object has bundle_sha256 and decisions. Accepted/rejected/superseded intents require a named reviewer, date, rationale, and evidence. Use the embedded canonical classification contract for group/subgroup/role vocabularies. Reference exact sources and discuss unresolved genus/type/cf/aff resolution, PPE/FSP, fall-speed units, and ecological interpretations separately.

The return validator checks identity, vocabulary and review documentation only. It produces a review-intent diff, never imports scientific acceptance. Existing canonical SEAD review schema only permits pending/null decisions, so coordinator governance and qualified review are still required before any authority transition. No new taxonomy registry, automatic PPE substitution, publication permission or LRA admission is created by this package.
"""
