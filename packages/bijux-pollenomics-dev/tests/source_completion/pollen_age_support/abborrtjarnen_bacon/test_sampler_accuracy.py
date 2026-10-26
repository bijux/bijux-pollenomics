"""Control exact prefix identity and withhold scores on failed qualification."""

from __future__ import annotations

import copy
from dataclasses import replace
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.ci.atlas_media.process_execution import CompletedCommand
from bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarnen_bacon import (
    sampler_accuracy as accuracy,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarnen_bacon import (
    workflow,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarnen_bacon.inputs import (
    CoreInputs,
    read_inputs,
)


def test_literal_prefix_includes_blank_first_and_unterminated_last_line(
    tmp_path: Path,
) -> None:
    old, new = tmp_path / "old.out", tmp_path / "extended.out"
    original = b"\n1 2 3\n4 5 6"
    old.write_bytes(original)
    new.write_bytes(original + b"\n7 8 9")
    result = accuracy.compare_prefix(old, new)
    assert result["matched"] is True
    assert result["bytes_compared"] == len(original)
    assert result["native_prefix_sha256"] == hashlib.sha256(original).hexdigest()


@pytest.mark.parametrize(
    "changed", [b"\n1 2 0\n4 5 6\n7", b"\n1 2 3", b"\n1 2 3\n4 5 6X7"]
)
def test_changed_truncated_or_reformatted_prefix_refuses(
    tmp_path: Path, changed: bytes
) -> None:
    old, new = tmp_path / "old.out", tmp_path / "extended.out"
    old.write_bytes(b"\n1 2 3\n4 5 6")
    new.write_bytes(changed)
    assert accuracy.compare_prefix(old, new)["matched"] is False


def test_prepared_accuracy_case_reuses_original_target_and_existing_binary() -> None:
    repository = Path(__file__).resolve().parents[6]
    if not (
        repository / "artifacts/physical-core/abborrtjarnen-fixed-iteration"
    ).is_dir():
        pytest.skip("The original failed native prefixes are not installed")
    original = read_inputs(repository, repository.parent / "-bijux-pollenomics-data")
    library = repository / "artifacts/qualification/native-reference/library"
    case, protocol = accuracy.prepare_case(repository, library, original)
    assert case.protocol["model"] == original.protocol["model"]
    assert case.protocol["diagnostics"] == original.protocol["diagnostics"]
    assert case.protocol["source_inputs"] == original.protocol["source_inputs"]
    assert case.protocol["execution"]["requested_ssize_per_chain"] == 16000
    assert case.counts is original.counts and case.predictions is original.predictions
    assert protocol["resources"]["max_output_bytes"] == 100000000
    changed = copy.deepcopy(original.protocol)
    changed["model"]["acc_shape"] = 2.0
    with pytest.raises(ValueError, match="target-law"):
        accuracy.prepare_case(repository, library, replace(original, protocol=changed))


@pytest.mark.parametrize(
    "failed_gate",
    ["prefix", "diagnostics", "elapsed", "memory", "final_output", "seed_axis", None],
)
def test_scores_wait_for_both_prefixes_and_all_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failed_gate: str | None
) -> None:
    (tmp_path / "artifacts").mkdir()
    library = tmp_path / "library"
    curves = library / "rintcal/extdata"
    curves.mkdir(parents=True)
    for name in ("3Col_intcal20.14C", "intcal20.14c"):
        (curves / name).write_bytes(b"controlled-curve")
    digest = hashlib.sha256(b"controlled-curve").hexdigest()
    monkeypatch.setattr(workflow, "CURVE_SHA256", digest)
    monkeypatch.setattr(workflow, "FULL_CURVE_SHA256", digest)
    monkeypatch.setattr(workflow, "_revision", lambda repository: "controlled-commit")
    names = tuple(f"sample-{i}" for i in range(107))
    case = CoreInputs(
        {
            "execution": {
                "seeds": [314159, 271828],
                "requested_ssize_per_chain": 16000,
            },
            "source_inputs": {},
        },
        (),
        names,
        np.arange(107, dtype=float),
        np.ones((107, 16), dtype=np.int64),
        np.full((4, 4, 16), 1 / 16),
        [],
    )
    qualification = {
        "original_directory": "artifacts/old-native",
        "original_failed_source_commit": "old-commit",
        "original_failed_status": "refused_mcmc_diagnostics",
    }
    monkeypatch.setattr(workflow, "read_inputs", lambda repository, source_root: case)
    monkeypatch.setattr(
        workflow,
        "prepare_case",
        lambda repository, library, source: (source, qualification),
    )
    events: list[str] = []

    def prefixes(*args: Any) -> list[dict[str, Any]]:
        events.append("both_prefixes_checked")
        return [
            {"seed": seed, "matched": failed_gate != "prefix"}
            for seed in (314159, 271828)
        ]

    monkeypatch.setattr(workflow, "prefix_checks", prefixes)
    ages = np.broadcast_to(np.arange(107, dtype=float), (16000, 107))
    monkeypatch.setattr(workflow, "physical_ages", lambda *args: ages)

    def load(path: Any, *args: Any, **kwargs: Any) -> Any:
        return ages if kwargs.get("delimiter") == "," else np.ones((19501, 54))

    monkeypatch.setattr(np, "loadtxt", load)

    def execute(
        command: tuple[str, ...],
        *,
        cwd: Path,
        timeout_seconds: float,
        max_output_bytes: int,
    ) -> CompletedCommand:
        chains = []
        payload = json.loads((cwd / "core-input.json").read_text())
        assert payload["protocol"]["execution"]["requested_ssize_per_chain"] == 16000
        assert payload["sampler_accuracy"] == qualification
        assert timeout_seconds == 600
        for seed in (314159, 271828):
            root = cwd / f"seed-{seed}"
            (root / "ABBO").mkdir(parents=True)
            native = root / "ABBO/ABBO_51.out"
            native.touch()
            with gzip.open(root / "ages.csv.gz", "wt") as stream:
                stream.write(",".join(names) + "\n")
            chains.append(
                {
                    "seed": seed,
                    "native_output": str(native),
                    "sections": 51,
                    "raw_rows": 19501,
                    "first_native_row": 3502,
                    "last_native_row": 19501,
                    "retained_rows": 16000,
                    "top_depth_cm": 0,
                    "section_thickness_cm": 1,
                }
            )
        if failed_gate == "seed_axis":
            chains[1]["seed"] = 314159
        (cwd / "fit-summary.json").write_text(
            json.dumps(
                {
                    "chains": chains,
                    "age_diagnostics": {"qualified": failed_gate != "diagnostics"},
                    "free_parameter_diagnostics": {"qualified": True},
                }
            )
        )
        return CompletedCommand(
            command,
            0,
            b"controlled native terminal",
            b"1500000001 maximum resident set size\n"
            if failed_gate == "memory"
            else b"1000000 maximum resident set size\n",
            601.0 if failed_gate == "elapsed" else 0.01,
            False,
            "not_required",
        )

    monkeypatch.setattr(workflow, "run_bounded_argv", execute)
    if failed_gate == "final_output":
        byte_counts = [0, 100000001]
        monkeypatch.setattr(
            workflow, "_output_bytes", lambda destination: byte_counts.pop(0)
        )

    def scores(*args: Any) -> tuple[np.ndarray, dict[str, Any], np.ndarray]:
        assert events == ["both_prefixes_checked"]
        assert failed_gate in (None, "final_output")
        return np.zeros((16000, 4)), {}, np.ones((16000, 4, 2), dtype=np.int64)

    monkeypatch.setattr(workflow, "score_draws", scores)
    oracle = tmp_path / "oracle.json"
    oracle.write_text(
        json.dumps(
            {
                "passed": True,
                "source_version": "4.0.2",
                "model_fits": 0,
                "absolute_tolerance": 1e-8,
                "source_support_refusals": 4,
                "fixture_cases": 6,
                "comparison_rows": 64,
                "relative_tolerance": 0,
                "maximum_native_corrected_helper_gap": 0.0,
            }
        )
    )
    output = tmp_path / "artifacts/accuracy"
    if failed_gate == "seed_axis":
        with pytest.raises(ValueError, match="two-seed"):
            workflow.run(
                tmp_path, tmp_path, library, oracle, output, sampler_accuracy=True
            )
        assert not list(output.glob("seed-*/draw-scores.csv.gz"))
        return
    result = workflow.run(
        tmp_path, tmp_path, library, oracle, output, sampler_accuracy=True
    )
    assert result["requested_draws"] == 32000
    assert result["sampler_accuracy_qualification"][
        "score_interpretation_permitted"
    ] is (failed_gate is None)
    assert bool(list(output.glob("seed-*/draw-scores.csv.gz"))) is (
        failed_gate in (None, "final_output")
    )
    assert result["consumer_status"] == (
        "computed_after_sampler_qualification"
        if failed_gate is None
        else "not_run_prefix_qualification"
        if failed_gate == "prefix"
        else "computed_then_refused_final_resources"
        if failed_gate == "final_output"
        else "not_run_sampler_qualification"
    )
    assert ("saved_ensemble_descriptors" in result) is (failed_gate is None)
