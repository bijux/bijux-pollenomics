"""Bounded shared-asset joins and complete conditional counting dispositions."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import (
    regional_counting_uncertainty as adapter,
)
from bijux_pollenomics_lra.models.errors import ValidationError


def miniature(
    root: Path, monkeypatch: pytest.MonkeyPatch, defect: str = ""
) -> tuple[Path, Path]:
    """Create tiny artificial source assets; never copy datasets or source trees."""
    repository = root / "repository"
    archive = root / "archive"

    def put(value: object) -> dict[str, Any]:
        raw = value.encode() if isinstance(value, str) else json.dumps(value).encode()
        digest = hashlib.sha256(raw).hexdigest()
        path = archive / "objects" / digest[:2] / digest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {"sha256": digest, "bytes": len(raw), "path": "/retired/never-read"}

    old, declarations = [], []
    for index in range(8):
        identity: dict[str, Any] = {
            "case": index,
            "fractions": {"Betula": "-0.25", "Ulmus": "1.25"},
        }
        context: dict[str, Any] = {
            "local_sample": {"counts": [2, 3], "sample_id": f"local-{index}"},
            "regional_sample": {"counts": [4, 6], "sample_id": f"regional-{index}"},
            "local_basin": {"diameter_m": 100},
            "regional_basin": {"diameter_m": 200},
            "parameters": [{"taxon": "Betula", "ppe": 2}, {"taxon": "Ulmus", "ppe": 1}],
            "selected_ring": {"mean_m": 750},
            "distance_weighting": "gpm neutral",
        }
        request: dict[str, Any] = {
            "taxa": list(adapter.TAXA),
            "pollen_unit": "count",
            "operation": "lra",
            "data_kind": "source_observations",
            "method_profile": "fixture",
            "parameters": context["parameters"],
            "rings": [context["selected_ring"]],
            "local": {
                "samples": [deepcopy(context["local_sample"])],
                "basin": context["local_basin"],
            },
            "regional": {
                "samples": [context["regional_sample"]],
                "basin": context["regional_basin"],
            },
            "configuration": {
                "love": {"method": "analytical", "stochastic": False},
                "reveals": {"stochastic": False},
            },
        }
        if defect == "sample":
            request["local"]["samples"][0]["sample_id"] = "unbound"
        if defect == "count":
            context["regional_sample"]["counts"] = [True, 3]
        if defect == "signed":
            identity["fractions"]["Betula"] = "0.25"
        if defect == "ppe":
            context["parameters"][0]["ppe"] = 0
        members = {
            "request.json": put(request),
            "numerical/local_love/aux_Kloc.csv": put(
                "index,Betula,Ulmus\n250,1,2\n750,1,2\n"
            ),
            "numerical/local_love/aux_Kreg.csv": put(
                "index,Betula,Ulmus\n250,2,3\n750,2,3\n"
            ),
            "numerical/local_love/cover_mean.csv": put(
                "index,Betula,Ulmus\n250,-0.25,1.25\n750,-0.25,1.25\n"
            ),
        }
        response = (
            "index,K\nBetula,1\nUlmus,2\n"
            if defect != "axis"
            else "index,K\nUlmus,1\nBetula,2\n"
        )
        extra = {
            "numerical/regional_reveals/deposition_factors.csv": put(response),
            "numerical/regional_reveals/result_contract.json": put(
                {"units": {"cover": "percent", "distance": "metre"}}
            ),
            "numerical/regional_reveals/run_manifest.json": put(
                {
                    "algorithm": "REVEALS",
                    "parameters": {
                        "stochastic": False,
                        "basin_diameter_m": 200,
                        "distance_weighting": "gpm neutral",
                    },
                }
            ),
        }
        manifest: dict[str, Any] = {
            "files": {name: pin["sha256"] for name, pin in (members | extra).items()},
            "retained_taxa": list(adapter.TAXA),
            "method_profile": "fixture",
            "scientific_identity": {"request_sha256": "a" * 64},
            "units": {
                "distance": "metre",
                "local_cover": "fraction",
                "regional_cover": "percent",
            },
        }
        if defect == "units":
            manifest["units"]["distance"] = "kilometre"
        if defect == "member":
            manifest["files"]["numerical/local_love/aux_Kloc.csv"] = extra[
                "numerical/regional_reveals/deposition_factors.csv"
            ]["sha256"]
        pin = put(manifest)
        declarations.append({"identity": identity, "manifest": pin, "members": members})
        old.append(
            {
                "identity": identity,
                "cache_manifest": pin,
                "member_pins": members,
                "original_refusal_preserved": True,
                "status": "computed",
                "fixed_context": context,
                "confidence_set": {"status": "nonempty" if index < 3 else "empty"},
            }
        )
    if defect == "duplicate":
        old[1]["identity"] = old[0]["identity"]
    contract = put(
        {
            "schema_version": "nordic-coupled-composition-admissibility-inputs.v1",
            "cases": declarations,
        }
    )
    previous = {
        "schema_version": "nordic-love-conditional-counting-result.v1",
        "original_native_epoch": adapter.NATIVE_EPOCH,
        "confidence_level": 0.95,
        "original_prediction_native_exit": 1,
        "original_failed_folds": 8,
        "original_dependent_method_refusals": 24,
        "confidence_set_counts": {"nonempty": 3, "empty": 5},
        "cases": old,
    }
    raw = json.dumps(previous).encode()
    path = repository / adapter.FIXED_RESULT
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    monkeypatch.setattr(adapter, "FIXED_SHA256", hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(adapter, "CONTRACT_SHA256", contract["sha256"])
    return repository, archive


def value(case: dict[str, Any]) -> dict[str, Any]:
    image = {"status": "nonempty", "cover_lower": [0, 0], "cover_upper": [1, 1]}
    return {
        "profile": adapter.PROFILE,
        "confidence_level": 0.95,
        "local_counting": {"counts": case["local_counts"], "confidence_level": 0.975},
        "regional_counting": {
            "counts": case["regional_counts"],
            "confidence_level": 0.975,
        },
        "marginal_confidence_level": 0.975,
        "guaranteed_joint_confidence_lower_bound": "19/20",
        **{
            key: case[key]
            for key in ("local_kernel", "regional_kernel", "regional_deposition", "ppe")
        },
        "regional_point_cover_exact": ["1/2", "1/2"],
        "image": image,
        "fixed_regional_control": {
            "regional_cover_exact": ["1/2", "1/2"],
            "local_confidence_level": 0.975,
            "image": deepcopy(image),
        },
    }


def test_exact_member_join_never_reads_retired_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, archive = miniature(tmp_path, monkeypatch)
    cases = adapter.load_cases(repository, archive)
    assert len(cases) == 8
    assert cases[0]["regional_counts"] == [4, 6]
    assert cases[0]["local_kernel"] == [1, 2]
    assert cases[0]["regional_kernel"] == [2, 3]
    assert cases[0]["regional_deposition"] == [1, 2]
    assert (
        cases[0]["original_scientific_request_sha256"]
        != cases[0]["original_member_sha256"]["request.json"]
    )
    assert cases[0]["signed_historical_cover"] == {"Betula": "-0.25", "Ulmus": "1.25"}
    rows = adapter.evaluate(cases, value)
    assert [row["status"] for row in rows] == ["computed"] * 8
    assert [row["previous_fixed_background_classification"] for row in rows] == [
        "nonempty"
    ] * 3 + ["empty"] * 5


@pytest.mark.parametrize(
    "defect",
    ["sample", "count", "signed", "ppe", "axis", "units", "member", "duplicate"],
)
def test_source_join_refuses_wrong_meaning_even_when_fixture_bytes_are_authenticated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    repository, archive = miniature(tmp_path, monkeypatch, defect)
    with pytest.raises(ValueError):
        adapter.load_cases(repository, archive)


@pytest.mark.parametrize("defect", ["bytes", "missing", "escape"])
def test_shared_raw_asset_integrity_is_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    repository, archive = miniature(tmp_path, monkeypatch)
    path = archive / "objects" / adapter.CONTRACT_SHA256[:2] / adapter.CONTRACT_SHA256
    if defect == "bytes":
        path.write_bytes(b"Changed raw asset")
    elif defect == "missing":
        path.unlink()
    else:
        outside = tmp_path / "outside"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
    with pytest.raises(ValueError):
        adapter.load_cases(repository, archive)


def test_known_refusal_does_not_drop_other_requests_and_fatal_stops_later_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, archive = miniature(tmp_path, monkeypatch)
    cases = adapter.load_cases(repository, archive)

    def mixed(case: dict[str, Any]) -> dict[str, Any]:
        index = case["identity"]["case"]
        if index == 1:
            raise ValidationError(
                "Certification refused", reason_code="counting_interval_certification"
            )
        if index == 3:
            raise RuntimeError("Unexpected numerical failure")
        return value(case)

    rows = adapter.evaluate(cases, mixed)
    assert [row["status"] for row in rows] == [
        "computed",
        "refused",
        "computed",
        "fatal",
        *["not_run"] * 4,
    ]
    assert all(
        row["signed_historical_cover"] == cases[index]["signed_historical_cover"]
        for index, row in enumerate(rows)
    )


@pytest.mark.parametrize("defect", ["confidence", "counts", "image", "control"])
def test_adapter_refuses_misbound_numerical_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    repository, archive = miniature(tmp_path, monkeypatch)
    cases = adapter.load_cases(repository, archive)

    def corrupted(case: dict[str, Any]) -> dict[str, Any]:
        result = value(case)
        if defect == "confidence":
            result["guaranteed_joint_confidence_lower_bound"] = "9/10"
        elif defect == "counts":
            result["regional_counting"]["counts"] = [1, 1]
        elif defect == "image":
            result["image"]["status"] = "empty"
        else:
            result["fixed_regional_control"]["local_confidence_level"] = 0.95
        return result

    rows = adapter.evaluate(cases, corrupted)
    assert [row["status"] for row in rows] == ["fatal", *["not_run"] * 7]


def test_maintained_api_and_matched_control_accept_a_tiny_artificial_panel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, archive = miniature(tmp_path, monkeypatch)
    cases = adapter.load_cases(repository, archive)
    result = adapter.maintained(cases[0])
    assert result["profile"] == adapter.PROFILE
    assert result["local_counting"]["counts"] == (2, 3)
    assert result["regional_counting"]["counts"] == (4, 6)
    assert (
        result["fixed_regional_control"]["local_confidence_level"]
        == result["marginal_confidence_level"]
    )
    assert adapter.evaluate(cases, lambda _: result)[0]["status"] == "computed"


def test_empty_joint_image_keeps_null_bounds_and_the_matched_control(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, archive = miniature(tmp_path, monkeypatch)
    cases = adapter.load_cases(repository, archive)

    def empty(case: dict[str, Any]) -> dict[str, Any]:
        result = value(case)
        result["image"] = {"status": "empty", "cover_lower": None, "cover_upper": None}
        return result

    rows = adapter.evaluate(cases, empty)
    assert all(
        row["status"] == "computed"
        and row["confidence_set"]["image"]["cover_lower"] is None
        for row in rows
    )
    assert all(
        row["confidence_set"]["fixed_regional_control"]["image"]["status"] == "nonempty"
        for row in rows
    )


@pytest.mark.parametrize("defect", ["dirty", "untracked", "origin"])
def test_source_revision_requires_clean_tracked_canonical_consumed_modules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    from bijux_pollenomics_lra.reconstruction.uncertainty import (
        homogeneous_counting,
        regional_counting,
        two_taxon_counting,
    )

    prefix = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/uncertainty"
    modules = [
        (regional_counting, f"{prefix}/regional_counting.py"),
        (homogeneous_counting, f"{prefix}/homogeneous_counting.py"),
        (two_taxon_counting, f"{prefix}/two_taxon_counting.py"),
        (
            adapter,
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/nordic_coupled/regional_counting_uncertainty.py",
        ),
    ]
    for module, relative in modules:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# Synthetic revision fixture, not executable scientific source\n"
        )
        monkeypatch.setattr(module, "__file__", str(path))
    for arguments in (
        ["init", "--quiet"],
        ["add", "--", "packages"],
        [
            "-c",
            "user.name=Bijux",
            "-c",
            "user.email=checks@bijux.io",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--quiet",
            "-m",
            "test(science): bind synthetic source revision",
        ],
    ):
        subprocess.run(
            ["git", "-C", str(tmp_path), *arguments], check=True, capture_output=True
        )
    revision = adapter._revision(tmp_path)
    assert len(revision) == 40
    path = tmp_path / modules[0][1]
    if defect == "dirty":
        path.write_text("# Changed consumed fixture\n")
    elif defect == "untracked":
        subprocess.run(
            ["git", "-C", str(tmp_path), "rm", "--cached", "--", modules[0][1]],
            check=True,
            capture_output=True,
        )
    else:
        foreign = tmp_path / "foreign.py"
        foreign.write_text("# Wrong import origin\n")
        monkeypatch.setattr(regional_counting, "__file__", str(foreign))
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        adapter._revision(tmp_path)
