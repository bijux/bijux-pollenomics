"""Authenticate fixed scoring-reader extensions without relabelling old outputs."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule

_SCORING_PROTOCOL_CONTRACTS: dict[
    str, tuple[int, str, tuple[tuple[bytes, bytes], ...]]
] = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/site_leakage_challenge.py": (
        14310,
        "f26f69acc37ff18cbec11109e61fd8970453790f2075d32040471f973e90eaa3",
        (
            (
                b'\n    The optional scoring store is used only after predictions are frozen. It\n    never supplies training compositions, distances or forward model inputs.\n    """\n    records = _records()\n    folds = grouped_leave_one_out(records)\n',
                b'\n    The optional scoring store is used only after predictions are frozen. It\n    never supplies training compositions, distances or forward model inputs.\n    Hellinger scores retain the original arithmetic of this fixed challenge.\n    """\n    records = _records()\n    folds = grouped_leave_one_out(records)\n',
            ),
            (
                b'                synthetic_pollen_truth_fraction=truth_pollen,\n                vegetation_score=vegetation_score.as_dict(),\n                pollen_mae_fraction=pollen_mae,\n                pollen_hellinger=hellinger_distance(pollen, truth_pollen),\n            )\n            cases.append(row)\n    scored = [case for case in cases if case["status"] == "scored"]\n',
                b'                synthetic_pollen_truth_fraction=truth_pollen,\n                vegetation_score=vegetation_score.as_dict(),\n                pollen_mae_fraction=pollen_mae,\n                pollen_hellinger=hellinger_distance(\n                    pollen,\n                    truth_pollen,\n                    arithmetic_profile="source-compatible-22c6e480",\n                ),\n            )\n            cases.append(row)\n    scored = [case for case in cases if case["status"] == "scored"]\n',
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_reconstruction/english_receiver_annulus.py": (
        12954,
        "47c2c1cadd89edb3d33a289dbc08a3aa14aa7680d13e9032b8a20927a3d6da44",
        (
            (
                b"from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (\n    require_absent_artifact_output,\n)\nfrom bijux_pollenomics_dev.ci.report_rebuild.source_paths import (\n    safe_source_file as _safe_file,\n)\n",
                b"from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (\n    require_absent_artifact_output,\n)\nfrom bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError\nfrom bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (\n    GitSourceMember,\n    validate_blobs,\n)\nfrom bijux_pollenomics_dev.ci.report_rebuild.source_paths import (\n    safe_source_file as _safe_file,\n)\n",
            ),
            (
                b'    english_shared_ppe as english,\n)\nfrom bijux_pollenomics_lra.api import fit_shared_ppe_likelihood\n\nCAPTURE = Path("data/method-certification/english-receiver-annulus/kernel-capture.json")\nCAPTURE_SHA256 = "f0eb17181b88498aafbea9c18b3cad47701d117cb3c5a07f2321ceec18723094"\nNOMINAL_COVER = {\n    "Betula": 0.000686079829522849,\n    "Calluna.vulgaris": 0.021086575494765877,\n',
                b'    english_shared_ppe as english,\n)\nfrom bijux_pollenomics_lra.api import fit_shared_ppe_likelihood\nfrom bijux_pollenomics_lra.models.validation import finite_number\n\nCAPTURE = Path("data/method-certification/english-receiver-annulus/kernel-capture.json")\nCAPTURE_SHA256 = "f0eb17181b88498aafbea9c18b3cad47701d117cb3c5a07f2321ceec18723094"\n_SOURCE_PREFIX = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/"\n_ORIGINAL_KERNEL_FILES = {\n    "dispersal/kernels.py": ("1cc5485448afbe0626601669a8ac81fbcffee05e", 9757),\n    "dispersal/receiver_annulus.py": ("f8d8044ec35023ebc8051990aacfb1fc0ce0c63f", 7383),\n    "models/errors.py": ("7fc96895ee1ad5302d22c7a91101cc56cf11e8f4", 1526),\n    "models/validation.py": ("63fba8f1a2956ee9bc11cceb3b1328109a1d81dd", 9306),\n}\nNOMINAL_COVER = {\n    "Betula": 0.000686079829522849,\n    "Calluna.vulgaris": 0.021086575494765877,\n',
            ),
            (
                b'NOMINAL_OBJECTIVE = 1.0121082419620198\n\n\ndef _captured_kernel(\n    repository: Path, payload: dict[str, Any]\n) -> tuple[np.ndarray, str]:\n    """Use an independently admitted mathematical capture, never infer its authority."""\n    path = _safe_file(repository, CAPTURE.as_posix(), "English receiver kernel capture")\n    digest = english._sha(path)\n    if digest != CAPTURE_SHA256:\n',
                b'NOMINAL_OBJECTIVE = 1.0121082419620198\n\n\ndef _original_kernel_sources(repository: Path, record: dict[str, Any]) -> None:\n    """Authenticate the complete original mathematical capture without source copies."""\n    identities = record["kernel_dependency_sha256"]\n    if set(identities) != {_SOURCE_PREFIX + name for name in _ORIGINAL_KERNEL_FILES}:\n        raise ValueError("English receiver original mathematical source scope differs")\n    try:\n        validate_blobs(\n            repository,\n            [\n                GitSourceMember(\n                    _SOURCE_PREFIX + name,\n                    _SOURCE_PREFIX + name,\n                    record["kernel_candidate"],\n                    blob,\n                    identities[_SOURCE_PREFIX + name],\n                    size,\n                )\n                for name, (blob, size) in _ORIGINAL_KERNEL_FILES.items()\n            ],\n        )\n    except ReportRebuildError as error:\n        raise ValueError(\n            "English receiver original mathematical dependency is unauthenticated"\n        ) from error\n\n\ndef _native_number(value: object, name: str, *, positive: bool = False) -> float:\n    """Admit native JSON numbers through current scalar rules without normalization."""\n    if type(value) not in {int, float}:\n        raise ValueError("English receiver requires a native numeric " + name)\n    try:\n        result = finite_number(value, name, minimum=0, strict_minimum=positive)\n    except OverflowError as error:\n        raise ValueError(\n            "English receiver requires a finite number for " + name\n        ) from error\n    if result != value:\n        raise ValueError("English receiver scalar value changed: " + name)\n    return result\n\n\ndef _captured_kernel(\n    repository: Path, payload: dict[str, Any]\n) -> tuple[np.ndarray, str]:\n    """Reuse original coefficients under unchanged equations and current scalar admission.\n\n    Reading stored coefficients does not recompute quadrature. The original\n    validator belongs to that execution; its whole body is not a dependency of\n    current scalar admission on the fixed native support.\n    """\n    path = _safe_file(repository, CAPTURE.as_posix(), "English receiver kernel capture")\n    digest = english._sha(path)\n    if digest != CAPTURE_SHA256:\n',
            ),
            (
                b'        or record["receiver_radius_m"] != 80\n    ):\n        raise ValueError("English receiver capture scope differs")\n    for name, expected in record["kernel_dependency_sha256"].items():\n        if (\n            english._sha(\n                _safe_file(repository, name, "English receiver mathematical source")\n',
                b'        or record["receiver_radius_m"] != 80\n    ):\n        raise ValueError("English receiver capture scope differs")\n    _original_kernel_sources(repository, record)\n    for scalar in (\n        "receiver_radius_m",\n        "diffusion_coefficient",\n        "turbulence_parameter",\n        "wind_speed_m_s",\n    ):\n        _native_number(record[scalar], scalar, positive=scalar != "receiver_radius_m")\n    for relative in _ORIGINAL_KERNEL_FILES:\n        if relative == "models/validation.py":\n            continue\n        name = _SOURCE_PREFIX + relative\n        expected = record["kernel_dependency_sha256"][name]\n        if (\n            english._sha(\n                _safe_file(repository, name, "English receiver mathematical source")\n',
            ),
            (
                b'        (row["fall_speed_m_s"], row["inner_m"], row["outer_m"]): row for row in cases\n    }\n    expected_keys = {\n        (p["fallspeed_m_s"], r["inner_m"], r["outer_m"])\n        for p in payload["parameters"]\n        for r in payload["rings"]\n    }\n',
                b'        (row["fall_speed_m_s"], row["inner_m"], row["outer_m"]): row for row in cases\n    }\n    expected_keys = {\n        (\n            _native_number(p["fallspeed_m_s"], "fall_speed_m_s", positive=True),\n            _native_number(r["inner_m"], "inner_radius_m"),\n            _native_number(r["outer_m"], "outer_radius_m"),\n        )\n        for p in payload["parameters"]\n        for r in payload["rings"]\n    }\n',
            ),
        ),
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/lilla_gloppsjon_direct_pollen_scoring.py": (
        20545,
        "71d21da676461aeafdbaa77f06f83af83a5bd421eaab1bd2bfe5c10c98c5647c",
        (
            (
                b'                        row["reason"] = result.status\n                    else:\n                        row["mae_fraction"] = result.mae_fraction\n                        row["hellinger_distance"] = hellinger_distance(\n                            prediction["fractions"], observed\n                        )\n                except ValidationRefusal as exc:\n                    row["status"] = "failed_scoring"\n',
                b'                        row["reason"] = result.status\n                    else:\n                        row["mae_fraction"] = result.mae_fraction\n                        # Replay the arithmetic used for this committed scoring protocol.\n                        row["hellinger_distance"] = hellinger_distance(\n                            prediction["fractions"],\n                            observed,\n                            arithmetic_profile="source-compatible-22c6e480",\n                        )\n                except ValidationRefusal as exc:\n                    row["status"] = "failed_scoring"\n',
            ),
        ),
    ),
}
SCORING_PROTOCOL_SOURCES = frozenset(_SCORING_PROTOCOL_CONTRACTS)
_OPTIMIZER_CAPTURE_SHA256 = (
    "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93"
)


