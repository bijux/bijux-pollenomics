"""Real experiment entry points retain exact split authority before backend work."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import SiteRecord, ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.contracts import canonical_json
from bijux_pollenomics.analysis.lra_validation.experiments.split_authority import (
    freeze_experiment_split,
)
from bijux_pollenomics.analysis.lra_validation.splits import (
    grouped_block_holdouts,
    grouped_leave_one_out,
)

from .fitted.test_admission import block_local_payload, block_payload
from .fitted.test_model import payload as fitted_payload
from .test_assimilation import local_payload
from .test_inputs import fixture_inputs

_CASES = (
    ("workflow", "prepare_experiment_predictions", "reconstruct_fold", False, False),
    (
        "fitted.workflow",
        "prepare_fitted_spatial_predictions",
        "reconstruct_fold",
        False,
        False,
    ),
    (
        "fitted.blocks",
        "prepare_spatial_block_predictions",
        "reconstruct_fold",
        True,
        False,
    ),
    ("assimilation", "prepare_local_pollen_predictions", "run_lra_batch", False, True),
    (
        "block_assimilation",
        "prepare_spatial_block_local_pollen_predictions",
        "run_lra_batch",
        True,
        True,
    ),
)


def _payload(name: str, root: Path) -> dict[str, Any]:
    factory = {
        "workflow": fixture_inputs,
        "fitted.workflow": fitted_payload,
        "fitted.blocks": block_payload,
        "assimilation": local_payload,
        "block_assimilation": block_local_payload,
    }[name]
    return factory(root)


@pytest.mark.parametrize("module_name,operation,backend,by_block,batch", _CASES)
def test_real_producer_persists_split_before_first_backend_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    operation: str,
    backend: str,
    by_block: bool,
    batch: bool,
) -> None:
    request = _payload(module_name, tmp_path / "inputs")
    module = importlib.import_module(
        "bijux_pollenomics.analysis.lra_validation.experiments." + module_name
    )
    records = tuple(
        SiteRecord(
            s["record_id"], s["site_id"], tuple(s["identity_keys"]), s.get("block_id")
        )
        for s in request["sites"]
    )
    folds = (
        grouped_block_holdouts(records) if by_block else grouped_leave_one_out(records)
    )
    expected = (canonical_json([f.as_dict() for f in folds]) + "\n").encode()
    calls: list[bytes] = []

    def checked_backend(*args: Any, **kwargs: Any) -> Any:
        (stage,) = tmp_path.glob(".product.pending-*")
        content = (stage / "folds.json").read_bytes()
        assert content == expected
        if module_name == "block_assimilation":
            assert (stage / "split_manifest.json").is_file()
        calls.append(content)
        raise ValidationRefusal(
            "controlled_backend_probe", "No numerical work in this unit check"
        )

    monkeypatch.setattr(module, backend, checked_backend)
    operation_function = getattr(module, operation)
    arguments = {
        "input_root": tmp_path / "inputs",
        "cache_root": tmp_path / "cache",
        "destination": tmp_path / "product",
    }
    if batch:
        with pytest.raises(ValidationRefusal, match="No numerical work"):
            operation_function(request, **arguments)
    else:
        product = operation_function(request, **arguments)
        assert (product.directory / "folds.json").read_bytes() == expected
        assert json.loads((product.directory / "failures.json").read_text())
    assert calls and all(content == expected for content in calls)


@pytest.mark.parametrize("module_name,operation", [(r[0], r[1]) for r in _CASES[:3]])
def test_changed_prefit_manifest_refuses_next_fold_without_rewriting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    operation: str,
) -> None:
    request = _payload(module_name, tmp_path / "inputs")
    module = importlib.import_module(
        "bijux_pollenomics.analysis.lra_validation.experiments." + module_name
    )
    calls = 0

    def changed_backend(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        (stage,) = tmp_path.glob(".product.pending-*")
        (stage / "folds.json").write_bytes(b"[]\n")
        raise ValidationRefusal("controlled_backend_probe", "Changed manifest")

    monkeypatch.setattr(module, "reconstruct_fold", changed_backend)
    with pytest.raises(ValidationRefusal, match="Frozen experiment split bytes differ"):
        getattr(module, operation)(
            request,
            input_root=tmp_path / "inputs",
            cache_root=tmp_path / "cache",
            destination=tmp_path / "product",
        )
    assert calls == 1 and not (tmp_path / "product").exists()
    (stage,) = tmp_path.glob(".product.pending-*")
    assert (stage / "folds.json").read_bytes() == b"[]\n"


@pytest.mark.parametrize("change", ["missing", "bytes", "symlink"])
def test_prefit_authority_preserves_exact_regular_bytes(
    tmp_path: Path, change: str
) -> None:
    records = (SiteRecord("a", "a"), SiteRecord("b", "b"))
    guard = freeze_experiment_split(tmp_path, grouped_leave_one_out(records))
    path = tmp_path / "folds.json"
    path.unlink()
    if change == "bytes":
        path.write_bytes(b"[]\n")
    elif change == "symlink":
        foreign = tmp_path / "foreign.json"
        foreign.write_bytes(guard.members[0][1])
        path.symlink_to(foreign)
    with pytest.raises(ValidationRefusal, match="Frozen experiment split bytes differ"):
        guard.verify()


def test_existing_split_is_never_overwritten(tmp_path: Path) -> None:
    (tmp_path / "folds.json").write_bytes(b"existing\n")
    with pytest.raises(ValidationRefusal, match="folds.json"):
        freeze_experiment_split(
            tmp_path,
            grouped_leave_one_out((SiteRecord("a", "a"), SiteRecord("b", "b"))),
        )
    assert (tmp_path / "folds.json").read_bytes() == b"existing\n"
