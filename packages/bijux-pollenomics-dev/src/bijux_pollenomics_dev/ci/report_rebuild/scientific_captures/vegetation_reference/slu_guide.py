"""Retain one genuine official SLU guide acquisition without recovering missing history."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import ReportOwnershipError, _regular_confined_file

OWNER = "validation/empd2-nfi-pairing/calibration-guide"

ORIGINAL_OWNER: JsonObject = {
    "owner_id": "validation/empd2-nfi-pairing/calibration-guide",
    "paths": [
        "docs/report/validation/empd2-nfi-pairing/inputs/slu-calibration-guide.pdf"
    ],
    "producer_inputs": [],
    "producer_paths": [],
    "role": "unresolved",
    "verification": "The tracked SLU calibration guide is pinned as SHA-256 "
    "793d90e287b2c686d0007f02497e12e8a72a47e5a45531918d9fc71d78499bc8 in "
    "the EMPD2–NFI report. Bind its original provider retrieval/copy "
    "receipt and publication/use statement to these exact bytes before "
    "retained-source ownership; the pairing producer consumes the guide "
    "but does not produce it.",
}
CORRECTION_WITNESS = "reports/science/source-cohorts/original-owner-acceptance.json"
CORRECTION_WITNESS_SHA256 = (
    "37d3ff0e8058675304a0dbee2d4454a077e7b0e294566b4bbe75ac7ffc99746e"
)
REPORT = "docs/report/validation/empd2-nfi-pairing/inputs/slu-calibration-guide.pdf"
ORIGINAL_CANDIDATE = "d027effd6c0ac91512cd586c3a51db987ea46d54"
PAGE_URL = "https://www.slu.se/en/about-slu/organisation/departments/forest-resource-management/miljoanalys/nfi/our-data/"
PDF_PATH = "/globalassets/slu.se/om-slu/organisation/institutioner/skoglig-resurshushallning/riksskogstaxeringen/dokument/dokument/info-data-for-calibration.pdf"
PDF_URL = "https://www.slu.se" + PDF_PATH
CAPTURE = "data/validation/slu-calibration-guide-source-capture/capture.json"
CAPTURE_SHA256 = "41b37d3136d020ad14176688e2fd65f3d0d6feaac010462b876f340fb553ee4a"
EXPECTED_MEMBERS: dict[str, dict[str, Any]] = {
    "execution/plan.json": {
        "sha256": "036f80b72208fbf561c9246836a3fe764a754853f1a611b814f22431076eb84d",
        "bytes": 712133,
    },
    "execution/terminal.json": {
        "sha256": "a9656e1e6e6f4f81e78f01ceff6f05317c6d907d0b3c6b6631c9760da83ad0bf",
        "bytes": 8660,
    },
    "execution/official-guide-terminal.json": {
        "sha256": "3ff95924e8f6d8ef0116b000c60740db9e1e468287ef5fdf35f6b99f1707b424",
        "bytes": 915,
    },
    "execution/independent-current-source-review.json": {
        "sha256": "66ae4d283d153dd5aa438bdfde9340de3cccc2af6fb583f2d0729bf7e0e215d5",
        "bytes": 2317,
    },
    "execution/current-retrieval.json": {
        "sha256": "796d1a10c00c53673d4fb2d4a03d864403dbfffe7c8c01a7dedfa4226e5f14cf",
        "bytes": 2447,
    },
    "execution/literal-guide-link.json": {
        "sha256": "ded7d0632841bc13c0ab271c4e1b79e857ce26f31a8370fd943f2fc4b2bf36dd",
        "bytes": 993,
    },
    "execution/current-official-page-and-literal-guide-acquisition.stdout": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/current-official-page-and-literal-guide-acquisition.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-current-response-link-and-guide-byte-review.stdout": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/independent-current-response-link-and-guide-byte-review.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "source-code/artifacts/science/current-report-custody/run_account_qualification.py": {
        "sha256": "9062395231bd7a4ec19bfe41df1587281c06e143b146119fe445a6eb0ce7ce8a",
        "bytes": 6924,
    },
    "source-code/artifacts/science/official-slu-guide-native-alias-custody/acquire.py": {
        "sha256": "89ee879ff97bbce3893815afe0e089a310c1c58b4d265ac2b9b530b2f46984ae",
        "bytes": 7028,
    },
    "source-code/artifacts/science/official-slu-guide-native-alias-custody/check_contracts.py": {
        "sha256": "53ef89397e41afcda029caa15db4a7b5cc00998ada10add5cdc9d85ecfa77ac0",
        "bytes": 12030,
    },
    "source-code/artifacts/science/official-slu-guide-native-alias-custody/contracts.py": {
        "sha256": "5ddcb86b3b486ab249644ddfc8184f30c7320891829a8a5eabee12b7ce2f2253",
        "bytes": 8130,
    },
    "source-code/artifacts/science/official-slu-guide-native-alias-custody/independent-source-review.json": {
        "sha256": "72b39e2e399889eb449f50b1d22a9de14f6bfab84abff112f20d3b67251530b3",
        "bytes": 1438,
    },
    "source-code/artifacts/science/official-slu-guide-native-alias-custody/observe.py": {
        "sha256": "d6363b7df0bf76d6e38ad587f28aeb3cb2da3e84dbfaa6d81037df4bfc9c731b",
        "bytes": 4632,
    },
    "source-code/artifacts/science/official-slu-guide-native-alias-custody/preflight/actual-native-alias-census.json": {
        "sha256": "fcada26d8164106b679e49a80300b106c76783310fc3a3238f489225ab4bda1e",
        "bytes": 2852,
    },
    "source-code/artifacts/science/official-slu-guide-native-alias-custody/prepare.py": {
        "sha256": "9524977ba91041ba037a5d8a5c55d5042090b8c74beaba389eeada0304af25e3",
        "bytes": 10252,
    },
    "source-code/artifacts/science/official-slu-guide-native-alias-custody/prepared-source-manifest.json": {
        "sha256": "7ae352ab97a68661ebaa9e079eafc018012b3878d79713b67b4f59b2e2cca892",
        "bytes": 1911,
    },
    "source-code/artifacts/science/official-slu-guide-native-alias-custody/protocol.json": {
        "sha256": "9f3e1a1df2b3fd73622718b52676c13f46fb5e6a4d8fc9594a42906eeb619a37",
        "bytes": 5993,
    },
    "source-code/artifacts/science/official-slu-guide-native-alias-custody/run.py": {
        "sha256": "633d080a67e85133a0cf334cbd78459e195d0281f0536bd6746b372abd7ff45b",
        "bytes": 4088,
    },
    "source-code/artifacts/science/official-slu-guide-native-alias-custody/runtime_custody.py": {
        "sha256": "0964eec589d0f69f97201b1bfbde558f33f41ab1e775fc53f879c85493af4d20",
        "bytes": 12005,
    },
    "source-code/artifacts/science/official-slu-guide-native-alias-custody/source-qualification.json": {
        "sha256": "3eeee1e6c3a7ebd15c873406091febdb6e865d08eae8abc6d0bb4d173b0cc0c4",
        "bytes": 3844,
    },
    "public-response/official-page-response.json": {
        "sha256": "3619732c48f97525f21ec540523d49ee70aac5bed5dec48649a88f6c74af3dd1",
        "bytes": 1869,
    },
    "public-response/official-PDF-response.json": {
        "sha256": "c1bba9b2c8f9cb2cd6c2c15c1a604e3a43c9a2c658db6034bea2b08b88beee92",
        "bytes": 2113,
    },
}
EXPECTED_SCOPE: dict[str, Any] = {
    "current_official_page_link_and_PDF_chain": True,
    "original_2026_09_21_copy_recovered": False,
    "historical_a063_receipt_recovered": False,
    "prior_8be8_documentary_use_review_available": False,
    "new_documentary_license_revalidation": False,
    "raw_page_payload_redistributed": False,
    "runtime_payloads_redistributed": False,
    "workbook_metadata_record_rewritten": False,
    "workbook_outcomes_decoded": 0,
    "measured_pairs_admitted": 0,
    "human_or_ecological_acceptance": False,
    "new_network_requests": 0,
}


def _require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("SLU guide: " + reason)


def _exact(left: object, right: object) -> None:
    _require(type(left) is type(right), "metadata types differ")
    if isinstance(left, dict) and isinstance(right, dict):
        _require(left.keys() == right.keys(), "metadata fields differ")
        for key in left:
            _exact(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list):
        _require(len(left) == len(right), "metadata list membership differs")
        for a, b in zip(left, right, strict=True):
            _exact(a, b)
    else:
        _require(left == right, "metadata values differ")


def _file(repository: Path, name: str) -> Path:
    try:
        return _regular_confined_file(repository, name, "SLU current guide source")
    except (ReportOwnershipError, OSError) as error:
        raise ReportRebuildError("SLU guide member is missing or unconfined") from error


def _object(value: object) -> dict[str, Any]:
    _require(
        isinstance(value, dict) and all(isinstance(k, str) for k in value),
        "expected a JSON object",
    )
    assert isinstance(value, dict)
    return value


def _json(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            _require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
        json.dumps(value, allow_nan=False)
        return _object(value)
    except (OSError, ValueError) as error:
        raise ReportRebuildError("SLU guide JSON is invalid") from error


def validate_native_records(
    plan: dict[str, Any],
    terminal: dict[str, Any],
    outer: dict[str, Any],
    acquisition: dict[str, Any],
    observer: dict[str, Any],
    link: dict[str, Any],
) -> None:
    """Validate actual two-stage source custody, not current network or runtime availability."""
    plan_sha = EXPECTED_MEMBERS["execution/plan.json"]["sha256"]
    _exact(plan["page_url"], PAGE_URL)
    _exact(plan["PDF_url"], PDF_URL)
    _exact(link["page_url"], PAGE_URL)
    _exact(link["resolved_pdf_url"], PDF_URL)
    _exact(len(link["matches"]), 1)
    _exact(link["matches"][0]["literal_href"], PDF_PATH)
    _exact(link["matches"][0]["resolved_url"], PDF_URL)
    _exact(plan["candidate"], ORIGINAL_CANDIDATE)
    _exact(terminal["candidate"], ORIGINAL_CANDIDATE)
    _exact(terminal["plan_sha256"], plan_sha)
    _exact(terminal["actual_exit"], 0)
    _exact(terminal["status"], "passed")
    _exact(terminal["canonical_before"], plan["canonical_identity"])
    _exact(terminal["canonical_after"], plan["canonical_identity"])
    _exact(terminal["before_pin_mismatches"], [])
    _exact(terminal["after_pin_mismatches"], [])
    _exact(terminal["absent_input_paths_unchanged"], True)
    _exact(len(plan["input_pins"]), 2509)
    _exact(len({row["path"] for row in plan["input_pins"]}), 2509)
    _exact(len(terminal["stages"]), 2)
    _exact(len(plan["stages"]), 2)
    for actual, wanted in zip(terminal["stages"], plan["stages"], strict=True):
        _exact(actual["id"], wanted["id"])
        _exact(actual["argv"], wanted["argv"])
        _exact(actual["actual_exit"], 0)
        _exact(actual["timed_out"], False)
    _exact(outer["candidate"], ORIGINAL_CANDIDATE)
    _exact(outer["plan_sha256"], plan_sha)
    _exact(
        outer["common_terminal"]["sha256"],
        EXPECTED_MEMBERS["execution/terminal.json"]["sha256"],
    )
    _exact(outer["actual_exit"], 0)
    _exact(outer["common_actual_exit"], 0)
    _exact(outer["memory_bound_pass"], True)
    _exact(outer["storage_bound_pass"], True)
    for record in (acquisition, observer):
        _exact(record["candidate"], ORIGINAL_CANDIDATE)
        _exact(record["plan_sha256"], plan_sha)
        _exact(record["actual_exit"], 0)
    _exact(acquisition["current_retrieval_only"], True)
    _exact(acquisition["original_2026_09_21_acquisition_recovered"], False)
    _exact(acquisition["historical_a063_receipt_recovered"], False)
    _exact(acquisition["workbook_or_outcome_requests"], 0)
    _exact(acquisition["same_raw_PDF_bytes"], True)
    _exact(acquisition["literal_href"], link)
    _exact(observer["literal_link"], link)
    _exact(observer["retained_raw_PDF_exact"], True)
    _exact(observer["official_current_page_response_link_asset_chain"], True)
    _exact(observer["original_2026_09_21_or_a063_recovered"], False)
    _exact(observer["workbook_measurement_outcomes_or_guide_history_closed"], False)
    _exact(observer["additional_network_requests"], 0)


def validate_public_response(
    response: dict[str, Any], plan: dict[str, Any], kind: str
) -> None:
    """Check the admitted cookie-free wire projection against original source facts."""
    _require(kind in {"page", "pdf"}, "unknown HTTP response role")
    expected = {
        "page": (
            PAGE_URL,
            "f2a2730afa7616d255fe5b2ab79fe752fff6ffc31dadd780233603b2d799d124",
            921362,
            "a32fd0dc3db356af24948171210eb21439a96fb25ff9ff613362c9950e26e4bd",
        ),
        "pdf": (
            PDF_URL,
            "793d90e287b2c686d0007f02497e12e8a72a47e5a45531918d9fc71d78499bc8",
            136339,
            "66d5a986d4fc97d78abea453cc399b76e6498fd8f043933a697ae9f9f939b905",
        ),
    }
    url, body_sha, size, receipt_sha = expected[kind]
    _exact(response["projection_schema"], "slu-public-http-response.v1")
    _exact(response["requested_url"], url)
    _exact(response["final_url"], url)
    _exact(response["original_response_sha256"], receipt_sha)
    _exact(response["sha256"], body_sha)
    _exact(response["bytes"], size)
    _exact(response["status"], 200)
    _exact(response["redirects"], [])
    _exact(response["TLS"]["certificate_verification_required"], True)
    _exact(response["TLS"]["hostname_verification"], True)
    _exact(response["TLS"]["CA"], plan["CA"])
    _exact(response["TLS"]["OpenSSL"], plan["OpenSSL"])
    _exact(response["proxy_handler"], {})
    _require(
        not any(
            str(header[0]).lower() in {"set-cookie", "set-cookie2"}
            for header in response["headers"]
        ),
        "cookie header redistributed",
    )


def _validate_original_owner(owners: list[JsonObject]) -> None:
    """Require the complete original unresolved contract, including unchanged criteria."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    _require(len(selected) == 1, "One exact original owner required")
    _exact(selected[0], ORIGINAL_OWNER)
    owned_paths = ORIGINAL_OWNER["paths"]
    assert isinstance(owned_paths, list)
    for other in owners:
        if other is selected[0]:
            continue
        paths = other.get("paths", [])
        _require(
            isinstance(paths, list)
            and all(isinstance(path, str) for path in paths)
            and not set(owned_paths).intersection(paths),
            "Another owner overlaps current evidence paths",
        )


