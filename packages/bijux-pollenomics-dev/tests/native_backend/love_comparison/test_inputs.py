"""Controlled input exports retain exact binary64 values and source labels."""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_dev.native_backend.love_comparison import inputs


def shared_inputs(directory: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    local = pd.DataFrame({"age": [0], "A": [0.12345678901234567]})
    parameters = pd.DataFrame({"Taxon": ["A"], "ppe": [2.345678901234567]})
    monkeypatch.setattr(
        inputs,
        "load_love_example",
        lambda: (local, local.copy(), {"ppes": parameters}, local.copy()),
    )
    monkeypatch.setattr(
        inputs,
        "workloads",
        lambda _: [
            SimpleNamespace(
                contract={
                    "config": inputs.CONFIG.as_dict(),
                    "candidates": np.linspace(0.1, 0.9, 320).reshape(32, 10).tolist(),
                }
            )
        ],
    )
    inputs.write(directory)


def test_shared_export_preserves_decimal_and_hex_binary64_and_taxon_labels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shared_inputs(tmp_path / "input", monkeypatch)
    tables = inputs.read(tmp_path / "input")
    assert tables["local"]["A"].iloc[0] == 0.12345678901234567
    assert tables["ppes"].Taxon.tolist() == ["A"]


@pytest.mark.parametrize("kind", ["number", "label", "hex"])
def test_numeric_or_axis_tampering_is_not_repaired(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    directory = tmp_path / "input"
    shared_inputs(directory, monkeypatch)
    target = directory / ("local.csv" if kind == "number" else "local-hex.csv")
    content = target.read_text()
    if kind == "number":
        content = content.replace("0.12345678901234566", "0.5")
    elif kind == "label":
        content = content.replace("age,A", "age,foreign")
    else:
        content = content.replace((0.12345678901234567).hex(), (0.5).hex())
    target.write_text(content)
    with pytest.raises(ValueError, match="differ"):
        inputs.read(directory)
