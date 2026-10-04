"""Refuse source identity, measurement and chronology substitutions."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin.sources import (
    explicit_panel,
    pollen_counts,
    read_bound,
    selected_age,
)

ROOT = Path(__file__).resolve().parents[5]
RAW = ROOT / "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json"


@pytest.fixture(scope="module")
def source_sample():
    payload = json.loads(RAW.read_bytes())
    dataset = next(
        row["site"]["collectionunit"]["dataset"]
        for row in payload["rows"]
        if row["site"]["collectionunit"]["dataset"]["datasetid"] == 19913
    )
    return dataset["samples"][1]


def test_actual_native_panel_and_named_age(source_sample):
    prepared = pollen_counts(source_sample)
    counts, reason = explicit_panel(prepared, ["Betula", "Pinus sylvestris"])
    assert reason is None and sum(counts) > 0
    age, reason = selected_age(prepared, 11516)
    assert reason is None and age["age"] == 19


def test_source_hash_cannot_admit_changed_bytes(tmp_path):
    path = tmp_path / "source.json"
    path.write_bytes(b'{"datum":[]}')
    identity = {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }
    assert read_bound(tmp_path, "source.json", identity) == path.read_bytes()
    path.write_bytes(b'{"datum":[0]}')
    with pytest.raises(ValueError, match="source identity mismatch"):
        read_bound(tmp_path, "source.json", identity)


def test_percent_pollen_cannot_be_counted(source_sample):
    changed = deepcopy(source_sample)
    pollen = next(
        d for d in changed["datum"] if d["element"] == d["elementtype"] == "pollen"
    )
    pollen["units"] = "%"
    with pytest.raises(ValueError, match="not NISP"):
        pollen_counts(changed)


def test_fractional_pollen_cannot_be_counted(source_sample):
    changed = deepcopy(source_sample)
    pollen = next(
        d for d in changed["datum"] if d["element"] == d["elementtype"] == "pollen"
    )
    pollen["value"] = 0.5
    with pytest.raises(ValueError, match="nonnegative integer"):
        pollen_counts(changed)


def test_missing_panel_row_cannot_be_observed_zero(source_sample):
    prepared = pollen_counts(source_sample)
    del prepared["counts"]["Betula"]
    counts, reason = explicit_panel(prepared, ["Betula", "Pinus sylvestris"])
    assert counts is None and reason == "panel_taxon_not_explicitly_reported"


def test_selected_age_requires_named_calibrated_chronology(source_sample):
    prepared = pollen_counts(source_sample)
    age, reason = selected_age(prepared, 999999)
    assert age is None and reason == "named_calibrated_chronology_missing_or_ambiguous"
    changed = deepcopy(prepared)
    changed["ages"][0]["agetype"] = "Radiocarbon years BP"
    age, reason = selected_age(changed, 11516)
    assert age is None and reason == "named_calibrated_chronology_missing_or_ambiguous"


def test_native_duplicate_pollen_needs_aggregation_decision(source_sample):
    changed = deepcopy(source_sample)
    changed["datum"].append(
        deepcopy(
            next(
                d
                for d in changed["datum"]
                if d["element"] == d["elementtype"] == "pollen"
            )
        )
    )
    with pytest.raises(ValueError, match="aggregation decision"):
        pollen_counts(changed)


def test_authored_protocol_rejects_nonmonotonic_windows():
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin.reconstruction import (
        validate_protocol,
    )

    with pytest.raises(ValueError, match="strictly increasing"):
        validate_protocol({"age_window_edges_cal_bp": [0, 100, 100]})


def test_metadata_identity_is_not_replaceable(tmp_path):
    body = (
        ROOT / "docs/report/publication-replay/landclim-study-inputs/records.jsonl"
    ).read_bytes()
    path = tmp_path / "metadata.jsonl"
    path.write_bytes(body)
    identity = {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
    path.write_bytes(body.replace(b'"raw":"Sweden"', b'"raw":"Denmark"', 1))
    assert path.read_bytes() != body
    with pytest.raises(ValueError, match="source identity mismatch"):
        read_bound(tmp_path, "metadata.jsonl", identity)


def test_output_boundary_and_atomic_failure(tmp_path, monkeypatch):
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
        producer,
    )

    root = tmp_path / "repository"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='test-producer'\n")
    (root / "artifacts").mkdir()
    output = root / "artifacts" / "account"

    def refuse(*args):
        raise ValueError("controlled scientific acceptance refusal")

    monkeypatch.setattr(producer, "reconstruct", refuse)
    with pytest.raises(ValueError, match="controlled scientific acceptance"):
        producer.publish(root, root, output, "a" * 40)
    assert not output.exists()
    assert len(list((root / "artifacts").glob(".swedish-static-basin-*"))) == 1
    from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

    with pytest.raises(ReportRebuildError, match="below repository artifacts"):
        producer.publish(root, root, root / "docs", "a" * 40)


def test_cli_candidate_is_bound_to_authored_source_descriptor(tmp_path, monkeypatch):
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
        producer,
    )

    descriptor = (
        tmp_path
        / "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/inputs/source-identities.json"
    )
    descriptor.parent.mkdir(parents=True)
    descriptor.write_text(json.dumps({"producer_source_candidate": "a" * 40}))
    calls = []
    monkeypatch.setattr(producer, "publish", lambda *args: calls.append(args))
    argv = [
        "--repository",
        str(tmp_path),
        "--output",
        str(tmp_path / "artifacts/output"),
    ]
    assert producer.main(argv) == 0
    assert calls[0][-1] == "a" * 40
    with pytest.raises(ValueError, match="source declaration"):
        producer.main(argv + ["--candidate", "b" * 40])
    assert len(calls) == 1