def _capture_required(repository: Path) -> bool:
    """A published correction keeps its existing physical evidence mandatory."""
    capture = repository / CAPTURE
    present = bool(capture.exists() or capture.is_symlink())
    witness = repository / CORRECTION_WITNESS
    _require(
        not any(node.is_symlink() for node in (witness, *witness.parents)),
        "Original-acceptance witness ancestry alias",
    )
    if witness.exists() or witness.is_symlink():
        path = _file(repository, CORRECTION_WITNESS)
        _exact(hashlib.sha256(path.read_bytes()).hexdigest(), CORRECTION_WITNESS_SHA256)
        _require(present, "Published partial evidence requires its exact capture")
    return present


def validated_slu_guide_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Validate partial current evidence while original owner acceptance stays unresolved."""
    present = _capture_required(repository)
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    if not selected and not present:
        return (), {}
    _validate_original_owner(owners)
    if not present:
        return (), {}
    packet_path = _file(repository, CAPTURE)
    _exact(hashlib.sha256(packet_path.read_bytes()).hexdigest(), CAPTURE_SHA256)
    packet = _json(packet_path)
    _exact(packet["schema_version"], "slu-current-guide-source-capture.v1")
    _exact(packet["owner_id"], OWNER)
    _exact(packet["original_execution_candidate"], ORIGINAL_CANDIDATE)
    _exact(packet["members"], EXPECTED_MEMBERS)
    _exact(packet["scope"], EXPECTED_SCOPE)
    prefix = str(Path(CAPTURE).parent)
    physical = set()
    for path in packet_path.parent.rglob("*"):
        _require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "capture contains an alias or special member",
        )
        if path.is_file():
            physical.add(path.relative_to(packet_path.parent).as_posix())
    _exact(physical, set(EXPECTED_MEMBERS) | {"capture.json"})
    for name, wanted in EXPECTED_MEMBERS.items():
        path = _file(repository, prefix + "/" + name)
        _exact(
            {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            },
            wanted,
        )
    records = [
        _json(_file(repository, prefix + "/execution/" + name))
        for name in (
            "plan.json",
            "terminal.json",
            "official-guide-terminal.json",
            "current-retrieval.json",
            "independent-current-source-review.json",
            "literal-guide-link.json",
        )
    ]
    validate_native_records(*records)
    for name in ("official-page-response.json", "official-PDF-response.json"):
        response = _json(_file(repository, prefix + "/public-response/" + name))
        validate_public_response(
            response,
            records[0],
            "page" if name == "official-page-response.json" else "pdf",
        )
    product = _file(repository, REPORT)
    digest = hashlib.sha256(product.read_bytes()).hexdigest()
    _exact(digest, "793d90e287b2c686d0007f02497e12e8a72a47e5a45531918d9fc71d78499bc8")
    _exact(product.stat().st_size, 136339)
    entry = tracked_by_path.get(REPORT)
    _require(entry is not None, "tracked PDF inventory required")
    assert entry is not None
    _exact(entry.path, REPORT.removeprefix("docs/report/"))
    _exact(entry.kind, "file")
    _exact(entry.sha256, digest)
    _exact(entry.size, 136339)
    return (), {
        "selected_retained_entries": 0,
        "original_owner_acceptance_discharged": False,
        "owner_remains_unresolved": True,
        "original_acceptance_criterion": ORIGINAL_OWNER["verification"],
        "owner_id": OWNER,
        "capture_sha256": CAPTURE_SHA256,
        "original_execution_candidate": ORIGINAL_CANDIDATE,
        "original_native_stages": [0, 0],
        "paths": [entry.path],
        "scope": dict(EXPECTED_SCOPE),
        "historical_runtime_current_availability_claimed": False,
    }
