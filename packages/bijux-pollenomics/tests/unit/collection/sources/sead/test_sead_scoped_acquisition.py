from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition import (
    SeadAcquisitionError,
)
from bijux_pollenomics.collection.sources.sead.archive import (
    SEAD_LINKED_SOURCE_TABLES,
)
from bijux_pollenomics.collection.sources.sead.scoped_acquisition import (
    acquire_scoped_sead_relations,
)


def _source_tables() -> dict[str, list[dict[str, object]]]:
    sites = [
        {
            "site_id": site_id,
            "site_name": f"site-{site_id}",
            "national_site_identifier": f"national-{site_id}",
            "latitude_dd": 55.0 + site_id,
            "longitude_dd": 10.0 + site_id,
            "altitude": site_id,
            "site_description": f"description-{site_id}",
            "site_uuid": f"uuid-{site_id}",
        }
        for site_id in range(1, 6)
    ]
    sites.append(
        {
            "site_id": 99,
            "site_name": "outside-bbox",
            "national_site_identifier": "outside",
            "latitude_dd": 40.0,
            "longitude_dd": 40.0,
            "altitude": 0,
            "site_description": "outside",
            "site_uuid": "uuid-99",
        }
    )
    return {
        "tbl_sites": sites,
        "tbl_sample_groups": [
            {"sample_group_id": 11, "site_id": 1, "sample_group_name": "g1"},
            {"sample_group_id": 12, "site_id": 2, "sample_group_name": "g2"},
            {"sample_group_id": 13, "site_id": 3, "sample_group_name": "g3"},
            {"sample_group_id": 15, "site_id": 5, "sample_group_name": "excluded"},
            {"sample_group_id": 999, "site_id": 999, "sample_group_name": "global"},
        ],
        "tbl_physical_samples": [
            {"physical_sample_id": 21, "sample_group_id": 11},
            {"physical_sample_id": 22, "sample_group_id": 12},
            {"physical_sample_id": 23, "sample_group_id": 13},
            {"physical_sample_id": 25, "sample_group_id": 15},
            {"physical_sample_id": 999, "sample_group_id": 999},
        ],
        "tbl_analysis_entities": [
            {"analysis_entity_id": 31, "physical_sample_id": 21, "dataset_id": 101},
            {"analysis_entity_id": 32, "physical_sample_id": 22, "dataset_id": 102},
            {"analysis_entity_id": 33, "physical_sample_id": 23, "dataset_id": 103},
            {"analysis_entity_id": 35, "physical_sample_id": 25, "dataset_id": 105},
            {"analysis_entity_id": 999, "physical_sample_id": 999, "dataset_id": 999},
        ],
        "tbl_analysis_entity_ages": [
            {
                "analysis_entity_age_id": 41,
                "analysis_entity_id": 31,
                "age": 100,
                "age_older": 110,
                "age_younger": 90,
                "chronology_id": 1,
                "dating_specifier": "fixture",
                "age_range": 20,
            },
            {
                "analysis_entity_age_id": 42,
                "analysis_entity_id": 32,
                "age": 200,
                "age_older": 210,
                "age_younger": 190,
                "chronology_id": 2,
                "dating_specifier": "fixture",
                "age_range": 20,
            },
            {
                "analysis_entity_age_id": 43,
                "analysis_entity_id": 33,
                "age": 300,
                "age_older": 310,
                "age_younger": 290,
                "chronology_id": 3,
                "dating_specifier": "fixture",
                "age_range": 20,
            },
        ],
        "tbl_geochronology": [
            {
                "geochron_id": 51,
                "analysis_entity_id": 31,
                "dating_lab_id": 1,
                "lab_number": "lab-1",
                "age": 100,
                "error_older": 10,
                "error_younger": 10,
                "notes": None,
                "dating_uncertainty_id": 201,
            }
        ],
        "tbl_dendro_dates": [
            {
                "dendro_date_id": 61,
                "analysis_entity_id": 32,
                "age_older": 210,
                "age_younger": 190,
                "age_type_id": 301,
                "dating_uncertainty_id": 201,
                "dendro_lookup_id": 1,
                "season_id": 1,
                "age_range": 20,
            }
        ],
        "tbl_analysis_values": [
            {"analysis_value_id": 71, "analysis_entity_id": 31},
            {"analysis_value_id": 72, "analysis_entity_id": 32},
            {"analysis_value_id": 73, "analysis_entity_id": 33},
        ],
        "tbl_analysis_dating_ranges": [
            {
                "analysis_dating_range_id": 81,
                "analysis_value_id": 71,
                "low_value": 90,
                "high_value": 110,
                "age_type_id": 301,
                "dating_uncertainty_id": 201,
                "low_qualifier": None,
                "high_qualifier": None,
                "low_is_uncertain": False,
                "high_is_uncertain": False,
            },
            {
                "analysis_dating_range_id": 82,
                "analysis_value_id": 72,
                "low_value": 190,
                "high_value": 210,
                "age_type_id": 301,
                "dating_uncertainty_id": None,
                "low_qualifier": None,
                "high_qualifier": None,
                "low_is_uncertain": False,
                "high_is_uncertain": False,
            },
        ],
        "tbl_age_types": [
            {"age_type_id": 301, "age_type": "Calendar BP", "description": "fixture"}
        ],
        "tbl_relative_dates": [
            {
                "relative_date_id": 91,
                "analysis_entity_id": 33,
                "relative_age_id": 401,
                "dating_uncertainty_id": 201,
                "method_id": 501,
                "notes": "fixture",
            }
        ],
        "tbl_relative_ages": [
            {
                "relative_age_id": 401,
                "relative_age_name": "Period A",
                "description": "fixture",
                "abbreviation": "PA",
                "cal_age_older": None,
                "cal_age_younger": None,
                "c14_age_older": None,
                "c14_age_younger": None,
            }
        ],
        "tbl_relative_age_refs": [
            {"relative_age_ref_id": 601, "relative_age_id": 401, "biblio_id": 701}
        ],
        "tbl_dating_uncertainty": [
            {
                "dating_uncertainty_id": 201,
                "uncertainty": "reported",
                "description": "fixture",
            }
        ],
        "tbl_methods": [
            {
                "method_id": 501,
                "method_name": "stratigraphy",
                "method_abbrev_or_alt_name": "strat",
                "description": "fixture",
            }
        ],
        "tbl_datasets": [
            {"dataset_id": 101, "dataset_name": "d1", "biblio_id": 701},
            {"dataset_id": 102, "dataset_name": "d2", "biblio_id": 701},
            {"dataset_id": 103, "dataset_name": "d3", "biblio_id": None},
        ],
        "tbl_site_references": [
            {"site_reference_id": 801, "site_id": 1, "biblio_id": 701}
        ],
        "tbl_sample_group_references": [
            {"sample_group_reference_id": 901, "sample_group_id": 11, "biblio_id": 701}
        ],
        "tbl_biblio": [
            {
                "biblio_id": 701,
                "title": "Fixture",
                "full_reference": "Fixture reference",
                "year": 2026,
                "doi": "10.0000/fixture",
                "url": "https://example.invalid/fixture",
            }
        ],
    }


