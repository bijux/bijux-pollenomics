"""Miniature custody, coefficient-law and mixed-disposition controls."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import (
    counting_uncertainty as counting,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.counting_uncertainty import (
    CONTRACT_SHA256,
    NATIVE_EPOCH,
    PROFILE,
    coefficients,
    evaluate,
    saved_cases,
)
from bijux_pollenomics_lra.models.errors import ValidationError


def miniature(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Eight complete artificial cache ledgers; no source data or engine call."""

    def put(path: Path, data: object) -> dict[str, Any]:
        raw = data.encode() if isinstance(data, str) else json.dumps(data).encode()
        path.write_bytes(raw)
        return {
            "path": str(path),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }

    declared, evidence, prior = [], [], []
    for index in range(8):
        directory = root / str(index)
        directory.mkdir()
        identity = {
            "case": index,
            "fractions": {
                "Betula": "-0.3333333333333333",
                "Ulmus": "1.3333333333333333",
            },
        }
        sample = {"counts": [1, 7], "sample_id": str(index), "site_id": "site"}
        parameters = [{"taxon": "Betula", "ppe": 2}, {"taxon": "Ulmus", "ppe": 1}]
        ring = {"mean_m": 750}
        request = {
            "taxa": ["Betula", "Ulmus"],
            "parameters": parameters,
            "local": {"samples": [sample], "basin": {"kind": "lake"}},
            "regional": {"samples": [sample], "basin": {"kind": "lake"}},
            "rings": [ring],
            "configuration": {
                "love": {
                    "stochastic": False,
                    "max_ring": 2,
                    "distance_weighting": "sum",
                },
                "reveals": {"stochastic": False},
            },
        }
        bodies = {
            "request.json": request,
            "numerical/local_love/aux_Kloc.csv": "index,Betula,Ulmus\n250,1,3\n750,1,3\n",
            "numerical/local_love/aux_Kreg.csv": "index,Betula,Ulmus\n250,2,4\n750,2,4\n",
            "numerical/local_love/cover_mean.csv": "index,Betula,Ulmus\n250,-0.3333333333333333,1.3333333333333333\n750,-0.3333333333333333,1.3333333333333333\n",
            "numerical/local_love/aux_valid_ring.csv": "index,value\n250,True\n750,True\n",
            "numerical/local_love/run_manifest.json": {
                "parameters": {
                    "stochastic": False,
                    "paired_regional_cover_draws": True,
                    "paired_local_count_draws": False,
                    "paired_local_ppe_draws": False,
                }
            },
            "numerical/regional_reveals/reconstruction.csv": "Betula.mean,Betula.sd,Betula.q10,Betula.q90,Betula.median,Ulmus.mean,Ulmus.sd,Ulmus.q10,Ulmus.q90,Ulmus.median\n50,0,50,50,50,50,0,50,50,50\n",
        }
        members = {
            name: put(directory / (str(i) + ".data"), data)
            for i, (name, data) in enumerate(bodies.items())
        }
        manifest = put(
            directory / "manifest.json",
            {
                "files": {name: row["sha256"] for name, row in members.items()},
                "scientific_identity": {"engine_files": {"equation.py": "1" * 64}},
            },
        )
        declared.append(
            {"identity": identity, "manifest": manifest, "members": members}
        )
        evidence.append(identity)
        prior.append(
            {
                "identity": identity,
                "fixed_context": {
                    "local_sample": sample,
                    "regional_sample": sample,
                    "local_basin": {"kind": "lake"},
                    "regional_basin": {"kind": "lake"},
                    "parameters": parameters,
                    "selected_ring": ring,
                    "distance_weighting": "sum",
                    "regional_cover_percent": {"Betula": "50", "Ulmus": "50"},
                },
                "diagnostic": {
                    "conditional_nonnegative_cover_exists": False,
                    "denominator_D": {"numerator": "2", "denominator": "1"},
                },
            }
        )
    contract = {
        "schema_version": "nordic-coupled-composition-admissibility-inputs.v1",
        "cases": declared,
        "original_finding": put(
            root / "finding.json", {"candidate": NATIVE_EPOCH, "evidence": evidence}
        ),
        "original_batch": put(root / "batch.json", {"execution_epoch": NATIVE_EPOCH}),
        "source_pins": [{"engine_member": "equation.py", "sha256": "1" * 64}],
    }
    previous = {
        "schema_version": "nordic-coupled-composition-admissibility.v1",
        "input_contract_sha256": CONTRACT_SHA256,
        "original_native_epoch": NATIVE_EPOCH,
        "cases": prior,
    }
    return contract, previous


