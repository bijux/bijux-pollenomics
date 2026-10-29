"""Exercise archive, role, source-attribution and retained-copy boundaries on synthetic inputs."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from io import BytesIO
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
from typing import Any
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contracts as c
import execute_source as executor
import metadata as m
from run import accounted_receipt


class Guards(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=c.SOURCE / "preflight")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def fixture(self) -> tuple[BytesIO, dict[str, Any]]:
        names = [
            *m.CSV_MEMBERS,
            m.PDF_MEMBER,
            m.SCRIPT_MEMBER,
            "LandCover_OpenLand/output.gpkg",
            "LandCover_OpenLand/LandCover_OpenLand.Rproj",
            *[f"LandCover_OpenLand/.Rproj.user/private{i}" for i in range(14)],
            "LandCover_OpenLand/",
            "LandCover_OpenLand/Data/",
            *[f"LandCover_OpenLand/d{i}/" for i in range(6)],
        ]
        self.assertEqual(len(names), 51)
        stream = BytesIO()
        entries = []
        with ZipFile(stream, "w") as zipped:
            for name in names:
                raw = b"" if name.endswith("/") else name.encode()
                zipped.writestr(name, raw)
                if name in {*m.CSV_MEMBERS, m.PDF_MEMBER}:
                    entries.append(
                        {
                            "path": "Land-cover Maps/" + Path(name).name,
                            "type": "blob",
                            "sha": hashlib.sha1(
                                b"blob " + str(len(raw)).encode() + b"\x00" + raw,
                                usedforsecurity=False,
                            ).hexdigest(),
                            "size": len(raw),
                        }
                    )
        entries.extend(
            [
                {"path": n, "type": "blob", "sha": "f" * 40, "size": 0}
                for n in ["README.md", "LICENSE"]
            ]
        )
        entries.append({"path": "Land-cover Maps", "type": "tree", "sha": "e" * 40})
        return stream, {"sha": m.SOURCE_COMMIT, "truncated": False, "tree": entries}

    def infos(self, zipped: ZipFile) -> list[Any]:
        infos = zipped.infolist()
        large = next(r for r in infos if r.filename.endswith("output.gpkg"))
        large.file_size += 204016242 - sum(r.file_size for r in infos)
        return infos

    def test_complete_tree_and_typed_sizes(self) -> None:
        _, tree = self.fixture()
        self.assertEqual(len(m.upstream_blobs(tree)), 28)
        for value in [True, -1, 0.0, "1"]:
            bad = deepcopy(tree)
            bad["tree"][0]["size"] = value
            with self.assertRaises(ValueError):
                m.upstream_blobs(bad)

    def test_tree_missing_duplicate_truncated_wrong_commit(self) -> None:
        _, tree = self.fixture()
        for key, value in [
            ("sha", "0" * 40),
            ("truncated", True),
            ("tree", tree["tree"][:-1]),
            ("tree", [*tree["tree"][:-1], tree["tree"][0]]),
        ]:
            bad = deepcopy(tree)
            bad[key] = value
            with self.assertRaises(ValueError):
                m.upstream_blobs(bad)

    def test_safe_complete_directory(self) -> None:
        stream, _ = self.fixture()
        with ZipFile(stream) as zipped:
            m.safe_directory(self.infos(zipped))

    def test_zip_alias_and_special_modes(self) -> None:
        for mode in [
            stat.S_IFLNK,
            stat.S_IFIFO,
            stat.S_IFSOCK,
            stat.S_IFCHR,
            stat.S_IFBLK,
        ]:
            stream, _ = self.fixture()
            with ZipFile(stream) as zipped:
                infos = self.infos(zipped)
                infos[0].external_attr = (mode | 0o644) << 16
                with self.assertRaises(ValueError):
                    m.safe_directory(infos)

    def test_zip_paths_and_encryption(self) -> None:
        for name in [
            "../escape",
            "/absolute",
            "LandCover_OpenLand/../escape",
            "LandCover_OpenLand//escape",
            "LandCover_OpenLand/./escape",
            "LandCover_OpenLand/unsafe\\path",
        ]:
            stream, _ = self.fixture()
            with ZipFile(stream) as zipped:
                infos = self.infos(zipped)
                infos[-1].filename = name
                with self.assertRaises(ValueError):
                    m.safe_directory(infos)
        stream, _ = self.fixture()
        with ZipFile(stream) as zipped:
            infos = self.infos(zipped)
            infos[0].flag_bits |= 1
            with self.assertRaises(ValueError):
                m.safe_directory(infos)

    def test_zip_missing_duplicate_and_expanded_count(self) -> None:
        stream, _ = self.fixture()
        with ZipFile(stream) as zipped:
            infos = self.infos(zipped)
            for bad in [infos[:-1], [*infos[:-1], infos[0]]]:
                with self.assertRaises(ValueError):
                    m.safe_directory(bad)
            infos[-1].file_size += 1
            with self.assertRaises(ValueError):
                m.safe_directory(infos)

    def test_selected_27_reads_exclude_GeoPackage_editor(self) -> None:
        stream, tree = self.fixture()
        with ZipFile(stream) as zipped:
            rows, reads = m.expected_rows(
                zipped, self.infos(zipped), m.upstream_blobs(tree)
            )
        self.assertEqual(len(rows), 51)
        self.assertEqual(len(reads), 27)
        self.assertTrue(
            all("output.gpkg" not in n and ".Rproj.user" not in n for n in reads)
        )
        self.assertEqual(
            sum(r["upstream_identity"] == "exact_pinned_git_blob" for r in rows), 26
        )

    def test_member_blob_tamper(self) -> None:
        stream, tree = self.fixture()
        tree["tree"][0]["sha"] = "0" * 40
        with ZipFile(stream) as zipped, self.assertRaises(ValueError):
            m.expected_rows(zipped, self.infos(zipped), m.upstream_blobs(tree))

    def test_roles_refuse_rights_or_independence(self) -> None:
        self.assertEqual(
            m.role(m.CSV_MEMBERS[0])[3:5],
            ("private_source_review_only", "modeled_source_not_independent_truth"),
        )
        self.assertEqual(
            m.role("LandCover_OpenLand/output.gpkg")[4],
            "not_pinned_upstream_and_interpolation_unreviewed",
        )
        self.assertEqual(m.role(m.SCRIPT_MEMBER)[3], "reference_only_no_execution")
        with self.assertRaises(ValueError):
            m.role("LandCover_OpenLand/new_observation.bin")

    def test_complete_products_only_source_digest_changes(self) -> None:
        stream, tree = self.fixture()
        with ZipFile(stream) as zipped:
            rows, _ = m.expected_rows(
                zipped, self.infos(zipped), m.upstream_blobs(tree)
            )
        raw = m.csv_bytes(rows)
        report = c.load(c.ROOT / c.REPORT / "report.json")
        bridge = c.load(c.SOURCE / "source-attribution-bridge.json")
        report["members_csv"] = {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        actual = deepcopy(report)
        actual["inputs"][bridge["path"]] = bridge["current"]["sha256"]
        m.compare_products(report, actual, rows, raw, bridge)
        for key, value in [
            ("public_member_admissions", 1),
            ("independent_vegetation_benchmarks", False),
            ("modeled_source_member_count", 24),
        ]:
            bad = deepcopy(actual)
            bad[key] = value
            with self.assertRaises(ValueError):
                m.compare_products(report, bad, rows, raw, bridge)
        with self.assertRaises(ValueError):
            m.compare_products(report, actual, rows, raw + b"\n", bridge)

    def test_actual_attribution_pair_and_executable_change_refusal(self) -> None:
        old = (
            c.ROOT
            / "artifacts/science/hyde-openland-source-feasibility/recorded-authority.py"
        ).read_bytes()
        bridge = c.load(c.SOURCE / "source-attribution-bridge.json")
        current = (c.ROOT / bridge["path"]).read_bytes()
        producer = (c.ROOT / c.PRODUCER).read_bytes()
        c.bridge_pair(old, current, producer, bridge)
        with self.assertRaises(ValueError):
            c.bridge_pair(old, current + b"\nX=1\n", producer, bridge)
        with self.assertRaises(ValueError):
            c.bridge_pair(
                old,
                current,
                producer + b"\nfrom example import SOURCE_ATTRIBUTION\n",
                bridge,
            )

    def test_copychain_input_roles_and_tamper(self) -> None:
        original = self.root / "original"
        original.mkdir()
        copies = self.root / "copies"
        copies.mkdir()
        records = {}
        chain = []
        for role, name in [
            ("upstream_tree", "upstream-tree.json"),
            ("doi_lineage", "doi-lineage.json"),
        ]:
            source = original / name
            source.write_text("{}\n")
            target = copies / name
            target.write_bytes(source.read_bytes())
            records[role] = c.pin(source)
            chain.append(
                {
                    "role": "retained_declared_metadata_input_not_new_acquisition",
                    "source": c.pin(source),
                    "copied": c.pin(target),
                }
            )
        m.validate_copies(chain, records, copies)
        bad = deepcopy(chain)
        bad[0]["role"] = "fresh_native_generated_metadata"
        with self.assertRaises(ValueError):
            m.validate_copies(bad, records, copies)
        (copies / "upstream-tree.json").write_text("tampered")
        with self.assertRaises(ValueError):
            m.validate_copies(chain, records, copies)

    def test_copychain_extra_and_alias(self) -> None:
        original = self.root / "original"
        original.mkdir()
        copies = self.root / "copies"
        copies.mkdir()
        records = {}
        chain = []
        for role, name in [
            ("upstream_tree", "upstream-tree.json"),
            ("doi_lineage", "doi-lineage.json"),
        ]:
            source = original / name
            source.write_text("{}\n")
            target = copies / name
            target.write_bytes(source.read_bytes())
            records[role] = c.pin(source)
            chain.append(
                {
                    "role": "retained_declared_metadata_input_not_new_acquisition",
                    "source": c.pin(source),
                    "copied": c.pin(target),
                }
            )
        extra = copies / "extra"
        extra.write_text("x")
        with self.assertRaises(ValueError):
            m.validate_copies(chain, records, copies)
        extra.unlink()
        target = copies / "upstream-tree.json"
        target.unlink()
        target.symlink_to(original / target.name)
        with self.assertRaises(ValueError):
            m.validate_copies(chain, records, copies)

    def test_output_traversal_existing_and_alias(self) -> None:
        with self.assertRaises(ValueError):
            c.output_root(self.root, absent=True)
        with self.assertRaises(ValueError):
            c.output_root(self.root / "child/../../escape", absent=True)
        alias = self.root / "link"
        alias.symlink_to(self.root)
        with self.assertRaises(ValueError):
            c.output_root(alias / "out", absent=True)

    def test_source_ancestor_alias_rejected(self) -> None:
        directory = self.root / "physical"
        directory.mkdir()
        (directory / "data").write_text("source")
        alias = self.root / "alias"
        alias.symlink_to(directory, target_is_directory=True)
        with self.assertRaises(ValueError):
            c.pin(alias / "data")

    def test_output_FIFO_and_inclusive_limit(self) -> None:
        file = self.root / "file"
        file.write_text("x")
        with self.assertRaises(ValueError):
            accounted_receipt(self.root, {"actual_exit": 0}, 1)
        pipe = self.root / "pipe"
        os.mkfifo(pipe)
        with self.assertRaises(ValueError):
            accounted_receipt(self.root, {"actual_exit": 0}, 100000)

    def test_typed_union_and_original_mutation(self) -> None:
        source = self.root / "source"
        source.write_text("original")
        row = c.pin(source)
        self.assertEqual(c.union([row], [row]), [row])
        with self.assertRaises(ValueError):
            c.union([row], [{**row, "bytes": 1}])
        source.write_text("changed")
        self.assertNotEqual(c.pin(source), row)
        with self.assertRaises(ValueError):
            c.verify_inputs(
                {
                    "input_pins": [row],
                    "first_party_namespaces": [],
                    "absent_input_paths": [],
                }
            )
        self.assertFalse(c.exact({"v": 0}, {"v": False}))

    def test_million_unrelated_calls_do_not_read_name_or_construct_Path(self) -> None:
        class UnrelatedCode:
            co_filename = "/unrelated/site/module.py"

            @property
            def co_name(self) -> str:
                raise AssertionError("Unrelated function name inspected")

        frame = SimpleNamespace(f_code=UnrelatedCode())
        counters: dict[str, Any] = {
            "member_content_reads": [],
            "LRA_implementation_function_calls": 0,
        }
        watch = executor.member_watch(
            "/stdlib/zipfile.py",
            "/source/lra/src/",
            "/private/archive.zip",
            {"allowed"},
            counters,
        )

        def forbidden_path(*args: Any, **kwargs: Any) -> None:
            raise AssertionError("Path constructed inside callback")

        with patch.object(executor, "Path", forbidden_path):
            for _ in range(1000000):
                watch(frame, "call", None)
        self.assertEqual(
            counters,
            {"member_content_reads": [], "LRA_implementation_function_calls": 0},
        )

    def test_exact_zip_read_names_and_denials(self) -> None:
        from zipfile import ZipInfo

        counters: dict[str, Any] = {
            "member_content_reads": [],
            "LRA_implementation_function_calls": 0,
        }
        watch = executor.member_watch(
            "/stdlib/zipfile.py",
            "/source/lra/src/",
            "/private/archive.zip",
            {"allowed"},
            counters,
        )
        with ZipFile(BytesIO(), "w") as zipped:
            zipped.filename = "/private/archive.zip"
            code = SimpleNamespace(co_filename="/stdlib/zipfile.py", co_name="read")
            for member in ("allowed", ZipInfo("allowed")):
                watch(
                    SimpleNamespace(
                        f_code=code, f_locals={"self": zipped, "name": member}
                    ),
                    "call",
                    None,
                )
            self.assertEqual(counters["member_content_reads"], ["allowed", "allowed"])
            for bad_member in ("output.gpkg", "private-editor", None):
                with self.assertRaises(ValueError):
                    watch(
                        SimpleNamespace(
                            f_code=code, f_locals={"self": zipped, "name": bad_member}
                        ),
                        "call",
                        None,
                    )

    def test_other_archive_and_function_not_attributed_to_selected_archive(
        self,
    ) -> None:
        counters: dict[str, Any] = {
            "member_content_reads": [],
            "LRA_implementation_function_calls": 0,
        }
        watch = executor.member_watch(
            "/stdlib/zipfile.py",
            "/source/lra/src/",
            "/private/archive.zip",
            {"allowed"},
            counters,
        )
        with ZipFile(BytesIO(), "w") as zipped:
            zipped.filename = "/private/other.zip"
            code = SimpleNamespace(co_filename="/stdlib/zipfile.py", co_name="read")
            watch(
                SimpleNamespace(
                    f_code=code, f_locals={"self": zipped, "name": "not-allowed-here"}
                ),
                "call",
                None,
            )
            watch(
                SimpleNamespace(
                    f_code=code,
                    f_locals={
                        "self": SimpleNamespace(filename="/private/archive.zip"),
                        "name": "not-allowed-here",
                    },
                ),
                "call",
                None,
            )
            watch(
                SimpleNamespace(
                    f_code=SimpleNamespace(
                        co_filename="/stdlib/zipfile.py", co_name="write"
                    )
                ),
                "call",
                None,
            )
        self.assertEqual(counters["member_content_reads"], [])

    def test_exact_LRA_prefix_denial_and_neighbour_noncall_omission(self) -> None:
        counters: dict[str, Any] = {
            "member_content_reads": [],
            "LRA_implementation_function_calls": 0,
        }
        watch = executor.member_watch(
            "/stdlib/zipfile.py",
            "/source/lra/src/",
            "/private/archive.zip",
            {"allowed"},
            counters,
        )
        with self.assertRaises(ValueError):
            watch(
                SimpleNamespace(
                    f_code=SimpleNamespace(
                        co_filename="/source/lra/src/fit.py", co_name="fit"
                    )
                ),
                "call",
                None,
            )
        self.assertEqual(counters["LRA_implementation_function_calls"], 1)
        watch(
            SimpleNamespace(
                f_code=SimpleNamespace(
                    co_filename="/source/lra/src/model.py", co_name="<module>"
                )
            ),
            "call",
            None,
        )

        class Neighbour:
            co_filename = "/source/lra/src-neighbour/model.py"

            @property
            def co_name(self) -> str:
                raise AssertionError("Unrelated neighbour name inspected")

        watch(SimpleNamespace(f_code=Neighbour()), "call", None)
        watch(None, "return", None)
        self.assertEqual(counters["LRA_implementation_function_calls"], 1)


if __name__ == "__main__":
    unittest.main()
