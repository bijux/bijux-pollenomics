"""Native timing boundaries and source failure evidence remain explicit."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_dev.ci.atlas_media.process_execution import (
    CompletedCommand,
    run_bounded_argv,
)
from bijux_pollenomics_dev.native_backend.love_comparison import (
    execution,
    inputs,
    worker,
)
from bijux_pollenomics_dev.native_backend.profiling import THREAD_VARIABLES
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.optimization.solver import ReplayOptimizer


def test_first_and_warm_costs_are_not_whole_process_or_incremental_memory() -> None:
    result = execution.timing([4.0, 1.0, 2.0, 3.0, 4.0, 5.0])
    assert result["first_seconds"] == 4
    assert result["warm_median_seconds"] == 3
    assert result["warm_min_seconds"] == 1
    assert result["warm_max_seconds"] == 5
    assert execution.peak_rss("123 maximum resident set size\n", "Darwin") == 123
    assert (
        execution.peak_rss("Maximum resident set size (kbytes): 123\n", "Linux")
        == 123 * 1024
    )


@pytest.mark.parametrize(
    "samples", [[1.0] * 5, [1.0] * 7, [1.0] * 5 + [-1.0], [1.0] * 5 + [float("nan")]]
)
def test_timing_population_or_nonfinite_sample_refuses(samples: list[float]) -> None:
    with pytest.raises(ValueError, match="sample population"):
        execution.timing(samples)


@pytest.mark.parametrize(
    "stderr,system",
    [
        ("", "Darwin"),
        ("1 maximum resident set size\n2 maximum resident set size\n", "Darwin"),
        ("1 maximum resident set size", "Windows"),
    ],
)
def test_ambiguous_or_unavailable_native_rss_refuses(stderr: str, system: str) -> None:
    with pytest.raises(ValueError, match="unavailable or ambiguous"):
        execution.peak_rss(stderr, system)


def test_existing_replay_optimizer_first_min_tie_and_all_invalid_refusal() -> None:
    solver = ReplayOptimizer(np.array([[0.2, 0.8], [0.8, 0.2]]))
    result = solver.solve(lambda _: 1.0)
    np.testing.assert_array_equal(result.x, [0.2, 0.8])
    with pytest.raises(ValidationError, match="Every replay candidate"):
        solver.solve(lambda _: float("nan"))


def fake_tables() -> dict[str, pd.DataFrame]:
    tables = {
        name: pd.DataFrame({"A": [1]})
        for name in ("local", "regional", "ppes", "rings")
    }
    tables["candidates"] = pd.DataFrame(np.linspace(0.1, 0.9, 320).reshape(32, 10))
    return tables


def test_python_worker_retains_all_calls_refusal_and_outputs_before_scoring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tables = fake_tables()
    calls: list[Any] = []
    monkeypatch.setattr(worker, "read", lambda _: tables)

    def consume(*_: object, replay_candidates: np.ndarray, **__: object) -> Any:
        calls.append(replay_candidates.copy())
        if not replay_candidates.any():
            raise ValidationError("Every replay candidate has an undefined objective")
        table = pd.DataFrame(np.ones((10, 10)))
        return SimpleNamespace(
            cover={"mean": table},
            pollen_percentages={"mean": table},
            objective_values=table,
            auxiliary={"K": table},
            diagnostics=[SimpleNamespace(x=replay_candidates[0], nfev=32)] * 8,
        )

    monkeypatch.setattr(worker, "run_love", consume)
    result = worker.run(tmp_path, tmp_path)
    assert len(calls) == 7
    assert len(result["call_seconds"]) == 6
    assert result["mandatory_certifications_per_call"] == 8
    assert result["search_returns_per_call"] == 256
    assert "undefined objective" in result["all_undefined_refusal"]
    assert (tmp_path / "python-k.csv").is_file()


@pytest.mark.parametrize("drift", ["products", "candidate", "budget"])
def test_changed_warm_products_or_trace_cannot_qualify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, drift: str
) -> None:
    tables = fake_tables()
    monkeypatch.setattr(worker, "read", lambda _: tables)
    calls = 0

    def consume(*_: object, replay_candidates: np.ndarray, **__: object) -> Any:
        nonlocal calls
        calls += 1
        table = pd.DataFrame([[2.0 if calls == 2 and drift == "products" else 1.0]])
        index = 1 if calls == 2 and drift == "candidate" else 0
        budget = 31 if calls == 2 and drift == "budget" else 32
        return SimpleNamespace(
            cover={"mean": table},
            pollen_percentages={"mean": table},
            objective_values=table,
            auxiliary={"K": table},
            diagnostics=[SimpleNamespace(x=replay_candidates[index], nfev=budget)] * 8,
        )

    monkeypatch.setattr(worker, "run_love", consume)
    with pytest.raises(ValueError, match="differ"):
        worker.run(tmp_path, tmp_path)


def test_r_wrapper_times_original_expression_without_copying_numerical_source(
    tmp_path: Path,
) -> None:
    entry = tmp_path / "entry.R"
    entry.write_text("""args <- commandArgs(trailingOnly=TRUE)
