"""Reconcile source-reported Nordic AADR IDs with governed country products."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from functools import cache
from hashlib import sha256
import io
import json
from pathlib import Path

from bijux_pollenomics.adna.species.homo_sapiens.materialization.models import (
    AadrCoordinateEvidence,
)
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
from bijux_pollenomics.collection.sources.boundaries.store import (
    load_repository_country_boundaries,
)
from bijux_pollenomics_dev.source_completion.adna.aadr_country_support import (
    coordinate_country_support,
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
SPATIAL_FIELDS = (
    "coordinate_groups",
    "coordinate_group_statuses",
    "coordinate_reconciliation_status",
    "spatial_status",
    "spatial_method",
    "spatial_country",
    "spatial_candidates",
    "spatial_reason",
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


def run(root: Path, output: Path, *, country_support: bool = False) -> None:
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
    boundary_inputs: list[dict[str, object]] = []
    boundaries = (
        load_repository_country_boundaries(root / "data") if country_support else {}
    )
    boundary_manifest = root / "data/boundaries/raw/source_manifest.json"
    if country_support:
        boundary_inputs = [
            _identity(path, root)
            for path in [
                boundary_manifest,
                *(
                    root / f"data/boundaries/raw/{name.lower()}.geojson"
                    for name in COUNTRIES.values()
                ),
            ]
        ]
    boundary_manifest_bytes = boundary_manifest.read_bytes() if country_support else b""
    boundary_version = (
        json.loads(boundary_manifest_bytes)["version"] if country_support else ""
    )

    @cache
    def support(
        country: str, evidence: tuple[AadrCoordinateEvidence, ...]
    ) -> dict[str, str | None]:
        return coordinate_country_support(
            evidence,
            source_country=COUNTRIES[country],
            boundaries=boundaries,
            boundary_digest=sha256(boundary_manifest_bytes).hexdigest(),
            boundary_version=boundary_version,
        )

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
    rows: list[dict[str, str | int | None]] = []
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
        if country_support:
            rows[-1].update(
                coordinate_groups=len(record.coordinate_groups),
                coordinate_reconciliation_status=record.coordinate_status,
                coordinate_group_statuses=";".join(
                    group.evidence.status for group in record.coordinate_groups
                ),
                **support(
                    country, tuple(group.evidence for group in record.coordinate_groups)
                ),
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
    writer = csv.DictWriter(
        buffer,
        fieldnames=FIELDS + SPATIAL_FIELDS if country_support else FIELDS,
        lineterminator="\n",
    )
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
    if country_support:
        if boundary_inputs != [
            _identity(root / str(item["path"]), root) for item in boundary_inputs
        ]:
            raise ValueError("AADR boundary inputs changed during comparison")
        report["schema_version"] = "aadr-nordic-country-support.v1"
        report["boundary_inputs"] = boundary_inputs
        report["spatial_counts"] = {
            code: dict(
                sorted(
                    Counter(
                        str(row["spatial_status"])
                        for row in rows
                        if row["country"] == code
                    ).items()
                )
            )
            for code in COUNTRIES
        }
        report["spatial_scope"] = {
            "source_coordinate_precision_validated": False,
            "country_review_accepted": False,
            "boundary_crs": "EPSG:4326",
            "coordinate_interpretation": "Source latitude/longitude on the boundary degree axes; source datum, spatial precision and archaeological locality accuracy are not independently qualified.",
            "boundary_version": boundary_version,
            "outside_proximity_review_band_degrees": 0.15,
            "review_band_is_coordinate_uncertainty": False,
            "coordinate_group_policy": "One distinct usable numeric pair; missing claims may complement it. Conflicting or invalid nonmissing claims refuse. Original groups remain separate source evidence.",
        }
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
    parser.add_argument("--country-support", action="store_true")
    arguments = parser.parse_args()
    run(
        arguments.repository.resolve(),
        arguments.output.resolve(),
        country_support=arguments.country_support,
    )
