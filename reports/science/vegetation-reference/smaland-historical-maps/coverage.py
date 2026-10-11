"""Extract published map support and pollen anchors from the Cui et al. study."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


SOURCES = {
    "article.xml": "300b147cb3318924ac734ae47666ce4a4799e44f8d6ee680b218265dae4b8948",
    "appendix-s1.pdf": "e315ffdbc0fb1db10bb81c6468ea9331e56c342ada7137947189d7deab20a8b9",
    "pmc-metadata.json": "4d85d8206321c58ec37dd551ccf87dddeeceab4a39a248f12375c8c14d863109",
}
SITE_NAMES = ("STAVÅKRA", "NOTTERYD", "STORASJÖ")


def _verified_bytes(root: Path, name: str) -> bytes:
    payload = (root / name).read_bytes()
    if hashlib.sha256(payload).hexdigest() != SOURCES[name]:
        raise ValueError(f"primary source changed: {name}")
    return payload


def produce(source_root: Path) -> dict[str, object]:
    metadata = json.loads(_verified_bytes(source_root, "pmc-metadata.json"))
    if (metadata["pmcid"], metadata["doi"], metadata["license_code"]) != (
        "PMC4224531",
        "10.1002/ece3.1198",
        "CC BY",
    ):
        raise ValueError("article identity or release rights changed")

    article = ET.fromstring(_verified_bytes(source_root, "article.xml"))
    if {item.get("id") for item in article.findall(".//table-wrap")} != {
        "tbl1",
        "tbl2",
    }:
        raise ValueError("published article table inventory changed")
    table = article.find('.//table-wrap[@id="tbl1"]')
    if table is None:
        raise ValueError("published pollen time-window table missing")
    rows = table.findall("./table/tbody/tr")
    if len(rows) != 5:
        raise ValueError("published pollen time-window rows changed")
    first = [" ".join(cell.itertext()).strip() for cell in rows[0].findall("td")]
    third = [" ".join(cell.itertext()).strip() for cell in rows[2].findall("td")]
    if first != [
        "TW1 AD 1950–2010",
        "Topographic map (2008, 2010)",
        "1950/1950",
        "2536",
        "1930/1993/1935",
        "617/841/574",
    ] or third[:2] != ["TW3 AD 1825–1925", "Lagaskifte Period (1825–1922)"]:
        raise ValueError("published pollen anchors changed")

    appendix = _verified_bytes(source_root, "appendix-s1.pdf")
    converted = subprocess.run(
        [
            "gs",
            "-q",
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=txtwrite",
            "-sOutputFile=-",
            "-",
        ],
        input=appendix,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8")
    text = re.sub(r"\s+", " ", converted)
    start = text.index("Table 1 Historical maps within a 3 km-radius area")
    end = text.index("Harmonization of land-use/vegetation classes", start)
    table_text = text[start:end]
    coverage: list[dict[str, object]] = []
    for site in SITE_NAMES:
        match = re.search(
            rf"{site} .*?Coverage of Maps (\d+)% (\d+)% (\d+)% (\d+)% \(%\)",
            table_text,
        )
        if match is None:
            raise ValueError(f"map support row missing: {site}")
        values = [int(value) for value in match.groups()]
        coverage.append(
            {
                "site": site,
                "modern_tw1_tw2_percent": values[0],
                "reform_tw3_percent": values[1],
                "tw4_storskifte_percent": values[2],
                "tw4_older_percent": values[3],
            }
        )
    if [tuple(row.values())[1:] for row in coverage] != [
        (100, 75, 24, 10),
        (100, 12, 63, 11),
        (100, 77, 59, 0),
    ]:
        raise ValueError("published map support changed")

    pollen_age_ce = [int(value) for value in first[4].split("/")]
    pollen_count = [int(value) for value in first[5].split("/")]
    for row, age, count in zip(coverage, pollen_age_ce, pollen_count, strict=True):
        row["shared_tw1_tw2_pollen_age_ce"] = age
        row["shared_tw1_tw2_pollen_count"] = count
        row["map_class_area_values_available_in_article_tables"] = False
        row["measured_vegetation_pair_admission"] = (
            "refused_numeric_reference_unavailable"
        )

    return {
        "schema_version": "smaland-historical-map-support.v1",
        "article_doi": metadata["doi"],
        "source_sha256": SOURCES,
        "map_radius_km": 3,
        "site_order_from_article_table_1": ["STAV", "NOTT", "STOR"],
        "time_window_1_and_2_share_one_pollen_sample_per_site": True,
        "coverage": coverage,
        "regional_reveals_tw1_tw2_age_ce": first[2],
        "regional_reveals_tw1_tw2_pollen_count": int(first[3]),
        "admission": "source_support_only_no_numeric_vegetation_benchmark",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = produce(args.source_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
