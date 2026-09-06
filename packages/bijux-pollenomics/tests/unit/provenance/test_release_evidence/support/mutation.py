"""Controlled fixture policy and gate-record mutation."""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.provenance import ArtifactInput

from .artifacts import _refresh_validation_artifact
from .codec import _canonical_json, _digest, _json_digest


def _rewrite_gate_record(
    root: Path,
    artifacts: list[ArtifactInput],
    transform: Callable[[dict[str, object]], None],
) -> None:
    path = root / "artifacts/gate-evidence/quality.json"
    record = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
    transform(record)
    content = {key: value for key, value in record.items() if key != "record_digest"}
    record["record_digest"] = _json_digest(content)
    path.write_bytes(_canonical_json(record) + b"\n")
    _refresh_validation_artifact(root, artifacts)


def _rewrite_fixture_policy(
    root: Path,
    artifacts: list[ArtifactInput],
    transform: Callable[[dict[str, object]], None],
) -> None:
    path = root / "configs/release_evidence_policy.json"
    policy = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
    old_digest = _digest(path.read_bytes())
    transform(policy)
    path.write_bytes(_canonical_json(policy) + b"\n")
    new_digest = _digest(path.read_bytes())
    for index, artifact in enumerate(artifacts):
        updates: dict[str, object] = {}
        if artifact.identity == "release-evidence-policy":
            updates["output_digest"] = new_digest
        if artifact.role in {"generated_output", "validation_result"}:
            updates["config_digests"] = tuple(
                new_digest if digest == old_digest else digest
                for digest in artifact.config_digests
            )
        if updates:
            artifacts[index] = ArtifactInput(**{**artifact.__dict__, **updates})
