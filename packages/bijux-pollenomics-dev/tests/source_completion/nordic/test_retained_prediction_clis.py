"""Exercise Swedish prediction routing with fake source CLIs only."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import runpy
import sys
from types import ModuleType, SimpleNamespace

import pytest

from bijux_pollenomics_dev.source_completion.nordic import (
    swedish_author_predictions,
    swedish_core_predictions,
    swedish_lake_predictions,
)

ROUTES = (
    swedish_author_predictions,
    swedish_lake_predictions,
    swedish_core_predictions,
)


def repository(tmp_path: Path, route: ModuleType) -> Path:
    root = tmp_path / "repository"
    (root / "artifacts").mkdir(parents=True)
    source = root / route.SOURCE
    source.parent.mkdir(parents=True)
    source.write_text("# fake source; never executed\n", encoding="utf-8")
    prepared = root / route.PREPARED
    (prepared / "inputs").mkdir(parents=True)
    (prepared / "input-manifest.json").write_text(
        json.dumps(
            {
                "axis": [str(index) for index in range(31)],
                "target_outcomes_in_prediction_inputs": False,
            }
        ),
        encoding="utf-8",
    )
    (prepared / "inputs/metadata-SE.json.gz").write_bytes(b"metadata fixture")
    (prepared / "inputs/training-SE.json.gz").write_bytes(b"training fixture")
    return root


def bind_fake_cli(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    route: ModuleType,
    calls: list[tuple[str, tuple[str, ...]]],
) -> None:
    source = root / route.SOURCE
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(source)),
    )

    def fake_module(module: str, *, run_name: str) -> None:
        assert run_name == "__main__"
        assert sys.argv == [
            str(source),
            "predict",
            "--prepared",
            str(root / route.PREPARED),
            "--output",
            str(root / "artifacts/source-products"),
        ]
        calls.append((module, tuple(sys.argv)))
        output = Path(sys.argv[-1])
        output.mkdir()
        (output / "predictions-SE.json.gz").write_bytes(b"prediction fixture")

    monkeypatch.setattr(runpy, "run_module", fake_module)


@pytest.mark.parametrize("route", ROUTES)
def test_only_predict_stage_uses_exact_module_and_restores_argv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: ModuleType
) -> None:
    root = repository(tmp_path, route)
    calls: list[tuple[str, tuple[str, ...]]] = []
    bind_fake_cli(monkeypatch, root, route, calls)
    prior = sys.argv
    assert (
        route.main(
            [
                "--repository",
                str(root),
                "--output",
                str(root / "artifacts/source-products"),
            ]
        )
        == 0
    )
    assert sys.argv is prior
    assert len(calls) == 1
    assert calls[0][0] == (
        str(route.SOURCE)
        .removeprefix("packages/bijux-pollenomics-dev/src/")
        .removesuffix(".py")
        .replace("/", ".")
    )
    assert calls[0][1][1] == "predict"
    assert (
        root / "artifacts/source-products/predictions-SE.json.gz"
    ).read_bytes() == b"prediction fixture"


def test_source_failure_restores_argv_and_does_not_enter_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    route = swedish_author_predictions
    root = repository(tmp_path, route)
    source = root / route.SOURCE
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(source)),
    )
    monkeypatch.setattr(
        runpy,
        "run_module",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("source refusal")),
    )
    prior = sys.argv
    with pytest.raises(RuntimeError, match="source refusal"):
        route.run(root, root / "artifacts/source-products")
    assert sys.argv is prior


def test_refuses_different_module_origin_before_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    route = swedish_lake_predictions
    root = repository(tmp_path, route)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: SimpleNamespace(origin=str(root / "other.py")),
    )
    monkeypatch.setattr(
        runpy,
        "run_module",
        lambda *args, **kwargs: pytest.fail("CLI entered"),
    )
    with pytest.raises(ValueError, match="origin differs"):
        route.run(root, root / "artifacts/source-products")


@pytest.mark.parametrize("mode", ("outside", "existing", "symlink", "relative"))
def test_refuses_invalid_destination_before_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    route = swedish_core_predictions
    root = repository(tmp_path, route)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: pytest.fail("source import attempted"),
    )
    monkeypatch.setattr(
        runpy,
        "run_module",
        lambda *args, **kwargs: pytest.fail("CLI entered"),
    )
    output = root / "artifacts/source-products"
    if mode == "outside":
        output = tmp_path / "outside"
    elif mode == "existing":
        output.mkdir()
    elif mode == "symlink":
        output.symlink_to(tmp_path, target_is_directory=True)
    elif mode == "relative":
        output = Path("artifacts/source-products")
    with pytest.raises(ValueError):
        route.run(root, output)


def test_refuses_symlinked_input_and_unsealed_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    route = swedish_author_predictions
    root = repository(tmp_path, route)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: pytest.fail("source import attempted"),
    )
    monkeypatch.setattr(
        runpy,
        "run_module",
        lambda *args, **kwargs: pytest.fail("CLI entered"),
    )
    metadata = root / route.PREPARED / "inputs/metadata-SE.json.gz"
    metadata.unlink()
    metadata.symlink_to(root / route.PREPARED / "inputs/training-SE.json.gz")
    with pytest.raises(ValueError, match="prepared inputs"):
        route.run(root, root / "artifacts/source-products")
    metadata.unlink()
    metadata.write_bytes(b"metadata fixture")
    manifest = root / route.PREPARED / "input-manifest.json"
    value = json.loads(manifest.read_text())
    value["target_outcomes_in_prediction_inputs"] = True
    manifest.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="seal target outcomes"):
        route.run(root, root / "artifacts/source-products")


@pytest.mark.parametrize("route", ROUTES)
def test_refuses_unconfigured_seed_before_source_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, route: ModuleType
) -> None:
    root = repository(tmp_path, route)
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda module: pytest.fail("source import attempted"),
    )
    with pytest.raises(SystemExit) as error:
        route.main(
            [
                "--repository",
                str(root),
                "--output",
                str(root / "artifacts/source-products"),
                "--seed",
                "42",
            ]
        )
    assert error.value.code == 2


def test_real_module_loader_preserves_relative_imports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev import source_completion

    route = swedish_author_predictions
    root = repository(tmp_path, route)
    source = root / route.SOURCE
    source.write_text(
        "from .prediction_fixture import write_prediction\nwrite_prediction()\n"
    )
    helper = source.with_name("prediction_fixture.py")
    helper.write_text(
        "from pathlib import Path\nimport sys\ndef write_prediction():\n    assert sys.argv[1] == 'predict'\n    output = Path(sys.argv[-1])\n    output.mkdir()\n    (output / 'predictions-SE.json.gz').write_bytes(b'relative-import prediction')\n"
    )
    module = "bijux_pollenomics_dev.source_completion.swedish_author_target_pollen"
    helper_module = "bijux_pollenomics_dev.source_completion.prediction_fixture"
    monkeypatch.delitem(sys.modules, module, raising=False)
    monkeypatch.setattr(source_completion, "__path__", [str(source.parent)])
    original = sys.argv
    try:
        route.run(root, root / "artifacts/source-products")
        assert sys.argv is original
        assert (
            root / "artifacts/source-products/predictions-SE.json.gz"
        ).read_bytes() == b"relative-import prediction"
    finally:
        sys.modules.pop(helper_module, None)
