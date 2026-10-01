"""Reconcile source-reported Nordic AADR IDs with governed country products."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from hashlib import sha256
import io
import json
from pathlib import Path

from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    reconcile_aadr_panels,
)
from bijux_pollenomics.collection.sources.aadr.materialization.accountability.political_entities import (
    reconcile_source_reported_political_entities,
)
from bijux_pollenomics.collection.sources.aadr.materialization.accountability.validation import (
    validate_aadr_source_accountability_receipt,
)
from bijux_pollenomics.collection.sources.aadr.materialization.inputs import (
    load_aadr_release_inputs,
)

COUNTRIES = {"DK": "Denmark", "FI": "Finland", "NO": "Norway", "SE": "Sweden"}
FIELDS = (
    "genetic_id",
    "country",
    "decision",
    "reason",
    "coordinate_status",
    "chronology_status",
    "chronology_reason",
    "source_rows",
)


def _identity(path: Path, root: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(content),
        "sha256": sha256(content).hexdigest(),
    }


def _published_ids(
    root: Path, country: str, name: str
) -> tuple[set[str], dict[str, object]]:
    slug = name.lower()
    path = (
        root / "docs" / "report" / "countries" / slug / f"{slug}_aadr_v66_samples.csv"
    )
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ids = {row["genetic_id"] for row in rows}
    if len(ids) != len(rows) or any(row["political_entity"] != name for row in rows):
        raise ValueError(f"Duplicate or mismatched {country} published AADR row")
    summary = json.loads((path.parent / f"{slug}_aadr_v66_summary.json").read_text())
    if summary["total_unique_samples"] != len(ids) or summary["country"] != name:
        raise ValueError(f"Published {country} sample count differs from summary")
    return ids, _identity(path, root)


def run(root: Path, output: Path) -> None:
    if output.exists():
        raise ValueError(f"Output directory already exists: {output}")
    receipt_path = (
        root
        / "data/adna/species/homo_sapiens/review/aadr_v66_source_accountability.json"
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    validate_aadr_source_accountability_receipt(receipt)
    if (
        receipt["map_admitted"] is not False
        or receipt["scientifically_admitted"] is not False
    ):
        raise ValueError("AADR source-accountability admission posture changed")
    inputs = load_aadr_release_inputs(root / "data", "v66")
    expected_sources = {
        row["path"]: row["sha256"] for row in receipt["input_artifacts"]
    }
    source_inputs = [_identity(path, root) for path, _ in inputs.files]
    if {row["path"]: row["sha256"] for row in source_inputs} != expected_sources:
        raise ValueError("AADR raw source identity differs from accountability receipt")

    reconciliation = reconcile_aadr_panels(inputs.source_tables)
    dispositions = {
        row.genetic_id: row.disposition
        for row in reconcile_source_reported_political_entities(reconciliation)
    }
    published = {}
    published_sources = []
    for code, name in COUNTRIES.items():
        published[code], source = _published_ids(root, code, name)
        published_sources.append(source)
    rows = []
    counts: dict[str, Counter[str]] = {code: Counter() for code in COUNTRIES}
    for record in reconciliation.records:
        country = dispositions[record.genetic_id]
        if country not in COUNTRIES:
            continue
        coordinate_status = (
            record.coordinate_groups[0].evidence.status
            if len(record.coordinate_groups) == 1
            else "conflict"
        )
        chronology = (
            record.chronology_groups[0].evidence
            if len(record.chronology_groups) == 1
            else None
        )
        included = record.genetic_id in published[country]
        if included and coordinate_status != "admitted":
            raise ValueError(
                f"Published ID lacks usable coordinates: {record.genetic_id}"
            )
        if not included and coordinate_status != "missing":
            raise ValueError(f"Unaccounted source-to-country ID: {record.genetic_id}")
        decision = "published" if included else "excluded"
        counts[country][decision] += 1
        rows.append(
            {
                "genetic_id": record.genetic_id,
                "country": country,
                "decision": decision,
                "reason": "country_sample_product"
                if included
                else "coordinate_missing",
                "coordinate_status": coordinate_status,
                "chronology_status": (
                    chronology.evaluation_status if chronology else "conflict"
                ),
                "chronology_reason": (
                    chronology.refusal_reason_code if chronology else "conflict"
                ),
                "source_rows": ";".join(
                    f"{link.dataset_name}:{link.source_record_number}"
                    for link in record.source_rows
                ),
            }
        )
    rows.sort(key=lambda row: (str(row["country"]), str(row["genetic_id"])))
    expected_counts = receipt["source_reported_political_entity"][
        "genetic_id_disposition_counts"
    ]
    for code in COUNTRIES:
        if (
            counts[code]["published"] != len(published[code])
            or sum(counts[code].values()) != expected_counts[code]
        ):
            raise ValueError(f"AADR {code} source-to-product denominator differs")
    if len(rows) != sum(expected_counts[code] for code in COUNTRIES):
        raise ValueError("AADR Nordic source denominator differs")

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    decision_bytes = buffer.getvalue().encode("utf-8")
    report = {
        "schema_version": "aadr-nordic-entity-account.v1",
        "source_release": "v66",
        "source_accountability": _identity(receipt_path, root),
        "source_inputs": source_inputs,
        "country_sample_products": published_sources,
        "decision_file": {
            "path": "decisions.csv",
            "rows": len(rows),
            "bytes": len(decision_bytes),
            "sha256": sha256(decision_bytes).hexdigest(),
        },
        "country_counts": {
            code: {
                "source_genetic_ids": expected_counts[code],
                "published": counts[code]["published"],
                "excluded_missing_coordinates": counts[code]["excluded"],
            }
            for code in COUNTRIES
        },
        "source_genetic_ids": len(rows),
        "published": sum(counts[code]["published"] for code in COUNTRIES),
        "excluded_missing_coordinates": sum(
            counts[code]["excluded"] for code in COUNTRIES
        ),
        "map_admitted": False,
        "scientifically_admitted": False,
    }
    inputs.verify_unchanged()
    output.mkdir(parents=True)
    (output / "decisions.csv").write_bytes(decision_bytes)
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"reconciled {report['source_genetic_ids']} source IDs: "
        f"{report['published']} published, "
        f"{report['excluded_missing_coordinates']} excluded for missing coordinates"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.repository.resolve(), arguments.output.resolve())
