"""Direct contracts for source-bound local Linux R evidence."""

from __future__ import annotations

import csv
from hashlib import sha256 as hash_bytes
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.lra_reference.contracts import ReferenceRefusal
from bijux_pollenomics_dev.ci.lra_reference.evidence import (
    file_inventory,
    validate_oracle,
)
from bijux_pollenomics_dev.ci.lra_reference.profiles import validate_source_domains
from bijux_pollenomics_dev.ci.lra_reference.sources import sha256
from bijux_pollenomics_dev.lra_validation import linux_reference

ROOT = next(
    parent
    for parent in Path(__file__).parents
    if (parent / "configs/pytest.ini").is_file()
)


def test_container_uses_read_only_inputs_and_bounded_offline_execution(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    runtime = tmp_path / "runtime"
    provision = tmp_path / "provision"
    output = tmp_path / "output"
    image = "sha256:" + "a" * 64
    argv = linux_reference._container_command(
        repository, output, runtime, provision, image
    )
    assert argv[:5] == [
        "docker",
        "run",
        "--rm",
        "--name",
        "bijux-pollenomics-linux-r-oracle-aaaaaaaaaaaa",
    ]
    assert argv[argv.index("--network") + 1] == "none"
    assert argv[argv.index("--cpus") + 1] == "1"
    assert argv[argv.index("--memory") + 1] == "4g"
    mounts = [argv[index + 1] for index, word in enumerate(argv) if word == "--mount"]
    assert mounts == [
        f"type=bind,source={repository},target=/repo,readonly",
        f"type=bind,source={runtime},target=/output,readonly",
        f"type=bind,source={provision},target=/provision,readonly",
        f"type=bind,source={output},target=/run",
    ]
    assert "R_LIBS_USER=/provision/library" in argv
    assert "OMP_NUM_THREADS=1" in argv


def test_core_raw_denominator_rejects_missing_r_vector(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "oracle"
    root.mkdir()
    (root / "report.json").write_text(json.dumps({"prepared_cases": 43}) + "\n")
    manifest = [{"id": f"C{index:04d}", "values": 1} for index in range(43)]
    (root / "case_manifest.json").write_text(json.dumps(manifest) + "\n")
    with (root / "R_case_status.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "status"])
        writer.writeheader()
        writer.writerows({"id": row["id"], "status": "completed"} for row in manifest)
    for row in manifest[:-1]:
        (root / f"{row['id']}.csv").write_text("kind,value\nnumeric,1\n")
    monkeypatch.setattr(
        linux_reference,
        "validate_oracle",
        lambda *args, **kwargs: 43,
    )
    with pytest.raises(ReferenceRefusal, match="raw vector is missing"):
        linux_reference._validate_core_raw(root, "a" * 64)


def test_preflight_refusal_never_becomes_release_certificate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("repository", "runtime", "provision", "sources"):
        (tmp_path / name).mkdir()

    def invalid_runtime(*args: Any) -> dict[str, Any]:
        raise ReferenceRefusal("Reused R runtime bytes differ")

    monkeypatch.setattr(linux_reference, "_verify_reused_runtime", invalid_runtime)
    report = linux_reference.execute(
        repository=tmp_path / "repository",
        output=tmp_path / "run",
        retained=tmp_path / "retained",
        runtime_tree=tmp_path / "runtime",
        provision_tree=tmp_path / "provision",
        source_cache=tmp_path / "sources",
        image_id_path=tmp_path / "missing-image-id",
        dockerfile=tmp_path / "missing-Dockerfile",
    )
    assert report["status"] == "refused"
    assert report["release_certificate"] is False
    assert report["linux_r_executed"] is False
    assert "Reused R runtime bytes differ" in str(report["error"])
    assert json.loads((tmp_path / "retained/report.json").read_text()) == report


def test_retained_linux_r_vectors_satisfy_exact_local_profiles() -> None:
    root = ROOT / "docs/report/method-certification/linux-r-oracle"
    report_bytes = (root / "report.json").read_bytes()
    report = json.loads(report_bytes)
    context = json.loads((root / "context.json").read_text())
    assert context["report_sha256"] == hash_bytes(report_bytes).hexdigest()
    source_set = report["executed_source_files"]
    assert context["executed_source_file_count"] == len(source_set)
    assert (
        context["executed_source_set_sha256"]
        == hash_bytes(
            json.dumps(source_set, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    assert context["head_during_execution_independently_verified"] is False
    assert context["head_changed_before_annotation"] is True
    assert report["status"] == "passed_local_linux_oracle"
    assert report["release_certificate"] is False
    assert report["release_refusal_codes"] == [
        "local_linux_arm_is_not_locked_ubuntu_x86_64_ci",
        "github_run_attempt_and_artifact_absent",
    ]
    assert report["core_cases"] == {"attempted": 43, "passed": 43}
    assert report["source_domain_cases"] == {"attempted": 23, "passed": 23}
    assert report["source_lock"]["lock_sha256"] == sha256(
        ROOT / "configs/ci/lra-r-source-lock.v1.json"
    )
    raw = {name: file_inventory(root / name) for name in ("oracle", "source-domains")}
    assert raw == report["raw_files"]
    assert linux_reference._inventory_hash(raw) == report["raw_inventory_sha256"]
    reference = report["source_lock"]["reference_sha256"]
    core = json.loads((root / "oracle/report.json").read_text())
    manifest = json.loads((root / "oracle/case_manifest.json").read_text())
    assert validate_oracle(core, manifest, reference, expected_core_cases=43) == 43
    assert (
        validate_source_domains(root / "source-domains", reference)["passed_cases"]
        == 23
    )
