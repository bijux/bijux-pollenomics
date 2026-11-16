"""The 2025 reference preserves source identities without becoming a model profile."""

from __future__ import annotations

from copy import deepcopy
import csv
from hashlib import sha256
from importlib import import_module
import io
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.taxa import (
    parameter_coverage,
)


def implementation() -> Any:
    return import_module(
        "bijux_pollenomics_dev.source_completion.pollen_reconstruction."
        "bokesjon_pilot.taxa.legacyvegetation"
    )


def reference_rows() -> tuple[
    dict[str, Any], list[dict[str, str]], list[dict[str, str]]
]:
    originals = [
        {
            "taxon": "Betula",
            "continent": "Europe",
            "rpp": "4.1",
            "rpp_se": "",
            "reference": "literal source",
            "study_doi": "https://example.org/study",
            "source_workbook": "originals/original-rpp.xlsx",
            "source_sheet": "Worksheet 1",
            "source_row": "2",
            "taxon_cell": "A2",
            "rpp_cell": "C2",
            "rpp_se_cell": "D2",
        }
    ]
    synthesis = []
    for taxon, level, region, row, rpp, sd, speed in (
        ("Betula", "genus", "Europe", "6", "4.94", "0.443", "0.024"),
        ("Betulaceae", "family", "Europe", "56", "5.195", "0.145", "0.028"),
        ("Ulmus", "genus", "Europe", "36", "–", "–", "0.032"),
        ("Ulmus", "genus", "Northern Hemisphere", "36", "2.025", "0.312", "0.022"),
        ("Sapindales", "order", "Europe", "123", "0.23", "0.043", "0.043"),
        ("Sapindales", "order", "Europe", "127", "–", "–", "–"),
    ):
        synthesis.append(
            {
                "taxon": taxon,
                "taxonomic_level": level,
                "region": region,
                "rpp": rpp,
                "rpp_sd": sd,
                "n_estimates": "–" if rpp == "–" else "3",
                "fall_speed": speed,
                "source_workbook": "originals/synthesized-rpp.xlsx",
                "source_sheet": "Worksheet 1",
                "source_row": row,
                "taxon_cell": "A" + row,
                "rpp_cell": "G" + row,
                "rpp_sd_cell": "H" + row,
            }
        )
    source = {
        "schema_version": "pollen-productivity-reference.v1",
        "paper": {
            "doi": "10.5194/essd-17-2007-2025",
            "attribution": "Schild et al. (2025), Tables A1/B1",
        },
        "source_originals": [
            {"path": path, "sha256": "a" * 64, "bytes": 123}
            for path in (
                "originals/original-rpp.xlsx",
                "originals/synthesized-rpp.xlsx",
            )
        ],
        "statistical_semantics": {
            "rpp_units": "Poaceae reference normalization",
            "fall_speed_units": "vg unit not stated; not qualified",
            "original_uncertainty": "sourceSE",
            "synthesis_uncertainty": "sourceSD",
        },
        "source_discrepancies": [
            {"issue": "Duplicate source label", "taxon": "Sapindales"}
        ],
    }
    return source, originals, synthesis


def test_exact_reference_rows_stay_distinct_and_never_supply_an_automatic_profile() -> (
    None
):
    source, originals, synthesis = reference_rows()
    result = implementation().adapt_reference(source, originals, synthesis)
    rows = result["synthesized_rows"]
    assert len(rows) == 6 and len({tuple(r["source_row_identity"]) for r in rows}) == 6
    assert [r["source_row"] for r in rows if r["taxon"] == "Sapindales"] == [
        "123",
        "127",
    ]
    ulmus = next(r for r in rows if r["taxon"] == "Ulmus" and r["region"] == "Europe")
    assert ulmus["rpp"] == ulmus["rpp_sd"] == ulmus["n_estimates"] == "–"
    assert ulmus["fall_speed"] == "0.032" and ulmus["nominal_rpp_available"] is False
    assert all(r["fall_speed_unit_status"] == "unqualified_native_vg" for r in rows)
    assert all(r["nominal_rpp_fsp_available"] is False for r in rows)
    assert rows[0]["uncertainty_semantics"] == "source_label_SD"
    assert result["original_rows"][0]["uncertainty_semantics"] == "source_label_SE"
    assert result["original_rows"][0]["rpp_se"] == ""
    assert "ppe_sd" not in rows[0] and "fall_speed_m_s" not in rows[0]
    assert (
        result["scientific_admission"] is False and result["model_axes_selected"] == []
    )
    originals[0]["rpp"] = "caller mutation"
    assert result["original_rows"][0]["rpp"] == "4.1"


