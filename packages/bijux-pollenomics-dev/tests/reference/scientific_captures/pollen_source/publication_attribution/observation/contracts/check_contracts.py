"""Exercise only controlled publication, input-custody and entrypoint guards."""

from __future__ import annotations

import ast
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from typing import Any, cast
import unittest
from urllib.parse import quote

_entry_path = Path(__file__).absolute()
if _entry_path != _entry_path.resolve(strict=True) or any(
    p.is_symlink() for p in (_entry_path, *_entry_path.parents)
):
    raise ValueError("Physical absolute controller entry and ancestors required")
_entry_directory = _entry_path.parent
_expected_python = {
    "common_runner.py",
    "prepare.py",
    "run.py",
    "runtime_contracts.py",
    "check_contracts.py",
    "runtime_guarded_runner.py",
    "source_runtime.py",
    "observe.py",
    "execute_source.py",
    "contracts.py",
    "metadata.py",
    "observation_custody.py",
    "check_observation.py",
}
_present_python = set()
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or not (_entry.is_dir() or _entry.is_file()):
        raise ValueError("Controller alias/special entry before helper import")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller directory before helper import")
    if _entry.suffix in {".py", ".pyc", ".so", ".dylib", ".pyd"}:
        if _entry.name not in _expected_python:
            raise ValueError("Unexpected controller import before helper import")
        _present_python.add(_entry.name)
if _present_python != _expected_python:
    raise ValueError("Incomplete exact controller import namespace")
sys.path.insert(0, str(_entry_directory))
import contracts as c  # noqa: E402
from execute_source import call_watcher, deny_network, guard_destination  # noqa: E402
import metadata as m  # noqa: E402