def fake_result(
    counts: list[int], a: list[float], b: list[float], *, empty: bool = False
) -> dict[str, Any]:
    return {
        "profile": PROFILE,
        "confidence_level": 0.95,
        "counts": counts,
        "total_count": sum(counts),
        "local_coefficients": a,
        "regional_deposition": b,
        "status": "empty" if empty else "nonempty",
        "cover_lower": None if empty else (0.0, 0.0),
        "cover_upper": None if empty else (1.0, 1.0),
        "point_cover": (0.0, 1.0),
        "pollen_probability_interval": (0.0, 1.0),
        "feasible_pollen_probability_bounds": ("0", "1"),
        "tail_target_lower_bound": "0.025",
        "pollen_tail_upper_bounds": (None, None),
        "bound_search_evaluations": (0, 0),
    }


def test_reopens_all_eight_miniature_caches_without_evaluation(tmp_path: Path) -> None:
    contract, prior = miniature(tmp_path)
    cases = saved_cases(contract, prior)
    assert len(cases) == 8
    assert [row["identity"]["case"] for row in cases] == list(range(8))


def test_common_denominator_matches_an_independent_raw_pollen_law(
    tmp_path: Path,
) -> None:
    contract, prior = miniature(tmp_path)
    case = saved_cases(contract, prior)[0]
    case["local_sample"] = {"counts": [2, 3]}
    counts, a, b, _ = coefficients(case)
    assert counts == [2, 3] and a == [4.0, 2.0] and b == [2.0, 2.0]
    # n/PPE=(1,3), D=2 and regional terms=(1,2) imply v1=1/8.
    # Forward raw pollen is (4v+2)/(2v+6), which equals observed 2/5.
    v = Fraction(1, 8)
    assert (4 * v + 2) / (2 * v + 6) == Fraction(2, 5)
    assert a != [2.0, 3.0]  # PPE*Kloc would implement a different law.


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "membership",
        "context",
        "member-bytes",
        "axis",
        "equation",
    ],
)
def test_incomplete_or_foreign_saved_inputs_refuse(tmp_path: Path, change: str) -> None:
    contract, prior = miniature(tmp_path)
    if change == "missing":
        contract["cases"].pop()
    elif change == "duplicate":
        contract["cases"][1] = deepcopy(contract["cases"][0])
    elif change == "membership":
        del contract["cases"][0]["members"]["request.json"]
    elif change == "context":
        prior["cases"][0]["fixed_context"]["local_sample"] = {"counts": [9, 9]}
    elif change == "member-bytes":
        Path(contract["cases"][0]["members"]["request.json"]["path"]).write_bytes(b"{}")
    elif change == "equation":
        contract["source_pins"][0]["sha256"] = "2" * 64
    else:
        first = contract["cases"][0]
        request_pin = first["members"]["request.json"]
        request_path = Path(request_pin["path"])
        request = json.loads(request_path.read_bytes())
        request["taxa"].reverse()
        raw = json.dumps(request).encode()
        request_path.write_bytes(raw)
        request_pin.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        manifest_path = Path(first["manifest"]["path"])
        manifest = json.loads(manifest_path.read_bytes())
        manifest["files"]["request.json"] = request_pin["sha256"]
        raw = json.dumps(manifest).encode()
        manifest_path.write_bytes(raw)
        first["manifest"].update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    with pytest.raises(ValueError):
        saved_cases(contract, prior)


def test_mixed_empty_nonempty_and_typed_refusal_are_all_retained(
    tmp_path: Path,
) -> None:
    contract, prior = miniature(tmp_path)
    cases = saved_cases(contract, prior)
    calls = 0

    def evaluator(n: list[int], a: list[float], b: list[float]) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise ValidationError(
                "bounded tail refusal", reason_code="counting_interval_certification"
            )
        return fake_result(n, a, b, empty=calls == 2)

    rows = evaluate(cases, evaluator)
    assert calls == len(rows) == 8
    assert rows[0]["confidence_set"]["status"] == "nonempty"
    assert rows[1]["confidence_set"]["status"] == "empty"
    assert rows[1]["confidence_set"]["cover_lower"] is None
    assert rows[2]["status"] == "refused" and rows[2]["confidence_set"] is None
    assert all(row["original_refusal_preserved"] is True for row in rows)


