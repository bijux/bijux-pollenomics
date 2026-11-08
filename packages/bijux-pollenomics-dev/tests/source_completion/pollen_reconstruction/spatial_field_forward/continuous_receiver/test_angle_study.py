"""Real synthetic producer/observer transport and fail-closed six-owner accounting."""

from __future__ import annotations

from dataclasses import asdict
from fractions import Fraction as F
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.angle_moments import (
    observe,
    study,
    transport,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.angle_moments.inputs import (
    FrozenInputs,
    identity,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.angle_moments.population import (
    MomentPopulation,
    enclose_population,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.contracts import (
    OWNERS,
    RESOURCE_LIMITS,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.receiver_angles import (
    verify_angle_certificate,
)


@pytest.fixture(scope="module")
def synthetic_population() -> MomentPopulation:
    """Evaluate one source-free five-domain geometry, never the frozen six cases."""
    geometry = Geometry(F(1, 2), F(1), F(4), (F(1000), F(0)), (F(2000), F(0)))
    population = enclose_population((geometry,), max_leaves=5)
    return MomentPopulation(
        population.results * 6,
        population.refusals * 6,
        population.budgets * 6,
        population.elapsed_seconds,
    )


def configure(
    root: Path, monkeypatch: pytest.MonkeyPatch, population: MomentPopulation
) -> Path:
    result = population.results[0]
    assert result is not None
    model = result.partition.geometry
    geometry = {
        "coefficient_A": str(model.coefficient),
        "receiver_radius_m": str(model.receiver),
        "outer_radius_m": str(model.outer),
        "first_anchor_xy_m": [str(x) for x in model.first],
        "second_anchor_xy_m": [str(x) for x in model.second],
    }
    frozen = {
        "source_commit": "retained-unit-law",
        "cases": [
            {"core": core, "taxon": taxon, "geometry": geometry}
            for core, taxon in OWNERS
        ],
    }
    inputs = FrozenInputs(
        {
            "law": {"unit_control": True},
            "limits": "synthetic control only",
            "independent_resources": {"wall_seconds": 180},
        },
        frozen,
        (model,) * 6,
        {"unit-control": identity(b"exact synthetic law")},
    )
    guard = transport.SourceGuard("committed-unit-control", "index-control", ())
    for module in (study, observe):
        monkeypatch.setattr(module, "read_inputs", lambda *args: inputs)
        monkeypatch.setattr(
            module, "environment", lambda *args: {"synthetic_control": True}
        )
        monkeypatch.setattr(module, "source_guard", lambda *args: guard)
        monkeypatch.setattr(
            module,
            "check_terminal",
            lambda *args: {
                "source_and_index_unchanged": True,
                "inputs_unchanged": True,
                "elapsed_seconds": 0,
                "peak_rss_bytes": 1,
            },
        )
    monkeypatch.setattr(study, "enclose_population", lambda *args: population)
    return root / "unit-control.json"


def test_actual_synthetic_serialization_replays_independently(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)
    producer = tmp_path / "artifacts/producer"
    native = study.run_study(tmp_path, protocol, producer)
    assert native["status"] == "refuse_unresolved"
    assert native["complete_cases"] == 6
    assert native["certified_widths"] < 18
    result = observe.run_observer(
        tmp_path, protocol, producer, tmp_path / "artifacts/observer"
    )
    assert result["accounting_verified"] is True
    assert result["status"] == "refuse_unresolved"
    assert result["complete_cases"] == 6
    assert result["completed_leaves"] == 30
    assert result["independent_certified_widths"] < 18
    assert all(row["initial_domains"] == 5 for row in result["cases"])
    assert all("independent_bounds" in row for row in result["cases"])
    assert native["native_prefix_recaptured"] is False


@pytest.mark.parametrize(
    "fault",
    ["source", "input", "resource", "owner", "certificate-index", "certificate-bytes"],
)
def test_observer_refuses_changed_identity_owner_or_certificate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
    fault: str,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)
    producer = tmp_path / "artifacts/producer"
    study.run_study(tmp_path, protocol, producer)
    path = producer / "result.json"
    result = json.loads(path.read_bytes())
    if fault == "source":
        result["source_commit"] = "foreign"
    elif fault == "input":
        result["input_identities"] = {}
    elif fault == "resource":
        result["resource_limits"]["wall_seconds"] = 181
    elif fault == "owner":
        result["cases"][0]["core"] = "foreign"
    elif fault == "certificate-index":
        result["cases"][0]["certificate_index"] = 1
    else:
        (producer / "certificates.json").write_bytes(b"[]")
    path.write_text(json.dumps(result))
    output = tmp_path / "artifacts/observer"
    with pytest.raises(ValueError):
        observe.run_observer(tmp_path, protocol, producer, output)
    failed = json.loads((output / "independent-check.json").read_bytes())
    assert failed["status"] == "failed"
    assert len(failed["cases"]) == 6
    assert failed["error"]


def test_producer_failure_keeps_all_original_owner_slots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)

    def fail(*args: object) -> None:
        raise ValueError("source mismatch control")

    monkeypatch.setattr(study, "source_guard", fail)
    output = tmp_path / "artifacts/producer"
    with pytest.raises(ValueError, match="source mismatch"):
        study.run_study(tmp_path, protocol, output)
    result = json.loads((output / "result.json").read_bytes())
    assert result["status"] == "failed"
    assert [(row["core"], row["taxon"]) for row in result["cases"]] == list(OWNERS)
    assert all(row["complete"] is False for row in result["cases"])


def test_work_minimum_and_one_dimensional_reservation_checks() -> None:
    work = {
        "attempted_panels": 5,
        "reserved_node_evaluations": 35,
        "completed_node_evaluations": 35,
        "derivative_boxes": 5,
        "leaf_reservations": 5,
    }
    minima = {
        "minimum_attempted_panels": 5,
        "minimum_completed_nodes": 35,
        "minimum_derivative_boxes": 5,
        "leaves": 5,
    }
    assert observe._work({"work": work}, minima) == work
    for name, value in (
        ("reserved_node_evaluations", 34),
        ("derivative_boxes", 4),
        ("leaf_reservations", 4),
        ("attempted_panels", True),
    ):
        changed = {**work, name: value}
        with pytest.raises(ValueError):
            observe._work({"work": changed}, minima)


def test_output_owner_is_fresh_bounded_and_does_not_follow_symbols(
    tmp_path: Path,
) -> None:
    output = transport.fresh_output(tmp_path, tmp_path / "artifacts/output")
    raw = transport.write_json(output, "receipt.json", {"scope": "control"})
    assert identity(raw)["bytes"] == len(raw)
    with pytest.raises(ValueError):
        transport.fresh_output(tmp_path, output)
    with pytest.raises(ValueError):
        transport.write_json(output, "receipt.json", {})
    with pytest.raises(ValueError):
        transport.write_json(output, "../escape.json", {})
    with pytest.raises(ValueError, match="allocation"):
        transport.write_json(output, "oversize.json", "x" * 4_850_000)
    (tmp_path / "artifacts/alias").symlink_to(output, target_is_directory=True)
    with pytest.raises(ValueError):
        transport.fresh_output(tmp_path, tmp_path / "artifacts/alias/child")


def test_source_guard_serialization_keeps_exact_closure() -> None:
    guard = transport.SourceGuard("source", "index", (("owned.py", "digest"),))
    assert json.loads(json.dumps(asdict(guard))) == {
        "head": "source",
        "index_sha256": "index",
        "files": [["owned.py", "digest"]],
    }
    assert RESOURCE_LIMITS["integration_work_seconds"] == 160


@pytest.mark.parametrize(
    "field", ["status", "q_bound", "global_series_remainder_radius"]
)
def test_observer_binds_reported_status_and_series_witness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
    field: str,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)
    producer = tmp_path / "artifacts/producer"
    study.run_study(tmp_path, protocol, producer)
    path = producer / "result.json"
    result = json.loads(path.read_bytes())
    result["cases"][0][field] = "foreign"
    path.write_text(json.dumps(result))
    output = tmp_path / "artifacts/observer"
    with pytest.raises(ValueError, match="mathematical flags"):
        observe.run_observer(tmp_path, protocol, producer, output)
    failed = json.loads((output / "independent-check.json").read_bytes())
    assert failed["cases"][0]["independent_bounds"]
    assert failed["progress"]["completed_leaves"] == 5
    assert failed["cases"][1]["status"] == "not_replayed"


def test_terminal_producer_failure_keeps_closed_cases_and_certificates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)

    def fail(*args: object) -> None:
        raise ValueError("terminal source mismatch control")

    monkeypatch.setattr(study, "check_terminal", fail)
    output = tmp_path / "artifacts/producer"
    with pytest.raises(ValueError, match="terminal source"):
        study.run_study(tmp_path, protocol, output)
    result = json.loads((output / "result.json").read_bytes())
    assert result["status"] == "failed"
    assert result["complete_cases"] == 6
    assert all(
        row["complete"] is True and row["saved_leaves"] == 5 for row in result["cases"]
    )
    assert result["certificate_identity"] == identity(
        (output / "certificates.json").read_bytes()
    )


