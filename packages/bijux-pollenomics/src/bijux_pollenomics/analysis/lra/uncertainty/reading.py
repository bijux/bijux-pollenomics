"""Reopen joint products and replay their retained plan-to-child input graph."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..engine.errors import LRARefusal
from ..outputs.reading import read_lra_product
from .admission import admit
from .contracts import (
    NUMERICAL_REASONS,
    PROFILE,
    SCOPE,
    JointLRAPlan,
    canonical,
    digest,
    parse_json,
    reference,
)
from .projection import projections
from .statistics import child_values, summaries


def inventory(directory: Path) -> dict[str, str]:
    paths = list(directory.rglob("*"))
    if directory.is_symlink() or any(
        p.is_symlink() or not (p.is_file() or p.is_dir()) for p in paths
    ):
        raise ValueError("Joint product contains nonregular or linked members")
    return {
        p.relative_to(directory).as_posix(): digest(p.read_bytes())
        for p in sorted(paths)
        if p.is_file() and p != directory / "manifest.json"
    }


def denominators(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "requested_draw_bins": len(rows),
        "successful_draw_bins": sum(r["status"] == "success" for r in rows),
        "refused_draw_bins": sum(r["status"] == "refused" for r in rows),
        "not_run_draw_bins": sum(r["status"] == "not_run" for r in rows),
    }


def scientific_identity(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        key: manifest[key]
        for key in (
            "schema_version",
            "profile",
            "scientific_acceptance",
            "plan_sha256",
            "base_request_sha256",
            "code_identity",
            "status",
            "interrupted",
            "denominators",
            "summaries",
            "uncertainty_scope",
        )
    } | {
        "rows": [
            {key: value for key, value in row.items() if key != "child_manifest_sha256"}
            for row in manifest["rows"]
        ]
    }


def _producer(value: object) -> None:
    keys = {
        "engine_files",
        "host_adapter_files",
        "host_publication_files",
        "runtime_environment",
    }
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("Joint producer identity is incomplete")
    runtime = {
        "python",
        "platform",
        "bijux-pollenomics",
        "numpy",
        "scipy",
        "pandas",
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    }
    for key, entries in value.items():
        if not isinstance(entries, dict) or not entries:
            raise ValueError("Empty producer identity component")
        if key == "runtime_environment":
            if set(entries) != runtime or any(
                not isinstance(v, str) or not v for v in entries.values()
            ):
                raise ValueError("Incomplete runtime identity")
        else:
            for name, checksum in entries.items():
                reference({"path": name, "sha256": checksum})
    if set(value["host_publication_files"]) != {"core/owned_tree.py"}:
        raise ValueError("Shared publication identity missing")


def _row_fields(actual: dict[str, Any], selection: dict[str, Any]) -> None:
    extra: set[str] = set()
    status = actual["status"]
    if status == "success":
        extra = {
            "child",
            "child_manifest_sha256",
            "child_scientific_content_sha256",
            "coordinates",
            "values",
        }
    elif status == "refused" and actual["reason_code"] == "nonfinite_child_cover":
        extra = {
            "child",
            "child_manifest_sha256",
            "child_scientific_content_sha256",
            "detail",
        }
    elif status == "refused" and actual["reason_code"] == "numerical_refusal":
        extra = {"error"}
        error = actual.get("error")
        if (
            not isinstance(error, dict)
            or set(error)
            not in (
                {"status", "reason_code", "detail"},
                {"status", "reason_code", "detail", "diagnostics"},
            )
            or error.get("status") != "refused"
            or error.get("reason_code") not in NUMERICAL_REASONS
            or not isinstance(error.get("detail"), str)
        ):
            raise ValueError("Retained numerical diagnostic is malformed")
    if set(actual) != set(selection) | extra:
        raise ValueError("Joint outcome fields differ from its status")


@dataclass(frozen=True)
class JointLRAProduct:
    """A pinned exploratory finite-law bundle, not scientific acceptance."""

    directory: Path
    manifest_sha256: str
    canonical_manifest: str

    def manifest(self) -> dict[str, Any]:
        encoded = self.canonical_manifest.encode("utf-8")
        if digest(encoded) != self.manifest_sha256:
            raise LRARefusal(
                "invalid_joint_product", "Retained manifest identity changed"
            )
        return parse_json(encoded)


def read_joint_lra_ensemble(
    directory: Path, *, expected_manifest_sha256: str
) -> JointLRAProduct:
    """Verify expected bytes and derive every retained child request without engine imports."""
    try:
        if (
            not isinstance(expected_manifest_sha256, str)
            or len(expected_manifest_sha256) != 64
        ):
            raise ValueError("Expected manifest SHA-256 is required")
        if not directory.is_dir() or any(
            p.is_symlink() for p in (directory, *directory.parents)
        ):
            raise ValueError("Joint product must be an unlinked directory")
        encoded = (directory / "manifest.json").read_bytes()
        if digest(encoded) != expected_manifest_sha256:
            raise ValueError("Joint manifest differs from expected digest")
        manifest = parse_json(encoded)
        if (
            manifest["schema_version"] != "lra-joint-product.v1"
            or manifest["profile"] != PROFILE
            or manifest["scientific_acceptance"] != "not_evaluated"
        ):
            raise ValueError("Unsupported joint schema/profile/acceptance")
        fields = {
            "schema_version",
            "profile",
            "scientific_acceptance",
            "status",
            "interrupted",
            "plan_sha256",
            "base_request_sha256",
            "code_identity",
            "rows",
            "denominators",
            "summaries",
            "uncertainty_scope",
            "scientific_content_sha256",
            "files",
        }
        if set(manifest) != fields or canonical(
            manifest["uncertainty_scope"]
        ) != canonical(SCOPE):
            raise ValueError("Joint schema or uncertainty claims differ")
        _producer(manifest["code_identity"])
        before = inventory(directory)
        if before != manifest["files"]:
            raise ValueError("Joint file inventory differs")
        plan = JointLRAPlan((directory / "plan.json").read_text(encoding="utf-8"))
        admitted = admit(plan, directory / "source")
        if manifest["plan_sha256"] != plan.sha256 or manifest[
            "base_request_sha256"
        ] != digest(admitted.base_json.encode("utf-8")):
            raise ValueError("Joint parent identities differ")
        expected = projections(admitted)
        rows = manifest["rows"]
        if not isinstance(rows, list) or len(rows) != len(expected):
            raise ValueError("Requested draw/bin rows missing or duplicated")
        allowed = {"plan.json"} | {"source/" + name for name, _ in admitted.files}
        stopped = False
        for index, (actual, (selection, request, generated)) in enumerate(
            zip(rows, expected, strict=True)
        ):
            if not isinstance(actual, dict):
                raise ValueError("Expected a joint outcome object")
            if any(
                canonical(actual.get(k)) != canonical(v)
                for k, v in selection.items()
                if k not in ("status", "reason_code")
            ):
                raise ValueError("Joint row contradicts its supplied atom/bin")
            if request is None:
                if actual != selection:
                    raise ValueError("Ineligible bin was relabeled")
                continue
            _row_fields(actual, selection)
            for path, data in generated.items():
                allowed.add("source/" + path)
                if (directory / "source" / path).read_bytes() != data:
                    raise ValueError(
                        "Modeled input evidence differs from original source/atom"
                    )
            if actual["status"] not in ("success", "refused", "not_run"):
                raise ValueError("Unknown joint row outcome")
            child = actual.get("child")
            if child is not None:
                if child != f"children/{index:04d}":
                    raise ValueError("Child path is not its canonical draw/bin slot")
                product = read_lra_product(
                    directory / child,
                    expected_manifest_sha256=actual["child_manifest_sha256"],
                )
                retained = parse_json((directory / child / "request.json").read_bytes())
                if (
                    canonical(retained) != canonical(request)
                    or product.product.scientific_content_sha256
                    != actual["child_scientific_content_sha256"]
                ):
                    raise ValueError(
                        "Retained child does not derive from supplied joint atom"
                    )
                child_identity = product.manifest()["scientific_identity"]
                if canonical(
                    {k: child_identity.get(k) for k in manifest["code_identity"]}
                ) != canonical(manifest["code_identity"]):
                    raise ValueError(
                        "Child producer differs from joint producer identity"
                    )
                allowed.add(child + "/manifest.json")
                allowed.update(
                    child + "/" + name for name in product.manifest()["files"]
                )
            if stopped and actual["status"] != "not_run":
                raise ValueError("Eligible work was recorded after interruption")
            if actual["status"] == "success":
                if child is None or actual.get("reason_code") is not None:
                    raise ValueError("Successful row lacks a valid child")
                coordinates, values = child_values(directory / child, request)
                if canonical(actual.get("coordinates")) != canonical(
                    coordinates
                ) or canonical(actual.get("values")) != canonical(values):
                    raise ValueError("Retained joint values differ from child output")
            elif actual["status"] == "not_run":
                stopped = True
                if (
                    child is not None
                    or actual.get("reason_code") != "interrupted"
                    or manifest["interrupted"] is not True
                ):
                    raise ValueError("Not-run accounting lacks parent interruption")
            elif actual.get("reason_code") == "nonfinite_child_cover":
                if child is None or not isinstance(actual.get("detail"), str):
                    raise ValueError("Nonfinite refusal lacks its completed child")
                try:
                    child_values(directory / child, request)
                except (ValueError, KeyError):
                    pass
                else:
                    raise ValueError("Finite child was relabeled nonfinite")
            elif actual.get("reason_code") != "numerical_refusal":
                raise ValueError("Invalid eligible-row refusal")
        if set(before) != allowed:
            raise ValueError("Joint inventory includes unowned or omitted members")
        counts = denominators(rows)
        if (
            canonical(manifest["denominators"]) != canonical(counts)
            or type(manifest["interrupted"]) is not bool
        ):
            raise ValueError("Joint denominators/interruption differ")
        status = (
            "complete" if counts["successful_draw_bins"] == len(rows) else "incomplete"
        )
        if manifest["status"] != status:
            raise ValueError("Joint completeness posture differs")
        if canonical(manifest["summaries"]) != canonical(
            summaries(rows, [row["bin_id"] for row in plan.payload()["bins"]])
        ):
            raise ValueError("Joint summaries or failed-mass accounting differ")
        if manifest["scientific_content_sha256"] != digest(
            canonical(scientific_identity(manifest))
        ):
            raise ValueError("Joint scientific identity differs")
        if (
            inventory(directory) != before
            or (directory / "manifest.json").read_bytes() != encoded
        ):
            raise ValueError("Joint product changed during reading")
        return JointLRAProduct(
            directory, expected_manifest_sha256, encoded.decode("utf-8")
        )
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
        raise LRARefusal("invalid_joint_product", str(exc)) from exc
