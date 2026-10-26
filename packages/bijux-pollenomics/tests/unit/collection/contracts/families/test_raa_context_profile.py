"""A native acquisition profile cannot promote the separate WFS density authority."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.collection.contracts.families import (
    build_source_family_state_matrix_payload,
)
from bijux_pollenomics.collection.sources.raa.materialization.context import (
    open_raa_source_context,
)

from ...sources.raa.geometry.support import database, identity

ROOT = Path(__file__).resolve().parents[7]


def raa_row(data: Path) -> dict[str, object]:
    payload = build_source_family_state_matrix_payload(data, counts={})
    rows = cast(list[dict[str, object]], payload["rows"])
    assert all(
        "source_context_profile" not in row
        for row in rows
        if row["source_key"] != "raa"
    )
    return next(row for row in rows if row["source_key"] == "raa")


def prepare(root: Path) -> tuple[Path, Path]:
    inputs = root / "inputs"
    inputs.mkdir()
    raw = database(inputs)
    digest, size = identity(raw)
    descriptor = json.loads(
        (ROOT / "data/raa/raw/national_geopackage_source.json").read_bytes()
    )
    descriptor.update(sha256=digest, byte_count=size)
    data = root / "data"
    target = data / "raa/raw/national_geopackage_source.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(descriptor))
    with open_raa_source_context(raw, descriptor) as context:
        profile = context.profile
    counts = cast(dict[str, int], profile["native_table_row_counts"])
    reports = root / "reports/science/archaeology-native-reconciliation"
    reports.mkdir(parents=True)
    population = {
        "source_identity": profile["source_identity"],
        "source_context_profile": profile,
        "scientific_admission": False,
        "chronology_admission": False,
        "native_ownership_summary": {
            "tables": {name: {"source_rows": value} for name, value in counts.items()}
        },
    }
    geometry = {
        "source_identity": profile["source_identity"],
        "native_geometry_summary": {
            "tables": {
                name: {"source_rows": counts[name]}
                for name in (
                    "point",
                    "linestring",
                    "polygon",
                    "lämningar_sverige_lägesosäkerhet",
                )
            },
            "geometry_occurrences": 0,
            "crs_status": "declared_crs_verified",
            "boundary": {
                "scientific_admission": False,
                "chronology_admission": False,
                "canonical_source_adoption": False,
            },
        },
    }
    (reports / "report.json").write_text(json.dumps(population))
    (reports / "geometry.json").write_text(json.dumps(geometry))
    return data, reports


def test_generated_optional_profile_preserves_all_legacy_fields(tmp_path: Path) -> None:
    initial = raa_row(tmp_path / "data")
    data, _ = prepare(tmp_path)
    current = raa_row(data)
    profile = cast(dict[str, object], current.pop("source_context_profile"))
    assert current == initial
    assert current["authority_status"] == "refused"
    assert current["published_status"] == "refused"
    assert current["coverage_metrics"] == {
        "raa_total_site_count": None,
        "raa_heritage_site_count": None,
    }
    assert profile["status"] == "admitted_source_context"
    assert profile["source_record_count"] == 1
    assert profile["scientific_admission"] is False
    assert profile["legacy_density_admission"] is False
    assert profile["publication_admission"] is False


@pytest.mark.parametrize(
    "mutation", ["source", "rights", "science", "counts", "scope", "missing"]
)
def test_source_context_profile_refuses_unbound_qualification(
    tmp_path: Path, mutation: str
) -> None:
    data, reports = prepare(tmp_path)
    if mutation == "missing":
        (reports / "report.json").unlink()
    else:
        path = (
            data / "raa/raw/national_geopackage_source.json"
            if mutation == "rights"
            else reports / "geometry.json"
            if mutation in {"source", "counts"}
            else reports / "report.json"
        )
        value = json.loads(path.read_bytes())
        if mutation == "rights":
            value["rights_status"] = "not established"
        elif mutation == "source":
            value["source_identity"]["sha256"] = "f" * 64
        elif mutation == "counts":
            value["native_geometry_summary"]["geometry_occurrences"] = 1
        elif mutation == "science":
            value["scientific_admission"] = True
        elif mutation == "scope":
            value["source_context_profile"]["publication_admission"] = True
        path.write_text(json.dumps(value))
    profile = cast(dict[str, object], raa_row(data)["source_context_profile"])
    assert profile["status"] == "not_admitted"
    assert profile["reason_codes"] == [
        "missing_or_invalid_native_context_qualification"
    ]
