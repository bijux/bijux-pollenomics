"""Qualify only the reviewed unconsumed author-evaluation source deltas."""

from __future__ import annotations

import ast
from collections.abc import Callable
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file

METRICS = "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra_validation/metrics.py"
SPATIAL = "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra_validation/spatial/__init__.py"
HISTORICAL_SOURCE_BINDINGS = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra_validation/metrics.py": {
        "sha256": "8c90297434e12dc5d5c14a2bed1857c9f19fbdbbdccd54d1454f3bb112ea5219",
        "bytes": 9355,
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra_validation/spatial/__init__.py": {
        "sha256": "3403cfda5c5791b95312b0293e87d20b8fe3d6f89e9a9814d405d80fb339e6ac",
        "bytes": 497,
    },
}
QUALIFIED_METRICS_SOURCE = {
    "sha256": "69d549fd0115c6bb5744aa9c971074f36769f53eb9efb7d1dedc2838589b458b",
    "bytes": 9713,
}
ADDED_EXPORTS = {
    "JointSpatialDraw",
    "UnavailableSpatialDraw",
    "propagate_withheld_spatial_draws",
    "spatial_identifiability",
}
QUALIFICATION = "reports/science/method-certification/author-evaluation-consumed-source-qualification.json"
QUALIFICATION_SHA256 = (
    "26d5b8e0c26e3c103a38d00522344e722281dd905607d556368722d55bd5f01e"
)
QUALIFICATION_BYTES = 101193
SCORE_EPOCH = "238978b0a426107dd3856dc0b080dab135cce72e"
NATIVE_REFERENCES = {
    "comparison": {
        "path": "artifacts/science/author-retained-pollen-current-score-execution/native/comparison.json",
        "sha256": "a07f3bd78b17a55e020b7c1b6d36ffd554d3ddddbc3ac96ae4cd5b49e45983d6",
        "bytes": 89948,
    },
    "terminal": {
        "path": "artifacts/science/author-retained-pollen-current-score-execution/native/terminal.json",
        "sha256": "682f1da26b290045bcf3456c1bfa4e3e637ceac3bb8e3535097680cf91719579",
        "bytes": 3211,
    },
    "execution": {
        "path": "artifacts/science/author-retained-pollen-current-score-execution/execution.json",
        "sha256": "0a248d15a22f80246a63d8a2fee7609349d19cd4d191a4ee5a6c09fca1071f0f",
        "bytes": 1392,
    },
}
PLAN_SHA256 = "58b9fd64f164f6ded700d61539b54db42a72aa76311fba5221912f6a4eda41d7"
HOLDOUT_EPOCH = "cacf5c5d956f379cf21b94b64791e1daf7650f1a"
CAPTURE_SHA256 = "76617093d6c0802273453bd9c4cdc68d2486e04baa146c4893ae7e441a090f7b"
ROUTES = (
    (
        "executions/uncertainty/first-party-inputs/docs/report/method-certification/author-site-uncertainty/replay.py",
        "2803daf31997eb360de257fdc92d046fbc68e68939b1bec48089a338c1e86e0a",
        10243,
    ),
    (
        "executions/profile/first-party-inputs/docs/report/method-certification/author-site-profile-comparison/replay.py",
        "0c86df8b7c4964eea0f01e445361a73782495a199a71974631d39430915ec51f",
        6883,
    ),
    (
        "executions/holdout/first-party-inputs/docs/report/pollen-reconstruction/author-example-site-mean-holdout/replay.py",
        "ebaa48cb85d3d130168f8ed603ebe48fe31ce957e07b9b4ca9ff140b234c780a",
        6003,
    ),
    (
        "executions/holdout/first-party-inputs/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/observed_pollen_baseline.py",
        "b351802269ba2a74f74845c549dc2f6e5650f235c596bdb859f9826e0d05f690",
        18098,
    ),
)


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ReportRebuildError(message)


def _identity(body: bytes) -> dict[str, Any]:
    return {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}


def _ast(body: bytes) -> ast.Module:
    try:
        return ast.parse(body)
    except (SyntaxError, UnicodeError) as error:
        raise ReportRebuildError("Consumed-source Python syntax differs") from error