class _PostgrestFixture:
    def __init__(
        self,
        tables: dict[str, list[dict[str, object]]],
        *,
        ignore_filter_table: str | None = None,
        never_finish_table: str | None = None,
    ) -> None:
        self.tables = tables
        self.ignore_filter_table = ignore_filter_table
        self.never_finish_table = never_finish_table
        self.calls: list[dict[str, object]] = []

    def __call__(
        self,
        endpoint: str,
        *,
        params: list[tuple[str, str]],
        headers: dict[str, str],
        timeout: float,
    ) -> object:
        table = endpoint.rsplit("/", 1)[-1]
        self.calls.append(
            {
                "table": table,
                "params": list(params),
                "headers": dict(headers),
                "timeout": timeout,
            }
        )
        rows = [dict(row) for row in self.tables[table]]
        for field, expression in params:
            if field in {"select", "order"}:
                continue
            if table == self.ignore_filter_table and expression.startswith("in."):
                continue
            rows = [row for row in rows if _postgrest_match(row.get(field), expression)]
        order = next((value for key, value in params if key == "order"), "")
        order_fields = tuple(value for value in order.split(",") if value)
        if order_fields:
            rows.sort(
                key=lambda row: tuple(
                    (row.get(field) is None, row.get(field)) for field in order_fields
                )
            )
        select = next(value for key, value in params if key == "select")
        projected = [
            {field: row.get(field) for field in select.split(",")} for row in rows
        ]
        start_text, end_text = headers["Range"].split("-", 1)
        start = int(start_text)
        end = int(end_text)
        page = projected[start : end + 1]
        if table == self.never_finish_table:
            if not page:
                page = projected[:1]
            while page and len(page) < end - start + 1:
                page.append(dict(page[-1]))
        return page


