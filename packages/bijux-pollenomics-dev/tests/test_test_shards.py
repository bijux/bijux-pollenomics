"""Complete-universe and fail-closed contracts for bounded CI test jobs."""

from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from bijux_pollenomics_dev.ci.test_shards.__main__ import main, verify_receipts
from bijux_pollenomics_dev.ci.test_shards.plugin import shard_for

pytest_plugins = ["pytester"]


def _receipts(root: Path, count: int = 3) -> list[Path]:
    universe = [f"test_evidence.py::test_case[{index:03}]" for index in range(100)]
    paths = []
    for index in range(count):
        selected = [node for node in universe if shard_for(node, count) == index]
        path = root / f"shard-{index}.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "pytest-shard-receipt.v1",
                    "revision": "accepted-revision",
                    "index": index,
                    "count": count,
                    "exit_code": 0,
                    "collection_only": False,
                    "universe": universe,
                    "selected": selected,
                    "completed": selected,
                }
            )
        )
        paths.append(path)
    return paths


def test_all_shards_cover_the_universe_exactly_once(tmp_path: Path) -> None:
    assert (
        verify_receipts(_receipts(tmp_path), count=3, revision="accepted-revision")
        == 100
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "failed",
        "unfinished",
        "revision",
        "collection",
        "overlap",
        "collection_only",
        "missing_execution_mode",
    ],
)
def test_invalid_or_incomplete_shards_are_refused(
    tmp_path: Path, mutation: str
) -> None:
    paths = _receipts(tmp_path)
    if mutation == "missing":
        paths.pop()
    elif mutation == "duplicate":
        paths[1] = paths[0]
    else:
        row = json.loads(paths[0].read_text())
        if mutation == "failed":
            row["exit_code"] = 1
        elif mutation == "unfinished":
            row["completed"] = row["completed"][:-1]
        elif mutation == "revision":
            row["revision"] = "different-revision"
        elif mutation == "collection":
            row["universe"] = row["universe"][:-1]
        elif mutation == "collection_only":
            row["collection_only"] = True
        elif mutation == "missing_execution_mode":
            row.pop("collection_only")
        else:
            row["selected"] += json.loads(paths[1].read_text())["selected"][:1]
        paths[0].write_text(json.dumps(row))
    with pytest.raises(ValueError):
        verify_receipts(paths, count=3, revision="accepted-revision")


@pytest.mark.parametrize("mutation", [None, "revision", "universe", "collection_only"])
def test_independent_collection_plan_is_authoritative(
    tmp_path: Path, mutation: str | None
) -> None:
    paths = _receipts(tmp_path)
    plan = json.loads(paths[0].read_text())
    plan.update(count=1, selected=plan["universe"], completed=[], collection_only=True)
    if mutation == "revision":
        plan["revision"] = "different-revision"
    elif mutation == "universe":
        plan["universe"] = [*plan["universe"], "test_missing.py::test_case"]
        plan["selected"] = plan["universe"]
    elif mutation == "collection_only":
        plan["collection_only"] = False
    path = tmp_path / "collection-plan.json"
    path.write_text(json.dumps(plan))
    if mutation is None:
        assert (
            verify_receipts(
                paths,
                count=3,
                revision="accepted-revision",
                expected_universe_file=path,
            )
            == 100
        )
    else:
        with pytest.raises(ValueError, match="independent collection plan"):
            verify_receipts(
                paths,
                count=3,
                revision="accepted-revision",
                expected_universe_file=path,
            )


def test_plugin_preserves_existing_marker_selection(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    pytester.makepyfile("""
        import pytest
        @pytest.mark.parametrize("value", range(24))
        def test_selected(value):
            assert value >= 0
        @pytest.mark.generated_artifacts
        def test_excluded():
            raise AssertionError("existing marker exclusion must be preserved")
    """)
    plan = pytester.path / "artifacts" / "collection-plan.json"
    collected = pytester.runpytest(
        "-p",
        "bijux_pollenomics_dev.ci.test_shards.plugin",
        "-m",
        "not generated_artifacts",
        "--collect-only",
        f"--bijux-shard-receipt={plan}",
    )
    assert collected.ret == 0
    receipts = []
    for index in range(2):
        path = pytester.path / "artifacts" / f"shard-{index}.json"
        result = pytester.runpytest(
            "-p",
            "bijux_pollenomics_dev.ci.test_shards.plugin",
            "-m",
            "not generated_artifacts",
            "--bijux-shard-count=2",
            f"--bijux-shard-index={index}",
            f"--bijux-shard-receipt={path}",
        )
        assert result.ret == 0
        receipts.append(path)
    assert (
        verify_receipts(
            receipts, count=2, revision="local-unattested", expected_universe_file=plan
        )
        == 24
    )


@pytest.mark.parametrize("passing", [True, False])
def test_junit_attests_only_successful_reconciliation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, passing: bool
) -> None:
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "artifacts" / "receipts"
    root.mkdir(parents=True)
    paths = _receipts(root)
    for index, path in enumerate(paths):
        destination = root / str(index) / "shard-receipt.json"
        destination.parent.mkdir()
        path.rename(destination)
    if not passing:
        (root / "1" / "shard-receipt.json").unlink()
    junit = tmp_path / "artifacts" / "reconciliation.junit.xml"
    monkeypatch.setattr(
        "sys.argv",
        [
            "test_shards",
            "--receipt-root",
            str(root),
            "--count",
            "3",
            "--revision",
            "accepted-revision",
            "--junit-output",
            str(junit),
        ],
    )
    if passing:
        assert main() == 0
        suite = ET.parse(junit).getroot()
        assert suite.attrib["tests"] == "1"
        assert suite.attrib["failures"] == "0"
        assert "100 selected tests" in suite.find("testcase/system-out").text
    else:
        with pytest.raises(ValueError):
            main()
        assert not junit.exists()
