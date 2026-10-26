"""Independently check saved native sequence support without its producer helpers."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any

import pandas as pd
import pytest

_RELATIVE = Path("data/neotoma/relational")
_OWNER = ["dataset_id", "collection_unit_id"]
_TAXON = ["variable_id", "source_taxon_id", "source_reported_name"]
_KEY = [*_OWNER, *_TAXON]
_COUNTRIES = {"SE": (3, 228), "DK": (1, 91), "FI": (28, 1797), "NO": (52, 3544)}
_DEPTH_UNIT = "native_depth_unit_not_explicit_in_payload"


def _require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def _finite(value: Any) -> Decimal | None:
    if type(value) not in (str, int, float):
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def _scope(samples: list[dict[str, Any]], counts: pd.DataFrame) -> dict[str, Any]:
    """Use grouped measurement statistics and a separate finite-depth axis."""
    axis = sorted(
        samples, key=lambda r: (_finite(r["source_depth"]) or Decimal(), r["sample_id"])
    )
    depths = [_finite(r["source_depth"]) for r in samples]
    finite = [d for d in depths if d is not None]
    reasons = []
    if len(finite) != len(samples):
        reasons.append("missing_or_invalid_depth")
    if len(finite) != len(set(finite)):
        reasons.append("duplicate_depth")
    measured = counts.reindex([r["sample_id"] for r in samples], fill_value=0)
    invalid = int((measured["invalid"] > 0).sum())
    if invalid:
        reasons.append("invalid_native_count")
    if any(r["age_status"] != "resolved_source_age" for r in samples):
        reasons.append("unresolved_source_age")
    if len({(r["age_type"], r["chronology_id"]) for r in samples}) != 1:
        reasons.append("mixed_source_chronology_or_age_basis")
    ages = [_finite(r["source_age_bp"]) for r in axis]
    if (
        len(finite) == len(samples)
        and all(a is not None for a in ages)
        and any(
            a > b
            for a, b in zip(ages[:-1], ages[1:], strict=True)
            if a is not None and b is not None
        )
    ):
        reasons.append("age_reversal_with_depth")
    refused = (
        len(finite) != len(samples) or len(finite) != len(set(finite)) or invalid > 0
    )
    positive = set(measured.index[measured["positive"] > 0])
    first = None if refused else axis[0]
    last = None if refused else axis[-1]
    positive_axis = [r for r in axis if r["sample_id"] in positive]

    def endpoint(row: dict[str, Any] | None) -> str:
        if row is None:
            return "refused_depth_or_count"
        sid = row["sample_id"]
        if sid not in counts.index:
            return "missing_measurement"
        if counts.loc[sid, "invalid"] > 0:
            return "invalid_native_count"
        return "reported_positive" if sid in positive else "reported_zero_only"

    gap = None
    if not refused and len(axis) > 1:
        ordered_depths = [_finite(r["source_depth"]) for r in axis]
        gap = max(
            b - a
            for a, b in zip(ordered_depths[:-1], ordered_depths[1:], strict=True)
            if a is not None and b is not None
        )
    return {
        "sample_count": len(samples),
        "positive_samples": len(positive),
        "reported_zero_only_samples": int(
            (
                (measured["rows"] > 0)
                & (measured["invalid"] == 0)
                & (measured["mass"] == 0)
            ).sum()
        ),
        "missing_measurement_samples": int((measured["rows"] == 0).sum()),
        "invalid_measurement_samples": invalid,
        "reported_count_total": int(measured["mass"].sum()),
        "top_sample_id": None if first is None else first["sample_id"],
        "bottom_sample_id": None if last is None else last["sample_id"],
        "top_depth_native": None
        if first is None
        else str(_finite(first["source_depth"])),
        "bottom_depth_native": None
        if last is None
        else str(_finite(last["source_depth"])),
        "positive_at_top": None if first is None else first["sample_id"] in positive,
        "positive_at_bottom": None if last is None else last["sample_id"] in positive,
        "top_measurement_status": endpoint(first),
        "bottom_measurement_status": endpoint(last),
        "shallowest_positive_sample_id": positive_axis[0]["sample_id"]
        if positive_axis and not refused
        else None,
        "deepest_positive_sample_id": positive_axis[-1]["sample_id"]
        if positive_axis and not refused
        else None,
        "maximum_adjacent_depth_gap_native": None if gap is None else str(gap),
        "depth_boundary_status": "refused"
        if refused
        else "resolved_native_depth_order",
        "age_order_status": "refused" if reasons else "resolved_source_point_age_order",
        "reason_codes": ";".join(reasons),
    }


def _group_counts(frame: pd.DataFrame) -> pd.DataFrame:
    values = frame["source_value"]
    valid = values.map(lambda v: type(v) is int and v >= 0)
    valid &= frame["detection_status"].eq("reported_value")
    valid &= frame["source_reported_name"].map(
        lambda v: isinstance(v, str) and bool(v.strip())
    )
    grouped = frame[_KEY + ["sample_id"]].copy()
    grouped["rows"] = 1
    grouped["invalid"] = (~valid).astype(int)
    grouped["mass"] = pd.Series(
        [v if ok else 0 for v, ok in zip(values, valid, strict=True)],
        index=frame.index,
        dtype=object,
    )
    grouped["positive"] = pd.Series(
        [int(ok and v > 0) for v, ok in zip(values, valid, strict=True)],
        index=frame.index,
    )
    return grouped.groupby(_KEY + ["sample_id"], sort=False, dropna=False)[
        ["rows", "invalid", "mass", "positive"]
    ].sum()


def verify(repository: Path, result: Path) -> dict[str, Any]:
    started = time.monotonic()
    repository, result = repository.resolve(), result.resolve()
    report = json.loads((result / "report.json").read_text())
    inputs: dict[str, str] = {}

    def load(relative: Path, expected: str | None = None) -> Any:
        path = repository / relative
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        _require(
            expected is None or digest == expected,
            f"Input identity differs: {relative}",
        )
        inputs[str(relative)] = digest
        return json.loads(gzip.decompress(payload) if path.suffix == ".gz" else payload)

    north = Path("docs/report/regions/nordic/author-target-pollen")
    sweden = Path("docs/report/regions/nordic/swedish-author-target-pollen")
    parent, swedish = (
        load(north / "input-manifest.json"),
        load(sweden / "input-manifest.json"),
    )
    _require(
        swedish["parent_input_manifest_sha256"]
        == inputs[str(north / "input-manifest.json")],
        "Published cohort lineage differs",
    )
    selected: dict[str, dict[str, Any]] = {}
    for country, (sites, size) in _COUNTRIES.items():
        root, manifest = (sweden, swedish) if country == "SE" else (north, parent)
        relative = Path(f"inputs/metadata-{country}.json.gz")
        metadata = load(
            root / relative, manifest["produced_file_sha256"][str(relative)]
        )
        _require(
            metadata["country"] == country and len(metadata["sites"]) == sites,
            "Published country/sites differ",
        )
        for site in metadata["sites"]:
            site_id = (
                f"neotoma:site:{site['site_id']}"
                if country == "SE"
                else site["site_id"]
            )
            for source_id in site["candidate_sample_ids"]:
                sid = f"neotoma:sample:{source_id}" if country == "SE" else source_id
                _require(sid not in selected, "Repeated published cohort sample")
                selected[sid] = {
                    "country": country,
                    "site_id": site_id,
                    "claim": None
                    if country == "SE"
                    else metadata["selected_age_claim_ids"][sid],
                }
        _require(
            sum(r["country"] == country for r in selected.values()) == size,
            "Published sample denominator differs",
        )
    native_manifest = load(
        _RELATIVE / "manifest.json",
        parent["neotoma_relational_sha256"]["manifest.json"],
    )

    def surface(name: str) -> Any:
        total = 0
        for part in native_manifest["surfaces"][name]["parts"]:
            document = load(_RELATIVE / part["path"], part["sha256"])
            _require(
                len(document["rows"]) == part["row_count"],
                "Native part row count differs",
            )
            total += len(document["rows"])
            yield document["rows"]
            del document
        _require(
            total == native_manifest["surfaces"][name]["row_count"],
            "Native surface row count differs",
        )

    def index(name: str, key: str) -> dict[str, Any]:
        records = [r for part in surface(name) for r in part]
        found = {r[key]: r for r in records}
        _require(len(found) == len(records), f"Repeated native identity: {key}")
        return found

    samples = index("samples", "sample_id")
    units = index("collection_units", "collection_unit_id")
    datasets = index("datasets", "dataset_id")
    chronologies = index("chronologies", "chronology_id")
    owners = {
        (samples[s]["dataset_id"], samples[s]["collection_unit_id"]) for s in selected
    }
    captured = {
        s: r
        for s, r in samples.items()
        if (r["dataset_id"], r["collection_unit_id"]) in owners
    }
    for sid, row in selected.items():
        _require(
            samples[sid]["site_id"] == row["site_id"]
            and samples[sid]["country_code"] == row["country"],
            "Published sample physical owner differs",
        )
    claims = [
        r
        for part in surface("age_claims")
        for r in part
        if r["subject_type"] == "sample" and r["subject_id"] in captured
    ]
    by_sample: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        by_sample.setdefault(claim["subject_id"], []).append(claim)
    raw_ages = {}
    for filename, digest in swedish["swedish_source_sha256"].items():
        document = load(
            Path("data/neotoma/raw/neotoma_pollen_dataset_downloads") / filename, digest
        )
        for record in document["rows"]:
            for sample in (
                record["site"]
                .get("collectionunit", {})
                .get("dataset", {})
                .get("samples", [])
            ):
                sid = f"neotoma:sample:{sample['sampleid']}"
                if sid in selected and selected[sid]["country"] == "SE":
                    _require(
                        sid not in raw_ages and len(sample["ages"]) == 1,
                        "Swedish sole raw age identity differs",
                    )
                    raw_ages[sid] = sample["ages"][0]
        del document
    _require(len(raw_ages) == 228, "Swedish raw-age population differs")
    choices = {}
    for sid, cohort in selected.items():
        candidates = [
            c
            for c in by_sample.get(sid, [])
            if (
                c["source_payload"] == raw_ages[sid]
                if cohort["country"] == "SE"
                else c["chronology_claim_id"] == cohort["claim"]
            )
        ]
        _require(len(candidates) == 1, "Selected native claim identity differs")
        choices[sid] = candidates[0]
    owner_chronologies: dict[tuple[str, str], set[str]] = {}
    for sid, selected_claim in choices.items():
        r = captured[sid]
        owner_chronologies.setdefault(
            (r["dataset_id"], r["collection_unit_id"]), set()
        ).add(selected_claim["chronology_id"])
    expected_samples = []
    for sid, native in sorted(captured.items()):
        owner = (native["dataset_id"], native["collection_unit_id"])
        _require(
            units[owner[1]]["site_id"]
            == native["site_id"]
            == datasets[owner[0]]["site_id"],
            "Native parent/site ownership differs",
        )
        alternatives = [
            c
            for c in by_sample.get(sid, [])
            if len(owner_chronologies[owner]) == 1
            and c["chronology_id"] in owner_chronologies[owner]
        ]
        chosen = choices.get(sid, alternatives[0] if len(alternatives) == 1 else None)
        if chosen:
            _require(
                (chosen["dataset_id"], chosen["collection_unit_id"]) == owner
                and chosen["chronology_id"] in chronologies,
                "Native age parent differs",
            )
        age = None if chosen is None else _finite(chosen["source_age_value"])
        age_type = None if chosen is None else chosen["source_age_type"]
        age_unit = None if chosen is None else chosen["source_age_unit"]
        valid = (
            age is not None
            and age_type in {"Calendar years BP", "Calibrated radiocarbon years BP"}
            and age_unit == "year"
        )
        expected_samples.append(
            {
                "country": native["country_code"],
                "site_id": native["site_id"],
                "dataset_id": owner[0],
                "collection_unit_id": owner[1],
                "sample_id": sid,
                "in_selected_cohort": sid in selected,
                "source_depth": native["source_depth"],
                "depth_unit": _DEPTH_UNIT,
                "depth_status": "finite_native_depth"
                if _finite(native["source_depth"]) is not None
                else "missing_or_invalid_depth",
                "source_age_claim_id": None
                if chosen is None
                else chosen["chronology_claim_id"],
                "chronology_id": None if chosen is None else chosen["chronology_id"],
                "source_age_bp": None if age is None else str(age),
                "age_type": age_type,
                "age_unit": age_unit,
                "age_reference_year_ce": 1950 if valid else None,
                "age_status": "resolved_source_age"
                if valid
                else "refused_missing_ambiguous_or_invalid_source_age",
                "age_selection": "existing_country_study_claim"
                if sid in selected
                else "same_unique_owner_selected_chronology",
            }
        )
    saved_samples = _csv(result / "sample-support.csv")
    _require(
        saved_samples
        == [{k: _text(v) for k, v in row.items()} for row in expected_samples],
        "Saved sample/depth/age support differs",
    )

    grouped_parts = []
    observed: Counter[str] = Counter()
    seen: set[str] = set()
    for part in surface("observations"):
        relevant = [r for r in part if r["sample_id"] in captured]
        for row in relevant:
            _require(row["observation_id"] not in seen, "Repeated native observation")
            seen.add(row["observation_id"])
            parent_sample = captured[row["sample_id"]]
            _require(
                all(
                    row[k] == parent_sample[k]
                    for k in [*_OWNER, "site_id", "country_code"]
                ),
                "Native observation physical owner differs",
            )
        observed["captured_owner_observations"] += len(relevant)
        eligible = [
            r
            for r in relevant
            if r["source_element"] == r["source_element_type"] == "pollen"
            and r["source_unit"] == "NISP"
            and r["unit_family"] == "count"
        ]
        observed["other_element_or_unit_rows"] += len(relevant) - len(eligible)
        columns = [*_KEY, "sample_id", "source_value", "detection_status"]
        frame = pd.DataFrame(
            [{k: r[k] for k in columns} for r in eligible], columns=columns
        )
        frame["source_value"] = pd.Series(
            [r["source_value"] for r in eligible], dtype=object
        )
        for row in eligible:
            _require(
                type(row["source_taxon_id"]) is int
                and row["source_taxon_id"] > 0
                and row["variable_id"] == f"neotoma:variable:{row['source_taxon_id']}",
                "Native taxon axis differs",
            )
        if not frame.empty:
            grouped = _group_counts(frame)
            observed["invalid_native_nisp_rows"] += int(grouped["invalid"].sum())
            observed["valid_native_integer_nisp_rows"] += int(
                grouped["rows"].sum() - grouped["invalid"].sum()
            )
            grouped_parts.append(grouped)
        del relevant, eligible, frame, part
    measurements = (
        pd.concat(grouped_parts).groupby(level=list(range(6)), sort=False).sum()
    )
    source_axis = measurements.reset_index()[_TAXON].drop_duplicates()
    _require(
        not source_axis["variable_id"].duplicated().any(),
        "Native variable/name identity conflicts",
    )
    samples_by_owner: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in expected_samples:
        samples_by_owner.setdefault(
            (row["dataset_id"], row["collection_unit_id"]), []
        ).append(row)
    expected_taxa = {}
    for key, frame in measurements.groupby(level=list(range(5)), sort=False):
        dataset, unit, variable, taxon_id, name = (str(value) for value in key)
        sample_counts = frame.droplevel(list(range(5)))
        for scope in ("selected_cohort", "captured_owner_context"):
            population = [
                r
                for r in samples_by_owner[dataset, unit]
                if scope == "captured_owner_context" or r["in_selected_cohort"]
            ]
            expected_taxa[dataset, unit, variable, str(taxon_id), name, scope] = {
                "country": population[0]["country"],
                "site_id": population[0]["site_id"],
                "dataset_id": dataset,
                "collection_unit_id": unit,
                "variable_id": variable,
                "source_taxon_id": str(taxon_id),
                "source_reported_name": name,
                "scope": scope,
                "depth_unit": _DEPTH_UNIT,
                **_scope(population, sample_counts),
            }
    saved_taxa = _csv(result / "taxon-support.csv")
    saved_keys = [
        (
            r["dataset_id"],
            r["collection_unit_id"],
            r["variable_id"],
            r["source_taxon_id"],
            r["source_reported_name"],
            r["scope"],
        )
        for r in saved_taxa
    ]
    _require(
        len(set(saved_keys)) == len(saved_keys)
        and set(saved_keys) == set(expected_taxa),
        "Taxon/scope identity population differs",
    )
    for key, saved in zip(saved_keys, saved_taxa, strict=True):
        _require(
            saved == {k: _text(v) for k, v in expected_taxa[key].items()},
            f"Saved count/endpoint/refusal differs: {key}",
        )
    _require(report["source_inputs_sha256"] == inputs, "Saved input population differs")
    _require(
        Counter(report["observation_account"]) == observed,
        "Saved observation accounting differs",
    )
    _require(
        report["selected_samples"] == len(selected) == 5660
        and report["selected_sites"] == 84,
        "Published denominator differs",
    )
    _require(
        report["captured_owner_samples"] == len(expected_samples)
        and report["taxon_scope_rows"] == len(expected_taxa),
        "Saved output populations differ",
    )
    _require(
        report["model_fits"] == 0
        and report["depth_unit"] == _DEPTH_UNIT
        and report["status"] == "conditional_native_count_support",
        "Source interpretation status differs",
    )
    accounts = {}
    for country, (site_count, selected_count) in _COUNTRIES.items():
        population = [r for r in expected_samples if r["country"] == country]
        selected_population = [r for r in population if r["in_selected_cohort"]]
        _require(
            len({r["site_id"] for r in selected_population}) == site_count,
            "Selected physical site denominator differs",
        )
        scopes = {}
        for scope in ("selected_cohort", "captured_owner_context"):
            rows = [
                r
                for r in expected_taxa.values()
                if r["country"] == country and r["scope"] == scope
            ]
            scopes[scope] = {
                "taxon_rows": len(rows),
                "positive_at_top": sum(r["positive_at_top"] is True for r in rows),
                "positive_at_bottom": sum(
                    r["positive_at_bottom"] is True for r in rows
                ),
                "depth_boundary_refused": sum(
                    r["depth_boundary_status"] == "refused" for r in rows
                ),
                "age_order_refused": sum(
                    r["age_order_status"] == "refused" for r in rows
                ),
            }
        accounts[country] = {
            "selected_samples": selected_count,
            "selected_sites": site_count,
            "captured_owner_samples": len(population),
            "dataset_collection_unit_sequences": len(
                {(r["dataset_id"], r["collection_unit_id"]) for r in population}
            ),
            "source_age_refused_samples": sum(
                r["age_status"] != "resolved_source_age" for r in population
            ),
            "scope_rows": scopes,
        }
    _require(report["country_accounts"] == accounts, "Country/scope accounting differs")
    for input_name, digest in inputs.items():
        _require(
            hashlib.sha256((repository / input_name).read_bytes()).hexdigest() == digest,
            "Native input changed during independent check",
        )
    return {
        "status": "passed",
        "producer_source_commit": report["source_commit"],
        "selected_samples": len(selected),
        "selected_sites": 84,
        "sample_rows_checked": len(expected_samples),
        "taxon_scope_rows_checked": len(expected_taxa),
        "native_observations_checked": observed["captured_owner_observations"],
        "signed_age_samples": sum(
            _finite(r["source_age_bp"]) is not None and Decimal(r["source_age_bp"]) < 0
            for r in expected_samples
        ),
        "model_fits": 0,
        "elapsed_seconds": time.monotonic() - started,
    }


@pytest.mark.parametrize(
    "depths,reasons",
    [
        ([None, None], "missing_or_invalid_depth"),
        ([1, 1], "duplicate_depth"),
        ([None, 1, 1], "missing_or_invalid_depth;duplicate_depth"),
    ],
)
def test_independent_finite_depth_ties_exclude_missing_coordinates(
    depths: list[Any], reasons: str
) -> None:
    samples = [
        {
            "sample_id": str(i),
            "source_depth": d,
            "source_age_bp": str(i),
            "age_status": "resolved_source_age",
            "age_type": "Calendar years BP",
            "chronology_id": "c",
        }
        for i, d in enumerate(depths)
    ]
    counts = pd.DataFrame(
        {
            "rows": [1] * len(samples),
            "invalid": [0] * len(samples),
            "mass": [0] * len(samples),
            "positive": [0] * len(samples),
        },
        index=[r["sample_id"] for r in samples],
    )
    assert _scope(samples, counts)["reason_codes"] == reasons


def test_independent_grouping_preserves_duplicate_counts_invalid_and_zero_cells() -> (
    None
):
    values = [2, 3, 0, 1.0, True, -1]
    frame = pd.DataFrame(
        {
            "dataset_id": ["d"] * 6,
            "collection_unit_id": ["u"] * 6,
            "variable_id": ["v"] * 6,
            "source_taxon_id": [1] * 6,
            "source_reported_name": ["name"] * 6,
            "sample_id": [
                "positive",
                "positive",
                "zero",
                "invalid",
                "invalid",
                "invalid",
            ],
            "source_value": pd.Series(values, dtype=object),
            "detection_status": ["reported_value"] * 6,
        }
    )
    grouped = _group_counts(frame).droplevel(list(range(5)))
    assert grouped.loc["positive"].to_dict() == {
        "rows": 2,
        "invalid": 0,
        "mass": 5,
        "positive": 2,
    }
    assert grouped.loc["zero"].to_dict() == {
        "rows": 1,
        "invalid": 0,
        "mass": 0,
        "positive": 0,
    }
    assert grouped.loc["invalid"].to_dict() == {
        "rows": 3,
        "invalid": 3,
        "mass": 0,
        "positive": 0,
    }
    samples = [
        {
            "sample_id": sid,
            "source_depth": i,
            "source_age_bp": str(i - 1),
            "age_status": "resolved_source_age",
            "age_type": "Calendar years BP",
            "chronology_id": "c",
        }
        for i, sid in enumerate(["positive", "zero", "missing"])
    ]
    result = _scope(samples, grouped)
    assert result["reported_count_total"] == 5
    assert (
        result["positive_samples"]
        == result["reported_zero_only_samples"]
        == result["missing_measurement_samples"]
        == 1
    )
    assert result["top_measurement_status"] == "reported_positive"
    assert result["bottom_measurement_status"] == "missing_measurement"
    assert result["age_order_status"] == "resolved_source_point_age_order"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _require(
        not args.output.exists()
        and args.output.resolve().is_relative_to(
            (args.repository / "artifacts").resolve()
        ),
        "Independent output must be absent under repository artifacts",
    )
    result = verify(args.repository, args.result)
    result["observer_source_commit"] = subprocess.check_output(
        ["git", "-C", str(args.repository), "rev-parse", "HEAD"], text=True
    ).strip()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
