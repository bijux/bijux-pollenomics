"""Execute retained conditional requests through the existing deterministic host."""

from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from typing import Any
from uuid import uuid4

from ....core.filesystem import (
    BoundedInputTree,
    DirectoryAnchor,
    OwnedTreeWriter,
    publish_owned_replacement,
)
from ....core.filesystem.recovery_storage import resolve_publication_workspace_parent
from ..engine.discovery import load_engine, required_capability_for_profile
from ..engine.errors import LRARefusal
from ..execution.cache import run_lra_cached
from ..execution.service import run_lra_request
from ..outputs.identity import capture_code_identity, verify_code_identity
from ..outputs.reading import read_lra_product
from ..uncertainty.contracts import NUMERICAL_REASONS
from .admission import admit_source_cases
from .contracts import PROFILE, SourceCasePlan, canonical, digest, refuse
from .publication import retain_failed_design
from .reading import SourceCaseProduct, read_source_lra_cases, scientific_identity
from .results import child_vectors, design_summaries


def _disjoint(paths: list[Path]) -> None:
    for index, path in enumerate(paths):
        if any(
            path.is_relative_to(other) or other.is_relative_to(path)
            for other in paths[:index]
        ):
            refuse("Source, destination, cache and private recovery must be disjoint")


def run_source_lra_cases(
    plan: SourceCasePlan,
    *,
    input_root: Path,
    destination: Path,
    cache_directory: Path | None = None,
) -> SourceCaseProduct:
    """Publish derived views while preserving private evidence and prior products."""
    value = plan.payload()
    root, target = input_root.absolute(), destination.absolute()
    recovery_parent = resolve_publication_workspace_parent(
        target, namespace="lra-source-cases"
    )
    paths = [root, target, recovery_parent]
    if cache_directory is not None:
        paths.append(cache_directory.absolute())
    _disjoint(paths)
    with ExitStack() as stack:
        stack.enter_context(DirectoryAnchor(target.parent, create=True))
        stack.enter_context(DirectoryAnchor(recovery_parent, create=True))
        recovery = stack.enter_context(
            DirectoryAnchor(recovery_parent / uuid4().hex, create=True)
        )
        if cache_directory is not None:
            stack.enter_context(DirectoryAnchor(cache_directory, create=True))
        prior = None
        if target.exists() or target.is_symlink():
            prior = stack.enter_context(
                BoundedInputTree(
                    target,
                    max_bytes=value["limits"]["max_output_bytes"],
                    max_files=value["limits"]["max_output_files"],
                )
            )
            prior.validate()
        admitted = stack.enter_context(
            admit_source_cases(plan, input_root=root, workspace=recovery.path)
        )
        rows: list[dict[str, Any]] = []
        for case in value["cases"]:
            case_id = case["case_id"]
            row: dict[str, Any] = {
                "case_id": case_id,
                "mass": None if admitted.masses is None else admitted.masses[case_id],
                "request_ref": case["request_ref"],
                "parameter_declaration_ref": case["parameter_declaration_ref"],
                "status": "refused",
                "reason_code": None,
                "coordinates": None,
                "raw_values": None,
                "adjusted_values": None,
                "child_manifest_sha256": None,
                "child_scientific_content_sha256": None,
            }
            row["status"] = "not_run"
            rows.append(row)
        stack.enter_context(
            retain_failed_design(
                recovery.path / "failure", rows, weighted=admitted.masses is not None
            )
        )
        first = next(iter(admitted.requests.values())).payload()
        binding = load_engine(
            required_capability=required_capability_for_profile(first["method_profile"])
        )
        code = capture_code_identity(binding)
        for case, row in zip(value["cases"], rows, strict=True):
            case_id = case["case_id"]
            request = admitted.requests[case_id].payload()
            row["status"] = "refused"
            admitted.check()
            try:
                if cache_directory is None:
                    product = run_lra_request(
                        request,
                        input_root=admitted.inputs.snapshot,
                        destination=recovery.path / ("child-" + case_id),
                    )
                else:
                    product = run_lra_cached(
                        request,
                        input_root=admitted.inputs.snapshot,
                        cache_root=cache_directory,
                    ).product
                child_tree = stack.enter_context(
                    BoundedInputTree(
                        product.directory,
                        max_bytes=value["limits"]["max_output_bytes"],
                        max_files=value["limits"]["max_output_files"],
                    )
                )
                child_tree.validate()
                checksum = digest(child_tree.read(product.directory / "manifest.json"))
                verified = read_lra_product(
                    product.directory, expected_manifest_sha256=checksum
                )
                row.update(
                    child_manifest_sha256=checksum,
                    child_scientific_content_sha256=verified.product.scientific_content_sha256,
                )
                row.update(
                    child_vectors(
                        product.directory,
                        request,
                        max_bytes=value["limits"]["max_output_bytes"],
                    )
                )
                child_tree.validate()
                row["status"] = "success"
            except LRARefusal as error:
                if error.reason_code not in NUMERICAL_REASONS:
                    raise
                row["reason_code"] = error.reason_code
            admitted.check()
            verify_code_identity(binding, code)
        manifest = {
            "schema_version": "lra-source-case-product.v1",
            "profile": PROFILE,
            "purpose": "exploratory",
            "scientific_acceptance": "not_evaluated",
            "source_inputs_embedded": False,
            "source_redistribution_authorized": False,
            "empirical_source_authenticity_verified": False,
            "plan_sha256": plan.sha256,
            "envelope_ref": value["envelope_ref"],
            "design_kind": value["design"]["kind"],
            "law_ref": value["design"].get("law_ref"),
            "source_coverage": admitted.coverage,
            "source_parameter_uncertainty_propagated": False,
            "cases": rows,
            "summaries": design_summaries(rows, weighted=admitted.masses is not None),
            "code_identity": code.payload(),
        }
        manifest["scientific_content_sha256"] = scientific_identity(manifest)
        raw = canonical(manifest)
        writer = stack.enter_context(
            OwnedTreeWriter(
                recovery.path / "derived",
                max_bytes=value["limits"]["max_output_bytes"],
                max_files=1,
            )
        )
        writer.write_bytes("manifest.json", raw)
        admitted.check()
        verify_code_identity(binding, code)
        return publish_owned_replacement(
            writer,
            final=target,
            prior=prior,
            recovery=recovery,
            validate=lambda directory: read_source_lra_cases(
                directory, expected_manifest_sha256=digest(raw)
            ),
        )
