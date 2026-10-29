"""Synthetic portable DNA namespaces, full default schemas and domain refusals."""

from __future__ import annotations

from copy import deepcopy
import csv
from functools import partial
import io
import json
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.adna.current_domain import (
    CURRENT_FIELDS,
    SCHEMA,
    clean,
    qualify_record_modality,
    record_taxon,
    scan_products,
)


def refuses(call: Any) -> None:
    try:
        call()
    except (ReportRebuildError, ValueError, KeyError, TypeError):
        return
    raise AssertionError("Expected bounded DNA metadata refusal")


def artificial_products() -> tuple[dict[str, Any], dict[str, bytes]]:
    sample = dict.fromkeys(SCHEMA["typed_record_fields"])
    sample.update(
        identity={"stable_token": "synthetic-id"},
        species_latin_name="Homo sapiens",
        record_modality="metadata_only",
    )
    typed = {
        "country_query": "Denmark",
        "actual_typed_records": [sample],
        "actual_dataset_row_counts": {"synthetic": 1},
    }
    row = dict.fromkeys(CURRENT_FIELDS, "")
    row.update(
        schema_version="adna-sample-record-export.v2",
        species_latin_name="Homo sapiens",
        genetic_id="synthetic-id",
        sample_chronology="{}",
        sample_identity="{}",
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CURRENT_FIELDS)
    writer.writeheader()
    writer.writerow(row)
    properties: dict[str, Any] = dict(row)
    properties["sample_chronology"] = {}
    properties["sample_identity"] = {}
    geo = {
        "schema_version": "adna-sample-geojson-collection.v2",
        "type": "FeatureCollection",
        "features": [
            {
                "schema_version": "adna-sample-geojson.v2",
                "type": "Feature",
                "geometry": None,
                "properties": properties,
            }
        ],
    }
    payload = {
        "typed": json.dumps(typed).encode(),
        "csv": stream.getvalue().encode(),
        "geojson": json.dumps(geo).encode(),
    }
    item = {
        "domain": "human",
        "species": {"latin_name": "Homo sapiens"},
        "query": "Denmark",
        "records": 1,
        "rows": {
            key: {"path": "/" + key, "sha256": "a" * 64, "bytes": len(raw)}
            for key, raw in payload.items()
        },
    }
    return item, payload


def scan(item: dict[str, Any], payload: dict[str, bytes]) -> Any:
    return scan_products(
        [item], SCHEMA, lambda row: payload[row["path"].removeprefix("/")]
    )


def test_complete_typed_default_products() -> None:
    item, payload = artificial_products()
    observed, _ = scan(item, payload)
    assert (
        observed[0]["records"] == 1
        and observed[0]["no_pollen_semantics_leakage"] is True
    )


def test_recursive_pollen_and_modality_refusals() -> None:
    for sample, domain in [
        ({"record_modality": "archive_reads"}, "human"),
        ({"record_modality": "metadata_only"}, "animal"),
        ({"record_modality": "unknown"}, "animal"),
    ]:
        refuses(partial(qualify_record_modality, sample, domain, SCHEMA))
    for value in (
        {"nested": {"POLLEN_COUNT": 1}},
        {"pollen_eligible": True},
        {"nested": [{"pollen_propagation_eligible": 0}]},
    ):
        refuses(partial(clean, value, SCHEMA, set()))
    clean({"nested": {"pollen_eligible": False}}, SCHEMA, set())


def test_four_source_taxon_contexts_stay_blocked() -> None:
    for exception in SCHEMA["blocked_source_taxon_exceptions"]:
        item = {
            "domain": "animal",
            "species": {
                "latin_name": "Bos taurus"
                if exception["container_slug"] == "bos_taurus"
                else "Ovis aries",
                "slug": exception["container_slug"],
            },
        }
        sample = {
            "species_latin_name": exception["source_species"],
            "source_native_scientific_name": exception["source_species"],
            "source_native_tax_id": exception["source_native_tax_id"],
            "master_id": exception["master_id"],
            "project_accession": exception["project_accession"],
            "source_family": "ENA",
            "source_native_identity_kind": "biological_sample_accession",
            "taxon_alignment_status": "project_species_mismatch",
            "inclusion_status": "sample_context_blocked",
        }
        record_taxon(sample, item, SCHEMA)
        for key, value in [
            ("inclusion_status", "accepted"),
            ("taxon_alignment_status", "matched"),
            ("master_id", "unknown"),
        ]:
            changed = deepcopy(sample)
            changed[key] = value
            refuses(partial(record_taxon, changed, item, SCHEMA))


def test_default_product_mutations_refused() -> None:
    for kind in (
        "typed_field",
        "query",
        "modality",
        "pollen_nested",
        "csv_schema",
        "csv_missing",
        "csv_extension",
        "geo_field",
        "geo_population",
        "json_nonfinite",
    ):
        item, payload = artificial_products()
        if kind in ("typed_field", "query", "modality", "pollen_nested"):
            typed = json.loads(payload["typed"])
            if kind == "typed_field":
                typed["actual_typed_records"][0]["new_field"] = None
            elif kind == "query":
                typed["country_query"] = "Sweden"
            elif kind == "modality":
                typed["actual_typed_records"][0]["record_modality"] = "archive_reads"
            else:
                typed["actual_typed_records"][0]["identity"]["pollen_eligible"] = True
            payload["typed"] = json.dumps(typed).encode()
        elif kind == "csv_schema":
            payload["csv"] = payload["csv"].replace(
                b"adna-sample-record-export.v2", b"adna-sample-record-export.v1"
            )
        elif kind == "csv_missing":
            payload["csv"] = payload["csv"].splitlines(keepends=True)[0]
        elif kind == "csv_extension":
            payload["csv"] = payload["csv"].replace(b"{},{}", b"[],{}")
        elif kind == "json_nonfinite":
            payload["typed"] = payload["typed"].replace(b"null", b"NaN", 1)
        else:
            geo = json.loads(payload["geojson"])
            if kind == "geo_field":
                geo["features"][0]["properties"]["extra"] = 1
            else:
                geo["features"] = []
            payload["geojson"] = json.dumps(geo).encode()
        refuses(partial(scan, item, payload))
