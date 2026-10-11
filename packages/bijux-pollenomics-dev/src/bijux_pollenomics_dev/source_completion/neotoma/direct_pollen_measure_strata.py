"""Account literal source measures in the published Nordic direct-pollen target cohort."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.source_completion import nordic_direct_pollen as study

MANIFEST_PATH = Path("docs/report/regions/nordic/direct-pollen/manifest.json")
MANIFEST_SHA256 = "43ec4aa62c1c93c0b3af0da2733706eb68a9685bd3f37b18a3041d22e7382573"
SCREEN_PATH = Path("docs/report/source-relations/neotoma/pollen-screen/report.json")
SCREEN_SHA256 = "ffecf23d5f1eb9e7287b418b70a140daa1d30d8c9648672f32b37a47dbbf7b31"
RELATIONAL = Path("data/neotoma/relational")
COUNTRIES = ("DK", "FI", "NO")
SOURCE_MEASURES = (
    "NISP_raw_count",
    "percentage_or_proportion",
    "concentration",
    "influx",
    "presence_or_absence",
    "missing_source_unit",
    "other_literal_source_unit",
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read(repository: Path, relative: Path, expected: str) -> bytes:
    """Read only a real repository member with one declared byte identity."""
    path = repository / relative
    if path.resolve(strict=True) != path or not path.is_file():
        raise ValueError(f"source path is missing or linked: {relative}")
    content = path.read_bytes()
    if _sha(content) != expected:
        raise ValueError(f"source identity differs: {relative}")
    return content


def _rows(repository: Path, part: str, pins: Mapping[str, str]) -> list[dict[str, Any]]:
    document = json.loads(_read(repository, RELATIONAL / part, pins[part]))
    if (
        document.get("source_snapshot_id") != study.SOURCE_SNAPSHOT
        or document.get("build_id") != study.RELATIONAL_BUILD
        or not isinstance(document.get("rows"), list)
        or any(not isinstance(row, dict) for row in document["rows"])
    ):
        raise ValueError(f"relational source part differs: {part}")
    return cast(list[dict[str, Any]], document["rows"])


def source_measure(unit: object, family: object) -> str:
    """Classify only explicit native unit-family identities; preserve literals."""
    if unit is None or unit == "":
        return "missing_source_unit"
    if unit == "NISP" and family == "count":
        return "NISP_raw_count"
    if isinstance(family, str) and family in {"percentage", "proportion"}:
        return "percentage_or_proportion"
    if isinstance(family, str) and family in {
        "concentration_per_mass",
        "concentration_per_volume",
    }:
        return "concentration"
    if family == "influx_per_area_time":
        return "influx"
    if family == "presence_absence":
        return "presence_or_absence"
    return "other_literal_source_unit"


def refusal_reason(row: Mapping[str, Any]) -> str | None:
    """Explain the first failed condition in the pinned study's count predicate."""
    if (
        row.get("source_element") != "pollen"
        or row.get("source_element_type") != "pollen"
    ):
        return "source_element_labels_not_both_pollen"
    if row.get("source_unit") != "NISP":
        return "source_unit_not_native_NISP"
    if row.get("unit_family") != "count":
        return "source_unit_family_not_count"
    if row.get("detection_status") != "reported_value":
        return "source_value_not_reported"
    value = row.get("source_value")
    if type(value) is not int or value < 0:
        return "nonnegative_integer_count_required"
    name = row.get("source_reported_name")
    if not isinstance(name, str) or not name.strip():
        return "source_reported_name_missing"
    return None


def chosen_target_samples(
    screen_ids: Iterable[str],
    samples: Mapping[str, Mapping[str, Any]],
    ages: Mapping[str, list[dict[str, Any]]],
    chronologies: Mapping[str, dict[str, Any]],
    expected: Mapping[str, int],
) -> dict[str, dict[str, Any]]:
    """Reapply the published candidate and unique source-default age decisions."""
    ids = list(screen_ids)
    if len(ids) != len(set(ids)):
        raise ValueError("source screen candidate IDs repeat")
    selected: dict[str, dict[str, Any]] = {}
    for sample_id in ids:
        sample = samples.get(sample_id)
        if sample is None:
            raise ValueError("source screen sample is absent")
        country = sample["country_code"]
        if country not in COUNTRIES:
            continue
        claims = ages.get(sample_id, [])
        if not claims:
            raise ValueError("screen candidate lacks comparable age")
        claim = study._select_comparable_age(claims, dict(chronologies))
        if claim is None:
            continue
        if claim["source_age_type"] not in {
            "Calibrated radiocarbon years BP",
            "Calendar years BP",
        }:
            raise ValueError("unsupported source candidate age type")
        selected[sample_id] = dict(sample)
    counts = dict(Counter(sample["country_code"] for sample in selected.values()))
    if counts != dict(expected):
        raise ValueError("published country target sample denominators differ")
    return selected


