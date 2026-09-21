"""Replay supplied synthetic joint atoms through existing deterministic LRA products."""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
from typing import Any

from ..engine.discovery import (
    EngineBinding,
    load_engine,
    required_capability_for_profile,
)
from ..engine.errors import LRARefusal
from ..execution.adapter import validate_engine_configuration
from ..execution.cache import run_lra_cached
from ..execution.service import run_lra_request
from ..inputs.validation import validate_request
from ..outputs.atomic import publish_directory
from ..outputs.identity import capture_code_identity, verify_code_identity
from ..outputs.reading import read_lra_product
from .admission import admit, revalidate
from .contracts import (
    NUMERICAL_REASONS,
    PROFILE,
    SCOPE,
    JointLRAPlan,
    canonical,
    digest,
)
from .projection import projections
from .reading import (
    JointLRAProduct,
    denominators,
    inventory,
    read_joint_lra_ensemble,
    scientific_identity,
)
from .statistics import child_values, summaries


def _disjoint(paths: list[Path]) -> None:
    for index, path in enumerate(paths):
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise LRARefusal(
                "invalid_joint_output_path", "Symbolic paths are unsupported"
            )
        for other in paths[:index]:
            if path.resolve().is_relative_to(
                other.resolve()
            ) or other.resolve().is_relative_to(path.resolve()):
                raise LRARefusal(
                    "invalid_joint_output_path",
                    "Input, output and cache trees must be disjoint",
                )


def _selected_engine(required_capability: str | None) -> EngineBinding:
    """Keep source-profile preflight while enforcing revised facade selection."""
    return (
        load_engine()
        if required_capability is None
        else load_engine(required_capability=required_capability)
    )


def _completed(
    row: dict[str, Any],
    request: dict[str, Any],
    completed: Path,
    child: Path,
    index: int,
) -> None:
    checksum = digest((completed / "manifest.json").read_bytes())
    verified = read_lra_product(completed, expected_manifest_sha256=checksum)
    child.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(completed, child)
    row.update(
        child=f"children/{index:04d}",
        child_manifest_sha256=checksum,
        child_scientific_content_sha256=verified.product.scientific_content_sha256,
    )
    try:
        coordinates, values = child_values(child, request)
    except (ValueError, KeyError) as exc:
        row.update(
            status="refused", reason_code="nonfinite_child_cover", detail=str(exc)
        )
    else:
        row.update(
            status="success", reason_code=None, coordinates=coordinates, values=values
        )


def run_joint_lra_ensemble(
    plan: JointLRAPlan,
    *,
    input_root: Path,
    destination: Path,
    cache_directory: Path | None = None,
) -> JointLRAProduct:
    """Run atoms serially; incomplete attempted children remain outside the product."""
    root, target = input_root.absolute(), destination.absolute()
    paths = [root, target]
    if cache_directory is not None:
        paths.append(cache_directory.absolute())
    _disjoint(paths)
    if target.exists():
        raise LRARefusal("lra_output_exists", str(target))
    admitted = admit(plan, root)
    required_capability = required_capability_for_profile(
        admitted.base()["method_profile"]
    )
    binding = _selected_engine(required_capability)
    validate_engine_configuration(
        binding, validate_request(admitted.base(), input_root=root)
    )
    code = capture_code_identity(binding)
    prepared = projections(admitted)
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.joint-pending-", dir=target.parent)
    )
    work = Path(
        tempfile.mkdtemp(prefix=f".{target.name}.joint-attempts-", dir=target.parent)
    )
    source = stage / "source"
    for name, data in admitted.files:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (stage / "plan.json").write_bytes(plan.canonical_json.encode("utf-8"))
    for _, request, generated in prepared:
        for name, data in generated.items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if request is not None:
            validate_engine_configuration(
                binding, validate_request(request, input_root=source)
            )
    rows: list[dict[str, Any]] = []
    interrupted = False
    for index, (selection, request, _) in enumerate(prepared):
        row = dict(selection)
        if request is None:
            rows.append(row)
            continue
        if interrupted:
            row.update(status="not_run", reason_code="interrupted")
            rows.append(row)
            continue
        completed = work / f"{index:04d}"
        try:
            if cache_directory is None:
                product = run_lra_request(
                    request, input_root=source, destination=completed
                )
            else:
                cached = run_lra_cached(
                    request, input_root=source, cache_root=cache_directory
                )
                product = cached.product
            read_lra_product(
                product.directory, expected_manifest_sha256=product.manifest_sha256
            )
        except KeyboardInterrupt:
            interrupted = True
            # A signal may arrive after atomic child publication. Retain that child.
            if (completed / "manifest.json").is_file():
                _completed(
                    row, request, completed, stage / "children" / f"{index:04d}", index
                )
            else:
                row.update(status="not_run", reason_code="interrupted")
        except LRARefusal as exc:
            if exc.reason_code not in NUMERICAL_REASONS:
                raise
            row.update(
                status="refused", reason_code="numerical_refusal", error=exc.as_dict()
            )
        else:
            _completed(
                row,
                request,
                product.directory,
                stage / "children" / f"{index:04d}",
                index,
            )
        rows.append(row)
        revalidate(admitted, root)
        if _selected_engine(required_capability).as_dict() != binding.as_dict():
            raise LRARefusal(
                "lra_code_changed_during_run", "Engine distribution identity changed"
            )
        verify_code_identity(binding, code)
    counts = denominators(rows)
    manifest = {
        "schema_version": "lra-joint-product.v1",
        "profile": PROFILE,
        "scientific_acceptance": "not_evaluated",
        "status": "complete"
        if counts["successful_draw_bins"] == len(rows)
        else "incomplete",
        "interrupted": interrupted,
        "plan_sha256": plan.sha256,
        "base_request_sha256": digest(admitted.base_json.encode("utf-8")),
        "code_identity": code.payload(),
        "rows": rows,
        "denominators": counts,
        "summaries": summaries(rows, [b["bin_id"] for b in plan.payload()["bins"]]),
        "uncertainty_scope": SCOPE,
    }
    manifest["scientific_content_sha256"] = digest(
        canonical(scientific_identity(manifest))
    )
    manifest["files"] = inventory(stage)
    encoded = canonical(manifest)
    (stage / "manifest.json").write_bytes(encoded)
    checksum = digest(encoded)
    read_joint_lra_ensemble(stage, expected_manifest_sha256=checksum)
    revalidate(admitted, root)
    if _selected_engine(required_capability).as_dict() != binding.as_dict():
        raise LRARefusal(
            "lra_code_changed_during_run", "Engine distribution identity changed"
        )
    verify_code_identity(binding, code)
    publish_directory(stage, target)
    return JointLRAProduct(target, checksum, encoded.decode("utf-8"))
