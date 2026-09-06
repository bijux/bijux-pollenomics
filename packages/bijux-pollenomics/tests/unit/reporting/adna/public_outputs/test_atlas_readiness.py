"""Unit-safe denominator tests for animal atlas readiness."""

from __future__ import annotations

import copy

import pytest

from bijux_pollenomics.reporting.adna.public_outputs import atlas_readiness
from bijux_pollenomics.reporting.adna.public_outputs.atlas_readiness import (
    _atlas_readiness_status,
    _build_animal_atlas_readiness,
    _required_count,
    _share,
)
from bijux_pollenomics.reporting.adna.public_outputs.rendering import (
    _format_nullable_share,
    _render_animal_atlas_readiness_markdown,
)
from tests.support.repository import REPOSITORY_ROOT


def test_atlas_readiness_never_combines_sample_and_site_denominators() -> None:
    payload = _build_animal_atlas_readiness(REPOSITORY_ROOT / "data", [])

    assert payload["schema_version"] == "animal-atlas-readiness.v2"
    rows = payload["rows"]
    assert isinstance(rows, list)
    assert rows
    assert payload["reconciled_denominators"] == {
        "coordinate_provenance": {
            "denominator": 289,
            "mappable": 285,
            "refused": 4,
        },
        "publication": {
            "denominator": 285,
            "published": 151,
            "not_materialized": 134,
        },
        "samples": {
            "denominator": 1450,
            "mapped": 288,
            "blocked": 1162,
            "unresolved_subset_of_blocked": 90,
        },
    }
    for row in rows:
        assert isinstance(row, dict)
        assert row["tracked_sample_count"] == (
            row["mapped_sample_count"] + row["blocked_sample_count"]
        )
        assert row["coordinate_provenance_denominator"] == (
            row["coordinate_mappable_provenance_count"]
            + row["coordinate_refused_provenance_count"]
        )
        assert "total_curated_rows" not in row
        assert "map_ready_share" not in row


def test_undefined_shares_remain_null_and_render_as_not_applicable() -> None:
    assert _share(0, 0) is None
    assert _format_nullable_share(None) == "N/A"
    for numerator, denominator in ((1, 0), (2, 1), (-1, 1), (0, -1)):
        try:
            _share(numerator, denominator)
        except ValueError:
            continue
        raise AssertionError(
            f"invalid readiness share was accepted: {numerator}/{denominator}"
        )


def test_required_readiness_counts_fail_closed() -> None:
    for value in (None, "", "0", -1, False):
        try:
            _required_count({"count": value}, "count")
        except ValueError:
            continue
        raise AssertionError(f"invalid readiness count was accepted: {value!r}")


def test_zero_candidate_status_names_each_blocking_population() -> None:
    sample_status = _atlas_readiness_status(
        candidate_point_count=0,
        mapped_sample_count=0,
        blocked_sample_count=3,
        unresolved_count=0,
        refused_count=0,
    )
    coordinate_status = _atlas_readiness_status(
        candidate_point_count=0,
        mapped_sample_count=0,
        blocked_sample_count=0,
        unresolved_count=0,
        refused_count=2,
    )

    assert sample_status[0] == "blocked"
    assert "3 blocked sample rows" in sample_status[1]
    assert coordinate_status[0] == "blocked"
    assert "2 refused coordinate-provenance rows" in coordinate_status[1]


def test_readiness_markdown_keeps_a_rectangular_table() -> None:
    markdown = _render_animal_atlas_readiness_markdown(
        {"status_counts": {}, "rows": []}
    )
    table_lines = [line for line in markdown.splitlines() if line.startswith("|")]

    assert len(table_lines) == 3
    assert {line.count("|") for line in table_lines} == {13}


def _valid_accounting_payloads() -> tuple[dict[str, object], dict[str, object]]:
    readiness = {
        "rows": [
            {
                "species_latin_name": "Ovis aries",
                "species_common_name": "sheep",
                "direct_coordinate_backed": 1,
                "indirectly_geocoded": 1,
                "coordinate_provenance_mappable_count": 2,
                "refused_coordinate_provenance_count": 1,
                "region_only_coordinate_refusal_count": 1,
                "unresolved_location_coordinate_refusal_count": 0,
                "publication_candidate_count": 1,
                "not_materialized_count": 1,
                "unresolved_sample_count": 1,
            }
        ],
        "totals": {
            "coordinate_provenance_row_count": 3,
            "direct_coordinate_backed": 1,
            "indirectly_geocoded": 1,
            "coordinate_provenance_mappable_count": 2,
            "refused_coordinate_provenance_count": 1,
            "region_only_coordinate_refusal_count": 1,
            "unresolved_location_coordinate_refusal_count": 0,
            "publication_candidate_count": 1,
            "not_materialized_count": 1,
            "unresolved_sample_count": 1,
        },
    }
    honesty = {
        "rows": [
            {
                "species_latin_name": "Ovis aries",
                "tracked_sample_count": 2,
                "mapped_sample_count": 1,
                "blocked_sample_count": 1,
                "unresolved_sample_count": 1,
            }
        ],
        "totals": {
            "tracked_sample_count": 2,
            "mapped_sample_count": 1,
            "blocked_sample_count": 1,
            "unresolved_sample_count": 1,
        },
    }
    return readiness, honesty


