"""Exact observed count mass for Neotoma prerequisite samples, without admission."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from typing import Any, cast

from bijux_pollenomics.evidence.sources.neotoma.contract import COUNTRY_CODES

from .models import canonical_bytes
from .neotoma import source_accounting
from .neotoma_series import _source_element_status
from .reading import NeotomaEvidence

_COUNT_FIELDS = (
    "observations",
    "refused_count_observations",
    "count_candidate_observations",
    "pollen_count_observations",
    "nonpollen_count_observations",
    "unresolved_label_count_observations",
)
_UNIT_FIELDS = tuple(
    f"{label}_{field}"
    for label in ("pollen", "nonpollen", "unresolved_label")
    for field in ("count_observations", "exact_count_sum", "observed_zero_observations")
)


def _totals(counts: Counter[str]) -> dict[str, int]:
    if (
        counts["observations"]
        != counts["refused_count_observations"] + counts["count_candidate_observations"]
        or counts["count_candidate_observations"]
        != counts["pollen_count_observations"]
        + counts["nonpollen_count_observations"]
        + counts["unresolved_label_count_observations"]
    ):
        raise ValueError("Observed count-status partition does not reconcile")
    return {field: counts[field] for field in _COUNT_FIELDS}


def _unit_key(value: object) -> str:
    return canonical_bytes(value).decode("utf-8").rstrip("\n")


def _add(
    totals: Counter[str], units: dict[str, Counter[str]], record: dict[str, Any]
) -> None:
    totals["observations"] += 1
    if record["count_status"] != "count_candidate":
        totals["refused_count_observations"] += 1
        return
    count = record["typed_count"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("Count candidate has no exact nonnegative integer")
    observation = cast(dict[str, Any], record["source_observation"])
    key = _unit_key(observation.get("source_unit"))
    unit = units.setdefault(key, Counter())
    status = _source_element_status(
        observation.get("source_element"), observation.get("source_element_type")
    )
    field = {
        "source_label_pollen": "pollen",
        "source_element_not_pollen": "nonpollen",
        "source_element_missing": "unresolved_label",
        "source_element_type_missing": "unresolved_label",
        "source_element_labels_disagree": "unresolved_label",
    }.get(status)
    if field is None:
        raise ValueError(f"Unknown source element status: {status}")
    totals["count_candidate_observations"] += 1
    totals[f"{field}_count_observations"] += 1
    unit[f"{field}_count_observations"] += 1
    unit[f"{field}_exact_count_sum"] += count
    if count == 0:
        unit[f"{field}_observed_zero_observations"] += 1


def _units(rows: dict[str, Counter[str]]) -> list[dict[str, Any]]:
    return [
        {
            "source_unit": json.loads(key),
            **{field: counts[field] for field in _UNIT_FIELDS},
        }
        for key, counts in sorted(rows.items())
    ]


def assess_neotoma_candidate_count_mass(
    evidence: NeotomaEvidence, screen: dict[str, Any]
) -> dict[str, Any]:
    """Reconcile source-owned integer mass by sample, country, unit and label.

    These are observed source sums. No taxon eligibility, complete pollen
    denominator, sample chronology, basin or model parameter is inferred.
    """
    evidence.assert_unchanged()
    manifest = evidence.manifest()
    candidate_ids = screen.get("candidate_sample_ids")
    if (
        screen.get("schema_version") != "neotoma-pollen-prerequisite-screen.v1"
        or screen.get("source_snapshot_id") != manifest["source_snapshot_id"]
        or screen.get("normalized_build_id") != manifest["build_id"]
        or screen.get("normalized_manifest_sha256")
        != hashlib.sha256(evidence.manifest_bytes).hexdigest()
        or screen.get("raw_manifest_sha256")
        != dict(evidence.raw_files)["manifest.json"]
        or screen.get("lra_accepted_samples") != 0
        or screen.get("executable_request") is not None
        or not isinstance(candidate_ids, list)
        or any(not isinstance(value, str) for value in candidate_ids)
        or len(candidate_ids) != len(set(candidate_ids))
        or screen.get("candidate_sample_ids_sha256")
        != hashlib.sha256(canonical_bytes(candidate_ids)).hexdigest()
        or len(candidate_ids)
        != screen.get("screen_denominators", {}).get("necessary_candidate_samples")
    ):
        raise ValueError("Screen is not bound to this refused Neotoma source")
    decisions = cast(list[dict[str, Any]], screen["sample_decisions"])
    by_id = {row["sample_id"]: row for row in decisions}
    if len(by_id) != len(decisions) or any(
        by_id.get(sample_id, {}).get("screen_status") != "necessary_candidate"
        for sample_id in candidate_ids
    ):
        raise ValueError("Screen candidate decisions do not reconcile")
    accounting = source_accounting(evidence, candidate_ids)
    selected = accounting.selected_samples
    if selected != frozenset(candidate_ids):
        raise ValueError("Source accounting omitted candidate samples")

    sample_totals: dict[str, Counter[str]] = defaultdict(Counter)
    sample_units: dict[str, dict[str, Counter[str]]] = defaultdict(dict)
    country_totals: dict[str, Counter[str]] = defaultdict(Counter)
    country_units: dict[str, dict[str, Counter[str]]] = defaultdict(dict)
    for source in evidence.rows("observations"):
        observation = source.payload()
        sample_id = observation["sample_id"]
        if sample_id not in selected:
            continue
        country = str(observation["country_code"])
        if country != by_id[sample_id]["country_code"]:
            raise ValueError("Candidate observation country differs from sample")
        record = accounting.observation(source)
        _add(sample_totals[sample_id], sample_units[sample_id], record)
        _add(country_totals[country], country_units[country], record)

    rows = []
    for sample_id in candidate_ids:
        decision = by_id[sample_id]
        if (
            decision["source_locator"]
            != accounting.indexes["samples"][sample_id].locator()
        ):
            raise ValueError("Candidate sample locator differs from source")
        counts = sample_totals[sample_id]
        if any(
            counts[field] != decision[expected]
            for field, expected in (
                ("observations", "observation_count"),
                ("count_candidate_observations", "count_candidate_observations"),
                ("pollen_count_observations", "pollen_count_observations"),
            )
        ):
            raise ValueError("Candidate count mass differs from source screen")
        rows.append(
            {
                "sample_id": sample_id,
                "country_code": decision["country_code"],
                "source_locator": decision["source_locator"],
                **_totals(counts),
                "source_unit_partitions": _units(sample_units[sample_id]),
                "known_compatible_pollen_denominator_status": "not_evaluated",
                "lra_admission_status": "refused",
            }
        )
    countries = {
        country: {
            "candidate_samples": sum(row["country_code"] == country for row in rows),
            **_totals(country_totals[country]),
            "source_unit_partitions": _units(country_units[country]),
        }
        for country in COUNTRY_CODES
    }
    if sum(value["candidate_samples"] for value in countries.values()) != len(rows):
        raise ValueError("Country candidate count mass does not reconcile")
    evidence.assert_unchanged()
    return {
        "schema_version": "neotoma-candidate-count-mass.v1",
        "source_snapshot_id": manifest["source_snapshot_id"],
        "raw_manifest_sha256": dict(evidence.raw_files)["manifest.json"],
        "normalized_manifest_sha256": hashlib.sha256(
            evidence.manifest_bytes
        ).hexdigest(),
        "screen_candidate_ids_sha256": screen["candidate_sample_ids_sha256"],
        "candidate_sample_count": len(rows),
        "country_denominators": countries,
        "sample_rows": rows,
        "known_compatible_pollen_denominator_status": "not_evaluated",
        "lra_accepted_samples": 0,
        "publication_allowed": False,
    }
