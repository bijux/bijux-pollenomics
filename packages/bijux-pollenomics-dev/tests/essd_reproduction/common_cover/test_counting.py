"""Saved-source admission and count-only consumer outcomes on controlled inputs."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.common_cover import cohort, counting
from bijux_pollenomics_lra.reconstruction.uncertainty import multisite_counting

POINT_SOURCE = "1" * 40
PUBLICATION = "2" * 40
COUNT_SOURCE = "3" * 40


def fixture_report() -> dict[str, Any]:
    return {
        "schema_version": "boke-bus-conditional-multisite-likelihood.v1",
        "source_commit": POINT_SOURCE,
        "taxa": ["Betula", "Ulmus"],
        "age_unit": "calibrated years BP, AD1950 reference",
        "status_counts": {"computed": 13},
        "cores": [
            {"core": name, "response_PPE_times_K": [1.0, 1.0]}
            for name in ["BOKE", "BUS"]
        ],
        "groups": [
            {
                "window_cal_bp": [i * 100, (i + 1) * 100],
                "status": "computed",
                "sites": [
                    {
                        "core": core,
                        "projected_counts": counts,
                        "projected_panel_N": sum(counts),
                        "taxon_measured": [True, True],
                        "sample_ids": [i * 2 + site],
                    }
                    for site, (core, counts) in enumerate(
                        zip(
                            ["BOKE", "BUS"],
                            [[0, 100], [100, 0]] if i == 1 else [[4, 6], [5, 5]],
                            strict=True,
                        )
                    )
                ],
            }
            for i in range(13)
        ],
        "unmatched": [
            {
                "core": "BUS",
                "window_cal_bp": [2000 + i * 100, 2100 + i * 100],
                "status": "unmatched_window_no_fit",
            }
            for i in range(6)
        ],
        "scientific_inputs": [],
        "original_source_epochs": {"swedish": "original-source"},
    }


def admitted(report: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(report)
    result["groups"] = [
        {"window_cal_bp": row["window_cal_bp"], "sites": row["sites"]}
        for row in result["groups"]
    ]
    return result


def saved_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], bytes]:
    report = fixture_report()
    raw = json.dumps(report).encode()
    path = tmp_path / counting.POINT_REPORT
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)

    def git(repository: Path, *args: str) -> bytes:
        assert repository == tmp_path
        if args[0] == "show":
            assert args == ("show", f"HEAD:{counting.POINT_REPORT}")
            return raw
        if args[0] == "log":
            assert args[-1] == counting.POINT_REPORT
            return (PUBLICATION + "\n").encode()
        if args[0] == "cat-file":
            assert args[-1] == report["source_commit"]
            return b"commit\n"
        assert args == ("merge-base", "--is-ancestor", report["source_commit"], "HEAD")
        return b""

    monkeypatch.setattr(counting, "_git", git)
    return report, raw


def test_committed_point_bytes_keep_publication_and_execution_distinct(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report, _ = saved_fixture(tmp_path, monkeypatch)
    actual, identity = counting.read_point_report(tmp_path)
    assert actual == report
    assert identity == {
        "path": counting.POINT_REPORT,
        "publication_commit": PUBLICATION,
        "point_source_commit": POINT_SOURCE,
    }


@pytest.mark.parametrize(
    "defect",
    [
        "dirty",
        "missing_git",
        "bad_commit",
        "schema",
        "axis",
        "age",
        "population",
        "point_status",
    ],
)
def test_point_source_admission_refuses_changed_or_uncommitted_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    report, _ = saved_fixture(tmp_path, monkeypatch)
    path = tmp_path / counting.POINT_REPORT
    if defect == "dirty":
        path.write_bytes(path.read_bytes() + b"\n")
    elif defect == "missing_git":

        def missing(*args: Any) -> bytes:
            raise subprocess.CalledProcessError(128, "git show")

        monkeypatch.setattr(counting, "_git", missing)
    else:
        if defect == "bad_commit":
            report["source_commit"] = "not-a-commit"
        elif defect == "schema":
            report["schema_version"] = "other"
        elif defect == "axis":
            report["taxa"].reverse()
        elif defect == "age":
            report["age_unit"] = "uncalibrated BP"
        elif defect == "population":
            report["groups"].pop()
        else:
            report["groups"][0]["status"] = "nonconverged"
        raw = json.dumps(report).encode()
        path.write_bytes(raw)
        original = counting._git
        monkeypatch.setattr(
            counting,
            "_git",
            lambda repo, *args: raw if args[0] == "show" else original(repo, *args),
        )
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        counting.read_point_report(tmp_path)


@pytest.mark.parametrize(
    "key",
    ["groups", "cores", "unmatched", "scientific_inputs", "original_source_epochs"],
)
def test_native_metadata_binding_refuses_any_changed_input_family(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str
) -> None:
    report = fixture_report()
    source = admitted(report)
    monkeypatch.setattr(cohort, "load_groups", lambda repository: source)
    counting.authenticate_inputs(tmp_path, report)
    if key == "groups":
        report[key][0]["sites"][0]["projected_counts"][0] += 1
    elif key == "cores":
        report[key][0]["response_PPE_times_K"][0] = 2.0
    elif key == "original_source_epochs":
        report[key]["swedish"] = "different"
    else:
        report[key].append({"unexpected": True})
    with pytest.raises(ValueError, match="differ"):
        counting.authenticate_inputs(tmp_path, report)


def test_count_only_outcomes_preserve_empty_sets_and_refusals() -> None:
    report = fixture_report()
    report["groups"][2]["sites"][0]["taxon_measured"][0] = False
    report["groups"][3]["sites"][0]["projected_counts"] = [0, 0]
    rows = counting.evaluate(report)
    assert len(rows) == 13
    assert rows[0]["counting_set"]["status"] == "nonempty"
    assert rows[1]["counting_set"]["status"] == "empty"
    assert rows[1]["counting_set"]["cover_lower_exact"] is None
    assert rows[2]["status"] == "refused" and rows[2]["counting_set"] is None
    assert rows[3]["counting_set"]["excluded_zero_total_site_indices"] == (0,)
    assert rows[0]["sites"] is report["groups"][0]["sites"]


def test_fatal_failure_leaves_remaining_rows_explicitly_unrun(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("controlled execution failure")

    monkeypatch.setattr(multisite_counting, "multisite_two_taxon_counting_set", fail)
    rows = counting.evaluate(fixture_report())
    assert rows[0]["status"] == "fatal"
    assert all(row["status"] == "not_run" for row in rows[1:])


@pytest.mark.parametrize("changed_raw", [False, True])
def test_terminal_consumer_uses_saved_counts_and_checks_raw_integrity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed_raw: bool
) -> None:
    report, _ = saved_fixture(tmp_path, monkeypatch)
    raw = b"controlled primary data\n"
    source = tmp_path / "data" / "original.csv"
    source.parent.mkdir()
    source.write_bytes(raw)
    report["scientific_inputs"] = [
        {
            "path": "data/original.csv",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    ]
    point_identity = {
        "path": counting.POINT_REPORT,
        "publication_commit": PUBLICATION,
        "point_source_commit": POINT_SOURCE,
    }
    monkeypatch.setattr(
        counting, "read_point_report", lambda repository: (report, point_identity)
    )
    monkeypatch.setattr(counting, "_revision", lambda repository: COUNT_SOURCE)
    source_admission = admitted(report)
    monkeypatch.setattr(cohort, "load_groups", lambda repository: source_admission)
    if changed_raw:
        source.write_bytes(b"changed raw data\n")
    output = tmp_path / "artifacts" / "counting" / "report.json"
    output.parent.mkdir(parents=True)
    monkeypatch.setattr(
        sys,
        "argv",
        ["counting", "--repository", str(tmp_path), "--output", str(output)],
    )
    if changed_raw:
        with pytest.raises(ValueError, match="source identity mismatch"):
            counting.main()
        assert not output.exists()
    else:
        with pytest.raises(SystemExit) as exit_status:
            counting.main()
        assert exit_status.value.code == 0
        actual = json.loads(output.read_bytes())
        assert actual["source_commit"] == COUNT_SOURCE
        assert actual["point_report"] == point_identity
        assert actual["status_counts"] == {"computed": 13}
        assert actual["set_status_counts"] == {"nonempty": 12, "empty": 1}
        assert actual["unmatched"] == report["unmatched"]
        assert actual["new_point_fits"] == actual["new_kernel_evaluations"] == 0
        assert actual["simultaneous_across_windows_claimed"] is False
        assert actual["sampling_calibration_established"] is False
        assert output.stat().st_size <= 1024**2


def test_source_module_alias_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside canonical source"):
        counting._revision(tmp_path)
