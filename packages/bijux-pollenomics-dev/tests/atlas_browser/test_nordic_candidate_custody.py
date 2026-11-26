"""Synthetic tests for the candidate-bound Nordic browser input seal."""

import hashlib
from importlib import import_module
import json
from pathlib import Path
import shutil
import subprocess

import pytest


def test_captured_candidate_is_immutable_after_source_changes(tmp_path: Path) -> None:
    owner = import_module(
        "bijux_pollenomics_dev.ci.atlas_browser.nordic_candidate_custody"
    )
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "index.html").write_bytes(b"original")
    sealed = owner.capture_candidate(candidate)
    (candidate / "index.html").write_bytes(b"replacement")
    assert sealed["index.html"] == b"original"


def test_candidate_capture_refuses_symlink(tmp_path: Path) -> None:
    owner = import_module(
        "bijux_pollenomics_dev.ci.atlas_browser.nordic_candidate_custody"
    )
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "alias").symlink_to(tmp_path / "outside")
    with pytest.raises(ValueError, match="nonregular or aliased"):
        owner.capture_candidate(candidate)


def test_candidate_closure_rejects_same_count_detail_substitution() -> None:
    owner = import_module(
        "bijux_pollenomics_dev.ci.atlas_browser.nordic_candidate_custody"
    )
    generation = {
        "schema_version": "atlas-nordic-retained-source-candidate.v1",
        "source_atlas_build_id": "source",
        "candidate_build_id": "candidate",
        "selected_source_record_equality": True,
        "countries": ["Denmark", "Finland", "Norway", "Sweden"],
        "inputs_sha256": {"docs/report/regions/nordic/nordic_map.html": "0" * 64},
        "source_records": [
            {
                "record_id": str(i),
                "detail_record_sha256": str(i),
                "feature_sha256": str(i),
            }
            for i in range(8)
        ],
    }
    original = {
        "generation.json": json.dumps(generation).encode(),
        "index.html": b"page",
        "x.atlas-details.js": b"original cells",
    }
    owner.validate_candidate_closure(original, original)
    omitted = dict(original)
    fake_inputs = dict(generation, inputs_sha256={})
    omitted["generation.json"] = json.dumps(fake_inputs).encode()
    with pytest.raises(ValueError, match="input inventory"):
        owner.validate_candidate_closure(omitted, original)
    changed = dict(original)
    changed["x.atlas-details.js"] = b"different cells"
    with pytest.raises(ValueError, match="candidate"):
        owner.validate_candidate_closure(changed, original)
    altered = dict(original)
    fake = dict(generation)
    fake["source_atlas_build_id"] = "different"
    altered["generation.json"] = json.dumps(fake).encode()
    with pytest.raises(ValueError, match="candidate"):
        owner.validate_candidate_closure(altered, original)


def test_generation_input_pins_detect_mutation_and_parent_escape(
    tmp_path: Path,
) -> None:
    owner = import_module(
        "bijux_pollenomics_dev.ci.atlas_browser.nordic_candidate_custody"
    )
    source = tmp_path / "source.json"
    source.write_bytes(b"original")
    generation = {
        "inputs_sha256": {"source.json": hashlib.sha256(b"original").hexdigest()}
    }
    owner.validate_generation_inputs(tmp_path, generation)
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="generation input"):
        owner.validate_generation_inputs(tmp_path, generation)
    with pytest.raises(ValueError, match="generation input"):
        owner.validate_generation_inputs(
            tmp_path, {"inputs_sha256": {"../escape": "0" * 64}}
        )


def test_reference_producer_checks_candidate_against_original_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.ci.atlas_browser import (
        nordic_source_candidate as generator,
    )

    from .test_nordic_source_candidate import nordic_repository

    owner = import_module(
        "bijux_pollenomics_dev.ci.atlas_browser.nordic_candidate_custody"
    )
    nordic_repository(tmp_path)
    monkeypatch.setattr(generator, "observed_source_inputs", lambda _repo: {})
    candidate = tmp_path / "artifacts/candidate"
    generator.generate_nordic_source_candidate(tmp_path, candidate)
    sealed = owner.prepare_candidate(
        tmp_path, candidate, tmp_path / "artifacts/reference"
    )
    assert sealed["generation.json"] == (candidate / "generation.json").read_bytes()
    required = owner.required_candidate_assets(sealed)
    assert "index.html" in required
    assert sum(".atlas-nodes." in name for name in required) == 8
    assert any(".atlas-details." in name for name in required)
    asset = next(candidate.glob("*.atlas-details.*.js"))
    asset.write_bytes(asset.read_bytes() + b"modified")
    with pytest.raises(ValueError, match="candidate asset closure"):
        owner.prepare_candidate(
            tmp_path, candidate, tmp_path / "artifacts/reference-modified"
        )


