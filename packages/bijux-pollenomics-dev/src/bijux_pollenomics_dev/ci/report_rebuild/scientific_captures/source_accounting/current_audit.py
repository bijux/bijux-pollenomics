"""Validate the current governed accounting summary, preserving earlier summary history."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...retained_source import validate_capsule, validated_descriptor
from .transport import json_object, validate_packet

CAPTURE = "data/source-custody/source-reconciliation/current-audit/capture.json"
CAPTURE_SHA256 = "c7f755751a4da3e2e3eefbe83bb6d0e72be73461f4dc8faba659367c1bb60c68"
REPORT = "docs/report/source-relations/source-reconciliation/report.json"
REPORT_SHA256 = "eaac246b596399e19f88a4730f84500d2aca654e5549ed7868255b8bf73bd85a"
ORIGINAL_SHA256 = "16ff5155e6d653691587353ee2f1c741655f86f6cce12e669ff40c839a8b2eb2"
HISTORY = (
    "data/source-custody/source-reconciliation/summary-history/"
    + ORIGINAL_SHA256
    + ".json"
)
OWNER = "source-relations/source-reconciliation/report-products"
ORIGINAL_CRITERION = "Known audit/summary modules and five governing registries are declared, but this is not the full321-path read set. Original private Rootsi/OpenLand intake archives and complete manifest/authority closure must be bound before mechanical summary reproduction. Reuse the retained zero-finding accounting scope; do not rerun the unchanged full source audit or infer full_source_confirmation."

ORIGINAL_PRODUCERS = [
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/__main__.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/audit.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/evidence.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/intake_custody.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/intakes.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/landclim.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/manifests.py",
]

ORIGINAL_INPUTS = [
    "data/country_dimension_coverage.json",
    "data/source_fact_ownership_registry.json",
    "data/source_family_contracts.json",
    "data/source_family_evidence_stage_matrix.json",
    "data/source_spatiotemporal_posture_registry.json",
]
ORIGINAL_OWNER: JsonObject = {
    "owner_id": OWNER,
    "role": "unresolved",
    "paths": [REPORT],
    "producer_paths": ORIGINAL_PRODUCERS,
    "producer_inputs": ORIGINAL_INPUTS,
    "verification": ORIGINAL_CRITERION,
}
RETAINED_OWNER: JsonObject = {
    "owner_id": OWNER,
    "role": "retained_source",
    "paths": [REPORT],
    "producer_paths": [],
    "producer_inputs": [],
    "verification": ORIGINAL_CRITERION,
}

PROOF_ROOT = "data/source-custody/source-reconciliation/current-retention"
PROOF_IDENTITIES = {
    "plan.json": {
        "sha256": "8a44b18a87dfe1aaa00325d7c86fe833e109026979b8b81b2667e4e85456b370",
        "bytes": 57077104,
    },
    "capture-terminal.json": {
        "sha256": "6834815e2b743f497408cd9a1c7db76427f9fe828145e27705be14a71a9eacfa",
        "bytes": 4782,
    },
    "capture-launch-terminal.json": {
        "sha256": "c72958ac1f59408ba9de09c0c1c979be9cc738060e9ef8d10402fc85859b61b2",
        "bytes": 2472,
    },
    "assembly-result.json": {
        "sha256": "1061f6c01aea2a0072ad717a7cffe7822a23fecbd561d9a198fb88a44cad8057",
        "bytes": 562,
    },
    "independent-capture-review.json": {
        "sha256": "7f687eeab1f4da801223f6e222d332838ca260dddfde53d5ebee956d835faafb",
        "bytes": 1090,
    },
}


def require(value: object, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not value:
        raise ReportRebuildError("Current source accounting custody: " + reason)


def physical(repository: Path, name: str) -> Path:
    """Resolve an ordinary retained-input file without following aliases."""
    path = repository / name
    require(
        path.is_file()
        and path == path.resolve()
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Physical regular public accounting member required",
    )
    return path


def ownership(owners: list[JsonObject]) -> None:
    """Check the current report owner against its declared custody contract."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    require(len(selected) == 1, "Exactly one current accounting owner required")
    row = selected[0]
    same_metadata(row, RETAINED_OWNER)
    for other in owners:
        paths = other.get("paths")
        require(
            type(paths) is list and all(type(p) is str for p in paths),
            "Typed owner paths required",
        )
        assert isinstance(paths, list)
        require(
            other is row or REPORT not in paths, "Another owner overlaps current report"
        )


