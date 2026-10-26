"""Inspect native positive-count support at captured sequence boundaries.

The existing exposed country-study samples define the cohort. Other captured
samples may describe its dataset/collection-unit boundary, but do not enlarge
the analytical cohort or establish that the complete historical core survives.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Callable, Iterator, Mapping, Sequence
import csv
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ..nordic_direct_pollen import (
    RELATIONAL_BUILD,
    SOURCE_SNAPSHOT,
    _is_direct_pollen_count,
)

NORDIC = Path("docs/report/regions/nordic/author-target-pollen")
SWEDISH = Path("docs/report/regions/nordic/swedish-author-target-pollen")
RELATIONAL = Path("data/neotoma/relational")
RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads")
COUNTS = {"SE": (3, 228), "DK": (1, 91), "FI": (28, 1797), "NO": (52, 3544)}
DEPTH_UNIT = "native_depth_unit_not_explicit_in_payload"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def _number(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _index(rows: Sequence[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    result = {row[field]: row for row in rows}
    _require(len(result) == len(rows), f"Duplicate native identity: {field}")
    return result


def _cohort(
    repository: Path, inputs: dict[str, str]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], dict[str, Any]]:
    def read(relative: Path, expected: str | None = None) -> Any:
        path = repository / relative
        digest = _sha(path)
        _require(
            expected is None or digest == expected,
            f"Cohort identity differs: {relative}",
        )
        inputs[str(relative)] = digest
        body = path.read_bytes()
        return json.loads(gzip.decompress(body) if path.suffix == ".gz" else body)

    parent = read(NORDIC / "input-manifest.json")
    swedish = read(SWEDISH / "input-manifest.json")
    _require(
        swedish["parent_input_manifest_sha256"]
        == inputs[str(NORDIC / "input-manifest.json")],
        "Swedish and Nordic cohort lineage differ",
    )
    selected: dict[str, dict[str, Any]] = {}
    for country in COUNTS:
        root, manifest = (SWEDISH, swedish) if country == "SE" else (NORDIC, parent)
        relative = Path(f"inputs/metadata-{country}.json.gz")
        metadata = read(
            root / relative, manifest["produced_file_sha256"][str(relative)]
        )
        _require(metadata["country"] == country, "Cohort country identity differs")
        _require(
            len(metadata["sites"]) == COUNTS[country][0], "Cohort site count differs"
        )
        site_ids: set[str] = set()
        for site in metadata["sites"]:
            native_site = site["site_id"]
            if country == "SE":
                native_site = f"neotoma:site:{native_site}"
            _require(native_site not in site_ids, "Duplicate cohort site")
            site_ids.add(native_site)
            for sample in site["candidate_sample_ids"]:
                sid = f"neotoma:sample:{sample}" if country == "SE" else sample
                _require(sid not in selected, "Sample belongs to multiple cohort sites")
                selected[sid] = {
                    "country": country,
                    "site_id": native_site,
                    "selected_claim_id": metadata["selected_age_claim_ids"][sid]
                    if country != "SE"
                    else None,
                }
        _require(
            sum(row["country"] == country for row in selected.values())
            == COUNTS[country][1],
            "Cohort sample count differs",
        )
    return selected, parent, swedish


def _surfaces(
    repository: Path, parent: dict[str, Any], inputs: dict[str, str]
) -> tuple[dict[str, Any], Callable[[str], Iterator[dict[str, Any]]]]:
    path = repository / RELATIONAL / "manifest.json"
    digest = _sha(path)
    _require(
        digest == parent["neotoma_relational_sha256"]["manifest.json"],
        "Relational cohort closure differs",
    )
    inputs[str(RELATIONAL / "manifest.json")] = digest
    manifest = json.loads(path.read_text())
    _require(
        manifest["source_snapshot_id"] == SOURCE_SNAPSHOT
        and manifest["build_id"] == RELATIONAL_BUILD,
        "Native relational source/build differs",
    )

    def rows(name: str) -> Iterator[dict[str, Any]]:
        total = 0
        for part in manifest["surfaces"][name]["parts"]:
            relative = RELATIONAL / part["path"]
            source = repository / relative
            _require(
                _sha(source) == part["sha256"],
                f"Native source digest differs: {relative}",
            )
            inputs[str(relative)] = part["sha256"]
            document = json.loads(source.read_text())
            _require(
                len(document["rows"]) == part["row_count"], "Native part count differs"
            )
            for row in document["rows"]:
                total += 1
                yield row
            del document
        _require(
            total == manifest["surfaces"][name]["row_count"],
            "Native surface count differs",
        )

    return manifest, rows


def scope_support(
    samples: Sequence[dict[str, Any]], values: Mapping[str, Sequence[int | None]]
) -> dict[str, Any]:
    """Describe one taxon's reported native counts without filling missing cells."""
    _require(bool(samples), "A nonempty source sample scope is required")
    _require(
        all(
            value is None or (type(value) is int and value >= 0)
            for evidence in values.values()
            for value in evidence
        ),
        "Native count support requires validated integers or explicit invalid markers",
    )
    depths = [_decimal(row["source_depth"]) for row in samples]
    reasons: list[str] = []
    if any(d is None for d in depths):
        reasons.append("missing_or_invalid_depth")
    if len(set(depths)) != len(depths):
        reasons.append("duplicate_depth")
    invalid = sum(
        any(value is None for value in values.get(row["sample_id"], []))
        for row in samples
    )
    positive = [
        row
        for row in samples
        if any(
            value is not None and value > 0
            for value in values.get(row["sample_id"], [])
        )
    ]
    zeros = sum(
        bool(values.get(row["sample_id"]))
        and all(value == 0 for value in values[row["sample_id"]])
        for row in samples
    )
    missing = sum(not values.get(row["sample_id"]) for row in samples)
    if invalid:
        reasons.append("invalid_native_count")
    if any(row["age_status"] != "resolved_source_age" for row in samples):
        reasons.append("unresolved_source_age")
    if len({(row["age_type"], row["chronology_id"]) for row in samples}) != 1:
        reasons.append("mixed_source_chronology_or_age_basis")
    ordered = sorted(
        samples,
        key=lambda row: (_decimal(row["source_depth"]) or Decimal(), row["sample_id"]),
    )
    if not any(d is None for d in depths):
        ages = [_decimal(row["source_age_bp"]) for row in ordered]
        if all(age is not None for age in ages) and any(
            left > right
            for left, right in zip(ages[:-1], ages[1:], strict=True)
            if left is not None and right is not None
        ):
            reasons.append("age_reversal_with_depth")
    geometric_refusal = any(
        r in reasons
        for r in ("missing_or_invalid_depth", "duplicate_depth", "invalid_native_count")
    )
    first, last = (ordered[0], ordered[-1]) if not geometric_refusal else (None, None)
    positive_ids = {row["sample_id"] for row in positive}
    ordered_positive = [row for row in ordered if row["sample_id"] in positive_ids]
    shallow, deep = (
        (ordered_positive[0], ordered_positive[-1])
        if ordered_positive and not geometric_refusal
        else (None, None)
    )
    valid_depths = [
        depth for row in ordered if (depth := _decimal(row["source_depth"])) is not None
    ]
    gaps = (
        [
            right - left
            for left, right in zip(valid_depths[:-1], valid_depths[1:], strict=True)
        ]
        if not geometric_refusal
        else []
    )

    def endpoint(row: dict[str, Any] | None) -> str:
        if row is None:
            return "refused_depth_or_count"
        evidence = values.get(row["sample_id"], [])
        if not evidence:
            return "missing_measurement"
        if any(value is None for value in evidence):
            return "invalid_native_count"
        return (
            "reported_positive"
            if any(value for value in evidence)
            else "reported_zero_only"
        )

    return {
        "sample_count": len(samples),
        "positive_samples": len(positive),
        "reported_zero_only_samples": zeros,
        "missing_measurement_samples": missing,
        "invalid_measurement_samples": invalid,
        "reported_count_total": sum(
            value
            for row in samples
            for value in values.get(row["sample_id"], [])
            if value is not None
        ),
        "top_sample_id": first["sample_id"] if first else None,
        "bottom_sample_id": last["sample_id"] if last else None,
        "top_depth_native": _number(_decimal(first["source_depth"])) if first else None,
        "bottom_depth_native": _number(_decimal(last["source_depth"]))
        if last
        else None,
        "positive_at_top": first["sample_id"] in positive_ids if first else None,
        "positive_at_bottom": last["sample_id"] in positive_ids if last else None,
        "top_measurement_status": endpoint(first),
        "bottom_measurement_status": endpoint(last),
        "shallowest_positive_sample_id": shallow["sample_id"] if shallow else None,
        "deepest_positive_sample_id": deep["sample_id"] if deep else None,
        "maximum_adjacent_depth_gap_native": _number(max(gaps)) if gaps else None,
        "depth_boundary_status": "refused"
        if geometric_refusal
        else "resolved_native_depth_order",
        "age_order_status": "refused" if reasons else "resolved_source_point_age_order",
        "reason_codes": ";".join(reasons),
    }


