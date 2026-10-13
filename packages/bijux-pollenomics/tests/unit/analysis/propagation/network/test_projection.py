"""Production propagation projection contracts on explicitly constructed events."""

from __future__ import annotations

from dataclasses import replace
import json

import pytest

from bijux_pollenomics.analysis.propagation.network import (
    PhenomenonEvent,
    PropagationNetworkResult,
    generate_propagation_network,
)
from bijux_pollenomics.analysis.propagation.projection import (
    PropagationSelection,
    project_propagation_network,
)

from .support import event


def source_events() -> tuple[PhenomenonEvent, ...]:
    older = event(
        "older",
        country_code="NO",
        latitude=60,
        longitude=12,
        younger_bp=5600,
        older_bp=5600,
    )
    younger = event(
        "younger",
        country_code="SE",
        latitude=60.1,
        longitude=12.1,
        younger_bp=5500,
        older_bp=5500,
    )
    domestic = event(
        "domestic",
        country_code="SE",
        latitude=60.2,
        longitude=12.2,
        younger_bp=5550,
        older_bp=5550,
    )
    return older, younger, domestic


def network() -> PropagationNetworkResult:
    return generate_propagation_network(source_events())


@pytest.mark.parametrize(
    ("mode", "countries", "expected"),
    [
        ("all", ("SE",), 3),
        ("origin", ("NO",), 2),
        ("destination", ("NO",), 0),
        ("either_endpoint", ("NO",), 2),
        ("within_country", ("SE",), 1),
        ("cross_border", ("SE",), 2),
        ("cross_border", ("DK",), 0),
    ],
)
def test_country_filters_preserve_export_identity(
    mode: str, countries: tuple[str, ...], expected: int
) -> None:
    selection = PropagationSelection(country_mode=mode, countries=countries)  # type: ignore[arg-type]
    current = network()
    products = project_propagation_network(current, selection=selection)
    features = products["directed_candidates.geojson"]["features"]
    assert isinstance(features, list)
    assert len(features) == expected
    rows = current.scenario_results[0].directed_candidates
    actual = {feature["id"] for feature in features}
    events = {row.event_id: row for row in current.events}
    assert actual == {
        row.edge_id
        for row in rows
        if selection.matches(events[row.source_event_id], events[row.target_event_id])
    }
    for feature in features:
        row = next(row for row in rows if row.edge_id == feature["id"])
        assert all(
            feature["properties"][key] == value for key, value in row.as_dict().items()
        )
        assert feature["geometry"]["coordinates"] == [
            [
                events[row.source_event_id].longitude,
                events[row.source_event_id].latitude,
            ],
            [
                events[row.target_event_id].longitude,
                events[row.target_event_id].latitude,
            ],
        ]


def test_signal_empty_selection_and_feature_partitions() -> None:
    assert (
        project_propagation_network(
            network(), selection=PropagationSelection(signals=())
        )["directed_candidates.geojson"]["record_count"]
        == 0
    )
    assert (
        project_propagation_network(
            network(),
            selection=PropagationSelection(
                signals=(("ecological_role", "role:agriculture"),)
            ),
        )["directed_candidates.geojson"]["record_count"]
        == 0
    )


def test_union_deduplicates_only_identical_endpoint_sets_across_signals() -> None:
    older, younger, _ = source_events()
    events = []
    for feature in ("group:first", "group:second"):
        for original, observations in (
            (older, ("observation:a", "observation:b")),
            (younger, ("observation:c",)),
        ):
            events.append(
                replace(
                    original,
                    event_id="",
                    resolution="ecological_group",
                    feature_key=feature,
                    observation_ids=observations,
                )
            )
    # A subset is a distinct bundled relation; it cannot be silently merged.
    for original, observations in (
        (older, ("observation:a",)),
        (younger, ("observation:c",)),
    ):
        events.append(
            replace(
                original,
                event_id="",
                resolution="ecological_group",
                feature_key="group:subset",
                observation_ids=observations,
            )
        )
    result = project_propagation_network(generate_propagation_network(events))
    union = result["lower_level_edge_union.json"]
    assert union["feature_edge_count"] == 3
    assert union["endpoint_set_relation_count"] == 2
    assert union["whole_assemblage_network_constructed"] is False
    records = union["records"]
    assert isinstance(records, list)
    assert sorted(row["member_feature_edge_count"] for row in records) == [1, 2]
    assert all(
        row["source_site_id"] == older.site_id
        and row["target_site_id"] == younger.site_id
        for row in records
    )
    assert "Cartesian" in str(union["overlap_posture"])


def test_indeterminate_export_never_asserts_arrow() -> None:
    older, younger, _ = source_events()
    events = (
        replace(older, younger_bp=5500, older_bp=5600),
        replace(younger, younger_bp=5550, older_bp=5650),
    )
    result = project_propagation_network(generate_propagation_network(events))
    assert result["directed_candidates.geojson"]["record_count"] == 0
    indeterminate = result["indeterminate_pairs.geojson"]
    assert indeterminate["record_count"] == 2
    assert indeterminate["directional_arrow_allowed"] is False
    features = indeterminate["features"]
    assert isinstance(features, list)
    assert all(
        feature["properties"]["directional_arrow_allowed"] is False
        for feature in features
    )


def test_projection_is_content_deterministic_and_keeps_zero_distance() -> None:
    older, younger, _ = source_events()
    colocated = replace(younger, latitude=older.latitude, longitude=older.longitude)
    a = project_propagation_network(generate_propagation_network((older, colocated)))
    b = project_propagation_network(
        generate_propagation_network((colocated, older, older))
    )
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    features = a["directed_candidates.geojson"]["features"]
    assert isinstance(features, list)
    assert features[0]["properties"]["shared_location"] is True
    assert features[0]["properties"]["distance_km_unrounded"] == 0


def test_projection_rejects_stale_manifest_or_arrow_forgery() -> None:
    current = network()
    with pytest.raises(ValueError, match="manifest"):
        project_propagation_network(replace(current, event_manifest_digest="0" * 64))
    scenario = current.scenario_results[0]
    forged = replace(
        scenario,
        evaluated_pairs=tuple(
            replace(row, directional_arrow_allowed=False)
            for row in scenario.evaluated_pairs
        ),
    )
    with pytest.raises(ValueError, match="arrow"):
        project_propagation_network(replace(current, scenario_results=(forged,)))


@pytest.mark.parametrize(
    "selection",
    [
        {"country_mode": "unknown"},
        {"countries": ("XX",)},
        {"signals": (("taxon", "group:wrong"),)},
        {"scenario_id": ""},
    ],
)
def test_selection_rejects_unknown_identity(selection: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        PropagationSelection(**selection)  # type: ignore[arg-type]
