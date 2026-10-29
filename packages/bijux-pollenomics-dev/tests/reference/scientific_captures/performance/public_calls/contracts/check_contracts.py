"""Pure controlled negatives for retained measurement publication, without timing."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from contracts import (
    EXECUTION_CANDIDATE,
    THREADS,
    WORKERS,
    WORKLOADS,
    exact,
    measurement_projection,
    pin,
    relative_name,
    scientific_digest,
)
from observe import independent_boundary

A = Path(__file__).absolute().parent


class PublicationControls(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(
            prefix="controlled-publication-", dir=A / "preflight"
        )
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def fixture(self):
        observations = []
        for workload in WORKLOADS:
            contract = (
                {"sites": list("abcdef"), "taxa": list("0123456789"), "draws": 1024}
                if workload == WORKLOADS[0]
                else {
                    "logical_calls": 128,
                    "physical_fixture": 1,
                    "optimizer_search_convergence": False,
                }
            )
            value = (
                {"controlled_fixture": [None, 0, False, -0.0]}
                if workload == WORKLOADS[0]
                else [{"cover": [0.0, None]}] * 128
            )
            for worker in WORKERS:
                folder = self.root / workload / f"worker-{worker}"
                folder.mkdir(parents=True)
                (folder / (workload + ".json")).write_text(json.dumps(value))
                warm = [0.125] * 7 if worker < 3 else []
                row = {
                    "workload": workload,
                    "contract": contract,
                    "input_identity": "controlled-input",
                    "first_public_call_seconds": 0.25,
                    "warm_public_call_seconds": warm,
                    "scientific_output_sha256": scientific_digest(value),
                    "profile_is_unprofiled_hotspot_evidence": False,
                    "construction_loading_conversion_seconds": 0.5,
                    "output_projection_seconds": [0.01] * (8 if worker < 3 else 1),
                    "diagnostic_profile_total_seconds": 1.0,
                    "measured_unprofiled_boundaries": [],
                    "warnings": [],
                }
                data = {
                    "candidate": EXECUTION_CANDIDATE,
                    "worker": worker,
                    "rows": [row],
                    "R_or_compiler_executed": False,
                    "native_thread_counters_observed": False,
                    "thread_limits": THREADS,
                    "peak_RSS_native": 1024,
                    "rss_units": "bytes",
                    "worker_body_seconds": 2.0,
                }
                (folder / "measurement.json").write_text(json.dumps(data))
                if worker < 3:
                    observations.append(
                        {
                            "worker": worker,
                            "workload": workload,
                            "first_seconds": 0.25,
                            "warm_seconds": warm,
                            "warm_median_seconds": 0.125,
                            "warm_min_seconds": 0.125,
                            "warm_max_seconds": 0.125,
                            "whole_worker_peak_RSS_bytes": 1024,
                        }
                    )
        scaling = {
            "rows": [
                {"mode": mode, "workers": workers}
                for mode, workers in zip(
                    ["sequential", "parallel"] * 2,
                    [[100, 101], [102, 103]] * 2,
                    strict=True,
                )
            ]
        }
        (self.root / "scaling.json").write_text(json.dumps(scaling))
        return {
            "observations": observations,
            "all_worker_boundary_assessments": {},
            "qualified_all_three_worker_hotspots": [],
            "scaling": scaling,
            "thread_scope": "requested only",
            "scope": "pure controlled fixture",
            "remaining": "no admission",
        }

    def mutate(self, workload, worker, action):
        path = self.root / workload / f"worker-{worker}/measurement.json"
        body = json.loads(path.read_bytes())
        action(body)
        path.write_text(json.dumps(body))

    def test_preserves_all_six_first_and_seven_warm_samples(self):
        report = measurement_projection(self.root, {}, self.fixture())
        self.assertEqual(len(report["observations"]), 6)
        self.assertTrue(
            all(len(row["warm_seconds"]) == 7 for row in report["observations"])
        )
        self.assertIs(report["new_cpp_allowed"], False)

    def test_missing_warm_sample_refuses(self):
        review = self.fixture()
        self.mutate(
            WORKLOADS[0],
            0,
            lambda body: body["rows"][0]["warm_public_call_seconds"].pop(),
        )
        with self.assertRaisesRegex(ValueError, "timing membership"):
            measurement_projection(self.root, {}, review)

    def test_false_thread_counter_claim_refuses(self):
        review = self.fixture()
        self.mutate(
            WORKLOADS[0],
            0,
            lambda body: body.update(native_thread_counters_observed=True),
        )
        with self.assertRaisesRegex(ValueError, "thread scope"):
            measurement_projection(self.root, {}, review)

    def test_diagnostic_profile_cannot_become_hotspot_evidence(self):
        review = self.fixture()
        self.mutate(
            WORKLOADS[0],
            0,
            lambda body: body["rows"][0].update(
                profile_is_unprofiled_hotspot_evidence=True
            ),
        )
        with self.assertRaisesRegex(ValueError, "profile promoted"):
            measurement_projection(self.root, {}, review)

    def test_computational_repetitions_cannot_become_sites(self):
        review = self.fixture()
        self.mutate(
            WORKLOADS[1],
            0,
            lambda body: body["rows"][0]["contract"].update(physical_fixture=128),
        )
        with self.assertRaisesRegex(ValueError, "repetitions became"):
            measurement_projection(self.root, {}, review)

    def test_changed_scientific_output_refuses(self):
        review = self.fixture()
        path = self.root / WORKLOADS[0] / "worker-0" / (WORKLOADS[0] + ".json")
        path.write_text('{"controlled_fixture":[null,1,false,-0.0]}')
        with self.assertRaisesRegex(ValueError, "output digest"):
            measurement_projection(self.root, {}, review)

    def test_warm_summary_cannot_select_favorable_repeat(self):
        review = self.fixture()
        review["observations"][0]["warm_median_seconds"] = 0.001
        with self.assertRaisesRegex(ValueError, "six-observation"):
            measurement_projection(self.root, {}, review)

    def test_changed_scaling_process_membership_refuses(self):
        review = self.fixture()
        altered = deepcopy(review["scaling"])
        altered["rows"][1]["workers"] = [102]
        (self.root / "scaling.json").write_text(json.dumps(altered))
        review["scaling"] = altered
        with self.assertRaisesRegex(ValueError, "process membership"):
            measurement_projection(self.root, {}, review)

    def test_zero_null_boolean_and_integer_float_identity_remain_distinct(self):
        for a, b in [(None, 0), (False, 0), (0, 0.0), (-0.0, 0.0)]:
            self.assertFalse(exact(a, b))

    def test_unconfined_member_names_refuse(self):
        for value in ("", "../outside", "/absolute", "a//b", "a/./b"):
            with self.assertRaises(ValueError):
                relative_name(value)

    def test_symlinked_source_refuses(self):
        source = self.root / "source"
        source.write_text("controlled")
        linked = self.root / "linked"
        linked.symlink_to(source)
        with self.assertRaises(ValueError):
            pin(linked)

    def test_separate_boundary_conservative_share_and_overhead(self):
        timings = {
            "baseline": [1.0, 1.0, 1.0],
            "passthrough": [1.0, 1.0, 1.0],
            "instrumented": [1.0, 1.0, 1.0],
            "inside": [0.6, 0.6, 0.6],
            "clock_cost": [0.01, 0.01, 0.01],
        }
        admitted = independent_boundary(timings)
        self.assertEqual(admitted["conservative_measured_boundary_share"], 0.59)
        self.assertIs(admitted["qualified_measured_hotspot"], True)
        self.assertIs(admitted["allows_compilation"], False)
        timings["instrumented"] = [2.0, 2.0, 2.0]
        self.assertIs(
            independent_boundary(timings)["qualified_measured_hotspot"], False
        )

    def test_invalid_boundary_membership_and_inside_time_refuse(self):
        timings = {
            "baseline": [1.0] * 3,
            "passthrough": [1.0] * 3,
            "instrumented": [1.0] * 3,
            "inside": [2.0] * 3,
            "clock_cost": [0.0] * 3,
        }
        with self.assertRaises(ValueError):
            independent_boundary(timings)
        timings["inside"] = [0.5]
        with self.assertRaises(ValueError):
            independent_boundary(timings)

    def test_public_transport_wrong_capture_identity_refuses_before_reading(self):
        module_path = (
            A
            / "proposal/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/retained_performance.py"
        )
        spec = importlib.util.spec_from_file_location(
            "controlled_retained_performance", module_path
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        path = self.root / module.CAPTURE
        path.parent.mkdir(parents=True)
        path.write_text('{"controlled":true}')
        with self.assertRaisesRegex(ValueError, "capture identity"):
            module.validated_capture(self.root, capture_sha256="0" * 64)

    def consumer(self):
        module_path = (
            A
            / "proposal/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/retained_performance.py"
        )
        spec = importlib.util.spec_from_file_location(
            "controlled_writer_boundary", module_path
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_linked_descendant_directory_refuses_without_writing_outside(self):
        module = self.consumer()
        output, outside = self.root / "owned", self.root / "outside"
        output.mkdir()
        outside.mkdir()
        (output / "docs").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "target or ancestor"):
            module._output_targets(output)
        self.assertEqual(list(outside.iterdir()), [])

    def test_existing_final_output_refuses_before_either_write(self):
        module = self.consumer()
        output = self.root / "owned"
        existing = output / module.REPORT_ROOT / "README.md"
        existing.parent.mkdir(parents=True)
        existing.write_text("user content")
        with self.assertRaisesRegex(ValueError, "already exists"):
            module._output_targets(output)
        self.assertEqual(existing.read_text(), "user content")
        self.assertFalse((existing.parent / "report.json").exists())

    def test_unlinked_new_targets_are_exact_and_do_not_create_files(self):
        module = self.consumer()
        output = self.root / "owned"
        self.assertEqual(
            module._output_targets(output),
            (
                output / module.REPORT_ROOT / "report.json",
                output / module.REPORT_ROOT / "README.md",
            ),
        )
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
