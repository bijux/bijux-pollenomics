"""Canonical API usage, complete refused mass and example boundary regressions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.spatial import fit_spatial_model
from bijux_pollenomics.analysis.lra_validation.spatial.uncertainty import workflow
from bijux_pollenomics_dev.lra_validation.predictive_uncertainty import example

FIXTURE = Path(__file__).parents[1] / "fixtures/predictive_uncertainty/paired-law.json"


def prepare(tmp_path: Path, change: str | None = None) -> tuple[Path, str]:
    law = json.loads(FIXTURE.read_bytes())
    if change == "draw-order":
        law["atoms"].reverse()
    elif change == "taxon-order":
        law["taxa"].reverse()
    elif change == "paired-shape":
        law["atoms"][1]["ppe"] = [1]
    elif change == "target-label":
        law["target_pollen"] = {"a": 1, "b": 2}
    elif change == "target-alias":
        law["records"][0]["identity_keys"] = ["p10-alias"]
    elif change == "mass-bool":
        law["atoms"][0]["mass"]["numerator"] = True
    elif change == "incomplete-mass":
        law["atoms"][0]["mass"]["denominator"] = 4
    elif change == "unclosed-training":
        law["atoms"][1]["training_compositions"]["r1"]["a"] = 0.9
    path = tmp_path / "law.json"
    body = (json.dumps(law, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(body)
    return path, hashlib.sha256(body).hexdigest()


def test_canonical_usage_preserves_complete_and_unavailable_populations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    law, digest = prepare(tmp_path)
    original = fit_spatial_model
    calls = []

    def fit(*args: Any, **kwargs: Any) -> Any:
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(workflow, "fit_spatial_model", fit)
    output = tmp_path / "artifacts/usage"
    summary = example.run_example(
        repository=tmp_path, law_path=law, expected_sha256=digest, output=output
    )
    complete = json.loads((output / "complete.json").read_bytes())
    mixed = json.loads((output / "mixed-refusal.json").read_bytes())
    refused = json.loads((output / "all-unavailable.json").read_bytes())
    assert len(calls) == 3
    assert [r["draw_id"] for r in complete["rows"]] == ["d0", "d1"]
    assert complete["summary"]["mean"] == pytest.approx(
        [20 / 27, 7 / 27, 52 / 81, 29 / 81]
    )
    assert complete["summary"]["intervals"] is None
    for row in complete["rows"]:
        assert row["identifiability"]["unpenalized_rank"] == 1
        assert row["identifiability"]["ridge_augmented_rank"] == 2
    assert mixed["summary"]["successful_mass"] == {"numerator": 1, "denominator": 3}
    assert mixed["summary"]["failed_mass"] == {"numerator": 2, "denominator": 3}
    assert refused["summary"]["failed_mass"] == {"numerator": 1, "denominator": 1}
    for result in (mixed, refused):
        assert result["summary"]["mean"] is None
        assert result["summary"]["population_covariance"] is None
    for row in refused["rows"]:
        assert not row["spatial_fit_attempted"] and not row["forward_attempted"]
        assert row["upstream"]["source_row"]["reason_code"] == "missing_role_in_bin"
    for result in (complete, mixed, refused):
        assert result["outcome_accesses"] == []
        assert (
            not result["law_authenticity_verified"]
            and not result["empirical_coverage_verified"]
        )
        assert result["law_evidence_sha256"] == digest
        assert result["fold"]["test_record_ids"] == [
            "p10",
            "p10-alias",
        ]
    assert summary["law_sha256"] == digest
    assert not summary["field_coverage_verified"]


@pytest.mark.parametrize(
    "change",
    [
        "draw-order",
        "taxon-order",
        "paired-shape",
        "target-label",
        "target-alias",
        "mass-bool",
        "incomplete-mass",
        "unclosed-training",
    ],
)
def test_invalid_example_is_refused_before_any_fit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    law, digest = prepare(tmp_path, change)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Invalid input reached numerical fitting")

    monkeypatch.setattr(workflow, "fit_spatial_model", forbidden)
    output = tmp_path / "artifacts/refused"
    with pytest.raises(ValueError):
        example.run_example(
            repository=tmp_path, law_path=law, expected_sha256=digest, output=output
        )
    assert not output.exists()


def test_changed_source_identity_refuses_before_decoding(tmp_path: Path) -> None:
    law, digest = prepare(tmp_path)
    law.write_bytes(law.read_bytes() + b" ")
    with pytest.raises(ValueError, match="SHA-256"):
        example.run_example(
            repository=tmp_path,
            law_path=law,
            expected_sha256=digest,
            output=tmp_path / "artifacts/unused",
        )


def test_output_must_be_absent_and_confined(tmp_path: Path) -> None:
    law, digest = prepare(tmp_path)
    for output in (tmp_path / "outside", tmp_path / "artifacts/../outside"):
        with pytest.raises(ValueError):
            example.run_example(
                repository=tmp_path, law_path=law, expected_sha256=digest, output=output
            )
    output = tmp_path / "artifacts/existing"
    output.mkdir(parents=True)
    with pytest.raises(ValueError, match="absent artifacts"):
        example.run_example(
            repository=tmp_path, law_path=law, expected_sha256=digest, output=output
        )


def test_symlinked_law_refuses(tmp_path: Path) -> None:
    law, digest = prepare(tmp_path)
    link = tmp_path / "linked-law.json"
    link.symlink_to(law)
    with pytest.raises(ValueError, match="nonsymlinked"):
        example.run_example(
            repository=tmp_path,
            law_path=link,
            expected_sha256=digest,
            output=tmp_path / "artifacts/unused",
        )
