"""Compare the saved finite-age mixture with independent population moments."""

from __future__ import annotations

import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import numpy as np

from .independent_count_profiles import (
    NATIVE_PROFILE,
    SOURCE_PROFILE,
    SOURCE_PROTOCOL,
    prepare_recorded_profile,
)
from .independent_ledger import Observation, close, observe_ledger
from .independent_sources import (
    AXIS,
    BINS,
    TAXON_IDS,
    check_accounts,
    native_samples,
    public_parameters,
)

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/protocol.json"
)
COMPONENTS = {
    "age": "age",
    "count": "count",
    "shared_ppe": "ppe",
    "total": "total",
    "mean_gradient_ppe": "ppe_mean_gradient",
    "age_ppe_interaction": "ppe_gradient_variation",
}


def check_moments(result: dict[str, Any], observed: Observation) -> dict[str, Any]:
    """Keep undefined mass distinct from the separately conditional estimand."""
    expected_population = {
        "requested_draws": observed.rows,
        "complete_draws": observed.complete,
        "undefined_draws": observed.rows - observed.complete,
        "complete_probability": observed.complete / observed.rows,
        "support_by_window": {
            str(b): {
                "status_counts": dict(observed.support[b]),
                "probability_denominator": observed.rows,
            }
            for b in BINS
        },
    }
    if any(result[key] != value for key, value in expected_population.items()):
        raise ValueError("Saved all-row support population differs")
    unconditional = result["unconditional"]
    close(
        unconditional["undefined_fraction"],
        (observed.rows - observed.complete) / observed.rows,
        "unconditional missing mass",
    )
    if unconditional["mean"] is not None or unconditional["covariance"] is not None:
        raise ValueError(
            "Unconditional moments must use the declared reference or refusal"
        )
    if observed.complete < observed.rows:
        if (
            unconditional["status"] != "refused_undefined_mass"
            or unconditional["defined_moments_reference"] is not None
        ):
            raise ValueError("Undefined rows were silently admitted unconditionally")
    elif (
        unconditional["status"] != "defined_for_all_saved_rows"
        or unconditional["defined_moments_reference"] != "conditional_on_complete"
    ):
        raise ValueError("Unconditional complete moments reference differs")
    conditional = result["conditional_on_complete"]
    if conditional["draws"] != observed.complete:
        raise ValueError("Conditional population denominator differs")
    identities = [(a, b, taxon) for a, b in combinations(BINS, 2) for taxon in AXIS]
    if [
        (r["younger_window_id"], r["older_window_id"], r["taxon"])
        for r in conditional["contrasts"]
    ] != identities:
        raise ValueError("Thirty-contrast source axis differs")
    if not observed.complete:
        if (
            conditional["status"] != "refused_no_complete_draws"
            or any(
                conditional[field] is not None
                for field in (
                    "mean",
                    "mean_ppe_gradient",
                    "covariance_components",
                    "conditional_standard_deviation",
                )
            )
            or any(
                row
                != {
                    "younger_window_id": a,
                    "older_window_id": b,
                    "taxon": name,
                    "status": "refused_no_complete_draws",
                }
                for row, (a, b, name) in zip(
                    conditional["contrasts"], identities, strict=True
                )
            )
        ):
            raise ValueError("Empty complete-case population has invented moments")
        return {
            "maximum_moment_gap": 0.0,
            "covariance_entries_checked": 0,
            "contrasts_checked": 30,
        }
    if conditional["status"] != "conditional_on_complete":
        raise ValueError("Conditional estimand status differs")
    expected = observed.moments.finish()
    maximum = max(
        close(conditional["mean"], expected["mean"], "mixture mean"),
        close(
            conditional["mean_ppe_gradient"],
            expected["mean_gradient"],
            "mean PPE gradient",
        ),
    )
    closure = np.zeros((4, 20))
    for i in range(4):
        closure[i, 5 * i : 5 * (i + 1)] = 1
    maximum = max(
        maximum, close(closure @ expected["mean"], np.ones(4), "mean closure")
    )
    maximum = max(
        maximum,
        close(
            closure @ expected["mean_gradient"], np.zeros((4, 5)), "gradient closure"
        ),
    )
    for field, key in COMPONENTS.items():
        actual = np.asarray(conditional["covariance_components"][field], dtype=float)
        maximum = max(maximum, close(actual, expected[key], field))
        close(actual, actual.T, f"{field} symmetry")
        close(closure @ actual, np.zeros((4, 20)), f"{field} closure")
        if np.linalg.eigvalsh(actual).min() < -1e-12:
            raise ValueError("Saved covariance component is not PSD")
        diagnostics = {
            "maximum_symmetry_residual": float(np.max(np.abs(actual - actual.T))),
            "minimum_eigenvalue": float(np.linalg.eigvalsh(actual).min()),
            "maximum_window_closure_residual": float(np.max(np.abs(closure @ actual))),
        }
        checks = conditional["numeric_checks"][field]
        if set(checks) != set(diagnostics):
            raise ValueError("Saved covariance diagnostic axes differ")
        for key, value in diagnostics.items():
            close(checks[key], value, f"{field} numeric diagnostic")
    close(
        expected["ppe"],
        expected["ppe_mean_gradient"] + expected["ppe_gradient_variation"],
        "PPE interaction decomposition",
    )
    close(
        conditional["conditional_standard_deviation"],
        np.sqrt(np.maximum(0, np.diag(expected["total"]))),
        "joint conditional spread",
    )
    for row, (younger, older, taxon) in zip(
        conditional["contrasts"], identities, strict=True
    ):
        contrast = np.zeros(20)
        contrast[5 * BINS.index(younger) + AXIS.index(taxon)] = -1
        contrast[5 * BINS.index(older) + AXIS.index(taxon)] = 1
        if row["status"] != "conditional_on_complete":
            raise ValueError("Saved contrast estimand status differs")
        maximum = max(
            maximum,
            close(row["mean_difference"], contrast @ expected["mean"], "contrast mean"),
        )
        for field, key in COMPONENTS.items():
            maximum = max(
                maximum,
                close(
                    row["variance_components"][field],
                    contrast @ expected[key] @ contrast,
                    f"contrast {field}",
                ),
            )
        close(
            row["standard_deviation"],
            math.sqrt(max(0, float(contrast @ expected["total"] @ contrast))),
            "contrast conditional spread",
        )
    return {
        "maximum_moment_gap": maximum,
        "covariance_entries_checked": 6 * 400,
        "contrasts_checked": 30,
    }


