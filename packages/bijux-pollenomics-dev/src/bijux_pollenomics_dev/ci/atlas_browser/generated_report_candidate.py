"""Receipt and byte closure for managed generated-report browser candidates."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .artifact_candidate import canonical_digest, inventory, json_bytes
from .candidate_files import regular_bytes
from .contracts import (
    AtlasBrowserContractError,
    AtlasGeneratedReportCandidate,
    BrowserVerificationPlan,
    JsonObject,
    safe_artifact_path,
)

_COUNTRIES = ["Sweden", "Norway", "Finland", "Denmark"]
_RAA_KEY = "raa-archaeology"
_RAA_INPUT_STATUS = "raa_atlas_input_status.json"
_PUBLICATION_CONTRACT = "nordic_map_publication_contract.json"
_RAA_ASSET_SHA256 = "f9c34eccd0ca76ef5fc1e4a1a6b46d6678a9389044cbf3a6ce2d925fd30c353b"
_RAA_PAYLOAD_SHA256 = "9b37afcf73e93465fc255d8f6fd9e33b711b7c8d6dc6026db1af143f5ff577c1"
_RETAINED_DENSITY_SHA256 = (
    "acac7a952dc31be8b988ecb35386c877628e2580fae427f32281310635489d20"
)
_RETAINED_METADATA_SHA256 = (
    "baa5f7ec34e290d5b52ad93afb8a05e77830bd2b2672a15a579e571f5f6d91d8"
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _bound(root: Path, member: str, expected: str) -> bytes:
    payload = regular_bytes(root / safe_artifact_path(member))
    if _sha256(payload) != expected:
        raise AtlasBrowserContractError(f"generated report digest differs: {member}")
    return payload


def _option(command: list[object], name: str) -> object:
    indexes = [index for index, value in enumerate(command) if value == name]
    if len(indexes) != 1 or indexes[0] + 1 >= len(command):
        raise AtlasBrowserContractError(f"publisher command requires one {name}")
    return command[indexes[0] + 1]


def _receipt(root: Path, candidate: AtlasGeneratedReportCandidate) -> dict[str, Any]:
    receipt = json_bytes(
        _bound(root, candidate.generator_receipt, candidate.generator_receipt_sha256)
    )
    required = {
        "job_id",
        "input_commit",
        "input_tree",
        "exit_code",
        "termination",
        "read_set_unchanged",
        "command",
        "cwd",
        "outputs",
        "output_hashes",
    }
    if not required <= set(receipt):
        raise AtlasBrowserContractError("managed publication receipt is incomplete")
    job_id = receipt["job_id"]
    expected_job = Path(candidate.generator_receipt).parent.name
    if not isinstance(job_id, str) or job_id != expected_job:
        raise AtlasBrowserContractError("managed publication job identity differs")
    if (
        receipt["input_commit"] != candidate.generator_repository_head
        or receipt["input_tree"] != candidate.generator_repository_tree
        or receipt["exit_code"] != 0
        or receipt["termination"] != "exited"
        or receipt["read_set_unchanged"] is not True
    ):
        raise AtlasBrowserContractError("managed publication completion differs")
    command = receipt["command"]
    if (
        not isinstance(command, list)
        or any(not isinstance(value, str) or not value for value in command)
        or not any(
            command[index : index + 3] == ["-m", "bijux_pollenomics", "publish-reports"]
            for index in range(max(0, len(command) - 2))
        )
    ):
        raise AtlasBrowserContractError("managed publisher command differs")
    countries_index = command.index("--countries") if "--countries" in command else -1
    if (
        countries_index < 0
        or command[countries_index + 1 : countries_index + 5] != _COUNTRIES
    ):
        raise AtlasBrowserContractError("managed publisher country closure differs")
    presentation = root / candidate.presentation_root
    if _option(command, "--output-root") != str(presentation):
        raise AtlasBrowserContractError("managed publisher output root differs")
    if _option(command, "--published-output-root") != "docs/report":
        raise AtlasBrowserContractError("managed publisher publication root differs")
    cwd = receipt["cwd"]
    if (
        not isinstance(cwd, str)
        or not Path(cwd).is_absolute()
        or not Path(cwd).is_relative_to(root / "artifacts")
        or Path(cwd).is_relative_to(presentation)
    ):
        raise AtlasBrowserContractError("managed publisher cwd is unsafe")
    outputs = receipt["outputs"]
    if not isinstance(outputs, list) or str(presentation) not in outputs:
        raise AtlasBrowserContractError("managed publisher output is unrecorded")
    hashes = receipt["output_hashes"]
    if not isinstance(hashes, dict) or any(
        not isinstance(path, str) or not isinstance(digest, str) or len(digest) != 64
        for path, digest in hashes.items()
    ):
        raise AtlasBrowserContractError("managed publisher output hashes are invalid")
    prefix = str(presentation) + "/"
    receipt_hashes = {
        path.removeprefix(prefix): digest
        for path, digest in hashes.items()
        if path.startswith(prefix)
    }
    observed = inventory(presentation)
    physical_hashes = {row["path"]: row["sha256"] for row in observed}
    if receipt_hashes != physical_hashes:
        raise AtlasBrowserContractError(
            "managed publisher receipt differs from physical presentation"
        )
    if canonical_digest(physical_hashes) != candidate.presentation_inventory_sha256:
        raise AtlasBrowserContractError("generated report inventory identity differs")
    return receipt


def _raa_contract(
    presentation: Path, scope_directory: Path, build_id: str
) -> JsonObject:
    status = json_bytes(regular_bytes(scope_directory / _RAA_INPUT_STATUS))
    contract = json_bytes(regular_bytes(scope_directory / _PUBLICATION_CONTRACT))
    manifest = json_bytes(regular_bytes(scope_directory / "nordic_map_assets.json"))
    layers = contract.get("layer_rows")
    if not isinstance(layers, list):
        raise AtlasBrowserContractError("publication contract layers are absent")
    raa_layers = [
        row for row in layers if isinstance(row, dict) and row.get("key") == _RAA_KEY
    ]
    expected_reasons = [
        "missing_raw_inventory",
        "missing_raw_summary",
        "missing_scientific_review",
    ]
    if (
        len(raa_layers) != 1
        or raa_layers[0].get("default_enabled") is not True
        or raa_layers[0].get("applies_time_filter") is not False
        or raa_layers[0].get("contribution_role") != "display_only"
        or raa_layers[0].get("candidate_ranking_eligible") is not False
        or raa_layers[0].get("scientific_classification_eligible") is not False
        or raa_layers[0].get("propagation_status") != "refused"
        or raa_layers[0].get("propagation_reason_code") != "archaeology_context_only"
        or raa_layers[0].get("edge_count") != 0
        or raa_layers[0].get("authority_status") != "degraded"
        or raa_layers[0].get("authority_reason_codes") != expected_reasons
    ):
        raise AtlasBrowserContractError("RAÄ publication contract differs")
    accounting = status.get("density_count_accounting")
    geometry = status.get("geometry_publication")
    if (
        status.get("schema_version") != "raa-atlas-input-status.v1"
        or status.get("atlas_input_status") != "degraded"
        or status.get("reason_codes") != expected_reasons
        or status.get("evidence_role") != "archaeology_context_only"
        or status.get("propagation_eligible") is not False
        or not isinstance(geometry, dict)
        or geometry.get("default_map_state") != "enabled_degraded_context"
        or geometry.get("default_enabled") is not True
        or geometry.get("retained_density_is_authoritative") is not False
        or not isinstance(accounting, dict)
        or accounting.get("density_feature_count") != 106
        or accounting.get("density_cell_count_sum") != 339_412
        or accounting.get("metadata_fornlamning_count") != 318_265
        or accounting.get("difference") != 21_147
        or accounting.get("reconciled") is not False
    ):
        raise AtlasBrowserContractError("RAÄ retained-input status differs")
    assets = manifest.get("assets")
    if not isinstance(assets, dict):
        raise AtlasBrowserContractError("static asset table is absent")
    fields = assets.get("fields")
    records = assets.get("records")
    if not isinstance(fields, list) or not isinstance(records, list):
        raise AtlasBrowserContractError("static asset table is absent")
    rows = [
        dict(zip(fields, row, strict=True))
        for row in records
        if isinstance(row, list) and len(row) == len(fields)
    ]
    raa_assets = [row for row in rows if row.get("layer_key") == _RAA_KEY]
    domains = manifest.get("domains")
    if (
        manifest.get("build_id") != build_id
        or len(raa_assets) != 1
        or raa_assets[0].get("domain") != "nodes"
        or raa_assets[0].get("sha256") != _RAA_ASSET_SHA256
        or raa_assets[0].get("payload_sha256") != _RAA_PAYLOAD_SHA256
        or raa_assets[0].get("record_count") != 106
        or raa_assets[0].get("untimed_record_count") != 106
        or raa_assets[0].get("chronology_absent_record_count") != 106
        or raa_assets[0].get("time_min_bp") is not None
        or raa_assets[0].get("time_max_bp") is not None
        or not isinstance(domains, dict)
        or domains.get("edges")
        != {
            "status": "unavailable",
            "reason_code": "governed_map_edge_model_not_available",
            "record_count": 0,
        }
    ):
        raise AtlasBrowserContractError("RAÄ static asset or edge posture differs")
    if presentation not in scope_directory.parents:
        raise AtlasBrowserContractError("RAÄ scope is outside presentation")
    return {
        "input_status_sha256": _sha256(
            regular_bytes(scope_directory / _RAA_INPUT_STATUS)
        ),
        "publication_contract_sha256": _sha256(
            regular_bytes(scope_directory / _PUBLICATION_CONTRACT)
        ),
        "retained_density_sha256": _RETAINED_DENSITY_SHA256,
        "retained_metadata_sha256": _RETAINED_METADATA_SHA256,
    }


def audit_generated_report_candidate(plan: BrowserVerificationPlan) -> JsonObject:
    """Require receipt-bound bytes and the exact RAÄ degraded-context posture."""
    candidate = plan.candidate
    if not isinstance(candidate, AtlasGeneratedReportCandidate):
        raise AtlasBrowserContractError(
            "generated report audit requires a generated report candidate"
        )
    root = plan.repository_root.resolve()
    _receipt(root, candidate)
    presentation = root / candidate.presentation_root
    observed = inventory(presentation)
    if (
        canonical_digest({row["path"]: row["sha256"] for row in observed})
        != candidate.presentation_inventory_sha256
    ):
        raise AtlasBrowserContractError("generated report changed during audit")
    scope_directory = (root / plan.scopes[0].document).parent
    raa = _raa_contract(presentation, scope_directory, candidate.build_id)
    return {
        "schema_version": "atlas-generated-report-integrity.v1",
        "candidate": candidate.as_json(),
        "files": [
            {**row, "path": candidate.presentation_root + "/" + row["path"]}
            for row in observed
        ],
        "generator_receipt_sha256": candidate.generator_receipt_sha256,
        "raa_contract": raa,
    }


def verify_generated_report_served_bytes(
    plan: BrowserVerificationPlan, audit: JsonObject, report: object
) -> None:
    """Bind every required report/RAÄ identity actually served to Chromium."""
    if not isinstance(report, dict) or not isinstance(
        report.get("served_artifact_bytes"), list
    ):
        raise AtlasBrowserContractError("generated-report browser receipts are absent")
    if report.get("refused_artifact_reads") != []:
        raise AtlasBrowserContractError("browser refused altered report reads")
    files = audit.get("files")
    if not isinstance(files, list):
        raise AtlasBrowserContractError("generated report audit inventory is absent")
    expected = {row["path"]: row for row in files if isinstance(row, dict)}
    seen: set[str] = set()
    for row in report["served_artifact_bytes"]:
        if not isinstance(row, dict) or expected.get(row.get("path")) != row:
            raise AtlasBrowserContractError("served report bytes differ from candidate")
        path = row.get("path")
        if isinstance(path, str):
            seen.add(path)
    candidate = plan.candidate
    assert isinstance(candidate, AtlasGeneratedReportCandidate)
    scope_dir = Path(plan.scopes[0].document).parent
    required = {
        plan.scopes[0].document,
        plan.scopes[0].manifest,
        (scope_dir / _RAA_INPUT_STATUS).as_posix(),
        (scope_dir / _PUBLICATION_CONTRACT).as_posix(),
    }
    if not required <= seen:
        raise AtlasBrowserContractError(
            "browser did not observe required generated-report identities"
        )
