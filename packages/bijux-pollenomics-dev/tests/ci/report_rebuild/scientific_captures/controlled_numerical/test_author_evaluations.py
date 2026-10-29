"""Keep author consumed-source qualifications exact without numerical replay."""

from __future__ import annotations

from collections.abc import Callable
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.controlled_numerical import (
    author_evaluations as guard,
)

REPOSITORY = Path(__file__).resolve().parents[7]


@pytest.fixture(scope="module")
def qualification() -> dict[str, Any]:
    """Decode the bounded177-row product once; no2406-member source fixture."""
    return cast(
        dict[str, Any], json.loads((REPOSITORY / guard.QUALIFICATION).read_bytes())
    )


def test_actual_retained_score_scope_is_exact(qualification: dict[str, Any]) -> None:
    guard._numeric_qualification(qualification)
    assert qualification["executed_candidate"] == guard.SCORE_EPOCH
    report = qualification["comparison"]
    assert len(report["comparison_rows"]) == 177
    assert sum(report["original_dispositions"].values()) == 425
    assert report["original_holdout_epoch"] != qualification["executed_candidate"]


@pytest.mark.parametrize(
    "change",
    [
        "epoch",
        "old-epoch",
        "native-one",
        "boolean-zero",
        "timeout",
        "stage",
        "after-pins",
        "rows",
        "duplicate",
        "refused",
        "not-run",
        "mismatch",
        "nonfinite",
        "tolerance",
        "dispositions",
        "source",
        "native-proof",
        "resealed-product",
    ],
)
def test_changed_numerical_scope_or_native_proof_refused(
    qualification: dict[str, Any], change: str
) -> None:
    value = copy.deepcopy(qualification)
    report = value["comparison"]
    if change == "epoch":
        value["executed_candidate"] = "f" * 40
    elif change == "old-epoch":
        report["original_holdout_epoch"] = guard.SCORE_EPOCH
    elif change == "native-one":
        value["terminal"]["actual_exit"] = 1
    elif change == "boolean-zero":
        value["terminal"]["actual_exit"] = False
    elif change == "timeout":
        value["execution"]["timed_out"] = True
    elif change == "stage":
        value["terminal"]["stages"][0]["id"] = "different"
    elif change == "after-pins":
        value["terminal"]["source_pins_after_mismatches"] = ["changed"]
    elif change == "rows":
        report["comparison_rows"].pop()
    elif change == "duplicate":
        report["comparison_rows"][1] = copy.deepcopy(report["comparison_rows"][0])
    elif change in {"refused", "not-run"}:
        report["comparison_rows"][0]["status"] = (
            "current_validation_refusal"
            if change == "refused"
            else "not_run_after_fatal"
        )
    elif change == "mismatch":
        report["comparison_rows"][0]["current_mae_fraction"] = 1
    elif change == "nonfinite":
        report["comparison_rows"][0]["saved_mae_fraction"] = float("nan")
    elif change == "tolerance":
        report["absolute_tolerance"] = 1e-8
    elif change == "dispositions":
        report["original_dispositions"]["no_observed_count"] = 240
    elif change == "source":
        report["input_pins"]["metrics_source"]["sha256"] = "0" * 64
    elif change == "native-proof":
        value["native_references"]["execution"]["sha256"] = "0" * 64
    else:
        row = report["comparison_rows"][0]
        row["saved_mae_fraction"] = row["current_mae_fraction"] = 0.5
        raw = (json.dumps(report, indent=2) + "\n").encode()
        value["native_references"]["comparison"]["sha256"] = hashlib.sha256(
            raw
        ).hexdigest()
        value["native_references"]["comparison"]["bytes"] = len(raw)
    with pytest.raises(ReportRebuildError):
        guard._numeric_qualification(value)


