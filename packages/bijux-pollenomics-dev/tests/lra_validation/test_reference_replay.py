from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from bijux_pollenomics_dev.lra_validation.reference_replay import (
    compare_vectors,
    comparison_outcome,
    normalize_r_numbers,
    replay,
)


def test_r_literal_equivalence_preserves_strings_and_binary64_values() -> None:
    assert normalize_r_numbers('c(0.1,1.0,"taxon1.0")') == normalize_r_numbers(
        'c(0x1.999999999999ap-4,0x1.0000000000000p+0,"taxon1.0")'
    )
    assert normalize_r_numbers('c(0.1,"1.0")') != normalize_r_numbers(
        'c(0.10000000000000002,"1.0")'
    )
    assert normalize_r_numbers('c(1L,"1.0")') != normalize_r_numbers('c(1,"1.0")')


def test_comparison_preserves_nonfinite_positions_and_exact_coordinates() -> None:
    values = np.array([1.0, np.nan, np.inf, -np.inf])
    assert compare_vectors(values, values, rtol=1e-10, atol=1e-10, exact_indices=(0,))[
        "nan_positions"
    ] == [1]
    changed = values.copy()
    changed[0] += 1e-12
    assert (
        comparison_outcome(changed, values, rtol=1e-10, atol=1e-10, exact_indices=(0,))[
            "status"
        ]
        == "failed"
    )
    changed[0], changed[1] = 1.0, 0.0
    assert (
        comparison_outcome(changed, values, rtol=1e-10, atol=1e-10)["status"]
        == "failed"
    )


def test_shapes_strings_and_out_of_range_exact_coordinates_refuse() -> None:
    with pytest.raises(AssertionError, match="dimensions"):
        compare_vectors(np.array([1]), np.array([1, 2]), rtol=0, atol=0)
    with pytest.raises(AssertionError, match="outside"):
        compare_vectors(
            np.array([1]), np.array([1]), rtol=0, atol=0, exact_indices=(1,)
        )
    assert (
        comparison_outcome(np.array(["absent"]), np.array(["present"]), rtol=0, atol=0)[
            "status"
        ]
        == "failed"
    )


def test_certificate_tampering_refuses_before_output(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "certificate.json").write_text("{}\n")
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="certificate differs"):
        replay(tmp_path, bundle, output)
    assert not output.exists()


