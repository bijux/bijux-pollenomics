"""Synthetic SEAD method/type projection and publication refusal contracts."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any
import unittest

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.sead import analysis_value_methods as core


def fixture() -> tuple[
    dict[str, Any],
    list[dict[str, str]],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    row = {
        "country_code": "SE",
        "component_kind": "untyped_source_text",
        "parent_value_state": "reported",
        "value_class_id": "12",
        "value_class_name": "Inferred growth year ≥",
        "value_type_id": "6",
        "value_type_name": "Year",
        "source_unit_id": "8",
        "source_unit_name": "Years",
        "unit_status": "source_native_linked",
        "parent_count": "3",
    }
    census = {
        "schema_version": "sead-analysis-value-component-closure.v1",
        "row_count": 1,
        "summary": {
            "component_counts": {"untyped_source_text": 3},
            "country_parent_counts": {"SE": 3},
            "parent_count": 3,
            "typed_parent_count": 0,
            "untyped_parent_count": 3,
            "unit_status_counts": {"source_native_linked": 3},
        },
    }

    def table(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {"table": name, "rows": rows}

    classes = table(
        "tbl_value_classes",
        [
            {
                "value_class_id": 12,
                "name": "Inferred growth year ≥",
                "value_type_id": 6,
                "method_id": 10,
            }
        ],
    )
    types = table(
        "tbl_value_types",
        [{"value_type_id": 6, "name": "Year", "base_type": "integer", "unit_id": 8}],
    )
    methods = table(
        "tbl_methods", [{"method_id": 10, "method_name": "Dendrochronology"}]
    )
    units = table("tbl_units", [{"unit_id": 8, "unit_name": "Years"}])
    return census, [row], classes, types, methods, units


class CoverageContracts(unittest.TestCase):
    def test_absent_component_retains_declared_type_method_and_unit(self) -> None:
        report = core.project(*fixture())
        self.assertEqual(report["untyped_parent_count"], 3)
        self.assertEqual(report["source_method_counts"], {"10": 3})
        self.assertEqual(report["source_unit_linked_untyped_count"], 3)
        self.assertEqual(report["groups"][0]["declared_base_type"], "integer")
        self.assertEqual(report["groups"][0]["value_type_id"], 6)
        self.assertEqual(report["groups"][0]["value_type_name"], "Year")
        self.assertEqual(report["eligible_event_count"], 0)

    def test_missing_method_definition_refused(self) -> None:
        args = fixture()
        args[4]["rows"] = []
        with self.assertRaisesRegex(ValueError, "missing source method"):
            core.project(*args)

    def test_class_type_or_name_drift_refused(self) -> None:
        for change in ("type", "name"):
            args = fixture()
            if change == "type":
                args[2]["rows"][0]["value_type_id"] = 8
            else:
                args[1][0]["value_class_name"] = "Different"
            with self.assertRaisesRegex(ValueError, "class/type declaration differs"):
                core.project(*args)

    def test_boolean_class_type_foreign_key_cannot_match_integer_one(self) -> None:
        args = fixture()
        args[1][0]["value_type_id"] = "1"
        args[2]["rows"][0]["value_type_id"] = True
        args[3]["rows"][0]["value_type_id"] = 1
        with self.assertRaisesRegex(ValueError, "class/type declaration differs"):
            core.project(*args)

    def test_unit_loss_and_invalid_unit_refused(self) -> None:
        for change in ("link", "definition"):
            args = fixture()
            if change == "link":
                args[1][0]["source_unit_id"] = ""
            else:
                args[5]["rows"] = []
            with self.assertRaisesRegex(ValueError, "source unit definition differs"):
                core.project(*args)

    def test_method_is_not_inferred_from_native_display(self) -> None:
        args = fixture()
        args[2]["rows"][0]["method_id"] = 14
        with self.assertRaisesRegex(ValueError, "missing source method"):
            core.project(*args)

    def test_duplicate_group_and_count_loss_refused(self) -> None:
        args = fixture()
        args[1].append(copy.deepcopy(args[1][0]))
        with self.assertRaisesRegex(ValueError, "duplicate upstream census group"):
            core.project(*args)
        args = fixture()
        args[1][0]["parent_count"] = "2"
        with self.assertRaisesRegex(ValueError, "upstream census totals differ"):
            core.project(*args)

    def test_noncanonical_count_and_country_refused(self) -> None:
        args = fixture()
        args[1][0]["parent_count"] = "03"
        with self.assertRaisesRegex(
            ValueError, "noncanonical upstream count or identity"
        ):
            core.project(*args)
        args = fixture()
        args[1][0]["value_class_id"] = "012"
        with self.assertRaisesRegex(
            ValueError, "noncanonical upstream count or identity"
        ):
            core.project(*args)
        args = fixture()
        args[1][0]["country_code"] = "DK"
        with self.assertRaisesRegex(ValueError, "unexpected country"):
            core.project(*args)


def test_method_member_requires_two_matching_native_receipts() -> None:
    row = {
        "path": core.METHODS_MEMBER,
        "sha256": core.METHODS_SHA256,
        "byte_count": 10954,
    }
    admission = {"copied_files": [row]}
    manifest = {"files": [row]}
    core._require_methods_member(admission, manifest)
    for altered in (
        {"copied_files": [row, row]},
        {"copied_files": [{**row, "byte_count": 10955}]},
    ):
        with pytest.raises(ValueError, match="method table custody"):
            core._require_methods_member(altered, manifest)
    with pytest.raises(ValueError, match="method table custody"):
        core._require_methods_member(admission, {"files": []})


def test_postread_source_change_preserves_absent_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path
    (repository / "artifacts").mkdir()
    source = repository / "source.json"
    source.write_bytes(b"changed")
    monkeypatch.setattr(
        core,
        "build_report",
        lambda _repository: (
            {"source_readset_sha256": {"source.json": "0" * 64}},
            b"rows\n",
        ),
    )
    target = repository / "artifacts" / "coverage"
    with pytest.raises(ValueError, match="source changed before method publication"):
        core.run(repository, target)
    assert not target.exists()
    assert not target.with_name("coverage.stage").exists()


def test_symlink_output_ancestor_refused_before_producer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (repository / "artifacts").mkdir()
    (repository / "artifacts" / "linked").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(
        core, "build_report", lambda _repository: pytest.fail("producer called")
    )
    with pytest.raises(ReportRebuildError, match="artifact|symlink|real"):
        core.run(repository, repository / "artifacts" / "linked" / "coverage")
    assert list(outside.iterdir()) == []


def test_existing_output_preserved_before_producer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path
    (repository / "artifacts").mkdir()
    target = repository / "artifacts" / "coverage"
    target.mkdir()
    retained = target / "report.json"
    retained.write_bytes(b"prior verified report")
    monkeypatch.setattr(
        core, "build_report", lambda _repository: pytest.fail("producer called")
    )
    with pytest.raises(ReportRebuildError, match="exists|absent"):
        core.run(repository, target)
    assert retained.read_bytes() == b"prior verified report"


if __name__ == "__main__":
    unittest.main()