OLD_METRICS = b"SCALE = 1\ndef hellinger_distance(x):\n    return x\ndef score_pollen(x):\n    return SCALE*x\n"
NEW_METRICS = OLD_METRICS.replace(b"return x", b"return x + 1", 1)
OLD_SPATIAL = (
    b"from .model import FittedSpatialModel\n__all__ = ['FittedSpatialModel']\n"
)
NEW_SPATIAL = b"from .model import FittedSpatialModel\nfrom .identifiability import spatial_identifiability\n__all__ = ['FittedSpatialModel', 'spatial_identifiability']\n"


def test_only_unconsumed_metrics_function_is_removed_from_ast_comparison() -> None:
    guard._prove_delta(guard.METRICS, OLD_METRICS, NEW_METRICS)
    guard._prove_delta(guard.SPATIAL, OLD_SPATIAL, NEW_SPATIAL)


@pytest.mark.parametrize(
    "change",
    [
        "score",
        "global",
        "import",
        "missing-hellinger",
        "old-spatial-binding",
        "spatial-global",
    ],
)
def test_math_globals_or_existing_spatial_bindings_cannot_change(change: str) -> None:
    name, old, new = guard.METRICS, OLD_METRICS, NEW_METRICS
    if change == "score":
        new = new.replace(b"SCALE*x", b"SCALE+x")
    elif change == "global":
        new = new.replace(b"SCALE = 1", b"SCALE = 2")
    elif change == "import":
        new = b"from foreign import SCALE\n" + new
    elif change == "missing-hellinger":
        new = new.replace(b"hellinger_distance", b"different_function")
    else:
        name, old, new = guard.SPATIAL, OLD_SPATIAL, NEW_SPATIAL
        if change == "old-spatial-binding":
            new = new.replace(b"from .model", b"from .foreign")
        else:
            new += b"UNREVIEWED = 1\n"
    with pytest.raises(ReportRebuildError):
        guard._prove_delta(name, old, new)


@pytest.fixture
def source_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any], str, Callable[[str], bytes]]:
    name = guard.METRICS
    target = tmp_path / name
    target.parent.mkdir(parents=True)
    target.write_bytes(NEW_METRICS)
    monkeypatch.setattr(
        guard,
        "HISTORICAL_SOURCE_BINDINGS",
        {name: guard._identity(OLD_METRICS)},
    )
    retained = "executions/holdout/first-party-inputs/" + name

    def historical(logical: str) -> bytes:
        assert logical == retained
        return OLD_METRICS

    return (
        tmp_path,
        {"path": name, **guard._identity(OLD_METRICS)},
        retained,
        historical,
    )


def test_reviewed_pair_authenticates_git_logical_role(
    source_pair: tuple[Path, dict[str, Any], str, Callable[[str], bytes]],
) -> None:
    repository, historical, retained, read_original = source_pair
    receipt = guard.validated_consumed_source_pair(
        repository, historical, retained, read_original
    )
    assert receipt["historical"] == guard._identity(OLD_METRICS)
    assert receipt["current_consumed_implementation_exact"] is True
    assert receipt["whole_current_source_equality_claimed"] is False
    assert receipt["current_model_reexecution_claimed"] is False


@pytest.mark.parametrize(
    "change",
    [
        "foreign-path",
        "historical-hash",
        "boolean-size",
        "extra-proof",
        "retained-role",
        "unqualified-current",
        "symlink",
    ],
)
def test_unqualified_source_or_role_cannot_enter_consumed_correspondence(
    source_pair: tuple[Path, dict[str, Any], str, Callable[[str], bytes]], change: str
) -> None:
    repository, historical, retained, read_original = source_pair
    path = repository / historical["path"]
    if change == "foreign-path":
        historical["path"] = "unreviewed.py"
    elif change == "historical-hash":
        historical["sha256"] = "0" * 64
    elif change == "boolean-size":
        historical["bytes"] = True
    elif change == "extra-proof":
        historical["approved"] = True
    elif change == "retained-role":
        retained = "unreviewed/" + historical["path"]
    elif change == "unqualified-current":
        path.write_bytes(NEW_METRICS + b"different = True\n")
    else:
        path.unlink()
        path.symlink_to(repository / "outside.py")
    exception = ReportOwnershipError if change == "symlink" else ReportRebuildError
    with pytest.raises(exception):
        guard.validated_consumed_source_pair(
            repository, historical, retained, read_original
        )


