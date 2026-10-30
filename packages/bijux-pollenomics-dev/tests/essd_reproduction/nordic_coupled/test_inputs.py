"""Artificial coupled-cohort inputs exercise real readers without a kernel."""

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.inputs import (
    WINDOWS,
    admit,
    project,
)
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import Cell, Core


def fixture() -> tuple[tuple[Core, ...], dict[str, Any]]:
    declarations = []
    cores = []
    for code, site, dataset, cu, radius, axis in (
        ("BOKE", 28872, 54001, 39241, 80, ("Betula", "Fraxinus", "Ulmus")),
        ("BUS", 28869, 53995, 39238, 69, ("Betula", "Ulmus")),
        ("SOLSOE83", 3432, 4446, 4304, 89, ("Betula", "Ulmus")),
    ):
        declarations.append(
            {
                "id": code,
                "site": site,
                "dataset": dataset,
                "collection_unit": cu,
                "radius_m": radius,
                "longitude": 13.0,
                "latitude": 56.0,
                "chronology": 99,
            }
        )
        ppe = tuple(
            {"Betula": 5.106, "Fraxinus": 1.044, "Ulmus": 1.27}[x] for x in axis
        )
        sd = tuple({"Betula": 0.303, "Fraxinus": 0.048, "Ulmus": 0.05}[x] for x in axis)
        counts = tuple({"Betula": 6, "Fraxinus": 3, "Ulmus": 4}[x] for x in axis)
        cores.append(
            Core(
                code,
                "synthetic",
                site,
                dataset,
                cu,
                axis,
                ppe,
                sd,
                tuple(0.5 for _ in axis),
                tuple(Cell(w, counts, "1" * 64) for w in WINDOWS),
            )
        )
    return tuple(cores), {
        "schema_version": "artificial",
        "input_pins": [{"path": "uv.lock", "sha256": "2" * 64, "bytes": 1}],
        "cores": declarations,
        "source_epochs": {},
        "scope": "Artificial only",
    }


def test_complete_artificial_population_through_actual_readers(tmp_path: Path) -> None:
    cores, protocol = fixture()
    root = tmp_path / "inputs"
    project(cores, protocol, root)
    assert admit(root) == {
        "geometry_reads": 18,
        "training_pair_requests": 18,
        "engine_calls": 0,
    }
    directory = root / "cal-bp-2700-3200"
    provenance = json.loads((directory / "projection.json").read_text())
    assert provenance[0]["source_panel_N"] == 13
    assert provenance[0]["projected_panel_N"] == 10
    assert provenance[0]["excluded_panel_N"] == 3
    payload = json.loads((directory / "experiment.json").read_text())
    assert payload["regional_priority"][0].startswith("neotoma-4446-")
    geo = json.loads((directory / "BOKE-geometry.json").read_text())
    assert geo["inversion_rings"][0]["inner_m"] == 81
    assert geo["forward_rings"][0]["inner_m"] == 80
    assert geo["inversion_rings"][-1]["outer_m"] == 1000
    assert geo["forward_rings"][-1]["outer_m"] == 100000


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_core",
        "missing_window",
        "duplicate_window",
        "missing_taxon",
        "wrong_site",
        "wrong_ppe",
        "zero_panel",
    ],
)
def test_refuses_source_changes_before_output(tmp_path: Path, mutation: str) -> None:
    cores, protocol = fixture()
    core = cores[0]
    if mutation == "duplicate_core":
        cores = (*cores, core)
    elif mutation == "missing_window":
        core = replace(core, cells=core.cells[1:])
    elif mutation == "duplicate_window":
        core = replace(core, cells=core.cells + (core.cells[0],))
    elif mutation == "missing_taxon":
        core = replace(core, axis=("Betula", "Fraxinus", "other"))
    elif mutation == "wrong_site":
        core = replace(core, site=1)
    elif mutation == "wrong_ppe":
        core = replace(core, ppe=(5.0, 1.044, 1.27))
    else:
        core = replace(
            core, cells=tuple(replace(c, counts=(0, 3, 0)) for c in core.cells)
        )
    output = tmp_path / "inputs"
    with pytest.raises(ValueError):
        project((core, *cores[1:]), protocol, output)
    assert not output.exists()


def test_real_geometry_guard_refuses_shore_inversion(tmp_path: Path) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments import (
        SourceExperimentSpec,
    )
    from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
        read_geometry,
    )

    cores, protocol = fixture()
    root = tmp_path / "inputs"
    project(cores, protocol, root)
    directory = root / "cal-bp-2700-3200"
    payload = json.loads((directory / "experiment.json").read_text())
    spec = SourceExperimentSpec(payload)
    site = spec.sites[0]
    geometry_path = directory / site.geometry.path
    geometry = json.loads(geometry_path.read_text())
    geometry["inversion_rings"][0]["inner_m"] = 80
    from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import digest

    raw = json.dumps(geometry).encode()
    geometry_path.write_bytes(raw)
    site = replace(site, geometry=replace(site.geometry, sha256=digest(raw)))
    with pytest.raises(ValidationRefusal, match="beyond the physical shore"):
        read_geometry(directory, site, spec)
