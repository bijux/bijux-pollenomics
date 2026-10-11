"""Compare the published Solsø core rule with retained Neotoma source relations."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
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

    # Odgaard 1994, printed page 42 (PDF page 39): 1981 covers 9700–5260 BC
    # and 1540 BC–AD 1981; 1983 covers 5230–1750 BC. These use the paper's
    # calendar-year boundaries. Applying them to Neotoma ages is a proxy only.
    def selected(row: dict[str, object]) -> bool:
        age = row["source_age_value"]
        if not isinstance(age, (int, float)):
            raise ValueError("Non-numeric calibrated sample age")
        if row["collection_unit_id"] == CORE_1981:
            return age >= 7210 or age <= 3490
        return 3700 <= age <= 7180

    proxy = [row for row in calibrated if selected(row)]
    in_landclim_span = [row for row in proxy if 10 <= row["source_age_value"] <= 11659]
    counts = Counter(row["collection_unit_id"] for row in proxy)
    bounded_counts = Counter(row["collection_unit_id"] for row in in_landclim_span)
    if counts != {CORE_1981: 56, CORE_1983: 20}:
        raise ValueError("Paper-interval proxy changed")
    return {
        "schema_version": "solsoe-original-core-selection.v1",
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
