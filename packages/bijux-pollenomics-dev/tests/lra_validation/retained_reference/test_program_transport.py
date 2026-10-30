"""Keep historical oracle programmes in authenticated Git-backed bundle inventory."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.lra_reference.contracts import ReferenceRefusal
from bijux_pollenomics_dev.ci.lra_reference.evidence import file_inventory
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import (
    index as source_index,
)
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    environment,
    git_executable,
)
from bijux_pollenomics_dev.lra_validation.retained_reference.identity import (
    _source_transport,
)

PREFIX = "data/method-certification/source-locked-linux-r/reference-bundle"
ORACLE = "oracle/oracle.R"
DOMAIN = {
    "source-domains/r_support.R",
    "source-domains/run_source_domains.py",
    "source-domains/source_domains.R",
    "source-lock.json",
}


def _identity(body: bytes) -> dict[str, Any]:
    return {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}


def _fixture(
    root: Path, monkeypatch: pytest.MonkeyPatch, kind: str = "oracle"
) -> tuple[Path, dict[str, Any], dict[str, bytes]]:
    import subprocess

    executable = str(git_executable())

    def git(*arguments: str) -> str:
        return subprocess.run(
            [executable, "--no-replace-objects", "-C", str(root), *arguments],
            env=environment(),
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()

    git("init", "--initial-branch=main")
    bodies = {
        name: ("# invented inert member: " + name + "\n").encode()
        for name in DOMAIN | {ORACLE}
    }
    if kind == "extra":
        bodies["oracle/other.R"] = b"# invented extra programme; never executed\n"
    pairs = []
    for number, (name, body) in enumerate(sorted(bodies.items())):
        canonical = "packages/owned-witness/member-" + str(number)
        source = root / canonical
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(body)
        if name != ORACLE or kind != "legacy":
            pairs.append([name, canonical])
    git("add", "--", "packages/owned-witness")
    git(
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-m",
        "retain invented metadata witnesses",
    )
    revision = git("rev-parse", "HEAD")
    entries = [
        [canonical, git("rev-parse", revision + ":" + canonical)]
        for _, canonical in pairs
    ]
    members = {name: _identity(body) for name, body in bodies.items()}
    members["observed.csv"] = _identity(b"a,b\n1,2\n")
    capture = {
        "schema_version": "invented-owned-member-catalogue.v1",
        "members": members,
    }
    capture_raw = (json.dumps(capture, sort_keys=True) + "\n").encode()
    descriptor = {
        "schema_version": "git-retained-source.v1",
        "capture": {"name": "certificate.json", **_identity(capture_raw)},
        "historical_native_epochs": ["b" * 40],
        "source_revision_correspondence": [
            {"historical_source_commit": revision, "source_revision": revision}
        ],
        "git_groups": [
            {
                "historical_source_commit": revision,
                "source_revision": revision,
                "member_count": len(pairs),
                "git_entries_sha256": hashlib.sha256(
                    json.dumps(sorted(entries), separators=(",", ":")).encode()
                ).hexdigest(),
                "paths": sorted(pairs),
            }
        ],
        "generated_members": [],
        "rewritten_source_epoch_executed": False,
    }
    descriptor_raw = (json.dumps(descriptor, sort_keys=True) + "\n").encode()
    bundle = root / PREFIX
    bundle.mkdir(parents=True)
    (bundle / "certificate.json").write_bytes(capture_raw)
    (bundle / "source-transport.json").write_bytes(descriptor_raw)
    (bundle / "observed.csv").write_bytes(b"a,b\n1,2\n")
    if kind == "legacy":
        oracle = bundle / ORACLE
        oracle.parent.mkdir(parents=True)
        oracle.write_bytes(bodies[ORACLE])
    registry = {
        "schema_version": "retained-source-index.v1",
        "capsules": {
            PREFIX: {"descriptor": "source-transport.json", **_identity(descriptor_raw)}
        },
        "source_revisions": {},
    }
    registry_raw = (json.dumps(registry, sort_keys=True) + "\n").encode()
    path = root / source_index.INDEX_PATH
    path.parent.mkdir(parents=True)
    path.write_bytes(registry_raw)
    monkeypatch.setattr(
        source_index, "INDEX_SHA256", hashlib.sha256(registry_raw).hexdigest()
    )
    monkeypatch.setattr(source_index, "INDEX_BYTES", len(registry_raw))
    files = {
        name: {"sha256": row["sha256"], "byte_count": row["bytes"]}
        for name, row in members.items()
    }
    files["certificate.json"] = {
        "sha256": hashlib.sha256(capture_raw).hexdigest(),
        "byte_count": len(capture_raw),
    }
    return bundle, {"files": files}, bodies


def test_original_oracle_is_read_through_real_source_capsule_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, profile, bodies = _fixture(tmp_path, monkeypatch)
    source = _source_transport(bundle, profile)
    assert isinstance(source, SourceCapsule)
    assert source.detached == frozenset(DOMAIN | {ORACLE})
    assert file_inventory(bundle, source_transport=source) == profile["files"]
    assert source.read_source(ORACLE) == bodies[ORACLE]
    assert not (bundle / ORACLE).exists()
    source.fresh()


@pytest.mark.parametrize("kind", ["legacy", "extra"])
@pytest.mark.parametrize("boundary", ["inventory", "identity"])
def test_only_exact_five_historical_members_can_use_bundle_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str, boundary: str
) -> None:
    # Validate the real accepted oracle fixture before constructing each refusal.
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    root, profile, _ = _fixture(baseline, monkeypatch)
    accepted = _source_transport(root, profile)
    assert isinstance(accepted, SourceCapsule)
    assert file_inventory(root, source_transport=accepted) == profile["files"]
    rejected = tmp_path / "rejected"
    rejected.mkdir()
    bundle, profile, _ = _fixture(rejected, monkeypatch, kind)
    if boundary == "identity":
        with pytest.raises(ValueError, match="source transport population differs"):
            _source_transport(bundle, profile)
    else:
        from bijux_pollenomics_dev.ci.report_rebuild.retained_source import (
            validated_descriptor,
        )

        members = {
            name: {"sha256": row["sha256"], "bytes": row["byte_count"]}
            for name, row in profile["files"].items()
            if name != "certificate.json"
        }
        source = validated_descriptor(rejected, PREFIX, members)
        with pytest.raises(ReferenceRefusal, match="transport scope differs"):
            file_inventory(bundle, source_transport=source)


def test_physically_restored_oracle_is_refused_after_real_inventory_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle, profile, bodies = _fixture(tmp_path, monkeypatch)
    source = _source_transport(bundle, profile)
    assert isinstance(source, SourceCapsule)
    assert file_inventory(bundle, source_transport=source) == profile["files"]
    path = bundle / ORACLE
    path.parent.mkdir(parents=True)
    path.write_bytes(bodies[ORACLE])
    with pytest.raises(ReferenceRefusal, match="physical projection differs"):
        file_inventory(bundle, source_transport=source)
