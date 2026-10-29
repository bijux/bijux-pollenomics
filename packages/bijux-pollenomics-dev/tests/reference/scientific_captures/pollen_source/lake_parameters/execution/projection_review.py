"""Qualify optional current projection bytes and source-observation joins, not eligibility."""

from __future__ import annotations

from collections import Counter
import hashlib
from typing import Any

from lake_review import COUNTRIES, canonical, decode, require


def hashed_row(row: dict[str, Any]) -> None:
    payload = {
        name: value for name, value in row.items() if name != "source_row_sha256"
    }
    require(
        row.get("source_row_sha256") == hashlib.sha256(canonical(payload)).hexdigest(),
        "Projection row identity differs",
    )


def qualify_projection(
    expected: bytes,
    actual: bytes,
    capture_sha: str,
    indexed: list[dict[str, Any]],
    raw_manifest: str,
    normalized_manifest: str,
) -> dict[str, Any]:
    before, value = decode(expected), decode(actual)
    require(
        canonical(before) == canonical(value),
        "Complete current projection scientific value/type/membership differs",
    )
    require(
        value.get("schema_version") == "neotoma-lra-prerequisite-review-projection.v1"
        and value.get("source_family") == "neotoma",
        "Unexpected projection family/schema",
    )
    require(
        value.get("scientific_acceptance")
        == value.get("release_status")
        == "not_evaluated"
        and value.get("reviewer_authority") == "declared_not_authenticated"
        and value.get("executable_request") is None,
        "Projection refusal or authority was promoted",
    )
    identities = value["source_identities"]
    require(
        identities["lakeparameter_capture_sha256"] == capture_sha
        and identities["raw_manifest_sha256"] == raw_manifest
        and identities["normalized_manifest_sha256"] == normalized_manifest,
        "Projection source/capture identities differ",
    )
    chronology, basins = value["chronology_rows"], value["basin_rows"]
    samples = [row["sample_id"] for row in chronology]
    sites = [row["site_id"] for row in basins]
    require(
        len(samples) == len(set(samples)) and len(sites) == len(set(sites)),
        "Projection sample/site membership repeated",
    )
    denominators = value["denominators"]
    require(
        all(type(number) is int for number in denominators.values()),
        "Projection denominators must be native integers",
    )
    require(
        type(denominators["accepted_samples"]) is int
        and denominators["accepted_samples"] == 0
        and denominators["source_sites"]
        == denominators["basin_decisions_required"]
        == len(basins)
        and denominators["necessary_samples"]
        == denominators["chronology_decisions_required"]
        == len(chronology),
        "Projection source denominators/refusal differ",
    )
    source = {(row["page"], row["row_index"]): row for row in indexed}
    site_countries: dict[str, str] = {}
    lake_join_count = 0
    joined: set[tuple[int, int]] = set()
    for row in basins:
        hashed_row(row)
        require(
            row["country_code"] in COUNTRIES
            and row["basin_disposition"] == "not_evaluated"
            and row["support_evidence"] == [],
            "Basin/source-support refusal was changed",
        )
        site_countries[row["site_id"]] = row["country_code"]
        native_site = int(row["site_id"].removeprefix("neotoma:site:"))
        for evidence in row["candidate_basin_evidence"]:
            hashed_row(evidence)
            field = evidence["source_field"]
            if not field.startswith("lakeparameters.value:"):
                require(
                    field == "sites.source_payload.area",
                    "Unknown basin evidence source field",
                )
                continue
            locator = evidence["source_row_locator"]
            require(
                type(locator.get("row_index")) is int,
                "Native source row index required",
            )
            original = source.get((locator["page"], locator["row_index"]))
            require(original is not None, "Projection source page locator absent")
            assert original is not None
            native = original["native"]
            key = (native["siteid"], native["lakeparameterid"])
            require(key not in joined, "Repeated projection lakeparameter evidence")
            joined.add(key)
            require(
                locator["page_sha256"] == original["page_sha256"]
                and native["siteid"] == native_site
                and field == f"lakeparameters.value:{native['lakeparameterid']}"
                and canonical(evidence["source_value"]) == canonical(native["value"]),
                "Projection lakeparameter source site/type/value/locator join differs",
            )
            require(
                evidence["value_status"]
                == ("positive" if native["value"] > 0 else "nonpositive"),
                "Projection value posture differs",
            )
            kind = original["parameter_type"]
            require(
                evidence["source_parameter_code"] == kind.get("lakeparametercode")
                and evidence["source_unit"] == kind.get("lakeparameter")
                and evidence["unit_status"]
                == (
                    "source_parameter_label"
                    if kind.get("lakeparameter")
                    else "not_observed"
                )
                and evidence["source_domain"]
                == (
                    "area"
                    if kind.get("lakeparametercode") == "Area"
                    else "other_lakeparameter"
                ),
                "Projection source type/label/domain join differs",
            )
            lake_join_count += 1
    expected_joined = {
        (row["native"]["siteid"], row["native"]["lakeparameterid"])
        for row in indexed
        if f"neotoma:site:{row['native']['siteid']}" in site_countries
    }
    require(
        joined == expected_joined,
        "Projection omitted or added captured lakeparameter evidence",
    )
    for row in chronology:
        hashed_row(row)
        require(
            row["chronology_disposition"] == "not_evaluated"
            and row["site_id"] in site_countries
            and row["country_code"] == site_countries[row["site_id"]],
            "Chronology source ownership/refusal differs",
        )
        require(
            isinstance(row["candidate_age_claims"], list)
            and row["candidate_age_claims"],
            "Necessary chronology review has no owned source claims",
        )
        for claim in row["candidate_age_claims"]:
            hashed_row(claim)
            require(
                claim["source_claim"].get("subject_id") == row["sample_id"],
                "Chronology claim belongs to another source sample",
            )
    countries = value["country_denominators"]
    require(set(countries) == COUNTRIES, "All countries including UNASSIGNED required")
    site_counts = Counter(row["country_code"] for row in basins)
    sample_counts = Counter(row["country_code"] for row in chronology)
    for country, row in countries.items():
        require(
            type(row["basin_sites"]) is int and type(row["chronology_samples"]) is int,
            "Country counts must be native integers",
        )
        require(
            row["basin_sites"] == site_counts[country]
            and row["chronology_samples"] == sample_counts[country],
            "Projection country denominators differ",
        )
        if country == "UNASSIGNED" and (site_counts[country] or sample_counts[country]):
            require(
                row["coverage_status"] == "refused_unassigned_country",
                "Unassigned source country was admitted",
            )
    require(
        sum(row["candidate_sample_count"] for row in basins) == len(chronology),
        "Basin/sample source counts differ",
    )
    return {
        "scientific_typed_identity": True,
        "tracked_byte_checker_exit": 0 if expected == actual else 2,
        "source_sites": len(basins),
        "necessary_source_samples": len(chronology),
        "lakeparameter_locator_joins": lake_join_count,
        "accepted_samples": 0,
        "independent_pollen_eligibility_recomputation_claimed": False,
        "scope": "Complete current expected/generated projection identity, all internal row hashes, source lake site/type/value/locator joins and unreviewed chronology/basin/refusal structure. Maintained native producer validates raw/normalized authorities; independent ecological or pollen eligibility acceptance is not claimed.",
    }