def test_later_observer_failure_retains_replayed_prefix_and_current_owner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)
    producer = tmp_path / "artifacts/producer"
    study.run_study(tmp_path, protocol, producer)
    original = verify_angle_certificate
    calls = 0

    def stop(*args: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ValueError("later replay refusal control")
        return original(*args)

    monkeypatch.setattr(observe, "verify_angle_certificate", stop)
    output = tmp_path / "artifacts/observer"
    with pytest.raises(ValueError, match="later replay"):
        observe.run_observer(tmp_path, protocol, producer, output)
    result = json.loads((output / "independent-check.json").read_bytes())
    assert result["status"] == "failed"
    assert result["complete_cases"] == 1
    assert result["cases"][0]["status"] == "fixed_leaf_replayed"
    assert result["cases"][1]["status"] == "replay_started"
    assert result["cases"][2]["status"] == "not_replayed"
    assert result["progress"]["current_case"] == ["BOKE", "Ulmus"]
    assert result["progress"]["completed_leaves"] == 5


def historical_source(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, Any], dict[str, Any], transport.SourceGuard, dict[str, Any]]:
    """Model exact Git blobs; only the two observer modules may differ."""
    import hashlib
    import subprocess

    owner = observe._SOURCE_OWNER
    names = [
        owner + "angle_moments/transport.py",
        owner + "kernel.py",
        "uv.lock",
        "reports/captured-protocol.json",
        *sorted(observe._OBSERVER_ONLY),
    ]
    blobs = {name: ("historical:" + name).encode() for name in names}
    old = {name: hashlib.sha256(raw).hexdigest() for name, raw in blobs.items()}
    current = {
        name: ("e" * 64 if name in observe._OBSERVER_ONLY else digest)
        for name, digest in old.items()
    }
    original = {
        "head": "a" * 40,
        "index_sha256": "d" * 64,
        "files": [[name, digest] for name, digest in old.items()],
    }
    before = transport.SourceGuard("b" * 40, "c" * 64, tuple(current.items()))
    external_context = {"source_commit": "a" * 40, "index_sha256_before": "d" * 64}
    external_terminal = {"source_commit": "a" * 40}

    def blob(command: list[str], **kwargs: Any) -> bytes:
        name = command[-1].split(":", 1)[1]
        return str(len(blobs[name])).encode() if command[-2] == "-s" else blobs[name]

    monkeypatch.setattr(subprocess, "check_output", blob)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0),
    )
    monkeypatch.setattr(
        observe,
        "_external_receipts",
        lambda *args: (
            external_context,
            external_terminal,
            {"bound": "external receipts"},
        ),
    )
    return {"source": original}, {"source_commit": "a" * 40}, before, external_context


