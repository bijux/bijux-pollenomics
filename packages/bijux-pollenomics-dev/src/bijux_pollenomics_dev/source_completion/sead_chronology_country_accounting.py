"""Account for reviewed SEAD chronology claims by governed Nordic country."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

CLAIMS = Path("data/sead/normalized/chronology_claims.json")
LINEAGE = Path("data/sead/normalized/source_lineage.json")
SITES = Path("data/sead/normalized/nordic_environmental_sites.csv")
REVIEW = Path("docs/report/source-relations/sead/chronology-claim-review")
CUSTODY = Path("docs/report/source-relations/sead/public-custody/report.json")
COUNTRIES = {"SE": "Sweden", "DK": "Denmark", "NO": "Norway", "FI": "Finland"}
FIELDS = (
    "country_code",
    "country",
    "claim_type",
    "reviewed_age_basis",
    "comparability_status",
    "chronology_eligibility",
    "claim_count",
    "claim_site_count",
)
MATCHED = (
    "claim_type",
    "source_table",
    "source_record_id",
    "source_age_type",
    "source_age_unit",
    "comparability_status",
    "chronology_eligibility",
    "publication_role",
    "propagation_eligibility",
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read(repository: Path, path: Path) -> bytes:
    return (repository / path).read_bytes()


def account(
    claims: list[dict[str, Any]],
    reviews: list[dict[str, str]],
    sites: list[dict[str, str]],
    custody: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Reject missing/duplicate review identities and country/site drift."""
    by_review = {row["chronology_claim_id"]: row for row in reviews}
    claim_ids = [claim["chronology_claim_id"] for claim in claims]
    if (
        len(claims) != 25109
        or len(reviews) != len(claims)
        or len(set(claim_ids)) != len(claims)
        or len(by_review) != len(reviews)
        or set(claim_ids) != set(by_review)
    ):
        raise ValueError("SEAD claim/review join is not one-to-one")
    by_site = {row["record_id"]: row for row in sites}
    if len(by_site) != len(sites) or len(sites) != custody["raw_and_public_site_count"]:
        raise ValueError("SEAD public site identity/denominator changed")
    site_denominators = Counter(row["country"] for row in sites)
    if (
        dict(site_denominators) != custody["country_counts"]
        or custody["excluded_decision_count"] != 126
        or custody["excluded_status_counts"] != {"review": 103, "unassigned": 23}
        or set(site_denominators) != set(COUNTRIES.values())
    ):
        raise ValueError("SEAD governed country site denominators changed")
    counts: Counter[tuple[str, str, str, str, str]] = Counter()
    grouped_sites: dict[tuple[str, str, str, str, str], set[str]] = defaultdict(set)
    country_claims: Counter[str] = Counter()
    country_claim_sites: dict[str, set[str]] = defaultdict(set)
    types: Counter[str] = Counter()
    comparability: Counter[str] = Counter()
    eligibility: Counter[str] = Counter()
    basis: Counter[str] = Counter()
    refusal_reasons: dict[str, Counter[str]] = defaultdict(Counter)
    for claim in claims:
        claim_id = claim["chronology_claim_id"]
        review = by_review[claim_id]
        if any(str(claim[field]) != review[field] for field in MATCHED):
            raise ValueError(f"SEAD claim review status differs: {claim_id}")
        if review["reason_codes"] != ";".join(sorted(claim["reason_codes"])):
            raise ValueError(f"SEAD claim review reasons differ: {claim_id}")
        if (
            review["propagation_eligibility"] != "refused"
            or review["publication_role"]
            not in {"review_only", "chronology_display_only"}
            or (review["chronology_eligibility"] == "eligible")
            != (review["publication_role"] == "chronology_display_only")
        ):
            raise ValueError(f"SEAD claim gained scientific admission: {claim_id}")
        code = claim["country_code"]
        site_id = str(claim["source_site_id"])
        site = by_site.get(site_id)
        if (
            code not in COUNTRIES
            or site is None
            or site["country"] != COUNTRIES[code]
            or site["site_uuid"] != claim["site_uuid"]
        ):
            raise ValueError(f"SEAD claim/site country binding differs: {claim_id}")
        key = (
            code,
            claim["claim_type"],
            review["reviewed_age_basis"],
            review["comparability_status"],
            review["chronology_eligibility"],
        )
        counts[key] += 1
        grouped_sites[key].add(site_id)
        country_claims[code] += 1
        country_claim_sites[code].add(site_id)
        types[claim["claim_type"]] += 1
        comparability[review["comparability_status"]] += 1
        eligibility[review["chronology_eligibility"]] += 1
        basis[review["reviewed_age_basis"]] += 1
        reasons = claim["reason_codes"]
        if (review["chronology_eligibility"] == "eligible") != (not reasons):
            raise ValueError(f"SEAD chronology reason/eligibility differs: {claim_id}")
        refusal_reasons[code].update(reasons)
    rows = [
        dict(
            zip(
                FIELDS,
                (*key[:1], COUNTRIES[key[0]], *key[1:], count, len(grouped_sites[key])),
                strict=True,
            )
        )
        for key, count in sorted(counts.items())
    ]
    country_rows = [
        {
            "country_code": code,
            "country": country,
            "assigned_site_count": site_denominators[country],
            "claim_site_count": len(country_claim_sites[code]),
            "assigned_sites_without_claim_count": site_denominators[country]
            - len(country_claim_sites[code]),
            "claim_count": country_claims[code],
        }
        for code, country in COUNTRIES.items()
    ]
    return rows, {
        "claim_count": len(claims),
        "group_count": len(rows),
        "country_counts": dict(sorted(country_claims.items())),
        "claim_type_counts": dict(sorted(types.items())),
        "comparability_counts": dict(sorted(comparability.items())),
        "chronology_eligibility_counts": dict(sorted(eligibility.items())),
        "reviewed_age_basis_counts": dict(sorted(basis.items())),
        "chronology_refusal_reasons_by_country": {
            code: dict(sorted(refusal_reasons[code].items())) for code in COUNTRIES
        },
        "propagation_refusal_counts_by_country": {
            code: country_claims[code] for code in COUNTRIES
        },
        "assigned_site_count": len(sites),
        "excluded_site_count": custody["excluded_decision_count"],
        "excluded_site_status_counts": custody["excluded_status_counts"],
        "country_site_denominators": country_rows,
        "claim_site_count": len(set().union(*country_claim_sites.values())),
    }


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Replay bounded country totals to an absent repository artifact directory."""
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact destination required")
    paths = (
        CLAIMS,
        LINEAGE,
        SITES,
        REVIEW / "claims.csv",
        REVIEW / "report.json",
        CUSTODY,
    )
    contents = {path.as_posix(): _read(repository, path) for path in paths}
    hashes = {path: _sha(value) for path, value in contents.items()}
    bundle = json.loads(contents[CLAIMS.as_posix()])
    lineage = json.loads(contents[LINEAGE.as_posix()])
    reviewed = json.loads(contents[(REVIEW / "report.json").as_posix()])
    custody = json.loads(contents[CUSTODY.as_posix()])
    if (
        lineage["normalized_surface_sha256"].get("normalized/chronology_claims.json")
        != hashes[CLAIMS.as_posix()]
        or lineage["normalized_surface_sha256"].get(
            "normalized/nordic_environmental_sites.csv"
        )
        != hashes[SITES.as_posix()]
        or reviewed["claim_review_csv"]
        != {
            "path": "claims.csv",
            "sha256": hashes[(REVIEW / "claims.csv").as_posix()],
            "row_count": bundle["claim_count"],
        }
        or bundle["source_run_id"]
        != lineage["source_run_id"]
        != reviewed["source_run_id"]
        or bundle["source_run_id"] != custody["source_run_id"]
        or bundle["source_build_id"]
        != lineage["build_id"]
        != reviewed["source_build_id"]
        or bundle["acquisition_bundle_sha256"] != lineage["acquisition_bundle_sha256"]
        or bundle["acquisition_bundle_sha256"] != custody["acquisition_bundle_sha256"]
        or bundle["acquisition_manifest_sha256"]
        != lineage["acquisition_manifest_sha256"]
        or bundle["acquisition_manifest_sha256"]
        != reviewed["input_hashes"]["manifest_sha256"]
        or custody["inputs_sha256"].get(SITES.as_posix()) != hashes[SITES.as_posix()]
        or custody["inputs_sha256"].get(LINEAGE.as_posix())
        != hashes[LINEAGE.as_posix()]
        or bundle["propagation_status"] != "refused"
        or bundle["propagation_reason_code"] != "source_classification_not_accepted"
    ):
        raise ValueError("SEAD source/review/public custody digests or lineage differ")
    claims = bundle["claims"]
    reviews = list(
        csv.DictReader(
            io.StringIO(contents[(REVIEW / "claims.csv").as_posix()].decode())
        )
    )
    sites = list(csv.DictReader(io.StringIO(contents[SITES.as_posix()].decode())))
    rows, result = account(claims, reviews, sites, custody)
    if any(
        result[key] != bundle[key]
        for key in (
            "claim_count",
            "country_counts",
            "claim_type_counts",
            "comparability_counts",
            "chronology_eligibility_counts",
        )
    ) or any(
        result[key] != reviewed[key]
        for key in (
            "claim_count",
            "claim_type_counts",
            "comparability_counts",
            "chronology_eligibility_counts",
            "reviewed_age_basis_counts",
        )
    ):
        raise ValueError(
            "SEAD country accounting differs from pinned claim/review totals"
        )
    reason_totals: Counter[str] = Counter()
    for counts in result["chronology_refusal_reasons_by_country"].values():
        reason_totals.update(counts)
    if dict(reason_totals) != bundle["refusal_reason_counts"]:
        raise ValueError("SEAD country chronology refusal reasons differ")
    output.mkdir(parents=True)
    with (output / "rows.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    result.update(
        {
            "schema_version": "sead-chronology-country-accounting.v1",
            "source_run_id": bundle["source_run_id"],
            "posture": "reviewed chronology display/context accounting only; no event, propagation, or pollen admission",
            "input_sha256": dict(sorted(hashes.items())),
            "rows_csv": {
                "path": "rows.csv",
                "sha256": _sha((output / "rows.csv").read_bytes()),
                "row_count": len(rows),
            },
        }
    )
    (output / "report.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    return result


def main() -> int:
    """Account for reviewed SEAD chronology claims by governed Nordic country."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