def input_identities(
    repository: Path,
    source_root: Path,
    protocol: dict[str, Any],
    profile: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Bind external observations and the already qualified saved-age products."""
    source = json.loads((repository / protocol["source_profile"]).read_text())
    hashes = {}
    for namespace, root, pins in (
        ("source-store", source_root, source["source_store_files"]),
        (
            "repository",
            repository,
            {
                **source["repository_files"],
                **protocol["repository_inputs"],
                **(profile["repository_inputs"] if profile is not None else {}),
            },
        ),
    ):
        for relative, pin in pins.items():
            member = Path(relative)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError("Unsafe scientific input path")
            path = root / member
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if path.stat().st_size != pin["bytes"] or digest != pin["sha256"]:
                raise ValueError("Frozen scientific input identity differs")
            hashes[f"{namespace}/{relative}"] = digest
    return hashes


def verify_result(
    repository: Path, source_root: Path, result_path: Path
) -> dict[str, Any]:
    """Observe committed source, raw counts, all saved ages and resulting moments."""
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes)
    protocol_bytes = (repository / PROTOCOL).read_bytes()
    protocol = json.loads(protocol_bytes)
    committed = subprocess.check_output(
        ["git", "-C", str(repository), "show", f"{result['source_commit']}:{PROTOCOL}"]
    )
    if (
        committed != protocol_bytes
        or protocol["window_ids"] != list(BINS)
        or protocol["taxon_axis"] != list(AXIS)
    ):
        raise ValueError("Frozen protocol or analytical axes differ")
    if (
        result["schema_version"] != "abborrtjarnen-age-ppe.v1"
        or result["status"] != "conditional_age_count_ppe_delta_mixture"
    ):
        raise ValueError("Saved first-order mixture profile differs")
    profile_bytes = None
    profile = None
    count_profile = result.get("count_profile", NATIVE_PROFILE)
    if count_profile not in (NATIVE_PROFILE, SOURCE_PROFILE):
        raise ValueError("Unknown analytical count profile")
    if count_profile == SOURCE_PROFILE:
        profile_bytes = (repository / SOURCE_PROTOCOL).read_bytes()
        profile = json.loads(profile_bytes)
        committed_profile = subprocess.check_output(
            [
                "git",
                "-C",
                str(repository),
                "show",
                f"{result['source_commit']}:{SOURCE_PROTOCOL}",
            ]
        )
        if (
            profile_bytes != committed_profile
            or profile["count_profile"] != SOURCE_PROFILE
            or profile["base_protocol"] != str(PROTOCOL)
            or profile["default_count_profile"] != NATIVE_PROFILE
        ):
            raise ValueError("Frozen source-supported count profile differs")
    identities = input_identities(repository, source_root, protocol, profile)
    if result["input_sha256"] != identities or result["model_fits"] != 0:
        raise ValueError("Saved scientific identity or no-fit contract differs")
    axis = [
        {"window_id": b, "taxon": name, "native_taxon_id": tid}
        for b in BINS
        for name, tid in zip(AXIS, TAXON_IDS, strict=True)
    ]
    if result["component_axis"] != axis:
        raise ValueError("Saved twenty-component identity differs")
    samples = native_samples(source_root)
    analytical, support = samples, None
    if profile is not None:
        analytical, support = prepare_recorded_profile(
            repository, source_root, profile, result, samples, identities
        )
    check_accounts(
        result["sample_accounts"],
        samples,
        analytical=analytical if profile is not None else None,
        support=support,
    )
    ppe, sd = public_parameters(repository, result["parameters"])
    baseline = json.loads(
        (repository / protocol["physical_response_input"]).read_text()
    )
    if (
        result["physical_response"] != baseline["physical_response"]
        or result["parameters"] != baseline["parameters"]
    ):
        raise ValueError("Fixed nuisance inputs differ from qualified source result")
    response = np.asarray([row["factor"] for row in result["physical_response"]])
    if (
        [row["taxon"] for row in result["physical_response"]] != list(AXIS)
        or not np.all(np.isfinite(response))
        or np.any(response <= 0)
    ):
        raise ValueError("Conditional transport factors differ")
    profile_checked: dict[str, Any] = {}
    if profile is None:
        observed = observe_ledger(
            repository,
            protocol,
            result_path,
            result["draw_ledger"],
            samples,
            response,
            ppe,
            sd,
        )
    else:
        from .independent_profile_comparison import observe_source_ledger

        observed, profile_checked = observe_source_ledger(
            repository,
            profile,
            protocol,
            result_path,
            result,
            samples,
            analytical,
            response,
            ppe,
            sd,
        )
    checked = check_moments(result, observed)
    for actual, (seed, moments) in zip(
        result["chain_summaries"], observed.chains.items(), strict=True
    ):
        if (actual["seed"], actual["requested_draws"], actual["complete_draws"]) != (
            seed,
            16000,
            moments.observations,
        ):
            raise ValueError("Saved chain support population differs")
        if moments.observations:
            close(
                actual["conditional_mean"],
                moments.finish()["mean"],
                "chain conditional mean",
            )
        elif actual["conditional_mean"] is not None:
            raise ValueError("Empty chain population has an invented mean")
    if (
        result["new_ppe_draws"] != 0
        or result["field_calibration_or_coverage_claim"] is not False
        or result["historical_core_admission_changed"] is not False
    ):
        raise ValueError("Conditional scientific scope differs")
    control = result["fixed_age_control"]
    if (
        control["passed"] is not True
        or control["windows_checked"] != 4
        or not 0 <= control["maximum_absolute_gap"] <= 1e-12
    ):
        raise ValueError("Frozen-age source control failed")
    if (
        input_identities(repository, source_root, protocol, profile) != identities
        or result_path.read_bytes() != result_bytes
        or (repository / PROTOCOL).read_bytes() != protocol_bytes
        or (
            profile_bytes is not None
            and (repository / SOURCE_PROTOCOL).read_bytes() != profile_bytes
        )
    ):
        raise ValueError("Scientific inputs changed during observation")
    return {
        "status": "passed",
        "producer_source_commit": result["source_commit"],
        "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
        "native_samples_checked": len(samples),
        "saved_joint_age_rows_checked": observed.rows,
        "complete_rows": observed.complete,
        "undefined_rows": observed.rows - observed.complete,
        "maximum_ledger_cover_gap": observed.maximum_cover_gap,
        **checked,
        **profile_checked,
        "model_fits": 0,
    }
