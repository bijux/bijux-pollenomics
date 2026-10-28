"""Bind retained interval means across supported Python float summation runtimes."""

from __future__ import annotations

import csv
import importlib.util
import json
import math
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY = Path(__file__).resolve().parents[5]
REPORT = REPOSITORY / "docs/report/pollen-reconstruction"
INTERVAL = (
    REPOSITORY / "docs/report/regions/nordic/sambosjon-direct-pollen/interval-support"
)
METRICS = (
    "mae_fraction",
    "hellinger_distance",
    "parent_same_bin_mae_fraction",
    "parent_same_bin_hellinger_distance",
)


def _verifier() -> ModuleType:
    source = REPORT / "verify_report.py"
    spec = importlib.util.spec_from_file_location("sambosjon_report_verifier", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _scope_and_results() -> tuple[dict[str, object], list[list[str]]]:
    scope = json.loads((REPORT / "scope.json").read_text(encoding="utf-8"))
    with (REPORT / "results.csv").open(newline="", encoding="utf-8") as stream:
        results = list(csv.reader(stream))
    return scope, results


def test_adjacent_binary_floats_only() -> None:
    same = _verifier()._same_or_adjacent_float
    values = (0.25, 0.5, 1.0, 0.18574098068796224)
    for expected in values:
        lower = math.nextafter(expected, -math.inf)
        upper = math.nextafter(expected, math.inf)
        assert same(expected, expected)
        assert same(lower, expected)
        assert same(upper, expected)
        assert not same(math.nextafter(lower, -math.inf), expected)
        assert not same(math.nextafter(upper, math.inf), expected)
    for value in (math.nan, math.inf, -math.inf):
        assert not same(value, 1.0)
        assert not same(1.0, value)


def test_all_retained_method_means_are_equal_or_adjacent() -> None:
    same = _verifier()._same_or_adjacent_float
    report = json.loads((INTERVAL / "report.json").read_text(encoding="utf-8"))
    with (INTERVAL / "scores.csv").open(newline="") as stream:
        scores = list(csv.DictReader(stream))
    comparisons = 0
    for method, summary in report["methods"].items():
        selected = [
            row
            for row in scores
            if row["method"] == method and row["status"] == "scored"
        ]
        assert len(selected) == summary["paired_bins"] == 21
        for key in METRICS:
            observed = sum(float(row[key]) for row in selected) / len(selected)
            assert same(observed, summary[key]), (method, key)
            comparisons += 1
    assert comparisons == 12


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("metric", "interval method summaries differ"),
        ("producer", "contained-age scope differs"),
    ],
)
def test_retained_scope_passes_and_material_change_refuses(
    monkeypatch: pytest.MonkeyPatch, change: str, message: str
) -> None:
    verifier = _verifier()
    scope, results = _scope_and_results()
    verifier.verify_sambosjon_contained_age_support(scope, results)
    path = INTERVAL / "report.json"
    original_read_text = Path.read_text
    altered = json.loads(path.read_text(encoding="utf-8"))
    if change == "metric":
        altered["methods"]["nearest_site"]["mae_fraction"] += 1e-9
    else:
        altered["producer_sha256"] = "0" * 64

    def changed_read_text(
        self: Path, encoding: str | None = None, errors: str | None = None
    ) -> str:
        if self == path:
            return json.dumps(altered)
        return original_read_text(self, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", changed_read_text)
    with pytest.raises(ValueError, match=message):
        verifier.verify_sambosjon_contained_age_support(scope, results)