def _build_stubbed_readiness(
    monkeypatch: pytest.MonkeyPatch,
    readiness: dict[str, object],
    honesty: dict[str, object],
    *,
    candidate_count: int = 1,
) -> dict[str, object]:
    monkeypatch.setattr(
        atlas_readiness,
        "build_cross_species_map_readiness",
        lambda _data_root: readiness,
    )
    monkeypatch.setattr(
        atlas_readiness,
        "build_public_animal_output_honesty",
        lambda _data_root, _report_root: honesty,
    )
    monkeypatch.setattr(
        atlas_readiness,
        "_mapped_sample_ids_by_species",
        lambda _data_root: {"Ovis aries": {"sample-1"}},
    )
    monkeypatch.setattr(
        atlas_readiness,
        "_candidate_rows_by_species",
        lambda _data_root: {"Ovis aries": [object()] * candidate_count},
    )
    return _build_animal_atlas_readiness(REPOSITORY_ROOT / "data", [])


def test_readiness_equations_fail_closed_under_payload_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    readiness, honesty = _valid_accounting_payloads()
    assert _build_stubbed_readiness(monkeypatch, readiness, honesty)[
        "reconciled_denominators"
    ]

    mutations = (
        (
            "coordinate total",
            "readiness",
            "totals",
            "coordinate_provenance_row_count",
            4,
        ),
        ("direct total", "readiness", "totals", "direct_coordinate_backed", 0),
        ("indirect row", "readiness", "rows", "indirectly_geocoded", 0),
        (
            "region refusal total",
            "readiness",
            "totals",
            "region_only_coordinate_refusal_count",
            0,
        ),
        (
            "unresolved location row",
            "readiness",
            "rows",
            "unresolved_location_coordinate_refusal_count",
            1,
        ),
        (
            "readiness unresolved total",
            "readiness",
            "totals",
            "unresolved_sample_count",
            0,
        ),
        ("publication total", "readiness", "totals", "not_materialized_count", 2),
        ("species publication", "readiness", "rows", "not_materialized_count", 2),
        ("mapped samples", "honesty", "rows", "mapped_sample_count", 0),
        ("unresolved samples", "honesty", "rows", "unresolved_sample_count", 0),
        ("sample totals", "honesty", "totals", "tracked_sample_count", 3),
    )
    for _label, target, container, field, value in mutations:
        mutated_readiness = copy.deepcopy(readiness)
        mutated_honesty = copy.deepcopy(honesty)
        payload = mutated_readiness if target == "readiness" else mutated_honesty
        section = payload[container]
        if isinstance(section, list):
            section[0][field] = value
        else:
            section[field] = value
        with pytest.raises(ValueError, match="reconcile"):
            _build_stubbed_readiness(
                monkeypatch,
                mutated_readiness,
                mutated_honesty,
            )

    with pytest.raises(ValueError, match="publication candidates"):
        _build_stubbed_readiness(
            monkeypatch,
            readiness,
            honesty,
            candidate_count=2,
        )


@pytest.mark.parametrize(
    ("container", "field"),
    [
        ("rows", "direct_coordinate_backed"),
        ("rows", "indirectly_geocoded"),
        ("rows", "region_only_coordinate_refusal_count"),
        ("rows", "unresolved_location_coordinate_refusal_count"),
        ("totals", "direct_coordinate_backed"),
        ("totals", "indirectly_geocoded"),
        ("totals", "region_only_coordinate_refusal_count"),
        ("totals", "unresolved_location_coordinate_refusal_count"),
        ("totals", "unresolved_sample_count"),
    ],
)
def test_readiness_posture_counts_refuse_negative_values(
    monkeypatch: pytest.MonkeyPatch,
    container: str,
    field: str,
) -> None:
    readiness, honesty = _valid_accounting_payloads()
    section = readiness[container]
    if isinstance(section, list):
        section[0][field] = -1
    else:
        section[field] = -1

    with pytest.raises(ValueError, match="nonnegative"):
        _build_stubbed_readiness(monkeypatch, readiness, honesty)
