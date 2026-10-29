"""Exercise offline runtime boundary guards using stdlib-only controlled fixtures."""

from __future__ import annotations

import base64
import copy
import csv
import hashlib
from importlib import metadata
import io
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contracts
from contracts import (
    confined_output,
    digest,
    member,
    namespace_snapshot,
    record_rows,
    validate_payload,
    validate_probe_dependencies,
    validate_selection,
    verify_absences,
    verify_aliases,
    verify_base_namespaces,
    verify_cache_membership,
    verify_pin,
    wheel_name,
)
from observe import installed_member
from pip_entry import pip_arguments
from prepare import (
    OTool,
    OTool_SHA,
    dependency_load_names,
    is_macho,
    loader_commands,
    resolve_dependency,
    validate_inspector,
)
from run import completed_receipt


def fixture(root: Path) -> dict[str, Any]:
    archive = root / "payload"
    archive.mkdir()
    distribution = "example-1.2.3.dist-info"
    info = archive / distribution
    info.mkdir()
    payloads = {
        distribution
        + "/METADATA": b"Metadata-Version: 2.1\nName: example\nVersion: 1.2.3\n",
        distribution
        + "/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        "example/__init__.py": b"VALUE = 1\n",
    }
    rows = []
    for name, raw in payloads.items():
        path = archive / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(raw)
        encoded = (
            base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip("=")
        )
        rows.append([name, "sha256=" + encoded, str(len(raw))])
    rows.append([distribution + "/RECORD", "", ""])
    buffer = io.StringIO(newline="")
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    (info / "RECORD").write_text(buffer.getvalue())
    return {
        "archive": str(archive),
        "distribution": distribution,
        "metadata_sha256": digest(info / "METADATA"),
        "wheel_sha256": digest(info / "WHEEL"),
        "complete_wheel_tags": ["py3-none-any"],
    }


