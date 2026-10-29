"""Admit one genuinely executed training-only LOVE fixed-start diagnostic."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ..contracts import JsonObject, ReportRebuildError
from ..ownership import _regular_confined_file
from .optimizer_inputs.fixed_starts import (
    _finite,
    _object,
    _require,
    validate_lifecycle,
)

PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-start-sensitivity/"
OWNER = "pollen-reconstruction/author-lra-constrained/optimizer-start-sensitivity/report-products"
AUTHORITY = "reports/science/source-cohorts/author-love-start-diagnostic.json"
# Publication must bind the independently admitted actual terminal, never a prediction.
AUTHORITY_SHA256: str | None = (
    "e5d7966db299a0ab24eb9a035c2a159dbeb8afc2b6045de5b1430aa7d08b132e"
)
REPLAY_SHA256 = "b499c48f0a5051e31d0f918f01d4ffc2d9a79966ee1c34fada5cdc2085209351"
PROTOCOL_SHA256 = "d257517c80ea407de3c186a8fa611d3a68ef95aae2ee706173849148fe6a37d8"
PROTOCOL_BYTES = 6178
SELECTION_SHA256 = "efa17dad2becc4bd1737b8a771fff42764bdf246e83d8db1c6e39eba8fbffe7b"
BASELINE = "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/report.json"
BASELINE_SHA256 = "8ce87d7083b0dde01d9030bb82bbd6ea9d3193dc4c52fc0ad7c9346894d8774d"
INPUT_CAPTURE = "data/method-certification/author-optimizer-diagnostic-source-capture/"
CAPTURE_SHA256 = "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93"
INPUT_PREFIX = "executions/optimizer-diagnostics/controlled-inputs/artifacts/science/current-author-development-inputs/constrained-inputs/"
INPUT_IDENTITIES = {
    "experiment.json": {
        "sha256": "aba70474156edfd1e03ac777ddb1083b8f396f3e3a21a03d104a3b3713a544b4",
        "bytes": 10913,
    },
    "source-report.json": {
        "sha256": "e89867dd2baebe347c18256c094281162ac9107f5d5a862fe090d0b28f86b7dc",
        "bytes": 888,
    },
    "chronology.json": {
        "sha256": "9453607ca0296965f24c49ec1bc1e146d010e3699ab5ee92a2d643be91490506",
        "bytes": 107,
    },
    "taxa.json": {
        "sha256": "23ea956d3a64f6111c337e9e322cae32855e8604881483e9b12a2b27916c75e0",
        "bytes": 655,
    },
    "parameters.json": {
        "sha256": "33ab18119b606287f46989e92fe4c88c47560dd4964132f90591230894a373c6",
        "bytes": 174,
    },
    "dependency-lock.json": {
        "sha256": "ed1e9e8f907a860b5c10fa92a7c5967ad3dbfe94281c3bb1b6d30321204fe2fb",
        "bytes": 95,
    },
    "decision.json": {
        "sha256": "774b314f43f07138ae5ec99cf7b4e12e5314b133f4046bf47ecb9e66eda2bdd8",
        "bytes": 496,
    },
    "BROADOWN-raw.json": {
        "sha256": "d85e12b53b52df1d10528372f668fa73479fd390d54b73e88238dd5f19c7a748",
        "bytes": 846,
    },
    "BROADOWN-geometry.json": {
        "sha256": "3945348d26462772b3d223c896b76aa5c8371b2580c0b0c9ab6a294fffd9af24",
        "bytes": 1274,
    },
    "CUTHILL2-raw.json": {
        "sha256": "822a22542d2d8328ab0dbf8e57be472f741a7782ff7e034497b68ddbdb78ae30",
        "bytes": 841,
    },
    "CUTHILL2-geometry.json": {
        "sha256": "afc2d3c3a803add89446edfaed388d822ce448f55fe428118349fec05df8e7b9",
        "bytes": 1274,
    },
    "LONGBREACH-raw.json": {
        "sha256": "5a09ae6240cfe6b5f8c3390ccd0ced1ae6eb2f7d2588a4edb14328fdd341199f",
        "bytes": 843,
    },
    "LONGBREACH-geometry.json": {
        "sha256": "2af6d37741816cc0d2a13618e8cfb4865e1af3e5dec3b039ddfdd3e99b576d0e",
        "bytes": 1271,
    },
}


def _decode(raw: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            _require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def nonfinite(_value: str) -> None:
        raise ReportRebuildError("LOVE fixed-start nonfinite JSON number")

    try:
        return _object(
            json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
        )
    except (UnicodeError, ValueError) as error:
        raise ReportRebuildError("LOVE fixed-start invalid JSON") from error


def _read(repository: Path, name: str, expected: str, maximum: int) -> bytes:
    try:
        path = _regular_confined_file(repository, name, "LOVE fixed-start evidence")
    except (OSError, ValueError) as error:
        raise ReportRebuildError(
            "LOVE fixed-start missing or unconfined evidence"
        ) from error
    _require(
        path.stat().st_nlink == 1 and path.stat().st_size <= maximum,
        "evidence bound or alias differs",
    )
    raw = path.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == expected, "evidence SHA256 differs")
    return raw


def _identity(value: object) -> dict[str, Any]:
    row = _object(value)
    _require(set(row) == {"sha256", "bytes"}, "receipt identity fields differ")
    _require(
        type(row["sha256"]) is str
        and len(row["sha256"]) == 64
        and all(c in "0123456789abcdef" for c in row["sha256"]),
        "receipt digest differs",
    )
    _require(type(row["bytes"]) is int and row["bytes"] > 0, "receipt size differs")
    return row


def validated_author_love_start_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit only this new diagnostic through a separately pinned public authority."""
    declared = [row for row in owners if row.get("owner_id") == OWNER]
    if not declared and not (repository / AUTHORITY).exists():
        return (), {}
    names = [PREFIX + "report.json", PREFIX + "trials.jsonl"]
    _require(
        len(declared) == 1
        and declared[0].get("role") == "retained_source"
        and declared[0].get("paths") == names
        and declared[0].get("producer_paths") == []
        and declared[0].get("producer_inputs") == [],
        "exact new owner differs",
    )
    _require(AUTHORITY_SHA256 is not None, "actual execution authority not bound")
    assert AUTHORITY_SHA256 is not None
    authority = _decode(_read(repository, AUTHORITY, AUTHORITY_SHA256, 256 * 1024))
    _require(
        authority.get("schema_version")
        == "author-love-fixed-start-execution-authority.v1",
        "authority schema differs",
    )
    _require(
        authority.get("selection_sha256") == SELECTION_SHA256
        and authority.get("producer_sha256") == REPLAY_SHA256,
        "original source selection differs",
    )
    expected_protocol = {
        "path": PREFIX + "protocol.json",
        "sha256": PROTOCOL_SHA256,
        "bytes": PROTOCOL_BYTES,
    }
    _require(
        authority.get("public_protocol") == expected_protocol,
        "public scientific protocol differs",
    )
    public_protocol = _decode(
        _read(repository, PREFIX + "protocol.json", PROTOCOL_SHA256, 64 * 1024)
    )
    _require(
        set(public_protocol)
        == {
            "schema_version",
            "selected_items",
            "protocol",
            "physical_inputs",
            "previous_evidence",
            "existing_reference",
        },
        "public protocol field scope differs",
    )
    candidate = authority.get("source_candidate")
    _require(
        type(candidate) is str
        and len(candidate) == 40
        and all(c in "0123456789abcdef" for c in candidate),
        "execution candidate differs",
    )
    plan = _identity(authority.get("plan"))
    receipts = _object(authority.get("original_receipts"))
    _require(
        set(receipts) == {"common", "outer", "independent_review"},
        "original receipt identities differ",
    )
    for value in receipts.values():
        _identity(value)
    execution = _object(authority.get("execution"))
    _require(
        execution.get("candidate") == candidate
        and execution.get("plan_sha256") == plan["sha256"]
        and execution.get("stage_id")
        == "fixed-positive-start-love-training-comparison",
        "native plan join differs",
    )
    _require(
        all(
            type(execution.get(name)) is int and execution[name] == 0
            for name in ("native_exit", "common_exit", "outer_exit")
        )
        and execution.get("timed_out") is False
        and execution.get("source_before_after_equal") is True
        and execution.get("inputs_before_after_equal") is True
        and execution.get("runtime_before_after_equal") is True,
        "native/source/runtime terminal did not pass",
    )
    _require(
        type(execution.get("argv")) is list
        and len(execution["argv"]) >= 2
        and all(type(x) is str for x in execution["argv"]),
        "actual argv required",
    )
    _require(
        authority.get("independent_semantics")
        == {
            "attempts": 128,
            "ledger_rows": 256,
            "held_out_prediction_count": 0,
            "all_source_baselines_and_refusals_preserved": True,
        },
        "independent numerical scope differs",
    )
    _require(
        authority.get("acceptance")
        == {
            "untouched_confirmation": False,
            "vegetation_accuracy": False,
            "global_optimum": False,
            "R_optimizer_parity": False,
            "source_rights": False,
            "release_acceptance": False,
        },
        "scientific scope was broadened",
    )
    runtime = _object(authority.get("runtime"))
    for name in ("reference_sha256", "source_input_pins_sha256"):
        value = runtime.get(name)
        _require(
            type(value) is str
            and len(value) == 64
            and all(c in "0123456789abcdef" for c in value),
            "runtime reference differs",
        )
    resources = _object(authority.get("resources"))
    _require(
        resources.get("wall_limit_seconds") == 600
        and resources.get("declared_memory_bytes") == 2 * 1024**3
        and resources.get("declared_storage_bytes") == 64 * 1024**2
        and resources.get("memory_bound_pass") is True
        and resources.get("storage_bound_pass") is True,
        "resource terminal differs",
    )
    _require(
        all(
            type(resources.get(name)) is str and resources[name]
            for name in ("memory_measurement_scope", "storage_measurement_scope")
        ),
        "actual resource measurement scope required",
    )
    _read(repository, PREFIX + "replay.py", REPLAY_SHA256, 64 * 1024)
    capture = _decode(
        _read(repository, INPUT_CAPTURE + "capture.json", CAPTURE_SHA256, 32 * 1024**2)
    )
    old_members = {row["path"]: row for row in capture["members"]}
    inputs = authority.get("inputs")
    _require(
        type(inputs) is list
        and len(inputs) == 13
        and len({row.get("path") for row in inputs}) == 13,
        "thirteen original scientific inputs required",
    )
    expected_inputs = [
        {"path": INPUT_CAPTURE + INPUT_PREFIX + name, **identity}
        for name, identity in INPUT_IDENTITIES.items()
    ]
    _require(
        inputs == expected_inputs, "exact original thirteen input identities differ"
    )
    assert isinstance(inputs, list)
    input_bodies = {}
    for row in inputs:
        row = _object(row)
        input_name = row.get("path")
        _require(
            type(input_name) is str
            and input_name.startswith(INPUT_CAPTURE + INPUT_PREFIX),
            "original input custody path differs",
        )
        assert isinstance(input_name, str)
        member = old_members.get(input_name.removeprefix(INPUT_CAPTURE))
        _require(
            member is not None
            and row
            == {
                "path": input_name,
                "sha256": member["sha256"],
                "bytes": member["bytes"],
            },
            "original scientific input identity differs",
        )
        raw = _read(repository, input_name, row["sha256"], 64 * 1024)
        _require(len(raw) == row["bytes"], "original scientific input size differs")
        input_bodies[Path(input_name).name] = raw
    products = _object(authority.get("products"))
    _require(
        set(products) == {"report", "trials"}, "two actual numerical products required"
    )
    bodies = []
    accepted_entries = []
    for role, name in zip(("report", "trials"), names, strict=True):
        row = _object(products[role])
        _require(
            set(row) == {"path", "sha256", "bytes"} and row["path"] == name,
            "canonical product path differs",
        )
        _identity({"sha256": row["sha256"], "bytes": row["bytes"]})
        body = _read(repository, name, row["sha256"], 32 * 1024**2)
        entry = tracked_by_path.get(name)
        _require(
            len(body) == row["bytes"]
            and entry is not None
            and entry.kind == "file"
            and entry.sha256 == row["sha256"]
            and entry.size == row["bytes"],
            "tracked product differs from native authority",
        )
        assert entry is not None
        accepted_entries.append(entry)
        bodies.append(body)
    report = _decode(bodies[0])
    ledger = [_decode(line) for line in bodies[1].splitlines()]
    baseline = _decode(_read(repository, BASELINE, BASELINE_SHA256, 64 * 1024))
    _require(
        report.get("optimizer_contract") == public_protocol["protocol"],
        "executed numerical protocol differs",
    )
    _require(
        public_protocol["physical_inputs"]
        == [{"path": name, **identity} for name, identity in INPUT_IDENTITIES.items()],
        "public input identities differ",
    )
    _require(
        public_protocol["existing_reference"]["sha256"]
        == "6383372379623ced187c8b8b5dd43f813dd5ec384a467f872bb99b579e2d1e38",
        "original math reference differs",
    )
    validate_lifecycle(report, ledger, baseline)
    expected_taxa = _decode(input_bodies["taxa.json"])["prepared_taxa"]
    _require(
        all(row["taxa"] == expected_taxa for row in report["regional_handoffs"]),
        "handoff taxonomy differs from original source",
    )
    regional_starts: dict[str, list[float]] = {}
    for row in report["attempts"]:
        item = row["item_id"]
        if row["start_id"] == "local-observed-half-uniform":
            counts = _decode(input_bodies[item.split(":")[1] + "-raw.json"])["sample"][
                "counts"
            ]
            _require(
                type(counts) is list
                and len(counts) == 30
                and all(_finite(x) and x >= 0 for x in counts)
                and sum(counts) > 0,
                "original training denominator differs",
            )
            _require(
                all(
                    abs(x - (1 / 60 + 0.5 * n / sum(counts))) <= 1e-15
                    for x, n in zip(row["start"], counts, strict=True)
                ),
                "training-observed start differs",
            )
        if row["start_id"] == "regional-cover-half-uniform":
            regional_starts.setdefault(item, row["start"])
            _require(
                row["start"] == regional_starts[item],
                "regional start changed between rings",
            )
    return tuple(accepted_entries), {
        "owner_id": OWNER,
        "authority_sha256": AUTHORITY_SHA256,
        "executed_source_candidate": candidate,
        "attempts": 128,
        "ledger_rows": 256,
        "original_input_members_reused": 13,
        "scope": "Exposed training convergence diagnostic only; all original numerical refusals remain literal. No heldout score, ecological accuracy, global optimum, R optimizer parity, rights or release admission.",
    }
