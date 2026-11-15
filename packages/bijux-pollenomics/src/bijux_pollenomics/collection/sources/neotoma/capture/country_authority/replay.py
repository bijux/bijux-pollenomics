"""Authenticate exact country-name queries and the actual returned buffers."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any

from ..receipts import (
    _object,
    _read,
    _request_record,
    _safe_root,
    _utc,
    _validate_receipt,
    _validate_transport_failure,
)
from ..resources.models import NeotomaResourceLimits
from ..resources.replay import _same_json
from .models import (
    COUNTRY_NAMES,
    COUNTRY_SCHEMA,
    DEFAULT_COUNTRY_LIMITS,
    METADATA_SCOPE,
    POLICY_SOURCES,
    NeotomaCountryAuthorityBody,
    NeotomaCountryAuthorityCapture,
    NeotomaCountryAuthorityPlan,
)
from .protocol import (
    _UnavailableCountryAuthority,
    assess_http,
    plan_from_json,
    qualify_native_country,
    request_for,
    validate_plan,
)

SNAPSHOT_CONSISTENCY = "individually timed current country queries; no complete dictionary or transaction claim"
_ENTRY = {
    "country",
    "content_version",
    "api_version",
    "metadata_role",
    "attempts",
    "scientific_admission",
}


def _control(
    root: Path, expected: str | None
) -> tuple[dict[str, Any], NeotomaCountryAuthorityPlan, NeotomaResourceLimits, str]:
    content = _read(root / "capture-manifest.json", 4 * 1024 * 1024)
    digest = sha256(content).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError("Neotoma country authority manifest identity differs")
    manifest = _object(content)
    if (
        set(manifest)
        != {
            "schema_version",
            "status",
            "capture_utc_start",
            "capture_utc_end",
            "plan_sha256",
            "countries",
            "request_count",
            "response_bytes",
            "partitions",
            "metadata_scope",
            "snapshot_consistency",
            "scientific_admission",
        }
        or manifest["schema_version"] != COUNTRY_SCHEMA
        or manifest["status"] != "closed"
        or manifest["metadata_scope"] != METADATA_SCOPE
        or manifest["snapshot_consistency"] != SNAPSHOT_CONSISTENCY
        or manifest["scientific_admission"] != "not_asserted"
    ):
        raise ValueError("Neotoma country authority manifest fields or scope differ")
    content = _read(root / "request-plan.json", 1024 * 1024)
    if sha256(content).hexdigest() != manifest["plan_sha256"]:
        raise ValueError("Neotoma country authority plan identity differs")
    control = _object(content)
    if (
        set(control)
        != {"schema_version", "plan", "limits", "metadata_scope", "policy_sources"}
        or control["schema_version"] != COUNTRY_SCHEMA
        or control["metadata_scope"] != METADATA_SCOPE
        or not _same_json(control["policy_sources"], list(POLICY_SOURCES))
    ):
        raise ValueError("Neotoma country authority control fields or scope differ")
    plan, recorded = plan_from_json(control)
    return manifest, plan, recorded, digest


def replay_neotoma_country_authority(
    directory: Path,
    *,
    expected_manifest_sha256: str | None = None,
    limits: NeotomaResourceLimits = DEFAULT_COUNTRY_LIMITS,
) -> NeotomaCountryAuthorityCapture:
    """Verify closed HTTP records independently of native authority qualification."""
    root = _safe_root(directory)
    manifest, plan, recorded, digest = _control(root, expected_manifest_sha256)
    validate_plan(plan, limits)
    entries = manifest["countries"]
    if not isinstance(entries, list) or len(entries) != len(plan.countries):
        raise ValueError("Neotoma country authority country population differs")
    maximum_requests = min(limits.max_requests, recorded.max_requests)
    maximum_body = min(limits.max_response_bytes, recorded.max_response_bytes)
    maximum_total = min(limits.max_total_bytes, recorded.max_total_bytes)
    count = total = 0
    previous_end, end = (
        _utc(manifest["capture_utc_start"]),
        _utc(manifest["capture_utc_end"]),
    )
    if previous_end > end:
        raise ValueError("Neotoma country authority capture timestamps are reversed")
    files = {"capture-manifest.json", "request-plan.json"}
    for entry, country in zip(entries, plan.countries, strict=True):
        if (
            not isinstance(entry, dict)
            or entry.get("country") != country
            or entry.get("content_version") != "current"
            or entry.get("api_version") != "v2.0"
            or entry.get("metadata_role") != "reference_metadata"
            or entry.get("scientific_admission") != "not_asserted"
            or not isinstance(entry.get("attempts"), list)
            or len(entry["attempts"]) > 1
        ):
            raise ValueError(
                "Neotoma country authority country identity or attempts differ"
            )
        assessed: dict[str, Any] = {"terminal_status": "not_attempted_budget"}
        if entry["attempts"]:
            count += 1
            if count > maximum_requests or total >= maximum_total:
                raise ValueError(
                    "Neotoma country authority capture exceeds caller budget"
                )
            reference = entry["attempts"][0]
            request = request_for(country)
            receipt_name = f"{request.name}.receipt.json"
            if (
                not isinstance(reference, dict)
                or reference.get("request_name") != request.name
                or reference.get("receipt_file") != receipt_name
            ):
                raise ValueError("Neotoma country authority receipt pointer differs")
            content = _read(root / receipt_name, 1024 * 1024)
            if sha256(content).hexdigest() != reference.get("receipt_sha256"):
                raise ValueError("Neotoma country authority receipt identity differs")
            record = _object(content)
            files.add(receipt_name)
            started, finished = (
                _utc(record.get("utc_start")),
                _utc(record.get("utc_end")),
            )
            if started < previous_end or finished < started or finished > end:
                raise ValueError("Neotoma country authority request timestamps differ")
            previous_end = finished
            if record.get("terminal_status") == "transport_failure":
                if set(reference) != {
                    "request_name",
                    "receipt_file",
                    "receipt_sha256",
                } or set(record) != set(
                    _request_record(request, record["utc_start"])
                ) | {"utc_end", "terminal_status", "error", "body_complete"}:
                    raise ValueError(
                        "Neotoma country authority transport fields differ"
                    )
                _validate_transport_failure(record, request)
                assessed = {
                    "terminal_status": "transport_failure",
                    "reason": record["error"],
                }
            else:
                name = f"{request.name}.body"
                if (
                    set(reference)
                    != {"request_name", "receipt_file", "receipt_sha256", "body_file"}
                    or reference["body_file"] != name
                    or record.get("body_file") != name
                ):
                    raise ValueError("Neotoma country authority body pointer differs")
                bound = min(maximum_body, maximum_total - total)
                body = _read(root / name, bound + 1)
                assessed = assess_http(record, request, body, bound)
                total += len(body)
                files.add(name)
        if set(entry) != _ENTRY | set(assessed) or not _same_json(
            {key: entry[key] for key in assessed}, assessed
        ):
            raise ValueError(
                "Neotoma country authority derived source assessment differs"
            )
    partitions = dict(Counter(row["terminal_status"] for row in entries))
    if (
        type(manifest["request_count"]) is not int
        or type(manifest["response_bytes"]) is not int
        or manifest["request_count"] != count
        or manifest["response_bytes"] != total
        or not _same_json(manifest["partitions"], partitions)
    ):
        raise ValueError("Neotoma country authority denominator closure differs")
    if (
        any(path.is_symlink() or not path.is_file() for path in root.iterdir())
        or {path.name for path in root.iterdir()} != files
    ):
        raise ValueError("Neotoma country authority file inventory differs")
    return NeotomaCountryAuthorityCapture(
        digest, tuple(entries), count, total, partitions
    )


def read_neotoma_country_authority_body(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    country: str,
    limits: NeotomaResourceLimits = DEFAULT_COUNTRY_LIMITS,
) -> NeotomaCountryAuthorityBody:
    """Gate the literal country before any source body, then hash the actual buffer."""
    if type(country) is not str or country not in COUNTRY_NAMES:
        raise ValueError("Neotoma country authority country is unsupported")
    root = _safe_root(directory)
    _, plan, _, _ = _control(root, expected_manifest_sha256)
    if country not in plan.countries:
        raise ValueError("Neotoma country authority country was not selected")
    captured = replay_neotoma_country_authority(
        root, expected_manifest_sha256=expected_manifest_sha256, limits=limits
    )
    entry = next(row for row in captured.countries if row["country"] == country)
    if entry["terminal_status"] != "received_complete_unqualified_country_metadata":
        raise ValueError("Neotoma complete country metadata entity is unavailable")
    reference = entry["attempts"][0]
    content = _read(root / reference["receipt_file"], 1024 * 1024)
    if sha256(content).hexdigest() != reference["receipt_sha256"]:
        raise ValueError("Neotoma country authority receipt changed during body access")
    record = _object(content)
    body = _read(root / reference["body_file"], limits.max_response_bytes)
    _validate_receipt(record, request_for(country), body, limits.max_response_bytes)
    return NeotomaCountryAuthorityBody(
        country, body, sha256(body).hexdigest(), reference["receipt_sha256"]
    )


def qualify_neotoma_country_authority(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    limits: NeotomaResourceLimits = DEFAULT_COUNTRY_LIMITS,
) -> dict[str, Any]:
    """Derive exact country identities independently of immutable HTTP outcomes."""
    captured = replay_neotoma_country_authority(
        directory, expected_manifest_sha256=expected_manifest_sha256, limits=limits
    )
    rows = []
    for entry in captured.countries:
        row: dict[str, Any] = {
            "country": entry["country"],
            "original_terminal_status": entry["terminal_status"],
            "qualification_status": "not_qualified_source_result",
            "absence_certified": False,
            "geometry_interpreted": False,
            "country_assignment_or_numerical_admission": "not_asserted",
            "territorial_or_dictionary_completeness": "not_established",
        }
        if entry["terminal_status"] == "received_complete_unqualified_country_metadata":
            body = read_neotoma_country_authority_body(
                directory,
                expected_manifest_sha256=expected_manifest_sha256,
                country=entry["country"],
                limits=limits,
            )
            native = _object(body.body)
            row.update(
                native_payload=native,
                body_sha256=body.body_sha256,
                receipt_sha256=body.receipt_sha256,
            )
            try:
                native_id = qualify_native_country(entry["country"], native)
            except _UnavailableCountryAuthority as error:
                row.update(
                    qualification_status="unavailable_country_record", reason=str(error)
                )
            except ValueError as error:
                row.update(
                    qualification_status="refused_country_record", reason=str(error)
                )
            else:
                row.update(
                    qualification_status="qualified_country_record",
                    native_geopolitical_id=native_id,
                    native_record_pointer="/data/0",
                )
        rows.append(row)
    counts = Counter(
        row["native_geopolitical_id"]
        for row in rows
        if row["qualification_status"] == "qualified_country_record"
    )
    for row in rows:
        if (
            row.get("native_geopolitical_id") in counts
            and counts[row["native_geopolitical_id"]] > 1
        ):
            row.update(
                qualification_status="refused_conflicting_native_authority_ids",
                reason="Different exact country queries share one native source identity",
            )
            del row["native_geopolitical_id"]
            del row["native_record_pointer"]
    return {
        "source_capture_manifest_sha256": captured.manifest_sha256,
        "countries": rows,
        "qualification_partitions": dict(
            Counter(row["qualification_status"] for row in rows)
        ),
        "HTTP_capture_ledger_modified": False,
        "scientific_admission": "not_asserted",
    }