def _postgrest_match(value: object, expression: str) -> bool:
    if expression.startswith("in.(") and expression.endswith(")"):
        permitted = {
            int(item)
            for item in expression.removeprefix("in.(").removesuffix(")").split(",")
        }
        return value in permitted
    if expression.startswith("gte."):
        return isinstance(value, (int, float)) and float(value) >= float(
            expression.removeprefix("gte.")
        )
    if expression.startswith("lte."):
        return isinstance(value, (int, float)) and float(value) <= float(
            expression.removeprefix("lte.")
        )
    raise AssertionError(f"Unexpected fixture filter: {expression}")


def _fixed_clock() -> datetime:
    return datetime(2026, 9, 4, 12, 0, tzinfo=UTC)


def _run(
    output_root: Path,
    fetcher: Callable[..., object],
    **overrides: Any,
):
    arguments: dict[str, object] = {
        "bbox": (5.0, 50.0, 30.0, 70.0),
        "governed_country_by_site_id": {
            1: "SE",
            2: "DK",
            3: "NO",
            4: "FI",
            5: "UNASSIGNED",
        },
        "country_assignment_id": "boundaries-fixture-v1",
        "scope_id": "nordic-fixture-v1",
        "run_id": "run-fixture-001",
        "parent_run_id": "parent-fixture-001",
        "build_id": "build-fixture-001",
        "fetch_json_fn": fetcher,
        "clock": _fixed_clock,
        "sleep_fn": lambda _seconds: None,
        "id_batch_size": 2,
        "page_size": 2,
        "max_pages": 10,
    }
    arguments.update(overrides)
    return acquire_scoped_sead_relations(output_root, **arguments)  # type: ignore[arg-type]