def original_ownership(owners: list[JsonObject]) -> None:
    """Check the original report owner against its literal source contract."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    require(len(selected) == 1, "Exactly one original accounting owner required")
    same_metadata(selected[0], ORIGINAL_OWNER)
    for other in owners:
        paths = other.get("paths")
        require(
            type(paths) is list and all(type(p) is str for p in paths),
            "Typed original owner paths required",
        )
        assert isinstance(paths, list)
        require(
            other is selected[0] or REPORT not in paths,
            "Another owner overlaps original accounting report",
        )


def same_metadata(left: object, right: object) -> None:
    """Check nested metadata without coercing source types or membership."""
    require(type(left) is type(right), "Summary metadata types differ")
    if isinstance(left, dict) and isinstance(right, dict):
        require(set(left) == set(right), "Summary metadata fields differ")
        for key in left:
            same_metadata(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list):
        require(len(left) == len(right), "Summary ordered population differs")
        for a, b in zip(left, right, strict=True):
            same_metadata(a, b)
    elif isinstance(left, float) and isinstance(right, float):
        require(
            __import__("math").isfinite(left) and left.hex() == right.hex(),
            "Summary finite binary64 value differs",
        )
    else:
        require(left == right, "Summary metadata values differ")


def summary_correspondence(original: dict[str, Any], current: dict[str, Any]) -> None:
    """Compare original and current summaries under the declared correspondence."""
    require(
        set(original) == set(current) and len(current) == 18,
        "Exact original/current summary schema required",
    )
    provenance = {"summary_sha256", "full_audit_sha256", "input_closure_sha256"}
    require(provenance <= set(current), "Complete summary provenance fields required")
    for key in current:
        if key not in provenance:
            same_metadata(original[key], current[key])
    require(
        all(original[key] != current[key] for key in provenance),
        "Exact current provenance succession required",
    )
    require(
        original["full_audit_sha256"]
        == "26116f18017f5695c8782849e9ab827251d033cc56a8e1e76eabf38063c9ba90"
        and current["full_audit_sha256"]
        == "3ec6ed5dc52d23c88fead8b33f812ca31f1206c8cb497780c78bc7ea04c8aa3b",
        "Original/current content audit epochs differ",
    )
    require(
        current["full_source_confirmation"] is False,
        "Current accounting promoted full source confirmation",
    )


def qualify_metadata(
    records: dict[str, Any], capture_sha: str, packet: dict[str, Any]
) -> None:
    """Check recorded execution against its declared metadata correspondence."""
    plan, inner, outer, assembled, observed = [
        records[k] for k in ("plan", "inner", "outer", "assembly", "observer")
    ]
    require(
        inner["schema_version"] == "current-source-audit-metadata-capture-terminal.v1"
        and outer["schema_version"]
        == "current-source-audit-metadata-capture-watchdog.v1",
        "Correct current source-audit metadata receipt namespace required",
    )
    for value in (inner, outer):
        require(
            type(value["actual_exit"]) is int
            and value["actual_exit"] == 0
            and value["candidate"] == plan["candidate"]
            and value["plan_sha256"] == records["plan_identity"]["sha256"],
            "Actual successful metadata epoch required",
        )
    require(
        len(plan["stages"]) == len(inner["stages"]) == 2, "Exact two metadata stages"
    )
    for expected, actual, name, action in zip(
        plan["stages"],
        inner["stages"],
        (
            "retained-current-source-audit-assembly",
            "independent-current-source-audit-capture-observer",
        ),
        ("assemble", "observer"),
        strict=True,
    ):
        require(
            expected["id"] == actual["id"] == name
            and expected["action"] == actual["action"] == action
            and expected["argv"] == actual["argv"]
            and type(expected["timeout_seconds"]) is int
            and expected["timeout_seconds"] == 180
            and type(actual["timeout_seconds"]) is int
            and actual["timeout_seconds"] == expected["timeout_seconds"]
            and type(actual["actual_exit"]) is int
            and actual["actual_exit"] == 0
            and actual["timed_out"] is False,
            "Metadata stage contract differs",
        )
    require(
        inner["exception"] is None
        and inner["after_custody_error"] is None
        and all(
            inner[k] is True
            for k in (
                "memory_bound_pass",
                "inclusive_storage_bound_pass",
                "completed_whole_wall_bound_pass",
            )
        ),
        "Metadata custody/resource failure",
    )
    require(
        type(outer["child_native_exit"]) is int
        and outer["child_native_exit"] == 0
        and outer["child_timed_out"] is False
        and all(
            outer[k] is True
            for k in (
                "registered_plan_unchanged",
                "memory_bound_pass",
                "inclusive_storage_bound_pass",
                "completed_outer_wall_bound_pass",
            )
        ),
        "Metadata outer failure",
    )
    for value in (assembled, observed):
        require(
            type(value["actual_exit"]) is int and value["actual_exit"] == 0,
            "Actual retained packet proof absent",
        )
    require(
        assembled["metadata_retention_only"] is True
        and assembled["raw_decode_or_source_consumer_repeated"] is False
        and assembled["original_owner_acceptance_changed"] is False
        and assembled["capture"] == observed["capture"]
        and assembled["capture"]["sha256"] == capture_sha,
        "Metadata capture/scope differs",
    )
    require(
        observed["metadata_only"] is True
        and observed["raw_or_selected_rows_decoded_or_consumer_repeated"] is False
        and observed["original_owner_acceptance_changed"] is False
        and type(observed["original_ordered_inputs"]) is int
        and observed["original_ordered_inputs"] == 63315
        and type(observed["original_source_join_count"]) is int
        and observed["original_source_join_count"] == 7142,
        "Ordered input/source proof differs",
    )

    require(
        plan["schema_version"] == "current-source-audit-metadata-capture-plan.v1",
        "Exact metadata plan schema required",
    )
    require(
        type(plan["input_pins"]) is list and len(plan["input_pins"]) == 63365,
        "Complete registered metadata input union required",
    )
    names = [row["path"] for row in plan["input_pins"]]
    require(len(names) == len(set(names)), "Unique registered metadata inputs required")
    same_metadata(plan["transport"]["packet"], packet)
    same_metadata(observed["receipt_scope"], packet["receipt_scope"])
    require(
        type(assembled["public_payload_count"]) is int
        and assembled["public_payload_count"]
        == observed["retained_payloads"]
        == len(packet["members"])
        == 2269
        and type(observed["retained_payloads"]) is int,
        "Exact public payload population required",
    )
    require(
        type(assembled["exact_packet_bytes"]) is int
        and type(observed["actual_packet_bytes"]) is int
        and assembled["exact_packet_bytes"]
        == observed["actual_packet_bytes"]
        == 110733995,
        "Exact public packet storage required",
    )
    require(
        type(assembled["capture"]["bytes"]) is int
        and assembled["capture"]["bytes"] == 33636603
        and assembled["public_capture_path"] == CAPTURE,
        "Exact retained capture identity required",
    )
    require(
        outer["inner_terminal"]["sha256"]
        == PROOF_IDENTITIES["capture-terminal.json"]["sha256"]
        and type(outer["inner_terminal"]["bytes"]) is int
        and outer["inner_terminal"]["bytes"] == 4782,
        "Exact inner terminal join required",
    )
    resources = {
        "overall_timeout_seconds": 420,
        "outer_timeout_seconds": 480,
        "declared_memory_bytes": 2147483648,
        "declared_storage_bytes": 536870912,
    }
    for document in (plan, inner, outer):
        same_metadata(document["resources"], resources)


def exact_tree(root: Path, names: set[str]) -> None:
    """Require an exact, alias-free physical member inventory."""
    require(
        root.is_dir() and not any(p.is_symlink() for p in (root, *root.parents)),
        "Physical public capture required",
    )
    files: set[str] = set()
    directories: set[str] = set()
    for path in root.rglob("*"):
        require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "Capture alias/special member",
        )
        (files if path.is_file() else directories).add(
            path.relative_to(root).as_posix()
        )
    require(
        files == names | {"capture.json"} and directories == {"payloads"},
        "Exact current capture namespace required",
    )


def _validated(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    path = repository / CAPTURE
    require(
        path.exists()
        or path.is_symlink()
        or (
            not (repository / PROOF_ROOT).exists()
            and not (repository / PROOF_ROOT).is_symlink()
        ),
        "Published metadata retention proof requires its capture",
    )
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    if not selected and not path.exists() and not path.is_symlink():
        require(
            not (repository / HISTORY).exists()
            and not (repository / HISTORY).is_symlink(),
            "Orphan current accounting history requires its capture",
        )
        return (), {}
    # Unadmitted repositories may have the original unresolved owner and no current capture.
    if not path.exists() and not path.is_symlink():
        original_ownership(owners)
        require(
            not (repository / HISTORY).exists()
            and not (repository / HISTORY).is_symlink(),
            "Published accounting history requires its capture",
        )
        require(
            hashlib.sha256(physical(repository, REPORT).read_bytes()).hexdigest()
            == ORIGINAL_SHA256,
            "Current summary requires its exact capture",
        )
        return (), {}
    ownership(owners)
    raw = physical(repository, CAPTURE).read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == CAPTURE_SHA256,
        "Exact actual source-audit capture required",
    )
    packet = json_object(raw)
    resolver = validated_descriptor(
        repository, Path(CAPTURE).parent.as_posix(), packet["members"]
    )

    def read(name: str) -> bytes:
        return resolver.read_source(name)

    evidence = validate_packet(packet, read)
    proof_root = repository / PROOF_ROOT
    require(
        proof_root.is_dir()
        and not any(p.is_symlink() for p in (proof_root, *proof_root.parents)),
        "Physical portable metadata proof required",
    )
    require(
        {p.name for p in proof_root.iterdir()} == set(PROOF_IDENTITIES),
        "Exact portable metadata proof membership required",
    )
    roles = {
        "plan.json": "plan",
        "capture-terminal.json": "inner",
        "capture-launch-terminal.json": "outer",
        "assembly-result.json": "assembly",
        "independent-capture-review.json": "observer",
    }
    records: dict[str, Any] = {}
    for name, wanted in PROOF_IDENTITIES.items():
        raw_proof = physical(repository, PROOF_ROOT + "/" + name).read_bytes()
        require(
            len(raw_proof) == wanted["bytes"]
            and hashlib.sha256(raw_proof).hexdigest() == wanted["sha256"],
            "Portable metadata execution proof changed",
        )
        records[roles[name]] = json_object(raw_proof)
    records["plan_identity"] = PROOF_IDENTITIES["plan.json"]
    qualify_metadata(records, CAPTURE_SHA256, packet)
    bindings = {row["original"]["path"]: row for row in packet["public_bindings"]}
    plan_pin = packet["native_references"]["plan"]
    plan = json_object(read(bindings[plan_pin["path"]]["member"]))
    metadata_inputs = {row["path"]: row for row in records["plan"]["input_pins"]}
    require(
        len(plan["input_pins"]) == 63315,
        "Complete original native ordered identities required",
    )
    for original_pin in plan["input_pins"]:
        require(
            original_pin["path"] in metadata_inputs,
            "Original native input omitted by metadata execution",
        )
        same_metadata(original_pin, metadata_inputs[original_pin["path"]])
    current_row = bindings[plan["output"] + "/summary-current.json"]
    current = read(current_row["member"])
    require(
        hashlib.sha256(current).hexdigest() == REPORT_SHA256
        and physical(repository, REPORT).read_bytes() == current,
        "Current governed report differs from actual native summary",
    )
    producer_pin = packet["native_references"]["producer"]
    producer = json_object(read(bindings[producer_pin["path"]]["member"]))
    full_row = bindings[plan["output"] + "/full-current-audit.json"]
    full = json_object(read(full_row["member"]))
    require(
        sorted(row["path"] for row in full["input_files"])
        == plan["current_input_closure"]["repository"]["reader_paths"]
        and len(full["input_files"]) == 321,
        "Complete original consumed321-path scope required",
    )
    require(
        len(plan["current_input_closure"]["repository"]["files"]) == 592
        and len(plan["current_input_closure"]["private"]["files"]) == 7
        and len(full["manifest_byte_verifications"]) == 204,
        "Complete manifest/private/authority scope required",
    )
    expected_authorities = {
        "data/source_family_contracts.json",
        "data/source_family_evidence_stage_matrix.json",
        "data/country_dimension_coverage.json",
        "data/source_fact_ownership_registry.json",
        "data/source_spatiotemporal_posture_registry.json",
    }
    require(
        set(full["authority_paths"].values()) == expected_authorities,
        "All original five governing authorities required",
    )
    private = {
        row["path"]: row for row in plan["current_input_closure"]["private"]["files"]
    }
    for suffix, checksum, size in [
        (
            "/landclim/rootsi-workbooks/original/rootsi.7z",
            "f64d4dd411bc92362c9db2701c919063c2432e53fa523052e602da5f1a86183c",
            509919,
        ),
        (
            "/openland/original/LandCover_OpenLand.zip",
            "7ed602f3b480a995cd2e1ff6dc445e994442100b1f626a953185849305e2434b",
            204058381,
        ),
    ]:
        rows = [row for name, row in private.items() if name.endswith(suffix)]
        require(
            len(rows) == 1
            and rows[0]["sha256"] == checksum
            and type(rows[0]["bytes"]) is int
            and rows[0]["bytes"] == size,
            "Both exact original private archive identities required",
        )
    intake = full["external_intake_custody"]
    require(
        type(intake["verified_original_archives"]) is int
        and intake["verified_original_archives"] == 2
        and intake["receipt_count"] == 3
        and intake["country_claim_rows"] == 12
        and intake["scientific_admission"] == "not_established_by_custody",
        "Native private intake custody must remain separate from scientific admission",
    )
    for origin in producer["first_party_origins"]:
        relative = Path(origin["path"]).relative_to(Path(plan["owned_repository"]))
        current_source = physical(repository, relative.as_posix()).read_bytes()
        require(
            hashlib.sha256(current_source).hexdigest() == origin["sha256"]
            and len(current_source) == origin["bytes"],
            "Actual audit API source changed since current native proof",
        )
    for name in ORIGINAL_PRODUCERS:
        retained_source = bindings[str(Path(plan["owned_repository"]) / name)]
        source_raw = physical(repository, name).read_bytes()
        require(
            hashlib.sha256(source_raw).hexdigest()
            == retained_source["original"]["sha256"]
            and len(source_raw) == retained_source["original"]["bytes"],
            "Original declared audit producer source changed",
        )
    original = physical(repository, HISTORY).read_bytes()
    require(
        hashlib.sha256(original).hexdigest() == ORIGINAL_SHA256,
        "Exact original governed summary history required",
    )
    summary_correspondence(json_object(original), json_object(current))
    entry = tracked_by_path.get(REPORT)
    require(entry is not None, "Current report must be governed")
    assert entry is not None
    require(
        entry.path == REPORT.removeprefix("docs/report/")
        and entry.kind == "file"
        and entry.size == len(current)
        and entry.sha256 == REPORT_SHA256,
        "Current source-accounting tracked identity differs",
    )
    validate_capsule(repository, Path(CAPTURE).parent.as_posix(), packet["members"])
    return (entry,), {
        "owner_id": OWNER,
        "capture": {"path": CAPTURE, "sha256": CAPTURE_SHA256},
        "current_report": {"path": REPORT, "sha256": REPORT_SHA256},
        "original_governed_summary": {"path": HISTORY, "sha256": ORIGINAL_SHA256},
        "current_source_evidence": evidence,
        "full_original_owner_criterion_preserved": True,
        "capture_time_owner_was_unresolved": True,
        "current_governed_summary_succession_is_separate": True,
        "original_full_audit26116_recovered": False,
        "old_summary_byte_reproduction_claimed": False,
        "metadata_retention_execution_stages_and_wholes_zero": True,
        "retained_current_report_entries": 1,
        "source_rights_human_ecological_LRA_or_whole_requirement_admitted": False,
    }


def validated_current_source_accounting_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate the current summary without rerunning source/private consumers."""
    try:
        return _validated(repository, tracked_by_path, owners)
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise ReportRebuildError(
            "Current source accounting capture is malformed"
        ) from error
