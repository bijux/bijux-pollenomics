"""Synthetic source-page and actual interface controls without private data parsing."""

from __future__ import annotations

import ast
from collections.abc import Callable
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).absolute().parent
ROOT = SOURCE.parents[2]
sys.path.insert(0, str(SOURCE))
from contracts import validate_private_namespace  # noqa: E402
from lake_review import canonical, decode, reconstruct  # noqa: E402
from projection_review import qualify_projection  # noqa: E402
from source_admission import reviewed_controls, verify_namespace  # noqa: E402
from source_inputs import exact_union, pin  # noqa: E402


def bundle() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    sites = {
        "schema_version": "neotoma-candidate-site-evidence.v1",
        "lra_admission_status": "refused",
        "denominators": {"lra_accepted_samples": 0, "candidate_source_sites": 3},
        "site_rows": [
            {
                "site_id": f"neotoma:site:{number}",
                "country_code": country,
                "source_site_name": f"source {number}",
            }
            for number, country in ((1, "SE"), (2, "NO"), (3, "UNASSIGNED"))
        ],
        "country_denominators": {
            country: {} for country in ("DK", "FI", "NO", "SE", "UNASSIGNED")
        },
    }
    rows = [
        {"siteid": 1, "lakeparameterid": 1, "value": 2.5},
        *[
            {"siteid": 10000 + number, "lakeparameterid": 1, "value": number}
            for number in range(999)
        ],
    ]
    documents = {
        "lakeparameters-000.json": {"status": "success", "data": rows},
        "lakeparameters-001.json": {
            "status": "success",
            "data": [{"siteid": 2, "lakeparameterid": 3, "value": 0}],
        },
        "lakeparametertypes.json": {
            "status": "success",
            "data": [
                {
                    "lakeparameterid": 1,
                    "lakeparametercode": "MaxDep",
                    "lakeparameter": "Maximum depth (m)",
                },
                {
                    "lakeparameterid": 3,
                    "lakeparametercode": "Area",
                    "lakeparameter": "Surface area (ha)",
                },
            ],
        },
    }
    capture: dict[str, Any] = {
        "schema_version": "neotoma-live-lakeparameter-custody.v1",
        "source_consistency": "live_paginated_not_transactional_snapshot",
        "basin_admission_status": "not_evaluated",
    }
    return capture, sites, documents


def encode_bundle(
    capture: dict[str, Any], sites: dict[str, Any], documents: dict[str, Any]
) -> tuple[bytes, bytes, dict[str, bytes]]:
    raw = {name: canonical(value) for name, value in documents.items()}
    site_raw = canonical(sites)
    records = []
    native = []
    for index in range(2):
        name = f"lakeparameters-{index:03d}.json"
        rows = documents[name]["data"]
        native.extend(rows)
        records.append(
            {
                "path": name,
                "url": f"https://api.neotomadb.org/v2.0/data/dbtables/lakeparameters?limit=1000&offset={index * 1000}",
                "offset": index * 1000,
                "bytes": len(raw[name]),
                "sha256": hashlib.sha256(raw[name]).hexdigest(),
                "rows": len(rows),
            }
        )
    name = "lakeparametertypes.json"
    types = documents[name]["data"]
    records.append(
        {
            "path": name,
            "url": "https://api.neotomadb.org/v2.0/data/dbtables/lakeparametertypes?limit=100&offset=0",
            "offset": 0,
            "bytes": len(raw[name]),
            "sha256": hashlib.sha256(raw[name]).hexdigest(),
            "rows": len(types),
        }
    )
    selected = {int(row["site_id"].split(":")[-1]) for row in sites["site_rows"]}
    matched = [row for row in native if row["siteid"] in selected]
    capture.update(
        candidate_site_report_sha256=hashlib.sha256(site_raw).hexdigest(),
        pages=records,
        table_rows=len(native),
        type_rows=len(types),
        candidate_site_ids=len(selected),
        candidate_site_ids_with_parameter_rows=len({row["siteid"] for row in matched}),
        candidate_parameter_rows=len(matched),
        candidate_rows=matched,
        parameter_types=types,
    )
    return canonical(capture), site_raw, raw


