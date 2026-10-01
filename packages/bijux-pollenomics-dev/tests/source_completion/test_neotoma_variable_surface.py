"""Native Neotoma taxon keys remain distinct from reviewed taxonomic choices."""

from __future__ import annotations

import copy

from bijux_pollenomics_dev.source_completion.neotoma_variable_surface import (
    reconcile,
)


def _datum() -> dict[str, object]:
    return {
        "taxonid": 309,
        "variablename": "Typha latifolia",
        "taxongroup": "Vascular plants",
        "ecologicalgroup": "AQVP",
        "element": "pollen",
        "elementtype": "pollen",
        "units": "NISP",
        "value": 1,
    }


def _variable() -> dict[str, object]:
    return {
        "variable_id": "neotoma:variable:309",
        "source_taxon_id": 309,
        "source_reported_name": "Typha latifolia",
        "source_semantics": [
            {
                "source_taxon_group": "Vascular plants",
                "source_ecological_group": "AQVP",
                "source_element": "pollen",
                "source_element_type": "pollen",
            }
        ],
        "source_units": ["NISP"],
    }


def test_native_variable_attributes_and_source_nulls_are_exact() -> None:
    datum = _datum()
    variable = _variable()
    result = reconcile([datum], [variable], [])
    assert result["match"]
    assert result["native_datum_rows"] == 1
    assert result["native_variable_count"] == 1
    assert result["source_taxon_group_datum_counts"] == {"Vascular plants": 1}

    changed = copy.deepcopy(variable)
    changed["source_semantics"][0]["source_taxon_group"] = None
    mismatch = reconcile([datum], [changed], [])
    assert not mismatch["match"]
    assert mismatch["attribute_mismatches"] == [
        {"variable_id": "neotoma:variable:309", "fields": ["source_semantics"]}
    ]


def test_name_variant_requires_a_real_identity_conflict() -> None:
    datum = _datum()
    alternate = {**datum, "variablename": "Typha cf. latifolia", "value": 2}
    without_ledger = reconcile([datum, alternate], [_variable()], [])
    assert not without_ledger["match"]
    assert without_ledger["name_variant_variable_ids"] == ["neotoma:variable:309"]
    assert without_ledger["missing_identity_conflict_rows"] == [
        {
            "variable_id": "neotoma:variable:309",
            "incoming_identity": {"taxon_id": 309, "name": "Typha cf. latifolia"},
        }
    ]

    ledger = [
        {
            "conflict_kind": "variable_identity_conflict",
            "subject_id": "neotoma:variable:309",
            "detail": {
                "existing_taxon_id": 309,
                "incoming_taxon_id": 309,
                "existing_name": "Typha latifolia",
                "incoming_name": "Typha cf. latifolia",
            },
        }
    ]
    assert reconcile([datum, alternate], [_variable()], ledger)["match"]


def test_unidentified_taxon_is_retained_as_an_explicit_native_key() -> None:
    datum = {**_datum(), "taxonid": None, "variablename": "unknown type"}
    from bijux_pollenomics.collection.sources.neotoma.relational.variables import (
        variable_id,
    )

    variable = {
        **_variable(),
        "variable_id": variable_id(datum),
        "source_taxon_id": None,
        "source_reported_name": "unknown type",
    }
    result = reconcile([datum], [variable], [])
    assert result["match"]
    assert result["unidentified_taxon_variable_ids"] == [variable_id(datum)]
