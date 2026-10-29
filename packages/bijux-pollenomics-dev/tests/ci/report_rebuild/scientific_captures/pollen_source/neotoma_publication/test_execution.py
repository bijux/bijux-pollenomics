"""Preserve native failures, source import roles, citation limits and exact metadata bridges."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any
import unittest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source.neotoma_publication import (
    execution as subject,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source.neotoma_publication import (
    transport,
)

ROOT = next(
    p
    for p in Path(__file__).resolve().parents
    if (p / "pyproject.toml").is_file() and (p / "configs/pytest.ini").is_file()
)


class ExecutionControls(unittest.TestCase):
    def setUp(self) -> None:
        self.root = ROOT / Path(transport.CAPTURE).parent
        self.capture = json.loads((ROOT / transport.CAPTURE).read_bytes())

    def load(self, name: str) -> Any:
        return json.loads((self.root / name).read_bytes())

    def test_both_actual_histories_and_failure_inflation_refusals(self) -> None:
        for label, expected in transport.PLANS.items():
            refs = self.capture["executions"][label]["execution_members"]
            names = [
                "plan.json",
                "terminal.json",
                "neotoma-publication-terminal.json"
                if label == "production"
                else "neotoma-publication-observer-terminal.json",
                "runtime-custody-terminal.json",
            ]
            records = [self.load(refs[name]) for name in names]
            subject.validate_history(
                *records,
                label=label,
                candidate=transport.CANDIDATE,
                plan_sha256=expected,
            )
            for case in (
                "whole",
                "bool",
                "missing_stage",
                "stage_exit",
                "timed_out",
                "candidate",
                "plan",
                "custody",
                "runtime",
                "resource",
                "stage_argv",
                "checker",
            ):
                plan, common, inner, outer = records
                common, inner, outer = (
                    deepcopy(common),
                    deepcopy(inner),
                    deepcopy(outer),
                )
                if case == "whole":
                    common["actual_exit"] = 0 if label == "production" else 1
                elif case == "bool":
                    common["actual_exit"] = bool(common["actual_exit"])
                elif case == "missing_stage":
                    common["stages"].pop()
                elif case == "stage_exit":
                    common["stages"][0]["actual_exit"] = 1
                elif case == "timed_out":
                    common["stages"][0]["timed_out"] = True
                elif case == "candidate":
                    outer["source_candidate"] = "foreign"
                elif case == "plan":
                    inner["plan_sha256"] = "0" * 64
                elif case == "custody":
                    common["after_pin_mismatches"] = ["changed"]
                elif case == "runtime":
                    outer["after_runtime_error"] = "changed"
                elif case == "resource":
                    outer["completed_elapsed_seconds"] = float("inf")
                elif case == "stage_argv":
                    common["stages"][0]["argv"].append("--foreign")
                elif label == "production":
                    inner["tracked_byte_comparisons"][0]["checker_actual_exit"] = 0
                else:
                    outer["resource_bounds_met"] = False
                with (
                    self.subTest(label=label, case=case),
                    self.assertRaises(ReportRebuildError),
                ):
                    subject.validate_history(
                        plan,
                        common,
                        inner,
                        outer,
                        label=label,
                        candidate=transport.CANDIDATE,
                        plan_sha256=expected,
                    )

    def test_real_source_origin_roles_and_scope_refusals(self) -> None:
        refs = self.capture["executions"]["production"]["execution_members"]
        plan = self.load(refs["plan.json"])
        pins = {row["path"]: row for row in plan["input_pins"]}
        catalog = self.load(
            self.capture["retention_authority_members"][
                "ordered-original-input-identities.json"
            ]
        )
        retained = {row["path"]: row["retained_member"] for row in catalog}
        for kind in ("publication", "doi"):
            receipt = self.load(refs[kind + "-source-execution.json"])
            source = (self.root / retained[receipt["source"]["path"]]).read_bytes()
            subject.validate_source_role(kind, source, receipt, pins)
            for case in (
                "source",
                "empty_or_forged",
                "foreign",
                "bool",
                "network",
                "LRA",
            ):
                value = deepcopy(receipt)
                raw = source
                if case == "source":
                    raw += b"\nimport foreign_source\n"
                elif case == "empty_or_forged":
                    value["first_party_origins"] = (
                        []
                        if kind == "publication"
                        else [
                            {
                                "module": "foreign",
                                "path": "/foreign.py",
                                "sha256": "0" * 64,
                                "bytes": 0,
                            }
                        ]
                    )
                elif case == "foreign":
                    value["kind"] = "foreign"
                elif case == "bool":
                    value["source_exit"] = False
                elif case == "network":
                    value["counters"]["network_attempts"] = 1
                else:
                    value["counters"]["LRA_implementation_function_calls"] = 1
                with (
                    self.subTest(kind=kind, case=case),
                    self.assertRaises(ReportRebuildError),
                ):
                    subject.validate_source_role(kind, raw, value, pins)

    def test_exact_actual_two_leaf_bridges_and_refusal_denominators(self) -> None:
        refs = self.capture["executions"]["observation"]["execution_members"]
        review = self.load(refs["independent-publication-review.json"])
        subject.validate_review(review)
        for key, value in (
            ("used_datasets", 84),
            ("reviewed_DOI_pairs", 14),
            ("publication_ready", True),
            ("lra_accepted_samples", True),
            ("original_whole_exit", 0),
            ("current_observer_only_execution", False),
            (
                "historical_policy_and_current_policy_rights_or_human_equivalence_claimed",
                True,
            ),
        ):
            changed = deepcopy(review)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ReportRebuildError):
                subject.validate_review(changed)
        source_refs = self.capture["executions"]["production"]["execution_members"]
        catalog = self.load(
            self.capture["retention_authority_members"][
                "ordered-original-input-identities.json"
            ]
        )
        retained = {row["path"]: row["retained_member"] for row in catalog}
        for comparison, name in zip(
            review["whole_product_comparisons"],
            (transport.BASE + "report.json", transport.BASE + "doi-review.json"),
            strict=True,
        ):
            generated = self.load(source_refs["producer/" + name])
            original_repository = self.load(source_refs["plan.json"])["repository"]
            governed = self.load(retained[str(Path(original_repository) / name)])
            delta = comparison["sole_metadata_delta"]
            subject.metadata_bridge(
                generated,
                governed,
                delta["field"],
                delta["governed"],
                delta["generated"],
            )
            for case in ("extra", "count", "ordered", "metadata"):
                changed = deepcopy(generated)
                if case == "extra":
                    changed["unsupported_rights_claim"] = True
                elif case == "count":
                    changed[
                        "used_dataset_count"
                        if name.endswith("/report.json")
                        else "reviewed_dataset_count"
                    ] = True
                elif case == "ordered":
                    changed = dict(reversed(list(changed.items())))
                else:
                    if name.endswith("/report.json"):
                        changed["provider_policy"]["governed_review_sha256"] = "0" * 64
                    else:
                        changed["attribution_ledger_sha256"] = "0" * 64
                with (
                    self.subTest(product=name, case=case),
                    self.assertRaises(ReportRebuildError),
                ):
                    subject.metadata_bridge(
                        changed,
                        governed,
                        delta["field"],
                        delta["governed"],
                        delta["generated"],
                    )
