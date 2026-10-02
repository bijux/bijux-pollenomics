"""Source dispatch, byte serialization and confinement for replay adapters."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

import pytest

ADAPTERS = (
    ("denmark_pollen_chronology_coverage", "run(repository)", False),
    ("neotoma_compact_summary", "build_report()", True),
)


def _module(name: str) -> ModuleType:
    return importlib.import_module(f"bijux_pollenomics_dev.source_completion.{name}")


def _fixture(root: Path, module: ModuleType, signature: str) -> None:
    script = root / module.REPLAY
    script.parent.mkdir(parents=True)
    script.write_text(
        f"def {signature}:\n    return {{'z': 'é', 'a': 2}}\n", encoding="utf-8"
    )


@pytest.mark.parametrize(("name", "signature", "sorted_keys"), ADAPTERS)
def test_cli_dispatches_fixed_replay_and_preserves_source_serialization(
    tmp_path: Path, name: str, signature: str, sorted_keys: bool
) -> None:
    module = _module(name)
    _fixture(tmp_path, module, signature)
    output = tmp_path / "artifacts/report.json"
    assert module.main(["--repository", str(tmp_path), "--output", str(output)]) == 0
    expected = (
        '{\n  "a": 2,\n  "z": "é"\n}\n'
        if sorted_keys
        else '{\n  "z": "é",\n  "a": 2\n}\n'
    )
    assert output.read_bytes() == expected.encode("utf-8")
    with pytest.raises(ValueError, match="Absent"):
        module.publish(tmp_path, output)
    assert output.read_bytes() == expected.encode("utf-8")


@pytest.mark.parametrize(("name", "signature", "sorted_keys"), ADAPTERS)
def test_destinations_are_checked_before_replay_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    signature: str,
    sorted_keys: bool,
) -> None:
    module = _module(name)
    repository = tmp_path / "repository"
    _fixture(repository, module, signature)
    artifacts = repository / "artifacts"
    artifacts.mkdir()
    linked = artifacts / "linked"
    linked.symlink_to(artifacts / "absent")
    parent = artifacts / "escape"
    parent.symlink_to(tmp_path, target_is_directory=True)
    calls: list[object] = []
    monkeypatch.setattr(module.runpy, "run_path", lambda *_: calls.append(True))
    for output in (repository / "outside.json", artifacts, linked, parent / "new"):
        with pytest.raises(ValueError, match="output"):
            module.publish(repository, output)
    assert not calls


@pytest.mark.parametrize(("name", "signature", "sorted_keys"), ADAPTERS)
def test_external_replay_and_source_refusal_are_preserved(
    tmp_path: Path, name: str, signature: str, sorted_keys: bool
) -> None:
    module = _module(name)
    repository = tmp_path / "repository"
    _fixture(repository, module, signature)
    script = repository / module.REPLAY
    script.write_text(f"def {signature}:\n    raise ValueError('source changed')\n")
    output = repository / "artifacts/result.json"
    with pytest.raises(ValueError, match="source changed"):
        module.publish(repository, output)
    assert not output.exists()
    script.unlink()
    external = tmp_path / "external.py"
    external.write_text(f"def {signature}:\n    return {{}}\n")
    script.symlink_to(external)
    with pytest.raises(ValueError, match="outside the repository"):
        module.publish(repository, output)
    assert not output.exists()


@pytest.mark.parametrize(("name", "signature", "sorted_keys"), ADAPTERS)
def test_cli_requires_fixed_source_arguments(
    name: str, signature: str, sorted_keys: bool
) -> None:
    module = _module(name)
    with pytest.raises(SystemExit, match="2"):
        module.main(["--repository", "."])
    with pytest.raises(SystemExit, match="2"):
        module.main(["--output", "somewhere"])
    with pytest.raises(SystemExit, match="2"):
        module.main(["--repository", ".", "--output", "somewhere", "--capture", "x"])
