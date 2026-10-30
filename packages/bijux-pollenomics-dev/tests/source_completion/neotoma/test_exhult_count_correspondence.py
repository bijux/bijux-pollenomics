"""Controlled Exhult count comparisons without opening authentic inputs."""

from __future__ import annotations

from copy import deepcopy
import csv
import io
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.neotoma import (
    exhult_cells as cells,
)
from bijux_pollenomics_dev.source_completion.neotoma import (
    exhult_count_correspondence as producer,
)


def workbook(
    anchor: object = 1, values: tuple[object, ...] = (2, 0, 3)
) -> dict[str, Any]:
    return {
        "row_number": 2,
        "sample": anchor,
        "sample_type": 2,
        "age": -123.5,
        "age_type": 2,
        "features": [
            {"column": col + 3, "label": label, "value": value, "type": 2}
            for col, (label, value) in enumerate(
                zip(("Betula", "Ulmus", "Other"), values, strict=True)
            )
        ],
    }


def datum(label: str = "Betula", value: object = 2, **kwargs: object) -> dict[str, Any]:
    return {
        "variablename": label,
        "value": value,
        "units": "NISP",
        "taxonid": 100,
        "element": "pollen",
        "elementtype": "grain",
        **kwargs,
    }


def sample(anchor: object = 1, ident: int = 10) -> dict[str, Any]:
    return {
        "sampleid": ident,
        "depth": anchor,
        "datum": [datum()],
        "ages": [
            {
                "age": 555.2,
                "chronologyid": 20,
                "chronologyname": "Cal yr BP",
                "agetype": "Calibrated radiocarbon years BP",
                "ageolder": None,
                "ageyounger": None,
            }
        ],
    }


def test_explicit_counts_absence_and_denominators() -> None:
    row = workbook()
    source = sample()
    before = deepcopy((row, source))
    outputs, summary = cells.compare([row], [source])
    result = outputs[0]
    assert result["explicit_agreement"] == 1
    assert result["absent_source_workbook_zero"] == 1
    assert result["absent_source_workbook_positive"] == 1
    assert result["paired_workbook_mass"] == result["paired_native_nisp_mass"] == 2
    assert result["workbook_age"] == -123.5
    assert result["native_ages"] == [
        {
            "chronologyid": 20,
            "chronologyname": "Cal yr BP",
            "agetype": "Calibrated radiocarbon years BP",
        }
    ]
    assert summary["uniquely_paired_rows"] == 1
    assert (row, source) == before


def test_difference_is_sparse_and_mass_keeps_both_values() -> None:
    source = sample()
    source["datum"][0]["value"] = 7
    outputs, _ = cells.compare([workbook()], [source])
    result = outputs[0]
    assert result["explicit_difference"] == 1
    assert result["paired_workbook_mass"] == 2
    assert result["paired_native_nisp_mass"] == 7
    assert result["exceptions"][0]["native_datums"][0]["value"] == 7


@pytest.mark.parametrize("which", ["workbook", "native", "both"])
def test_duplicate_numeric_anchors_never_pair(which: str) -> None:
    rows, samples = [workbook()], [sample()]
    if which in {"workbook", "both"}:
        rows.append(deepcopy(rows[0]))
    if which in {"native", "both"}:
        samples.append(sample(1, 11))
    outputs, summary = cells.compare(rows, samples)
    assert summary["uniquely_paired_rows"] == 0
    assert summary["native_unpaired_rows"] == len(samples)
    assert all(row.get("explicit_agreement", 0) == 0 for row in outputs)
    assert all(not row.get("exceptions", []) for row in outputs)


def test_unmatched_populations_are_retained_without_count_copy() -> None:
    outputs, summary = cells.compare([workbook(2)], [sample(1)])
    assert [row["row_kind"] for row in outputs] == ["workbook", "native_unpaired"]
    assert outputs[0]["anchor_status"] == "unmatched_workbook_anchor"
    assert outputs[0]["unassessed_anchor"] == 3
    assert outputs[0]["exceptions"] == []
    assert outputs[1]["native_sample_ids"] == [10]
    assert summary["native_samples"] == summary["native_unpaired_rows"] == 1


@pytest.mark.parametrize("anchor,ctype", [(True, 4), ("1", 1), (None, 0)])
def test_non_numeric_cached_anchors_cannot_match_numeric_depth(
    anchor: object, ctype: int
) -> None:
    row = workbook(anchor)
    row["sample_type"] = ctype
    outputs, _ = cells.compare([row], [sample()])
    assert outputs[0]["anchor_status"] == "invalid_workbook_anchor"


def test_fractional_anchors_are_literal_and_do_not_imply_depth_units() -> None:
    outputs, _ = cells.compare([workbook(1.5)], [sample(1.5)])
    assert outputs[0]["anchor_status"] == "unique_numeric_anchor_concordance"
    assert outputs[0]["native_depth"] == 1.5