def parse(
    capture: bytes, sites: bytes, pages: dict[str, bytes]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    return reconstruct(
        capture,
        sites,
        pages.__getitem__,
        hashlib.sha256(capture).hexdigest(),
        hashlib.sha256(sites).hexdigest(),
    )


def hashed(row: dict[str, Any]) -> dict[str, Any]:
    value = {key: item for key, item in row.items() if key != "source_row_sha256"}
    return {**value, "source_row_sha256": hashlib.sha256(canonical(value)).hexdigest()}


def projection(report: dict[str, Any]) -> dict[str, Any]:
    basins, chronology = [], []
    for number, country in ((1, "SE"), (2, "NO"), (3, "UNASSIGNED")):
        site_id, sample = f"neotoma:site:{number}", f"sample:{number}"
        evidence = []
        for source in report["source_rows"]:
            if source["site_id"] != site_id:
                continue
            evidence.append(
                hashed(
                    {
                        "source_field": f"lakeparameters.value:{source['source_parameter_id']}",
                        "source_value": source["source_value"],
                        "source_unit": source["source_parameter_label"],
                        "source_domain": "area"
                        if source["source_parameter_code"] == "Area"
                        else "other_lakeparameter",
                        "source_row_locator": source["source_row_locator"],
                        "source_parameter_code": source["source_parameter_code"],
                        "value_status": "positive"
                        if source["source_value"] > 0
                        else "nonpositive",
                        "unit_status": "source_parameter_label",
                    }
                )
            )
        basins.append(
            hashed(
                {
                    "site_id": site_id,
                    "country_code": country,
                    "candidate_sample_count": 1,
                    "candidate_basin_evidence": evidence,
                    "support_evidence": [],
                    "basin_disposition": "not_evaluated",
                }
            )
        )
        chronology.append(
            hashed(
                {
                    "sample_id": sample,
                    "site_id": site_id,
                    "country_code": country,
                    "chronology_disposition": "not_evaluated",
                    "candidate_age_claims": [
                        hashed({"source_claim": {"subject_id": sample}})
                    ],
                }
            )
        )
    return {
        "schema_version": "neotoma-lra-prerequisite-review-projection.v1",
        "source_family": "neotoma",
        "scientific_acceptance": "not_evaluated",
        "release_status": "not_evaluated",
        "reviewer_authority": "declared_not_authenticated",
        "executable_request": None,
        "source_identities": {
            "lakeparameter_capture_sha256": report["capture_sha256"],
            "raw_manifest_sha256": "a" * 64,
            "normalized_manifest_sha256": "b" * 64,
        },
        "denominators": {
            "accepted_samples": 0,
            "source_sites": 3,
            "basin_decisions_required": 3,
            "necessary_samples": 3,
            "chronology_decisions_required": 3,
        },
        "basin_rows": basins,
        "chronology_rows": chronology,
        "country_denominators": {
            country: {
                "basin_sites": 1 if country in {"SE", "NO", "UNASSIGNED"} else 0,
                "chronology_samples": 1 if country in {"SE", "NO", "UNASSIGNED"} else 0,
                "coverage_status": "refused_unassigned_country"
                if country == "UNASSIGNED"
                else "prerequisite_review_only",
            }
            for country in ("DK", "FI", "NO", "SE", "UNASSIGNED")
        },
    }


class PageControls(unittest.TestCase):
    def test_complete_offsets_locator_values_country_and_refusals(self) -> None:
        raw, sites, pages = encode_bundle(*bundle())
        report, indexed = parse(raw, sites, pages)
        self.assertEqual(
            (
                len(indexed),
                report["candidate_source_sites"],
                report["candidate_sites_with_observed_parameter_rows"],
            ),
            (1001, 3, 2),
        )
        self.assertEqual(report["source_rows"][1]["source_value"], 0)
        self.assertEqual(report["source_rows"][1]["source_row_locator"]["row_index"], 0)
        self.assertEqual(report["candidate_sites_without_observed_parameter_rows"], 1)
        self.assertEqual(report["lra_admitted_samples"], 0)

    def refuse_source(
        self, change: Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], None]
    ) -> None:
        capture, sites, pages = bundle()
        change(capture, sites, pages)
        raw, site_raw, records = encode_bundle(capture, sites, pages)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            parse(raw, site_raw, records)

    def test_duplicate_native_key(self) -> None:
        self.refuse_source(
            lambda c, s, p: p["lakeparameters-000.json"]["data"].__setitem__(
                1, p["lakeparameters-000.json"]["data"][0]
            )
        )

    def test_boolean_numeric_value(self) -> None:
        self.refuse_source(
            lambda c, s, p: p["lakeparameters-000.json"]["data"][0].update(value=True)
        )

    def test_unknown_type(self) -> None:
        self.refuse_source(
            lambda c, s, p: p["lakeparameters-000.json"]["data"][0].update(
                lakeparameterid=999
            )
        )

    def test_duplicate_parameter_type(self) -> None:
        self.refuse_source(
            lambda c, s, p: p["lakeparametertypes.json"]["data"].__setitem__(
                1, p["lakeparametertypes.json"]["data"][0]
            )
        )

    def test_unknown_country(self) -> None:
        self.refuse_source(
            lambda c, s, p: s["site_rows"][0].update(country_code="OTHER")
        )

    def test_source_rights_or_geometry_not_promoted(self) -> None:
        self.refuse_source(lambda c, s, p: c.update(basin_admission_status="accepted"))

    def test_transactional_claim_refused(self) -> None:
        self.refuse_source(
            lambda c, s, p: c.update(source_consistency="transactional_snapshot")
        )

    def test_site_lra_admission_refused(self) -> None:
        self.refuse_source(lambda c, s, p: s.update(lra_admission_status="accepted"))

    def test_truncated_offset_page(self) -> None:
        self.refuse_source(lambda c, s, p: p["lakeparameters-000.json"]["data"].pop())

    def test_invalid_page_hash_and_size(self) -> None:
        raw, sites, pages = encode_bundle(*bundle())
        pages["lakeparameters-000.json"] += b" "
        with self.assertRaises(ValueError):
            parse(raw, sites, pages)

    def test_wrong_url_offset_and_count_type(self) -> None:
        raw, sites, pages = encode_bundle(*bundle())
        for field, value in (
            ("url", "http://untrusted/"),
            ("offset", 100),
            ("rows", True),
        ):
            capture = decode(raw)
            capture["pages"][0][field] = value
            with self.assertRaises(ValueError):
                parse(canonical(capture), sites, pages)

    def test_boolean_capture_summary(self) -> None:
        raw, sites, pages = encode_bundle(*bundle())
        capture = decode(raw)
        capture["candidate_site_ids"] = True
        with self.assertRaises(ValueError):
            parse(canonical(capture), sites, pages)

    def test_duplicate_json_and_nonfinite(self) -> None:
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.assertRaises(ValueError):
                decode(raw)