def _installed_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    import shutil

    from bijux_pollenomics_dev.lra_validation import reference_replay as module

    source = Path(module.__file__).resolve()
    original_repository = source.parents[5]
    repository = tmp_path / "repository"
    for relative in (
        "packages/bijux-pollenomics-lra/src",
        "packages/bijux-pollenomics-lra/tests/reference/lra_oracle",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference",
    ):
        shutil.copytree(
            original_repository / relative,
            repository / relative,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    canonical = (
        repository
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/reference_replay.py"
    )
    canonical.parent.mkdir(parents=True)
    shutil.copyfile(source, canonical)
    namespace = tmp_path / "site-packages/bijux_pollenomics_dev"
    installed = namespace / "lra_validation/reference_replay.py"
    installed.parent.mkdir(parents=True)
    shutil.copyfile(source, installed)
    shutil.copytree(
        source.parent.parent / "ci/lra_reference", namespace / "ci/lra_reference"
    )
    monkeypatch.setattr(module, "__file__", str(installed))
    return repository, namespace


def test_noneditable_replay_records_only_the_original_repository_source_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.lra_validation import reference_replay as module

    repository, installed = _installed_replay(tmp_path, monkeypatch)
    development = (
        repository / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev"
    )
    lra = repository / "packages/bijux-pollenomics-lra/src"
    oracle = repository / "packages/bijux-pollenomics-lra/tests/reference/lra_oracle"
    original = {
        path.relative_to(repository).as_posix()
        for path in (
            set(lra.rglob("*.py"))
            | set(oracle.rglob("*"))
            | set(lra.rglob("*.npz"))
            | set(lra.rglob("*.json"))
            | set((development / "ci/lra_reference").rglob("*.py"))
            | {development / "lra_validation/reference_replay.py"}
        )
        if path.is_file() and "__pycache__" not in path.parts
    }
    assert not installed.is_relative_to(repository)
    assert set(module._replay_source_hashes(repository)) == original
    assert all(not name.startswith("/") for name in original)


@pytest.mark.parametrize(
    "changed", ["replay", "validator", "missing", "extra", "symlink"]
)
def test_noneditable_replay_source_mismatch_refuses_before_bundle_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed: str
) -> None:
    import hashlib
    import json

    from bijux_pollenomics_dev.lra_validation import reference_replay as module

    repository, installed = _installed_replay(tmp_path, monkeypatch)
    leaf = installed / "ci/lra_reference/evidence.py"
    if changed == "replay":
        (installed / "lra_validation/reference_replay.py").write_text(
            "# different replay\n"
        )
    elif changed == "validator":
        leaf.write_text("# different validator\n")
    elif changed == "missing":
        leaf.unlink()
    elif changed == "extra":
        (leaf.parent / "unexpected.py").write_text("# unexpected validator\n")
    else:
        leaf.unlink()
        leaf.symlink_to(
            repository
            / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/evidence.py"
        )
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    certificate = json.dumps({"source_commit": "fixture", "lock_sha256": "fixture"})
    (bundle / "certificate.json").write_text(certificate)
    monkeypatch.setattr(
        module, "CERTIFICATE_SHA256", hashlib.sha256(certificate.encode()).hexdigest()
    )

    def forbidden_validation(*args: object, **kwargs: object) -> None:
        raise AssertionError("Changed replay sources reached bundle validation")

    monkeypatch.setattr(module, "validate_bundle", forbidden_validation)
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="Installed|symlink refused"):
        module.replay(repository, bundle, output)
    assert not output.exists()


def test_generated_bytecode_does_not_expand_replay_source_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.lra_validation import reference_replay as module

    repository, installed = _installed_replay(tmp_path, monkeypatch)
    original = module._replay_source_hashes(repository)
    cache = installed / "ci/lra_reference/__pycache__"
    cache.mkdir(exist_ok=True)
    (cache / "runtime.py").write_text("# runtime-only cache\n")
    assert module._replay_source_hashes(repository) == original


def test_installed_validator_drift_during_replay_refuses_report_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import hashlib
    import importlib
    import json
    from types import ModuleType

    from bijux_pollenomics_dev.lra_validation import reference_replay as module

    repository, installed = _installed_replay(tmp_path, monkeypatch)
    bundle = tmp_path / "bundle"
    for directory in ("oracle", "source-domains"):
        (bundle / directory).mkdir(parents=True)
        (bundle / directory / "case_manifest.json").write_text("[]\n")
    (bundle / "oracle/oracle.R").write_text("")
    certificate = json.dumps({"source_commit": "fixture", "lock_sha256": "fixture"})
    (bundle / "certificate.json").write_text(certificate)
    monkeypatch.setattr(
        module, "CERTIFICATE_SHA256", hashlib.sha256(certificate.encode()).hexdigest()
    )
    monkeypatch.setattr(module, "validate_bundle", lambda *args, **kwargs: None)
    core = ModuleType("fixture_core")
    domains = ModuleType("fixture_domains")

    def changed_setup(output: Path) -> tuple[list[str], list[object]]:
        (installed / "ci/lra_reference/evidence.py").write_text(
            "# changed during replay\n"
        )
        return [], []

    monkeypatch.setattr(core, "build_cases", changed_setup, raising=False)
    monkeypatch.setattr(domains, "cases", list, raising=False)
    original_import = importlib.import_module

    def fixture_import(name: str, package: str | None = None) -> ModuleType:
        if name == "lra_oracle.cases":
            return core
        if name == "lra_oracle.run_source_domains":
            return domains
        return original_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fixture_import)
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="Installed R validator source differs"):
        module.replay(repository, bundle, output)
    assert not (output / "report.json").exists()
