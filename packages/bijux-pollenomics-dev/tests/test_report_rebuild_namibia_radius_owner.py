"""Check the retained Namibia radius producer's qualified input route."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.source_completion.vegetation import (
    namibia_radius_sensitivity,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/radius-review.json")
POLLEN = "PANGAEA.931033.tab"
VEGETATION = "PANGAEA.931035.tab"
SOURCE_ID = "vegetation/namibia-modern-pollen-vegetation"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path, dict[str, Path]]:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    root = tmp_path / "source-store"
    directory = root / SOURCE_ID
    directory.mkdir(parents=True)
    descriptor_file = repository / DESCRIPTOR
    descriptor_file.parent.mkdir(parents=True)
    descriptor_file.write_text(
        json.dumps(
            {
                "source_id": SOURCE_ID,
                "files": [
                    {
                        "path": POLLEN,
                        "sha256": "a" * 64,
                        "columns": ["Event", "Aca [#]"],
                    },
                    {
                        "path": VEGETATION,
                        "sha256": "b" * 64,
                        "columns": ["Event", "Ring sect radius [m]"],
                    },
                ],
            }
        )
    )
    custody = directory / "source_manifest.json"
    custody.write_text("reviewed receipt\n")
    sources = {name: directory / name for name in (POLLEN, VEGETATION)}
    for source in sources.values():
        source.write_text("synthetic publisher row\n")
    inputs = {
        DESCRIPTOR.as_posix(): descriptor_file,
        f"external/{SOURCE_ID}/source_manifest.json": custody,
        **{f"external/{SOURCE_ID}/{name}": path for name, path in sources.items()},
    }
    qualified = QualifiedReportSources(directory, inputs, "c" * 64)
    monkeypatch.setattr(
        namibia_radius_sensitivity,
        "validated_external_report_sources",
        lambda *_args: qualified,
    )
    source_script = repository / namibia_radius_sensitivity.SOURCE_REPLAY
    source_script.parent.mkdir(parents=True)
    source_script.write_text(
        f"SOURCES = {repr({POLLEN: 'a' * 64, VEGETATION: 'b' * 64})}\n"
        "POLLEN_COLUMNS = ('Event', 'Aca [#]')\n"
        "VEGETATION_COLUMNS = ('Event', 'Ring sect radius [m]')\n"
    )
    radius_script = repository / namibia_radius_sensitivity.RADIUS_REPLAY
    radius_script.write_text(
        "import replay\nfrom pathlib import Path\nimport sys\n"
        "def main():\n"
        "    args = sys.argv\n"
        "    output = Path(args[args.index('--output-dir') + 1])\n"
        "    source = Path(args[args.index('--source-dir') + 1])\n"
        "    output.mkdir(parents=True)\n"
        "    (output / 'radius-sensitivity.csv').write_text(str(source) + '\\n')\n"
        "    (output / 'radius-sensitivity.json').write_text(replay.__file__ + '\\n')\n"
    )
    monkeypatch.setattr(
        namibia_radius_sensitivity, "SOURCE_REPLAY_SHA256", _sha(source_script)
    )
    monkeypatch.setattr(
        namibia_radius_sensitivity, "RADIUS_REPLAY_SHA256", _sha(radius_script)
    )
    return repository, root, radius_script, inputs


def _argv(repository: Path, root: Path, output: Path) -> list[str]:
    return [
        "--repository",
        str(repository),
        "--source-root",
        str(root),
        "--source-descriptor",
        DESCRIPTOR.as_posix(),
        "--output",
        str(output),
    ]


def test_wrapper_loads_only_pinned_local_replay_and_restores_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, root, _, _ = _fixture(tmp_path, monkeypatch)
    foreign = ModuleType("replay")
    foreign.__file__ = "/unrelated/replay.py"
    monkeypatch.setitem(sys.modules, "replay", foreign)
    output = repository / "artifacts/source-products"
    assert namibia_radius_sensitivity.main(_argv(repository, root, output)) == 0
    assert (output / "radius-sensitivity.csv").read_text() == str(
        root / SOURCE_ID
    ) + "\n"
    assert (output / "radius-sensitivity.json").read_text() == str(
        repository / namibia_radius_sensitivity.SOURCE_REPLAY
    ) + "\n"
    assert sys.modules["replay"] is foreign
    with pytest.raises(ReportRebuildError, match="absent"):
        namibia_radius_sensitivity.main(_argv(repository, root, output))


@pytest.mark.parametrize("script", ["source", "radius"])
def test_changed_retained_script_refuses_before_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, script: str
) -> None:
    repository, root, radius_path, _ = _fixture(tmp_path, monkeypatch)
    path = (
        repository / namibia_radius_sensitivity.SOURCE_REPLAY
        if script == "source"
        else radius_path
    )
    path.write_text("raise AssertionError('unreviewed producer ran')\n")
    output = repository / "artifacts/source-products"
    with pytest.raises(ReportRebuildError, match="replay read set changed"):
        namibia_radius_sensitivity.main(_argv(repository, root, output))
    assert not output.exists()


def test_qualified_identity_is_rechecked_after_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, root, _, inputs = _fixture(tmp_path, monkeypatch)
    calls = 0

    def change_after(*_args: object) -> QualifiedReportSources:
        nonlocal calls
        calls += 1
        return QualifiedReportSources(
            root / SOURCE_ID, inputs, ("c" if calls == 1 else "d") * 64
        )

    monkeypatch.setattr(
        namibia_radius_sensitivity, "validated_external_report_sources", change_after
    )
    with pytest.raises(ReportRebuildError, match="source identity changed"):
        namibia_radius_sensitivity.main(
            _argv(repository, root, repository / "artifacts/source-products")
        )
    assert calls == 2


def test_artifact_path_traversal_refuses_without_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, root, _, _ = _fixture(tmp_path, monkeypatch)
    escaped = repository / "artifacts/../escaped"
    with pytest.raises(ReportRebuildError, match="not canonical"):
        namibia_radius_sensitivity.main(_argv(repository, root, escaped))
    assert not (repository / "escaped").exists()