def test_scoped_acquisition_materializes_all_relations_without_orphan_pollution(
    tmp_path: Path,
) -> None:
    fetcher = _PostgrestFixture(_source_tables())

    result = _run(tmp_path.resolve(), fetcher)

    assert result.manifest_path == tmp_path / "run-fixture-001" / "manifest.json"
    assert {item.table for item in result.acquisitions} == set(
        SEAD_LINKED_SOURCE_TABLES
    )
    assert len(result.acquisitions) == 19
    assert result.country_reconciliation["counts"] == {
        "SE": 1,
        "DK": 1,
        "NO": 1,
        "FI": 1,
        "UNASSIGNED": 0,
    }
    assert result.country_reconciliation["bbox_row_count"] == 5
    assert result.country_reconciliation["scope_excluded_site_ids"] == [5]

    by_table = {item.table: item for item in result.acquisitions}
    assert [row["site_uuid"] for row in by_table["tbl_sites"].rows] == [
        "uuid-1",
        "uuid-2",
        "uuid-3",
        "uuid-4",
    ]
    assert [row["sample_group_id"] for row in by_table["tbl_sample_groups"].rows] == [
        11,
        12,
        13,
    ]
    assert by_table["tbl_sample_groups"].receipt["query_count"] == 2
    for acquisition in result.acquisitions:
        assert acquisition.receipt["status"] == "complete"
        assert acquisition.receipt["scope_id"] == "nordic-fixture-v1"
        assert acquisition.receipt["run_id"] == "run-fixture-001"
        assert acquisition.receipt["parent_run_id"] == "parent-fixture-001"
        assert acquisition.receipt["build_id"] == "build-fixture-001"
        assert acquisition.receipt["content_sha256"]
        assert acquisition.receipt["canonical_schema_sha256"]

    sample_group_join = next(
        item
        for item in result.join_reconciliations
        if item["edge"] == "sites.sample_groups"
    )
    assert sample_group_join["status"] == "complete"
    assert sample_group_join["zero_child_parent_ids"] == ["4"]
    assert sample_group_join["zero_child_parent_count"] == 1
    assert all(item["status"] == "complete" for item in result.join_reconciliations)

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "complete"
    assert manifest["required_tables"] == sorted(SEAD_LINKED_SOURCE_TABLES)
    assert len(manifest["files"]) == 40
    site_payload = json.loads(
        (result.manifest_path.parent / "payloads" / "tbl_sites.json").read_text(
            encoding="utf-8"
        )
    )
    assert [row["site_uuid"] for row in site_payload["rows"]] == [
        "uuid-1",
        "uuid-2",
        "uuid-3",
        "uuid-4",
    ]

    repeated = _run(tmp_path.resolve(), _PostgrestFixture(_source_tables()))
    assert repeated.manifest_path.read_bytes() == result.manifest_path.read_bytes()


def test_scoped_acquisition_rejects_a_source_that_ignores_dependency_filter(
    tmp_path: Path,
) -> None:
    fetcher = _PostgrestFixture(
        _source_tables(), ignore_filter_table="tbl_sample_groups"
    )

    with pytest.raises(ValueError, match="ignored dependency filter"):
        _run(tmp_path.resolve(), fetcher)

    assert not (tmp_path / "run-fixture-001").exists()


def test_scoped_acquisition_refuses_an_unresolved_lookup_reference(
    tmp_path: Path,
) -> None:
    tables = deepcopy(_source_tables())
    tables["tbl_age_types"] = []

    with pytest.raises(ValueError, match="age_types.analysis_dating_ranges"):
        _run(tmp_path.resolve(), _PostgrestFixture(tables))

    assert not (tmp_path / "run-fixture-001").exists()


def test_scoped_acquisition_refuses_unproven_page_completion(tmp_path: Path) -> None:
    fetcher = _PostgrestFixture(
        _source_tables(), never_finish_table="tbl_sample_groups"
    )

    with pytest.raises(SeadAcquisitionError) as exc_info:
        _run(
            tmp_path.resolve(),
            fetcher,
            id_batch_size=10,
            page_size=3,
            max_pages=2,
        )

    assert exc_info.value.result.table == "tbl_sample_groups"
    assert exc_info.value.result.receipt["status"] == "partial"
    assert exc_info.value.result.receipt["failure_reason"] == "page_limit_exceeded"
    assert not (tmp_path / "run-fixture-001").exists()


def test_scoped_acquisition_requires_an_explicit_disposition_for_every_bbox_site(
    tmp_path: Path,
) -> None:
    assignments = {1: "SE", 2: "DK", 3: "NO", 4: "FI"}

    with pytest.raises(ValueError, match="must exactly cover bbox sites"):
        _run(
            tmp_path.resolve(),
            _PostgrestFixture(_source_tables()),
            governed_country_by_site_id=assignments,
        )

    assert not (tmp_path / "run-fixture-001").exists()
