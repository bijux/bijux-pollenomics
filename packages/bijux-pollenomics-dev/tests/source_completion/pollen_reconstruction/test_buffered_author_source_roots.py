"""Keep buffered-pollen child imports bound to the candidate workspace."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

REPOSITORY = Path(__file__).resolve().parents[5]
REPLAY = (
    REPOSITORY / "docs/report/pollen-reconstruction/author-buffered-pollen/replay.py"
)


def test_replay_children_prefer_candidate_host_and_lra(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    specification = importlib.util.spec_from_file_location(
        "buffered_pollen_replay", REPLAY
    )
    assert specification is not None and specification.loader is not None
    replay = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(replay)
    candidate = tmp_path / "candidate"
    family = candidate / "family"
    family.mkdir(parents=True)
    source = tmp_path / "source"
    for name in ("author", "reference"):
        (source / name).mkdir(parents=True)
    source_bytes = b"source fixture"
    (source / "snapshot-manifest.json").write_bytes(source_bytes)
    (family / "manifest.json").write_text(
        json.dumps(
            {
                "producer_sha256": {},
                "private_source_manifest_sha256": hashlib.sha256(
                    source_bytes
                ).hexdigest(),
            }
        )
    )
    (candidate / "artifacts").mkdir()
    monkeypatch.setattr(replay, "REPOSITORY", candidate)
    monkeypatch.setattr(replay, "FAMILY", family)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "replay",
            "--source-root",
            str(source),
            "--output",
            str(candidate / "artifacts/products"),
        ],
    )
    captured: dict[str, str] = {}

    class ChildCaptured(Exception):
        pass

    def capture(_arguments: list[str], environment: dict[str, str]) -> None:
        captured.update(environment)
        raise ChildCaptured

    monkeypatch.setattr(replay, "_run", capture)
    with pytest.raises(ChildCaptured):
        replay.main()
    roots = [
        candidate / Path(path).relative_to(REPOSITORY)
        for path in captured["PYTHONPATH"].split(os.pathsep)
    ]
    for package in (
        "bijux-pollenomics-dev",
        "bijux-pollenomics",
        "bijux-pollenomics-lra",
    ):
        (candidate / "packages" / package / "src").mkdir(parents=True)
    foreign = tmp_path / "foreign-site-packages"
    for distribution, package in (
        ("bijux-pollenomics", "bijux_pollenomics"),
        ("bijux-pollenomics-lra", "bijux_pollenomics_lra"),
    ):
        for root, identity in (
            (candidate / "packages" / distribution / "src", "candidate"),
            (foreign, "foreign"),
        ):
            module = root / package
            module.mkdir(parents=True)
            (module / "__init__.py").write_text(f"SOURCE = {identity!r}\n")
    captured["PYTHONPATH"] = os.pathsep.join(str(root) for root in roots)
    probe = (
        "import sys,json; sys.path.append(sys.argv[1]); "
        "import bijux_pollenomics,bijux_pollenomics_lra; "
        "print(json.dumps([bijux_pollenomics.SOURCE,bijux_pollenomics_lra.SOURCE]))"
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", probe, str(foreign)],
        cwd=candidate,
        env=captured,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert json.loads(result.stdout) == ["candidate", "candidate"]
