"""Compare the published Solsø core rule with retained Neotoma source relations."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path

PAPER_SHA256 = "f6959549f955a5bf17540f41ca6c295f11f584c88e550627718fc555a9c3dadd"
SITE = "neotoma:site:3432"
CORE_1981 = "neotoma:collection-unit:4303"
CORE_1983 = "neotoma:collection-unit:4304"
# Odgaard 1994, Table 17, printed page 45 (PDF page 42):
# lab, mean depth cm, radiocarbon BP, one-sigma error, delta-13C per mille.
PUBLISHED_1983_CONTROLS = (
    ("K-5401", 416, 3290, 80, -28.8),
    ("K-5400", 453, 3980, 80, -28.9),
    ("K-5399", 496, 4260, 85, -26.6),
    ("K-5435", 505, 4440, 85, -29.7),
    ("K-5398", 514, 5680, 70, -27.1),
    ("K-5434", 524, 6640, 105, -29.1),
    ("K-5397", 535, 7240, 110, -28.1),
)


# Inclusive source-calendar intervals under the explicit BC + 1950 convention.
PAPER_INTERVALS_BP = {
    CORE_1981: ((-31, 3490), (7210, 11650)),
    CORE_1983: ((3700, 7180),),
}


def _source_age(row: dict[str, object]) -> int | float:
    value = row["source_age_value"]
    if type(value) not in (int, float):
        raise ValueError("Finite numeric calibrated source age required")
    assert isinstance(value, (int, float))
    if not math.isfinite(value):
        raise ValueError("Finite numeric calibrated source age required")
    return value


def closed_paper_interval_selected(row: dict[str, object]) -> bool:
    """Select only the complete inclusive declared source-calendar proxy intervals."""
    age = _source_age(row)
    core = row["collection_unit_id"]
    if not isinstance(core, str) or core not in PAPER_INTERVALS_BP:
        raise ValueError("Named Solsø core required")
    return any(lower <= age <= upper for lower, upper in PAPER_INTERVALS_BP[core])


def legacy_unbounded_selected(row: dict[str, object]) -> bool:
    """Retain the historical half-unbounded calculation as a separate comparison."""
    age = _source_age(row)
    if row["collection_unit_id"] == CORE_1981:
        return age >= 7210 or age <= 3490
    if row["collection_unit_id"] == CORE_1983:
        return 3700 <= age <= 7180
    raise ValueError("Named Solsø core required")


def describe_proxy_row(row: dict[str, object]) -> dict[str, object]:
    """Preserve raw source support/refusal while describing central-point membership."""
    closed = closed_paper_interval_selected(row)
    return {
        "source_record": row,
        "closed_central_point_proxy_selected": closed,
        "legacy_unbounded_central_point_proxy_selected": legacy_unbounded_selected(row),
        "bounded_closed_central_point_proxy_selected": closed
        and 10 <= _source_age(row) <= 11659,
        "analytical_eligibility_evaluated": False,
        "lra_admitted": False,
    }


def identity(path: Path, repository: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(repository).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data).hexdigest(),
    }


def run(repository: Path, paper: Path) -> dict[str, object]:
    if sha256(paper.read_bytes()).hexdigest() != PAPER_SHA256:
        raise ValueError("Original Solsø paper bytes differ from inspected publication")
    controls_path = (
        repository
        / "data/neotoma/relational/surfaces/chronology_controls/part-00001.json"
    )
    ages_path = (
        repository / "data/neotoma/relational/surfaces/age_claims/part-00001.json"
    )
    controls = json.loads(controls_path.read_text())["rows"]
    ages = json.loads(ages_path.read_text())["rows"]
    selected_controls = [
        row for row in controls if row["collection_unit_id"] == CORE_1983
    ]
    actual: Counter[tuple[str, int, int, int, float]] = Counter()
    for row in selected_controls:
        payload = row["source_payload"]
        geochron = payload["geochron"]
        if geochron["geochronerrorolder"] != geochron["geochronerroryounger"]:
            raise ValueError(
                "Asymmetric source error cannot match published one-sigma row"
            )
        key = (
            geochron["labnumber"],
            payload["depth"],
            geochron["geochronage"],
            geochron["geochronerrorolder"],
            geochron["delta13c"],
        )
        actual[key] += 1
    expected = set(PUBLISHED_1983_CONTROLS)
    if set(actual) != expected or set(actual.values()) != {2}:
        raise ValueError(
            "The published seven 1983 controls or chronology duplication changed"
        )
    chronologies = sorted({row["chronology_id"] for row in selected_controls})
    if len(chronologies) != 2:
        raise ValueError("Expected two Neotoma chronology views of seven controls")

    calibrated = [
        row
        for row in ages
        if row["site_id"] == SITE
        and row["source_age_type"] == "Calibrated radiocarbon years BP"
        and row["collection_unit_id"] in {CORE_1981, CORE_1983}
    ]
    if (
        len(calibrated) != 92
        or len({row["source_record_id"] for row in calibrated}) != 92
    ):
        raise ValueError("Solsø calibrated sample denominator changed")

    # Calendar interval translation is a declared proxy, not the author's
    # age model or an equivalence claim for Neotoma calibration.
    proxy = [row for row in calibrated if closed_paper_interval_selected(row)]
    in_landclim_span = [row for row in proxy if 10 <= _source_age(row) <= 11659]
    legacy_proxy = [row for row in calibrated if legacy_unbounded_selected(row)]
    legacy_bounded = [row for row in legacy_proxy if 10 <= _source_age(row) <= 11659]
    counts = Counter(row["collection_unit_id"] for row in proxy)
    bounded_counts = Counter(row["collection_unit_id"] for row in in_landclim_span)
    legacy_counts = Counter(row["collection_unit_id"] for row in legacy_proxy)
    if legacy_counts != {CORE_1981: 56, CORE_1983: 20}:
        raise ValueError("Historical unbounded source comparison changed")
    closed_ids = {row["source_record_id"] for row in proxy}
    excluded_legacy_rows = [
        {
            "source_record_id": row["source_record_id"],
            "collection_unit_id": row["collection_unit_id"],
            "source_age_value": row["source_age_value"],
            "source_age_type": row["source_age_type"],
            "source_record": row,
            "exclusion_reason": "central_value_outside_complete_closed_paper_interval",
        }
        for row in legacy_proxy
        if row["source_record_id"] not in closed_ids
    ]
    return {
        "schema_version": "solsoe-original-core-selection.v2",
        "publication": {
            "title": "The Holocene vegetation history of northern West Jutland",
            "author": "Bent Vad Odgaard",
            "year": 1994,
            "url": "https://pure.au.dk/portal/en/publications/the-holocene-vegetation-history-of-northern-west-jutland/",
            "pdf_url": "https://pure.au.dk/ws/files/39023242/Odgaard_1994_combined.pdf",
            "pdf_sha256": PAPER_SHA256,
            "pdf_bytes": paper.stat().st_size,
            "source_pages": {
                "basin_and_core_locations": "printed 35–36; PDF 32–33",
                "core_selection": "printed 42; PDF 39",
                "radiocarbon_controls": "printed 45; PDF 42",
            },
        },
        "core_locations_in_paper_local_metres": {
            "1981": {"east": -33, "north": 64},
            "1983": {"east": -50, "north": 70},
            "separation_metres": 18.027756377319946,
            "georeferenced": False,
        },
        "published_1983_controls": len(expected),
        "neotoma_1983_control_rows": len(selected_controls),
        "neotoma_1983_chronologies": chronologies,
        "exact_published_control_matches": len(expected),
        "paper_calendar_year_intervals": {
            "1981": ["9700–5260 BC", "1540 BC–AD 1981"],
            "1983": ["5230–1750 BC"],
        },
        "closed_paper_interval_proxy": {
            "reference_epoch": "1950 CE",
            "boundary_convention": "inclusive",
            "intervals_bp_by_core": {
                key: [list(pair) for pair in value]
                for key, value in PAPER_INTERVALS_BP.items()
            },
            "selected_native_sample_ids": sorted(closed_ids),
            "bounded_selected_native_sample_ids": sorted(
                row["source_record_id"] for row in in_landclim_span
            ),
            "legacy_selected_rows_excluded": sorted(
                excluded_legacy_rows, key=lambda row: row["source_record_id"]
            ),
            "source_chronology_equivalence_claimed": False,
            "older_endpoint_source_limit": "The paper's 9700 BC boundary is extrapolated; this declared proxy does not newly calibrate it",
            "calendar_conversion_limit": "BC + 1950 is the existing declared arithmetic proxy, not a resolved no-year-zero calendar conversion",
            "selection_measure": "Raw source central age only; neither full uncertainty containment nor overlap",
            "analytical_eligibility_evaluated": False,
            "native_source_proxy_ledger": [
                describe_proxy_row(row)
                for row in sorted(calibrated, key=lambda row: row["source_record_id"])
            ],
        },
        "legacy_unbounded_proxy": {
            "calculation": "1981 age >= 7210 OR age <= 3490; 1983 3700 <= age <= 7180",
            "historical_report_sha256": "8456bf919423c4b57ed202704cc43d04b891ba98069b9ad9e0765192abf533a6",
            "selected_samples": len(legacy_proxy),
            "selected_by_core": dict(sorted(legacy_counts.items())),
            "bounded_selected_samples": len(legacy_bounded),
            "selected_native_sample_ids": sorted(
                row["source_record_id"] for row in legacy_proxy
            ),
            "scope": "Historical half-unbounded conditional comparison, not the complete stated paper intervals",
        },
        "proxy_age_rule": "BP = BC + 1950, applied to Neotoma calibrated sample ages, not the author's age model",
        "neotoma_calibrated_samples": len(calibrated),
        "paper_interval_proxy_samples": len(proxy),
        "paper_interval_proxy_by_core": dict(sorted(counts.items())),
        "paper_interval_and_landclim_age_span_proxy_samples": len(in_landclim_span),
        "paper_interval_and_landclim_age_span_proxy_by_core": dict(
            sorted(bounded_counts.items())
        ),
        "landclim_ii_reported_sample_count": 79,
        "paper_interval_proxy_gap_to_landclim_ii": 79 - len(proxy),
        "bounded_proxy_gap_to_landclim_ii": 79 - len(in_landclim_span),
        "input_identities": [
            identity(controls_path, repository),
            identity(ages_path, repository),
        ],
        "lra_admitted_samples": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--paper", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.repository.resolve(), args.paper.resolve())
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "report.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("Original Solsø core comparison complete")


if __name__ == "__main__":
    main()
