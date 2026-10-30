"""Count-only intake, missing-panel identity and bounded consumer refusals."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.common_cover import (
    cohort,
    counting,
    measured_panels,
)
from bijux_pollenomics_dev.essd_reproduction.common_cover import (
    measured_panel_counting as consumer,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
    sources,
)

from .test_measured_panels import source_fixture
from .test_producer import checksum, native_fixture

REVISION = "3" * 40


def counted_fixture(tmp_path: Path) -> dict[str, Any]:
    loaded = source_fixture(tmp_path)
    loaded["cores"][1].update(ppe=[1.0, 1.0], saved_K=[1.0, 1.0])
    for i, group in enumerate(loaded["groups"]):
        for key in ("status", "solver", "common_cover_fit"):
            group.pop(key)
        for j, site in enumerate(group["sites"]):
            site["sample_ids"] = [2 * i + j]
    for i, site in enumerate(loaded["unmatched"]):
        site.update(
            original_axis=list(cohort.TAXA),
            original_counts=[4, 4],
            original_panel_N=8,
            projected_panel_N=8,
            Fraxinus_original_panel_count=None,
            window_cal_bp=[2000 + 100 * i, 2100 + 100 * i],
        )
    return loaded


def admit_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    loaded = counted_fixture(tmp_path)

    def source(repository: Path, project: Any) -> dict[str, Any]:
        assert repository == tmp_path and project is cohort.project_count_core
        return loaded

    monkeypatch.setattr(cohort, "_load_groups", source)
    return cohort.load_count_groups(tmp_path)


def test_full_native_fraxinus_only_window_is_counted_without_projected_selection() -> (
    None
):
    native, saved, core = native_fixture()
    first = native["site"]["collectionunit"]["dataset"]["samples"][0]
    first["datum"][0]["value"] = first["datum"][2]["value"] = 0
    sample = sources.pollen_counts(first)
    support = [
        {
            k: sample[k]
            for k in ("sample_id", "analysis_unit_id", "depth", "ages", "datum_rows")
        }
    ]
    core = replace(
        core,
        cells=(
            replace(
                core.cells[0], counts=(0, 3, 0), source_support_sha256=checksum(support)
            ),
            core.cells[1],
        ),
    )
    saved["results"][0]["reported_all_pollen_NISP_sum"] = 10
    rows = cohort.project_count_core(native, saved, core, [0, 100, 350])
    assert rows[0]["original_counts"] == [0, 3, 0]
    assert rows[0]["original_panel_N"] == 3
    assert rows[0]["projected_panel_N"] == 0
    assert rows[0]["sample_ids"] == [1] and len(rows) == 2
    with pytest.raises(ValueError, match="Projected panel has no counted grains"):
        cohort.project_core(native, saved, core, [0, 100, 350])


@pytest.mark.parametrize("defect", ["missing", "age", "support", "full_zero", "bool"])
def test_count_intake_retains_original_source_and_exclusion_refusals(
    defect: str,
) -> None:
    native, saved, core = native_fixture()
    row = native["site"]["collectionunit"]["dataset"]["samples"][0]
    if defect == "missing":
        row["datum"].pop(1)
    elif defect == "age":
        row["ages"][0]["chronologyid"] = 43
    elif defect == "support":
        core = replace(
            core,
            cells=(
                replace(core.cells[0], source_support_sha256="0" * 64),
                core.cells[1],
            ),
        )
    elif defect == "full_zero":
        for datum in row["datum"][:3]:
            datum["value"] = 0
    else:
        row["datum"][0]["value"] = False
    with pytest.raises(ValueError):
        cohort.project_count_core(native, saved, core, [0, 100, 350])


def test_positive_legacy_projection_output_is_identical_to_shared_count_intake() -> (
    None
):
    native, saved, core = native_fixture()
    assert cohort.project_core(
        native, saved, core, [0, 100, 350]
    ) == cohort.project_count_core(native, saved, core, [0, 100, 350])


def test_full_count_entry_uses_literal_responses_and_never_a_point_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Point-fit admission is outside this count entry")

    monkeypatch.setattr(counting, "read_point_report", forbidden)
    monkeypatch.setattr(measured_panels, "complete_panel", forbidden)
    loaded = admit_fixture(tmp_path, monkeypatch)
    assert len(loaded["groups"]) == 13 and len(loaded["unmatched"]) == 6
    assert loaded["full_panel_responses"][0]["response_PPE_times_K"] == [2.0, 3.0, 1.0]
    assert loaded["full_panel_responses"][1]["response_PPE_times_K"] == [1.0, 1.0]
    boke, bus = loaded["groups"][0]["sites"]
    assert boke["original_taxon_measured"] == [True, True, True]
    assert bus["original_taxon_measured"] == [True, True]
    assert bus["taxon_measured_on_common_axis"] == [True, False, True]
    assert bus["Fraxinus_original_panel_count"] is None
    assert all("common_cover_fit" not in group for group in loaded["groups"])


@pytest.mark.parametrize("defect", ["raw", "literal", "axis", "duplicate_pin"])
def test_count_entry_refuses_changed_original_response_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    loaded = counted_fixture(tmp_path)
    if defect == "raw":
        (tmp_path / measured_panels.SWEDISH_REPORT).write_bytes(b"changed")
    elif defect == "literal":
        path = tmp_path / cohort.PARAMETERS
        raw = path.read_bytes().replace(b"3.0 (0.2)", b"4.0 (0.2)")
        path.write_bytes(raw)
        loaded["scientific_inputs"][1].update(
            sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)
        )
    elif defect == "axis":
        loaded["cores"][0]["ppe"].reverse()
    else:
        loaded["scientific_inputs"].append(loaded["scientific_inputs"][0])
    monkeypatch.setattr(cohort, "_load_groups", lambda *args: loaded)
    with pytest.raises(ValueError):
        cohort.load_count_groups(tmp_path)


def test_joint_outcomes_retain_zero_subtotal_empty_region_and_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loaded = admit_fixture(tmp_path, monkeypatch)
    boke = loaded["groups"][0]["sites"][0]
    boke.update(original_counts=[0, 3, 0], original_panel_N=3, projected_panel_N=0)
    boke, bus = loaded["groups"][1]["sites"]
    boke.update(original_counts=[0, 0, 100], original_panel_N=100)
    bus.update(original_counts=[100, 0], original_panel_N=100)
    loaded["groups"][2]["sites"][1]["taxon_measured_on_common_axis"][1] = True
    before = deepcopy(loaded)
    rows = consumer.evaluate(loaded)
    assert len(rows) == 13 and loaded == before
    first = rows[0]["counting_region"]
    assert first["status"] == "nonempty"
    assert first["shared_panel_constraints"][0]["counting_interval"] is None
    assert first["complete_only_counting"] is not None
    assert first["excluded_complete_only_vertex"] is True
    assert first["cover_upper_exact"][1] == "1" and first["upper_attained"][1] is False
    assert rows[1]["counting_region"]["status"] == "empty"
    assert rows[1]["counting_region"]["cover_lower_exact"] is None
    assert rows[2]["status"] == "refused" and rows[2]["counting_region"] is None
    assert rows[0]["sites"] is loaded["groups"][0]["sites"]


@pytest.mark.parametrize(
    "defect", ["bool_count", "missing_mask", "effort", "mask_integer"]
)
def test_consumer_refuses_ambiguous_measured_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    loaded = admit_fixture(tmp_path, monkeypatch)
    boke = loaded["groups"][0]["sites"][0]
    if defect == "bool_count":
        boke["original_counts"][0] = False
    elif defect == "missing_mask":
        boke["original_taxon_measured"][1] = False
    elif defect == "effort":
        boke["original_panel_N"] += 1
    else:
        boke["taxon_measured_on_common_axis"][0] = 1
    first = consumer.evaluate(loaded)[0]
    assert first["status"] == "refused" and first["counting_region"] is None


@pytest.mark.parametrize("change", [None, "raw_during", "source_during", "fatal"])
def test_actual_cli_uses_only_count_inputs_and_rechecks_terminal_integrity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str | None
) -> None:
    loaded = admit_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(cohort, "load_count_groups", lambda repository: loaded)
    calls = 0

    def revision(repository: Path) -> str:
        nonlocal calls
        calls += 1
        return "4" * 40 if change == "source_during" and calls > 1 else REVISION

    monkeypatch.setattr(consumer, "_revision", revision)
    original = consumer.evaluate

    def evaluate(value: dict[str, Any]) -> list[dict[str, Any]]:
        if change == "fatal":
            value["groups"][0]["sites"][0].pop("original_counts")
        rows = original(value)
        if change == "raw_during":
            (tmp_path / cohort.PARAMETERS).write_bytes(b"changed during calculation")
        return rows

    monkeypatch.setattr(consumer, "evaluate", evaluate)
    output = tmp_path / "artifacts" / "count-region" / "report.json"
    output.parent.mkdir(parents=True)
    monkeypatch.setattr(
        sys,
        "argv",
        ["counting", "--repository", str(tmp_path), "--output", str(output)],
    )
    if change in {"raw_during", "source_during"}:
        with pytest.raises(ValueError, match="identity mismatch|source changed"):
            consumer.main()
        assert not output.exists()
        return
    with pytest.raises(SystemExit) as exit_status:
        consumer.main()
    assert exit_status.value.code == (1 if change == "fatal" else 0)
    actual = json.loads(output.read_bytes())
    assert actual["source_commit"] == REVISION
    assert actual["scientific_inputs"] == loaded["scientific_inputs"]
    assert actual["unmatched"] == loaded["unmatched"]
    assert actual["new_point_fits"] == actual["new_kernel_evaluations"] == 0
    assert actual["point_fit_selection_applied"] is False
    assert actual["positive_projected_effort_selection_applied"] is False
    assert actual["simultaneous_across_windows_claimed"] is False
    assert actual["sampling_calibration_established"] is False
    assert "point_report" not in actual and output.stat().st_size <= 1024**2
    if change == "fatal":
        assert actual["status_counts"] == {"fatal": 1, "not_run": 12}
    else:
        assert actual["status_counts"] == {"computed": 13}
        for row in actual["groups"]:
            region = row["counting_region"]
            assert Fraction(
                region["guaranteed_joint_confidence_lower_bound"]
            ) >= Fraction.from_float(0.95)
            assert region["marginal_confidence_level"] > 0.975
            assert len(region["corners"]) == 4


@pytest.mark.parametrize("defect", ["alias", "untracked", "dirty"])
def test_canonical_consumed_source_identity_is_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    root = Path(__file__).resolve().parents[5]
    if defect == "alias":
        with pytest.raises(ValueError, match="outside canonical source"):
            consumer._revision(tmp_path)
        return

    def git(argv: list[str], **kwargs: Any) -> bytes:
        if argv[3] == "rev-parse":
            return REVISION.encode()
        if argv[3] == ("ls-files" if defect == "untracked" else "diff"):
            raise subprocess.CalledProcessError(1, argv)
        return b""

    monkeypatch.setattr(subprocess, "check_output", git)
    with pytest.raises(subprocess.CalledProcessError):
        consumer._revision(root)
