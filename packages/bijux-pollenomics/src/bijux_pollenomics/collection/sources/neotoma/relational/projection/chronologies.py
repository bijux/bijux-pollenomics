"""Chronology model and control relational projection."""

from __future__ import annotations

from collections.abc import Mapping
import copy

from ..diagnostics import add_orphan, conflict_record, register_record
from ..identifiers import digest, optional_source_id
from ..source_payloads import copy_source_payload_excluding
from ..state import RelationalBuildState


def project_chronologies(
    state: RelationalBuildState,
    *,
    unit: Mapping[str, object],
    unit_source_id: str,
    unit_id: str,
    dataset_id: str,
    site_id: str,
    country_code: str,
) -> tuple[str | None, dict[str, str]]:
    default_source_id = optional_source_id(unit.get("defaultchronology"))
    chronology_ids_by_source: dict[str, str] = {}
    flagged_default_ids: list[str] = []
    chronologies = unit.get("chronologies")
    if not isinstance(chronologies, list):
        chronologies = []
    state.source_counts["chronology_rows"] += len(chronologies)
    for wrapper in chronologies:
        if not isinstance(wrapper, Mapping):
            add_orphan(
                state.orphans, "collection_unit", unit_id, "invalid_chronology_row"
            )
            continue
        chronology = wrapper.get("chronology")
        if not isinstance(chronology, Mapping):
            add_orphan(
                state.orphans,
                "collection_unit",
                unit_id,
                "missing_chronology_payload",
            )
            continue
        chronology_source_id = optional_source_id(chronology.get("chronologyid"))
        if chronology_source_id is None:
            add_orphan(
                state.orphans,
                "chronology",
                unit_id,
                "missing_source_identifier",
                source_value=chronology.get("chronologyid"),
            )
            chronology_key = f"unidentified:{digest(dict(chronology))[:20]}"
        else:
            chronology_key = chronology_source_id
        chronology_id = f"neotoma:chronology:{unit_source_id}:{chronology_key}"
        if chronology_source_id is not None:
            chronology_ids_by_source[chronology_source_id] = chronology_id
        chronology_metadata = chronology.get("chronology")
        if not isinstance(chronology_metadata, Mapping):
            chronology_metadata = {}
        source_is_default = chronology_metadata.get("isdefault") is True
        if source_is_default and chronology_source_id is not None:
            flagged_default_ids.append(chronology_source_id)
        register_record(
            state.tables["chronologies"],
            {
                "chronology_id": chronology_id,
                "source_chronology_id": chronology.get("chronologyid"),
                "collection_unit_id": unit_id,
                "site_id": site_id,
                "country_code": country_code,
                "selected_by_collection_unit_reference": (
                    chronology_source_id == default_source_id
                ),
                "source_is_default_assertion": source_is_default,
                "source_payload": copy_source_payload_excluding(
                    chronology, "chroncontrols"
                ),
                "source_snapshot_id": state.source_snapshot_id,
                "build_id": state.build_id,
            },
            id_field="chronology_id",
            conflicts=state.conflicts,
            conflict_kind="chronology_payload_conflict",
        )
        project_chronology_controls(
            state,
            chronology=chronology,
            chronology_id=chronology_id,
            unit_id=unit_id,
            site_id=site_id,
            country_code=country_code,
        )

    expected_flags = [default_source_id] if default_source_id is not None else []
    if sorted(flagged_default_ids) != expected_flags:
        state.conflicts.append(
            conflict_record(
                "default_chronology_assertions_conflict",
                dataset_id,
                {
                    "collection_unit_id": unit_id,
                    "explicit_default_chronology_id": (
                        f"neotoma:chronology:{unit_source_id}:{default_source_id}"
                        if default_source_id is not None
                        else None
                    ),
                    "source_flagged_default_chronology_ids": [
                        f"neotoma:chronology:{unit_source_id}:{source_id}"
                        for source_id in sorted(flagged_default_ids)
                    ],
                    "governing_selection": "collection_unit.defaultchronology",
                },
            )
        )
    if (
        default_source_id is not None
        and default_source_id not in chronology_ids_by_source
    ):
        add_orphan(
            state.orphans,
            "collection_unit",
            unit_id,
            "default_chronology_not_found",
            source_value=unit.get("defaultchronology"),
        )
    return default_source_id, chronology_ids_by_source


def project_chronology_controls(
    state: RelationalBuildState,
    *,
    chronology: Mapping[str, object],
    chronology_id: str,
    unit_id: str,
    site_id: str,
    country_code: str,
) -> None:
    controls = chronology.get("chroncontrols")
    if not isinstance(controls, list):
        controls = []
    state.source_counts["chronology_control_rows"] += len(controls)
    for control in controls:
        if not isinstance(control, Mapping):
            add_orphan(
                state.orphans,
                "chronology",
                chronology_id,
                "invalid_chronology_control_row",
            )
            continue
        control_source_id = optional_source_id(control.get("chroncontrolid"))
        if control_source_id is None:
            add_orphan(
                state.orphans,
                "chronology_control",
                chronology_id,
                "missing_source_identifier",
                source_value=control.get("chroncontrolid"),
            )
            control_key = f"unidentified:{digest(dict(control))[:20]}"
        else:
            control_key = control_source_id
        control_id = f"{chronology_id}:control:{control_key}"
        register_record(
            state.tables["chronology_controls"],
            {
                "chronology_control_id": control_id,
                "source_chronology_control_id": control.get("chroncontrolid"),
                "chronology_id": chronology_id,
                "collection_unit_id": unit_id,
                "site_id": site_id,
                "country_code": country_code,
                "source_payload": copy.deepcopy(dict(control)),
                "source_snapshot_id": state.source_snapshot_id,
                "build_id": state.build_id,
            },
            id_field="chronology_control_id",
            conflicts=state.conflicts,
            conflict_kind="chronology_control_payload_conflict",
        )
