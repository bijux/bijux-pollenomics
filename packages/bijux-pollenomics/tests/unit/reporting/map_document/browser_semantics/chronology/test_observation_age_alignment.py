"""Display-only observation ages reuse source qualification and explicit choices."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.reporting.map_document import template

from ..support import check_javascript_syntax, run_node_json, template_block
from .test_age_depth_diagram import decoded, projected_tabs, set_claim, set_sample


def required_element(tree: ET.Element, path: str) -> ET.Element:
    element = tree.find(path)
    assert element is not None, path
    return element


def alignment_script() -> str:
    assets = Path(template.__file__).parent / "assets"
    return (
        template_block("function escapeHtml", "function normalizedMediaLinks")
        + template_block(
            "function detailTableShape", "const DETAIL_TABLE_INTERNAL_KEYS"
        )
        + (assets / "chronology-diagram.js").read_text()
        + (assets / "pollen-diagram.js").read_text()
        + (assets / "pollen-age-axis.js").read_text()
    )


def observe(tabs: dict[str, object], expression: str) -> Any:
    """Use real producer transport, decoders and both qualified source controllers."""
    return run_node_json(
        alignment_script()
        + "const tabs="
        + json.dumps(tabs)
        + ";const original=JSON.stringify(tabs);const native=pollenDepthDiagramData(tabs);const key=native.groups[0]?.key;const depth=pollenAgeAxisData(tabs,key);const options=depth.options;const value=("
        + expression
        + ");if(original!==JSON.stringify(tabs))throw Error('source mutated');console.log(JSON.stringify(value));"
    )


def add_claim(tabs: dict[str, object], original: int, **changes: object) -> None:
    table = cast(dict[str, Any], tabs["chronology"])
    row = table["records"][original].copy()
    for field, value in changes.items():
        row[table["fields"].index(field)] = value
    table["records"].append(row)
    table["record_count"] = len(table["records"])


def test_actual_source_projection_has_no_implicit_age_or_default_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = projected_tabs(tmp_path, monkeypatch)
    original = deepcopy(tabs)
    output = observe(tabs, "depth")
    assert output["status"] == "depth" and output["selected"] is None
    assert len(output["options"]) == 3 and output["total"] == 1
    assert output["rows"][0]["depth"] == 12 and "age" not in output["rows"][0]
    assert output["rows"][0]["value"] == 3
    assert (
        output["rows"][0]["observation"]["observation_id"]
        == "neotoma:observation:40:50:1"
    )
    assert tabs == original
    # Reversing source row order cannot turn a source default into an axis choice.
    table = cast(dict[str, Any], tabs["chronology"])
    table["records"].reverse()
    assert observe(tabs, "depth")["selected"] is None


def test_explicit_choice_preserves_point_interval_and_source_refusal_semantics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = projected_tabs(tmp_path, monkeypatch)
    results = observe(
        tabs, "options.map(option=>pollenAgeAxisData(tabs,key,option.key))"
    )
    assert all(result["status"] == "age" for result in results)
    rows = [result["rows"][0] for result in results]
    assert len(rows) == 3 and all(row["sample"] == "neotoma:sample:40" for row in rows)
    assert sorted(
        row["age"]["point"] for row in rows if row["age"]["point"] is not None
    ) == [0, 125.5]
    interval = next(row for row in rows if row["age"]["point"] is None)
    assert interval["age"]["endpoints"] == [-10, 20]
    assert interval["age"]["claim"]["calibration_status"] == "uncalibrated"
    refused = next(row for row in rows if row["age"]["point"] == 0)
    assert refused["age"]["claim"]["comparability_status"] == "refused"
    assert refused["age"]["claim"]["refusal_reason"] == "<img src=x onerror=alert(1)>"
    assert refused["age"]["claim"]["is_default_chronology"] is None
    assert all(result["omitted"] == {} for result in results)


@pytest.mark.parametrize("field", ["collection_unit_id", "dataset_id"])
def test_other_native_source_partitions_are_not_offered_as_age_choices(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    for index in range(3):
        set_claim(tabs, field, "other-source", index)
    result = observe(tabs, "depth")
    assert result["options"] == [] and result["status"] == "depth"
    assert result["sourceAgeOmitted"] == {"sample_source_relation_mismatch": 3}


def test_missing_claim_does_not_become_zero_or_fall_back_to_another_chronology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    # Add a second genuine sample and observation, without manufacturing an age.
    sample_table = cast(
        dict[str, Any], cast(dict[str, object], tabs["samples"])["samples"]
    )
    sample = sample_table["records"][0].copy()
    sample[sample_table["fields"].index("sample_id")] = "neotoma:sample:99"
    sample_table["records"].append(sample)
    sample_table["record_count"] = 2
    observation_table = cast(dict[str, Any], tabs["pollen_composition"])
    # This table is still compact; only actual prefix-bearing columns are expanded.
    observation_table["records"] = observe(
        tabs,
        "tabs.pollen_composition.records.map(row=>{const decoded=decodeDetailTableRow(tabs.pollen_composition,row);return tabs.pollen_composition.fields.map(field=>decoded[field]);})",
    )
    observation_table.pop("identifier_prefixes", None)
    observation = observation_table["records"][0].copy()
    observation[observation_table["fields"].index("observation_id")] = "new-observation"
    observation[observation_table["fields"].index("sample_id")] = "neotoma:sample:99"
    observation_table["records"].append(observation)
    observation_table["record_count"] = 2
    output = observe(tabs, "pollenAgeAxisData(tabs,key,options[0].key)")
    assert output["total"] == 2 and len(output["rows"]) == 1
    assert output["omitted"] == {"sample_age_assignment_unavailable": 1}
    assert output["rows"][0]["age"]["point"] is not None


def test_multiple_same_group_claims_are_ambiguous_even_if_points_agree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    add_claim(tabs, 0, chronology_claim_id="another-native-claim")
    output = observe(
        tabs,
        "pollenAgeAxisData(tabs,key,options.find(option=>option.identity[6]==='comparable').key)",
    )
    assert output["rows"] == [] and output["total"] == 1
    assert output["omitted"] == {"ambiguous_sample_age_assignment": 1}
    assert (
        output["status"] == "age"
    )  # An explicit choice with no drawable observations.


@pytest.mark.parametrize("selected", ['"unknown"', '""', "false", "0"])
def test_unknown_age_choice_never_selects_first_or_source_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, selected: str
) -> None:
    result = observe(
        projected_tabs(tmp_path, monkeypatch), f"pollenAgeAxisData(tabs,key,{selected})"
    )
    assert result["status"] == "unavailable" and result["rows"] == []
    assert result["selected"] is None
    assert result["reason"] == "selected_source_age_group_unavailable"


def test_missing_depth_is_an_explicit_reused_source_qualification_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    set_sample(tabs, "source_depth", None)
    output = observe(tabs, "depth")
    assert output["status"] == "unavailable"
    assert output["reason"] == "native_source_group_unavailable"


def test_invalid_claim_keeps_depth_and_its_source_reason_population(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    set_claim(tabs, "source_age_younger", 100)
    set_claim(tabs, "source_age_older", 50)
    result = observe(tabs, "depth")
    assert result["status"] == "depth" and len(result["options"]) == 2
    assert result["sourceAgeOmitted"] == {"source_age_endpoints_reversed": 1}
    assert result["sourceAgeTotal"] == 3
    assert result["rows"][0]["value"] == 3


def test_missing_chronology_tables_does_not_disable_native_depth_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = projected_tabs(tmp_path, monkeypatch)
    tabs["chronology"] = {
        "status": "unavailable",
        "reason_code": "source_not_available",
    }
    result = observe(tabs, "depth")
    assert result["status"] == "depth" and result["options"] == []
    assert result["selected"] is None and result["rows"][0]["depth"] == 12
    assert result["sourceAgeOmitted"] is None and result["sourceAgeTotal"] is None
    assert result["reason"] == "encoded_age_depth_table_invalid"


def test_helper_parses_as_packaged_javascript(tmp_path: Path) -> None:
    check_javascript_syntax(alignment_script(), tmp_path / "observation-age.js")


@pytest.mark.parametrize("field", ["collection_unit_id", "dataset_id"])
def test_valid_age_group_for_another_source_partition_is_not_an_option(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    sample_table = cast(
        dict[str, Any], cast(dict[str, object], tabs["samples"])["samples"]
    )
    sample = sample_table["records"][0].copy()
    sample[sample_table["fields"].index("sample_id")] = "neotoma:sample:99"
    sample[sample_table["fields"].index(field)] = "different-native-partition"
    sample_table["records"].append(sample)
    sample_table["record_count"] = 2
    add_claim(
        tabs,
        0,
        chronology_claim_id="different-partition-claim",
        subject_id="neotoma:sample:99",
        source_record_id="neotoma:sample:99",
        **{field: "different-native-partition"},
    )
    output = observe(
        tabs, "({depth,allAgeGroups:ageDepthDiagramData(tabs).groups.length})"
    )
    assert output["allAgeGroups"] == 4
    assert len(output["depth"]["options"]) == 3
    assert output["depth"]["sourceAgeOmitted"] == {}


def test_zero_native_value_and_repeated_distinct_observations_keep_one_claim_each(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = projected_tabs(tmp_path, monkeypatch)
    table = cast(dict[str, Any], tabs["pollen_composition"])
    value_index = table["fields"].index("source_value")
    table["records"][0][value_index] = 0
    row = table["records"][0].copy()
    # Distinct native observations can share a sample and therefore its one age.
    row[table["fields"].index("observation_id")] = "another-observation"
    row[value_index] = 9
    table["records"].append(row)
    table["record_count"] = 2
    result = observe(
        tabs,
        "pollenAgeAxisData(tabs,key,options.find(option=>option.identity[6]==='comparable').key)",
    )
    assert result["total"] == 2 and len(result["rows"]) == 2
    assert sorted(row["value"] for row in result["rows"]) == [0, 9]
    assert result["omitted"] == {}
    assert {row["age"]["claim"]["chronology_claim_id"] for row in result["rows"]} == {
        "neotoma:age-claim:40:1"
    }


def test_stale_native_group_does_not_fall_back_to_another_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = observe(
        projected_tabs(tmp_path, monkeypatch),
        "pollenAgeAxisData(tabs,'unknown-native-group')",
    )
    assert result["status"] == "unavailable" and result["rows"] == []
    assert result["reason"] == "native_source_group_unavailable"


def test_depth_renderer_requires_explicit_age_choice_and_labels_every_source_basis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = projected_tabs(tmp_path, monkeypatch)
    html = observe(tabs, "renderPollenAgeDiagram(tabs,key)")
    tree = ET.fromstring(html)
    assert tree.find(".//svg") is None
    label, select = tree.find("label"), tree.find("select")
    assert label is not None and select is not None
    assert label.get("for") == select.get("id")
    assert select.get("data-pollen-age-group") == "true"
    options = select.findall("option")
    assert len(options) == 4 and options[0].get("value") == ""
    assert options[0].get("selected") == "selected"
    assert all(option.get("selected") is None for option in options[1:])
    for option in options[1:]:
        assert all(
            word in str(option.text)
            for word in [
                "collection",
                "dataset",
                "chronology",
                "source age type",
                "age unit",
                "calibration",
                "comparability",
                "names",
            ]
        )
    assert "not selection of an analysis chronology" in html
    assert "numeric native depth" in html and "No age/depth conversion" in html


def test_age_renderer_keeps_literal_interval_zero_refusal_and_accessible_escaping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = projected_tabs(tmp_path, monkeypatch)
    htmls = observe(
        tabs, "options.map(option=>renderPollenAgeDiagram(tabs,key,option.key))"
    )
    trees = [ET.fromstring(html) for html in htmls]
    assert all(
        required_element(tree, ".//svg").get("viewBox") == "0 0 640 300"
        for tree in trees
    )
    assert all(required_element(tree, ".//svg").get("role") == "img" for tree in trees)
    assert all(
        required_element(tree, ".//div[@class='source-diagram-plot']").get("role")
        == "region"
        for tree in trees
    )
    assert all(
        "Native variable semantics:" in " ".join(tree.itertext())
        and "pollen" in " ".join(tree.itertext())
        for tree in trees
    )
    assert all(
        tree.find(".//svg/title") is not None and tree.find(".//svg/desc") is not None
        for tree in trees
    )
    assert all(
        required_element(tree, ".//svg/g").get("tabindex") == "0" for tree in trees
    )
    interval = next(
        tree
        for tree in trees
        if "reported endpoints -10, 20" in ET.tostring(tree, encoding="unicode")
    )
    assert len(interval.findall(".//svg/g/path")) == 1
    assert not interval.findall(".//svg/g/circle") and not interval.findall(
        ".//svg/g/rect"
    )
    assert "Interval-only assignments have no inferred point or midpoint" in " ".join(
        interval.itertext()
    )
    assert all(
        "not confidence intervals" in " ".join(tree.itertext()) for tree in trees
    )
    refused = next(
        tree
        for tree in trees
        if "reported age point 0;" in ET.tostring(tree, encoding="unicode")
    )
    assert required_element(refused, ".//svg/g/rect").get("stroke-dasharray") == "2 3"
    assert refused.find(".//img") is None
    assert "<img src=x onerror=alert(1)>" in " ".join(refused.itertext())
    assert all(
        "source age table: 3 claims" in " ".join(tree.itertext()) for tree in trees
    )
    assert all("1 of 1 observations" in " ".join(tree.itertext()) for tree in trees)


def test_option_labels_keep_null_distinct_from_literal_string_and_unknown_unit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    set_claim(tabs, "source_age_unit", None)
    set_claim(tabs, "source_age_unit", "null", 1)
    text = " ".join(
        ET.fromstring(observe(tabs, "renderPollenAgeDiagram(tabs,key)")).itertext()
    )
    assert "age unit null" in text and 'age unit "null"' in text


def test_ambiguous_age_renderer_explains_empty_plot_without_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    add_claim(tabs, 0, chronology_claim_id="another-native-claim")
    html = observe(
        tabs,
        "renderPollenAgeDiagram(tabs,key,options.find(option=>option.identity[6]==='comparable').key)",
    )
    tree = ET.fromstring(html)
    assert tree.find(".//svg") is None
    text = " ".join(tree.itertext())
    assert "0 of 1 observations" in text
    assert "multiple age claims for this sample in the chosen group: 1" in text
    assert "No zero age or alternative chronology is substituted" in text


def test_large_age_renderer_uses_all_extrema_but_caps_only_displayed_observations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = decoded(projected_tabs(tmp_path, monkeypatch))
    table = cast(dict[str, Any], tabs["pollen_composition"])
    original = table["records"][0]
    table["records"] = [original.copy() for _ in range(501)]
    table["record_count"] = 501
    for index, row in enumerate(table["records"]):
        row[table["fields"].index("observation_id")] = f"obs-{index:03}"
        row[table["fields"].index("source_value")] = index
    samples = cast(dict[str, Any], cast(dict[str, object], tabs["samples"])["samples"])
    sample = samples["records"][0].copy()
    sample[samples["fields"].index("sample_id")] = "neotoma:sample:99"
    sample[samples["fields"].index("source_depth")] = 13
    samples["records"].append(sample)
    samples["record_count"] = 2
    add_claim(
        tabs,
        0,
        chronology_claim_id="last-sample-age",
        subject_id="neotoma:sample:99",
        source_record_id="neotoma:sample:99",
        source_age_value=9999,
    )
    prefix = table.get("identifier_prefixes", {}).get("sample_id", "")
    table["records"][-1][table["fields"].index("sample_id")] = (
        "neotoma:sample:99".removeprefix(prefix)
    )
    tree = ET.fromstring(
        observe(
            tabs,
            "renderPollenAgeDiagram(tabs,key,options.find(option=>option.identity[6]==='comparable').key)",
        )
    )
    assert len(tree.findall(".//svg/g")) == 500
    text = " ".join(tree.itertext())
    assert "500 of 501 aligned observations drawn" in text
    assert "501 of 501 observations" in text
    assert any(node.text == "500" for node in tree.findall(".//svg/text"))
    assert any(node.text == "9999" for node in tree.findall(".//svg/text"))
    assert "extrema use all aligned observations" in text


def test_reusable_age_figures_have_distinct_accessibility_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = projected_tabs(tmp_path, monkeypatch)
    html = observe(
        tabs,
        "(()=>{const data=pollenAgeAxisData(tabs,key,options[0].key);return '<section>'+pollenAgeFigureHtml(data,native.groups[0],0)+pollenAgeFigureHtml(data,native.groups[0],1)+'</section>';})()",
    )
    tree = ET.fromstring(html)
    svgs = tree.findall(".//svg")
    titles = [required_element(svg, "title").get("id") for svg in svgs]
    assert len(set(titles)) == 2
    assert all(
        str(svg.get("aria-labelledby")).split()[0] == title
        for svg, title in zip(svgs, titles, strict=True)
    )