class ProjectionControls(unittest.TestCase):
    def setUp(self) -> None:
        raw, sites, pages = encode_bundle(*bundle())
        self.report, self.indexed = parse(raw, sites, pages)
        self.value = projection(self.report)

    def qualify(self, value: dict[str, Any]) -> dict[str, Any]:
        raw = canonical(value)
        return qualify_projection(
            raw, raw, self.report["capture_sha256"], self.indexed, "a" * 64, "b" * 64
        )

    def test_complete_source_joins_and_distinct_projection(self) -> None:
        proof = self.qualify(self.value)
        self.assertEqual(proof["lakeparameter_locator_joins"], 2)
        self.assertEqual(proof["accepted_samples"], 0)

    def test_scientific_typed_change_and_wire_distinction(self) -> None:
        raw = canonical(self.value)
        proof = qualify_projection(
            raw,
            b" " + raw,
            self.report["capture_sha256"],
            self.indexed,
            "a" * 64,
            "b" * 64,
        )
        self.assertEqual(proof["tracked_byte_checker_exit"], 2)
        changed = deepcopy(self.value)
        changed["denominators"]["source_sites"] = 4
        with self.assertRaises(ValueError):
            qualify_projection(
                raw,
                canonical(changed),
                self.report["capture_sha256"],
                self.indexed,
                "a" * 64,
                "b" * 64,
            )

    def test_self_consistent_wrong_lake_value(self) -> None:
        row = self.value["basin_rows"][0]
        row["candidate_basin_evidence"][0]["source_value"] = 999
        row["candidate_basin_evidence"][0] = hashed(row["candidate_basin_evidence"][0])
        self.value["basin_rows"][0] = hashed(row)
        with self.assertRaises(ValueError):
            self.qualify(self.value)

    def test_self_consistent_missing_lake_evidence(self) -> None:
        self.value["basin_rows"][0]["candidate_basin_evidence"] = []
        self.value["basin_rows"][0] = hashed(self.value["basin_rows"][0])
        with self.assertRaises(ValueError):
            self.qualify(self.value)

    def test_changed_locator_or_parameter_label(self) -> None:
        for field, value in (
            ("source_unit", "invented"),
            (
                "source_row_locator",
                {
                    "page": "lakeparameters-000.json",
                    "row_index": 1,
                    "page_sha256": "a" * 64,
                },
            ),
        ):
            changed = deepcopy(self.value)
            row = changed["basin_rows"][0]
            row["candidate_basin_evidence"][0][field] = value
            row["candidate_basin_evidence"][0] = hashed(
                row["candidate_basin_evidence"][0]
            )
            changed["basin_rows"][0] = hashed(row)
            with self.assertRaises(ValueError):
                self.qualify(changed)

    def test_human_release_or_request_promotion(self) -> None:
        for field, value in (
            ("reviewer_authority", "approved"),
            ("scientific_acceptance", "accepted"),
            ("executable_request", {}),
        ):
            changed = deepcopy(self.value)
            changed[field] = value
            with self.assertRaises(ValueError):
                self.qualify(changed)

    def test_unassigned_country_refusal(self) -> None:
        self.value["country_denominators"]["UNASSIGNED"]["coverage_status"] = "accepted"
        with self.assertRaises(ValueError):
            self.qualify(self.value)

    def test_wrong_chronology_sample_owner(self) -> None:
        row = self.value["chronology_rows"][0]
        row["candidate_age_claims"][0]["source_claim"]["subject_id"] = "other"
        row["candidate_age_claims"][0] = hashed(row["candidate_age_claims"][0])
        self.value["chronology_rows"][0] = hashed(row)
        with self.assertRaises(ValueError):
            self.qualify(self.value)


