"""The qualified scorer must retain source, freeze and two-output boundaries."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support import (
    qualified_author_score as subject,
)


@dataclass(frozen=True)
class Case:
    repository: Path
    source_root: Path
    replay: Path
    frozen: Path
    output: Path
    source_sha256: str


@pytest.fixture
def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Case:
    repository = tmp_path / "repository"
    frozen = Path("docs/report/age-score")
    source = repository / frozen / "replay.py"
    source.parent.mkdir(parents=True)
    for name in subject.FROZEN:
        (source.parent / name).write_bytes(name.encode())
    source.write_text(
        "from pathlib import Path\n"
        f"LOOKUP = Path({subject.LOOKUP!r})\n"
        "def freeze(*args):\n"
        "    raise AssertionError('prediction freeze entered')\n"
        "def score(repository, prepared, author_source_root):\n"
        "    (prepared / 'report.json').write_bytes(b'report')\n"
        "    (prepared / 'scores.csv').write_bytes(b'scores')\n",
        encoding="utf-8",
    )
    (repository / "artifacts/output").mkdir(parents=True)
    source_root = tmp_path / "external-source"
    directory = source_root / subject.SOURCE_ID
    lookup = directory / subject.LOOKUP
    lookup.parent.mkdir(parents=True)
    lookup.write_bytes(b"author lookup")
    inputs = {f"external/{subject.SOURCE_ID}/{subject.LOOKUP}": lookup}
    inputs.update({f"external/source-{n:03d}": lookup for n in range(194)})
    qualified = QualifiedReportSources(directory, inputs, subject.DESCRIPTOR_SHA256)
    monkeypatch.setattr(
        subject, "validated_external_report_sources", lambda *_: qualified
    )
    return Case(
        repository,
        source_root,
        frozen / "replay.py",
        frozen,
        repository / "artifacts/output/source-products",
        hashlib.sha256(source.read_bytes()).hexdigest(),
    )


def invoke(
    case: Case, *, output: Path | None = None, digest: str | None = None
) -> None:
    subject.run(
        case.repository,
        case.source_root,
        subject.DESCRIPTOR,
        case.output if output is None else output,
        replay=case.replay,
        replay_sha256=case.source_sha256 if digest is None else digest,
        frozen=case.frozen,
    )


def test_exact_score_outputs_preserve_frozen_inputs(case: Case) -> None:
    before = {
        name: (case.repository / case.frozen / name).read_bytes()
        for name in subject.FROZEN
    }
    invoke(case)
    assert {path.name for path in case.output.iterdir()} == set(subject.SCORED)
    assert (case.output / "report.json").read_bytes() == b"report"
    assert (case.output / "scores.csv").read_bytes() == b"scores"
    assert {
        name: (case.repository / case.frozen / name).read_bytes()
        for name in subject.FROZEN
    } == before


def test_outside_artifact_output_refused(case: Case) -> None:
    with pytest.raises(ReportRebuildError, match="artifact"):
        invoke(case, output=case.repository / "docs/report/score")


def test_changed_original_scorer_refused(case: Case) -> None:
    with pytest.raises(ValueError, match="implementation differs"):
        invoke(case, digest="0" * 64)
    assert not case.output.exists()


def test_extra_staged_output_refused(case: Case) -> None:
    source = case.repository / case.replay
    source.write_text(
        source.read_text() + "    (prepared / 'extra.json').write_bytes(b'extra')\n"
    )
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="stage file population differs"):
        invoke(case, digest=digest)
    assert not case.output.exists()


def test_undeclared_descriptor_refused(case: Case) -> None:
    with pytest.raises(ValueError, match="descriptor differs"):
        subject.run(
            case.repository,
            case.source_root,
            Path("configs/ci/other-source.json"),
            case.output,
            replay=case.replay,
            replay_sha256=case.source_sha256,
            frozen=case.frozen,
        )
    assert not case.output.exists()


def test_symlinked_original_scorer_refused(case: Case) -> None:
    source = case.repository / case.replay
    original = source.with_name("original.py")
    source.rename(original)
    source.symlink_to(original.name)
    with pytest.raises(Exception, match="regular|real"):
        invoke(case)
    assert not case.output.exists()


def test_staged_frozen_input_mutation_refused(case: Case) -> None:
    source = case.repository / case.replay
    source.write_text(
        source.read_text()
        + "    (prepared / 'protocol.json').write_bytes(b'changed')\n"
    )
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="frozen author age predictions changed"):
        invoke(case, digest=digest)
    assert not case.output.exists()


def test_qualified_source_mutation_refused(case: Case) -> None:
    source = case.repository / case.replay
    source.write_text(
        source.read_text()
        + "    (author_source_root / 'author/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv').write_bytes(b'changed')\n"
    )
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="inputs changed during scoring"):
        invoke(case, digest=digest)
    assert not case.output.exists()
