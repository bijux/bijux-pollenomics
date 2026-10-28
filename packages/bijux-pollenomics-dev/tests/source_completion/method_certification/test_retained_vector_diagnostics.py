"""Exercise writer confinement and refusal before any retained-vector calculation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.method_certification import (
    retained_vector_diagnostics as producer,
)


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    (root / "artifacts").mkdir(parents=True)
    return root


@pytest.mark.parametrize("mode", ["existing", "traversal", "alias"])
def test_output_refuses_before_calculation(tmp_path: Path, mode: str) -> None:
    root = _root(tmp_path)
    output = root / "artifacts/result"
    if mode == "existing":
        output.mkdir()
    elif mode == "traversal":
        output = root / "artifacts/../escaped"
    else:
        (root / "artifacts/alias").symlink_to(
            root / "artifacts", target_is_directory=True
        )
        output = root / "artifacts/alias/result"
    with pytest.raises(ReportRebuildError):
        producer.build(root, output)
    assert not (root / "escaped").exists()


def test_source_origin_refuses_different_repository(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with pytest.raises(ValueError, match="selected repository writer"):
        producer._snapshot(root)


@pytest.mark.parametrize(
    "mode", ["passed", "threshold_failure", "review_failure", "source_change"]
)
def test_publication_requires_review_and_stable_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    root = _root(tmp_path)
    protocol = root / "protocol.json"
    protocol.write_text("{}")
    calls = 0

    def snapshot(repository: Path) -> tuple[Path, bytes]:
        nonlocal calls
        assert repository == root
        calls += 1
        return (
            protocol,
            b"changed" if mode == "source_change" and calls == 2 else b"source",
        )

    def report(repository: Path, selected: Path) -> dict[str, Any]:
        assert repository == root and selected == protocol
        return {"status": "failed" if mode == "threshold_failure" else "passed"}

    def review(repository: Path, path: Path, selected: Path) -> dict[str, Any]:
        assert repository == root and selected == protocol and path.is_file()
        assert path.read_text() == '{\n  "status": "passed"\n}\n'
        if mode == "review_failure":
            raise ValueError("controlled scalar review refusal")
        return {"status": "passed", "report_sha256": "controlled"}

    monkeypatch.setattr(producer, "_snapshot", snapshot)
    monkeypatch.setattr(producer, "build_diagnostics", report)
    monkeypatch.setattr(producer, "verify", review)
    output = root / "artifacts/products"
    if mode != "passed":
        with pytest.raises(ValueError):
            producer.build(root, output)
        assert not output.exists()
    else:
        producer.build(root, output)
        assert {path.name for path in output.iterdir()} == {
            "retained-vector-diagnostics.json",
            "retained-vector-review.json",
        }
    assert not any(
        path.name.startswith(".retained-vectors-") for path in output.parent.iterdir()
    )
