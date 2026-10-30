"""Extend saved three-place inputs with the literal FLINK native panel."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.essd_reproduction.author_lra_development import _rings
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import inputs, workflow
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.sensitivity import encoded
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import (
    buffer,
    decode,
    digest,
)

PROTOCOL = "docs/report/pollen-reconstruction/nordic-coupled-workflow/assumptions/flink-nordic-cohort.json"
SCHEMA = "flink-nordic-cohort.v1"
IDENTITY = {
    "site_id": 28889,
    "dataset_id": 54024,
    "collection_unit_id": 39258,
    "default_chronology_id": 38438,
}
ASSUMPTIONS = {
    "radius_m": 98,
    "longitude": 13.24333,
    "latitude": 56.25444,
    "PPE": [5.106, 1.27],
    "PPE_SD": [0.303, 0.05],
    "fallspeed_m_s": [0.024, 0.032],
    "regional_priority": "ascending_native_site_id",
}
require = workflow.require


def validate_projection(projection: dict[str, Any]) -> list[dict[str, Any]]:
    """Refuse missing observations rather than supplying zero count cells."""
    require(
        projection["schema_version"] == "flink-native-panel-results.v1"
        and projection["identity"] == IDENTITY
        and projection["axis"]
        == [{"label": "Betula", "taxon_id": 29}, {"label": "Ulmus", "taxon_id": 310}]
        and projection["sample_count"] == 109
        and projection["engine_calls"] == 0,
        "FLINK source identity or literal axis differs",
    )
    samples = projection["samples"]
    by_id = {row["sample_id"]: row for row in samples}
    require(len(samples) == len(by_id) == 109, "Complete unique sample ledger required")
    windows: list[dict[str, Any]] = projection["windows"]
    require(
        [row["window_cal_bp_half_open"] for row in windows]
        == [list(window) for window in inputs.WINDOWS],
        "Six exact ordered source windows required",
    )
    used: set[int] = set()
    for row in windows:
        ids, counts = row["sample_ids"], row["panel_counts"]
        require(
            row["status"] == "projected",
            "Native window refusal retained; extension refused",
        )
        require(
            type(ids) is list
            and bool(ids)
            and len(ids) == len(set(ids))
            and not used.intersection(ids)
            and all(type(value) is int and value in by_id for value in ids),
            "Missing, duplicate or foreign source sample",
        )
        used.update(ids)
        require(
            type(counts) is list
            and len(counts) == 2
            and all(type(n) is int and n >= 0 for n in counts)
            and type(row["panel_N"]) is int
            and 0 < sum(counts) == row["panel_N"] <= 2**53
            and type(row["pollen_N"]) is int
            and type(row["excluded_pollen_N"]) is int
            and row["pollen_N"] == row["panel_N"] + row["excluded_pollen_N"]
            and row["excluded_pollen_N"] >= 0,
            "Exact integer projected and excluded denominators required",
        )
        require(
            len(row["support_sha256"]) == 64
            and all(c in "0123456789abcdef" for c in row["support_sha256"]),
            "Native support hash required",
        )
        require(
            set(ids)
            == {
                s["sample_id"]
                for s in samples
                if s["window"] == row["window_cal_bp_half_open"]
            }
            and all(
                by_id[i]["panel_complete"] is True
                and by_id[i]["nonnegative_age"] is True
                for i in ids
            ),
            "Incomplete or inconsistent native source membership",
        )
    return windows


def extend(
    nominal: dict[str, bytes], projection: dict[str, Any], protocol: dict[str, Any]
) -> dict[str, bytes]:
    """Keep all nominal bytes and add separately named four-place products."""
    require(
        protocol["schema_version"] == SCHEMA
        and protocol["baseline_protocol_sha256"] == workflow.PROTOCOL_SHA256
        and protocol["model_assumptions"] == ASSUMPTIONS,
        "Declared conditional cohort protocol differs",
    )
    require(len(nominal) == 80, "Authenticated nominal80 required")
    windows = validate_projection(projection)
    result = dict(nominal)
    rows = []

    def add(name: str, value: object) -> dict[str, str]:
        """Retain one distinct feasible witness in deterministic source order."""
        require(name not in result, "Nominal input overwrite refused")
        raw = encoded(value)
        require(len(raw) <= 65536, "Input member exceeds bound")
        result[name] = raw
        return {"path": Path(name).name, "sha256": digest(raw)}

    for name, window in zip(workflow.NAMES, windows, strict=True):
        prefix = name + "/"
        experiment = deepcopy(decode(nominal[prefix + "experiment.json"]))
        sites = experiment["sites"]
        require(
            [row["site_id"] for row in sites]
            == ["neotoma-site-28872", "neotoma-site-28869", "neotoma-site-3432"],
            "Original three physical places differ",
        )
        template = experiment["request_template"]
        require(
            template["taxa"] == list(inputs.AXIS)
            and template["parameters"]
            == [
                {"taxon": taxon, "ppe": ppe, "ppe_sd": sd, "fallspeed_m_s": fall}
                for taxon, ppe, sd, fall in zip(
                    inputs.AXIS,
                    (5.106, 1.27),
                    (0.303, 0.05),
                    (0.024, 0.032),
                    strict=True,
                )
            ],
            "Original nominal parameter assumptions differ",
        )
        younger, older = window["window_cal_bp_half_open"]
        record = "neotoma-54024-39258-" + name
        metadata = {
            "site_id": "neotoma-site-28889",
            "sample_id": record,
            "coordinate": float(younger),
            "bin_id": name,
            "age_type": "calendar_bp",
            "age_support_bp": [[float(younger), float(older)]],
            "chronology_evidence_id": "chronology",
        }
        raw = add(
            prefix + "FLINK-raw.json",
            {
                "data_kind": "source_observations",
                "taxa": list(inputs.AXIS),
                "sample": dict(metadata, counts=window["panel_counts"]),
            },
        )
        geometry = add(
            prefix + "FLINK-geometry.json",
            {
                "basin": {"diameter_m": 196, "site_type": "lake"},
                "inversion_rings": _rings(98, inversion=True)[:2],
                "forward_rings": _rings(98, inversion=False),
                "sample_metadata": metadata,
                "longitude": 13.24333,
                "latitude": 56.25444,
            },
        )
        sites.append(
            {
                "record_id": record,
                "site_id": metadata["site_id"],
                "identity_keys": [metadata["site_id"], "neotoma-collection-39258"],
                "raw": raw,
                "geometry": geometry,
            }
        )
        experiment["regional_priority"] = [
            row["record_id"]
            for row in sorted(
                sites, key=lambda row: int(row["site_id"].removeprefix("neotoma-site-"))
            )
        ]
        chronology = deepcopy(decode(nominal[prefix + "chronology.json"]))
        chronology["flink_source"] = {
            "identity": IDENTITY,
            "native_chronology": projection["chronology"],
            "source_window": window,
            "support_meaning": "Native point ages assigned to half-open bins; pooled-bin stationarity is a model assumption, not sample age uncertainty.",
        }
        decision = {
            "protocol": protocol,
            "nominal_decision_sha256": digest(nominal[prefix + "decision.json"]),
            "native_projection_scope": projection["scope"],
            "source_window": window,
        }
        for role, value in (("chronology", chronology), ("decision", decision)):
            reference = add(prefix + "cohort-" + role + ".json", value)
            selected = [row for row in template["evidence"] if row["role"] == role]
            require(len(selected) == 1, "Unique original evidence role required")
            selected[0].update(reference)
        template["versions"]["chronology"] = SCHEMA
        template["versions"]["geometry"] = SCHEMA
        reference = add(prefix + "cohort-experiment.json", experiment)
        rows.append({"directory": name, "experiment": reference})
        add(
            prefix + "cohort-projection.json",
            {
                "nominal_projection_sha256": digest(
                    nominal[prefix + "projection.json"]
                ),
                "nominal_projection": json.loads(nominal[prefix + "projection.json"]),
                "flink_identity": IDENTITY,
                "flink_source_window": window,
                "native_sample_ids": window["sample_ids"],
                "scope": protocol["scope"],
            },
        )
    add(
        "cohort-inputs.json",
        {
            "schema_version": SCHEMA,
            "experiments": rows,
            "protocol": protocol,
            "nominal_members_preserved": 80,
            "scope": protocol["scope"],
        },
    )
    require(
        len(result) == 117 and sum(map(len, result.values())) <= 2097152,
        "Extended input population or budget differs",
    )
    require(
        all(result[key] == raw for key, raw in nominal.items()),
        "Original nominal bytes changed",
    )
    return result


def derive(repository: Path, *, protocol_sha256: str) -> dict[str, bytes]:
    """Authenticate saved products without reopening original count archives."""
    _, protocol = workflow.read(repository / PROTOCOL, protocol_sha256, 65536)
    authenticated = {}
    for pin in protocol["input_pins"]:
        relative = Path(pin["path"])
        require(
            not relative.is_absolute() and ".." not in relative.parts,
            "Confined source pin required",
        )
        require(pin["path"] not in authenticated, "Duplicate source pin")
        authenticated[pin["path"]] = buffer(
            repository / relative, pin["sha256"], pin["bytes"]
        )
    nominal_root = repository / protocol["nominal_input_root"]
    manifest = protocol["nominal_manifest"]
    require(manifest in authenticated, "Original nominal inventory must be pinned")
    pins_raw = authenticated[manifest]
    _, pins = workflow.input_scope(
        nominal_root, repository / manifest, digest(pins_raw)
    )
    wrapper = decode(authenticated[protocol["nominal_original_inventory"]])
    require(
        wrapper["candidate"] == protocol["source_epochs"]["nominal_input"]
        and wrapper["members"]
        == [{**row, "path": str(nominal_root / row["path"])} for row in pins],
        "Original native80 inventory correspondence differs",
    )
    nominal = {
        row["path"]: buffer(nominal_root / row["path"], row["sha256"], row["bytes"])
        for row in pins
    }
    terminal = decode(authenticated[protocol["flink_terminal"]])
    execution = decode(authenticated[protocol["flink_execution"]])
    require(
        terminal["actual_exit"]
        == execution["actual_exit"]
        == execution["native_exit"]
        == 0
        and execution["timed_out"] is False
        and terminal["candidate"]
        == execution["candidate"]
        == protocol["source_epochs"]["flink_projection"]
        and terminal["before_pin_mismatches"] == terminal["after_pin_mismatches"] == [],
        "Successful unchanged native projection receipts required",
    )
    projection = decode(authenticated[protocol["flink_projection"]])
    manifest_data = decode(authenticated[protocol["flink_manifest"]])
    projection_raw = authenticated[protocol["flink_projection"]]
    require(
        manifest_data["files"]
        == [
            {
                "path": "panel-projection.json",
                "sha256": digest(projection_raw),
                "bytes": len(projection_raw),
            }
        ],
        "Native projection/manifest join differs",
    )
    require(
        manifest_data["engine_calls"] == 0
        and manifest_data["source"]["sha256"] == projection["source"]["sha256"],
        "Native source/projection authority differs",
    )
    result = extend(nominal, projection, protocol)
    workflow.input_scope(nominal_root, repository / manifest, digest(pins_raw))
    return result


def admit(output: Path) -> dict[str, int]:
    """Exercise all distinct place/fold training readers without an engine."""
    from bijux_pollenomics.analysis.lra.inputs.validation import validate_request
    from bijux_pollenomics.analysis.lra_validation.experiments import (
        SourceExperimentSpec,
    )
    from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
        make_request,
        read_geometry,
    )
    from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out

    index = decode((output / "cohort-inputs.json").read_bytes())
    require(
        [r["directory"] for r in index["experiments"]] == list(workflow.NAMES),
        "Six ordered bins required",
    )
    geometries = requests = folds_count = 0
    for row in index["experiments"]:
        directory = output / row["directory"]
        reference = row["experiment"]
        require(
            reference["path"] == "cohort-experiment.json",
            "Exact cohort experiment member required",
        )
        _, payload = workflow.read(
            directory / reference["path"], reference["sha256"], 65536
        )
        spec = SourceExperimentSpec(payload)
        require(
            len(spec.sites) == 4 and len({s.record.site_id for s in spec.sites}) == 4,
            "Four distinct places required",
        )
        by_record = {site.record.record_id: site for site in spec.sites}
        for site in spec.sites:
            read_geometry(directory, site, spec)
            geometries += 1
        for fold in grouped_leave_one_out([site.record for site in spec.sites]):
            priority = [
                key for key in spec.regional_priority if key in fold.train_record_ids
            ]
            anchor = by_record[priority[0]]
            locals_ = [
                by_record[key] for key in fold.train_record_ids if key != priority[0]
            ]
            require(
                len(priority) == 3
                and len(locals_) == 2
                and not set(fold.test_record_ids).intersection(fold.train_record_ids),
                "Outer training split differs",
            )
            for local in locals_:
                validate_request(
                    make_request(spec, local, anchor, fold, directory),
                    input_root=directory,
                )
                requests += 1
            folds_count += 1
    require(
        (geometries, folds_count, requests) == (24, 24, 48),
        "Complete reader population differs",
    )
    return {
        "geometry_reads": geometries,
        "outer_folds": folds_count,
        "training_pair_requests": requests,
        "engine_calls": 0,
    }


def materialize(
    repository: Path, output: Path, manifest: Path, *, protocol_sha256: str
) -> dict[str, Any]:
    """Write a fresh117-member extension and admit exact generic reader handoffs."""
    for path in (output, manifest):
        workflow.physical(path)
        require(
            path.is_relative_to(repository / "artifacts") and not path.exists(),
            "Absent artifact output required",
        )
    require(
        output not in manifest.parents and manifest != output,
        "Manifest must be outside input root",
    )
    _, protocol = workflow.read(repository / PROTOCOL, protocol_sha256, 65536)
    nominal_root = repository / protocol["nominal_input_root"]
    for path in (output, manifest):
        require(
            not path.is_relative_to(nominal_root)
            and not nominal_root.is_relative_to(path),
            "Nominal namespace overlap refused",
        )
    buffers = derive(repository, protocol_sha256=protocol_sha256)
    output.mkdir(parents=True)
    for name, raw in buffers.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
    members = [
        {"path": name, "sha256": digest(raw), "bytes": len(raw)}
        for name, raw in sorted(buffers.items())
    ]
    body = encoded(members)
    with manifest.open("xb") as stream:
        stream.write(body)
    return {
        "input_manifest_sha256": digest(body),
        "members": len(members),
        "reader_admission": admit(output),
    }


def main() -> None:
    """Parse arguments for the declared source-bound conditional calculation."""
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for field in ("repository", "output", "manifest"):
        parser.add_argument("--" + field, type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            materialize(
                args.repository,
                args.output,
                args.manifest,
                protocol_sha256=args.protocol_sha256,
            )
        )
    )


if __name__ == "__main__":
    main()
