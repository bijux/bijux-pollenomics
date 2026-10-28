"""Exact input identities and typed joins for the retained Solsø declarations."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Any

BASE = Path(
    "/opt/homebrew/Cellar/python@3.11/3.11.13/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
)
BASE_SHA = "92019a8331209d7247702193bbdfbe359807d7ee1df92566fcf31935f6b273d4"
PREFIX = BASE.parents[1]
REPLAY = "docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/replay.py"
REPORT = REPLAY.removesuffix("replay.py") + "report.json"
CONTROLS = "data/neotoma/relational/surfaces/chronology_controls/part-00001.json"
AGES = "data/neotoma/relational/surfaces/age_claims/part-00001.json"
PAPER = Path(
    "/Users/bijan/bijux/-bijux-pollenomics-data/landclim/solsoe/odgaard-1994.pdf"
)
IDENTITIES = {
    REPLAY: ("9604574d34c2555164d75f2cfdd30475f3f1f74d1a50ff600ea7d812a33bf746", 11546),
    REPORT: ("8456bf919423c4b57ed202704cc43d04b891ba98069b9ad9e0765192abf533a6", 2417),
    CONTROLS: (
        "bb84e43a97c3ac548505ad34e489c551ce44ab6c072d28aaa88bc287dbeeac84",
        3908881,
    ),
    AGES: (
        "6b8983b43138ec68895d96070508218d0b7c4f9908bf87860f96b79d2725c558",
        37052858,
    ),
}
PAPER_ID = (
    "f6959549f955a5bf17540f41ca6c295f11f584c88e550627718fc555a9c3dadd",
    12519377,
)
COMMON_SHA = "9062395231bd7a4ec19bfe41df1587281c06e143b146119fe445a6eb0ce7ce8a"
OWNER = (
    "countries/denmark/solsoe-source-lineage/original-core-selection/report-products"
)
SITE = "neotoma:site:3432"
CORE_1981 = "neotoma:collection-unit:4303"
CORE_1983 = "neotoma:collection-unit:4304"
DECLARED = (
    ("K-5401", 416, 3290, 80, -28.8),
    ("K-5400", 453, 3980, 80, -28.9),
    ("K-5399", 496, 4260, 85, -26.6),
    ("K-5435", 505, 4440, 85, -29.7),
    ("K-5398", 514, 5680, 70, -27.1),
    ("K-5434", 524, 6640, 105, -29.1),
    ("K-5397", 535, 7240, 110, -28.1),
)


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path: Path) -> dict[str, Any]:
    require(
        path.is_file() and not path.is_symlink(),
        f"Physical regular input required: {path}",
    )
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def exact(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            exact(left[k], right[k]) for k in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            exact(a, b) for a, b in zip(left, right, strict=True)
        )
    return bool(left == right)


def load(path: Path) -> Any:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len({k for k, _ in rows}) == len(rows), "Duplicate JSON keys")
        return dict(rows)

    def constant(value: str) -> None:
        raise ValueError("Nonfinite JSON constant: " + value)

    return json.loads(
        path.read_bytes(), object_pairs_hook=pairs, parse_constant=constant
    )


def dump(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )


def owner_contract(inventory: dict[str, Any]) -> dict[str, Any]:
    rows = [r for r in inventory["owners"] if r.get("owner_id") == OWNER]
    require(len(rows) == 1, "Exactly one named Solsø owner required")
    row = rows[0]
    require(
        set(row)
        == {
            "owner_id",
            "role",
            "paths",
            "producer_paths",
            "producer_inputs",
            "verification",
        },
        "Solsø owner fields differ",
    )
    require(
        row["role"] == "unresolved"
        and exact(row["paths"], [REPORT])
        and exact(row["producer_paths"], [REPLAY])
        and exact(row["producer_inputs"], sorted([AGES, CONTROLS])),
        "Declared Solsø owner boundary differs",
    )
    require(
        type(row["verification"]) is str and bool(row["verification"]),
        "Owner verification limits must remain explicit",
    )
    return {str(key): value for key, value in row.items()}


def number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def inspect_relations(
    controls: list[dict[str, Any]], ages: list[dict[str, Any]]
) -> dict[str, Any]:
    selected = [r for r in controls if r["collection_unit_id"] == CORE_1983]
    matches: Counter[tuple[Any, ...]] = Counter()
    chronology_rows: dict[str, list[tuple[Any, ...]]] = {}
    native_control_ids = []
    source_numeric_ids = set()
    native_geochron_ids = set()
    for row in selected:
        source = row["source_payload"]
        geo = source["geochron"]
        require(
            type(geo["labnumber"]) is str and type(row["chronology_id"]) is str,
            "Typed source labels required",
        )
        native_id = row["source_chronology_control_id"]
        require(
            type(native_id) is int
            and native_id > 0
            and exact(native_id, source["chroncontrolid"])
            and row["chronology_control_id"]
            == row["chronology_id"] + ":control:" + str(native_id),
            "Native chronology control identity join differs",
        )
        require(
            row["site_id"] == SITE
            and source["chroncontroltype"] == "Radiocarbon"
            and geo["agetype"] == "Radiocarbon years BP",
            "Named site/control source role differs",
        )
        native_control_ids.append(row["chronology_control_id"])
        source_numeric_ids.add(native_id)
        require(
            type(geo["geochronid"]) is int and geo["geochronid"] > 0,
            "Typed native radiocarbon control ID required",
        )
        native_geochron_ids.add(geo["geochronid"])
        require(
            all(
                number(v)
                for v in (
                    source["depth"],
                    geo["geochronage"],
                    geo["geochronerrorolder"],
                    geo["geochronerroryounger"],
                    geo["delta13c"],
                )
            ),
            "Finite native control fields required",
        )
        require(
            exact(geo["geochronerrorolder"], geo["geochronerroryounger"]),
            "Asymmetric source error",
        )
        key = (
            geo["labnumber"],
            source["depth"],
            geo["geochronage"],
            geo["geochronerrorolder"],
            geo["delta13c"],
        )
        # Typed JSON cells must match the declared producer constants individually.
        require(
            any(
                all(exact(a, b) for a, b in zip(key, expected, strict=True))
                for expected in DECLARED
            ),
            "Undeclared or mistyped control",
        )
        matches[key] += 1
        chronology_rows.setdefault(row["chronology_id"], []).append(key)
    require(
        len(selected) == 14
        and set(matches) == set(DECLARED)
        and set(matches.values()) == {2},
        "Seven controls/two views changed",
    )
    require(
        len(set(native_control_ids)) == 14,
        "Fourteen distinct native chronology control view IDs required",
    )
    require(
        len(source_numeric_ids) == 14 and len(native_geochron_ids) == 7,
        "Retained native relation/control denominators changed",
    )
    require(
        len(chronology_rows) == 2
        and all(
            Counter(rows) == Counter(DECLARED) for rows in chronology_rows.values()
        ),
        "Each chronology must contain every declared control",
    )
    calibrated = [
        r
        for r in ages
        if r["site_id"] == SITE
        and r["source_age_type"] == "Calibrated radiocarbon years BP"
        and r["collection_unit_id"] in (CORE_1981, CORE_1983)
    ]
    require(
        all(
            type(r["source_record_id"]) is str and r["source_record_id"]
            for r in calibrated
        ),
        "Native source record IDs required",
    )
    require(
        all(
            r["subject_type"] == "sample"
            and r["subject_id"] == r["source_record_id"]
            and r["source_record_id"].startswith("neotoma:sample:")
            and exact(r["source_age_value"], r["source_payload"]["age"])
            and r["source_payload"]["agetype"] == r["source_age_type"]
            for r in calibrated
        ),
        "Native sample/source age join differs",
    )
    require(
        len(calibrated) == 92
        and len({r["source_record_id"] for r in calibrated}) == 92,
        "92 distinct calibrated native records required",
    )
    require(
        all(number(r["source_age_value"]) for r in calibrated),
        "Finite numeric source ages required",
    )
    proxy = [
        r
        for r in calibrated
        if (r["source_age_value"] >= 7210 or r["source_age_value"] <= 3490)
        if r["collection_unit_id"] == CORE_1981
    ]
    proxy.extend(
        r
        for r in calibrated
        if r["collection_unit_id"] == CORE_1983
        and 3700 <= r["source_age_value"] <= 7180
    )
    bounded = [r for r in proxy if 10 <= r["source_age_value"] <= 11659]
    counts = dict(sorted(Counter(r["collection_unit_id"] for r in proxy).items()))
    bounded_counts = dict(
        sorted(Counter(r["collection_unit_id"] for r in bounded).items())
    )
    require(
        counts == {CORE_1981: 56, CORE_1983: 20}
        and bounded_counts == {CORE_1981: 54, CORE_1983: 20},
        "Declared proxy selection changed",
    )
    return {
        "chronologies": sorted(chronology_rows),
        "control_rows": 14,
        "native_control_view_ids": sorted(native_control_ids),
        "source_control_numeric_ids": sorted(source_numeric_ids),
        "native_geochron_numeric_ids": sorted(native_geochron_ids),
        "declared_control_count": 7,
        "native_sample_ids": sorted(r["source_record_id"] for r in calibrated),
        "proxy_ids": sorted(r["source_record_id"] for r in proxy),
        "bounded_proxy_ids": sorted(r["source_record_id"] for r in bounded),
        "proxy_by_core": counts,
        "bounded_by_core": bounded_counts,
    }


def verify_report(
    report: dict[str, Any], original: dict[str, Any], joins: dict[str, Any]
) -> None:
    require(exact(report, original), "Complete retained report typed values differ")
    expected = {
        "published_1983_controls": 7,
        "neotoma_1983_control_rows": 14,
        "exact_published_control_matches": 7,
        "neotoma_calibrated_samples": 92,
        "paper_interval_proxy_samples": 76,
        "paper_interval_and_landclim_age_span_proxy_samples": 74,
        "landclim_ii_reported_sample_count": 79,
        "paper_interval_proxy_gap_to_landclim_ii": 3,
        "bounded_proxy_gap_to_landclim_ii": 5,
        "lra_admitted_samples": 0,
    }
    require(
        all(exact(report[k], value) for k, value in expected.items()),
        "Native denominators/proxy gaps changed",
    )
    require(
        exact(report["neotoma_1983_chronologies"], joins["chronologies"]),
        "Chronology IDs differ",
    )
    require(
        exact(report["paper_interval_proxy_by_core"], joins["proxy_by_core"])
        and exact(
            report["paper_interval_and_landclim_age_span_proxy_by_core"],
            joins["bounded_by_core"],
        ),
        "Native selections differ",
    )
    require(
        report["core_locations_in_paper_local_metres"]["georeferenced"] is False,
        "Georeferenced basin cannot be inferred",
    )


def closed_ledger(ages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Independent source-central-point classification; preserve every original cell."""
    selected = [
        r
        for r in ages
        if r["site_id"] == SITE
        and r["source_age_type"] == "Calibrated radiocarbon years BP"
        and r["collection_unit_id"] in (CORE_1981, CORE_1983)
    ]
    require(len(selected) == 92, "Raw central-point denominator differs")
    ledger = []
    for row in sorted(selected, key=lambda r: r["source_record_id"]):
        value = row["source_age_value"]
        require(number(value), "Finite central source age required")
        if row["collection_unit_id"] == CORE_1981:
            closed = (-31 <= value <= 3490) or (7210 <= value <= 11650)
            legacy = value >= 7210 or value <= 3490
        else:
            closed = legacy = 3700 <= value <= 7180
        ledger.append(
            {
                "source_record": row,
                "closed_central_point_proxy_selected": closed,
                "legacy_unbounded_central_point_proxy_selected": legacy,
                "bounded_closed_central_point_proxy_selected": closed
                and 10 <= value <= 11659,
                "analytical_eligibility_evaluated": False,
                "lra_admitted": False,
            }
        )
    return ledger