def test_duplicate_workbook_columns_all_excluded() -> None:
    row = workbook()
    row["features"][1]["label"] = "Betula"
    outputs, summary = cells.compare([row], [sample()])
    assert outputs[0]["duplicate_workbook_label"] == 2
    assert outputs[0]["explicit_agreement"] == 0
    assert summary["duplicate_workbook_columns_excluded"] == [
        {"column": 3, "label": "Betula"},
        {"column": 4, "label": "Betula"},
    ]
    assert all(
        item["status"] != "duplicate_workbook_label"
        for item in outputs[0]["exceptions"]
    )


@pytest.mark.parametrize("different_identity", [False, True])
def test_repeated_native_nisp_is_never_summed(different_identity: bool) -> None:
    source = sample()
    source["datum"].append(datum(taxonid=101 if different_identity else 100))
    outputs, _ = cells.compare([workbook()], [source])
    assert outputs[0]["ambiguous_source"] == 1
    assert outputs[0]["paired_native_nisp_mass"] == 0
    assert len(outputs[0]["exceptions"][0]["native_datums"]) == 2


def test_same_name_different_variables_across_samples_are_ambiguous() -> None:
    second = sample(2, 11)
    second["datum"][0]["taxonid"] = 101
    rows, summary = cells.compare([workbook(1), workbook(2)], [sample(), second])
    assert all(row["ambiguous_source"] == 1 for row in rows)
    assert summary["globally_ambiguous_native_nisp_labels"] == ["Betula"]
    assert all("variableid" not in source["datum"][0] for source in [sample(), second])
    assert [row["exceptions"][0]["native_datums"][0]["taxonid"] for row in rows] == [
        100,
        101,
    ]


def test_non_nisp_is_separate_and_cannot_supply_missing_count() -> None:
    source = sample()
    source["datum"].append(datum("Ulmus", 0, units="percent"))
    outputs, _ = cells.compare([workbook()], [source])
    assert outputs[0]["native_non_nisp_datums"] == 1
    assert outputs[0]["native_non_nisp_labels"] == ["Ulmus"]
    assert outputs[0]["absent_source_workbook_zero"] == 1


@pytest.mark.parametrize("value", [True, -1, 2.5, None, "2"])
def test_invalid_counts_never_become_grains(value: object) -> None:
    row = workbook(values=(value, 0, 3))
    outputs, _ = cells.compare([row], [sample()])
    assert outputs[0]["invalid_workbook_count"] == 1
    source = sample()
    source["datum"][0]["value"] = value
    outputs, _ = cells.compare([workbook()], [source])
    assert outputs[0]["invalid_source_nisp"] == 1


@pytest.mark.parametrize(
    "age_count,status",
    [
        (0, "missing"),
        (1, "single_claim_unqualified"),
        (2, "multiple_claims_unqualified"),
    ],
)
def test_age_claims_never_select_a_chronology(age_count: int, status: str) -> None:
    source = sample()
    source["ages"] *= age_count
    outputs, _ = cells.compare([workbook()], [source])
    assert outputs[0]["age_claim_status"] == status
    assert len(outputs[0]["native_ages"]) == age_count


def test_csv_serializes_literal_types_and_sparse_rows() -> None:
    outputs, _ = cells.compare([workbook()], [sample(), sample(8, 11)])
    restored = list(csv.DictReader(io.StringIO(producer.render_csv(outputs))))
    assert json.loads(restored[0]["workbook_age"]) == -123.5
    assert json.loads(restored[1]["native_sample_ids"]) == [11]
    assert restored[1]["workbook_row"] == ""


def test_raw_source_binding_refuses_changed_authority_before_payload(
    tmp_path: Path,
) -> None:
    target = tmp_path / producer.IDENTITIES
    target.parent.mkdir(parents=True)
    target.write_text(
        json.dumps({"source_files": {producer.RAW: {"bytes": 1, "sha256": "0" * 64}}})
    )
    with pytest.raises(ValueError, match="raw source authority"):
        producer.load_native(tmp_path)


def test_workbook_binding_refuses_foreign_member_before_decode(tmp_path: Path) -> None:
    (tmp_path / "manifest.json").write_text(
        json.dumps({"archive_sha256": "0" * 64, "members": []})
    )
    with pytest.raises(ValueError, match="workbook binding"):
        producer.load_workbook(tmp_path)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_refusals_are_valid_json_not_zero(value: float) -> None:
    outputs, _ = cells.compare([workbook(values=(value, 0, 3))], [sample()])
    assert outputs[0]["invalid_workbook_count"] == 1
    restored = list(csv.DictReader(io.StringIO(producer.render_csv(outputs))))
    exception = json.loads(restored[0]["exceptions"])[0]
    assert exception["workbook_value"] == {"nonfinite_float": repr(value)}


@pytest.mark.parametrize("name", [None, 12])
def test_missing_or_numeric_native_name_is_not_coerced_to_text(name: object) -> None:
    row = workbook()
    row["features"][0]["label"] = str(name)
    source = sample()
    source["datum"][0]["variablename"] = name
    outputs, _ = cells.compare([row], [source])
    assert outputs[0]["explicit_agreement"] == 0
    assert outputs[0]["native_invalid_label_datums"] == 1
    assert outputs[0]["absent_source_workbook_positive"] == 2