def test_real_coverage_consumer_adds_reference_candidates_without_changing_old_fields() -> (
    None
):
    source, originals, synthesis = reference_rows()
    reference = implementation().adapt_reference(source, originals, synthesis)
    native = {
        "taxon_axis": [
            {"native_label": name, "taxon_id": i, "known_NISP_sum": 1}
            for i, name in enumerate(("Betula", "Betulaceae", "Ulmus", "Sapindales"), 1)
        ]
    }
    baseline = parameter_coverage(native, [], [])
    augmented = parameter_coverage(native, [], [], legacyvegetation_2025=reference)
    assert {
        k: v
        for k, v in augmented.items()
        if k != "legacyvegetation_2025_reference" and k != "native_taxa"
    } == {k: v for k, v in baseline.items() if k != "native_taxa"}
    for old, new in zip(baseline["native_taxa"], augmented["native_taxa"], strict=True):
        assert {k: v for k, v in new.items() if k != "legacyvegetation_2025"} == old
    mapped = {
        r["native_label"]: r["legacyvegetation_2025"] for r in augmented["native_taxa"]
    }
    assert len(mapped["Sapindales"]["synthesized_exact_label_candidates"]) == 2
    assert {
        r["region"] for r in mapped["Ulmus"]["synthesized_exact_label_candidates"]
    } == {"Europe", "Northern Hemisphere"}
    assert (
        mapped["Betula"]["synthesized_exact_label_candidates"][0]["taxonomic_level"]
        == "genus"
    )
    assert (
        mapped["Betulaceae"]["synthesized_exact_label_candidates"][0]["taxonomic_level"]
        == "family"
    )
    assert augmented["legacyvegetation_2025_reference"]["model_axes_selected"] == []
    assert json.loads(json.dumps(augmented))["scientific_admission"] is False


@pytest.mark.parametrize(
    "damage",
    [
        "duplicate_identity",
        "noncanonical_row",
        "foreign_workbook",
        "wrong_sheet",
        "nonstrings",
    ],
)
def test_ambiguous_or_changed_source_identity_refuses(damage: str) -> None:
    source, originals, synthesis = reference_rows()
    if damage == "duplicate_identity":
        synthesis.append(deepcopy(synthesis[0]))
    elif damage == "noncanonical_row":
        synthesis[0]["source_row"] = "06"
    elif damage == "foreign_workbook":
        synthesis[0]["source_workbook"] = "../other.xlsx"
    elif damage == "wrong_sheet":
        synthesis[0]["source_sheet"] = "Other"
    else:
        synthesis[0]["rpp"] = 4.94  # type: ignore[assignment]
    with pytest.raises(ValueError):
        implementation().adapt_reference(source, originals, synthesis)


