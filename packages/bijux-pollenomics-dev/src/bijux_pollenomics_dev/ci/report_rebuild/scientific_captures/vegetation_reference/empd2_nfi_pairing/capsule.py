"""Transport retained public source and refusal bytes without private or runtime payloads."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ....contracts import JsonObject, ReportRebuildError
from ....ownership import ReportOwnershipError, _regular_confined_file
from ....retained_source import validate_capsule
from .execution import (
    CAPTURE,
    CAPTURE_SHA256,
    MEMBER_COUNT,
    ORIGINAL_CANDIDATE,
    OWNER,
    PRODUCTS,
    RECEIPTS,
    REPORT_ROOT,
    SCOPE_COUNTS,
    TIMEOUT_RECEIPTS,
    _exact,
    _json,
    _native_records,
    _object,
    _pin,
    _public_refusals,
    _read_json,
    _require,
)

ADDITIONAL_DETACHED_SOURCE_MEMBERS = frozenset(
    [
        "control/check_contracts.py",
        "control/common_runner.py",
        "control/contracts.py",
        "control/execute_source.py",
        "control/metadata.py",
        "control/observe.py",
        "control/preflight/qualify_source.py",
        "control/preflight/source_style.py",
        "control/prepare.py",
        "control/run.py",
        "control/runtime_contracts.py",
        "control/runtime_guarded_runner.py",
        "control/source_runtime.py",
        "timeout-observation/control/check_contracts.py",
        "timeout-observation/control/common_runner.py",
        "timeout-observation/control/contracts.py",
        "timeout-observation/control/execute_source.py",
        "timeout-observation/control/metadata.py",
        "timeout-observation/control/observe.py",
        "timeout-observation/control/prepare.py",
        "timeout-observation/control/run.py",
        "timeout-observation/control/runtime_contracts.py",
        "timeout-observation/control/runtime_guarded_runner.py",
        "timeout-observation/control/source_runtime.py",
    ]
)


def _validate_source_transport(
    repository: Path, prefix: str, members: dict[str, Any]
) -> None:
    """Validate the original logical members without embedding package source trees."""
    detached = validate_capsule(
        repository,
        prefix,
        members,
    )
    _exact(
        sorted(detached),
        sorted(
            name
            for name in members
            if name in ADDITIONAL_DETACHED_SOURCE_MEMBERS
            or name.startswith("source/packages/")
        ),
    )


def _name(value: object) -> str:
    _require(type(value) is str and bool(value), "EMPD2/NFI member name required")
    assert isinstance(value, str)
    path = PurePosixPath(value)
    _require(
        not path.is_absolute()
        and ".." not in path.parts
        and path.as_posix() == value
        and "\\" not in value,
        "EMPD2/NFI member escapes capsule",
    )
    return value


def _file(repository: Path, name: str) -> Path:
    try:
        return _regular_confined_file(
            repository, name, "EMPD2/NFI retained source refusal"
        )
    except (OSError, ReportOwnershipError) as error:
        raise ReportRebuildError(
            "EMPD2/NFI retained file is absent, aliased or unconfined"
        ) from error


def _capture_claims(capture: dict[str, Any]) -> None:
    expected = {
        "schema_version": "empd2-nfi-outcome-blind-source-capture.v1",
        "owner_id": "validation/empd2-nfi-pairing/report-products",
        "publication_members": {
            "docs/report/validation/empd2-nfi-pairing/pairs.csv": "publication/pairs.csv",
            "docs/report/validation/empd2-nfi-pairing/report.json": "publication/report.json",
        },
        "original_execution_candidate": "97be88f37a117a518c8c4639ccca98927e13cb24",
        "retention_mode": "authored_public_source_and_execution_custody",
        "new_metadata_native_execution_claimed": False,
        "member_count": 2286,
        "original_input_count": 66501,
        "original_input_custody_member": "original-input-custody.json",
        "public_first_party_source_members": 2159,
        "omitted_first_party_bytecode_identities": 4356,
        "bytecode_payloads_or_fresh_compilation_equivalence_claimed": False,
        "original_native_stage_exits": [0, 0],
        "private_input_payloads_included": False,
        "private_source_bound_pair_payload_included": False,
        "runtime_payloads_included": False,
        "source_refusal_scope": {
            "NFI_metadata_rows": 43892,
            "NFI_tract_plot_keys": 6018,
            "selected_metadata_cells": 263358,
            "native_source_pairs": 16,
            "source_fields": 26,
            "public_fields": 19,
            "excluded_private_location_fields": 8,
            "measured_pairs_admitted": 0,
            "refusals": 16,
            "outcome_columns_decoded": 0,
            "LRA_implementation_function_calls": 0,
            "all_53_spatial_combinations_recomputed": False,
            "raw_XML_and_shared_strings_physically_read": True,
            "raw_outcome_bytes_unread_claimed": False,
            "new_source_rights_human_or_scientific_acceptance": False,
        },
    }
    expected.update(
        original_execution_receipts=RECEIPTS,
        preserved_timeout_receipts=TIMEOUT_RECEIPTS,
        original_input_scope_counts=SCOPE_COUNTS,
    )
    _require(
        set(capture) == set(expected) | {"members"},
        "EMPD2/NFI capture key membership differs",
    )
    _exact({key: capture[key] for key in expected}, expected)


def _log_bindings(
    common: dict[str, Any],
    logs: dict[str, dict[str, Any]],
    producer: dict[str, Any],
    observer: dict[str, Any],
) -> None:
    for stage in common["stages"]:
        for stream in ("stdout", "stderr"):
            name = stage["id"] + "." + stream
            _require(
                Path(stage[stream]).name == name
                and logs[name]["sha256"] == stage[stream + "_sha256"],
                "EMPD2/NFI actual native log hash differs",
            )
    _exact(producer.get("source_execution"), RECEIPTS["source-execution.json"])
    _exact(producer.get("source_exit"), 0)
    _exact(producer.get("metadata_exit"), 0)
    _exact(
        observer.get("independent_review"), RECEIPTS["independent-pairing-review.json"]
    )
    _exact(observer.get("refusals"), 16)
    _exact(observer.get("admitted"), 0)


def validated_empd2_nfi_pairing_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit the retained pairing refusal without claiming calibrated validation."""
    rows = [row for row in owners if row.get("owner_id") == OWNER]
    if (
        not any(row.get("role") == "retained_source" for row in rows)
        and not (repository / CAPTURE).exists()
    ):
        return (), {}
    paths = [REPORT_ROOT + "/pairs.csv", REPORT_ROOT + "/report.json"]
    _require(
        len(rows) == 1
        and rows[0].get("role") == "retained_source"
        and rows[0].get("paths") == paths
        and rows[0].get("producer_paths") == rows[0].get("producer_inputs") == [],
        "EMPD2/NFI exact retained owner differs",
    )
    path = _file(repository, CAPTURE)
    _require(
        _pin(path)["sha256"] == CAPTURE_SHA256,
        "EMPD2/NFI sealed source capsule differs",
    )
    capture = _json(path)
    _capture_claims(capture)
    prefix = path.parent.relative_to(repository).as_posix()
    members = _object(capture.get("members"))
    _exact(capture.get("member_count"), MEMBER_COUNT)
    _require(len(members) == MEMBER_COUNT, "EMPD2/NFI complete member count differs")
    _validate_source_transport(repository, prefix, members)
    records = []
    for name, record in RECEIPTS.items():
        file = _file(repository, prefix + "/execution/" + name)
        _exact(_pin(file), {key: record[key] for key in ("sha256", "bytes")})
        records.append(_json(file))
    plan, common, pairing, runtime, execution, review = records
    _native_records(plan, common, pairing, runtime, execution, review)
    logs = {
        name: _pin(_file(repository, prefix + "/execution/" + name))
        for name in (
            "maintained-outcome-blind-pairing.stdout",
            "maintained-outcome-blind-pairing.stderr",
            "independent-source-pairing-observer.stdout",
            "independent-source-pairing-observer.stderr",
        )
    }
    producer_log = _file(
        repository, prefix + "/execution/maintained-outcome-blind-pairing.stdout"
    )
    observer_log = _file(
        repository, prefix + "/execution/independent-source-pairing-observer.stdout"
    )
    _log_bindings(
        common,
        logs,
        json.loads(producer_log.read_text().splitlines()[-1]),
        json.loads(observer_log.read_text().splitlines()[-1]),
    )
    _exact(capture.get("original_execution_receipts"), RECEIPTS)
    _exact(capture.get("original_execution_candidate"), ORIGINAL_CANDIDATE)
    _exact(capture.get("original_input_count"), 66501)
    _exact(capture.get("original_input_scope_counts"), SCOPE_COUNTS)
    _exact(capture.get("public_first_party_source_members"), 2159)
    _exact(capture.get("omitted_first_party_bytecode_identities"), 4356)
    _exact(capture.get("original_native_stage_exits"), [0, 0])
    _require(
        capture.get("schema_version") == "empd2-nfi-outcome-blind-source-capture.v1"
        and capture.get("owner_id") == OWNER
        and capture.get("retention_mode")
        == "authored_public_source_and_execution_custody",
        "EMPD2/NFI source capsule contract differs",
    )
    for field in (
        "new_metadata_native_execution_claimed",
        "bytecode_payloads_or_fresh_compilation_equivalence_claimed",
        "private_input_payloads_included",
        "private_source_bound_pair_payload_included",
        "runtime_payloads_included",
    ):
        _require(capture.get(field) is False, "EMPD2/NFI custody scope broadened")
    custody = _json_array(_file(repository, prefix + "/original-input-custody.json"))
    _exact([_object(row).get("original") for row in custody], plan["input_pins"])
    counts: dict[str, int] = {}
    by_source = {}
    roots = [Path(row["root"]) for row in plan["first_party_namespaces"]]
    control = Path(plan["stages"][0]["argv"][3]).parent
    for raw in custody:
        row = _object(raw)
        original = _object(row.get("original"))
        name = original["path"]
        scope = row["scope"]
        member = row["member"]
        counts[scope] = counts.get(scope, 0) + 1
        by_source[name] = row
        if member is not None:
            _exact(
                members.get(_name(member)),
                {key: original[key] for key in ("sha256", "bytes")},
            )
        source = Path(name)
        if any(source.is_relative_to(root) for root in roots):
            if source.suffix == ".pyc":
                _require(
                    scope == "first_party_bytecode_identity_only" and member is None,
                    "EMPD2/NFI bytecode omission expanded",
                )
            else:
                _require(
                    scope == "public_first_party_source_resource"
                    and member
                    == "source/"
                    + source.relative_to(Path(plan["repository"])).as_posix(),
                    "EMPD2/NFI first-party source member absent",
                )
        elif source.is_relative_to(control):
            _require(
                scope == "declared_execution_control"
                and member == "control/" + source.relative_to(control).as_posix(),
                "EMPD2/NFI declared control missing",
            )
        else:
            _require(
                member is None
                and scope
                in {
                    "private_input_identity_only",
                    "runtime_identity_only",
                    "existing_public_metadata_identity_only",
                },
                "EMPD2/NFI input omission role differs",
            )
    _exact(counts, SCOPE_COUNTS)
    for origin in execution["first_party_origins"]:
        origin_row = by_source.get(origin["path"])
        _require(
            origin_row is not None
            and origin_row["scope"] == "public_first_party_source_resource"
            and origin_row["member"] in members,
            "EMPD2/NFI actual first-party origin missing",
        )
        assert origin_row is not None
        _exact(
            origin_row["original"],
            {key: origin[key] for key in ("path", "sha256", "bytes")},
        )
    _exact(len(execution["first_party_origins"]), 1163)
    for name, record in TIMEOUT_RECEIPTS.items():
        _exact(
            _pin(_file(repository, prefix + "/timeout-observation/" + name)),
            {key: record[key] for key in ("sha256", "bytes")},
        )
    old = _json(
        _file(repository, prefix + "/timeout-observation/pairing-terminal.json")
    )
    _exact(old.get("actual_exit"), 1)
    _exact(old["native_stages"][0]["actual_exit"], 124)
    _require(
        len(old["native_stages"]) == 1 and old["native_stages"][0]["timed_out"] is True,
        "EMPD2/NFI original timeout relabelled",
    )
    entries = []
    _exact(
        capture.get("publication_members"),
        {name: "publication/" + Path(name).name for name in paths},
    )
    for name in paths:
        product = _file(repository, name)
        retained = _file(repository, prefix + "/publication/" + Path(name).name)
        expected = PRODUCTS[Path(name).name]
        _exact(_pin(product), {key: expected[key] for key in ("sha256", "bytes")})
        _require(
            product.read_bytes() == retained.read_bytes(),
            "EMPD2/NFI current/native product bytes differ",
        )
        entry = tracked_by_path.get(name)
        _require(
            entry is not None
            and entry.kind == "file"
            and entry.sha256 == expected["sha256"]
            and entry.size == expected["bytes"],
            "EMPD2/NFI current tracked product differs",
        )
        assert entry is not None
        entries.append(entry)
    public = list(
        csv.DictReader(
            io.StringIO(
                _file(repository, prefix + "/publication/pairs.csv").read_text()
            )
        )
    )
    report = _json(_file(repository, prefix + "/publication/report.json"))
    _public_refusals(public, report)
    return tuple(entries), {
        "owner_id": OWNER,
        "capture_sha256": CAPTURE_SHA256,
        "original_execution_candidate": ORIGINAL_CANDIDATE,
        "original_native_stages": [0, 0],
        "paths": [entry.path for entry in entries],
        "observed_first_party_origins": 1163,
        "public_source_resources": 2159,
        "omitted_bytecode_identities": 4356,
        "original_inputs": 66501,
        "admitted_measured_pairs": 0,
        "refusals": 16,
        "outcome_columns_decoded": 0,
        "new_metadata_native_execution_claimed": False,
        "fresh_compilation_or_bytecode_source_equivalence_claimed": False,
        "scope": "Current outcome-blind source refusal replay and exact public bytes; no tree outcomes, new vegetation score, rights/human/ecological admission or original historical acquisition recovery.",
    }


def _json_array(path: Path) -> list[Any]:
    value = _read_json(path)
    _require(type(value) is list, "EMPD2/NFI ordered custody array required")
    assert isinstance(value, list)
    return value