class Guards(unittest.TestCase):
    def setUp(self) -> None:
        parent = contracts.SOURCE / "preflight"
        parent.mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(dir=parent)
        self.root = Path(self.directory.name)
        self.old_cache = contracts.CACHE
        contracts.CACHE = self.root

    def tearDown(self) -> None:
        contracts.CACHE = self.old_cache
        self.directory.cleanup()

    def test_complete_original_record_payload(self) -> None:
        result = validate_payload(fixture(self.root))
        self.assertEqual(len(result["members"]), 4)
        self.assertEqual(result["wheel_filename"], "example-1.2.3-py3-none-any.whl")

    def test_wrong_cache_file_sha(self) -> None:
        row = fixture(self.root)
        (Path(row["archive"]) / "example/__init__.py").write_bytes(b"VALUE = 2\n")
        with self.assertRaises(ValueError):
            validate_payload(row)

    def test_original_record_member_size(self) -> None:
        row = fixture(self.root)
        path = Path(row["archive"]) / row["distribution"] / "RECORD"
        path.write_text(path.read_text().replace(",10\n", ",11\n"))
        with self.assertRaises(ValueError):
            validate_payload(row)

    def test_unlisted_cached_payload(self) -> None:
        row = fixture(self.root)
        (Path(row["archive"]) / "extra").write_bytes(b"extra")
        with self.assertRaises(ValueError):
            validate_payload(row)

    def test_missing_cached_payload(self) -> None:
        row = fixture(self.root)
        (Path(row["archive"]) / "example/__init__.py").unlink()
        with self.assertRaises(ValueError):
            validate_payload(row)

    def test_metadata_alias_refuses_before_read(self) -> None:
        row = fixture(self.root)
        path = Path(row["archive"]) / row["distribution"] / "METADATA"
        target = self.root / "external"
        path.rename(target)
        path.symlink_to(target)
        with self.assertRaises(ValueError):
            validate_payload(row)

    def test_original_metadata_identity(self) -> None:
        row = fixture(self.root)
        row["metadata_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_payload(row)

    def test_complete_native_tags_are_exact(self) -> None:
        row = fixture(self.root)
        row["complete_wheel_tags"] = ["cp311-cp311-macosx_14_0_arm64"]
        with self.assertRaises(ValueError):
            validate_payload(row)

    def test_wheel_tag_compression_no_extra_compatibility(self) -> None:
        self.assertEqual(
            wheel_name("example-1.2.3.dist-info", ["py2-none-any", "py3-none-any"]),
            "example-1.2.3-py2.py3-none-any.whl",
        )
        with self.assertRaises(ValueError):
            wheel_name(
                "example-1.2.3.dist-info",
                ["cp311-cp311-macosx_14_0_arm64", "cp312-cp312-macosx_14_0_arm64"],
            )

    def test_record_duplicate_members(self) -> None:
        with self.assertRaises(ValueError):
            record_rows(b"x/RECORD,,\nx/RECORD,,\n", "x/RECORD")

    def test_record_other_unhashed_entry(self) -> None:
        with self.assertRaises(ValueError):
            record_rows(b"other,,\nx/RECORD,,\n", "x/RECORD")

    def test_member_traversal_absolute_and_backslash(self) -> None:
        for value in (
            "../escape",
            "/escape",
            "a/../escape",
            "a\\escape",
            "a\nfile",
            "",
            ".",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                member(value)

    def test_input_boolean_size_and_same_size_changes(self) -> None:
        path = self.root / "input"
        path.write_bytes(b"abc")
        original = contracts.pin(path)
        wrong = {**original, "bytes": True}
        with self.assertRaises(ValueError):
            verify_pin(wrong)
        path.write_bytes(b"abd")
        with self.assertRaises(ValueError):
            verify_pin(original)

    def test_runtime_alias_raw_spelling_preserved(self) -> None:
        target = self.root / "target"
        target.write_bytes(b"abc")
        link = self.root / "link"
        link.symlink_to("target")
        records = contracts.aliases([link])
        verify_aliases(records)
        link.unlink()
        link.symlink_to("./target")
        with self.assertRaises(ValueError):
            verify_aliases(records)

    def test_runtime_alias_target_preserved(self) -> None:
        for name in ("target", "other"):
            (self.root / name).write_bytes(b"abc")
        link = self.root / "link"
        link.symlink_to("target")
        records = contracts.aliases([link])
        link.unlink()
        link.symlink_to("other")
        with self.assertRaises(ValueError):
            verify_aliases(records)

    def test_owned_output_refuses_outside_or_alias(self) -> None:
        for path in (
            contracts.ROOT / "outside-runtime",
            contracts.ROOT / "artifacts/../outside-runtime",
        ):
            with self.assertRaises(ValueError):
                confined_output(path)
        link = self.root / "linked"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            confined_output(link / "child")

    def test_installed_scheme_maps_without_payload_inference(self) -> None:
        site = self.root / "environment/lib/python3.11/site-packages"
        environment = self.root / "environment"
        self.assertEqual(
            installed_member(
                environment,
                site,
                "example.data/purelib/example/__init__.py",
                "example-1.2.3.dist-info",
            ),
            site / "example/__init__.py",
        )
        self.assertEqual(
            installed_member(
                environment,
                site,
                "example.data/scripts/example",
                "example-1.2.3.dist-info",
            ),
            environment / "bin/example",
        )
        with self.assertRaises(ValueError):
            installed_member(
                environment,
                site,
                "example.data/unknown/example",
                "example-1.2.3.dist-info",
            )

    def test_inclusive_completed_receipt_exact_bound(self) -> None:
        (self.root / "payload").write_bytes(b"data")
        raw, total = completed_receipt(self.root, {"actual_exit": 0}, 10000)
        self.assertEqual(total, 4 + len(raw))
        self.assertEqual(
            completed_receipt(self.root, {"actual_exit": 0}, total)[1], total
        )
        with self.assertRaises(ValueError):
            completed_receipt(self.root, {"actual_exit": 0}, total - 1)

    def test_selection_membership_and_optional_limit(self) -> None:
        actual = contracts.json_value(
            contracts.ROOT
            / "artifacts/science/runtime-availability-custody/offline-runtime-selection.json"
        )
        validate_selection(actual)
        duplicate = copy.deepcopy(actual)
        duplicate["selected"][1] = duplicate["selected"][0]
        with self.assertRaises(ValueError):
            validate_selection(duplicate)
        wrong = copy.deepcopy(actual)
        wrong["missing_optional_release_distributions"].pop()
        with self.assertRaises(ValueError):
            validate_selection(wrong)

    def test_offline_pip_flags_and_owned_prefix(self) -> None:
        environment = self.root / "environment"
        requirements = self.root / "wheels/requirements.txt"
        argv = pip_arguments(environment, requirements)
        for value in (
            "--isolated",
            "--no-index",
            "--no-deps",
            "--require-hashes",
            "--no-cache-dir",
            "--no-compile",
            "--disable-pip-version-check",
            "--no-input",
        ):
            self.assertEqual(argv.count(value), 1)
        self.assertEqual(argv[argv.index("--prefix") + 1], str(environment))
        self.assertEqual(argv[argv.index("--requirement") + 1], str(requirements))

    def test_all_observer_probes_require_selected_distribution(self) -> None:
        selection = contracts.json_value(
            contracts.ROOT
            / "artifacts/science/runtime-availability-custody/offline-runtime-selection.json"
        )
        rows = []
        for row in selection["selected"]:
            name, version = (
                row["distribution"].removesuffix(".dist-info").rsplit("-", 1)
            )
            rows.append({"name": name, "version": version})
        validate_probe_dependencies(rows)
        bad = {**contracts.OBSERVER_PROBES, "lxml.etree": "lxml"}
        with self.assertRaises(ValueError):
            validate_probe_dependencies(rows, bad)
        wrong = copy.deepcopy(rows)
        next(row for row in wrong if row["name"] == "numpy")["version"] = "2.4.5"
        with self.assertRaises(ValueError):
            validate_probe_dependencies(wrong)

    def test_cache_empty_directory_namespace_is_protected(self) -> None:
        row = validate_payload(fixture(self.root))
        verify_cache_membership([row])
        (Path(row["archive"]) / "unlisted-empty-directory").mkdir()
        with self.assertRaises(ValueError):
            verify_cache_membership([row])

    def test_native_install_id_is_separate_from_external_rpath(self) -> None:
        listing = "cmd LC_ID_DYLIB\ncmdsize 80\nname @rpath/libexample.dylib (offset 24)\ncmd LC_RPATH\ncmdsize 40\npath @loader_path/../lib (offset 12)\n"
        rpaths, ids = loader_commands(listing)
        self.assertEqual(ids, {"@rpath/libexample.dylib"})
        self.assertEqual(rpaths, ["@loader_path/../lib"])

    def test_complete_base_namespace_refuses_new_file_or_empty_directory(self) -> None:
        root = self.root / "base"
        root.mkdir()
        (root / "module.py").write_bytes(b"pass\n")
        captured = namespace_snapshot(root, [])
        verify_base_namespaces([captured])
        added = root / "shadow.py"
        added.write_bytes(b"pass\n")
        with self.assertRaises(ValueError):
            verify_base_namespaces([captured])
        added.unlink()
        added.mkdir()
        with self.assertRaises(ValueError):
            verify_base_namespaces([captured])

    def test_base_namespace_alias_spelling_is_bound(self) -> None:
        root = self.root / "base"
        root.mkdir()
        (root / "stdlib").mkdir()
        link = root / "library"
        link.symlink_to("stdlib", target_is_directory=True)
        captured = namespace_snapshot(root, [])
        verify_base_namespaces([captured])
        link.unlink()
        link.symlink_to("./stdlib", target_is_directory=True)
        with self.assertRaises(ValueError):
            verify_base_namespaces([captured])

    def test_absent_zip_refuses_regular_and_dangling_entries(self) -> None:
        path = self.root / "python311.zip"
        verify_absences([str(path)])
        path.write_bytes(b"not admitted")
        with self.assertRaises(ValueError):
            verify_absences([str(path)])
        path.unlink()
        path.symlink_to(self.root / "missing")
        with self.assertRaises(ValueError):
            verify_absences([str(path)])

    def test_native_dependencies_refuse_missing_ambiguous_or_unknown(self) -> None:
        owner = self.root / "binary.so"
        owner.write_bytes(b"\xcf\xfa\xed\xfe" + b"controlled header")
        self.assertTrue(is_macho(owner))
        self.assertFalse(is_macho(Path(__file__)))
        first = self.root / "first"
        second = self.root / "second"
        first.mkdir()
        second.mkdir()
        library = first / "lib.dylib"
        library.write_bytes(b"fixture")
        self.assertEqual(
            resolve_dependency("@loader_path/first/lib.dylib", owner, [], owner)[0],
            library,
        )
        self.assertEqual(
            resolve_dependency("@executable_path/first/lib.dylib", owner, [], owner)[0],
            library,
        )
        self.assertEqual(
            resolve_dependency("@rpath/lib.dylib", owner, [str(first)], owner)[0],
            library,
        )
        for token in ("@rpath/missing.dylib", "@unknown/lib.dylib", "relative.dylib"):
            with self.assertRaises(ValueError):
                resolve_dependency(token, owner, [str(first)], owner)
        (second / "lib.dylib").write_bytes(b"other")
        with self.assertRaises(ValueError):
            resolve_dependency(
                "@rpath/lib.dylib", owner, [str(first), str(second)], owner
            )

    def test_arm64_dependency_headers_do_not_become_load_names(self) -> None:
        binary = self.root / "universal.so"
        dependency = "\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1351.0.0)"
        output = str(binary) + " (architecture arm64):\n" + dependency + "\n"
        self.assertEqual(
            dependency_load_names(output, binary), ["/usr/lib/libSystem.B.dylib"]
        )
        with self.assertRaises(ValueError):
            dependency_load_names(
                output + str(binary) + " (architecture x86_64):\n", binary
            )
        with self.assertRaises(ValueError):
            dependency_load_names(output + "unexpected malformed row\n", binary)
        selection = contracts.json_value(
            contracts.ROOT
            / "artifacts/science/runtime-availability-custody/offline-runtime-selection.json"
        )
        selected = next(
            row
            for row in selection["selected"]
            if row["distribution"] == "charset_normalizer-3.4.6.dist-info"
        )
        native_candidates = list(
            Path(selected["archive"]).glob("*__mypyc.cpython-311-darwin.so")
        )
        self.assertEqual(len(native_candidates), 1)
        actual = native_candidates[0]
        self.assertTrue(is_macho(actual))
        with actual.open("rb") as stream:
            self.assertEqual(stream.read(4), b"\xca\xfe\xba\xbe")
        actual_output = subprocess.check_output(
            [str(OTool), "-arch", "arm64", "-L", str(actual)], text=True
        )
        self.assertTrue(dependency_load_names(actual_output, actual))

    def test_loader_and_build_overrides_refused_by_key_presence(self) -> None:
        admitted = contracts.require_runtime_environment(
            {"PATH": "/controlled", "OMP_NUM_THREADS": "1"}
        )
        self.assertEqual(admitted["present_forbidden_key_names"], [])
        self.assertFalse(admitted["environment_values_disclosed"])
        for key in [
            "DYLD_LIBRARY_PATH",
            "DYLD_INSERT_LIBRARIES",
            "DYLD_UNKNOWN",
            *contracts.FORBIDDEN_RUNTIME_KEYS,
        ]:
            self.assertTrue(contracts.runtime_override_key(key))
            for value in ("", "controlled-secret-value"):
                with self.assertRaises(ValueError) as raised:
                    contracts.require_runtime_environment({key: value})
                self.assertIn(key, str(raised.exception))
                self.assertNotIn("controlled-secret-value", str(raised.exception))

    def test_inspector_role_has_actual_arm64_slice_and_exact_closure(self) -> None:
        validate_inspector(OTool, OTool_SHA)
        output = subprocess.check_output(
            [str(OTool), "-arch", "arm64", "-L", str(OTool)], text=True
        )
        self.assertEqual(
            set(dependency_load_names(output, OTool)),
            {"/usr/lib/libc++.1.dylib", "/usr/lib/libSystem.B.dylib"},
        )
        validate_inspector(OTool, OTool_SHA)
        controlled = self.root / "inspector"
        controlled.write_bytes(
            b"\xcf\xfa\xed\xfe"
            + (0x0100000C).to_bytes(4, "little")
            + (2).to_bytes(4, "little")
        )
        with self.assertRaises(ValueError):
            validate_inspector(controlled, digest(controlled))
        controlled.write_bytes(b"\xca\xfe\xba\xbe" + b"\0" * 8)
        with self.assertRaises(ValueError):
            validate_inspector(controlled, digest(controlled))
        with self.assertRaises(ValueError):
            validate_inspector(OTool, "0" * 64)

    def test_cached_pip_metadata_does_not_satisfy_fresh_owned_install(self) -> None:
        selection = contracts.json_value(
            contracts.ROOT
            / "artifacts/science/runtime-availability-custody/offline-runtime-selection.json"
        )
        rows = selection["selected"]
        self.assertEqual(len(rows), 147)
        pip = [row for row in rows if row["distribution"] == "pip-26.2.dist-info"]
        self.assertEqual(len(pip), 1)
        site = self.root / "empty-owned-site"
        site.mkdir()
        visible = [
            dist.version
            for dist in metadata.distributions(path=[pip[0]["archive"], str(site)])
            if dist.metadata["Name"].lower() == "pip"
        ]
        self.assertEqual(visible, ["26.2"])
        self.assertEqual(list(metadata.distributions(path=[str(site)])), [])
        argv = pip_arguments(
            self.root / "fresh-owned-environment", self.root / "requirements.txt"
        )
        self.assertEqual(argv.count("--ignore-installed"), 1)
        self.assertNotIn("--force-reinstall", argv)
        self.assertNotIn("uninstall", argv)
        previous = (
            contracts.ROOT
            / "artifacts/science/source-runtime-inspector-custody/observe.py"
        )
        self.assertEqual(
            (Path(__file__).parent / "observe.py").read_bytes(), previous.read_bytes()
        )


if __name__ == "__main__":
    unittest.main()