def _revision(repository: Path) -> str:
    prefix = ["git", "-C", str(repository)]
    revision = subprocess.check_output(
        [*prefix, "rev-parse", "HEAD"], text=True
    ).strip()
    source = Path(__file__).resolve()
    consumed = [
        source.relative_to(repository),
        (source.parents[1] / "nordic_direct_pollen.py").relative_to(repository),
    ]
    subprocess.run(
        [*prefix, "ls-files", "--error-unmatch", "--", *map(str, consumed)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [*prefix, "diff", "--exit-code", revision, "--", *map(str, consumed)],
        check=True,
        capture_output=True,
    )
    return revision


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    _require(bool(rows), "A complete nonempty source support table is required")
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def publish(repository: Path, output: Path) -> dict[str, Any]:
    """Inspect the frozen country cohort once, with explicit captured-owner context."""
    started = time.monotonic()
    repository = repository.resolve()
    revision = _revision(repository)
    destination = require_absent_artifact_output(repository, output)
    inputs: dict[str, str] = {}
    selected, parent, swedish = _cohort(repository, inputs)
    _, rows = _surfaces(repository, parent, inputs)
    native_samples = _index(list(rows("samples")), "sample_id")
    units = _index(list(rows("collection_units")), "collection_unit_id")
    datasets = _index(list(rows("datasets")), "dataset_id")
    chronologies = _index(list(rows("chronologies")), "chronology_id")
    for sid, cohort in selected.items():
        _require(sid in native_samples, "Cohort sample missing from native source")
        native = native_samples[sid]
        _require(
            native["site_id"] == cohort["site_id"]
            and native["country_code"] == cohort["country"],
            "Cohort/native ownership differs",
        )
    owners = {
        (native_samples[s]["dataset_id"], native_samples[s]["collection_unit_id"])
        for s in selected
    }
    captured = {
        sid: row
        for sid, row in native_samples.items()
        if (row["dataset_id"], row["collection_unit_id"]) in owners
    }
    claims_by_sample: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in rows("age_claims"):
        if claim["subject_type"] == "sample" and claim["subject_id"] in captured:
            claims_by_sample[claim["subject_id"]].append(claim)
    # Sweden's existing producer used the sole raw source age, including signed
    # values; it did not use the other countries' comparable/default selection.
    swedish_raw: dict[str, dict[str, Any]] = {}
    for filename, expected in swedish["swedish_source_sha256"].items():
        relative = RAW / filename
        _require(_sha(repository / relative) == expected, "Swedish raw source differs")
        inputs[str(relative)] = expected
        document = json.loads((repository / relative).read_text())
        for record in document["rows"]:
            site = record["site"]
            for sample in (
                site.get("collectionunit", {}).get("dataset", {}).get("samples", [])
            ):
                sid = f"neotoma:sample:{sample['sampleid']}"
                if sid in selected and selected[sid]["country"] == "SE":
                    _require(
                        sid not in swedish_raw and len(sample.get("ages", [])) == 1,
                        "Swedish sole-source-age branch differs",
                    )
                    swedish_raw[sid] = sample["ages"][0]
        del document
    _require(len(swedish_raw) == 228, "Swedish source-age sample membership differs")
    selected_claims: dict[str, dict[str, Any]] = {}
    for sid, cohort in selected.items():
        if cohort["country"] == "SE":
            raw_age = swedish_raw[sid]
            matches = [
                claim
                for claim in claims_by_sample[sid]
                if claim["source_payload"] == raw_age
            ]
        else:
            matches = [
                claim
                for claim in claims_by_sample[sid]
                if claim["chronology_claim_id"] == cohort["selected_claim_id"]
            ]
        _require(
            len(matches) == 1, "Existing selected source-age identity is not unique"
        )
        selected_claims[sid] = matches[0]
    owner_chronologies: dict[tuple[str, str], set[str]] = defaultdict(set)
    for sid, claim in selected_claims.items():
        sample = captured[sid]
        owner_chronologies[sample["dataset_id"], sample["collection_unit_id"]].add(
            claim["chronology_id"]
        )
    sample_rows: list[dict[str, Any]] = []
    for sid, sample in sorted(captured.items()):
        owner = (sample["dataset_id"], sample["collection_unit_id"])
        native_unit, native_dataset = units[owner[1]], datasets[owner[0]]
        _require(
            native_unit["site_id"] == sample["site_id"] == native_dataset["site_id"],
            "Native parent/site ownership differs",
        )
        choices = [
            c
            for c in claims_by_sample[sid]
            if len(owner_chronologies[owner]) == 1
            and c["chronology_id"] in owner_chronologies[owner]
        ]
        chosen_claim = selected_claims.get(sid)
        if chosen_claim is None and len(choices) == 1:
            chosen_claim = choices[0]
        if chosen_claim is not None:
            _require(
                chosen_claim["collection_unit_id"] == owner[1]
                and chosen_claim["dataset_id"] == owner[0],
                "Age claim physical owner differs",
            )
            _require(
                chosen_claim["chronology_id"] in chronologies,
                "Age chronology parent missing",
            )
        age = _decimal(chosen_claim["source_age_value"]) if chosen_claim else None
        age_type = chosen_claim["source_age_type"] if chosen_claim else None
        age_unit = chosen_claim["source_age_unit"] if chosen_claim else None
        valid_age = (
            age is not None
            and age_type in {"Calibrated radiocarbon years BP", "Calendar years BP"}
            and age_unit == "year"
        )
        sample_rows.append(
            {
                "country": sample["country_code"],
                "site_id": sample["site_id"],
                "dataset_id": owner[0],
                "collection_unit_id": owner[1],
                "sample_id": sid,
                "in_selected_cohort": sid in selected,
                "source_depth": sample["source_depth"],
                "depth_unit": DEPTH_UNIT,
                "depth_status": "finite_native_depth"
                if _decimal(sample["source_depth"]) is not None
                else "missing_or_invalid_depth",
                "source_age_claim_id": chosen_claim["chronology_claim_id"]
                if chosen_claim
                else None,
                "chronology_id": chosen_claim["chronology_id"]
                if chosen_claim
                else None,
                "source_age_bp": _number(age),
                "age_type": age_type,
                "age_unit": age_unit,
                "age_reference_year_ce": 1950 if valid_age else None,
                "age_status": "resolved_source_age"
                if valid_age
                else "refused_missing_ambiguous_or_invalid_source_age",
                "age_selection": "existing_country_study_claim"
                if sid in selected
                else "same_unique_owner_selected_chronology",
            }
        )
    measurements: dict[tuple[str, str, str], dict[str, list[int | None]]] = defaultdict(
        dict
    )
    observations: Counter[str] = Counter()
    seen: set[str] = set()
    variable_axis: dict[str, tuple[str, str]] = {}
    for row in rows("observations"):
        sid = row["sample_id"]
        if sid not in captured:
            continue
        _require(
            row["observation_id"] not in seen, "Duplicate native observation identity"
        )
        seen.add(row["observation_id"])
        sample = captured[sid]
        _require(
            all(
                row[k] == sample[k]
                for k in ("dataset_id", "collection_unit_id", "site_id", "country_code")
            ),
            "Native observation parent differs",
        )
        observations["captured_owner_observations"] += 1
        if not (
            row["source_element"] == row["source_element_type"] == "pollen"
            and row["source_unit"] == "NISP"
            and row["unit_family"] == "count"
        ):
            observations["other_element_or_unit_rows"] += 1
            continue
        taxon = (
            row["variable_id"],
            str(row["source_taxon_id"]),
            row["source_reported_name"],
        )
        _require(
            type(row["source_taxon_id"]) is int
            and row["source_taxon_id"] > 0
            and row["variable_id"] == f"neotoma:variable:{row['source_taxon_id']}",
            "Native variable/taxon identity is invalid",
        )
        _require(
            all(isinstance(v, str) and v for v in taxon),
            "Native taxon identity unresolved",
        )
        _require(
            variable_axis.setdefault(taxon[0], taxon[1:]) == taxon[1:],
            "Conflicting native variable/taxon/name identity",
        )
        key = (sample["dataset_id"], sample["collection_unit_id"], json.dumps(taxon))
        values = measurements[key].setdefault(sid, [])
        valid = _is_direct_pollen_count(row)
        values.append(row["source_value"] if valid else None)
        observations[
            "valid_native_integer_nisp_rows" if valid else "invalid_native_nisp_rows"
        ] += 1
    by_owner: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for sample in sample_rows:
        by_owner[sample["dataset_id"], sample["collection_unit_id"]].append(sample)
    taxon_rows = []
    for (dataset, unit, taxon_json), measurement_values in sorted(measurements.items()):
        variable, taxon_id, name = json.loads(taxon_json)
        captured_rows = by_owner[dataset, unit]
        for scope in ("selected_cohort", "captured_owner_context"):
            population = [
                r
                for r in captured_rows
                if scope != "selected_cohort" or r["in_selected_cohort"]
            ]
            support = scope_support(population, measurement_values)
            taxon_rows.append(
                {
                    "country": population[0]["country"],
                    "site_id": population[0]["site_id"],
                    "dataset_id": dataset,
                    "collection_unit_id": unit,
                    "variable_id": variable,
                    "source_taxon_id": taxon_id,
                    "source_reported_name": name,
                    "scope": scope,
                    "depth_unit": DEPTH_UNIT,
                    **support,
                }
            )
    _require(bool(taxon_rows), "No native source-count support found")
    for relative, expected in inputs.items():
        _require(
            _sha(repository / relative) == expected,
            f"Consumed source changed: {relative}",
        )
    _require(_revision(repository) == revision, "Consumed source revision changed")
    destination.mkdir(parents=True)
    _write_csv(destination / "sample-support.csv", sample_rows)
    _write_csv(destination / "taxon-support.csv", taxon_rows)
    country_accounts = {}
    for country in COUNTS:
        subset = [r for r in sample_rows if r["country"] == country]
        selected_rows = [r for r in subset if r["in_selected_cohort"]]
        _require(
            (len({r["site_id"] for r in selected_rows}), len(selected_rows))
            == COUNTS[country],
            "Selected population changed",
        )
        country_accounts[country] = {
            "selected_samples": len(selected_rows),
            "selected_sites": COUNTS[country][0],
            "captured_owner_samples": len(subset),
            "dataset_collection_unit_sequences": len(
                {(r["dataset_id"], r["collection_unit_id"]) for r in subset}
            ),
            "source_age_refused_samples": sum(
                r["age_status"] != "resolved_source_age" for r in subset
            ),
            "scope_rows": {
                scope: {
                    "taxon_rows": len(items),
                    "positive_at_top": sum(r["positive_at_top"] is True for r in items),
                    "positive_at_bottom": sum(
                        r["positive_at_bottom"] is True for r in items
                    ),
                    "depth_boundary_refused": sum(
                        r["depth_boundary_status"] == "refused" for r in items
                    ),
                    "age_order_refused": sum(
                        r["age_order_status"] == "refused" for r in items
                    ),
                }
                for scope in ("selected_cohort", "captured_owner_context")
                for items in [
                    [
                        r
                        for r in taxon_rows
                        if r["country"] == country and r["scope"] == scope
                    ]
                ]
            },
        }
    report = {
        "schema_version": "neotoma-native-sequence-support.v1",
        "source_commit": revision,
        "status": "conditional_native_count_support",
        "model_fits": 0,
        "selected_samples": len(selected),
        "selected_sites": 84,
        "captured_owner_samples": len(sample_rows),
        "taxon_scope_rows": len(taxon_rows),
        "country_accounts": country_accounts,
        "observation_account": dict(observations),
        "source_inputs_sha256": inputs,
        "elapsed_seconds": time.monotonic() - started,
        "depth_unit": DEPTH_UNIT,
        "age_interpretation": "Source point ages in declared calendar/calibrated BP years, reference1950; no age probability, chronology fit or historical truth is inferred. Missing, mixed or reversed support is refused for age ordering.",
        "measurement_interpretation": "Only literal reported pollen NISP rows on native variable-ID/taxon-ID/name axes. Missing listed measurement is not zero or biological absence. Multiple source measurements are retained in integer totals; any invalid cell refuses taxon boundary inference.",
        "boundary_interpretation": "A positive native count at the shallowest/deepest captured sample flags endpoint support only. Selected cohort and all captured samples of the same dataset/collection unit are distinct. Captured owner context is not proof of a complete historical sequence, first arrival, continuity, comparable sampling effort, or an admitted ecological event.",
        "rights_and_exposure": "Previously exposed development cohort. Neotoma2025 CC BY4.0 default with Neotoma/EPD/investigator/dataset attribution; source-specific publication/eligibility questions and all LRA/field admission remain separate. No private author taxonomy map is consumed or distributed.",
    }
    size = sum(p.stat().st_size for p in destination.iterdir())
    report["output_bytes_before_report"] = size
    if size > 16_000_000:
        report["status"] = "refused_output_budget"
    (destination / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = publish(args.repository, args.output)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "selected_samples",
                    "captured_owner_samples",
                    "taxon_scope_rows",
                    "elapsed_seconds",
                )
            }
        )
    )
    return 0 if result["status"] == "conditional_native_count_support" else 1


if __name__ == "__main__":
    raise SystemExit(main())
