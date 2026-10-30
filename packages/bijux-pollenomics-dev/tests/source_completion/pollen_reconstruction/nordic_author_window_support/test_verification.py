"""Analytical artificial source evidence and fail-closed independent readback."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
from decimal import Decimal
from hashlib import sha256
import io
import json
from pathlib import Path
from typing import Any

import pytest

from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.verification import (
    decode,
)

from . import verification as audit
from .fixtures import (
    cell,
    csv_bytes,
    lookup_fixture,
    native_fixture,
    native_samples,
    parameter_fixture,
    protocol,
    saved_inputs,
)
from .native_owners import author_panel, native_owner
from .population import expected_core, parameter_evidence


def lookup() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for row in lookup_fixture():
        out.setdefault(row["oldvar"], []).append(row)
    return out


@pytest.mark.parametrize("index", range(7))
def test_complete_core_analytical_mass_and_native_identity(index: int) -> None:
    source, core, profile = native_fixture(index)
    original = deepcopy(source)
    expected = expected_core(source, core, profile, lookup())
    n = core["identity"]["source_sample_count"]
    assert expected["population"]["samples"] == n
    assert expected["source_totals"]["panel_counts"] == [4 * n, 2 * n]
    assert expected["source_totals"]["pollen_N"] == 9 * n
    assert expected["source_totals"]["excluded_pollen_N"] == 3 * n
    assert expected["support_summary"]["supported_windows"] == 6
    for row in expected["windows"]:
        count = len([i for i in range(n) if i % 9 == (row["window"][0] - 2700) // 500])
        assert row["member_count"] == count and row["panel_counts"] == [
            4 * count,
            2 * count,
        ]
        assert row["pollen_N"] == 9 * count and row["excluded_pollen_N"] == 3 * count
    assert (
        expected["chronology"]["native_collection_default_reference"]
        == core["chronology"]["native_collection_default_reference"]
    )
    assert (
        expected["samples"][0]["taxa"][1]["source_name"]
        == core["native_axes"][1]["source_name"]
    )
    assert (
        expected["samples"][0]["datum_accounting"][2]["disposition"]
        == "unmapped_native_name"
    )
    assert expected["samples"][0]["datum_accounting"][3]["disposition"] == "non_pollen"
    assert expected["samples"][0]["native_ages"] == native_samples(source)[0]["ages"]
    assert source == original


def test_all_source_owners_and_sols_shared_place_are_not_pooled() -> None:
    ledgers = [expected_core(*native_fixture(i), lookup()) for i in range(7)]
    assert sum(r["population"]["samples"] for r in ledgers) == 542
    assert sum(len(r["windows"]) for r in ledgers) == 42
    assert len({r["physical_family"] for r in ledgers}) == 6
    assert len({r["country"] for r in ledgers}) == 4
    assert ledgers[3]["physical_family"] == ledgers[4]["physical_family"]
    assert (
        ledgers[3]["samples"][0]["sample_id"] != ledgers[4]["samples"][0]["sample_id"]
    )


@pytest.mark.parametrize("kind", ["missing", "duplicate", "type", "bounds", "boolean"])
def test_unassignable_age_suppresses_only_its_core(kind: str) -> None:
    source, core, profile = native_fixture(5)
    ages = native_samples(source)[0]["ages"]
    if kind == "missing":
        ages.pop(0)
    elif kind == "duplicate":
        ages.append(deepcopy(ages[0]))
    elif kind == "type":
        ages[0]["agetype"] = "Radiocarbon years BP"
    elif kind == "bounds":
        ages[0]["ageolder"] = 2699
    else:
        ages[0]["age"] = True
    result = expected_core(source, core, profile, lookup())
    assert all(
        row["status"] == "suppressed_unassignable_age" and row["panel_counts"] is None
        for row in result["windows"]
    )
    assert result["source_totals"]["panel_N"] == 900
    other = expected_core(*native_fixture(6), lookup())
    assert other["support_summary"]["supported_windows"] == 6


def test_signed_bound_and_missing_keys_do_not_change_selected_point_epoch() -> None:
    source, core, profile = native_fixture(3)
    age = native_samples(source)[8]["ages"][0]
    age["ageyounger"] = -41
    age["ageolder"] = None
    result = expected_core(source, core, profile, lookup())
    row = result["samples"][8]
    assert row["selected_age"]["age"] == 7
    assert row["age_disposition"] == "outside_requested_windows"
    assert row["selected_age"]["ageyounger"] == -41
    assert row["native_ages"][1]["age"] == 720
    assert "ageyounger" not in result["samples"][0]["selected_age"]
    assert result["support_summary"]["supported_windows"] == 6


@pytest.mark.parametrize(
    "kind",
    ["default", "flag", "extra_declaration", "owner", "nested", "duplicate_dataset"],
)
def test_source_ownership_and_literal_default_metadata_refuse(kind: str) -> None:
    source, core, _ = native_fixture(0)
    site = source["rows"][0]["site"]
    unit = site["collectionunit"]
    if kind == "default":
        unit["defaultchronology"] += 1
    elif kind == "flag":
        unit["chronologies"][0]["chronology"]["chronology"]["isdefault"] = 1
    elif kind == "extra_declaration":
        extra = deepcopy(unit["chronologies"][0])
        extra["chronology"]["chronologyid"] += 1
        unit["chronologies"].append(extra)
    elif kind == "owner":
        native_samples(source)[1]["sampleid"] = native_samples(source)[0]["sampleid"]
    elif kind == "nested":
        unit["dataset"]["datasetid"] += 1
    else:
        source["rows"].append(deepcopy(source["rows"][0]))
    with pytest.raises(ValueError):
        native_owner(source, core)


@pytest.mark.parametrize(
    "value,state",
    [
        (0, "measured_zero"),
        (1.0, "invalid_count"),
        (True, "invalid_count"),
        (None, "null_native_value"),
        (10**80, "measured"),
    ],
)
def test_count_tokens_and_large_integer_arithmetic(value: object, state: str) -> None:
    source, core, profile = native_fixture()
    native_samples(source)[0]["datum"][1]["value"] = value
    row = expected_core(source, core, profile, lookup())["samples"][0]
    assert row["taxa"][1]["status"] == state
    if type(value) is int:
        assert row["panel_N"] == value + 4 and row["pollen_N"] == value + 7
    else:
        assert row["panel_N"] is None and row["pollen_N"] is None


def test_missing_native_axis_is_not_source_zero_and_third_concept_is_not_hidden() -> (
    None
):
    source, core, _ = native_fixture()
    datum = native_samples(source)[0]["datum"]
    datum.pop(1)
    out = author_panel(datum, core, lookup(), ["zz.do not use", "aage.cal.BP"])
    assert (
        out["panel_counts"] == [4, None]
        and out["taxa"][1]["status"] == "missing_native_axis"
    )
    mapping = lookup()
    mapping["Extra pine"] = [
        {"row_number": 99, "oldvar": "Extra pine", "author_target": "Pinus"}
    ]
    datum.append(cell("Extra pine", 999, 1))
    with pytest.raises(ValueError, match="additional"):
        author_panel(datum, core, mapping, [])


@pytest.mark.parametrize("stomate_count", [1, 10**80, None, True])
def test_explicit_stomate_is_not_duplicate_pollen_or_pollen_mass(
    stomate_count: object,
) -> None:
    source, core, profile = native_fixture(1)
    datum = native_samples(source)[0]["datum"]
    stomate = deepcopy(datum[1])
    stomate.update(element="stomate", elementtype="stomate", value=stomate_count)
    datum.insert(0, stomate)
    original = deepcopy(datum)
    row = expected_core(source, core, profile, lookup())["samples"][0]
    assert row["panel_counts"] == [4, 2] and row["pollen_N"] == 9
    assert row["taxa"][1]["status"] == "measured"
    assert row["taxa"][1]["native_matches"] == [{"datum_index": 2, "native": datum[2]}]
    assert row["datum_accounting"][0]["native"] == stomate
    assert row["datum_accounting"][0]["disposition"] == "non_pollen"
    assert datum == original


def test_stomate_only_is_missing_pollen_not_zero() -> None:
    source, core, profile = native_fixture(1)
    datum = native_samples(source)[0]["datum"]
    datum[1].update(element="stomate", elementtype="stomate")
    row = expected_core(source, core, profile, lookup())["samples"][0]
    assert row["taxa"][1]["status"] == "missing_native_axis"
    assert row["panel_counts"] == [4, None] and row["panel_N"] is None
    assert row["datum_accounting"][1]["native"] == datum[1]


@pytest.mark.parametrize(
    "roles",
    [
        {},
        {"element": "pollen"},
        {"element": "stomate", "elementtype": "pollen"},
        {"element": "stomate", "elementtype": "unknown"},
        {"element": None, "elementtype": None},
        {"element": "", "elementtype": ""},
        {"element": " ", "elementtype": " "},
    ],
)
@pytest.mark.parametrize("beside_valid", [False, True])
def test_unknown_or_contradictory_pollen_role_cannot_hide_axis_evidence(
    roles: dict[str, object], beside_valid: bool
) -> None:
    source, core, profile = native_fixture(1)
    datum = native_samples(source)[0]["datum"]
    altered = deepcopy(datum[1])
    altered.pop("element")
    altered.pop("elementtype")
    altered.update(roles)
    if beside_valid:
        datum.append(altered)
    else:
        datum[1] = altered
    row = expected_core(source, core, profile, lookup())["samples"][0]
    assert row["taxa"][1]["status"] == (
        "duplicate_native_axis" if beside_valid else "incompatible_metadata"
    )
    assert row["panel_N"] is None
    assert len(row["datum_accounting"]) == len(datum)


def test_true_pollen_duplicate_still_refuses_with_stomate_context() -> None:
    source, core, profile = native_fixture(1)
    datum = native_samples(source)[0]["datum"]
    datum.append(deepcopy(datum[1]))
    stomate = deepcopy(datum[1])
    stomate.update(element="stomate", elementtype="stomate")
    datum.append(stomate)
    row = expected_core(source, core, profile, lookup())["samples"][0]
    assert row["taxa"][1]["status"] == "duplicate_native_axis"
    assert len(row["taxa"][1]["native_matches"]) == 2
    assert row["panel_N"] is None
    assert row["pollen_N"] is None
    assert row["datum_accounting"][-1]["disposition"] == "non_pollen"


def test_parameter_full_axis_and_exact_selected_decimal_profile() -> None:
    lut, mean, cov, binding = parameter_fixture()
    out, mapping = parameter_evidence(
        {"lookup": lut, "mean": mean, "covariance": cov}, protocol(), binding
    )
    assert len(out["axis"]) == 31 and len(out["covariance_rows"]) == 31
    assert (
        out["lookup"]["rows"] == 10788 and out["lookup"]["unique_source_names"] == 9731
    )
    assert out["selected"]["alpha_text"] == ["5.10571", "6.05833"]
    assert out["selected"]["covariance_text"] == [
        ["0.092006056", "0"],
        ["0", "0.056016002"],
    ]
    assert Decimal(out["selected"]["covariance_text"][0][0]) != Decimal("0.303") ** 2
    assert mapping["Pinus sylvestris"][0]["author_target"] == "Pinus"


def test_author_lookup_latin1_names_are_not_casefolded_or_transliterated() -> None:
    lut, mean, cov, binding = parameter_fixture()
    lut = lut.replace(b"Synthetic source 0,", b"Synthetic p\xe5lle,")
    _, mapping = parameter_evidence(
        {"lookup": lut, "mean": mean, "covariance": cov}, protocol(), binding
    )
    assert "Synthetic pålle" in mapping and "Synthetic palle" not in mapping


@pytest.mark.parametrize(
    "kind", ["lookup_conflict", "lookup_missing", "axis", "asymmetry", "nan", "rounded"]
)
def test_parameter_or_lookup_corruption_refuses(kind: str) -> None:
    lut, mean, cov, binding = parameter_fixture()
    profile = protocol()
    if kind == "lookup_conflict":
        lut += b"Pinus,Betula\n"
    elif kind == "lookup_missing":
        lut = lut.replace(b"Pinus sylvestris,Pinus\n", b"Unknown pine,Pinus\n")
    elif kind == "axis":
        mean = mean.replace(b"Pinus,6.05833", b"Other pine,6.05833")
    elif kind == "rounded":
        mean = mean.replace(b"Betula,5.10571", b"Betula,5.106")
    elif kind == "nan":
        mean = mean.replace(b"Pinus,6.05833", b"Pinus,NaN")
    else:
        rows = list(csv.DictReader(io.StringIO(cov.decode())))
        rows[0]["Pinus"] = "0.1"
        cov = csv_bytes(list(rows[0]), rows)
    with pytest.raises(ValueError):
        parameter_evidence(
            {"lookup": lut, "mean": mean, "covariance": cov}, profile, binding
        )


def closed_fixture(base: Path) -> tuple[Path, Path, Path, Path, dict[str, Any]]:
    repo, original = base / "repo", base / "original"
    repo.mkdir()
    original.mkdir()
    profile, protocol_path = saved_inputs(repo, original)
    enriched, mapping, params, pins = audit.contract(repo, original, profile)
    runner = repo / audit.RUNNER
    runner.parent.mkdir(parents=True, exist_ok=True)
    runner.write_bytes(b"synthetic runner; never execute")
    state = {
        "head": "0" * 40,
        "index_sha256": "1" * 64,
        "python_files": {"source.py": "2" * 64},
    }
    out = repo / "artifacts/products"
    out.mkdir(parents=True)

    def store(name: str, value: Any) -> dict[str, Any]:
        raw = (json.dumps(value, sort_keys=True, default=float) + "\n").encode()
        (out / name).write_bytes(raw)
        return {"path": name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}

    products = {"parameters": store("parameters.json", params)}
    summaries = {}
    statuses: Counter[str] = Counter()
    for core in profile["cores"]:
        native = decode(
            audit.read_pin(repo, core["source"], profile["source_max_bytes"])
        )
        value = expected_core(native, core, enriched, mapping)
        products[core["key"]] = store(core["key"] + ".json", value)
        summaries[core["key"]] = {
            k: value[k]
            for k in [
                "identity",
                "country",
                "physical_family",
                "population",
                "support_summary",
            ]
        }
        statuses.update(value["support_summary"]["window_status_counts"])
    pbytes = protocol_path.read_bytes()
    rbytes = runner.read_bytes()
    protocol_pin = {
        "path": str(protocol_path.relative_to(repo)),
        "bytes": len(pbytes),
        "sha256": sha256(pbytes).hexdigest(),
    }
    runner_pin = {
        "path": audit.RUNNER,
        "bytes": len(rbytes),
        "sha256": sha256(rbytes).hexdigest(),
    }
    common = {
        "protocol": protocol_pin,
        "runner": runner_pin,
        "source_commit": state["head"],
        "index_sha256": state["index_sha256"],
        "python_files_checked": 1,
        "sourcepins": pins,
    }
    products["input_manifest"] = store(
        "input-manifest.json",
        {"schema_version": "nordic-author-window-inputs.v1", **common},
    )
    store(
        "result.json",
        {
            "schema_version": "nordic-author-window-result.v1",
            "status": "produced_awaiting_independent_verification",
            **common,
            "source_guards_passed": True,
            "products": products,
            "cores": summaries,
            "population": profile["population"],
            "window_status_counts": dict(statuses),
            "engine_calls": 0,
            "model_fits": 0,
            "source_acquisition": False,
            "scientific_or_field_admission": False,
            "resources": {
                "elapsed_seconds": 1,
                "peak_rss_bytes": 1000,
                "output_bytes": sum(p.stat().st_size for p in out.iterdir()),
            },
        },
    )
    return repo, original, out, protocol_path, state


def test_closed_full_population_readback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, original, out, profile, state = closed_fixture(tmp_path)
    monkeypatch.setattr(audit, "code_state", lambda _: deepcopy(state))
    monkeypatch.setattr(audit, "committed_protocol", lambda *_: None)
    facts = audit.verify(repo, original, out, profile)
    assert (
        facts["native_sample_owners_checked"] == 542
        and facts["requested_windows_checked"] == 42
    )
    assert facts["window_status_counts"] == {"supported": 42}
    assert (
        facts["author_covariance_cells_checked"] == 961
        and facts["source_files_checked"] == 14
    )


@pytest.mark.parametrize(
    "kind",
    ["member_bytes", "extra_member", "source_bytes", "metadata", "epoch", "resource"],
)
def test_readback_rejects_closed_inventory_source_or_epoch_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    repo, original, out, profile, state = closed_fixture(tmp_path)
    monkeypatch.setattr(audit, "code_state", lambda _: deepcopy(state))
    monkeypatch.setattr(audit, "committed_protocol", lambda *_: None)
    if kind == "member_bytes":
        (out / "laihalampi.json").write_bytes(b"{}")
    elif kind == "extra_member":
        (out / "extra.json").write_bytes(b"{}")
    elif kind == "source_bytes":
        next(original.rglob("*.csv")).write_bytes(b"changed")
    elif kind == "metadata":
        r = json.loads(profile.read_bytes())
        p = repo / r["provenance"]["chronology_metadata"]["path"]
        p.write_bytes(b"{}")
    else:
        r = json.loads((out / "result.json").read_bytes())
        if kind == "epoch":
            r["source_commit"] = "f" * 40
        else:
            r["resources"]["peak_rss_bytes"] = 2 * 1024**3
        (out / "result.json").write_text(json.dumps(r))
    with pytest.raises(ValueError):
        audit.verify(repo, original, out, profile)


def test_safe_pin_path_refuses_alias_and_type_coercion(tmp_path: Path) -> None:
    p = tmp_path / "source.json"
    p.write_bytes(b"{}")
    link = tmp_path / "alias.json"
    link.symlink_to(p)
    for path, size in [("alias.json", 2), ("../source.json", 2), ("source.json", True)]:
        with pytest.raises(ValueError):
            audit.read_pin(
                tmp_path,
                {"path": path, "bytes": size, "sha256": sha256(b"{}").hexdigest()},
                10,
            )
