"""Publish a self-contained report from a verified retained joint product."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import Any, cast

from ....analysis.lra.uncertainty.api import read_joint_lra_ensemble
from ....analysis.lra.uncertainty.contracts import JointLRAPlan
from ....core.owned_tree import publish_new_output_tree
from ..contracts import (
    LRAPresentationRefusal,
    canonical,
    digest,
    regular_bytes,
    require_digest,
)
from .contracts import JointLRAPresentation, JointProductStatus
from .downloads import capture_joint_product, generated_hashes, write_joint_downloads
from .projection import project_joint_product
from .rendering import render_report


def _normalized(path: Path) -> Path:
    if ".." in path.parts or any(
        parent.is_symlink() for parent in (path, *path.parents)
    ):
        raise LRAPresentationRefusal("invalid_presentation_output", str(path))
    return Path(os.path.abspath(path.absolute()))


def _receipt(
    destination: Path, encoded: bytes, manifest: dict[str, Any]
) -> JointLRAPresentation:
    counts = manifest["denominators"]
    return JointLRAPresentation(
        directory=destination,
        manifest_sha256=digest(encoded),
        product_manifest_sha256=manifest["product_manifest_sha256"],
        scientific_content_sha256=manifest["scientific_content_sha256"],
        plan_sha256=manifest["plan_sha256"],
        product_status=cast(JointProductStatus, manifest["product_status"]),
        interrupted=manifest["interrupted"],
        bin_count=manifest["counts"]["bins"],
        requested_draw_bins=counts["requested_draw_bins"],
        successful_draw_bins=counts["successful_draw_bins"],
        refused_draw_bins=counts["refused_draw_bins"],
        not_run_draw_bins=counts["not_run_draw_bins"],
    )


def render_joint_lra_report(
    product_directory: Path,
    *,
    expected_manifest_sha256: str,
    destination: Path,
) -> JointLRAPresentation:
    """Render admitted retained bytes without engine imports or recomputation."""
    require_digest(expected_manifest_sha256)
    product_directory = _normalized(product_directory)
    destination = _normalized(destination)
    if (
        destination == Path(destination.anchor)
        or destination.is_relative_to(product_directory)
        or product_directory.is_relative_to(destination)
    ):
        raise LRAPresentationRefusal("invalid_presentation_output", str(destination))
    try:
        manifest, product = capture_joint_product(
            product_directory, expected_manifest_sha256
        )
        plan = JointLRAPlan(product["plan.json"].decode("utf-8")).payload()
        projection = project_joint_product(
            manifest,
            plan,
            product_manifest_sha256=expected_manifest_sha256,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(destination)
        stage = Path(
            tempfile.mkdtemp(
                prefix=f".{destination.name}.pending-", dir=destination.parent
            )
        )
        write_joint_downloads(stage, product, projection)
        css = regular_bytes(Path(__file__).with_name("report.css"))
        (stage / "report.css").write_bytes(css)
        (stage / "index.html").write_text(
            render_report(projection, manifest), encoding="utf-8"
        )
        read_joint_lra_ensemble(
            stage / "product", expected_manifest_sha256=expected_manifest_sha256
        )
        payload: dict[str, Any] = {
            "schema_version": "lra-joint-presentation.v1",
            "status": "generated_exploratory",
            "scientific_acceptance": "not_evaluated",
            "publication_authorized": False,
            "product_manifest_sha256": expected_manifest_sha256,
            "scientific_content_sha256": manifest["scientific_content_sha256"],
            "plan_sha256": manifest["plan_sha256"],
            "base_request_sha256": manifest["base_request_sha256"],
            "profile": manifest["profile"],
            "product_status": manifest["status"],
            "interrupted": manifest["interrupted"],
            "denominators": manifest["denominators"],
            "uncertainty_scope": manifest["uncertainty_scope"],
            "report_scope": "exact_retained_joint_product_and_lossless_projection",
            "download_serialization": "canonical JSON + LF; RFC4180-compatible UTF-8 CSV; exact originals",
            "capabilities": {
                "geometry": False,
                "map": False,
                "publication": False,
                "scientific_acceptance": False,
                "empirical_coverage": False,
                "intervals": False,
                "renormalization": False,
                "numerical_recomputation": False,
            },
            "counts": {
                "bins": len(projection["bins"]),
                "draw_bin_rows": len(projection["draw_bin_ledger"]),
                "mean_rows": len(projection["means"]),
                "ordered_covariance_cells": len(projection["covariance"]),
                "copied_product_members": len(product),
            },
            "files": generated_hashes(stage),
        }
        encoded = canonical(payload)
        (stage / "manifest.json").write_bytes(encoded)
        capture_joint_product(product_directory, expected_manifest_sha256)
        read_joint_lra_ensemble(
            stage / "product", expected_manifest_sha256=expected_manifest_sha256
        )
        if any(
            digest((stage / member).read_bytes()) != sha256
            for member, sha256 in payload["files"].items()
        ):
            raise ValueError("Presentation member changed before publication")
        for path in stage.rglob("*"):
            if path.is_file():
                with path.open("rb") as stream:
                    os.fsync(stream.fileno())
        publish_new_output_tree(
            final_output_root=destination, staging_output_root=stage
        )
        return _receipt(destination, encoded, payload)
    except LRAPresentationRefusal:
        raise
    except FileExistsError as exc:
        raise LRAPresentationRefusal(
            "presentation_output_exists", str(destination)
        ) from exc
    except (OSError, ValueError, KeyError, TypeError, IndexError, OverflowError) as exc:
        raise LRAPresentationRefusal("invalid_joint_presentation", str(exc)) from exc


__all__ = ["render_joint_lra_report"]