def raw_case() -> dict[str, Any]:
    return {
        "part_number": 8,
        "rows": [
            {
                "site": {
                    "siteid": 28868,
                    "dataset": {"datasetid": 53994},
                    "collectionunit": {
                        "collectionunitid": 39237,
                        "dataset": {
                            "datasetid": 53994,
                            "samples": [sample(), sample(2, 11)],
                        },
                    },
                }
            }
        ],
    }


def test_native_selection_keeps_all_samples_not_screen_denominator() -> None:
    source = raw_case()
    source["rows"].append({"site": {"dataset": {"datasetid": 123}}})
    selected = producer.select_samples(source)
    assert [row["sampleid"] for row in selected] == [10, 11]
    assert selected is source["rows"][0]["site"]["collectionunit"]["dataset"]["samples"]


@pytest.mark.parametrize(
    "field",
    ["part", "site", "unit", "dataset", "duplicate_dataset", "duplicate_sample"],
)
def test_native_selection_refuses_foreign_or_duplicate_identity(field: str) -> None:
    raw = raw_case()
    site = raw["rows"][0]["site"]
    if field == "part":
        raw["part_number"] = 9
    elif field == "site":
        site["siteid"] = 1
    elif field == "unit":
        site["collectionunit"]["collectionunitid"] = 1
    elif field == "dataset":
        site["collectionunit"]["dataset"]["datasetid"] = 1
    elif field == "duplicate_dataset":
        raw["rows"].append(deepcopy(raw["rows"][0]))
    else:
        site["collectionunit"]["dataset"]["samples"].append(sample())
    with pytest.raises(ValueError):
        producer.select_samples(raw)


class ControlledSheet:
    """Literal cached cells only; no workbook file or parser execution."""

    name = "Sheet1"
    nrows = 2
    ncols = 4
    merged_cells: list[tuple[int, int, int, int]] = []

    def __init__(self, header: str = "Sample age (cal AD/BC)") -> None:
        self.values: list[list[object]] = [
            ["Sample", header, "Betula", "Ulmus"],
            [1.5, -123.5, 2, ""],
        ]

    def cell(self, rowx: int, colx: int) -> Any:
        value = self.values[rowx][colx]
        return SimpleNamespace(
            value=value, ctype=2 if isinstance(value, (int, float)) else 1
        )


def test_cached_sheet_keeps_missing_text_distinct_from_zero_and_literal_age() -> None:
    rows = cells.workbook_rows(ControlledSheet())
    assert rows[0]["sample"] == 1.5
    assert rows[0]["age"] == -123.5
    assert rows[0]["features"][1] == {
        "column": 4,
        "label": "Ulmus",
        "value": "",
        "type": 1,
    }
    outputs, _ = cells.compare(rows, [sample(1.5)])
    assert outputs[0]["invalid_workbook_count"] == 1
    assert outputs[0]["absent_source_workbook_zero"] == 0


def test_other_age_header_cannot_inherit_declared_exhult_scope() -> None:
    with pytest.raises(ValueError, match="metadata headers"):
        cells.workbook_rows(ControlledSheet("Sample age (LANDCLIM)"))


def test_distinct_native_symmetry_is_not_merged_under_same_taxon_id() -> None:
    first, second = sample(), sample(2, 11)
    first["datum"][0]["symmetry"] = "radial"
    second["datum"][0]["symmetry"] = "bilateral"
    rows, _ = cells.compare([workbook(1), workbook(2)], [first, second])
    assert all(row["ambiguous_source"] == 1 for row in rows)


def test_many_absent_zeros_keep_counts_without_copying_cell_values() -> None:
    row = workbook()
    row["features"] = [
        {"column": i + 3, "label": f"Absent{i}", "value": 0, "type": 2}
        for i in range(202)
    ]
    outputs, summary = cells.compare([row], [sample()])
    assert outputs[0]["absent_source_workbook_zero"] == 202
    assert summary["cell_status_counts"]["absent_source_workbook_zero"] == 202
    assert outputs[0]["exceptions"] == []
    assert len(producer.render_csv(outputs)) < 1500


def test_duplicate_zero_columns_are_listed_once_not_per_row() -> None:
    rows = [workbook(1), workbook(2)]
    for row in rows:
        row["features"] = [
            {"column": col, "label": "Duplicate", "value": 0, "type": 2}
            for col in [3, 4]
        ]
    outputs, summary = cells.compare(rows, [sample(), sample(2, 11)])
    assert summary["cell_status_counts"]["duplicate_workbook_label"] == 4
    assert len(summary["duplicate_workbook_columns_excluded"]) == 2
    assert all(row["exceptions"] == [] for row in outputs)


@pytest.mark.parametrize("context", [None, {"datasetid": 123}])
def test_optional_site_dataset_context_cannot_redirect_actual_download(
    context: object,
) -> None:
    raw = raw_case()
    site = raw["rows"][0]["site"]
    if context is None:
        site.pop("dataset")
    else:
        site["dataset"] = context
    assert [row["sampleid"] for row in producer.select_samples(raw)] == [10, 11]