def _prove_delta(name: str, old: bytes, new: bytes) -> None:
    if name == METRICS:
        from ..source_roles.numerical_precision import stable_hellinger_profile_basis

        basis = stable_hellinger_profile_basis(new)
        _require(
            basis is not None,
            "Explicit Hellinger profile differs beyond its finite source law",
        )
        assert basis is not None
        new = basis
    historical, current = _ast(old), _ast(new)
    if name == METRICS:
        definitions = []
        for tree in (historical, current):
            removed = [
                node
                for node in tree.body
                if isinstance(node, ast.FunctionDef)
                and node.name == "hellinger_distance"
            ]
            _require(
                len(removed) == 1,
                "Exactly one unconsumed Hellinger definition required",
            )
            definitions.append(removed[0])
            tree.body = [node for node in tree.body if node not in removed]
        # Defaults, annotations and decorators can execute while a module loads.
        # Only the unused function body may differ, never its definition header.
        for definition in definitions:
            definition.body = []
        _require(
            ast.dump(definitions[0], include_attributes=False)
            == ast.dump(definitions[1], include_attributes=False),
            "Unconsumed Hellinger definition header changed",
        )
    elif name == SPATIAL:
        allowed = {
            "spatial_identifiability": "identifiability",
            "JointSpatialDraw": "uncertainty",
            "UnavailableSpatialDraw": "uncertainty",
            "propagate_withheld_spatial_draws": "uncertainty",
        }
        for node in list(current.body):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name in ADDED_EXPORTS:
                        _require(
                            node.level == 1
                            and node.module == allowed[alias.name]
                            and alias.asname in (None, alias.name),
                            "Unconsumed spatial export origin changed",
                        )
                node.names = [
                    alias for alias in node.names if alias.name not in ADDED_EXPORTS
                ]
                if not node.names:
                    current.body.remove(node)
            elif (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "__all__"
            ):
                _require(
                    isinstance(node.value, ast.List),
                    "Literal spatial export list required",
                )
                assert isinstance(node.value, ast.List)
                node.value.elts = [
                    value
                    for value in node.value.elts
                    if not isinstance(value, ast.Constant)
                    or value.value not in ADDED_EXPORTS
                ]
    else:
        raise ReportRebuildError("No reviewed author consumed-source delta")
    _require(
        ast.dump(historical, include_attributes=False)
        == ast.dump(current, include_attributes=False),
        "Author consumed functions/imports/globals changed",
    )


def validated_consumed_source_pair(
    repository: Path,
    historical: dict[str, Any],
    retained: str,
    read_original: Callable[[str], bytes],
) -> JsonObject:
    """Authenticate original source and prove the finite unconsumed API boundary."""
    name = historical.get("path")
    _require(
        isinstance(name, str) and name in HISTORICAL_SOURCE_BINDINGS,
        "Unreviewed author scientific source changed",
    )
    assert isinstance(name, str)
    expected = HISTORICAL_SOURCE_BINDINGS[name]
    _require(
        historical == {"path": name, **expected}
        and type(historical.get("bytes")) is int,
        "Original author projection identity differs",
    )
    _require(
        retained.endswith("/first-party-inputs/" + name),
        "Author retained source role differs",
    )
    old = read_original(retained)
    _require(_identity(old) == expected, "Original author source bytes differ")
    path = _regular_confined_file(repository, name, "author consumed source")
    _require(path.stat().st_nlink == 1, "Author current source has multiple links")
    _prove_delta(name, old, path.read_bytes())
    return {
        "path": name,
        "historical": expected,
        "classification": "reviewed-unconsumed-source-delta",
        "current_consumed_implementation_exact": True,
        "whole_current_source_equality_claimed": False,
        "current_model_reexecution_claimed": False,
    }


def _routes(repository: Path, read_original: Callable[[str], bytes]) -> None:
    for name, checksum, size in ROUTES:
        body = read_original(name)
        _require(
            _identity(body) == {"sha256": checksum, "bytes": size},
            "Original author consumed route differs",
        )
        tree = _ast(body)
        forbidden = ADDED_EXPORTS | {"hellinger_distance"}
        for node in ast.walk(tree):
            _require(
                not (isinstance(node, ast.Name) and node.id in forbidden)
                and not (isinstance(node, ast.Attribute) and node.attr in forbidden),
                "Original author route invokes changed API",
            )
            if isinstance(node, ast.ImportFrom):
                _require(
                    not any(alias.name in forbidden for alias in node.names)
                    and ".lra_validation.spatial" not in (node.module or ""),
                    "Original author route imports changed API",
                )
        if name == ROUTES[-1][0]:
            current_name = name.split("/first-party-inputs/", 1)[1]
            current = _regular_confined_file(
                repository, current_name, "author score consumer"
            )
            _require(
                current.read_bytes() == body, "Actual author scoring consumer changed"
            )


def _json(body: bytes) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in rows:
            _require(key not in result, "Duplicate author qualification key")
            result[key] = value
        return result

    try:
        value = json.loads(
            body,
            object_pairs_hook=pairs,
            parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
        )
    except (ValueError, UnicodeError) as error:
        raise ReportRebuildError(
            "Author numerical qualification JSON differs"
        ) from error
    _require(isinstance(value, dict), "Author qualification object required")
    assert isinstance(value, dict)
    return value