def packet(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "parameter-reference"
    root.mkdir()
    source, originals, synthesis = reference_rows()
    tables = []
    for name, rows in (
        ("original-study-estimates.csv", originals),
        ("synthesized-estimates.csv", synthesis),
    ):
        text = io.StringIO(newline="")
        writer = csv.DictWriter(text, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        raw = text.getvalue().encode()
        (root / name).write_bytes(raw)
        tables.append(
            {
                "path": name,
                "sha256": sha256(raw).hexdigest(),
                "bytes": len(raw),
                "rows": len(rows),
            }
        )
    source["reference_tables"] = tables
    raw = json.dumps(source).encode()
    (root / "source.json").write_bytes(raw)
    return root, sha256(raw).hexdigest()


def test_selected_reader_binds_three_metadata_files_without_workbook_or_sibling_reads(
    tmp_path: Path,
) -> None:
    root, expected = packet(tmp_path)
    (root / "forbidden-observations.body").write_bytes(b"must remain opaque")
    result = implementation().read_reference(root, expected_source_sha256=expected)
    assert {r["path"] for r in result["source_pins"]} == {
        "source.json",
        "original-study-estimates.csv",
        "synthesized-estimates.csv",
    }
    assert len(result["original_rows"]) == 1 and len(result["synthesized_rows"]) == 6
    assert not (root / "originals").exists()
    (root / "synthesized-estimates.csv").write_bytes(b"changed")
    with pytest.raises(ValueError):
        implementation().read_reference(root, expected_source_sha256=expected)


def test_parameter_metadata_leaf_alias_refuses(tmp_path: Path) -> None:
    root, expected = packet(tmp_path)
    original = root / "source.json"
    retained = root / "retained-source.json"
    original.rename(retained)
    original.symlink_to(retained)
    with pytest.raises((ValueError, OSError)):
        implementation().read_reference(root, expected_source_sha256=expected)


@pytest.mark.parametrize("declared_bytes", [65537, 1])
def test_declared_byte_limit_is_enforced_before_opening_the_csv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, declared_bytes: int
) -> None:
    import os

    root, _ = packet(tmp_path)
    source = json.loads((root / "source.json").read_bytes())
    source["reference_tables"][0]["bytes"] = declared_bytes
    raw = json.dumps(source).encode()
    (root / "source.json").write_bytes(raw)
    opened = []
    original = os.open

    def observe(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if isinstance(path, (str, bytes, os.PathLike)):
            opened.append(Path(os.fsdecode(path)).name)
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", observe)
    with pytest.raises(ValueError):
        implementation().read_reference(
            root, expected_source_sha256=sha256(raw).hexdigest()
        )
    assert "original-study-estimates.csv" not in opened


def test_cli_opt_in_reaches_the_existing_workflow(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import sys

    module = import_module(
        "bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.__main__"
    )
    calls = []

    def observe(*args: Any, **kwargs: Any) -> Path:
        calls.append((args, kwargs))
        return tmp_path / "unexecuted"

    monkeypatch.setattr(module, "run", observe)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "bokesjon-pilot",
            "--repository",
            str(tmp_path),
            "--output",
            str(tmp_path / "output"),
            "--legacyvegetation-2025",
        ],
    )
    module.main()
    assert len(calls) == 1 and calls[0][1]["include_legacyvegetation_2025"] is True


def test_packet_root_replacement_refuses_before_the_next_metadata_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, expected = packet(tmp_path)
    module = implementation()
    original_decode = module.json.loads
    original_read = module.BoundedInputTree.read
    reads = []
    substituted: list[Path] = []

    def decode(*args: Any, **kwargs: Any) -> Any:
        value = original_decode(*args, **kwargs)
        if isinstance(value, dict) and "reference_tables" in value and not substituted:
            retained = tmp_path / "retained-parameter-reference"
            root.rename(retained)
            root.mkdir()
            (root / "original-study-estimates.csv").write_bytes(
                b"foreign generated body"
            )
            substituted.append(retained)
        return value

    def read(tree: Any, path: Path, **kwargs: Any) -> bytes:
        body = original_read(tree, path, **kwargs)
        assert isinstance(body, bytes)
        reads.append(path.name)
        return body

    monkeypatch.setattr(module.json, "loads", decode)
    monkeypatch.setattr(module.BoundedInputTree, "read", read)
    with pytest.raises((ValueError, OSError)):
        module.read_reference(root, expected_source_sha256=expected)
    assert substituted, "The generated root replacement must actually occur"
    assert reads == ["source.json"], (
        "Root drift must refuse before another metadata body is read"
    )
    assert (
        root / "original-study-estimates.csv"
    ).read_bytes() == b"foreign generated body"
    assert (substituted[0] / "source.json").is_file()
