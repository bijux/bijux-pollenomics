"""Refuse native-probe misclassification and any relabelled bootstrap custody."""

from __future__ import annotations

import copy
import importlib.machinery
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    NATIVE_PROBES,
    OBSERVER_PROBES,
    SOURCE,
    digest,
    json_value,
    namespace_snapshot,
    native_origin,
    pin,
    verify_base_namespaces,
)
from prepare import (
    OUTER_SHA,
    PLAN_SHA,
    RETAINED,
    bootstrap_contract,
    observation_output,
    production_pins,
)
from run import completed_receipt


class Guards(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = tempfile.TemporaryDirectory(
            prefix="boundary-", dir=SOURCE / "preflight"
        )
        self.root = Path(self.storage.name)

    def tearDown(self) -> None:
        self.storage.cleanup()

    def test_actual_module_resolution_distinguishes_pure_version_and_native_main(
        self,
    ) -> None:
        self.assertEqual(NATIVE_PROBES["mypy.main"], "mypy")
        self.assertNotIn("mypy.version", NATIVE_PROBES)
        self.assertEqual(OBSERVER_PROBES["mypy.version"], "mypy")
        site = RETAINED / "environment/lib/python3.11/site-packages"
        finder = importlib.machinery.FileFinder(
            str(site / "mypy"),
            (
                importlib.machinery.ExtensionFileLoader,
                importlib.machinery.EXTENSION_SUFFIXES,
            ),
            (importlib.machinery.SourceFileLoader, importlib.machinery.SOURCE_SUFFIXES),
        )
        main = finder.find_spec("mypy.main")
        version = finder.find_spec("mypy.version")
        assert main and main.origin and version and version.origin
        self.assertTrue(main.origin.endswith("main.cpython-311-darwin.so"))
        self.assertTrue(version.origin.endswith("version.py"))
        self.assertEqual(native_origin(Path(main.origin), site)["path"], main.origin)
        with self.assertRaises(ValueError):
            native_origin(Path(version.origin), site)

    def test_native_probe_refuses_alias_wrong_abi_and_outside_site(self) -> None:
        site = self.root / "site"
        site.mkdir()
        path = site / "core.cpython-312-darwin.so"
        path.write_bytes(b"controlled")
        with self.assertRaises(ValueError):
            native_origin(path, site)
        outside = self.root / "core.cpython-311-darwin.so"
        outside.write_bytes(b"controlled")
        with self.assertRaises(ValueError):
            native_origin(outside, site)
        link = site / outside.name
        link.symlink_to(outside)
        with self.assertRaises(ValueError):
            native_origin(link, site)

    def test_exact_original_three_production_zero_and_whole_one(self) -> None:
        self.assertEqual(digest(RETAINED / "plan.json"), PLAN_SHA)
        self.assertEqual(
            digest(RETAINED / "runtime-bootstrap-terminal.json"), OUTER_SHA
        )
        bootstrap_contract(
            json_value(RETAINED / "plan.json"),
            json_value(RETAINED / "terminal.json"),
            json_value(RETAINED / "runtime-bootstrap-terminal.json"),
        )

    def test_production_failure_or_boolean_is_not_a_pass(self) -> None:
        plan = json_value(RETAINED / "plan.json")
        common = json_value(RETAINED / "terminal.json")
        outer = json_value(RETAINED / "runtime-bootstrap-terminal.json")
        for value in (1, False, 0.0):
            bad = copy.deepcopy(common)
            bad["stages"][0]["actual_exit"] = value
            with self.assertRaises(ValueError):
                bootstrap_contract(plan, bad, outer)

    def test_original_failure_and_argv_cannot_be_relabelled(self) -> None:
        plan = json_value(RETAINED / "plan.json")
        common = json_value(RETAINED / "terminal.json")
        outer = json_value(RETAINED / "runtime-bootstrap-terminal.json")
        for change in ("whole", "observer", "argv", "pins"):
            bad = copy.deepcopy(common)
            if change == "whole":
                bad["actual_exit"] = 0
            elif change == "observer":
                bad["stages"][3]["actual_exit"] = 0
            elif change == "argv":
                bad["stages"][0]["argv"].append("unqualified")
            else:
                bad["after_pin_mismatches"] = ["changed"]
            with self.assertRaises(ValueError):
                bootstrap_contract(plan, bad, outer)

    def test_materialized_namespace_refuses_added_module_or_empty_directory(
        self,
    ) -> None:
        captured = namespace_snapshot(self.root, [])
        new = self.root / "shadow.py"
        new.write_bytes(b"controlled")
        with self.assertRaises(ValueError):
            verify_base_namespaces([captured])
        new.unlink()
        new.mkdir()
        with self.assertRaises(ValueError):
            verify_base_namespaces([captured])

    def test_inclusive_fresh_receipt_output_bounds(self) -> None:
        (self.root / "log").write_bytes(b"controlled")
        raw, total = completed_receipt(self.root, {"actual_exit": 0}, 10000)
        self.assertEqual(total, 10 + len(raw))
        self.assertEqual(
            completed_receipt(self.root, {"actual_exit": 0}, total)[1], total
        )
        with self.assertRaises(ValueError):
            completed_receipt(self.root, {"actual_exit": 0}, total - 1)

    def test_actual_all_original_production_files_authenticate_to_terminal(
        self,
    ) -> None:
        rows = production_pins(
            RETAINED,
            json_value(RETAINED / "terminal.json"),
            RETAINED / "terminal.json",
            RETAINED / "runtime-bootstrap-terminal.json",
        )
        self.assertEqual(len(rows), 28526)

    def test_original_products_and_known_final_stdout_refuse_drift(self) -> None:
        common = self.root / "terminal.json"
        common.write_bytes(b"{}")
        outer = self.root / "outer.json"
        outer.write_bytes(b"{}")
        payload = self.root / "payload"
        payload.write_bytes(b"controlled")
        out = self.root / "common-runner.stdout"
        prefix = b'{"stage":"controlled"}\n'
        out.write_bytes(prefix)
        declared = {"products": [pin(payload), pin(out)], "status": "failed"}
        suffix = (
            json.dumps(
                {"terminal": str(common), "sha256": digest(common), "status": "failed"}
            )
            + "\n"
        ).encode()
        out.write_bytes(prefix + suffix)
        self.assertEqual(len(production_pins(self.root, declared, common, outer)), 4)
        payload.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            production_pins(self.root, declared, common, outer)
        payload.write_bytes(b"controlled")
        out.write_bytes(prefix + suffix + b"unreviewed")
        with self.assertRaises(ValueError):
            production_pins(self.root, declared, common, outer)
        out.write_bytes(prefix + suffix)
        (self.root / "extra").write_bytes(b"unreviewed")
        with self.assertRaises(ValueError):
            production_pins(self.root, declared, common, outer)

    def test_new_output_cannot_be_inside_original_runtime_or_held_source(self) -> None:
        for path in (
            RETAINED / "uncreated-observation",
            SOURCE / "uncreated-observation",
        ):
            with self.assertRaises(ValueError):
                observation_output(path)


if __name__ == "__main__":
    unittest.main()