def _numeric_qualification(value: dict[str, Any]) -> None:
    """Validate actual retained outcomes; never execute score/model code here."""
    _require(
        value.get("schema_version")
        == "author-evaluation-consumed-source-qualification.v1",
        "Author qualification schema differs",
    )
    report, terminal, execution = (
        value[name] for name in ("comparison", "terminal", "execution")
    )
    candidate = value["executed_candidate"]
    _require(
        candidate == SCORE_EPOCH and value["native_references"] == NATIVE_REFERENCES,
        "Actual score epoch required",
    )
    _require(
        report["schema_version"] == "author-retained-pollen-current-score-comparison.v1"
        and report["candidate"] == candidate
        and report["passed"] is True
        and report["original_holdout_epoch"] == HOLDOUT_EPOCH,
        "Author score comparison epoch/disposition differs",
    )
    _require(
        type(report["absolute_tolerance"]) is int
        and report["absolute_tolerance"] == 0
        and type(report["new_fits_optimizer_K_R_or_hellinger_calls"]) is int
        and report["new_fits_optimizer_K_R_or_hellinger_calls"] == 0,
        "Author score scope/tolerance differs",
    )
    _require(
        report["original_dispositions"]
        == {"scored": 177, "no_observed_count": 241, "no_training_site_same_bin": 7},
        "Original425author dispositions differ",
    )
    rows = report["comparison_rows"]
    _require(
        isinstance(rows, list) and len(rows) == 177,
        "Exactly177current score results required",
    )
    keys = set()
    for row in rows:
        _require(
            set(row["identity"]) == {"grid_id", "held_out_site_id", "bin_id_bp"},
            "Author score identity axis differs",
        )
        key = tuple(
            row["identity"][name]
            for name in ("grid_id", "held_out_site_id", "bin_id_bp")
        )
        _require(
            all(type(part) is str and part for part in key) and key not in keys,
            "Duplicate/incomplete author score identity",
        )
        keys.add(key)
        _require(
            row["status"] == "compared" and row["passed"] is True,
            "Current author score refused/notrun/mismatched",
        )
        for name in ("mae_fraction", "total_variation"):
            saved, current = row["saved_" + name], row["current_" + name]
            _require(
                type(saved) in (int, float)
                and type(current) in (int, float)
                and math.isfinite(saved)
                and math.isfinite(current)
                and 0 <= saved <= 1
                and saved == current,
                "Author MAE/TV not exact finite retained values",
            )
    inputs = report["input_pins"]
    _require(
        inputs["original_capture"]["sha256"] == CAPTURE_SHA256
        and {k: inputs["metrics_source"][k] for k in ("sha256", "bytes")}
        == QUALIFIED_METRICS_SOURCE,
        "Author score source authority differs",
    )
    for name in ("comparison", "terminal", "execution"):
        raw = (json.dumps(value[name], indent=2, allow_nan=False) + "\n").encode()
        _require(
            _identity(raw)
            == {k: value["native_references"][name][k] for k in ("sha256", "bytes")},
            "Retained author native buffer identity differs",
        )
    _require(
        terminal["candidate"] == candidate
        and terminal["plan_sha256"] == PLAN_SHA256
        and type(terminal["actual_exit"]) is int
        and terminal["actual_exit"] == 0
        and terminal["source_pins_before_mismatches"]
        == terminal["source_pins_after_mismatches"]
        == [],
        "Actual author native custody/exit differs",
    )
    stages = terminal["stages"]
    _require(
        len(stages) == 1
        and stages[0]["id"] == "current-retained-pollen-MAE-TV"
        and type(stages[0]["actual_exit"]) is int
        and stages[0]["actual_exit"] == 0
        and stages[0]["timed_out"] is False,
        "Actual author scoring stage differs",
    )
    _require(
        execution["candidate"] == candidate
        and execution["command"][-1] == PLAN_SHA256
        and type(execution["actual_exit"]) is int
        and execution["actual_exit"] == 0
        and type(execution["native_exit"]) is int
        and execution["native_exit"] == 0
        and execution["timed_out"] is False,
        "Actual author collector did not pass",
    )


def validated_author_score_qualification(
    repository: Path, pairs: list[JsonObject], read_original: Callable[[str], bytes]
) -> JsonObject:
    """Require finite source roles and the retained177-group execution proof."""
    _require(
        len(pairs) == 2
        and {row["path"] for row in pairs} == set(HISTORICAL_SOURCE_BINDINGS),
        "Author changed-source population differs",
    )
    _routes(repository, read_original)
    path = _regular_confined_file(
        repository, QUALIFICATION, "author score qualification"
    )
    _require(
        path.stat().st_nlink == 1
        and path.stat().st_size == QUALIFICATION_BYTES
        and 0 < QUALIFICATION_BYTES <= 256 * 1024,
        "Bounded physical author qualification required",
    )
    raw = path.read_bytes()
    _require(
        _identity(raw)
        == {"sha256": QUALIFICATION_SHA256, "bytes": QUALIFICATION_BYTES},
        "Reviewed author qualification identity differs",
    )
    try:
        value = _json(raw)
        _numeric_qualification(value)
    except (KeyError, TypeError, ValueError) as error:
        raise ReportRebuildError(
            "Author numerical qualification is incomplete"
        ) from error
    return {
        "qualification_sha256": QUALIFICATION_SHA256,
        "executed_candidate": value["executed_candidate"],
        "original_holdout_epoch": HOLDOUT_EPOCH,
        "score_groups": 177,
        "original_dispositions": 425,
        "scope": "Current-source retained MAE/TV compatibility only. Original three model/source epochs and unresolved six-table lawful-custody criterion unchanged; no Hellinger result, new heldout/model/accuracy, hosted or complete scientific certification.",
    }
