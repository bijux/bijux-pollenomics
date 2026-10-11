"""Exercise source-bound owner adapters with fake calculations only."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from bijux_pollenomics_dev.source_completion.neotoma.pollen_prerequisites import (
    candidate_series,
    concept_priority,
    dataset_attribution,
    sample_decisions,
    writer_execution,
)


def _repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    (root / "artifacts").mkdir(parents=True)
    (root / writer_execution.RAW).mkdir(parents=True)
    (root / writer_execution.RELATIONAL).mkdir(parents=True)
    for relative in (
        concept_priority.SCREEN,
        concept_priority.REVIEW,
        dataset_attribution.PRIORITY,
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"fixture":true}', encoding="utf-8")
    return root


def test_series_uses_explicit_sixteen_ids_and_exact_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repository(tmp_path)
    output = root / "artifacts/series.json"
    called: list[tuple[str, ...]] = []

    def fake_series(
        *, raw_root: Path, normalized_root: Path, selected_sample_ids: tuple[str, ...]
    ) -> SimpleNamespace:
        assert raw_root == root / writer_execution.RAW
        assert normalized_root == root / writer_execution.RELATIONAL
        called.append(selected_sample_ids)
        return SimpleNamespace(canonical_json=b'{"refused":16}\n')

    monkeypatch.setattr(
        candidate_series, "inspect_neotoma_lra_candidate_series", fake_series
    )
    candidate_series.run(root, output)
    assert output.read_bytes() == b'{"refused":16}\n'
    assert called == [
        tuple(f"neotoma:sample:{number}" for number in range(355236, 355252))
    ]
    with pytest.raises(ValueError, match="absent"):
        candidate_series.run(root, output)


def test_screen_preserves_retained_unicode_and_indented_file_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repository(tmp_path)
    output = root / "artifacts/screen.json"
    monkeypatch.setattr(
        sample_decisions,
        "inspect_neotoma_lra_pollen_screen",
        lambda **kwargs: SimpleNamespace(
            canonical_json='{"z":0,"label":"é","lra_accepted_samples":0}'.encode()
        ),
    )
    sample_decisions.run(root, output)
    assert (
        output.read_bytes()
        == ('{\n  "label": "é",\n  "lra_accepted_samples": 0,\n  "z": 0\n}\n').encode()
    )


def test_screen_nonfinite_result_refuses_before_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repository(tmp_path)
    output = root / "artifacts/screen.json"
    monkeypatch.setattr(
        sample_decisions,
        "inspect_neotoma_lra_pollen_screen",
        lambda **kwargs: SimpleNamespace(canonical_json=b'{"value":NaN}'),
    )
    with pytest.raises(ValueError):
        sample_decisions.run(root, output)
    assert not output.exists()


def test_concept_and_attribution_use_only_governed_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repository(tmp_path)
    observed: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        concept_priority, "read_neotoma_evidence", lambda *args: object()
    )
    monkeypatch.setattr(
        dataset_attribution, "read_neotoma_evidence", lambda *args: object()
    )

    def fake_priority(
        evidence: object, screen: object, review: object
    ) -> dict[str, object]:
        observed.append(("priority", str(screen), str(review)))
        return {"lra_accepted_samples": 0}

    def fake_attribution(
        evidence: object, screen: object, review: object, priority: object
    ) -> dict[str, object]:
        observed.append(("attribution", str(screen), str(review), str(priority)))
        return {"candidate_dataset_count": 169, "lra_accepted_samples": 0}

    monkeypatch.setattr(
        concept_priority, "prioritize_neotoma_candidate_taxa", fake_priority
    )
    monkeypatch.setattr(
        dataset_attribution, "attribute_neotoma_priority_datasets", fake_attribution
    )
    concept_priority.run(root, root / "artifacts/priority.json")
    dataset_attribution.run(root, root / "artifacts/attribution.json")
    assert (
        root / "artifacts/priority.json"
    ).read_bytes() == b'{"lra_accepted_samples":0}\n'
    assert (
        root / "artifacts/attribution.json"
    ).read_bytes() == b'{"candidate_dataset_count":169,"lra_accepted_samples":0}\n'
    assert [row[0] for row in observed] == ["priority", "attribution"]
    assert all("fixture" in row[1] for row in observed)


def test_refuses_outside_or_symlinked_output_before_source_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repository(tmp_path)
    monkeypatch.setattr(
        concept_priority,
        "read_neotoma_evidence",
        lambda *args: pytest.fail("source read started"),
    )
    with pytest.raises(ValueError, match="outside"):
        concept_priority.run(root, tmp_path / "outside.json")
    (root / "artifacts/alias").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        concept_priority.run(root, root / "artifacts/alias/output.json")


def test_refuses_symlinked_scoped_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repository(tmp_path)
    review = root / concept_priority.REVIEW
    review.unlink()
    review.symlink_to(root / concept_priority.SCREEN)
    monkeypatch.setattr(
        concept_priority, "read_neotoma_evidence", lambda *args: object()
    )
    with pytest.raises(ValueError, match="real repository file"):
        concept_priority.run(root, root / "artifacts/priority.json")


@pytest.mark.parametrize(
    "module",
    [candidate_series, sample_decisions, concept_priority, dataset_attribution],
)
def test_cli_fixed_repository_and_output_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, module: ModuleType
) -> None:
    root = _repository(tmp_path)
    output = root / "artifacts/result.json"
    observed: list[tuple[Path, Path]] = []
    monkeypatch.setattr(
        module,
        "run",
        lambda repository, destination: observed.append((repository, destination)),
    )
    assert module.main(["--repository", str(root), "--output", str(output)]) == 0
    assert observed == [(root, output)]
    with pytest.raises(SystemExit) as error:
        module.main(
            ["--repository", str(root), "--output", str(output), "--seed", "42"]
        )
    assert error.value.code == 2
    assert len(observed) == 1


@pytest.mark.parametrize(
    "kind", ["artifact-root", "raw-root", "relational-root", "existing-output"]
)
def test_unsafe_roots_refused_before_calculation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root = _repository(tmp_path)
    output = root / "artifacts/result.json"
    if kind == "existing-output":
        output.write_bytes(b"preserved")
    else:
        relative = {
            "artifact-root": Path("artifacts"),
            "raw-root": writer_execution.RAW,
            "relational-root": writer_execution.RELATIONAL,
        }[kind]
        path = root / relative
        path.rmdir()
        target = tmp_path / "external"
        target.mkdir()
        path.symlink_to(target, target_is_directory=True)
    monkeypatch.setattr(
        sample_decisions,
        "inspect_neotoma_lra_pollen_screen",
        lambda **kwargs: pytest.fail("calculation started"),
    )
    with pytest.raises(ValueError):
        sample_decisions.run(root, output)
    if kind == "existing-output":
        assert output.read_bytes() == b"preserved"


def test_invalid_retained_object_refuses_before_priority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _repository(tmp_path)
    (root / concept_priority.REVIEW).write_text("[]")
    monkeypatch.setattr(
        concept_priority, "read_neotoma_evidence", lambda *args: object()
    )
    monkeypatch.setattr(
        concept_priority,
        "prioritize_neotoma_candidate_taxa",
        lambda *args: pytest.fail("priority calculation started"),
    )
    with pytest.raises(ValueError, match="object"):
        concept_priority.run(root, root / "artifacts/result.json")
    assert not (root / "artifacts/result.json").exists()
