"""Run a retained nominal comparison through the maintained source-case workflow."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
import json
from pathlib import Path
import re
import subprocess
from typing import Any
from uuid import uuid4

from bijux_pollenomics.analysis.lra.api import (
    read_source_lra_cases,
    run_source_lra_cases,
)
from bijux_pollenomics.analysis.lra.source_cases.contracts import canonical, digest
from bijux_pollenomics.analysis.lra.source_cases.results import child_vectors
from bijux_pollenomics.core.filesystem import BoundedInputTree, DirectoryAnchor
from bijux_pollenomics.core.filesystem.recovery_storage import (
    resolve_publication_workspace_parent,
)
from bijux_pollenomics.reporting.bundles.staging import publish_into_staging_dir
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ..basin_sensitivity.inputs import BaselineInputs, load_inputs
from ..taxa import legacyvegetation
from .preparation import CASE_IDS, PreparedSourceCases, prepare
from .reporting import compare, markdown
from .source_inputs import read_normalization_context


def frozen_code_revision(expected: str) -> str:
    """Bind imported checkout code, independently of the retained input location."""
    if re.fullmatch("[0-9a-f]{40}", expected) is None:
        raise ValueError("An exact imported-code revision is required")
    root = next(
        (p for p in Path(__file__).absolute().parents if (p / "uv.lock").is_file()),
        None,
    )
    if root is None:
        raise ValueError(
            "The nominal source consumer requires an imported source checkout"
        )
    for name, package in (
        ("bijux_pollenomics", "bijux-pollenomics"),
        ("bijux_pollenomics_lra", "bijux-pollenomics-lra"),
    ):
        module = import_module(name)
        filename = module.__file__
        if filename is None:
            raise ValueError("Imported numerical package has no code location")
        origin = Path(filename).absolute()
        if (
            not origin.is_relative_to(root / "packages" / package / "src")
            or origin.resolve() != origin
        ):
            raise ValueError(
                "Host, engine and nominal consumer must use one imported checkout"
            )
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if head != expected:
        raise ValueError("Imported code revision differs from the declared revision")
    owned = [str(p.relative_to(root)) for p in Path(__file__).parent.glob("*.py")]
    try:
        subprocess.run(
            ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", *owned],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "diff",
                "--exit-code",
                head,
                "--",
                "packages/bijux-pollenomics/src",
                "packages/bijux-pollenomics-lra/src",
                "packages/bijux-pollenomics-dev/src",
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as error:
        raise ValueError(
            "Committed unchanged imported source code is required"
        ) from error
    return head


def execute_prepared(
    prepared: PreparedSourceCases,
    inputs: BaselineInputs,
    *,
    destination: Path,
    source_revision: str,
    code_validator: Callable[[], object] | None = None,
) -> dict[str, Any]:
    """Keep input and child storage private while publishing a complete derived view."""
    target = destination.absolute()
    recovery_parent = resolve_publication_workspace_parent(
        target, namespace="boke-parameter-sensitivity"
    )
    with (
        DirectoryAnchor(recovery_parent, create=True),
        DirectoryAnchor(recovery_parent / uuid4().hex, create=True) as private,
    ):
        prepared.materialize(private.path / "inputs")
        public_bytes: dict[str, bytes] = {}

        def build(candidate: Path) -> dict[str, Any]:
            product = run_source_lra_cases(
                prepared.plan,
                input_root=private.path / "inputs",
                destination=candidate / "source-cases",
            )
            saved = read_source_lra_cases(
                product.directory, expected_manifest_sha256=product.manifest_sha256
            )
            manifest = saved.manifest()
            report = compare(manifest)
            baseline = next(r for r in manifest["cases"] if r["case_id"] == CASE_IDS[0])
            baseline_match = None
            if baseline["status"] == "success":
                original = child_vectors(
                    inputs.directory, inputs.request, max_bytes=8 * 1024 * 1024
                )
                baseline_match = all(
                    baseline[key] == original[key]
                    for key in ["coordinates", "raw_values", "adjusted_values"]
                )
                if not baseline_match:
                    raise ValueError(
                        "Source-case baseline differs from the retained numerical result"
                    )
            base = inputs.request
            report.update(
                schema_version="boke-nominal-ppe-comparison.v1",
                code_revision=source_revision,
                source_request_sha256=digest(inputs.request_bytes),
                source_case_manifest_sha256=product.manifest_sha256,
                source_case_plan_sha256=prepared.plan.sha256,
                baseline_exact_numeric_match=baseline_match,
                source_pins=list(inputs.source_pins),
                source_scale_binding=json.loads(prepared.normalization_json),
                cover_policy={
                    "method": "clip-and-renormalize",
                    "realization": "Set negatives to zero, then normalize surviving positive mass",
                    "zero_surviving_mass": "explicit_refusal",
                    "authority": "Discussion with supervisor Anneli Poska, as reported by the project author (personal communication)",
                    "discussion_date": None,
                },
                support={
                    "taxa": base["taxa"],
                    "pollen_unit": base["pollen_unit"],
                    "temporal_matching": base["temporal_matching"],
                    "records": [
                        {
                            "role": role,
                            "basin_assumption": base[role]["basin"],
                            "pooled_records": [
                                {
                                    **{
                                        key: sample[key]
                                        for key in [
                                            "sample_id",
                                            "site_id",
                                            "bin_id",
                                            "age_type",
                                            "age_support_bp",
                                        ]
                                    },
                                    "modelled_panel_count": sum(sample["counts"]),
                                }
                                for sample in base[role]["samples"]
                            ],
                        }
                        for role in ["regional", "local"]
                    ],
                    "rings": base["rings"],
                    "configuration": base["configuration"],
                    "scope": "Retained pooled-source and physical assumptions, not scientific admission",
                },
                uncertainty="Conditional nominal point estimates only; no count, source-SD, chronology, basin or model uncertainty propagated",
                native2025_fall_speed_used=False,
                paper_reproduction=False,
            )
            public_bytes["report.json"] = canonical(report)
            public_bytes["README.md"] = markdown(report).encode()
            public_bytes["source-cases/manifest.json"] = (
                product.directory / "manifest.json"
            ).read_bytes()
            for name in ["report.json", "README.md"]:
                (candidate / name).write_bytes(public_bytes[name])
            return report

        def validate(candidate: Path) -> None:
            if code_validator is not None:
                code_validator()
            actual = {
                p.relative_to(candidate).as_posix()
                for p in candidate.rglob("*")
                if p.is_file()
            }
            if actual != set(public_bytes):
                raise ValueError(
                    "Only the complete derived report and source-case manifest may be published"
                )
            with BoundedInputTree(
                candidate, max_bytes=64 * 1024 * 1024, max_files=3
            ) as tree:
                for name, expected in public_bytes.items():
                    if tree.read(candidate / name) != expected:
                        raise ValueError(
                            "Derived publication differs from its computed result"
                        )
            read_source_lra_cases(
                candidate / "source-cases",
                expected_manifest_sha256=digest(
                    public_bytes["source-cases/manifest.json"]
                ),
            )

        return publish_into_staging_dir(target, build, validate=validate)


def run(repository: Path, destination: Path, *, source_revision: str) -> dict[str, Any]:
    """Load the existing source owners and execute one explicitly scoped comparison."""
    frozen_code_revision(source_revision)
    repository = repository.absolute()
    target = require_absent_artifact_output(repository, destination)
    inputs = load_inputs(repository)
    reference = legacyvegetation.read_reference(
        repository / legacyvegetation.DIRECTORY,
        expected_source_sha256=legacyvegetation.SOURCE_SHA256,
    )
    buffers, scope = read_normalization_context(repository, reference)
    prepared = prepare(inputs, reference, buffers=buffers, scope=scope)
    frozen_code_revision(source_revision)
    return execute_prepared(
        prepared,
        inputs,
        destination=target,
        source_revision=source_revision,
        code_validator=lambda: frozen_code_revision(source_revision),
    )