@pytest.mark.parametrize("unknown_reason", [False, True])
def test_unknown_failure_keeps_fatal_and_all_later_not_run_rows(
    tmp_path: Path, unknown_reason: bool
) -> None:
    contract, prior = miniature(tmp_path)

    def evaluator(n: list[int], a: list[float], b: list[float]) -> dict[str, Any]:
        if unknown_reason:
            raise ValidationError("new unknown failure", reason_code="foreign_failure")
        raise RuntimeError("implementation failure")

    rows = evaluate(saved_cases(contract, prior), evaluator)
    assert [row["status"] for row in rows] == ["fatal", *["not_run"] * 7]


@pytest.mark.parametrize("counts", [[True, 3], [0, 0], [10001, 1], [2.5, 3], [2, 3, 4]])
def test_counts_are_the_bounded_integer_restricted_panel(
    tmp_path: Path, counts: list[Any]
) -> None:
    contract, prior = miniature(tmp_path)
    case = saved_cases(contract, prior)[0]
    case["local_sample"] = {"counts": counts}
    with pytest.raises(ValueError, match="integer two-taxon"):
        coefficients(case)


@pytest.mark.parametrize("presentation", ("absent", "changed"))
def test_cli_uses_scientific_inputs_independently_of_presentation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, presentation: str
) -> None:
    contract, prior = miniature(tmp_path)
    contract["repository"] = str(tmp_path)
    contract_raw = json.dumps(contract).encode()
    contract_path = tmp_path / "contract.json"
    contract_path.write_bytes(contract_raw)
    contract_sha = hashlib.sha256(contract_raw).hexdigest()
    monkeypatch.setattr(counting, "CONTRACT_SHA256", contract_sha)
    prior["input_contract_sha256"] = contract_sha
    prior_raw = json.dumps(prior).encode()
    prior_path = tmp_path / "prior.json"
    prior_path.write_bytes(prior_raw)
    prior_sha = hashlib.sha256(prior_raw).hexdigest()
    monkeypatch.setattr(counting, "PRIOR_SHA256", prior_sha)
    protocol = {
        "schema_version": "nordic-love-conditional-counting.v1",
        "profile": PROFILE,
        "alpha": 0.05,
        "confidence_level": 0.95,
        "cases": 8,
        "taxa": ["Betula", "Ulmus"],
        "input_pins": {
            "cache_contract": {
                "path": "contract.json",
                "sha256": contract_sha,
                "bytes": len(contract_raw),
            },
            "prior_admissibility": {
                "path": "prior.json",
                "sha256": prior_sha,
                "bytes": len(prior_raw),
            },
        },
        "conditioning": {},
        "interpretation_limits": [],
    }
    protocol_raw = json.dumps(protocol).encode()
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_bytes(protocol_raw)
    presentation_path = (
        tmp_path
        / "reports/science/pollen-reconstruction/nordic-coupled-workflow/admissibility-publication.json"
    )
    if presentation == "changed":
        presentation_path.parent.mkdir(parents=True)
        presentation_path.write_text('{"public_reader": {"sha256": "changed"}}')
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    output = artifacts / "result.json"
    argv = [
        "counting_uncertainty.py",
        "--repository",
        str(tmp_path),
        "--protocol",
        str(protocol_path),
        "--protocol-sha256",
        hashlib.sha256(protocol_raw).hexdigest(),
        "--execution-epoch",
        "a" * 40,
        "--output",
        str(output),
    ]
    monkeypatch.setattr("sys.argv", argv)
    called: list[int] = []

    def miniature_evaluation(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        called.extend(row["identity"]["case"] for row in cases)
        return evaluate(cases, evaluator=fake_result)

    monkeypatch.setattr(counting, "evaluate", miniature_evaluation)
    with pytest.raises(SystemExit) as completed:
        counting.main()
    assert completed.value.code == 0
    assert called == list(range(8))
    result = json.loads(output.read_bytes())
    assert set(result["input_pins"]) == {"cache_contract", "prior_admissibility"}
    assert len(result["cases"]) == 8
    assert result["status_counts"] == {"computed": 8}
    prior_path.write_bytes(prior_raw.replace(b'"cases"', b'"caSes"', 1))
    with pytest.raises(ValueError, match="Input buffer identity differs"):
        counting.main()
    assert called == list(range(8))
