"""Exercise original-call, saved-observer, packet privacy and registered-stage contracts artificially."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

SOURCE = Path(__file__).absolute().parent


def main() -> None:
    sys.path.insert(0, str(SOURCE))
    import call_evidence
    from call_evidence import DENIAL, ORIGINAL_SOURCE_SHA, ZIP, qualify_original
    from callable_identity import CODE_FIELDS
    from contracts import PYTHON, RESOURCES
    from members import encoded, namespace, specification
    from packet import public_members
    import publication
    from run import validate_stages
    from runtime_evidence import PLAN_SHA
    from source_inputs import exact_union

    old = SOURCE.parent / "sweden-country-saved-semantic-custody/check_saved.py"
    body = old.read_text()
    start = body.index("    cases = []")
    end = body.index("    success = qualify_original(*original)")
    fragment = body[start:end].replace(
        '"retained-authority.json"', '"country-authority.json"'
    )
    context: dict[str, Any] = {
        "SOURCE": SOURCE,
        "Path": Path,
        "json": json,
        "CODE_FIELDS": CODE_FIELDS,
        "ORIGINAL_SOURCE_SHA": ORIGINAL_SOURCE_SHA,
        "ORIGINAL_PLAN_SHA": call_evidence.ORIGINAL_PLAN_SHA,
        "DENIAL": DENIAL,
        "ZIP": ZIP,
    }
    exec(compile("if True:\n" + fragment, str(old), "exec"), context)
    original = context["original"]
    normal = qualify_original(*original)
    cases: list[str] = [
        "genuine_original_predicate_on_artificial_normal_return_controller1_whole1"
    ]

    def refused(label: str, function: Any, *args: Any) -> None:
        try:
            function(*args)
        except (ValueError, KeyError, TypeError):
            cases.append(label)
        else:
            raise AssertionError(label)

    value: Any
    for index, key, value in (
        (1, "actual_exit", 0),
        (2, "actual_exit", False),
        (3, "actual_return_events", []),
        (3, "IO_denials", []),
        (4, "complete_typed_graphs_equal", False),
    ):
        changed = deepcopy(original)
        changed[index][key] = value
        refused("original_" + key + repr(value), qualify_original, *changed)
    country, inner, outer, clock, proof, progress, refs, runtime = deepcopy(original)
    base = SOURCE / "preflight/ARTIFICIAL"
    base.mkdir(exist_ok=True)

    def identity(name: str, sha: str | None = None) -> dict[str, Any]:
        return {
            "path": str(base / name),
            "sha256": sha or hashlib.sha256(name.encode()).hexdigest(),
            "bytes": 1,
        }

    ids = {name: identity(name) for name in publication.REF_NAMES}
    for name, filename in (
        ("country-plan", "plan.json"),
        ("country-inner", "sweden-country-semantic-terminal.json"),
        ("country-outer", "sweden-country-semantic-launch-terminal.json"),
        ("country-progress", "stage-progress.json"),
        ("country-clock", "country-clock-observation.json"),
        ("country-callable", "country-callable-identity.json"),
        ("country-products", "output-products.json"),
        ("country-receipt", "producer/receipt.json"),
    ):
        ids[name] = refs[filename]
    ids["country-controller-manifest"] = country["input_pins"][0]
    ids["saved-controller-manifest"] = identity(
        "saved-controller/prepared-source-manifest.json", publication.SAVED_SOURCE_SHA
    )
    ids["saved-controller-review"] = identity(
        "saved-controller/independent-source-review.json"
    )
    ids["country-controller-review"] = identity(
        "country-controller/independent-source-review.json"
    )
    ids["source-declaration"] = identity(
        str(
            Path(ids["country-controller-manifest"]["path"]).parent
            / "declared-inputs.json"
        )
    )
    ids["runtime-plan"] = identity("runtime-plan", PLAN_SHA)
    source_declaration: dict[str, Any] = {
        "original_owner": {
            "owner_id": publication.OWNER,
            "role": "unresolved",
            "paths": [publication.REPORT],
            "verification": "ARTIFICIAL full original criterion",
        },
        "published_roles": [{"relative_path": "summary.json"}],
    }
    country["source_declaration"] = source_declaration
    country["original_owned_source_candidate"] = "2" * 40
    runtime_authority: dict[str, Any] = {
        key: ids[name]
        for key, name in (
            ("plan", "runtime-plan"),
            ("common", "runtime-common"),
            ("outer", "runtime-outer"),
            ("independent_review", "runtime-review"),
        )
    }
    runtime_authority["lexical_python"] = str(PYTHON)
    country["qualified_source_runtime"] = runtime_authority
    country["source_ledger"] = ids["owned-source-ledger"]
    country["input_pins"] = exact_union(
        country["input_pins"],
        [
            ids[name]
            for name in (
                "country-controller-review",
                "source-declaration",
                "owned-source-ledger",
                "runtime-plan",
                "runtime-common",
                "runtime-outer",
                "runtime-review",
            )
        ],
    )
    saved = deepcopy(country)
    saved.update(
        candidate="3" * 40,
        output=str(base / "saved-output"),
        original_registered_plan_sha256=call_evidence.ORIGINAL_PLAN_SHA,
        original_country_execution_candidate=country["candidate"],
        original_saved_country_output=country["output"],
        retained_failed_controller_history=ids["saved-history"],
        resources={
            "overall_timeout_seconds": 600,
            "outer_timeout_seconds": 660,
            "declared_memory_bytes": 8 * 1024**3,
            "declared_storage_bytes": 1024**3,
        },
    )
    saved["input_pins"] = exact_union(
        country["input_pins"],
        [
            ids[name]
            for name in (
                "country-plan",
                "saved-controller-manifest",
                "saved-controller-review",
                "saved-history",
            )
        ],
    )
    stage = {
        "id": "independent-saved-country-semantic-clock-observer",
        "action": "observer",
        "timeout_seconds": 360,
        "argv": [
            str(PYTHON),
            "-I",
            "-B",
            str(Path(ids["saved-controller-manifest"]["path"]).parent / "entry.py"),
            "observer",
            "--plan",
            ids["saved-plan"]["path"],
        ],
    }
    saved["stages"] = [stage]
    sin = {
        "actual_exit": 0,
        "candidate": saved["candidate"],
        "plan_sha256": ids["saved-plan"]["sha256"],
        "products_manifest": ids["saved-products"],
        "exception": None,
        "after_custody_error": None,
        "completed_whole_wall_bound_pass": True,
        "memory_bound_pass": True,
        "inclusive_storage_bound_pass": True,
        "stages": [
            {
                **stage,
                "actual_exit": 0,
                "timed_out": False,
                "stdout": identity("saved-output/stage.stdout"),
                "stderr": identity("saved-output/stage.stderr"),
            }
        ],
    }
    sout = {
        "actual_exit": 0,
        "candidate": saved["candidate"],
        "plan_sha256": ids["saved-plan"]["sha256"],
        "inner_terminal": ids["saved-inner"],
        "registered_plan_unchanged": True,
        "child_timed_out": False,
        "child_native_exit": 0,
        "completed_outer_wall_bound_pass": True,
        "memory_bound_pass": True,
        "inclusive_storage_bound_pass": True,
        "stdout": identity("saved-output/launch.stdout"),
        "stderr": identity("saved-output/launch.stderr"),
    }
    product = {
        "path": str(Path(country["output"]) / "producer/candidate/summary.json"),
        "sha256": "7" * 64,
        "bytes": 1,
    }
    receipt: dict[str, Any] = {
        "semantic_changes": {name: [] for name in publication.CATEGORIES},
        "change_counts": dict.fromkeys(publication.CATEGORIES, 0),
        "status": "changed",
    }
    receipt["semantic_changes"]["scientific_result"] = [{"ARTIFICIAL": "changed"}]
    receipt["change_counts"]["scientific_result"] = 1
    report = {
        "actual_exit": 0,
        "candidate": saved["candidate"],
        "registered_plan_sha256": ids["saved-plan"]["sha256"],
        "original_controller_actual_exit": 1,
        "original_whole_actual_exit": 1,
        "country_call_returned_normally": True,
        "actual_country_call_return_events": 1,
        "full_captured_return_object_recovered": False,
        "original_read_or_import_origin_ledger_recovered": False,
        "independent_expected_projection_is_not_captured_return": True,
        "independent_country_producer_calls": 0,
        "full_source_resource_input_closure_bound": True,
        "original_owner_verification": source_declaration["original_owner"][
            "verification"
        ],
        "historical_generated_ownership_or_vegetation_rights_human_LRA_admitted": False,
        "original_country_execution_candidate": country["candidate"],
        "original_owned_source_candidate": country["original_owned_source_candidate"],
        "original_registered_plan_sha256": call_evidence.ORIGINAL_PLAN_SHA,
        "country_callable_identity": ids["country-callable"],
        "country_clock_observation": ids["country-clock"],
        "native_UTC_clock": normal["native_UTC_clock"],
        "exact_absent_default_import_attempt": normal[
            "exact_absent_default_import_attempt"
        ],
        "retained_call_authority": ids["saved-history"],
        "semantic_receipt": {
            "independently_reconstructed_changes": deepcopy(
                receipt["semantic_changes"]
            ),
            "tracked_byte_checker_actual_exit": 2,
            "complete_ordered_typed_synthesis_differences": [],
        },
        "actual_products": [product],
        "source_authority_unavailability": ["ARTIFICIAL missing context"],
        "human_source_joins": {},
        "animal_source_joins": {},
        "synthesis_source_joins": {},
    }
    runtime.update(
        candidate="4" * 40,
        retained_environment=str(PYTHON.parent.parent),
        stages=[{"id": "runtime", "argv": ["ARTIFICIAL"]}],
        input_pins=[],
        retained_bootstrap={
            "original_whole_actual_exit": 1,
            "production_stage_actual_exits": [0, 0, 0],
            "original_observer_actual_exit": 1,
        },
    )
    rcommon = {
        "actual_exit": 0,
        "candidate": runtime["candidate"],
        "plan_sha256": PLAN_SHA,
        "stages": [
            {
                "id": "runtime",
                "argv": ["ARTIFICIAL"],
                "actual_exit": 0,
                "timed_out": False,
            }
        ],
    }
    router = {
        "actual_exit": 0,
        "candidate": runtime["candidate"],
        "plan_sha256": PLAN_SHA,
        "common_actual_exit": 0,
        "timed_out": False,
        "input_after_failures": [],
        "runtime_alias_after_failure": None,
        "memory_bound_pass": True,
        "storage_bound_pass": True,
        "overall_wall_bound_pass": True,
        "original_bootstrap_whole_actual_exit": 1,
        "production_stages_repeated": False,
    }
    rreview = {
        "actual_exit": 0,
        "candidate": runtime["candidate"],
        "new_environment": str(PYTHON.parent.parent),
        "selected_distribution_count": 147,
        "distributions": [{}] * 147,
        "new_observation_only": True,
        "first_party_editable_metadata_copied": False,
        "old_runtime_recovered_or_same_process_claimed": False,
        "installed_first_party_interface_claimed": False,
        "original_bootstrap_whole_actual_exit": 1,
    }
    early_root = base / "pre-country"
    early_names = {
        "plan.json",
        "sweden-country-semantic-terminal.json",
        "sweden-country-semantic-launch-terminal.json",
        "output-products.json",
        "stage-progress.json",
        "original-source-ledger.json",
        "maintained-full-Sweden-country-consumer.stdout",
        "maintained-full-Sweden-country-consumer.stderr",
        "launch.stdout",
        "launch.stderr",
    }
    early_rows = [identity("pre-country/" + name) for name in sorted(early_names)]
    early_source = identity("sweden-country-semantic-custody/controller.py")
    source = identity("owned/packages/example/src/module.py")
    comparand = identity("owned/docs/report/countries/sweden/summary.json")
    private = identity("owned/data/private.json")
    ledger = {
        "canonical_identity": {"candidate": country["original_owned_source_candidate"]},
        "copied_sources": [source],
        "copied_data_inputs": [comparand, private],
        "original_sources": [identity("original-source.py")],
        "original_data_inputs": [identity("original-private.json")],
        "omitted_unselected_cache_bytecode": [],
        "omitted_configured_generated_metadata": [],
    }
    country["owned_repository"] = saved["owned_repository"] = str(base / "owned")
    # Retain the exact artificial call signature after the owned root is selected.
    clock["actual_country_calls"][0].update(
        version_dir=str(base / "owned/data/aadr/v66"),
        context_root=str(base / "owned/data"),
    )
    country["input_pins"] = exact_union(
        country["input_pins"], [early_source, source, comparand, private]
    )
    saved["input_pins"] = exact_union(saved["input_pins"], country["input_pins"])
    documents = {
        "country-plan": country,
        "country-inner": inner,
        "country-outer": outer,
        "country-clock": clock,
        "country-progress": progress,
        "country-callable": proof,
        "country-products": {"files": [product]},
        "country-receipt": receipt,
        "owned-source-ledger": ledger,
        "runtime-plan": runtime,
        "runtime-common": rcommon,
        "runtime-outer": router,
        "runtime-review": rreview,
        "saved-plan": saved,
        "saved-inner": sin,
        "saved-outer": sout,
        "saved-review": report,
        "saved-products": {
            "files": [
                ids[name] for name in ("saved-review", "saved-plan", "saved-history")
            ]
        },
        "saved-history": {"country_call_returned_normally": True},
        "source-declaration": source_declaration,
        "pre-country-history": {
            "original_complete_namespace": {"root": str(early_root)},
            "original_outputs": early_rows,
        },
    }
    for prefix, sha, files in (
        ("country", ORIGINAL_SOURCE_SHA, [ids["source-declaration"]]),
        ("saved", publication.SAVED_SOURCE_SHA, []),
    ):
        documents[prefix + "-controller-manifest"] = {
            "source_only": True,
            "files": files,
        }
        documents[prefix + "-controller-review"] = {
            "approved": True,
            "source_manifest_sha256": sha,
        }
    authority = {"documents": documents, "identities": ids, "original_references": refs}
    witness = publication.qualify_saved(documents, ids, refs)
    assert (
        witness["tracked_byte_checker_actual_exit"] == 2
        and witness["original_whole_actual_exit"] == 1
    )
    assert (
        witness["saved_whole_actual_exit"] == 0
        and witness["missing_full_return_read_or_import_telemetry_recovered"] is False
    )
    cases.append(
        "complete_actual_saved_qualifier_with_original1_normalreturn_and_separate_saved0"
    )
    for role, key, value in (
        ("saved-inner", "actual_exit", False),
        ("saved-outer", "child_native_exit", 1),
        ("saved-review", "full_captured_return_object_recovered", True),
        ("saved-review", "independent_country_producer_calls", 1),
        (
            "saved-review",
            "historical_generated_ownership_or_vegetation_rights_human_LRA_admitted",
            True,
        ),
        ("saved-review", "original_owner_verification", "weaker"),
        ("saved-review", "original_whole_actual_exit", 0),
        ("saved-inner", "after_custody_error", "bad"),
        ("saved-outer", "memory_bound_pass", False),
    ):
        changed = deepcopy(documents)
        changed[role][key] = value
        refused(role + "_" + key, publication.qualify_saved, changed, ids, refs)
    for role in ("saved-history", "saved-review"):
        changed = deepcopy(documents)
        if role == "saved-history":
            changed["saved-plan"]["input_pins"] = [
                r for r in changed["saved-plan"]["input_pins"] if r != ids[role]
            ]
        else:
            changed["saved-products"]["files"] = [
                r for r in changed["saved-products"]["files"] if r != ids[role]
            ]
        refused(
            "wrong_role_membership_" + role,
            publication.qualify_saved,
            changed,
            ids,
            refs,
        )
    changed = deepcopy(documents)
    changed["country-receipt"]["semantic_changes"]["scientific_result"] = []
    refused(
        "semantic_difference_not_erased", publication.qualify_saved, changed, ids, refs
    )
    changed = deepcopy(documents)
    changed["saved-review"]["actual_products"][0]["path"] = str(
        base / "saved-output/producer/candidate/summary.json"
    )
    refused(
        "saved_root_not_country_product_root",
        publication.qualify_saved,
        changed,
        ids,
        refs,
    )
    roles, omissions = public_members(authority)
    assert not any(row["source_identity"]["path"] == private["path"] for row in roles)
    assert omissions["owned_private_input_identities"] == [private]
    cases.append(
        "original_private_bodies_excluded_and_all_ordered_input_roles_retained"
    )
    capture, payloads = specification(authority, "5" * 40, "6" * 64)
    assert (
        len(payloads) == len(capture["members"])
        and capture["metadata_registered_plan_sha256"] == "6" * 64
    )
    assert set(capture["references"]) == set(publication.REF_NAMES)
    cases.append(
        "complete_packet_metadata_reconstruction_and_content_address_deduplication"
    )
    changed = deepcopy(authority)
    changed["documents"]["owned-source-ledger"]["copied_sources"].append(
        identity("escaped.py")
    )
    refused("escaped_owned_source", public_members, changed)
    for name in ("", ".", "members/../x", "members/" + "0" * 64):
        refused(
            "unsafe_member_" + repr(name),
            namespace,
            base,
            {name: {"sha256": "1" * 64, "bytes": 0}},
        )
    plan_path = base / "plan.json"
    stages = [
        {
            "id": name,
            "action": action,
            "timeout_seconds": 180,
            "argv": [
                str(PYTHON),
                "-I",
                "-B",
                str(SOURCE / "entry.py"),
                action,
                "--plan",
                str(plan_path),
            ],
        }
        for name, action in (
            ("portable-returned-country-source-assembly", "assembler"),
            ("independent-portable-country-source-observer", "observer"),
        )
    ]
    schedule: dict[str, Any] = {"resources": deepcopy(RESOURCES), "stages": stages}
    validate_stages(schedule, plan_path)
    cases.append("actual_two_metadata_stage_schedule")
    for index, key, value in (
        (0, "action", "producer"),
        (1, "timeout_seconds", False),
        (0, "id", "wrong"),
    ):
        changed = deepcopy(schedule)
        changed["stages"][index][key] = value
        refused("stage_" + key, validate_stages, changed, plan_path)
    changed = deepcopy(schedule)
    changed["stages"].reverse()
    refused("stage_order", validate_stages, changed, plan_path)
    tree = ast.parse((SOURCE / "prepare.py").read_bytes())
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "mkdir"
    ]
    assert calls and "forecast = encoded(plan)" in (SOURCE / "prepare.py").read_text()
    assert not any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id in {"bootstrap", "replay", "generate_country_report"}
        for filename in ("assemble.py", "observe.py", "prepare.py")
        for n in ast.walk(ast.parse((SOURCE / filename).read_bytes()))
    )
    cases.append("no_retained_code_import_or_country_API_dispatch")
    # Only artificial files are used for registered-buffer and ancestry checks.
    from types import SimpleNamespace
    from unittest.mock import patch

    import contracts

    registered = base / "registered.json"
    registered_raw = encoded({"ARTIFICIAL": True})
    registered.write_bytes(registered_raw)
    digest = hashlib.sha256(registered_raw).hexdigest()
    assert contracts.registered_plan(registered, digest) == {"ARTIFICIAL": True}
    for invalid_digest in ("", "0" * 64, False, None):
        refused(
            "registered_digest_" + repr(invalid_digest),
            contracts.registered_plan,
            registered,
            invalid_digest,
        )
    with patch.object(
        Path, "read_bytes", side_effect=[registered_raw, b"REBOUND"]
    ) as reader:
        assert contracts.registered_plan(registered, digest) == {"ARTIFICIAL": True}
        assert reader.call_count == 1
    cases.append("actual_registered_parser_hashes_and_parses_one_buffer")
    original_dir = base / "original-physical"
    original_dir.mkdir(exist_ok=True)
    original_file = original_dir / "source.txt"
    original_file.write_text("ARTIFICIAL")
    scoped: Any = SimpleNamespace(verify=lambda: None)
    with patch.multiple(
        contracts,
        reviewed_controls=lambda root: None,
        authenticate_runtime=lambda: ({}, []),
        verify_base_namespaces=lambda snapshots: None,
    ):
        contracts.checkpoint({}, scoped, [], [str(original_file)])
        cases.append("actual_checkpoint_original_ancestry_positive")
        alias = base / "original-alias"
        alias.symlink_to(original_dir, target_is_directory=True)
        try:
            refused(
                "actual_checkpoint_same_byte_ancestor_alias",
                contracts.checkpoint,
                {},
                scoped,
                [],
                [str(alias / "source.txt")],
            )
        finally:
            alias.unlink()
    packet_root = base / "artificial-packet"
    if packet_root.exists():
        __import__("shutil").rmtree(packet_root)
    (packet_root / "members").mkdir(parents=True)
    content = b"ARTIFICIAL public payload"
    content_sha = hashlib.sha256(content).hexdigest()
    member = "members/" + content_sha
    (packet_root / member).write_bytes(content)
    (packet_root / "capture.json").write_bytes(encoded({"ARTIFICIAL": True}))
    member_rows = {member: {"sha256": content_sha, "bytes": len(content)}}
    namespace(packet_root, member_rows)
    cases.append("actual_complete_artificial_packet_namespace_and_hash_positive")
    (packet_root / "unknown.txt").write_text("ARTIFICIAL")
    refused("packet_unknown_member", namespace, packet_root, member_rows)
    (packet_root / "unknown.txt").unlink()
    (packet_root / member).write_bytes(b"TAMPER")
    refused("packet_changed_bytes", namespace, packet_root, member_rows)
    summary: dict[str, Any] = {
        "actual_exit": 0,
        "scope": "Artificial source contracts only; no real product/private/runtime read or packet assembly",
        "case_count": len(cases),
        "cases": cases,
    }
    (SOURCE / "preflight/source-controls.json").write_bytes(encoded(summary))
    print(json.dumps({"actual_exit": 0, "case_count": len(cases)}))


if __name__ == "__main__":
    main()
