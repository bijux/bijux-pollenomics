"""Accept one declared reading-link alias while retaining raw and score custody."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[4]
READING_LINK = (
    b"[family replay](https://github.com/bijux/bijux-pollenomics/blob/"
    b"6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/"
    b"pollen-reconstruction/author-buffered-pollen/replay.py)"
)


@pytest.fixture
def buffered(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    spec = importlib.util.spec_from_file_location(
        "buffered_custody_reader",
        ROOT / "docs/report/pollen-reconstruction/verify_report.py",
    )
    assert spec is not None and spec.loader is not None
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    monkeypatch.setattr(verifier, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(verifier, "BUFFERED_NUMERICAL_SOURCES", {"producer.py"})
    monkeypatch.setattr(verifier, "BUFFERED_READER_WITNESSES", {})
    directory = tmp_path / "buffered"
    files: dict[str, bytes] = {
        "README.md": b"Synthetic mean: 0.1. See [family replay](replay.py).\n"
    }

    def encoded(value: object) -> bytes:
        return (json.dumps(value, sort_keys=True) + "\n").encode()

    def digest(raw: bytes) -> str:
        return hashlib.sha256(raw).hexdigest()

    methods = {
        "training_mean": "training-mean",
        "nearest_site": "nearest-site",
        "inverse_distance_squared": "inverse-distance-squared",
        "clr_rbf_ridge_half_count": "fitted-clr-rbf",
    }
    receipts = {}
    for method, name in methods.items():
        report = encoded({"scored_site_bins": 1, "prediction_report_sha256": {}})
        scores = b"site,value\nsynthetic,0.1\n"
        files[name + "/scores/report.json"] = report
        files[name + "/scores/scores.csv"] = scores
        receipts[method] = {
            "report_sha256": digest(report),
            "scores_sha256": digest(scores),
        }
    files["comparisons/fitted-common-support/report.json"] = encoded(
        {
            "observed_site_bins": 1,
            "common_scored_site_bins": 1,
            "methods": [
                {
                    "method": "clr_rbf_ridge_half_count",
                    "common_site_macro_mae_fraction": 0.1,
                },
                {"method": "training_mean", "common_site_macro_mae_fraction": 0.2},
            ],
            "score_receipts": receipts,
            "method_specific_scored_bins": dict.fromkeys(methods, 1),
        }
    )
    files["comparisons/taxon/report.json"] = encoded({"common_scored_site_bins": 1})
    files["comparisons/strict-clr-support/report.json"] = encoded(
        {"blocks": [{"bins_with_strict_clr_fit": 0}]}
    )
    for index in range(54 - len(files)):
        files[f"synthetic/member-{index}.bin"] = b"explicit synthetic fixture\n"
    producer = tmp_path / "producer.py"
    producer.write_bytes(b"synthetic_producer = True\n")
    manifest = {
        "private_source_manifest_sha256": "1" * 64,
        "files": [
            {"path": name, "sha256": digest(body), "bytes": len(body)}
            for name, body in files.items()
        ],
        "producer_sha256": {"producer.py": digest(producer.read_bytes())},
    }
    for name, body in files.items():
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    (directory / "manifest.json").write_bytes(encoded(manifest))
    scope: dict[str, Any] = {
        "author_buffered_spatial_pollen": {
            "directory": "buffered",
            "private_source_manifest_sha256": "1" * 64,
            "observed_site_bins": 1,
            "fixed_baseline_scored_bins": 1,
            "four_method_common_scored_bins": 1,
            "fitted_site_macro_mae_fraction": 0.1,
            "training_mean_common_site_macro_mae_fraction": 0.2,
        }
    }
    return SimpleNamespace(
        verifier=verifier, directory=directory, producer=producer, scope=scope
    )


@pytest.mark.parametrize("current_link", [False, True])
def test_original_and_exact_reading_link_keep_full_custody(
    buffered: SimpleNamespace, current_link: bool
) -> None:
    if current_link:
        path = buffered.directory / "README.md"
        path.write_bytes(
            path.read_bytes().replace(b"[family replay](replay.py)", READING_LINK)
        )
    buffered.verifier.verify_author_buffered_pollen(buffered.scope)


@pytest.mark.parametrize(
    "mutation",
    [
        "scientific_text",
        "whitespace",
        "other_revision",
        "duplicate",
        "raw_score",
        "producer",
    ],
)
def test_alias_never_exempts_other_scientific_or_source_mutation(
    buffered: SimpleNamespace, mutation: str
) -> None:
    path = buffered.directory / "README.md"
    raw = path.read_bytes().replace(b"[family replay](replay.py)", READING_LINK)
    if mutation == "scientific_text":
        raw = raw.replace(b"0.1", b"0.9")
    elif mutation == "whitespace":
        raw += b" "
    elif mutation == "other_revision":
        raw = raw.replace(b"6956a977", b"00000000")
    elif mutation == "duplicate":
        raw += READING_LINK
    elif mutation == "raw_score":
        (buffered.directory / "training-mean/scores/scores.csv").write_bytes(
            b"substituted raw score"
        )
    else:
        buffered.producer.write_bytes(b"synthetic_producer = False\n")
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="buffered author"):
        buffered.verifier.verify_author_buffered_pollen(buffered.scope)


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_manifest_producer_population_is_exact_in_the_synthetic_scope(
    buffered: SimpleNamespace, mutation: str
) -> None:
    path = buffered.directory / "manifest.json"
    manifest = json.loads(path.read_bytes())
    if mutation == "missing":
        manifest["producer_sha256"].pop("producer.py")
    else:
        extra = buffered.producer.with_name("extra.py")
        extra.write_bytes(b"extra_synthetic_producer = True\n")
        manifest["producer_sha256"]["extra.py"] = hashlib.sha256(
            extra.read_bytes()
        ).hexdigest()
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="source roles differ"):
        buffered.verifier.verify_author_buffered_pollen(buffered.scope)
