"""Typed reopen for self-contained non-aggregated regional components."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, cast

from ..engine.errors import LRARefusal
from ..outputs.reading import read_lra_product
from .contracts import ExecutionStatus, RegionalComponentPlan, RegionalComponentSet

_STATUSES = ("completed", "refused", "failed", "not_run", "unobserved")
_ROW_FIELDS = {
    "index",
    "item_id",
    "request_sha256",
    "site_id",
    "sample_id",
    "bin_id",
    "geometry",
    "item_status",
    "product_path",
    "product_manifest_sha256",
    "product_scientific_content_sha256",
    "product_producer_identity",
    "error",
}
_SCIENCE_FIELDS = {
    "plan",
    "batch_sha256",
    "components",
    "component_execution_status",
    "counts",
    "aggregation_performed",
    "aggregation_profile",
    "regional_estimate",
    "regional_uncertainty",
    "publication_profile",
    "scientific_acceptance",
    "bundle_producer_identity",
}


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(value: bytes) -> dict[str, Any]:
    result = json.loads(value, object_pairs_hook=_object)
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object")
    json.dumps(result, allow_nan=False)
    return result


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _inventory(root: Path) -> dict[str, str]:
    paths = list(root.rglob("*"))
    if root.is_symlink() or any(path.is_symlink() for path in paths):
        raise ValueError("Regional component bundle contains a symbolic link")
    if any(not path.is_file() and not path.is_dir() for path in paths):
        raise ValueError("Regional component bundle contains a non-regular entry")
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in paths
        if path.is_file() and path != root / "manifest.json"
    }


def _plan(payload: dict[str, Any]) -> RegionalComponentPlan:
    grouping = payload["grouping_evidence"]
    plan = RegionalComponentPlan(
        component_set_id=payload["component_set_id"],
        regional_support_id=payload["regional_support_id"],
        bin_id=payload["bin_id"],
        bin_bounds_bp=tuple(payload["bin_bounds_bp"]),
        ordered_item_ids=tuple(payload["ordered_item_ids"]),
        grouping_evidence_path=grouping["path"],
        grouping_evidence_sha256=grouping["sha256"],
        batch_summary_sha256=payload["batch_summary_sha256"],
        schema_version=payload["schema_version"],
        aggregation_requested=payload["aggregation_requested"],
        aggregation_profile=payload["aggregation_profile"],
    )
    if plan.as_dict() != payload:
        raise ValueError("Plan contains unrecognized or noncanonical fields")
    return plan


def _error(value: object, status: str) -> None:
    if not isinstance(value, str):
        raise ValueError("Non-completed components require canonical error bytes")
    parsed = json.loads(value, object_pairs_hook=_object)
    if (
        not isinstance(parsed, dict)
        or not isinstance(parsed.get("reason_code"), str)
        or not parsed["reason_code"]
        or not isinstance(parsed.get("detail"), str)
    ):
        raise ValueError("Invalid component error envelope")
    if status == "refused" and parsed.get("status") != "refused":
        raise ValueError("Refused component lacks a refused error envelope")
    if (
        json.dumps(parsed, sort_keys=True, separators=(",", ":"), allow_nan=False)
        != value
    ):
        raise ValueError("Component error bytes are not canonical")


def _status(rows: list[dict[str, Any]]) -> str:
    completed = sum(row["item_status"] == "completed" for row in rows)
    if completed == len(rows):
        return "complete"
    if completed == 0 and all(row["item_status"] == "refused" for row in rows):
        return "refused"
    return "partial"


def _producer_identity(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"host_version", "files"}:
        raise ValueError("Invalid bundle producer identity")
    files = value["files"]
    expected = {
        "api.py",
        "regional_components/__init__.py",
        "regional_components/contracts.py",
        "regional_components/publication.py",
        "regional_components/reading.py",
        "regional_components/workflow.py",
    }
    if (
        not isinstance(value["host_version"], str)
        or not value["host_version"]
        or not isinstance(files, dict)
        or set(files) != expected
        or any(
            not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            for digest in files.values()
        )
    ):
        raise ValueError("Invalid bundle producer file identities")


def _validate_rows(
    root: Path, plan: RegionalComponentPlan, rows: list[dict[str, Any]]
) -> None:
    if [row.get("item_id") for row in rows] != list(plan.ordered_item_ids):
        raise ValueError("Component rows differ from the plan's exact order")
    producer: object | None = None
    cohort: object | None = None
    site_ids: set[str] = set()
    sample_ids: set[str] = set()
    for index, row in enumerate(rows):
        geometry = cast(dict[str, Any], row.get("geometry"))
        if set(row) != _ROW_FIELDS or set(geometry) != {
            "site_type",
            "diameter_m",
            "geometry_evidence_id",
        }:
            raise ValueError("Component row fields differ from the contract")
        status = row.get("item_status")
        if row.get("index") != index or status not in _STATUSES:
            raise ValueError("Invalid component index or terminal state")
        if row.get("bin_id") != plan.bin_id:
            raise ValueError("Component bin differs from plan")
        request_bytes = (root / f"requests/{index:06d}.json").read_bytes()
        request = _json(request_bytes)
        if request_bytes != _canonical(request) or _sha256(
            request_bytes[:-1]
        ) != row.get("request_sha256"):
            raise ValueError("Retained request bytes differ from component identity")
        samples = request.get("regional", {}).get("samples", [])
        bins = request.get("temporal_matching", {}).get("bins", [])
        if request.get("operation") != "reveals" or len(samples) != 1 or len(bins) != 1:
            raise ValueError("Component request is not one single-site REVEALS input")
        sample, time_bin = samples[0], bins[0]
        if sample["site_id"] in site_ids or sample["sample_id"] in sample_ids:
            raise ValueError("Component site and sample identities must be unique")
        site_ids.add(sample["site_id"])
        sample_ids.add(sample["sample_id"])
        basin = request["regional"]["basin"]
        if (
            sample.get("site_id") != row["site_id"]
            or sample.get("sample_id") != row["sample_id"]
            or sample.get("bin_id") != row["bin_id"]
            or time_bin.get("bin_id") != plan.bin_id
            or [float(time_bin["younger_bp"]), float(time_bin["older_bp"])]
            != list(plan.bin_bounds_bp)
            or row["geometry"]
            != {
                "site_type": basin["site_type"],
                "diameter_m": float(basin["diameter_m"]),
                "geometry_evidence_id": basin["geometry_evidence_id"],
            }
        ):
            raise ValueError("Component row contradicts its retained request")
        locks = [
            evidence["sha256"]
            for evidence in request["evidence"]
            if evidence["role"] == "dependency_lock"
        ]
        if len(locks) != 1:
            raise ValueError("Component request must retain one dependency lock")
        versions = request["versions"]
        current_cohort = {
            "data_kind": request["data_kind"],
            "method_profile": request["method_profile"],
            "pollen_unit": request["pollen_unit"],
            "taxa": request["taxa"],
            "parameters": request["parameters"],
            "versions": {
                name: versions[name]
                for name in ("taxonomy", "parameters", "chronology", "binning")
            },
            "dependency_lock_sha256": locks[0],
        }
        if cohort is None:
            cohort = current_cohort
        elif current_cohort != cohort:
            raise ValueError("Retained component requests do not form one cohort")
        path = row.get("product_path")
        if status == "completed":
            if path != f"components/{index:06d}" or row.get("error") is not None:
                raise ValueError("Completed component has invalid product/error fields")
            expected_manifest = row.get("product_manifest_sha256")
            reopened = read_lra_product(
                root / cast(str, path),
                expected_manifest_sha256=cast(str, expected_manifest),
            )
            if reopened.product.scientific_content_sha256 != row.get(
                "product_scientific_content_sha256"
            ) or reopened.manifest().get("request_sha256") != row.get("request_sha256"):
                raise ValueError("Copied component identity differs from its row")
            child_manifest = reopened.manifest()
            child_identity = child_manifest["scientific_identity"]
            current = {
                "engine": child_manifest["engine"],
                **{
                    name: child_identity[name]
                    for name in (
                        "engine_files",
                        "host_adapter_files",
                        "host_publication_files",
                        "runtime_environment",
                    )
                },
            }
            if current != row.get("product_producer_identity"):
                raise ValueError("Component producer identity differs from child")
            if current is None:
                raise ValueError("Completed component lacks producer identity")
            if producer is None:
                producer = current
            elif current != producer:
                raise ValueError("Completed component producers differ")
        else:
            if any(
                row.get(name) is not None
                for name in (
                    "product_path",
                    "product_manifest_sha256",
                    "product_scientific_content_sha256",
                    "product_producer_identity",
                )
            ):
                raise ValueError("Non-completed component references a product")
            _error(row.get("error"), cast(str, status))


def _validate_summary(
    summary: dict[str, Any],
    scientific: dict[str, Any],
    rows: list[dict[str, Any]],
) -> None:
    counts = scientific["counts"]
    completed = counts["completed"]
    interrupted = any(counts[name] for name in ("not_run", "unobserved"))
    if (
        summary.get("schema_version") != "lra-batch-result.v1"
        or summary.get("scientific_acceptance") != "not_evaluated"
        or summary.get("batch_sha256") != scientific.get("batch_sha256")
        or not isinstance(summary.get("items"), list)
        or len(summary["items"]) != len(rows)
        or set(cast(dict[str, Any], summary.get("counts"))) != set(_STATUSES)
        or sum(cast(dict[str, int], summary["counts"]).values()) != len(rows)
        or summary.get("all_items_completed") != (completed == len(rows))
        or summary.get("batch_status") != ("interrupted" if interrupted else "finished")
        or (summary.get("interruption_reason") is None) == interrupted
    ):
        raise ValueError("Retained batch summary identity is inconsistent")
    for row, item in zip(rows, summary["items"], strict=True):
        if any(
            item.get(name) != row[name]
            for name in ("index", "item_id", "request_sha256", "item_status")
        ):
            raise ValueError("Batch item differs from component row")
        expected_error = None if row["error"] is None else json.loads(row["error"])
        if item.get("error") != expected_error:
            raise ValueError("Batch error differs from retained component error")
        product = item.get("product")
        if row["item_status"] == "completed":
            if (
                not isinstance(product, dict)
                or product.get("manifest_sha256") != row["product_manifest_sha256"]
                or product.get("scientific_content_sha256")
                != row["product_scientific_content_sha256"]
            ):
                raise ValueError("Batch product differs from component row")
        elif product is not None:
            raise ValueError("Non-completed batch item references a product")
    if summary.get("counts") != scientific.get("counts"):
        raise ValueError("Batch and component-set denominators differ")


def read_regional_component_set(
    directory: Path, *, expected_manifest_sha256: str | None = None
) -> RegionalComponentSet:
    """Reopen every retained byte and child product without numerical imports."""
    directory = directory.absolute()
    try:
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("Component set must be a real directory")
        encoded = (directory / "manifest.json").read_bytes()
        manifest_digest = _sha256(encoded)
        if (
            expected_manifest_sha256 is not None
            and manifest_digest != expected_manifest_sha256
        ):
            raise ValueError("Manifest differs from the expected external digest")
        manifest = _json(encoded)
        expected_manifest_fields = {
            "schema_version",
            "product_kind",
            "component_execution_status",
            "counts",
            "requested_component_count",
            "aggregation_performed",
            "aggregation_profile",
            "regional_estimate",
            "regional_uncertainty",
            "publication_profile",
            "scientific_acceptance",
            "scientific_content_sha256",
            "bundle_producer_identity",
            "scientific_identity",
            "files",
        }
        if (
            set(manifest) != expected_manifest_fields
            or manifest.get("schema_version") != "regional-component-set.v1"
            or manifest.get("product_kind") != "regional_site_component_set"
            or manifest.get("aggregation_performed") is not False
            or manifest.get("aggregation_profile") is not None
            or manifest.get("regional_estimate") is not None
            or manifest.get("regional_uncertainty") is not None
            or manifest.get("publication_profile") is not None
            or manifest.get("scientific_acceptance") != "not_evaluated"
        ):
            raise ValueError("Unsupported component-set claim posture")
        inventory = _inventory(directory)
        if inventory != manifest.get("files"):
            raise ValueError("Component-set inventory differs from recorded bytes")
        plan_payload = _json((directory / "plan.json").read_bytes())
        plan = _plan(plan_payload)
        if (
            _sha256((directory / "evidence/grouping.bin").read_bytes())
            != plan.grouping_evidence_sha256
        ):
            raise ValueError("Retained grouping evidence differs from plan")
        if (
            _sha256((directory / "evidence/batch-summary.json").read_bytes())
            != plan.batch_summary_sha256
        ):
            raise ValueError("Retained batch summary differs from plan")
        lines = (directory / "components.jsonl").read_bytes().splitlines()
        rows = [_json(line) for line in lines]
        if not rows or len(rows) != manifest.get("requested_component_count"):
            raise ValueError("Component denominator is empty or inconsistent")
        _validate_rows(directory, plan, rows)
        counts = {
            status: sum(row["item_status"] == status for row in rows)
            for status in _STATUSES
        }
        status = _status(rows)
        if counts != manifest.get("counts") or status != manifest.get(
            "component_execution_status"
        ):
            raise ValueError("Component terminal denominator is inconsistent")
        scientific = manifest["scientific_identity"]
        if set(scientific) != _SCIENCE_FIELDS or any(
            scientific.get(name) != manifest.get(name)
            for name in (
                "component_execution_status",
                "counts",
                "aggregation_performed",
                "aggregation_profile",
                "regional_estimate",
                "regional_uncertainty",
                "publication_profile",
                "scientific_acceptance",
            )
        ):
            raise ValueError("Scientific identity claim fields are inconsistent")
        summary = _json((directory / "evidence/batch-summary.json").read_bytes())
        _validate_summary(summary, scientific, rows)
        _producer_identity(scientific.get("bundle_producer_identity"))
        if (
            scientific.get("plan") != plan_payload
            or scientific.get("components") != rows
            or scientific.get("counts") != counts
            or scientific.get("component_execution_status") != status
            or manifest.get("bundle_producer_identity")
            != scientific.get("bundle_producer_identity")
            or _sha256(_canonical(scientific))
            != manifest.get("scientific_content_sha256")
        ):
            raise ValueError("Component scientific identity is inconsistent")
        if (
            _inventory(directory) != inventory
            or (directory / "manifest.json").read_bytes() != encoded
        ):
            raise ValueError("Component set changed while it was reopened")
        return RegionalComponentSet(
            directory,
            manifest_digest,
            manifest["scientific_content_sha256"],
            cast(ExecutionStatus, status),
            counts,
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise LRARefusal("invalid_regional_component_set", str(exc)) from exc
