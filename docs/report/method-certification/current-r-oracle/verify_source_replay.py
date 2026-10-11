"""Check the retained R replay against its present source and vector closure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics_dev.lra_validation.native_reference.annulus_capture import (
    AnnulusCapture,
)
from bijux_pollenomics_dev.lra_validation.native_reference.capture_selection import (
    CaptureProfile,
    validated_current_capture,
)
from bijux_pollenomics_dev.lra_validation.native_reference.count_domain_capture import (
    CountDomainCapture,
)
from bijux_pollenomics_dev.lra_validation.native_reference.source_replay import (
    build_source_replay,
)
from bijux_pollenomics_dev.source_completion.method_certification.native_r_comparison import (
    _consumer_inputs,
)

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_retained_comparison(
    repository: Path, report: dict[str, Any], replay: dict[str, Any]
) -> AnnulusCapture | CountDomainCapture:
    """Authenticate retained capture and present consumer bytes without rerunning R."""
    profile = report.get("native_capture_profile")
    if profile not in ("annulus", "count-domain"):
        raise ValueError("Retained comparison native capture profile differs")
    selected_profile = cast(CaptureProfile, profile)
    capture = validated_current_capture(repository, profile=selected_profile)
    consumer = _consumer_inputs(repository, capture.manifest_sha256, selected_profile)
    scope = {
        "native_capture_profile": selected_profile,
        "native_capture_source_revision": capture.source_revision,
        "native_capture_manifest_sha256": capture.manifest_sha256,
        "native_capture_source_context": capture.source_context,
        "fresh_R_executed_for_this_comparison": False,
        "current_python_expectations_regenerated_for_this_comparison": False,
        "consumer_inputs": consumer,
        "native_source_acquisition": "retained_public_locked_archive_acquisition",
        "scope": "retained native R capture against original R vectors; current consumer code and data bytes are independently identified, protected captured science inputs match, and neither R nor Python expectations are newly executed",
    }
    if report.get("schema_version") != "retained-native-r-comparison-report.v1":
        raise ValueError("Retained comparison report schema differs")
    for record in (report, replay):
        # JSON scalar identity distinguishes false source-scope flags from zero.
        if json.dumps(
            record.get("native_capture_source_context"), sort_keys=True, allow_nan=False
        ) != json.dumps(capture.source_context, sort_keys=True, allow_nan=False):
            raise ValueError("Retained comparison dirty source context differs")
        if any(record.get(name) != value for name, value in scope.items()) or any(
            name in record
            for name in (
                "source_revision",
                "consumer_source_revision",
                "private_source_custody",
            )
        ):
            raise ValueError("Retained comparison capture/consumer scope differs")
        for name in (
            "fresh_R_executed_for_this_comparison",
            "current_python_expectations_regenerated_for_this_comparison",
        ):
            if record[name] is not False:
                raise ValueError("Retained comparison must not claim fresh execution")
    # The immutable serializer validates historical native case/vector provenance.
    # Project only its schema tag in a copy; this performs no native execution.
    native_shape = dict(report, schema_version="current-native-r-reference.1")
    expected = build_source_replay(native_shape, capture.source_revision)
    for name, value in expected.items():
        if (
            name not in {"schema_version", "source_revision", "scope"}
            and replay.get(name) != value
        ):
            raise ValueError(
                "Retained comparison replay differs from native case/vector record"
            )
    return capture


def main() -> None:
    replay = json.loads((HERE / "source-replay.json").read_text())
    retained = json.loads((HERE / "report.json").read_text())
    capture = None
    if replay["schema_version"] == "retained-native-r-comparison-source-replay.v1":
        capture = _require_retained_comparison(ROOT, retained, replay)
    elif (
        replay["schema_version"] != "native-r-source-replay.v1"
        or retained.get("schema_version") != "current-native-r-reference.1"
        or any(
            field in record
            for record in (retained, replay)
            for field in (
                "consumer_inputs",
                "native_capture_profile",
                "native_capture_source_revision",
                "native_capture_manifest_sha256",
                "native_capture_source_context",
                "fresh_R_executed_for_this_comparison",
                "current_python_expectations_regenerated_for_this_comparison",
            )
        )
    ):
        raise ValueError("Unexpected R source replay/report schema")
    for field in ("current_inputs_sha256", "analysis_inputs_sha256"):
        for relative, expected in replay[field].items():
            if sha256(ROOT / relative) != expected:
                raise ValueError(f"R replay source changed: {relative}")
    if (
        sha256(ROOT / "configs/ci/lra-r-source-lock.v1.json")
        != replay["source_lock_sha256"]
        or sha256(
            ROOT
            / "docs/report/method-certification/original-r-reference/reference-bundle/certificate.json"
        )
        != replay["original_certificate_sha256"]
        or sha256(
            ROOT
            / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/live_reference_comparison.py"
        )
        != replay["runner_sha256"]
    ):
        raise ValueError("R replay authority changed")
    vectors = {
        relative: digest
        for relative, digest in retained["raw_results_sha256"].items()
        if relative.endswith(".csv")
    }
    summary = replay["retained_numeric_csv"]
    if (
        len(vectors) != summary["file_count"]
        or hashlib.sha256(
            json.dumps(vectors, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        != summary["mapping_sha256"]
        or any(
            sha256((capture.directory if capture is not None else HERE) / relative)
            != digest
            for relative, digest in vectors.items()
        )
    ):
        raise ValueError("Retained R numeric vectors changed")
    cases = replay["cases"]
    if (
        (cases["core_attempted"], cases["core_passed"]) != (43, 43)
        or (cases["source_domain_attempted"], cases["source_domain_passed"]) != (23, 23)
        or (cases["optimized_love_passed"], len(cases["optimized_love_ids"]))
        != (18, 18)
        or (
            cases["original_r_vectors_compared"],
            cases["original_r_vectors_passed"],
        )
        != (48, 48)
    ):
        raise ValueError("R replay case denominator changed")
    if (
        capture is not None
        and _require_retained_comparison(ROOT, retained, replay) != capture
    ):
        raise ValueError("Retained native capture changed during reader verification")
    print(
        "verified current consumer source and 97 retained numeric CSV files; no new R execution"
    )


if __name__ == "__main__":
    main()