class InterfaceControls(unittest.TestCase):
    def test_actual_prepared_stage_roles_and_custody_budgets(self) -> None:
        tree = ast.parse((SOURCE / "prepare.py").read_bytes())
        plan = next(
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "plan"
            and isinstance(node.value, ast.Dict)
        )
        resources = next(
            value
            for key, value in zip(plan.keys, plan.values, strict=True)
            if isinstance(key, ast.Constant) and key.value == "resources"
        )
        actual = eval(  # noqa: S307 - restricted literal AST from owned source
            compile(ast.Expression(resources), "owned-resource-literals", "eval"),
            {"__builtins__": {}},
        )
        self.assertEqual(
            actual,
            {
                "overall_timeout_seconds": 720,
                "outer_timeout_seconds": 740,
                "declared_memory_bytes": 4 * 1024**3,
                "declared_storage_bytes": 128 * 1024**2,
            },
        )
        stages = next(
            ast.literal_eval(node.value)
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "selections"
                for target in node.targets
            )
        )
        appended = [
            ast.literal_eval(node.args[0])
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "selections"
            and node.func.attr == "append"
        ]
        self.assertEqual(
            stages,
            [("maintained-lakeparameter-reader-checker", "execute_reader.py", 120)],
        )
        self.assertEqual(
            set(appended),
            {
                (
                    "maintained-current-prerequisite-projection",
                    "execute_projection.py",
                    240,
                ),
                (
                    "independent-lake-source-and-optional-projection-observer",
                    "observe.py",
                    120,
                ),
            },
        )
        optional = next(row for row in appended if row[1] == "execute_projection.py")
        observer = next(row for row in appended if row[1] == "observe.py")
        for selected in ([*stages, observer], [*stages, optional, observer]):
            self.assertTrue(all(type(row[2]) is int and row[2] > 0 for row in selected))
            total = sum(row[2] for row in selected)
            self.assertLessEqual(total + 240, actual["overall_timeout_seconds"])
            self.assertGreater(
                actual["outer_timeout_seconds"], actual["overall_timeout_seconds"]
            )

    def test_only_declared_budget_literals_change_preparer(self) -> None:
        previous = (
            ROOT / "artifacts/science/neotoma-lakeparameter-source-custody/prepare.py"
        )
        before = ast.parse(previous.read_bytes())
        after = ast.parse((SOURCE / "prepare.py").read_bytes())
        deltas = []
        for left, right in zip(ast.walk(before), ast.walk(after), strict=True):
            self.assertIs(type(left), type(right))
            if (
                isinstance(left, ast.Constant)
                and isinstance(right, ast.Constant)
                and left.value != right.value
            ):
                deltas.append((left.value, right.value))
                right.value = left.value
        self.assertCountEqual(
            deltas, [(360, 720), (380, 740), (45, 120), (180, 240), (60, 120)]
        )
        self.assertEqual(ast.dump(before), ast.dump(after))

    def test_loader_override_refused_before_any_git_tool(self) -> None:
        import contracts

        with (
            patch.dict("os.environ", {"LD_PRELOAD": "unadmitted"}),
            patch("contracts.subprocess.check_output") as command,
        ):
            with self.assertRaises(ValueError):
                contracts.identity()
            command.assert_not_called()

    def test_synthetic28_custody_namespace_and_alias_ancestry(self) -> None:
        with tempfile.TemporaryDirectory(dir=SOURCE / "preflight") as name:
            fixture = Path(name)
            root = fixture / "authority/source"
            (root / "capture-pages").mkdir(parents=True)
            paths = [
                root / "capture.json",
                root / "site-evidence.json",
                *[root / "capture-pages" / f"page-{index}.json" for index in range(26)],
            ]
            for path in paths:
                path.write_bytes(b"synthetic hash-only identity")
            expected = sorted(
                (pin(path) for path in paths), key=lambda row: row["path"]
            )
            validate_private_namespace(root, expected)
            alias = fixture / "alias"
            alias.symlink_to(fixture / "authority", target_is_directory=True)
            aliased_root = alias / "source"
            aliased = [
                {**row, "path": str(aliased_root / Path(row["path"]).relative_to(root))}
                for row in expected
            ]
            with self.assertRaises(ValueError):
                validate_private_namespace(aliased_root, aliased)
            (root / "unlisted").mkdir()
            with self.assertRaises(ValueError):
                validate_private_namespace(root, expected)

    def test_exact28_declaration_without_opening_private_pages(self) -> None:
        value = json.loads((SOURCE / "declared-inputs.json").read_bytes())
        rows = value["private_expected_pins"]
        self.assertEqual(len(rows), 28)
        self.assertEqual(sum(row["bytes"] for row in rows), 3549257)
        self.assertEqual(len({row["path"] for row in rows}), 28)
        self.assertTrue(
            all(
                Path(row["path"]).is_relative_to(Path(value["capture_root"]))
                for row in rows
            )
        )
        self.assertEqual(len(value["optional_inputs"]), 30)

    def test_original_reader_actual_cli_and_no_output_writer(self) -> None:
        source = ROOT / "docs/report/source-relations/neotoma/lakeparameters/verify.py"
        tree = ast.parse(source.read_bytes())
        parser_options = [
            ast.literal_eval(call.args[0])
            for call in ast.walk(tree)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "add_argument"
        ]
        self.assertEqual(parser_options, ["--capture-root"])
        self.assertFalse(
            any(
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr in {"write_bytes", "write_text"}
                for call in ast.walk(tree)
            )
        )

    def test_original_common_plan_schema_and_required_fields(self) -> None:
        raw = (SOURCE / "common_runner.py").read_bytes()
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "9062395231bd7a4ec19bfe41df1587281c06e143b146119fe445a6eb0ce7ce8a",
        )
        common = ast.parse(raw)
        required = {
            node.slice.value
            for node in ast.walk(common)
            if isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "plan"
            and isinstance(node.slice, ast.Constant)
        }
        prepared = ast.parse((SOURCE / "prepare.py").read_bytes())
        plan = next(
            node.value
            for node in ast.walk(prepared)
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "plan"
            and isinstance(node.value, ast.Dict)
        )
        declared = {key.value for key in plan.keys if isinstance(key, ast.Constant)}
        self.assertTrue(required <= declared | {"stages"})
        self.assertIn("absent_input_paths", declared)
        common_identity = next(
            node
            for node in common.body
            if isinstance(node, ast.FunctionDef) and node.name == "identity"
        )
        owned = ast.parse((SOURCE / "contracts.py").read_bytes())
        owned_identity = next(
            node
            for node in owned.body
            if isinstance(node, ast.FunctionDef) and node.name == "identity"
        )
        for function in (common_identity, owned_identity):
            identity_dict = next(
                node.value
                for node in ast.walk(function)
                if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)
            )
            self.assertEqual(
                {
                    key.value
                    for key in identity_dict.keys
                    if isinstance(key, ast.Constant)
                },
                {"candidate", "status", "tracked_inventory_sha256"},
            )

    def test_actual_optional_cli_options(self) -> None:
        source = (
            ROOT
            / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/taxa_review/lra_prerequisites/__main__.py"
        )
        tree = ast.parse(source.read_bytes())
        options = {
            ast.literal_eval(call.args[0])
            for call in ast.walk(tree)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "add_argument"
        }
        self.assertEqual(
            options,
            {
                "--raw-root",
                "--normalized-root",
                "--lakeparameter-capture-root",
                "--lakeparameter-capture-sha256",
                "--output",
            },
        )

    def test_conflicting_expected_pins_refused(self) -> None:
        row = {"path": "/source", "sha256": "a" * 64, "bytes": 1}
        self.assertEqual(exact_union([row], [row]), [row])
        for group in ([row, row], [{**row, "sha256": "b" * 64}]):
            with self.assertRaises(ValueError):
                exact_union([row], group)

    def test_reviewed_actual_namespace_positive_and_shadow(self) -> None:
        names = json.loads((SOURCE / "source-layout.json").read_bytes())[
            "python_members"
        ]
        with tempfile.TemporaryDirectory(dir=SOURCE / "preflight") as name:
            root = Path(name)
            for member in names:
                (root / member).write_text("# source fixture\n")
            rows = sorted(
                (pin(root / member) for member in names), key=lambda row: row["path"]
            )
            raw = json.dumps({"source_only": True, "files": rows}).encode()
            (root / "prepared-source-manifest.json").write_bytes(raw)
            (root / "independent-source-review.json").write_text(
                json.dumps(
                    {
                        "approved": True,
                        "source_manifest_sha256": hashlib.sha256(raw).hexdigest(),
                    }
                )
            )
            reviewed_controls(root)
            (root / "contracts.so").write_bytes(b"unselected")
            with self.assertRaises(ValueError):
                verify_namespace(root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
