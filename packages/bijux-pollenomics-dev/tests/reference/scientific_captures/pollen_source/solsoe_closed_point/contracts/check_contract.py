"""Pure controlled joins and isolation refusals; never execute the maintained replay."""

from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
from typing import Any
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    AGES,
    CONTROLS,
    CORE_1981,
    CORE_1983,
    DECLARED,
    OWNER,
    REPLAY,
    REPORT,
    SITE,
    closed_ledger,
    exact,
    expected_closed_report,
    inspect_relations,
    load,
    owner_contract,
    verify_closed_report,
    verify_report,
)
from runtime import alias, check_aliases, profile_guard, qualify_process_snapshot


def fixture() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    controls = []
    for chronology in ("view-a", "view-b"):
        for index, (lab, depth, age, error, isotope) in enumerate(DECLARED):
            native_id = index + 1 + (0 if chronology == "view-a" else 7)
            controls.append(
                {
                    "site_id": SITE,
                    "collection_unit_id": CORE_1983,
                    "chronology_id": chronology,
                    "source_chronology_control_id": native_id,
                    "chronology_control_id": chronology + ":control:" + str(native_id),
                    "source_payload": {
                        "chroncontrolid": native_id,
                        "chroncontroltype": "Radiocarbon",
                        "depth": depth,
                        "geochron": {
                            "geochronid": index + 101,
                            "agetype": "Radiocarbon years BP",
                            "labnumber": lab,
                            "geochronage": age,
                            "geochronerrorolder": error,
                            "geochronerroryounger": error,
                            "delta13c": isotope,
                        },
                    },
                }
            )
    ages = []
    for index, (core, age) in enumerate(
        [(CORE_1981, 8000)] * 54
        + [(CORE_1981, 12000)] * 2
        + [(CORE_1983, 5000)] * 20
        + [(CORE_1981, 5000)] * 16
    ):
        identifier = f"neotoma:sample:{index}"
        ages.append(
            {
                "site_id": SITE,
                "source_age_type": "Calibrated radiocarbon years BP",
                "collection_unit_id": core,
                "source_record_id": identifier,
                "subject_id": identifier,
                "subject_type": "sample",
                "source_age_value": age,
                "source_payload": {
                    "age": age,
                    "agetype": "Calibrated radiocarbon years BP",
                },
            }
        )
    return controls, ages