def test_captured_transport_returns_immutable_bytes_on_repeated_requests() -> None:
    root = Path(__file__).resolve().parents[4]
    module = (
        root
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_captured_transport.mjs"
    ).as_uri()
    script = f"""import {{captureAssets}} from {json.dumps(module)};
const source={{"index.html":Buffer.from("original")}};
const assets=captureAssets(source); source["index.html"].fill(0);
const first=assets.serve("index.html"); first.fill(0);
const second=assets.serve("index.html");
if(second.toString()!=="original")throw Error("captured bytes mutated");
if(assets.serve("../index.html")!==null)throw Error("unsafe path accepted");
console.log(JSON.stringify(assets.served()));"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    assert json.loads(result.stdout) == {
        "index.html": hashlib.sha256(b"original").hexdigest()
    }


def test_output_must_be_absent_and_owned_by_repository(tmp_path: Path) -> None:
    owner = import_module(
        "bijux_pollenomics_dev.ci.atlas_browser.nordic_candidate_custody"
    )
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    existing = artifacts / "existing"
    existing.mkdir()
    with pytest.raises(ValueError, match="absent repository artifact"):
        owner.validate_output_destination(tmp_path, existing)
    with pytest.raises(ValueError, match="absent repository artifact"):
        owner.validate_output_destination(tmp_path, tmp_path / "outside")


def test_v2_receipt_rejects_stale_generation_and_unserved_content() -> None:
    owner = import_module(
        "bijux_pollenomics_dev.ci.atlas_browser.nordic_candidate_custody"
    )
    records = [
        {"record_id": f"record-{i}", "chronology": {"records": [{}]}} for i in range(8)
    ]
    generation = {
        "source_atlas_build_id": "source",
        "candidate_build_id": "candidate",
        "source_records": records,
    }
    generation_bytes = json.dumps(generation).encode()
    files = {
        "generation.json": generation_bytes,
        "index.html": b"index",
        "x.atlas-nodes.js": b"nodes",
        "x.atlas-details.js": b"details",
    }
    receipt = {
        "schema_version": "atlas-nordic-source-browser-verification.v2",
        "status": "PASS",
        "runtime_errors": [],
        "candidate_generation_sha256": hashlib.sha256(generation_bytes).hexdigest(),
        "candidate_build_id": "candidate",
        "source_atlas_build_id": "source",
        "served_files_sha256": {
            k: hashlib.sha256(v).hexdigest()
            for k, v in files.items()
            if k != "generation.json"
        },
        "chronology_tables": [
            {
                "width": w,
                "record_id": r["record_id"],
                "rows": 1,
                "all_source_cells_equal": True,
            }
            for w in (390, 1440)
            for r in records
        ],
    }
    required = {"index.html", "x.atlas-nodes.js", "x.atlas-details.js"}
    owner.validate_browser_receipt(files, receipt, required)
    bad = dict(receipt, candidate_generation_sha256="0" * 64)
    with pytest.raises(ValueError, match="browser receipt"):
        owner.validate_browser_receipt(files, bad, required)
    bad = dict(receipt, served_files_sha256={"index.html": "0" * 64})
    with pytest.raises(ValueError, match="browser receipt"):
        owner.validate_browser_receipt(files, bad, required)


def test_verifier_refuses_existing_output_before_browser(tmp_path: Path) -> None:
    owner = import_module(
        "bijux_pollenomics_dev.ci.atlas_browser.nordic_candidate_custody"
    )
    output = tmp_path / "artifacts/existing"
    output.mkdir(parents=True)
    with pytest.raises(ValueError, match="absent repository artifact"):
        owner.run(
            tmp_path, tmp_path / "candidate", output, tmp_path / "browser", "0" * 64
        )


def test_failed_second_receipt_write_leaves_no_final_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = import_module(
        "bijux_pollenomics_dev.ci.atlas_browser.nordic_candidate_custody"
    )
    staging = tmp_path / "staging"
    staging.mkdir()
    destination = tmp_path / "result"
    original = owner.OwnedTreeWriter.write_bytes

    def fail_log(writer: object, name: str, data: bytes) -> None:
        if name == "browser.log":
            raise OSError("injected log failure")
        original(writer, name, data)

    monkeypatch.setattr(owner.OwnedTreeWriter, "write_bytes", fail_log)
    with pytest.raises(OSError, match="injected log failure"):
        owner.publish_result(destination, staging, b"receipt", b"log")
    assert not destination.exists()


def test_browser_start_failure_never_publishes_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.ci.atlas_browser import (
        nordic_source_candidate as generator,
    )

    from .test_nordic_source_candidate import nordic_repository

    owner = import_module(
        "bijux_pollenomics_dev.ci.atlas_browser.nordic_candidate_custody"
    )
    nordic_repository(tmp_path)
    monkeypatch.setattr(generator, "observed_source_inputs", lambda _repo: {})
    candidate = tmp_path / "artifacts/candidate"
    generator.generate_nordic_source_candidate(tmp_path, candidate)
    actual = Path(__file__).resolve().parents[4]
    scripts = Path(
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser"
    )
    for name in ("nordic-country-captured.mjs", "nordic_captured_transport.mjs"):
        target = tmp_path / scripts / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(actual / scripts / name, target)
    output = tmp_path / "artifacts/browser-result"
    digest = hashlib.sha256((candidate / "generation.json").read_bytes()).hexdigest()
    with pytest.raises(RuntimeError, match="browser verifier failed"):
        owner.run(tmp_path, candidate, output, tmp_path / "missing-browser", digest)
    assert not output.exists()


def test_completed_result_is_attached_without_replacing_existing_output(
    tmp_path: Path,
) -> None:
    owner = import_module(
        "bijux_pollenomics_dev.ci.atlas_browser.nordic_candidate_custody"
    )
    staging = tmp_path / "staging"
    staging.mkdir()
    result = tmp_path / "result"
    owner.publish_result(result, staging, b"receipt", b"log")
    assert (result / "receipt.json").read_bytes() == b"receipt"
    assert (result / "browser.log").read_bytes() == b"log"
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises((FileExistsError, ValueError)):
        owner.publish_result(result, other, b"replacement", b"replacement")
    assert (result / "receipt.json").read_bytes() == b"receipt"