output <- args[2]
local <- regional <- params <- rings <- NULL
CANDIDATES <- matrix(1)
optimized_all_nonfinite_refusal <- function(...) "refused: all replay candidates invalid"
executions <- 0L
result <- { executions <- executions+1L; REPLAY_TRACE <- as.list(seq_len(8)); list(cover=list(mean=1),pollenpercentages=list(mean=2),mBestValue=3) }
writeLines(as.character(executions),file.path(output,"executions.txt"))
""")
    before = entry.read_bytes()
    script = Path(execution.__file__).with_name("timed_replay.R")
    result = run_bounded_argv(
        (
            "/usr/local/bin/Rscript",
            "--vanilla",
            str(script),
            "unused",
            str(tmp_path),
            "unused",
            "unused",
            "unused",
            str(entry),
        ),
        cwd=tmp_path,
        timeout_seconds=5,
    )
    assert result.returncode == 0, result.stderr.decode()
    assert entry.read_bytes() == before
    assert (tmp_path / "executions.txt").read_text().strip() == "6"
    assert len(pd.read_csv(tmp_path / "timings.csv")) == 6
    assert (
        (tmp_path / "all-undefined-refusal.txt")
        .read_text()
        .strip()
        .startswith("refused:")
    )


@pytest.mark.parametrize("assignments", ["", "result <- 1\nresult <- 2\n"])
def test_r_wrapper_refuses_ambiguous_original_entry(
    tmp_path: Path, assignments: str
) -> None:
    entry = tmp_path / "entry.R"
    entry.write_text(assignments)
    script = Path(execution.__file__).with_name("timed_replay.R")
    result = run_bounded_argv(
        (
            "/usr/local/bin/Rscript",
            "--vanilla",
            str(script),
            "unused",
            str(tmp_path),
            "unused",
            "unused",
            "unused",
            str(entry),
        ),
        cwd=tmp_path,
        timeout_seconds=5,
    )
    assert result.returncode != 0
    assert not (tmp_path / "timings.csv").exists()


@pytest.mark.parametrize(
    "failure", ["dirty_source", "missing_input", "missing_archive"]
)
def test_actual_worker_failure_and_later_integrity_failure_both_survive_in_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    for name in THREAD_VARIABLES:
        monkeypatch.setenv(name, "1")
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "library").mkdir()
    for relative in (
        inputs.REPLAY,
        inputs.SUPPORT,
        inputs.ARCHIVE,
        execution.PACKAGE / "timed_replay.R",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("controlled source")
    calls = 0

    def source_revision(_: Path) -> str:
        nonlocal calls
        calls += 1
        if calls > 1 and failure == "dirty_source":
            raise ValueError("consumed source became dirty")
        return "a" * 40

    def write_inputs(path: Path) -> dict[str, str]:
        path.mkdir()
        (path / "input.csv").write_text("A\n1\n")
        return {
            "input.csv": hashlib.sha256((path / "input.csv").read_bytes()).hexdigest()
        }

    monkeypatch.setattr(execution, "revision", source_revision)
    monkeypatch.setattr(inputs, "write", write_inputs)

    def failed_command(argv: tuple[str, ...], **_: object) -> CompletedCommand:
        if failure == "missing_input":
            (tmp_path / "artifacts/result/input/input.csv").unlink()
        elif failure == "missing_archive":
            (tmp_path / inputs.ARCHIVE).unlink()
        return CompletedCommand(
            argv,
            7,
            b"original stdout",
            b"original worker failure",
            0.1,
            False,
            "not_required",
        )

    monkeypatch.setattr(execution, "run_bounded_argv", failed_command)
    destination = tmp_path / "artifacts" / "result"
    with pytest.raises(RuntimeError, match="python worker failed"):
        execution.run(
            tmp_path, destination, tmp_path / "library", Path("/usr/local/bin/Rscript")
        )
    report = json.loads((destination / "report.json").read_text())
    assert report["source_commit"] == "a" * 40
    assert report["status"] == "source_or_input_changed"
    assert report["commands"][0]["exit_code"] == 7
    assert report["error_type"] == "RuntimeError"
    if failure == "dirty_source":
        assert report["source_guard_error"] == "consumed source became dirty"
    elif failure == "missing_input":
        assert report["inputs_stable"] is False
        assert report["integrity_failures"] == ["input/input.csv"]
    else:
        assert report["archive_stable"] is False
        assert report["integrity_failures"] == [inputs.ARCHIVE.as_posix()]
    assert (
        destination / "python-stderr.txt"
    ).read_bytes() == b"original worker failure"


def test_removed_raw_asset_is_failed_integrity_not_an_unreported_io_exception(
    tmp_path: Path,
) -> None:
    path = tmp_path / "asset"
    path.write_bytes(b"raw")
    digest = hashlib.sha256(b"raw").hexdigest()
    assert execution.unchanged(path, digest)
    path.write_bytes(b"different")
    assert not execution.unchanged(path, digest)
    path.unlink()
    assert not execution.unchanged(path, digest)