class Contracts(unittest.TestCase):
    def test_named_owner_boundary(self) -> None:
        original = {
            "owners": [
                {
                    "owner_id": OWNER,
                    "role": "unresolved",
                    "paths": [REPORT],
                    "producer_paths": [REPLAY],
                    "producer_inputs": sorted([AGES, CONTROLS]),
                    "verification": "Original provider/rights history remains unqualified",
                }
            ]
        }
        self.assertEqual(owner_contract(original), original["owners"][0])
        for field, value in (
            ("role", "retained_source"),
            ("paths", []),
            ("producer_paths", []),
            ("producer_inputs", [AGES]),
            ("verification", ""),
        ):
            mutated = deepcopy(original)
            mutated["owners"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                owner_contract(mutated)
        mutated = deepcopy(original)
        mutated["owners"].append(deepcopy(mutated["owners"][0]))
        with self.assertRaises(ValueError):
            owner_contract(mutated)

    def test_positive_declared_join(self) -> None:
        rows = inspect_relations(*fixture())
        self.assertEqual(len(rows["native_sample_ids"]), 92)
        self.assertEqual(len(rows["proxy_ids"]), 76)
        self.assertEqual(len(rows["bounded_proxy_ids"]), 74)
        self.assertEqual(len(rows["native_control_view_ids"]), 14)
        self.assertEqual(len(rows["source_control_numeric_ids"]), 14)
        self.assertEqual(len(rows["native_geochron_numeric_ids"]), 7)

    def test_native_control_and_sample_joins(self) -> None:
        for field, value in (
            ("source_chronology_control_id", True),
            ("chronology_control_id", "other"),
            ("site_id", "other"),
        ):
            controls, ages = fixture()
            controls[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                inspect_relations(controls, ages)
        for field, value in (
            ("subject_id", "other"),
            ("subject_type", "site"),
            ("source_record_id", "generic:1"),
        ):
            controls, ages = fixture()
            ages[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                inspect_relations(controls, ages)
        controls, ages = fixture()
        ages[0]["source_payload"]["age"] = 8001
        with self.assertRaises(ValueError):
            inspect_relations(controls, ages)

    def test_missing_control(self) -> None:
        controls, ages = fixture()
        controls.pop()
        with self.assertRaises(ValueError):
            inspect_relations(controls, ages)

    def test_duplicate_control(self) -> None:
        controls, ages = fixture()
        controls[-1] = deepcopy(controls[-2])
        with self.assertRaises(ValueError):
            inspect_relations(controls, ages)

    def test_asymmetric_error(self) -> None:
        controls, ages = fixture()
        controls[0]["source_payload"]["geochron"]["geochronerroryounger"] = 81
        with self.assertRaises(ValueError):
            inspect_relations(controls, ages)

    def test_bool_control(self) -> None:
        controls, ages = fixture()
        controls[0]["source_payload"]["depth"] = True
        with self.assertRaises(ValueError):
            inspect_relations(controls, ages)

    def test_third_chronology(self) -> None:
        controls, ages = fixture()
        controls[0]["chronology_id"] = "extra-view"
        with self.assertRaises(ValueError):
            inspect_relations(controls, ages)

    def test_repeated_native_id(self) -> None:
        controls, ages = fixture()
        ages[-1]["source_record_id"] = ages[0]["source_record_id"]
        with self.assertRaises(ValueError):
            inspect_relations(controls, ages)

    def test_empty_native_id(self) -> None:
        controls, ages = fixture()
        ages[-1]["source_record_id"] = ""
        with self.assertRaises(ValueError):
            inspect_relations(controls, ages)

    def test_invalid_ages(self) -> None:
        for value in (None, True, "8000", float("nan"), float("inf")):
            controls, ages = fixture()
            ages[0]["source_age_value"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                inspect_relations(controls, ages)

    def test_proxy_boundary_changed(self) -> None:
        controls, ages = fixture()
        ages[0]["source_age_value"] = 7209
        with self.assertRaises(ValueError):
            inspect_relations(controls, ages)

    def test_bounded_selection_changed(self) -> None:
        controls, ages = fixture()
        ages[0]["source_age_value"] = 11660
        with self.assertRaises(ValueError):
            inspect_relations(controls, ages)

    def test_native_type_and_null_identity(self) -> None:
        for left, right in ((True, 1), (1.0, 1), (None, 0), ([1, 2], [2, 1])):
            self.assertFalse(exact(left, right))

    def test_report_claim_tamper(self) -> None:
        root = Path(__file__).parents[3]
        original = load(
            root
            / "docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/report.json"
        )
        joins = {
            "chronologies": original["neotoma_1983_chronologies"],
            "proxy_by_core": original["paper_interval_proxy_by_core"],
            "bounded_by_core": original[
                "paper_interval_and_landclim_age_span_proxy_by_core"
            ],
        }
        verify_report(original, original, joins)
        for field, value in (
            ("lra_admitted_samples", None),
            ("lra_admitted_samples", False),
            ("landclim_ii_reported_sample_count", 76),
            ("paper_interval_proxy_gap_to_landclim_ii", 0),
        ):
            mutated = deepcopy(original)
            mutated[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                verify_report(mutated, original, joins)
        mutated = deepcopy(original)
        mutated["core_locations_in_paper_local_metres"]["georeferenced"] = True
        with self.assertRaises(ValueError):
            verify_report(mutated, original, joins)

    def test_alias_custody(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).parent / "preflight"
        ) as temporary:
            root = Path(temporary)
            target = root / "native"
            target.write_bytes(b"native")
            link = root / "entry"
            link.symlink_to("native")
            row = alias(link, root)
            self.assertTrue(check_aliases([row]))
            link.unlink()
            link.symlink_to("/usr/bin/true")
            self.assertFalse(check_aliases([row]))
            with self.assertRaises(ValueError):
                alias(link, root)

    def test_isolated_profile_and_source_only(self) -> None:
        profile = profile_guard()
        self.assertFalse(profile["scientific_installed_runtime"])
        source = (
            Path(__file__).parents[3]
            / "docs/report/countries/denmark/solsoe-source-lineage/original-core-selection/replay.py"
        ).read_text()
        module = ast.parse(source)
        assignment = next(
            n
            for n in module.body
            if isinstance(n, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "PUBLISHED_1983_CONTROLS"
                for t in n.targets
            )
        )
        self.assertEqual(ast.literal_eval(assignment.value), DECLARED)
        imports = {
            n.module.split(".")[0]
            for n in ast.walk(module)
            if isinstance(n, ast.ImportFrom) and n.module
        }
        imports.update(
            a.name.split(".")[0]
            for n in ast.walk(module)
            if isinstance(n, ast.Import)
            for a in n.names
        )
        self.assertEqual(
            imports,
            {
                "__future__",
                "argparse",
                "collections",
                "hashlib",
                "json",
                "math",
                "pathlib",
            },
        )

    def test_closed_synthetic_source_ledger(self) -> None:
        controls, ages = fixture()
        ledger = closed_ledger(ages)
        self.assertEqual(
            sum(r["closed_central_point_proxy_selected"] for r in ledger), 74
        )
        self.assertEqual(
            sum(r["legacy_unbounded_central_point_proxy_selected"] for r in ledger), 76
        )
        self.assertTrue(
            all(
                r["analytical_eligibility_evaluated"] is False
                and r["lra_admitted"] is False
                for r in ledger
            )
        )
        # Controlled fixture only: no actual92-row producer or accepted total.
        self.assertEqual(
            [r["source_record"] for r in ledger],
            sorted(ages, key=lambda r: r["source_record_id"]),
        )

    def test_closed_current_schema_refuses_claim_tampering(self) -> None:
        controls, ages = fixture()
        joins = inspect_relations(controls, ages)
        original = load(Path(__file__).parents[3] / REPORT)
        original["neotoma_1983_chronologies"] = joins["chronologies"]
        report = expected_closed_report(original, joins, ages)
        verify_closed_report(report, original, joins, ages)
        for field, value in (
            ("paper_interval_proxy_samples", 76),
            ("schema_version", "solsoe-original-core-selection.v1"),
            ("lra_admitted_samples", True),
        ):
            mutated = deepcopy(report)
            mutated[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_closed_report(mutated, original, joins, ages)
        for field, value in (
            ("analytical_eligibility_evaluated", True),
            ("source_chronology_equivalence_claimed", True),
            ("selection_measure", "full uncertainty containment"),
        ):
            mutated = deepcopy(report)
            mutated["closed_paper_interval_proxy"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_closed_report(mutated, original, joins, ages)
        mutated = deepcopy(report)
        mutated["closed_paper_interval_proxy"]["native_source_proxy_ledger"][0][
            "source_record"
        ]["source_age_value"] = 0
        with self.assertRaises(ValueError):
            verify_closed_report(mutated, original, joins, ages)

    def test_raw_refusal_support_is_not_repaired(self) -> None:
        _, ages = fixture()
        ages[0].update(
            source_age_value=7,
            source_payload={"age": 7, "agetype": "Calibrated radiocarbon years BP"},
            younger_bp=None,
            older_bp=None,
            source_age_younger=-41,
            source_age_older=60,
            comparability_status="refused",
            refusal_reason="negative_bp",
        )
        row = next(
            r
            for r in closed_ledger(ages)
            if r["source_record"]["source_record_id"] == ages[0]["source_record_id"]
        )
        self.assertIs(row["closed_central_point_proxy_selected"], True)
        self.assertIs(row["bounded_closed_central_point_proxy_selected"], False)
        self.assertEqual(row["source_record"], ages[0])
        self.assertIsNone(row["source_record"]["younger_bp"])
        self.assertIs(row["lra_admitted"], False)

    def test_unowned_native_and_namespace_refuse(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).parent / "preflight"
        ) as temporary:
            root = Path(temporary)
            owned = root / "module.py"
            owned.write_text("source")
            from contracts import pin

            good = {
                "native_images": [],
                "namespace": [{"module": "owned", "file": str(owned)}],
            }
            qualify_process_snapshot(good, [pin(owned)], root)
            for raw in (
                {"native_images": ["/unowned/native.dylib"], "namespace": []},
                {
                    "native_images": [],
                    "namespace": [{"module": "global", "file": "/unowned/source.py"}],
                },
            ):
                with self.assertRaises((ValueError, FileNotFoundError)):
                    qualify_process_snapshot(raw, [pin(owned)], root)

    def test_loader_environment_keys_are_refused_even_empty(self) -> None:
        from runtime import require_environment

        require_environment({"HOME": "/inherited", "OMP_NUM_THREADS": "1"})
        for key in (
            "DYLD_LIBRARY_PATH",
            "DYLD_INSERT_LIBRARIES",
            "LD_PRELOAD",
            "LD_LIBRARY_PATH",
            "_PYTHON_HOST_PLATFORM",
            "__PYVENV_LAUNCHER__",
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                require_environment({key: ""})

    def test_dangling_absent_namespace_refuses(self) -> None:
        from runtime import absent_path

        with tempfile.TemporaryDirectory(
            dir=Path(__file__).parent / "preflight"
        ) as temporary:
            root = Path(temporary)
            path = root / "python311.zip"
            self.assertTrue(absent_path(path))
            path.symlink_to(root / "unavailable")
            self.assertFalse(absent_path(path))

    def test_complete_namespace_detects_added_empty_or_shadow_entries(self) -> None:
        from runtime import tree_membership

        with tempfile.TemporaryDirectory(
            dir=Path(__file__).parent / "preflight"
        ) as temporary:
            root = Path(temporary)
            (root / "module.py").write_text("source")
            before = tree_membership(root)
            (root / "empty").mkdir()
            self.assertNotEqual(tree_membership(root), before)
            (root / "empty").rmdir()
            self.assertEqual(tree_membership(root), before)
            (root / "shadow.py").write_text("")
            self.assertNotEqual(tree_membership(root), before)

    def test_arm64_native_parser_rejects_other_headers_and_rows(self) -> None:
        from runtime import dependency_load_names, loader_commands

        image = Path("/owned/image.dylib")
        self.assertEqual(
            dependency_load_names(
                "/owned/image.dylib (architecture arm64):\n\t@rpath/self (compatibility version 1.0.0, current version 1.0.0)\n",
                image,
            ),
            ["@rpath/self"],
        )
        rpaths, identities = loader_commands(
            "Load command 0\n      cmd LC_ID_DYLIB\n     name @rpath/self (offset 24)\nLoad command 1\n      cmd LC_RPATH\n     path @loader_path (offset 12)\n"
        )
        self.assertEqual(rpaths, ["@loader_path"])
        self.assertEqual(identities, {"@rpath/self"})
        for output in (
            "/owned/image.dylib (architecture x86_64):\n",
            "/owned/image.dylib:\nBAD\n",
        ):
            with self.assertRaises(ValueError):
                dependency_load_names(output, image)

    def test_classic_native_inspector_requires_exact_arm64_shape(self) -> None:
        import hashlib
        import struct

        from runtime import validate_inspector

        with tempfile.TemporaryDirectory(
            dir=Path(__file__).parent / "preflight"
        ) as temporary:
            path = Path(temporary) / "inspector"
            raw = b"\xcf\xfa\xed\xfe" + struct.pack("<II", 0x0100000C, 0)
            path.write_bytes(raw)
            validate_inspector(path, hashlib.sha256(raw).hexdigest())
            path.write_bytes(raw[:8] + struct.pack("<I", 2))
            with self.assertRaises(ValueError):
                validate_inspector(path, hashlib.sha256(path.read_bytes()).hexdigest())
            with self.assertRaises(ValueError):
                validate_inspector(path, "0" * 64)

    def test_completed_wall_bound_keeps_timeout_and_type_limits(self) -> None:
        from runtime import wall_within_bound

        self.assertTrue(wall_within_bound(110.0, 110))
        self.assertFalse(wall_within_bound(110.000001, 110))
        for elapsed in (float("nan"), float("inf"), -1.0, True):
            self.assertFalse(wall_within_bound(elapsed, 110))

    def test_absolute_homebrew_at_names_and_loader_context(self) -> None:
        from runtime import expand_dependency

        owner = Path("/source/native/_hashlib.so")
        executable = Path("/source/bin/python3.11")
        for name in (
            "/opt/homebrew/opt/openssl@3/lib/libcrypto.3.dylib",
            "/opt/homebrew/opt/xz/lib/liblzma.5.dylib",
            "/owned/name@loader_path/lib.dylib",
        ):
            self.assertEqual(expand_dependency(name, owner, executable), Path(name))
        self.assertEqual(
            expand_dependency("@loader_path/lib.dylib", owner, executable),
            owner.parent / "lib.dylib",
        )
        self.assertEqual(
            expand_dependency("@executable_path/lib.dylib", owner, executable),
            executable.parent / "lib.dylib",
        )

    def test_unknown_loader_prefix_and_relative_paths_refuse(self) -> None:
        from runtime import expand_dependency

        for value in (
            "@unknown/lib.dylib",
            "@loader_pathology/lib.dylib",
            "@loader_path",
            "@executable_path",
            "@rpath/lib.dylib",
            "relative/lib.dylib",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                expand_dependency(
                    value, Path("/source/native/image"), Path("/source/bin/python")
                )

    def test_actual_native_declared_aliases_remain_exact(self) -> None:
        import os

        from contracts import sha
        from runtime import expand_dependency

        rows = load(Path(__file__).parent / "preflight/actual-declared-aliases.json")
        self.assertEqual(len(rows), 2)
        for row in rows:
            alias = Path(row["alias"])
            lexical = expand_dependency(
                row["lexical_file"], Path("/owned/image"), Path("/owned/bin/python")
            )
            self.assertTrue(alias.is_symlink())
            self.assertEqual(os.readlink(alias), row["link"])
            self.assertEqual(str(alias.resolve(strict=True)), row["target"])
            self.assertEqual(str(lexical.resolve(strict=True)), row["resolved_file"])
            self.assertEqual(sha(lexical), row["sha256"])
            self.assertEqual(lexical.stat().st_size, row["bytes"])


if __name__ == "__main__":
    unittest.main()
