"""Recorded-gate specification binding tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from bijux_pollenomics.provenance import ReleaseEvidenceError, hash_repository_object

from ..support import _artifacts, _build, _digest, _json_digest, _rewrite_gate_record


@pytest.mark.parametrize(
    "attack",
    [
        "argv",
        "environment",
        "empty-inputs",
        "substituted-input",
        "producer",
        "root",
        "runtime",
    ],
)
def test_coherently_rehashed_gate_cannot_replace_trusted_specification(
    tmp_path: Path, attack: str
) -> None:
    artifacts = _artifacts(tmp_path)

    def mutate(record: dict[str, object]) -> None:
        if attack == "argv":
            record["argv"] = ["true"]
            record["command_digest"] = _json_digest(record["argv"])
        elif attack == "environment":
            record["environment"] = {"PATH": "/attacker"}
            record["environment_digest"] = _json_digest(record["environment"])
        elif attack == "empty-inputs":
            record["inputs"] = []
            record["input_digest"] = _json_digest([])
        elif attack == "substituted-input":
            alternate = tmp_path / "alternate-input.txt"
            alternate.write_text("attacker input\n", encoding="utf-8")
            inputs = [
                {
                    "path": "alternate-input.txt",
                    **hash_repository_object(tmp_path, "alternate-input.txt"),
                }
            ]
            record["inputs"] = inputs
            record["input_digest"] = _json_digest(inputs)
        elif attack == "producer":
            producer = {"identity": "attacker", "version": "1"}
            record["producer"] = {**producer, "digest": _json_digest(producer)}
        elif attack == "root":
            record["repository_root_digest"] = _json_digest("/relocated")
        else:
            record["specification_digest"] = _json_digest(
                {"runtime_identity": {"command_executable_sha256": _digest(b"fake")}}
            )

    _rewrite_gate_record(tmp_path, artifacts, mutate)

    with pytest.raises(ReleaseEvidenceError):
        _build(tmp_path, artifacts=artifacts)


def test_coherently_rehashed_producer_source_substitution_is_refused(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)

    def mutate(record: dict[str, object]) -> None:
        source_files = [
            {
                "module": "bijux_pollenomics.provenance.gates",
                "sha256": _digest(b"substituted producer"),
                "byte_count": len(b"substituted producer"),
            }
        ]
        producer_content = {
            "identity": "bijux-pollenomics.recorded-gate",
            "version": "4",
            "source_files": source_files,
            "source_digest": _json_digest(source_files),
        }
        record["producer"] = {
            **producer_content,
            "digest": _json_digest(producer_content),
        }

    _rewrite_gate_record(tmp_path, artifacts, mutate)

    with pytest.raises(ReleaseEvidenceError, match="producer identity mismatch"):
        _build(tmp_path, artifacts=artifacts)
