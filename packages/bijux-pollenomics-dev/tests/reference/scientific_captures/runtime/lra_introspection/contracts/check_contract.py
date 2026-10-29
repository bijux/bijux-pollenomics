"""Source-only negative controls; no optimizer, model, R or preparer is invoked."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import check_optimizer, check_paired, rows
from observe_numerical import differences, namespace_records
from observe_runtime_probe import validate_metadata
from runtime_custody import (
    aliases_unchanged,
    core_introspection_module,
    dependency,
    load_commands,
    native_seeds,
    requested_environment,
    runpaths,
    stdlib_alias_contract,
    tree,
)

R = Path(__file__).resolve().parents[3]


class ContractTests(unittest.TestCase):
    def optimizer(self) -> list[Any]:
        p = R / "docs/report/method-certification/optimizer-solution-quality"
        return [
            json.loads((p / "cases.json").read_bytes()),
            rows(p / "python-fits.csv"),
            rows(p / "r-fits.csv"),
            rows(p / "summary.csv"),
        ]

    def paired(self) -> list[Any]:
        p = R / "docs/report/method-certification/paired-love-draws"
        return [
            rows(p / "python-values.csv"),
            rows(p / "r-values.csv"),
            json.loads((p / "draws.json").read_bytes()),
            json.loads((p / "setup.json").read_bytes()),
        ]

    def test_retained_three_case_scalar_positive(self) -> None:
        self.assertEqual(check_optimizer(*self.optimizer())["ordered_cases"], 3)

    def test_optimizer_order_and_budget_are_not_relaxed(self) -> None:
        for selector in ["order", "budget", "gap", "candidate", "summary"]:
            with self.subTest(selector=selector):
                v = self.optimizer()
                if selector == "order":
                    v[2].reverse()
                elif selector == "budget":
                    v[2][0]["iter"] = "399"
                elif selector == "gap":
                    v[1][0]["bestval"] = "0.1"
                elif selector == "candidate":
                    v[1][0]["c1"] = "0"
                else:
                    v[3][0]["r_gap"] = "0.01"
                with self.assertRaises(ValueError):
                    check_optimizer(*v)

    def test_retained_complete_paired_positive(self) -> None:
        result = check_paired(*self.paired())
        self.assertEqual(
            (result["paired_finite_values"], result["paired_missing_values"]),
            (120, 280),
        )

    def test_missing_zero_identity_tolerance_and_count_type_refuse(self) -> None:
        for selector in [
            "missing-zero",
            "identity",
            "tolerance",
            "count-bool",
            "regional",
        ]:
            with self.subTest(selector=selector):
                v = self.paired()
                if selector == "missing-zero":
                    v[0][0]["value"] = "0"
                elif selector == "identity":
                    v[0][0]["taxon"] = "unknown"
                elif selector == "tolerance":
                    v[0][70]["value"] = str(float(v[0][70]["value"]) + 0.001)
                elif selector == "count-bool":
                    v[2]["local_counts"][0][0][0] = True
                else:
                    v[2]["regional_cover"][0] = 0
                with self.assertRaises(ValueError):
                    check_paired(*v)

    def test_native_id_is_not_a_load_dependency(self) -> None:
        data = "cmd LC_ID_DYLIB\n name example.so (offset 24)\ncmd LC_LOAD_DYLIB\n name /required.dylib (offset 24)\ncmd LC_LOAD_WEAK_DYLIB\n name /optional.dylib (offset 24)"
        self.assertEqual(
            load_commands(data),
            [
                {"command": "LC_LOAD_DYLIB", "path": "/required.dylib"},
                {"command": "LC_LOAD_WEAK_DYLIB", "path": "/optional.dylib"},
            ],
        )

    def test_loader_aliases_and_strong_weak_system_boundaries(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent / "preflight"
        ) as d:
            root = Path(d)
            loader = root / "loader"
            loader.write_bytes(b"source")
            target = root / "actual"
            target.write_bytes(b"library")
            (root / "alias").symlink_to(target)
            row = {"command": "LC_LOAD_DYLIB", "path": "@loader_path/alias"}
            self.assertEqual(dependency(loader, row)["target"]["path"], str(target))
            self.assertFalse(
                dependency(
                    loader,
                    {"command": "LC_LOAD_DYLIB", "path": "/usr/lib/sealed.dylib"},
                )["physical_file_claim"]
            )
            self.assertNotIn(
                "target",
                dependency(
                    loader,
                    {"command": "LC_LOAD_WEAK_DYLIB", "path": str(root / "absent")},
                ),
            )
            for name in [str(root / "absent"), "@rpath/unknown"]:
                with self.assertRaises(ValueError):
                    dependency(loader, {"command": "LC_LOAD_DYLIB", "path": name})

    def test_runtime_tree_alias_custody_refuses_escape(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent / "preflight"
        ) as d:
            root = Path(d)
            owned = root / "owned"
            owned.mkdir()
            p = owned / "file"
            p.write_bytes(b"owned")
            alias = owned / "alias"
            alias.symlink_to(p)
            files, links = tree(owned)
            self.assertEqual(files, [p])
            self.assertTrue(aliases_unchanged(links))
            outside = root / "outside"
            outside.write_bytes(b"other")
            alias.unlink()
            alias.symlink_to(outside)
            self.assertFalse(aliases_unchanged(links))
            with self.assertRaises(ValueError):
                tree(owned)

    def test_explicit_external_files_and_omitted_directory_are_exact(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent / "preflight") as d:
            root = Path(d)
            owned = root / "owned"
            owned.mkdir()
            outside = root / "binary"
            outside.write_bytes(b"framework")
            global_site = root / "global-site"
            global_site.mkdir()
            (global_site / "not-admitted").write_bytes(b"ambient")
            alias = owned / "binary-alias"
            alias.symlink_to(outside)
            unused = owned / "unused"
            unused.symlink_to(global_site)
            files, links = tree(
                owned,
                external_files={alias: outside},
                unused_directory_aliases={unused: global_site},
            )
            self.assertEqual(files, [outside])
            raw = {path: os.readlink(path) for path in links}
            self.assertTrue(aliases_unchanged(links, link_text=raw))
            alias.unlink()
            alias.symlink_to("../binary")
            self.assertTrue(aliases_unchanged(links))
            self.assertFalse(aliases_unchanged(links, link_text=raw))
            with self.assertRaisesRegex(ValueError, "root=.*alias=.*target="):
                tree(owned)
            with self.assertRaisesRegex(ValueError, "External file alias differs"):
                tree(
                    owned,
                    external_files={alias: root / "wrong"},
                    unused_directory_aliases={unused: global_site},
                )

    def test_stdlib_contract_rejects_ambient_paths_and_ambiguous_config(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent / "preflight") as d:
            root = Path(d)
            stdlib = root / "framework/lib/python3.11"
            (stdlib / "config-3.11-darwin").mkdir(parents=True)
            binary = root / "framework/Python"
            binary.write_bytes(b"framework")
            global_site = root / "global-site"
            global_site.mkdir()
            (stdlib / "site-packages").symlink_to(global_site)
            for name in ("libpython3.11.a", "libpython3.11.dylib"):
                (stdlib / "config-3.11-darwin" / name).symlink_to(binary)
            environment = root / "environment"
            environment.mkdir()
            cfg = environment / "pyvenv.cfg"
            cfg.write_text("include-system-site-packages = false\n")
            external, omitted, record = stdlib_alias_contract(
                stdlib, environment, [str(environment)], global_site=global_site
            )
            self.assertEqual(len(external), 2)
            self.assertEqual(len(omitted), 1)
            self.assertFalse(
                record["unused_global_site_alias"]["contents_traversed_or_admitted"]
            )
            self.assertEqual(
                tree(stdlib, external_files=external, unused_directory_aliases=omitted)[
                    0
                ],
                [binary],
            )
            for path in (str(global_site), str(global_site / "child")):
                with self.assertRaisesRegex(ValueError, "Ambient global packages"):
                    stdlib_alias_contract(
                        stdlib, environment, [path], global_site=global_site
                    )
            for value in ("true", "false\ninclude-system-site-packages = false"):
                cfg.write_text(f"include-system-site-packages = {value}\n")
                with self.assertRaises(ValueError):
                    stdlib_alias_contract(
                        stdlib, environment, [], global_site=global_site
                    )

    def test_raw_R_snapshot_precedes_validation_and_probe_skips_math(self) -> None:
        text = (Path(__file__).parent / "oracle_metadata.R").read_text()
        self.assertLess(text.index("before <<- actual"), text.index("validate(actual)"))
        self.assertIn("raw_path = raw", text)
        self.assertLess(
            text.index("info <- capture.output(sessionInfo())"),
            text.index("namespaces <- lapply"),
        )
        self.assertLess(
            text.index("info <- capture.output(sessionInfo())"),
            text.index("dlls <- lapply"),
        )
        self.assertIn('"DLL outside declared native closure:"', text)
        self.assertIn("if (!metadata_only) {", text)
        self.assertIn("original_script = if (metadata_only) NULL", text)
        self.assertIn("numerical_exit <- NULL", text)

    def test_metadata_only_observer_forbids_numerical_and_unowned_DLL(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).parent / "preflight"
        ) as folder:
            root = Path(folder)
            home, library = root / "R", root / "native"
            namespaces = []
            pins = []
            for name, version in (
                ("base", "4.6.0"),
                ("disqover", "0.9.14"),
                ("RcppDE", "0.1.9"),
                ("jsonlite", "2.0.0"),
            ):
                path = home / "library" / name
                path.mkdir(parents=True)
                file = path / "DESCRIPTION"
                file.write_text("controlled")
                pins.append({"path": str(file)})
                namespaces.append(
                    {
                        "name": name,
                        "version": version,
                        "raw_path": str(path),
                        "path": str(path),
                        "path_error": None,
                    }
                )
            library.mkdir()
            dll = library / "RcppDE.so"
            dll.write_bytes(b"controlled DLL")
            pins.append({"path": str(dll)})
            snapshot = {
                "version": "4.6.0",
                "R_arch": "",
                "dynlib_ext": ".so",
                "R_home": str(home),
                "library_paths": [str(home / "library"), str(library)],
                "namespaces": namespaces,
                "DLLs": [
                    {
                        "name": "RcppDE",
                        "raw_path": str(dll),
                        "path": str(dll),
                        "path_error": None,
                        "built_in": False,
                    }
                ],
                "session_info": ["controlled"],
            }
            meta: dict[str, Any] = {
                "schema_version": "controlled-lra-R-process.v1",
                "metadata_only": True,
                "original_script": None,
                "numerical_exit": None,
                "numerical_error": None,
                "metadata_exit": 0,
                "metadata_error": None,
                "actual_trailing_arguments": [],
                "before": snapshot,
                "after": copy.deepcopy(snapshot),
            }
            plan: dict[str, Any] = {
                "input_pins": pins,
                "native_dependency_files": [str(dll)],
                "current_R_home": str(home),
                "original_Darwin_native_installation": {"root": str(library)},
            }
            self.assertEqual(validate_metadata(meta, plan)["before_DLLs"], 1)
            for selector in (
                "numerical",
                "refusal",
                "raw_path",
                "version",
                "missingDLL",
                "sentinel",
            ):
                bad = copy.deepcopy(meta)
                wrong_plan = copy.deepcopy(plan)
                if selector == "numerical":
                    bad["numerical_exit"] = 0
                elif selector == "refusal":
                    bad["metadata_exit"] = 1
                elif selector == "raw_path":
                    bad["before"]["DLLs"][0]["raw_path"] = str(root / "wrong.so")
                elif selector == "version":
                    bad["before"]["namespaces"][0]["version"] = "4.5.0"
                elif selector == "missingDLL":
                    wrong_plan["native_dependency_files"] = []
                else:
                    bad["before"]["DLLs"][0]["built_in"] = True
                with self.assertRaises(ValueError):
                    validate_metadata(bad, wrong_plan)

    def test_typed_history_preserves_zero_and_null(self) -> None:
        result = differences({"x": 0, "y": None}, {"x": 0.0, "y": 0})
        self.assertEqual(len(result), 2)

    def test_r_wrapper_retains_real_base_namespace_handling(self) -> None:
        text = (Path(__file__).parent / "oracle_metadata.R").read_text()
        self.assertIn(
            'if (identical(name, "base")) file.path(R.home("library"), "base") else getNamespaceInfo(name, "path")',
            text,
        )
        self.assertIn("source(original, local = .GlobalEnv)", text)
        self.assertIn("numerical_exit <<- 1L", text)
        self.assertNotIn("commandArgs <-", text)

    def test_declared_namespace_excludes_debug_and_optional_devices(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent / "preflight"
        ) as d:
            root = Path(d)
            package = root / "R/library/example"
            (package / "libs/debug").mkdir(parents=True)
            (package / "NAMESPACE").write_text(
                "useDynLib(example, .registration=TRUE)\n"
            )
            for name in ["example.so", "unused-cairo.so", "debug/example.so"]:
                (package / "libs" / name).write_bytes(b"controlled library")
            home = root / "R"
            (home / "etc").mkdir()
            (home / "include").mkdir()
            (home / "modules").mkdir()
            (home / "etc/Makeconf").write_text(
                'LAPACK_LIBS = -L"$(R_HOME)/lib$(R_ARCH)" -lRlapack\nR_ARCH = \nSHLIB_EXT = .so\n'
            )
            (home / "include/Rversion.h").write_text(
                '#define R_MAJOR  "4"\n#define R_MINOR  "6.0"\n'
            )
            (home / "modules/lapack.so").write_bytes(b"controlled LAPACK module")
            self.assertEqual(
                core_introspection_module(home, "lapack"), home / "modules/lapack.so"
            )
            with self.assertRaises(ValueError):
                core_introspection_module(home, "arbitrary-module")
            jsonlite = home / "library/jsonlite"
            jsonlite.mkdir()
            library = root / "owned-library"
            library.mkdir()
            for name in (
                "GenSA",
                "RcppArmadillo",
                "RcppDE",
                "Rmalschains",
                "disqover",
                "plyr",
            ):
                installed = library / name
                (installed / "libs").mkdir(parents=True)
                (installed / "DESCRIPTION").write_text(f"Package: {name}\n")
                (installed / "NAMESPACE").write_text(
                    f"useDynLib({name}, .registration=TRUE)\n"
                )
                (installed / "libs" / (name + ".so")).write_bytes(
                    b"controlled owned library"
                )
            plan = root / "artifacts/science/native-reference-admission/plan.json"
            plan.parent.mkdir(parents=True)
            plan.write_text(
                json.dumps({"host_package_paths": {"example": str(package)}})
            )
            selected = native_seeds(root, home, library)
            self.assertIn(package / "libs/example.so", selected)
            self.assertIn(library / "RcppDE/libs/RcppDE.so", selected)
            self.assertIn(library / "disqover/libs/disqover.so", selected)
            self.assertNotIn(package / "libs/unused-cairo.so", selected)
            self.assertNotIn(package / "libs/debug/example.so", selected)
            extra = library / "unknown"
            extra.mkdir()
            with self.assertRaises(ValueError):
                native_seeds(root, home, library)
            extra.rmdir()
            installed = library / "RcppDE"
            moved = root / "owned-RcppDE"
            installed.rename(moved)
            installed.symlink_to(moved)
            with self.assertRaises(ValueError):
                native_seeds(root, home, library)
            installed.unlink()
            moved.rename(installed)
            description = installed / "DESCRIPTION"
            for value in (None, "Package: wrong\n"):
                if value is None:
                    description.unlink()
                else:
                    description.write_text(value)
                with self.assertRaises(ValueError):
                    native_seeds(root, home, library)
            description.write_text("Package: RcppDE\n")
            (package / "libs/example.so").unlink()
            with self.assertRaises(ValueError):
                native_seeds(root, home, library)

    def test_exact_loader_rpath_and_ambiguity_refusal(self) -> None:
        self.assertEqual(
            runpaths("cmd LC_RPATH\n path @loader_path (offset 12)"), ("@loader_path",)
        )
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent / "preflight"
        ) as d:
            root = Path(d)
            loader = root / "loader"
            loader.write_bytes(b"controlled loader")
            library = root / "value.dylib"
            library.write_bytes(b"one")
            row = {"command": "LC_LOAD_DYLIB", "path": "@rpath/value.dylib"}
            self.assertEqual(
                dependency(loader, row, rpaths=("@loader_path",))["target"]["path"],
                str(library),
            )
            other = root / "other"
            other.mkdir()
            (other / "value.dylib").write_bytes(b"two")
            with self.assertRaises(ValueError):
                dependency(loader, row, rpaths=("@loader_path", str(other)))

    def test_same_process_base_and_dll_records_are_exact(self) -> None:
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent / "preflight"
        ) as d:
            root = Path(d)
            family = "optimizer-solution-quality"
            home = root / "R"
            namespaces = []
            pins = []
            for name, version in [
                ("base", "4.6.0"),
                ("jsonlite", "2.0.0"),
                ("RcppDE", "0.1.9"),
                ("disqover", "0.9.14"),
            ]:
                directory = home / "library" / name
                directory.mkdir(parents=True)
                description = directory / "DESCRIPTION"
                description.write_text("controlled namespace")
                namespaces.append(
                    {"name": name, "version": version, "path": str(directory)}
                )
                pins.append({"path": str(description)})
            dll = home / "library/disqover/source.so"
            dll.write_bytes(b"controlled DLL")
            pins.append({"path": str(dll)})
            owned = root / "owned/replay.py"
            rscript = home / "bin/Rscript"
            source = root / "original.R"
            plan = {
                "output": str(root),
                "repository": str(root),
                "current_R_home": str(home),
                "native_Rscript": {"path": str(rscript)},
                "input_pins": pins,
                "native_dependency_files": [str(dll)],
                "maintained_replays": {
                    family: {
                        "canonical_R": {"path": str(source)},
                        "owned_python": {"path": str(owned)},
                    }
                },
                "stages": [
                    {
                        "id": family + "-current-native-replay",
                        "argv": [
                            "PY",
                            "-B",
                            str(owned),
                            "--repository",
                            str(root),
                            "--library",
                            "LIB",
                            "--rscript",
                            str(rscript),
                        ],
                    }
                ],
            }
            arguments = [
                str(owned.parent / "cases.json"),
                str(root / family / "python-fits.csv"),
                str(root / family / "r-fits.csv"),
                str(root / family / "r-session.txt"),
            ]
            snapshot = {
                "R_home": str(home),
                "namespaces": namespaces,
                "DLLs": [
                    {"name": "base", "path": "base", "built_in": True},
                    {"name": "disqover", "path": str(dll), "built_in": False},
                ],
                "session_info": ["controlled session"],
            }
            meta: dict[str, Any] = {
                "schema_version": "controlled-lra-R-process.v1",
                "original_script": str(source),
                "actual_trailing_arguments": arguments,
                "numerical_exit": 0,
                "numerical_error": None,
                "metadata_exit": 0,
                "metadata_error": None,
                "before": snapshot,
                "after": copy.deepcopy(snapshot),
            }
            self.assertEqual(namespace_records(meta, plan, family)["after_DLLs"], 2)
            for change in [
                "base-sentinel",
                "foreign-dll",
                "metadata-bool",
                "failed-numerical",
                "arguments",
            ]:
                value = copy.deepcopy(meta)
                if change == "base-sentinel":
                    value["after"]["DLLs"][0]["name"] = "foreign"
                elif change == "foreign-dll":
                    value["after"]["DLLs"][1]["path"] = str(root / "foreign.so")
                elif change == "metadata-bool":
                    value["metadata_exit"] = False
                elif change == "failed-numerical":
                    value["numerical_exit"] = 1
                else:
                    value["actual_trailing_arguments"].reverse()
                with self.subTest(change=change), self.assertRaises(ValueError):
                    namespace_records(value, plan, family)

    def test_artifact_destinations_preserve_inherited_home(self) -> None:
        root = R / "artifacts/science/controlled-lra-runtime-fixture"
        environment = requested_environment(root, root / "library", root / "R")
        self.assertNotIn("HOME", environment)
        self.assertEqual(environment["R_USER"], str(root / "home"))
        self.assertEqual(environment["TMPDIR"], str(root / "scratch"))
        self.assertEqual(environment["R_HISTFILE"], str(root / "history"))
        self.assertEqual(environment["R_ENVIRON_USER"], "/dev/null")
        self.assertEqual(environment["R_PROFILE_USER"], "/dev/null")


if __name__ == "__main__":
    unittest.main()