def account_rows(
    observations: Iterable[dict[str, Any]],
    selected: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Partition each selected source observation once, preserving exact units."""
    groups: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    observed_samples: dict[str, set[str]] = defaultdict(set)
    observed_sites: dict[str, set[str]] = defaultdict(set)
    observed_names: dict[str, set[str]] = defaultdict(set)
    seen: set[str] = set()
    totals: dict[str, Counter[str]] = defaultdict(Counter)
    reasons: Counter[str] = Counter()
    for row in observations:
        sample_id = row["sample_id"]
        if sample_id not in selected:
            continue
        observation_id = row["observation_id"]
        if not isinstance(observation_id, str) or observation_id in seen:
            raise ValueError("source observation ID is missing or duplicate")
        seen.add(observation_id)
        country = row["country_code"]
        site_id = row["site_id"]
        if (
            country != selected[sample_id]["country_code"]
            or site_id != selected[sample_id]["site_id"]
        ):
            raise ValueError("source observation and selected sample identity differ")
        unit = row["source_unit"]
        family = row["unit_family"]
        unit_json = json.dumps(
            unit, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        family_json = json.dumps(
            family, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        reason = refusal_reason(row)
        if (reason is None) != study._is_direct_pollen_count(row):
            raise ValueError("published direct-pollen count predicate differs")
        decision = "accepted" if reason is None else "refused"
        key = (country, unit_json, family_json, decision, reason or "accepted")
        group = groups.setdefault(
            key,
            {
                "country_code": country,
                "source_unit_json": unit_json,
                "unit_family_json": family_json,
                "source_measure": source_measure(unit, family),
                "decision": decision,
                "decision_reason": reason,
                "observation_count": 0,
                "site_ids": set(),
                "sample_ids": set(),
                "reported_names": set(),
            },
        )
        group["observation_count"] += 1
        group["site_ids"].add(site_id)
        group["sample_ids"].add(sample_id)
        observed_samples[country].add(sample_id)
        observed_sites[country].add(site_id)
        name = row["source_reported_name"]
        if isinstance(name, str):
            group["reported_names"].add(name)
            observed_names[country].add(name)
        totals[country][decision] += 1
        if reason is not None:
            reasons[reason] += 1
    output = []
    for _key, group in sorted(groups.items()):
        output.append(
            {
                "country_code": group["country_code"],
                "source_unit_json": group["source_unit_json"],
                "unit_family_json": group["unit_family_json"],
                "source_measure": group["source_measure"],
                "decision": group["decision"],
                "decision_reason": group["decision_reason"],
                "observation_count": group["observation_count"],
                "unique_site_count": len(group["site_ids"]),
                "unique_sample_count": len(group["sample_ids"]),
                "unique_source_reported_name_count": len(group["reported_names"]),
            }
        )
    summary = {
        "unique_observation_count": len(seen),
        "country_denominators": {
            country: {
                "candidate_sample_count": sum(
                    sample["country_code"] == country for sample in selected.values()
                ),
                "observed_sample_count": len(observed_samples[country]),
                "observed_site_count": len(observed_sites[country]),
                "observed_source_reported_name_count": len(observed_names[country]),
                "accepted_observation_count": totals[country]["accepted"],
                "refused_observation_count": totals[country]["refused"],
            }
            for country in COUNTRIES
        },
        "refusal_reason_counts": dict(sorted(reasons.items())),
        "source_measure_observation_counts": {
            measure: sum(
                row["observation_count"]
                for row in output
                if row["source_measure"] == measure
            )
            for measure in SOURCE_MEASURES
        },
    }
    if sum(row["observation_count"] for row in output) != len(seen):
        raise ValueError("source measure groups do not reconcile observations")
    return output, summary


def build_report(repository: Path) -> dict[str, Any]:
    """Bind the source account to the saved study input and prerequisite decisions."""
    if not repository.is_absolute() or repository.resolve(strict=True) != repository:
        raise ValueError("real absolute repository root required")
    manifest = json.loads(_read(repository, MANIFEST_PATH, MANIFEST_SHA256))
    if manifest.get("schema_version") != "nordic-direct-pollen-results.v1":
        raise ValueError("published study manifest schema differs")
    identity = manifest["input_identity"]
    if (
        identity["schema_version"] != "nordic-direct-pollen-inputs.v1"
        or identity["source_snapshot_id"] != study.SOURCE_SNAPSHOT
        or identity["relational_build_id"] != study.RELATIONAL_BUILD
        or identity["runner_sha256"] != _sha(Path(study.__file__).read_bytes())
    ):
        raise ValueError("published study source identity differs")
    screen = json.loads(_read(repository, SCREEN_PATH, SCREEN_SHA256))
    if (
        _sha(json.dumps(screen, sort_keys=True, separators=(",", ":")).encode())
        != identity["pollen_screen_sha256"]
    ):
        raise ValueError("published screen decision identity differs")
    pins: dict[str, str] = identity["relational_file_sha256"]
    for part, digest in pins.items():
        _read(repository, RELATIONAL / part, digest)
    samples = {
        r["sample_id"]: r
        for r in _rows(repository, "surfaces/samples/part-00001.json", pins)
    }
    chronologies = {
        r["chronology_id"]: r
        for r in _rows(repository, "surfaces/chronologies/part-00001.json", pins)
    }
    ages: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in _rows(repository, "surfaces/age_claims/part-00001.json", pins):
        if (
            claim["subject_type"] == "sample"
            and claim["comparability_status"] == "comparable"
        ):
            ages[claim["subject_id"]].append(claim)
    selected = chosen_target_samples(
        screen["candidate_sample_ids"],
        samples,
        ages,
        chronologies,
        identity["country_candidate_samples"],
    )

    def observations() -> Iterable[dict[str, Any]]:
        for part in sorted(
            path for path in pins if path.startswith("surfaces/observations/")
        ):
            yield from _rows(repository, part, pins)

    groups, summary = account_rows(observations(), selected)
    if summary["unique_observation_count"] != 174970 or len(groups) != 22:
        raise ValueError("reviewed source target measure denominator changed")
    readset = {
        MANIFEST_PATH.as_posix(): MANIFEST_SHA256,
        SCREEN_PATH.as_posix(): SCREEN_SHA256,
    }
    readset.update(
        {(RELATIONAL / part).as_posix(): digest for part, digest in pins.items()}
    )
    return {
        "schema_version": "nordic-direct-pollen-target-measure-account.v1",
        "scope": "published_DK_FI_NO_16_label_target_candidates_only",
        "source_snapshot_id": study.SOURCE_SNAPSHOT,
        "relational_build_id": study.RELATIONAL_BUILD,
        "published_study_producer_sha256": identity["runner_sha256"],
        "source_readset_sha256": dict(sorted(readset.items())),
        "summary": summary,
        "strata": groups,
        "deduplication_rule": "Every unique native observation_id enters exactly one source-unit/family/decision group. Samples may occur in several groups; unique site, sample and source-reported-name denominators are recomputed within each group.",
        "interpretation": "Literal source-measure accounting for existing target cohort decisions only; no measure conversion, taxon identity approval, pollen absence, new prediction, LRA or vegetation admission.",
    }


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Atomically publish one compact account after postread source verification."""
    if not repository.is_absolute() or repository.resolve(strict=True) != repository:
        raise ValueError("real absolute repository root required")
    destination = require_absent_artifact_output(repository, output)
    stage = require_absent_artifact_output(
        repository, output.with_name(output.name + ".stage")
    )
    report = build_report(repository)
    try:
        stage.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        for relative, digest in report["source_readset_sha256"].items():
            _read(repository, Path(relative), digest)
        if (
            _sha(Path(study.__file__).read_bytes())
            != report["published_study_producer_sha256"]
        ):
            raise ValueError("published source producer changed before publication")
        require_absent_artifact_output(repository, destination)
        stage.replace(destination)
    finally:
        if stage.exists():
            stage.unlink()
    return report


def main(argv: list[str] | None = None) -> int:
    """Write the source measure account to one absent repository artifact file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