def expected_closed_report(
    original: dict[str, Any], joins: dict[str, Any], ages: list[dict[str, Any]]
) -> dict[str, Any]:
    """Exact current schema inferred from raw relations, never a preasserted total."""
    ledger = closed_ledger(ages)
    selected = [
        r["source_record"] for r in ledger if r["closed_central_point_proxy_selected"]
    ]
    bounded = [
        r["source_record"]
        for r in ledger
        if r["bounded_closed_central_point_proxy_selected"]
    ]
    excluded = [
        {
            "source_record_id": r["source_record"]["source_record_id"],
            "collection_unit_id": r["source_record"]["collection_unit_id"],
            "source_age_value": r["source_record"]["source_age_value"],
            "source_age_type": r["source_record"]["source_age_type"],
            "source_record": r["source_record"],
            "exclusion_reason": "central_value_outside_complete_closed_paper_interval",
        }
        for r in ledger
        if r["legacy_unbounded_central_point_proxy_selected"]
        and not r["closed_central_point_proxy_selected"]
    ]
    result = dict(original)
    result.update(
        {
            "schema_version": "solsoe-original-core-selection.v2",
            "paper_interval_proxy_samples": len(selected),
            "paper_interval_proxy_by_core": dict(
                sorted(Counter(r["collection_unit_id"] for r in selected).items())
            ),
            "paper_interval_and_landclim_age_span_proxy_samples": len(bounded),
            "paper_interval_and_landclim_age_span_proxy_by_core": dict(
                sorted(Counter(r["collection_unit_id"] for r in bounded).items())
            ),
            "paper_interval_proxy_gap_to_landclim_ii": 79 - len(selected),
            "bounded_proxy_gap_to_landclim_ii": 79 - len(bounded),
            "legacy_unbounded_proxy": {
                "calculation": "1981 age >= 7210 OR age <= 3490; 1983 3700 <= age <= 7180",
                "historical_report_sha256": IDENTITIES[REPORT][0],
                "selected_samples": len(joins["proxy_ids"]),
                "selected_by_core": joins["proxy_by_core"],
                "bounded_selected_samples": len(joins["bounded_proxy_ids"]),
                "selected_native_sample_ids": joins["proxy_ids"],
                "scope": "Historical half-unbounded conditional comparison, not the complete stated paper intervals",
            },
            "closed_paper_interval_proxy": {
                "reference_epoch": "1950 CE",
                "boundary_convention": "inclusive",
                "intervals_bp_by_core": {
                    CORE_1981: [[-31, 3490], [7210, 11650]],
                    CORE_1983: [[3700, 7180]],
                },
                "selected_native_sample_ids": sorted(
                    r["source_record_id"] for r in selected
                ),
                "bounded_selected_native_sample_ids": sorted(
                    r["source_record_id"] for r in bounded
                ),
                "legacy_selected_rows_excluded": excluded,
                "source_chronology_equivalence_claimed": False,
                "older_endpoint_source_limit": "The paper's 9700 BC boundary is extrapolated; this declared proxy does not newly calibrate it",
                "calendar_conversion_limit": "BC + 1950 is the existing declared arithmetic proxy, not a resolved no-year-zero calendar conversion",
                "selection_measure": "Raw source central age only; neither full uncertainty containment nor overlap",
                "analytical_eligibility_evaluated": False,
                "native_source_proxy_ledger": ledger,
            },
        }
    )
    return result


def verify_closed_report(
    report: dict[str, Any],
    original: dict[str, Any],
    joins: dict[str, Any],
    ages: list[dict[str, Any]],
) -> None:
    require(
        exact(report, expected_closed_report(original, joins, ages)),
        "Closed report/source ledger exact typed values differ",
    )
    require(
        exact(report["neotoma_1983_chronologies"], joins["chronologies"])
        and exact(report["neotoma_1983_control_rows"], joins["control_rows"]),
        "Native control views differ from current report",
    )
    require(
        report["lra_admitted_samples"] == 0
        and report["core_locations_in_paper_local_metres"]["georeferenced"] is False,
        "Physical/LRA scope expanded",
    )
