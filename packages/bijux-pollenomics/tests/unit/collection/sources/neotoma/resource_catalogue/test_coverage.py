"""Coverage joins each declared native resource/version once without epoch promotion."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    build_neotoma_resource_catalogue,
)


@pytest.mark.parametrize(
    ("chronologies", "raw_total", "available_rows", "records", "states"),
    [
        ([], 0, 0, 0, {}),
        (None, None, 0, 0, {"parent_unavailable": 1}),
        ([{"chronology": {"chroncontrols": None}}], None, 0, 0, {"null": 1}),
        ([{"chronology": {}}], None, 0, 0, {"missing": 1}),
        ([{"chronology": {"chroncontrols": {}}}], None, 0, 0, {"malformed": 1}),
        ([{"chronology": None}], None, 0, 0, {"unavailable_wrapper": 1}),
        ([None], None, 0, 0, {"unavailable_wrapper": 1}),
        (
            [{"chronology": {"chroncontrols": [None, {"chroncontrolid": 11}]}}],
            2,
            2,
            1,
            {"array": 1},
        ),
        (
            [
                {"chronology": {"chroncontrols": [{"chroncontrolid": 11}]}},
                {"chronology": {"chroncontrols": None}},
            ],
            None,
            1,
            1,
            {"array": 1, "null": 1},
        ),
    ],
)
def test_control_population_counts_preserve_unavailable_and_literal_rows(
    catalogue_sources: Callable[..., dict[str, Any]],
    chronologies: object,
    raw_total: int | None,
    available_rows: int,
    records: int,
    states: dict[str, int],
) -> None:
    inputs = catalogue_sources(chronology_metadata=chronologies)
    catalogue = build_neotoma_resource_catalogue(**inputs)
    resource = next(row for row in catalogue["resources"] if row["dataset_id"] == 201)
    current = resource["versions"]["current"]
    assert current["acquisition_status"] == "parsed_native"
    counts = current["native_counts"]
    assert counts["raw_chroncontrol_rows"] == raw_total
    assert counts["available_chroncontrol_rows"] == available_rows
    assert counts["chroncontrol_record_rows"] == records
    assert counts["chroncontrol_nonrecord_rows"] == available_rows - records
    assert counts["chroncontrol_population_states"] == states
    assert counts["chroncontrol_collections_available"] is (raw_total is not None)
    assert counts["dated_measurements"] is None
    assert resource["method_capability"]["scientific_admission"] == "not_asserted"


def test_missing_datum_population_is_unavailable_while_empty_array_is_zero(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    catalogue = build_neotoma_resource_catalogue(
        **catalogue_sources(
            sample_metadata=[{"sampleid": 41}, {"sampleid": 42, "datum": []}]
        )
    )
    resource = next(row for row in catalogue["resources"] if row["dataset_id"] == 201)
    current = resource["versions"]["current"]
    assert current["acquisition_status"] == "parsed_native"
    counts = current["native_counts"]
    assert counts["raw_sample_rows"] == 2
    assert counts["raw_datum_rows"] is None
    assert counts["available_datum_rows"] == 0
    assert counts["datum_population_states"] == {"array": 1, "missing": 1}


def test_resource_version_partition_preserves_roles_epochs_and_null_native_rows(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    catalogue = build_neotoma_resource_catalogue(**catalogue_sources())
    assert catalogue["summary"]["resource_count"] == 4
    assert catalogue["summary"]["version_status_count"] == 8
    assert catalogue["summary"]["acquisition_partition_complete"] is True
    rows = {row["dataset_id"]: row for row in catalogue["resources"]}
    assert rows[201]["versions"]["current"]["acquisition_status"] == "parsed_native"
    assert (
        rows[201]["versions"]["doi_frozen"]["qualification_status"]
        == "parsed_frozen_native"
    )
    assert (
        rows[201]["versions"]["doi_frozen"]["source_terminal_status"]
        == "unresolved_frozen_schema"
    )
    assert (
        rows[203]["versions"]["current"]["acquisition_status"]
        == "not_attempted_exposure_role"
    )
    assert rows[204]["exposure_role"] == "heldout_no_numerical_access"
    assert rows[202]["versions"]["current"]["native_counts"]["raw_sample_rows"] == 1
    assert rows[202]["versions"]["current"]["native_counts"]["raw_datum_rows"] == 1
    assert (
        rows[202]["versions"]["current"]["native_counts"]["datum_rows_with_values"] == 0
    )
    assert (
        rows[202]["versions"]["current"]["native_counts"]["dated_measurements"] is None
    )
    assert rows[202]["method_capability"]["independent_lra_accuracy"] is False
    assert len(catalogue["sites"]) == 3
    assert catalogue["countries"]["SE"]["site_count"] == 3
    assert (
        catalogue["countries"]["SE"]["resource_role_counts"][
            "reserved_candidate_confirmation"
        ]
        == 1
    )
    assert rows[201]["rights"]["constituent_database"] is None
    assert rows[201]["original_epoch"]["status"] == "not_supplied"


def test_partial_capture_is_a_complete_status_partition_with_explicit_pending_slots(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    catalogue = build_neotoma_resource_catalogue(
        **catalogue_sources(capture_resources=False)
    )
    assert catalogue["summary"]["version_status_count"] == 8
    assert catalogue["summary"]["acquisition_partition_complete"] is False
    row = catalogue["resources"][0]
    assert (
        row["versions"]["current"]["acquisition_status"]
        == "not_attempted_pending_capture"
    )
    assert (
        catalogue["summary"]["version_status_counts"]["not_attempted_exposure_role"]
        == 4
    )


def test_unknown_native_type_retains_explicit_unsupported_capability(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    catalogue = build_neotoma_resource_catalogue(
        **catalogue_sources(auxiliary_type="unregistered source proxy")
    )
    row = next(row for row in catalogue["resources"] if row["dataset_id"] == 202)
    assert row["method_capability"]["status"] == "unsupported_dataset_type"
    assert (
        row["versions"]["current"]["acquisition_status"] == "unsupported_dataset_type"
    )
    assert row["versions"]["current"]["native_counts"] is None


def test_duplicate_selected_resource_roots_are_not_implicitly_deduplicated(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    inputs = catalogue_sources()
    sources = inputs["resource_captures"]
    root = next(iter(sources.values()))
    manifest = root / "capture-manifest.json"
    document = json.loads(manifest.read_bytes())
    document["capture_utc_end"] = document["capture_utc_end"].replace("+00:00", "Z")
    sibling = root.parent / "sibling"
    sibling.mkdir()
    for path in root.iterdir():
        (sibling / path.name).write_bytes(path.read_bytes())
    (sibling / manifest.name).write_text(json.dumps(document))
    sources[sha256((sibling / manifest.name).read_bytes()).hexdigest()] = sibling
    with pytest.raises(ValueError, match="duplicate|ambiguous|Duplicate|Ambiguous"):
        build_neotoma_resource_catalogue(**inputs)


def test_blocked_resource_has_no_invented_response_epoch(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    catalogue = build_neotoma_resource_catalogue(**catalogue_sources())
    row = next(row for row in catalogue["resources"] if row["dataset_id"] == 204)
    assert row["versions"]["doi_frozen"]["source"]["epoch_kind"] == "not_acquired"


def test_selected_reuse_root_does_not_recount_its_probe_ancestor(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
        NeotomaResourcePlan,
        NeotomaResourceSpec,
        capture_neotoma_resources,
    )

    inputs = catalogue_sources()
    digest, original = next(iter(inputs["resource_captures"].items()))
    control = json.loads((original / "request-plan.json").read_bytes())
    specifications = tuple(
        NeotomaResourceSpec(**{**row, "versions": tuple(row["versions"])})
        for row in control["plan"]["resources"]
    )
    reused_root = original.parent / "reused"
    result = capture_neotoma_resources(
        reused_root,
        plan=NeotomaResourcePlan(specifications, inputs["expected_roster_sha256"]),
        reuse_from={digest: original},
        fetch=lambda *_a, **_k: pytest.fail("catalogue ancestor refetched"),
    )
    inputs["resource_captures"] = {result.manifest_sha256: reused_root}
    inputs["source_captures"] = {digest: original}
    catalogue = build_neotoma_resource_catalogue(**inputs)
    assert (
        catalogue["summary"]["resource_count"] == 4
        and catalogue["summary"]["version_status_count"] == 8
    )
    assert catalogue["selected_resource_capture_manifest_sha256"] == [
        result.manifest_sha256
    ]
    row = catalogue["resources"][0]
    assert row["versions"]["current"]["source"]["capture_manifest_sha256"] == digest
    assert row["versions"]["doi_frozen"]["source"]["capture_manifest_sha256"] == digest


def test_large_exact_native_integer_is_counted_without_float_conversion(
    catalogue_sources: Callable[..., dict[str, Any]],
) -> None:
    catalogue = build_neotoma_resource_catalogue(
        **catalogue_sources(large_integer=True)
    )
    row = catalogue["resources"][0]
    assert row["versions"]["current"]["native_counts"]["numeric_value_rows"] == 1
    assert row["versions"]["doi_frozen"]["native_counts"]["numeric_value_rows"] == 1
