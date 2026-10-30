"""Project retained Nordic panels into explicitly conditional LRA experiments."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..author_lra_development import FALL_SPEED_PROFILE, _rings
from ..physical_forward.inputs import Core, buffer, digest, load, physical, require

PROTOCOL = "docs/report/pollen-reconstruction/nordic-coupled-workflow/assumptions/protocol.json"
AXIS = ("Betula", "Ulmus")
WINDOWS = tuple((float(x), float(x + 500)) for x in range(2700, 5700, 500))


def store(root: Path, name: str, value: object) -> dict[str, str]:
    """Create only a fixed, owned finite JSON member."""
    require(
        Path(name).name == name and name.endswith(".json"), "Owned JSON name required"
    )
    raw = (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode()
    require(len(raw) <= 65536, "Input member exceeds bound")
    with (root / name).open("xb") as stream:
        stream.write(raw)
    return {"path": name, "sha256": digest(raw)}


def project(
    cores: tuple[Core, ...], protocol: dict[str, Any], output: Path
) -> dict[str, Any]:
    """Materialize six separate bin experiments; arithmetic is limited to count projection."""
    physical(output)
    require(not output.exists(), "Absent output required")
    expected = protocol["cores"]
    require(
        len([x for x in protocol["input_pins"] if x["path"] == "uv.lock"]) == 1,
        "Exact dependency lock identity required",
    )
    require(
        [x["id"] for x in expected] == ["BOKE", "BUS", "SOLSOE83"],
        "Core population differs",
    )
    selected_cores = [c for c in cores if c.id in {x["id"] for x in expected}]
    require(len(selected_cores) == 3, "Duplicate or missing selected core")
    selected = {c.id: c for c in selected_cores}
    require(len(selected) == 3, "Three selected source cores required")
    projections = {}
    for declaration in expected:
        core = selected[declaration["id"]]
        require(
            core.site == declaration["site"]
            and core.dataset == declaration["dataset"]
            and core.collection_unit == declaration["collection_unit"],
            "Native source identity differs",
        )
        require(all(t in core.axis for t in AXIS), "Unmeasured taxon refused")
        indices = [core.axis.index(t) for t in AXIS]
        require(
            [core.ppe[i] for i in indices] == [5.106, 1.27]
            and [core.sd[i] for i in indices] == [0.303, 0.05],
            "Shared PPE profile differs",
        )
        cells = {}
        for window in WINDOWS:
            matches = [c for c in core.cells if c.window == window]
            require(len(matches) == 1, "Missing or duplicate exact source window")
            cell = matches[0]
            require(
                len(cell.counts) == len(core.axis)
                and all(type(n) is int and n >= 0 for n in cell.counts),
                "Integer source count axis required",
            )
            counts = [cell.counts[i] for i in indices]
            require(
                0 < sum(counts) <= 2**53,
                "Positive projected source denominator required",
            )
            require(
                len(cell.source_support_sha256) == 64,
                "Source support identity required",
            )
            cells[window] = (counts, sum(cell.counts), cell.source_support_sha256)
        projections[core.id] = cells
    output.mkdir(parents=True)
    experiments = []
    for younger, older in WINDOWS:
        name = f"cal-bp-{int(younger)}-{int(older)}"
        directory = output / name
        directory.mkdir()
        authority = [
            {
                "core": d["id"],
                "site": d["site"],
                "dataset": d["dataset"],
                "collection_unit": d["collection_unit"],
                "chronology": d["chronology"],
                "source_support_sha256": projections[d["id"]][(younger, older)][2],
            }
            for d in expected
        ]
        common = {
            "source_epochs": protocol["source_epochs"],
            "original_input_pins": protocol.get("input_pins", []),
            "source_window_authority": authority,
        }
        role_values = {
            "chronology": {
                **common,
                "declared_bin_cal_bp": [younger, older],
                "support_meaning": "Declared pooled-bin stationarity, not native age confidence bounds",
            },
            "taxa": {
                **common,
                "axis": list(AXIS),
                "projection": "Actually measured saved cells only; excluded labels never imputed zero",
            },
            "parameters": {
                **common,
                "PPE": [5.106, 1.27],
                "PPE_SD": [0.303, 0.05],
                "fallspeed_m_s": [0.024, 0.032],
                "fall_speed_profile": FALL_SPEED_PROFILE,
            },
            "dependency_lock": {
                "actual_lock": [
                    x for x in protocol.get("input_pins", []) if x["path"] == "uv.lock"
                ],
                "scope": "Exact source dependency lock, not a new runtime certificate",
            },
            "decision": {
                "protocol": protocol,
                "source_window_authority": authority,
                "scope": "Conditional modeling choices only; no source-rights or scientific approval inferred",
            },
        }
        evidence = []
        for role, value in role_values.items():
            reference = store(directory, role + ".json", value)
            evidence.append({"evidence_id": role, "role": role, **reference})
        sites, provenance = [], []
        for declaration in expected:
            core = selected[declaration["id"]]
            counts, original_total, support = projections[core.id][(younger, older)]
            record = f"neotoma-{core.dataset}-{core.collection_unit}-{name}"
            metadata = {
                "site_id": f"neotoma-site-{core.site}",
                "sample_id": record,
                "coordinate": younger,
                "bin_id": name,
                "age_type": "calendar_bp",
                "age_support_bp": [[younger, older]],
                "chronology_evidence_id": "chronology",
            }
            radius = declaration["radius_m"]
            geometry = {
                "basin": {"diameter_m": 2 * radius, "site_type": "lake"},
                "inversion_rings": _rings(radius, inversion=True)[:2],
                "forward_rings": _rings(radius, inversion=False),
                "sample_metadata": metadata,
                "longitude": declaration["longitude"],
                "latitude": declaration["latitude"],
            }
            sites.append(
                {
                    "record_id": record,
                    "site_id": metadata["site_id"],
                    "identity_keys": [
                        metadata["site_id"],
                        f"neotoma-collection-{core.collection_unit}",
                    ],
                    "raw": store(
                        directory,
                        core.id + "-raw.json",
                        {
                            "data_kind": "source_observations",
                            "taxa": list(AXIS),
                            "sample": dict(metadata, counts=counts),
                        },
                    ),
                    "geometry": store(directory, core.id + "-geometry.json", geometry),
                }
            )
            provenance.append(
                {
                    "record_id": record,
                    "native_site": core.site,
                    "native_dataset": core.dataset,
                    "native_collection_unit": core.collection_unit,
                    "selected_chronology": declaration["chronology"],
                    "source_axis": list(core.axis),
                    "projected_axis": list(AXIS),
                    "source_panel_N": original_total,
                    "projected_panel_N": sum(counts),
                    "excluded_panel_N": original_total - sum(counts),
                    "source_support_sha256": support,
                }
            )
        priority = [
            sites[i]["record_id"]
            for i in sorted(range(3), key=lambda i: expected[i]["site"])
        ]
        configuration = {
            "seed": 7,
            "love": {
                "method": "analytical",
                "stochastic": False,
                "max_ring": 2,
                "repeats": 2,
                "distance_weighting": "gpm neutral",
                "fall_speed_profile": FALL_SPEED_PROFILE,
            },
            "reveals": {
                "stochastic": False,
                "iterations": 2,
                "distance_weighting": "gpm neutral",
                "fall_speed_profile": FALL_SPEED_PROFILE,
            },
        }
        template = {
            "schema_version": "lra-request.v1",
            "operation": "lra",
            "data_kind": "source_observations",
            "purpose": "exploratory",
            "method_profile": "disqover-0.9.14-source-compatible",
            "taxa": list(AXIS),
            "pollen_unit": "count",
            "configuration": configuration,
            "parameters": [
                {
                    "taxon": "Betula",
                    "fallspeed_m_s": 0.024,
                    "ppe": 5.106,
                    "ppe_sd": 0.303,
                },
                {"taxon": "Ulmus", "fallspeed_m_s": 0.032, "ppe": 1.27, "ppe_sd": 0.05},
            ],
            "evidence": evidence,
            "exclusions": [],
            "uncertainty_omissions": [
                "chronology",
                "basin_geometry",
                "parameter_domain",
                "spatial_model",
                "ppe_covariance",
            ],
            "temporal_matching": {
                "rule": "declared_bin_stationarity",
                "decision_evidence_id": "decision",
                "bins": [{"bin_id": name, "younger_bp": younger, "older_bp": older}],
            },
            "versions": dict.fromkeys(
                ("binning", "chronology", "geometry", "parameters", "taxonomy"),
                protocol["schema_version"],
            ),
        }
        payload = {
            "schema_version": "lra-experiment.v1",
            "profile": "source-observations-withheld-site-baselines-v1",
            "sites": sites,
            "regional_priority": priority,
            "baselines": ["training_mean", "nearest_site", "inverse_distance_squared"],
            "local_ring_count": 2,
            "local_support_radius_m": 1000,
            "support_profile": "same-outer-radius-homogeneous-v1",
            "request_template": template,
        }
        reference = store(directory, "experiment.json", payload)
        store(directory, "projection.json", provenance)
        experiments.append({"directory": name, "experiment": reference})
    result = {
        "schema_version": "nordic-coupled-inputs.v1",
        "experiments": experiments,
        "source_epochs": protocol["source_epochs"],
        "scope": protocol["scope"],
    }
    store(output, "inputs.json", result)
    return result


def materialize(
    repository: Path, output: Path, *, protocol_sha256: str
) -> dict[str, Any]:
    """Root-owned actual source read; never execute a reconstruction or score."""
    physical(output)
    require(not output.exists(), "Absent output required")
    path = repository / PROTOCOL
    raw = buffer(path, protocol_sha256, path.stat().st_size)
    protocol = json.loads(raw)
    cores, matched_protocol, pins = load(repository)
    require(
        protocol["matched_protocol_sha256"]
        == digest(
            (
                repository
                / "docs/report/pollen-reconstruction/matched-pollen-forward/assumptions/protocol.json"
            ).read_bytes()
        ),
        "Matched source protocol differs",
    )
    require(
        protocol["source_epochs"] == matched_protocol["source_epochs"],
        "Saved source epochs differ",
    )
    generator = protocol["ring_generator"]
    buffer(repository / generator["path"], generator["sha256"], generator["bytes"])
    for entry in protocol["input_pins"]:
        buffer(repository / entry["path"], entry["sha256"], entry["bytes"])
    result = project(cores, protocol, output)
    store(output, "source-pins.json", pins)
    return result


def admit(output: Path) -> dict[str, int]:
    """Exercise actual geometry/request validators without invoking an engine."""
    from bijux_pollenomics.analysis.lra.inputs.validation import validate_request
    from bijux_pollenomics.analysis.lra_validation.experiments import (
        SourceExperimentSpec,
    )
    from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
        make_request,
        read_geometry,
    )
    from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out

    physical(output)
    index = json.loads((output / "inputs.json").read_text())
    require(len(index["experiments"]) == 6, "Six experiments required")
    geometries = requests = 0
    require(
        [x["directory"] for x in index["experiments"]]
        == [f"cal-bp-{int(a)}-{int(b)}" for a, b in WINDOWS],
        "Exact input directory namespace required",
    )
    for row in index["experiments"]:
        require(
            row["experiment"]["path"] == "experiment.json",
            "Exact input member required",
        )
        directory = output / row["directory"]
        reference = row["experiment"]
        path = directory / reference["path"]
        spec = SourceExperimentSpec(
            json.loads(buffer(path, reference["sha256"], path.stat().st_size))
        )
        for site in spec.sites:
            read_geometry(directory, site, spec)
            geometries += 1
        by_record = {site.record.record_id: site for site in spec.sites}
        for fold in grouped_leave_one_out([site.record for site in spec.sites]):
            priority = [x for x in spec.regional_priority if x in fold.train_record_ids]
            anchor = by_record[priority[0]]
            local = next(
                by_record[x] for x in fold.train_record_ids if x != priority[0]
            )
            validate_request(
                make_request(spec, local, anchor, fold, directory), input_root=directory
            )
            requests += 1
    require((geometries, requests) == (18, 18), "Complete reader population differs")
    return {
        "geometry_reads": geometries,
        "training_pair_requests": requests,
        "engine_calls": 0,
    }