def wire(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode()


def provider(primary: Any = True) -> dict[str, Any]:
    return {
        "status": "success",
        "data": [
            {
                "publication": {
                    "publicationid": 7,
                    "datasets": [{"datasetid": 20, "primary": primary}],
                    "citation": "Ångström; literal source",
                    "doi": "10.1/NativeCase",
                    "year": 0,
                    "pubtype": None,
                    "author": ["Author", "Å"],
                }
            }
        ],
    }


def registry(doi: str, target: int = 20) -> dict[str, Any]:
    return {
        "data": {
            "type": "dois",
            "attributes": {
                "doi": doi,
                "created": "native-created",
                "publicationYear": 2025,
                "titles": [{"title": "Å native title", "lang": "sv"}],
                "url": f"http://data.neotomadb.org/datasets/{target}",
                "version": None,
                "relatedIdentifiers": [],
            },
        }
    }


class PublicationGuards(unittest.TestCase):
    def test_complete_controlled_used_dataset_projection_and_country_refusals(
        self,
    ) -> None:
        sources = []
        selected = []
        raw_responses = {}
        manifest_rows = []
        countries = ["SE"] * 3 + ["DK"] * 2 + ["NO"] * 52 + ["FI"] * 28
        for index in range(209):
            token = 20 + index
            identity = f"neotoma:dataset:{token}"
            dois = (
                [f"10.1/a{token}", f"10.1/b{token}"]
                if index < 13
                else [f"10.1/C{token}", f"10.1/c{token}"]
                if index < 16
                else [f"10.1/s{token}"]
            )
            source = {
                "dataset_id": identity,
                "source_dataset_id": token,
                "source_payload": {
                    "doi": dois,
                    "datasetpi": [{"contactname": "Å source investigator"}],
                    "database": "European Pollen Database",
                    "datasetnotes": None,
                },
            }
            sources.append(source)
            if index >= 85:
                continue
            selected.append(
                {
                    "dataset_id": identity,
                    "site_id": f"neotoma:site:{token}",
                    "country_code": countries[index],
                    "direct_pollen_study_disposition": "included",
                    "source_dataset_row_sha256": m.digest(
                        json.dumps(
                            source, sort_keys=True, separators=(",", ":")
                        ).encode()
                    ),
                }
            )
            value = provider()
            value["data"][0]["publication"]["datasets"][0]["datasetid"] = token
            value["data"][0]["publication"]["year"] = 1998
            if index in (79, 80, 81):
                second = copy.deepcopy(value["data"][0])
                second["publication"]["publicationid"] = 8
                value["data"].append(second)
            if index in (82, 83):
                value["data"] = []
            if index == 84:
                value["data"][0]["publication"]["datasets"][0]["primary"] = None
            raw_responses[token] = wire(value)
        for index in range(84):
            raw_responses[2000 + index] = wire({"status": "success", "data": []})
        for token, raw in raw_responses.items():
            manifest_rows.append(
                {
                    "dataset_id": token,
                    "path": f"responses/dataset-{token}-publications.json",
                    "http_status": 200,
                    "sha256": m.digest(raw),
                    "bytes": len(raw),
                }
            )
        dataset_raw = wire({"rows": sources})
        entity: dict[str, Any] = {
            "schema_version": "neotoma-nordic-entity-decisions.v1",
            "direct_pollen_included_datasets": 85,
            "inputs": {
                "data/neotoma/relational/surfaces/datasets/part-00001.json": m.digest(
                    dataset_raw
                )
            },
            "decisions": selected,
        }
        manifest_raw = wire(
            {
                "schema_version": "neotoma-candidate-publication-capture.v1",
                "response_count": 169,
                "responses": manifest_rows,
            }
        )
        policy = b"controlled marker ba75c8f22491f5b5e83a835f964aedea53b62e526cf6ea36bb10b376e774b3a4"
        result = m.expected_publication(
            wire(entity), dataset_raw, policy, manifest_raw, raw_responses
        )
        self.assertEqual(result["used_dataset_count"], 85)
        self.assertFalse(result["publication_ready"])
        self.assertEqual(result["lra_accepted_samples"], 0)
        self.assertEqual(
            result["provider_publication_status_counts"],
            {
                "one_source_primary_publication": 79,
                "multiple_source_primary_publications": 3,
                "no_publication_link": 2,
                "no_source_primary_flag": 1,
            },
        )
        self.assertEqual(
            result["dataset_doi_status_counts"],
            {
                "distinct_source_dois": 13,
                "ascii_case_equivalent_source_dois": 3,
                "one_source_doi": 69,
            },
        )
        self.assertEqual(
            {k: v["used_datasets"] for k, v in result["country_denominators"].items()},
            {"SE": 3, "DK": 2, "NO": 52, "FI": 28},
        )
        for selector in (
            "country",
            "entity_hash",
            "used_count",
            "missing_unused_response",
            "bool_count",
        ):
            changed = copy.deepcopy(entity)
            responses = dict(raw_responses)
            if selector == "country":
                changed["decisions"][0]["country_code"] = "XX"
            if selector == "entity_hash":
                changed["inputs"][
                    "data/neotoma/relational/surfaces/datasets/part-00001.json"
                ] = "0" * 64
            if selector == "used_count":
                changed["decisions"].pop()
            if selector == "missing_unused_response":
                responses.pop(2000)
            if selector == "bool_count":
                changed["direct_pollen_included_datasets"] = True
            with self.subTest(selector=selector), self.assertRaises(ValueError):
                m.expected_publication(
                    wire(changed), dataset_raw, policy, manifest_raw, responses
                )

    def test_native_provider_fields_and_primary_missingness(self) -> None:
        for primary in (True, False, None):
            with self.subTest(primary=primary):
                source = provider(primary)
                original = copy.deepcopy(source)
                rows = m.provider_links(20, wire(source))
                self.assertEqual(source, original)
                self.assertIs(rows[0]["source_primary_flag"], primary)
                self.assertEqual(rows[0]["source_year"], 0)
                self.assertIsNone(rows[0]["source_publication_type"])
                self.assertEqual(rows[0]["source_authors"], ["Author", "Å"])
                canonical = (
                    json.dumps(
                        source["data"][0]["publication"],
                        ensure_ascii=False,
                        allow_nan=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n"
                ).encode()
                self.assertEqual(rows[0]["source_payload_sha256"], m.digest(canonical))
                self.assertEqual(
                    m.publication_status(rows),
                    "one_source_primary_publication"
                    if primary is True
                    else "no_source_primary_flag",
                )
        self.assertEqual(m.publication_status([]), "no_publication_link")

    def test_provider_bad_id_duplicate_nullable_flags_and_source_join_refuse(
        self,
    ) -> None:
        for selector in range(7):
            value = provider()
            if selector == 0:
                value["data"][0]["publication"]["publicationid"] = True
            if selector == 1:
                value["data"].append(copy.deepcopy(value["data"][0]))
            if selector == 2:
                value["data"][0]["publication"]["datasets"][0]["datasetid"] = 21
            if selector == 3:
                value["data"][0]["publication"]["datasets"].append(
                    {"datasetid": 20, "primary": True}
                )
            if selector == 4:
                value["data"][0]["publication"]["datasets"][0]["primary"] = 1
            if selector == 5:
                value["status"] = "error"
            if selector == 6:
                value["data"][0]["publication"]["datasets"] = None
            with (
                self.subTest(selector=selector),
                self.assertRaises((ValueError, TypeError)),
            ):
                m.provider_links(20, wire(value))
        with self.assertRaises(ValueError):
            m.provider_links(True, wire(provider()))

    def test_registry_native_title_landing_and_explicit_equivalence(self) -> None:
        first = registry("10.1/UPPER")
        second = registry("10.1/other")
        a = m.registry_record("10.1/upper", wire(first))
        b = m.registry_record("10.1/other", wire(second))
        self.assertEqual(a["registry_doi"], "10.1/UPPER")
        self.assertEqual(a["titles"], first["data"]["attributes"]["titles"])
        self.assertIsNone(a["version"])
        self.assertEqual(
            m.pair_status(20, [a, b]),
            ([], True, "same_dataset_target_without_declared_equivalence"),
        )
        a["related_identifiers"] = [
            {
                "relationType": "IsMetadataFor",
                "relatedIdentifierType": "DOI",
                "relatedIdentifier": "10.1/OTHER",
            }
        ]
        self.assertEqual(
            m.pair_status(20, [a, b])[2],
            "same_dataset_target_without_declared_equivalence",
        )
        a["related_identifiers"][0]["relationType"] = "IsIdenticalTo"
        self.assertEqual(
            m.pair_status(20, [a, b]),
            (["10.1/upper"], True, "registry_declared_identical"),
        )
        self.assertIsNone(m.landing_dataset("https://foreign.invalid/datasets/20"))
        b["landing_dataset_id"] = 21
        a["related_identifiers"] = []
        self.assertEqual(m.pair_status(20, [a, b])[2], "registry_target_mismatch")
        for doi in ("10.1/different", "10.1/Å"):
            with self.subTest(doi=doi), self.assertRaises(ValueError):
                m.registry_record(doi, wire(first))

    def test_complete_thirteen_pair_projection_preserves_titles_and_refusals(
        self,
    ) -> None:
        selected = []
        rows = []
        responses = {}
        for index in range(13):
            token = 20 + index
            names = [f"10.1/a{token}", f"10.1/b{token}"]
            selected.append(
                {
                    "dataset_id": f"neotoma:dataset:{token}",
                    "site_id": f"neotoma:site:{token}",
                    "country_code": "FI",
                    "dataset_doi_status": "distinct_source_dois",
                    "dataset_dois": names,
                }
            )
            for position, doi in enumerate(names, 1):
                value = registry(doi, token)
                if index < 3 and position == 1:
                    value["data"]["attributes"]["relatedIdentifiers"] = [
                        {
                            "relationType": "IsIdenticalTo",
                            "relatedIdentifierType": "DOI",
                            "relatedIdentifier": names[1],
                        }
                    ]
                raw = wire(value)
                path = f"responses/dataset-{token}-doi-{position}.json"
                responses[path] = raw
                rows.append(
                    {
                        "dataset_id": token,
                        "source_doi": doi,
                        "path": path,
                        "url": "https://api.datacite.org/dois/" + quote(doi, safe=""),
                        "http_status": 200,
                        "sha256": m.digest(raw),
                        "bytes": len(raw),
                    }
                )
        manifest = {
            "schema_version": "neotoma-nordic-distinct-doi-capture.v1",
            "response_count": 26,
            "responses": rows,
        }
        result = m.expected_doi(
            {"decisions": selected},
            b"declared actual input bytes",
            wire(manifest),
            responses,
        )
        self.assertEqual(result["reviewed_dataset_count"], 13)
        self.assertEqual(result["reviewed_doi_count"], 26)
        self.assertEqual(
            result["doi_pair_status_counts"],
            {
                "registry_declared_identical": 3,
                "same_dataset_target_without_declared_equivalence": 10,
            },
        )
        self.assertEqual(result["lra_accepted_samples"], 0)
        for selector in ("title", "landing", "version", "relation", "bool", "order"):
            changed = copy.deepcopy(result)
            row = changed["decisions"][0]["registry_records"][0]
            if selector == "title":
                row["titles"][0]["title"] += " altered"
            if selector == "landing":
                row["landing_url"] += "/changed"
            if selector == "version":
                row["version"] = 0
            if selector == "relation":
                row["related_identifiers"] = []
            if selector == "bool":
                changed["lra_accepted_samples"] = False
            if selector == "order":
                changed["decisions"].reverse()
            with self.subTest(selector=selector):
                self.assertFalse(m.exact(changed, result))
        rows[0]["http_status"] = True
        with self.assertRaises(ValueError):
            m.expected_doi({"decisions": selected}, b"input", wire(manifest), responses)

    def test_duplicate_nonfinite_json_and_bool_number_distinctions(self) -> None:
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                m.object_bytes(raw)
        self.assertFalse(m.exact({"zero": 0}, {"zero": False}))
        self.assertFalse(m.exact([1, 2], [2, 1]))

    def test_expected_pin_union_refuses_source_or_archive_change_during_census(
        self,
    ) -> None:
        for role in ("controller", "capture-response", "capture-manifest"):
            old = {"path": "/declared/" + role, "sha256": "a" * 64, "bytes": 1}
            frozen = c.union([old])
            old["sha256"] = "c" * 64
            self.assertEqual(frozen[0]["sha256"], "a" * 64)
            changed = {**frozen[0], "sha256": "b" * 64}
            with self.subTest(role=role), self.assertRaises(ValueError):
                c.union(frozen, [changed])
        with self.assertRaises(ValueError):
            c.union([{"path": "/declared", "sha256": "a" * 64, "bytes": True}])

    def test_actual_common_plan_schema_and_stage_bindings(self) -> None:
        tree = ast.parse((c.SOURCE / "common_runner.py").read_bytes())
        accesses = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "plan"
            and isinstance(node.slice, ast.Constant)
        ]
        expected = {
            "repository",
            "output",
            "canonical_identity",
            "input_pins",
            "absent_input_paths",
            "stages",
            "resources",
            "environment",
            "candidate",
            "scope",
        }
        self.assertEqual(
            {cast(ast.Constant, node.slice).value for node in accesses}, expected
        )
        fake: dict[str, Any] = {
            name: []
            if name.endswith("paths") or name in ("stages", "input_pins")
            else {}
            for name in expected
        }
        for node in accesses:
            eval(compile(ast.Expression(node), "common-schema", "eval"), {"plan": fake})
        del fake["absent_input_paths"]
        fake["absent_paths"] = []
        expression = next(
            node
            for node in accesses
            if cast(ast.Constant, node.slice).value == "absent_input_paths"
        )
        with self.assertRaises(KeyError):
            eval(
                compile(ast.Expression(expression), "common-schema", "eval"),
                {"plan": fake},
            )
        stages = [
            {"id": "provider", "argv": ["owned", "provider"]},
            {"id": "doi", "argv": ["owned", "doi"]},
        ]
        native = [{**row, "actual_exit": 0, "timed_out": False} for row in stages]
        m.native_progress(native, stages)
        for key, value in (
            ("actual_exit", False),
            ("actual_exit", 2),
            ("timed_out", True),
            ("argv", ["other"]),
        ):
            changed = copy.deepcopy(native)
            changed[1][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                m.native_progress(changed, stages)

    def test_entry_prefix_refuses_native_shadows_aliases_fifo_and_unknown_directories(
        self,
    ) -> None:
        entries = (
            "prepare.py",
            "execute_source.py",
            "observe.py",
            "run.py",
            "runtime_guarded_runner.py",
        )
        with tempfile.TemporaryDirectory(dir=c.SOURCE / "preflight") as temporary:
            root = Path(temporary)
            for name in c.MODULES:
                (root / name).write_text("")
            for entry in entries:
                raw = (c.SOURCE / entry).read_text()
                tree = ast.parse(raw)
                imports = [
                    node
                    for node in tree.body
                    if isinstance(node, (ast.Import, ast.ImportFrom))
                    and (
                        (
                            isinstance(node, ast.Import)
                            and any(
                                alias.name in {"contracts", "metadata"}
                                for alias in node.names
                            )
                        )
                        or (
                            isinstance(node, ast.ImportFrom)
                            and node.module in {"contracts", "source_runtime"}
                        )
                    )
                ]
                self.assertTrue(imports)
                prefix = "\n".join(raw.splitlines()[: imports[0].lineno - 1])
                for selector in (
                    "positive",
                    "contracts.so",
                    "runtime.so",
                    "alias",
                    "fifo",
                    "directory",
                    "missing",
                ):
                    extra = None
                    removed = None
                    if selector.endswith(".so"):
                        extra = root / selector
                        extra.write_bytes(b"not an import")
                    if selector == "alias":
                        extra = root / "linked.json"
                        extra.symlink_to(root / "contracts.py")
                    if selector == "fifo":
                        extra = root / "pipe"
                        os.mkfifo(extra)
                    if selector == "directory":
                        extra = root / "unowned"
                        extra.mkdir()
                    if selector == "missing":
                        removed = root / "metadata.py"
                        removed.unlink()
                    original_path = list(sys.path)
                    try:
                        if selector == "positive":
                            exec(
                                compile(prefix, str(root / entry), "exec"),
                                {
                                    "__file__": str(root / entry),
                                    "__name__": "prefix_fixture",
                                },
                            )
                        else:
                            with (
                                self.subTest(entry=entry, selector=selector),
                                self.assertRaises(ValueError),
                            ):
                                exec(
                                    compile(prefix, str(root / entry), "exec"),
                                    {
                                        "__file__": str(root / entry),
                                        "__name__": "prefix_fixture",
                                    },
                                )
                    finally:
                        sys.path[:] = original_path
                        if extra is not None:
                            if extra.is_dir() and not extra.is_symlink():
                                extra.rmdir()
                            else:
                                extra.unlink()
                        if removed is not None:
                            removed.write_text("")

    def test_producer_destination_refuses_descendant_alias_and_parent_escape(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir=c.SOURCE / "preflight") as temporary:
            base = Path(temporary)
            output = base / "output"
            outside = base / "outside"
            output.mkdir()
            outside.mkdir()
            destination = output / "producer/report.json"
            guard_destination(output, destination)
            (output / "producer").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                guard_destination(output, destination)
            self.assertEqual(list(outside.iterdir()), [])
            (output / "producer").unlink()
            with self.assertRaises(ValueError):
                guard_destination(output, output / "../outside/report.json")
            (output / "producer").write_text("file ancestor")
            with self.assertRaises(ValueError):
                guard_destination(output, destination)

    def test_metadata_boundary_denial_and_unrelated_profile_calls(self) -> None:
        counts = {"LRA_implementation_function_calls": 0, "network_attempts": 0}
        watcher = call_watcher("/owned/lra/", counts)
        frame = SimpleNamespace(
            f_code=SimpleNamespace(
                co_filename="/unrelated/source.py", co_name="outside"
            )
        )
        for _ in range(10000):
            watcher(frame, "call", None)
        self.assertEqual(
            counts, {"LRA_implementation_function_calls": 0, "network_attempts": 0}
        )
        frame.f_code.co_filename = "/owned/lra/model.py"
        with self.assertRaises(ValueError):
            watcher(frame, "call", None)
        audit = deny_network(counts)
        audit("open", ())
        with self.assertRaises(ValueError):
            audit("socket.connect", ())
        self.assertEqual(
            counts, {"LRA_implementation_function_calls": 1, "network_attempts": 1}
        )


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    if not result.result.wasSuccessful():
        raise AssertionError("Controlled source guards failed")
