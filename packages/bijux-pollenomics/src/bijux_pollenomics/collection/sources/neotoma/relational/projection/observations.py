"""Long-form Neotoma observation relational projection."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import copy

from ......core.text import clean_optional_text
from ..diagnostics import add_orphan, register_record
from ..identifiers import digest
from ..state import RelationalBuildState
from ..variables import register_variable, unit_family, variable_id


def project_observations(
    state: RelationalBuildState,
    *,
    sample: Mapping[str, object],
    sample_source_id: str,
    sample_id: str,
    dataset_id: str,
    unit_id: str,
    site_id: str,
    country_code: str,
) -> None:
    datum_rows = sample.get("datum")
    if not isinstance(datum_rows, list):
        datum_rows = []
    state.source_counts["observation_rows"] += len(datum_rows)
    state.country_counts[country_code]["observation_rows"] += len(datum_rows)
    occurrence_counts: Counter[str] = Counter()
    for datum in datum_rows:
        if not isinstance(datum, Mapping):
            add_orphan(state.orphans, "sample", sample_id, "invalid_observation_row")
            continue
        datum_payload = copy.deepcopy(dict(datum))
        datum_digest = digest(datum_payload)
        occurrence_counts[datum_digest] += 1
        observation_id = (
            f"neotoma:observation:{sample_source_id}:"
            f"{datum_digest[:20]}:{occurrence_counts[datum_digest]}"
        )
        source_variable_id = variable_id(datum)
        register_variable(
            state.tables["variables"],
            variable_id=source_variable_id,
            datum=datum,
            source_snapshot_id=state.source_snapshot_id,
            build_id=state.build_id,
            conflicts=state.conflicts,
        )
        source_unit = clean_optional_text(datum.get("units"))
        state.unit_counts[source_unit or "<missing>"] += 1
        register_record(
            state.tables["observations"],
            {
                "observation_id": observation_id,
                "sample_id": sample_id,
                "dataset_id": dataset_id,
                "collection_unit_id": unit_id,
                "site_id": site_id,
                "country_code": country_code,
                "variable_id": source_variable_id,
                "source_taxon_id": copy.deepcopy(datum.get("taxonid")),
                "source_reported_name": copy.deepcopy(datum.get("variablename")),
                "source_element": copy.deepcopy(datum.get("element")),
                "source_element_type": copy.deepcopy(datum.get("elementtype")),
                "source_ecological_group": copy.deepcopy(datum.get("ecologicalgroup")),
                "source_taxon_group": copy.deepcopy(datum.get("taxongroup")),
                "source_unit": copy.deepcopy(datum.get("units")),
                "unit_family": unit_family(source_unit),
                "aggregation_key": f"neotoma:exact-unit:{source_unit}"
                if source_unit
                else None,
                "source_value": copy.deepcopy(datum.get("value")),
                "detection_status": "reported_value",
                "source_denominator": None,
                "denominator_status": "not_provided_by_source",
                "source_context": copy.deepcopy(datum.get("context")),
                "source_payload": datum_payload,
                "source_snapshot_id": state.source_snapshot_id,
                "build_id": state.build_id,
            },
            id_field="observation_id",
            conflicts=state.conflicts,
            conflict_kind="observation_identity_conflict",
        )
