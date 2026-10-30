"""Keep qualified original recorded zeros separate from native missing data."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any

from ..abborrtjarnen_ppe_dependence.inputs import native_counts
from ..abborrtjarnen_ppe_dependence.sources import (
    TAXA,
    TAXON_IDS,
    bound_files,
    require,
)
from . import chronology

NATIVE = "neotoma_explicit_five_taxon"
SOURCE = "pangaea_recorded_zeros_local_nc"
PROFILES = (NATIVE, SOURCE)
PROTOCOL = Path(
    "reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/source-supported-counts/protocol.json"
)
OWNER_FIELDS = (
    "native_sample_id",
    "depth_native_exact",
    "original_depth_token",
    "original_row_index",
    "original_column",
    "native_taxon_id",
    "taxon",
)


def qualified_zeros(
    proof: dict[str, Any], verified: dict[str, Any], protocol: dict[str, Any]
) -> list[dict[str, Any]]:
    """A complete independently checked correspondence precedes any overlay."""
    binding, comparison = proof["depth_binding"], proof["comparison"]
    require(
        proof["schema_version"] == "abborrtjarnen-original-count-correspondence.v1"
        and proof["source_commit"] == protocol["source_count_commit"]
        and proof["status"] == "reported_counts_match"
        and proof["candidate_classification_status"] == "enabled_reported_counts_match"
        and all(
            binding[k] == 107
            for k in (
                "original_rows",
                "native_samples",
                "unique_original_depths",
                "unique_native_depths",
            )
        )
        and all(
            not binding[k]
            for k in (
                "duplicate_original_depths",
                "duplicate_native_depths",
                "original_only_depths",
                "native_only_depths",
            )
        )
        and binding["depth_pairs_sha256"] == protocol["depth_pairs_sha256"]
        and comparison["slot_audit_sha256"] == protocol["slot_audit_sha256"]
        and comparison["total_slots"] == 535
        and comparison["native_reported_slots"]
        == comparison["reported_count_matches"]
        == 527
        and comparison["native_absent_slots"] == 8
        and comparison["reported_count_disagreements"] == 0
        and comparison["reported_population_matches"] is True
        and comparison["reported_count_precondition_passed"] is True,
        "Original recorded-zero correspondence is incomplete",
    )
    expected = {
        "status": "verified",
        "producer_source_commit": protocol["source_count_commit"],
        "observer_source_commit": protocol["source_count_commit"],
        "result_sha256": protocol["repository_inputs"][protocol["source_count_result"]][
            "sha256"
        ],
        "source_rows_checked": 107,
        "native_samples_checked": 107,
        "slots_checked": 535,
        "reported_checked": 527,
        "reported_disagreements": 0,
        "absent_native_checked": 8,
        "morphological_comments_checked": 5,
        "source_inputs_checked": 3,
        "model_fits": 0,
    }
    require(
        all(verified.get(k) == v for k, v in expected.items()),
        "Independent original-count qualification differs",
    )
    candidates: list[dict[str, Any]] = proof["absence_candidates"]
    owner_bytes = json.dumps(
        [{k: c[k] for k in OWNER_FIELDS} for c in candidates],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()
    require(
        len(candidates) == 8
        and protocol["zero_owner_fields"] == list(OWNER_FIELDS)
        and hashlib.sha256(owner_bytes).hexdigest()
        == protocol["expected_zero_owners_sha256"]
        and all(
            c["original_status"] == "explicit_zero"
            and c["original_token"] == "0"
            and type(c["original_integer_value"]) is int
            and c["original_integer_value"] == 0
            and c["native_reported"] is False
            and c["native_value"] is None
            and c["original_invalid_reason"] is None
            and c["comparison_status"] == "absent_native_datum"
            for c in candidates
        ),
        "Only the eight qualified literal original zeros may support this profile",
    )
    return candidates


def apply(
    case: dict[str, Any], raw: list[dict[str, Any]], repository: Path, profile: str
) -> dict[str, Any]:
    """Retain native accounts; add a separately sourced analytical panel."""
    require(profile in PROFILES, "Unknown count profile")
    if profile == NATIVE:
        return case
    protocol = json.loads((repository / PROTOCOL).read_bytes())
    require(
        protocol["count_profile"] == SOURCE
        and protocol["base_protocol"] == str(chronology.PROTOCOL),
        "Original recorded-zero profile declaration differs",
    )
    bodies = bound_files(repository, protocol["repository_inputs"])
    proof = json.loads(bodies[protocol["source_count_result"]])
    verified = json.loads(bodies[protocol["source_count_verification"]])
    require(
        all(case["input_sha256"].get(k) == v for k, v in proof["input_sha256"].items())
        and len(proof["input_sha256"]) == 3,
        "Count correspondence and age/PPE source bytes differ",
    )
    zeros = qualified_zeros(proof, verified, protocol)
    require(
        len(raw) == len({s["sampleid"] for s in raw}) == 107,
        "Count-profile native population differs",
    )
    measured = {s["sampleid"]: native_counts(s) for s in raw}
    missing = {
        (s["sampleid"], taxon)
        for s in raw
        for taxon in measured[s["sampleid"]]["missing"]
    }
    require(
        sum(len(set(TAXA) & set(c["measured"])) for c in measured.values()) == 527
        and missing == {(c["native_sample_id"], c["taxon"]) for c in zeros}
        and len(missing) == 8,
        "Native omitted slots do not equal the qualified original-zero population",
    )
    by_id = {s["sampleid"]: s for s in raw}
    require(
        len(case["samples"]) == len(case["sample_accounts"]) == 107
        and {s["sample_id"] for s in case["samples"]} == set(by_id),
        "Analytical and native count-profile sample owners differ",
    )
    for c in zeros:
        require(
            Fraction(str(by_id[c["native_sample_id"]]["depth"]))
            == Fraction(c["depth_native_exact"])
            == 100 * Fraction(c["original_depth_token"])
            and TAXON_IDS[TAXA.index(c["taxon"])] == c["native_taxon_id"],
            "Original-zero physical row/depth/taxon ownership differs",
        )
    case["native_samples"] = case["samples"]
    samples, accounts = [], []
    for sample, account in zip(case["samples"], case["sample_accounts"], strict=True):
        support = [c for c in zeros if c["native_sample_id"] == sample["sample_id"]]
        require(
            account["sample_id"] == sample["sample_id"]
            and sample["missing_taxa"] == measured[sample["sample_id"]]["missing"]
            and sample["counts"] == measured[sample["sample_id"]]["vector"],
            "Prepared native count-profile observations changed",
        )
        counts = measured[sample["sample_id"]]["measured"]
        values = [
            counts[name][1]
            if name in counts
            else next(
                c["original_integer_value"] for c in support if c["taxon"] == name
            )
            for name in TAXA
        ]
        require(
            sum(values) == sample["reported_panel_subtotal"],
            "Recorded zeros changed native count mass",
        )
        additions = {
            "analytical_missing_taxa": [],
            "analytical_panel_mass": sum(values),
            "source_recorded_zero_support": support,
        }
        samples.append({**sample, **additions, "counts": values})
        accounts.append({**account, **additions})
    case.update(
        samples=samples,
        sample_accounts=accounts,
        count_profile=SOURCE,
        count_profile_protocol=protocol,
    )
    case["input_sha256"].update(
        {
            f"repository/{k}": v["sha256"]
            for k, v in protocol["repository_inputs"].items()
        }
    )
    case["source_support"] = {
        "count_profile": SOURCE,
        "native_complete_panels": 99,
        "native_missing_panels": 8,
        "analytical_complete_panels": 107,
        "recorded_source_zero_slots": 8,
        "original_count_correspondence": {
            "result": protocol["source_count_result"],
            "independent_check": protocol["source_count_verification"],
        },
        "rights_and_correspondence": protocol["rights_and_correspondence"],
    }
    return case
