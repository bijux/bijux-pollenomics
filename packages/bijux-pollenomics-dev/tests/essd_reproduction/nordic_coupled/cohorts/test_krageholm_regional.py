"""Synthetic source projections keep a permanent region and exact old count support."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import grouped_leave_one_out
from bijux_pollenomics.analysis.lra_validation.experiments import SourceExperimentSpec
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
    make_request,
    read_geometry,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import (
    regional_source_support,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.cohorts import (
    krageholm_regional as cohort,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.inputs import store
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import Core, digest
from tests.essd_reproduction.nordic_coupled.test_inputs import fixture as small_fixture
from tests.essd_reproduction.nordic_coupled.test_regional_source_support import (
    artificial,
    native_samples,
)


def sources() -> tuple[
    tuple[Core, ...],
    dict[str, Any],
    dict[str, Any],
    dict[str, list[dict[str, Any]]],
    dict[str, list[dict[str, Any]]],
]:
    protocol = json.loads(
        (Path(__file__).resolve().parents[6] / cohort.PROTOCOL).read_bytes()
    )
    cores, _ = small_fixture()
    raw, audit_protocol = artificial()
    ages = [
        age
        for age, size in zip(
            (2700, 3200, 3700, 4200, 4700, 5200), (4, 4, 3, 2, 3, 3), strict=True
        )
        for _ in range(size)
    ]
    for index, row in enumerate(native_samples(raw)):
        row["ages"][-1]["age"] = ages[index] if index < 19 else 6000 + index
        if index >= 91:
            row["datum"].pop(1)
    audit = regional_source_support.project(raw, audit_protocol)
    references: dict[str, list[dict[str, Any]]] = {name: [] for name in cohort.NAMES}
    supports: dict[str, list[dict[str, Any]]] = {}
    for core, declaration in zip(cores, protocol["small_cores"], strict=True):
        supports[core.id] = []
        indices = [core.axis.index(taxon) for taxon in ("Betula", "Ulmus")]
        for name, cell in zip(cohort.NAMES, core.cells, strict=True):
            total = sum(cell.counts[index] for index in indices)
            references[name].append(
                {
                    "record_id": f"neotoma-{core.dataset}-{core.collection_unit}-{name}",
                    "native_site": core.site,
                    "native_dataset": core.dataset,
                    "native_collection_unit": core.collection_unit,
                    "selected_chronology": declaration["chronology"],
                    "source_axis": list(core.axis),
                    "projected_axis": ["Betula", "Ulmus"],
                    "source_panel_N": sum(cell.counts),
                    "projected_panel_N": total,
                    "excluded_panel_N": sum(cell.counts) - total,
                    "source_support_sha256": cell.source_support_sha256,
                }
            )
            supports[core.id].append(
                {
                    "window": list(cell.window),
                    "native_sample_count": 3,
                    "source_support_sha256": cell.source_support_sha256,
                    "source_report": {
                        "path": "artificial.json",
                        "bytes": 1,
                        "sha256": "1" * 64,
                    },
                    "source_selector": "artificial literal source support",
                }
            )
    return cores, audit, protocol, references, supports


def stage(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, str, dict[str, Any]]:
    cores, audit, protocol, references, supports = sources()
    (repository / "artifacts").mkdir()
    protocol_path = repository / cohort.PROTOCOL
    protocol_path.parent.mkdir(parents=True)
    protocol_path.write_text(json.dumps(protocol))
    _, pin = cohort.declaration(repository)
    output = repository / "artifacts/inputs"
    index = cohort.project(cores, audit, protocol, references, supports, output)
    index.update(source_commit="c" * 40, protocol=pin, qualified_source_inputs=[])
    store(output, "inputs.json", index)
    monkeypatch.setattr(cohort, "revision", lambda repository: "c" * 40)
    return output / "inputs.json", digest((output / "inputs.json").read_bytes()), index


def test_complete_minimal_inputs_have_only_three_target_folds_and_two_local_pairs(
    tmp_path: Path,
) -> None:
    cores, audit, protocol, references, supports = sources()
    output = tmp_path / "inputs"
    result = cohort.project(cores, audit, protocol, references, supports, output)
    assert (
        len(result["members"]) == 90
        and result["source_population"]["small_selected_sample_supports"] == 54
    )
    assert (
        result["source_population"]["krag_original_owners"] == 96
        and result["source_population"]["krag_selected_owners"] == 19
    )
    assert (
        result["source_population"]["krag_panel_complete_samples"] == 91
        and result["source_population"]["krag_sourcewide_panel_status"]
        == "suppressed_incomplete_panel"
    )
    pairs = []
    for row in result["experiments"]:
        directory = output / row["directory"]
        payload = json.loads((directory / "experiment.json").read_bytes())
        spec = SourceExperimentSpec(payload)
        assert spec.target_record_ids is not None
        anchor = spec.sites[-1]
        assert set(read_geometry(directory, anchor, spec)) == {
            "basin",
            "sample_metadata",
            "longitude",
            "latitude",
        }
        for fold in grouped_leave_one_out(
            [site.record for site in spec.sites],
            target_record_ids=spec.target_record_ids,
        ):
            assert (
                anchor.record.record_id in fold.train_record_ids
                and anchor.record.record_id not in fold.test_record_ids
            )
            locals_ = [
                site
                for site in spec.sites
                if site.record.record_id in fold.train_record_ids
                and site.record.record_id in spec.target_record_ids
            ]
            assert len(locals_) == 2
            for local in locals_:
                request: Any = make_request(spec, local, anchor, fold, directory)
                assert request["regional"]["basin"]["diameter_m"] == 1674
                pairs.append(request)
        authority = json.loads((directory / "projection.json").read_bytes())
        assert (
            len(authority) == 4
            and authority[-1]["native_collection_default_reference"] == 13365
        )
        assert all(
            row["qualified_source_support"]["native_sample_count"] == 3
            for row in authority[:3]
        )
        for role in ("chronology", "taxa", "parameters", "dependency_lock", "decision"):
            common = (directory / (role + ".json")).read_text()
            assert not any(
                '"' + key + '"' in common
                for key in (
                    "source_window_authority",
                    "projected_panel_N",
                    "native_sample_ids",
                    "source_support_sha256",
                    "source_report",
                    "counts",
                    "native_sample_count",
                )
            )
            assert "-raw.json" not in common and "projection.json" not in common
    assert len(pairs) == 36


@pytest.mark.parametrize(
    "mutation",
    [
        "source_owner",
        "source_window",
        "source_count",
        "missing_literal",
        "old_fingerprint",
        "old_count",
        "rounded_count",
        "sample_support_count",
    ],
)
def test_changed_source_support_refused_before_any_output(
    tmp_path: Path, mutation: str
) -> None:
    cores, audit, protocol, references, supports = sources()
    if mutation == "source_owner":
        audit["samples"][0]["sample_id"] = audit["samples"][1]["sample_id"]
    elif mutation == "source_window":
        audit["windows"][0]["sample_ids"].pop()
    elif mutation == "source_count":
        audit["windows"][0]["panel_counts"][0] += 1
    elif mutation == "missing_literal":
        audit["samples"][0]["panel_complete"] = False
    elif mutation == "old_fingerprint":
        references[cohort.NAMES[0]][0]["source_support_sha256"] = "0" * 64
    elif mutation == "old_count":
        references[cohort.NAMES[0]][0]["projected_panel_N"] += 1
    elif mutation == "sample_support_count":
        supports["BOKE"][0]["native_sample_count"] = 3.0
    else:
        first = cores[0]
        invalid_counts: Any = (6.0, 3, 4)
        cells = (replace(first.cells[0], counts=invalid_counts), *first.cells[1:])
        cores = (replace(first, cells=cells), *cores[1:])
    with pytest.raises(ValueError):
        cohort.project(
            cores, audit, protocol, references, supports, tmp_path / "inputs"
        )
    assert not (tmp_path / "inputs").exists()


def test_closed_input_inventory_refuses_missing_and_unlisted_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    index, checksum, _ = stage(tmp_path, monkeypatch)
    cohort.read_inputs(tmp_path, index, checksum)
    (index.parent / "unlisted.json").write_text("{}")
    with pytest.raises(ValueError, match="Unlisted input"):
        cohort.read_inputs(tmp_path, index, checksum)


def test_small_source_counts_are_not_derived_from_fractional_observations(
    tmp_path: Path,
) -> None:
    cores, audit, protocol, references, supports = sources()
    changed = deepcopy(references)
    changed[cohort.NAMES[0]][0]["source_panel_N"] = 1.0
    with pytest.raises(ValueError, match="projection changed"):
        cohort.project(cores, audit, protocol, changed, supports, tmp_path / "inputs")


def test_structural_admission_never_opens_raw_or_projection_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    index, checksum, _ = stage(tmp_path, monkeypatch)
    original = cohort.pinned
    opened = []

    def structural(
        repository: Path, pin: dict[str, Any], maximum: int = 4194304
    ) -> Any:
        assert not pin["path"].endswith("-raw.json") and not pin["path"].endswith(
            "/projection.json"
        )
        opened.append(pin["path"])
        return original(repository, pin, maximum)

    monkeypatch.setattr(cohort, "pinned", structural)
    cohort.read_inputs(tmp_path, index, checksum)
    assert len(opened) == 60