def test_partial_or_duplicate_delta_population_refuses_before_custody(
    tmp_path: Path,
) -> None:
    for paths in ([], [guard.METRICS], [guard.METRICS, guard.METRICS]):
        with pytest.raises(ReportRebuildError):
            guard.validated_author_score_qualification(
                tmp_path, [{"path": path} for path in paths], lambda name: b""
            )


@pytest.mark.parametrize("change", ["missing", "symlink", "changed", "unbounded"])
def test_qualification_physical_or_product_mutation_refuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    qualification: dict[str, Any],
    change: str,
) -> None:
    monkeypatch.setattr(guard, "_routes", lambda repository, reader: None)
    path = tmp_path / guard.QUALIFICATION
    path.parent.mkdir(parents=True)
    body = (json.dumps(qualification, indent=2) + "\n").encode()
    if change == "symlink":
        path.symlink_to(tmp_path / "outside.json")
    elif change == "changed":
        path.write_bytes(body.replace(b'"passed": true', b'"passed": false', 1))
    elif change == "unbounded":
        path.write_bytes(body + b" " * (256 * 1024))
    expected = (
        ReportOwnershipError if change in {"missing", "symlink"} else ReportRebuildError
    )
    with pytest.raises(expected):
        guard.validated_author_score_qualification(
            tmp_path,
            [{"path": name} for name in guard.HISTORICAL_SOURCE_BINDINGS],
            lambda name: b"",
        )


@pytest.mark.parametrize("changed_api", [False, True])
def test_original_consumer_route_keeps_unconsumed_changes_outside_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed_api: bool
) -> None:
    body = (
        b"from bijux_pollenomics.analysis.lra_validation.metrics import score_pollen\n"
    )
    if changed_api:
        body += b"from bijux_pollenomics.analysis.lra_validation.metrics import hellinger_distance\n"
    name = "executions/holdout/first-party-inputs/consumer.py"
    monkeypatch.setattr(
        guard, "ROUTES", ((name, hashlib.sha256(body).hexdigest(), len(body)),)
    )
    (tmp_path / "consumer.py").write_bytes(body)
    if changed_api:
        with pytest.raises(ReportRebuildError):
            guard._routes(tmp_path, lambda logical: body)
    else:
        guard._routes(tmp_path, lambda logical: body)


@pytest.mark.parametrize(
    "change", ["default", "decorator", "return-annotation", "export-origin"]
)
def test_unconsumed_definition_cannot_change_import_time_behavior(change: str) -> None:
    name, old, new = guard.METRICS, OLD_METRICS, NEW_METRICS
    if change == "default":
        new = new.replace(
            b"hellinger_distance(x)", b"hellinger_distance(x=unreviewed())"
        )
    elif change == "decorator":
        new = new.replace(
            b"def hellinger_distance", b"@unreviewed\ndef hellinger_distance"
        )
    elif change == "return-annotation":
        new = new.replace(
            b"hellinger_distance(x):", b"hellinger_distance(x) -> unreviewed():"
        )
    else:
        name, old = guard.SPATIAL, OLD_SPATIAL
        new = NEW_SPATIAL.replace(b"from .identifiability", b"from .foreign")
    with pytest.raises(ReportRebuildError):
        guard._prove_delta(name, old, new)


def test_current_source_comments_are_not_a_software_postimage_gate(
    source_pair: tuple[Path, dict[str, Any], str, Callable[[str], bytes]],
) -> None:
    repository, historical, retained, read_original = source_pair
    path = repository / historical["path"]
    path.write_bytes(path.read_bytes() + b"# Unchanged consumed implementation.\n")
    receipt = guard.validated_consumed_source_pair(
        repository, historical, retained, read_original
    )
    assert receipt["current_consumed_implementation_exact"] is True