def test_historical_producer_bridge_authenticates_original_equations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, result, before, _ = historical_source(monkeypatch)
    bridge = observe._producer_source(
        tmp_path, tmp_path / "artifacts/producer/products", context, result, before
    )
    assert bridge["producer_source_commit"] == "a" * 40
    assert bridge["observer_source_commit"] == "b" * 40
    assert bridge["historical_git_blobs_authenticated"] is True
    assert bridge["unchanged_producer_source_files"] == 4
    assert sorted(row["path"] for row in bridge["observer_only_differences"]) == sorted(
        observe._OBSERVER_ONLY
    )
    assert bridge["external_receipts"]


@pytest.mark.parametrize(
    "fault",
    [
        "transport",
        "input",
        "lock",
        "omitted",
        "claim",
        "git-blob",
        "foreign-head",
        "index",
    ],
)
def test_historical_bridge_refuses_changed_producer_or_unbound_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    import subprocess

    context, result, before, external = historical_source(monkeypatch)
    current = dict(before.files)
    if fault in ("transport", "input", "lock"):
        name = {
            "transport": observe._SOURCE_OWNER + "angle_moments/transport.py",
            "input": "reports/captured-protocol.json",
            "lock": "uv.lock",
        }[fault]
        current[name] = "f" * 64
        before = transport.SourceGuard(
            before.head, before.index_sha256, tuple(current.items())
        )
    elif fault == "omitted":
        context["source"]["files"].pop(0)
    elif fault == "claim":
        result["source_commit"] = "f" * 40
    elif fault == "git-blob":
        context["source"]["files"][0][1] = "f" * 64
    elif fault == "foreign-head":
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda command, **kwargs: subprocess.CompletedProcess(command, 1),
        )
    else:
        external["index_sha256_before"] = "f" * 64
    with pytest.raises(ValueError):
        observe._producer_source(
            tmp_path, tmp_path / "artifacts/producer/products", context, result, before
        )