def scoring_protocol_extension_matches(
    name: str, captured: bytes, current: bytes
) -> bool:
    """Reverse only the declared scoring profile or stored-coefficient reader seams."""
    contract = _SCORING_PROTOCOL_CONTRACTS.get(name)
    if contract is None:
        return False
    size, checksum, pairs = contract
    if (
        len(captured) != size
        or hashlib.sha256(captured).hexdigest() != checksum
        or not 0 < len(current) <= 64 * 1024
    ):
        return False
    restored = current
    for previous, inserted in pairs:
        if captured.count(previous) != 1 or restored.count(inserted) != 1:
            return False
        restored = restored.replace(inserted, previous, 1)
    return restored == captured


def validated_scoring_protocol_source(
    repository: Path, historical: JsonObject, logical: str, source_buffer: SourceCapsule
) -> JsonObject:
    """Bind three original optimizer source members to their explicit reader changes."""
    name = historical.get("path")
    contract = _SCORING_PROTOCOL_CONTRACTS.get(name) if isinstance(name, str) else None
    if contract is None or not isinstance(name, str):
        raise ReportRebuildError("Scoring protocol source is outside its fixed scope")
    size, checksum, _ = contract
    expected = {"bytes": size, "sha256": checksum}
    if (
        repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.prefix
        != "data/method-certification/author-optimizer-diagnostic-source-capture"
        or source_buffer.descriptor.capture.get("sha256") != _OPTIMIZER_CAPTURE_SHA256
        or set(historical) != {"path", "bytes", "sha256"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": name, **expected}
        or logical != "executions/optimizer-diagnostics/first-party-inputs/" + name
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for original, path in group["resolved_paths"]
            if original == logical
        ]
        != [name]
    ):
        raise ReportRebuildError("Scoring protocol source binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    path = _regular_confined_file(repository, name, "current scoring protocol")
    before = path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 64 * 1024:
        raise ReportRebuildError("Scoring protocol must be bounded and single-link")
    current = path.read_bytes()
    if not scoring_protocol_extension_matches(name, captured, current):
        raise ReportRebuildError(
            "Scoring protocol differs beyond its original reader seams"
        )
    source_buffer.fresh()
    again = _regular_confined_file(repository, name, "current scoring protocol")
    after = again.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if (
        any(getattr(before, field) != getattr(after, field) for field in fields)
        or again.read_bytes() != current
    ):
        raise ReportRebuildError("Scoring protocol changed during correspondence")
    receiver = name.endswith("/english_receiver_annulus.py")
    return {
        "path": name,
        "classification": "finite_stored_receiver_coefficient_reader"
        if receiver
        else "explicit_historical_scoring_arithmetic_profile",
        "original_member": logical,
        "original_bytes": size,
        "original_sha256": checksum,
        "whole_old_module_reconstructed": True,
        "all_other_old_source_bytes_exact": True,
        "current_regular_single_link_and_stable": True,
        "saved_coefficients_read_not_recomputed": receiver,
        "current_scalar_admission_intentionally_separate": receiver,
        "historical_scoring_profile_explicitly_selected": not receiver,
        "old_native_equal_current_scoring_or_math_claimed": False,
        "new_quadrature_model_native_or_browser_execution_claimed": False,
    }