def external_products(root: Path, *, existing_products: bool = False) -> Path:
    parent = root / "artifacts/producer"
    products = parent / "products"
    if not existing_products:
        products.mkdir(parents=True)
        for name in ("execution-context.json", "result.json", "certificates.json"):
            (products / name).write_bytes(b"{}")
    for name in ("stdout.log", "stderr-time.log"):
        (parent / name).write_bytes(b"native completion control")
    context = {
        "whole_process_limit_seconds": 180,
        "original_integration_work_seconds": 160,
        "peak_rss_posthoc_maximum_bytes": 805306368,
        "all_output_maximum_bytes": 5000000,
    }
    (parent / "supervision-context.json").write_text(json.dumps(context))
    terminal = {
        "returncode": 0,
        "timed_out": False,
        "source_head_and_index_unchanged": True,
        "process_cap_pass": True,
        "rss_cap_pass": True,
        "output_cap_pass": True,
        "elapsed_seconds": 70,
        "peak_rss_bytes": 205733888,
        "all_output_bytes": 0,
    }
    path = parent / "supervision-terminal.json"
    for _ in range(4):
        path.write_text(json.dumps(terminal))
        terminal["all_output_bytes"] = sum(
            p.stat().st_size for p in parent.rglob("*") if p.is_file()
        )
    path.write_text(json.dumps(terminal))
    return products


def test_external_receipts_bind_complete_output_and_original_caps(
    tmp_path: Path,
) -> None:
    products = external_products(tmp_path)
    context, terminal, pins = observe._external_receipts(tmp_path, products)
    assert context["original_integration_work_seconds"] == 160
    assert terminal["returncode"] == 0
    assert len(pins) == 4
    (products.parent / "stdout.log").write_bytes(b"changed native stdout")
    with pytest.raises(ValueError, match="external resource receipt"):
        observe._external_receipts(tmp_path, products)


def test_external_receipts_refuse_extra_or_symbolic_members(tmp_path: Path) -> None:
    products = external_products(tmp_path)
    (products.parent / "foreign.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="members differ"):
        observe._external_receipts(tmp_path, products)
    (products.parent / "foreign.json").unlink()
    (products.parent / "foreign.json").symlink_to(products / "result.json")
    with pytest.raises(ValueError, match="output tree"):
        observe._external_receipts(tmp_path, products)


def test_observer_terminal_rechecks_same_length_external_log_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_population: MomentPopulation,
) -> None:
    protocol = configure(tmp_path, monkeypatch, synthetic_population)
    producer = tmp_path / "artifacts/producer/products"
    study.run_study(tmp_path, protocol, producer)
    external_products(tmp_path, existing_products=True)
    pins = observe._external_receipts(tmp_path, producer)[2]
    monkeypatch.setattr(
        observe, "_producer_source", lambda *args: {"external_receipts": pins}
    )
    original = verify_angle_certificate
    changed = False

    def tamper(*args: Any) -> dict[str, Any]:
        nonlocal changed
        if not changed:
            log = producer.parent / "stdout.log"
            body = log.read_bytes()
            log.write_bytes(b"X" + body[1:])
            changed = True
        return original(*args)

    monkeypatch.setattr(observe, "verify_angle_certificate", tamper)
    output = tmp_path / "artifacts/observer"
    with pytest.raises(ValueError, match="external receipts changed during replay"):
        observe.run_observer(tmp_path, protocol, producer, output)
    assert changed
    failed = json.loads((output / "independent-check.json").read_bytes())
    assert failed["status"] == "failed"
    assert failed["complete_cases"] == 6
