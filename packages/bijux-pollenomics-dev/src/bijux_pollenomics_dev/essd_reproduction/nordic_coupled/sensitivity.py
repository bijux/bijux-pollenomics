"""Declared PPE perturbations through the existing conditional coupled workflow."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from . import inputs, workflow

PROTOCOL = "docs/report/pollen-reconstruction/nordic-coupled-workflow/assumptions/ppe-sensitivity.json"
SCHEMA = "nordic-coupled-ppe-sensitivity.v1"
SCENARIOS = {
    "betula-lower": ("Betula", "4.803"),
    "betula-upper": ("Betula", "5.409"),
    "ulmus-lower": ("Ulmus", "1.22"),
    "ulmus-upper": ("Ulmus", "1.32"),
}
NOMINAL = {"Betula": 5.106, "Ulmus": 1.27}
SD = {"Betula": 0.303, "Ulmus": 0.05}


def encoded(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode()


def pin(path: Path, raw: bytes) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def derive(
    repository: Path,
    nominal_root: Path,
    nominal_manifest: Path,
    nominal_manifest_sha256: str,
    scenario_id: str,
    protocol_sha256: str,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Derive exact expected bytes; no source discovery, engine or score call."""
    require = workflow.require
    require(scenario_id in SCENARIOS, "Unknown PPE scenario")
    protocol_path = repository / PROTOCOL
    protocol_raw, protocol = workflow.read(protocol_path, protocol_sha256, 65536)
    binding = pin(protocol_path, protocol_raw)
    require(
        protocol["schema_version"] == SCHEMA
        and protocol["baseline_protocol_sha256"] == workflow.PROTOCOL_SHA256
        and protocol["axis"] == list(inputs.AXIS)
        and protocol["nominal_ppe"] == {k: str(v) for k, v in NOMINAL.items()}
        and protocol["ppe_sd"] == {k: str(v) for k, v in SD.items()}
        and protocol["scenarios"]
        == [
            {"id": key, "taxon": value[0], "ppe": value[1]}
            for key, value in SCENARIOS.items()
        ],
        "Declared PPE protocol differs",
    )
    _, baseline_protocol = workflow.read(
        repository / inputs.PROTOCOL, workflow.PROTOCOL_SHA256, 65536
    )
    rows, pins = workflow.input_scope(
        nominal_root, nominal_manifest, nominal_manifest_sha256
    )
    manifest_raw, _ = workflow.read(nominal_manifest, nominal_manifest_sha256, 65536)
    baseline = pin(nominal_manifest, manifest_raw)
    buffers: dict[str, bytes] = {}
    values: dict[str, Any] = {}
    old_pins = {row["path"]: row for row in pins}
    for row in pins:
        buffers[row["path"]], values[row["path"]] = workflow.read(
            nominal_root / row["path"], row["sha256"], 65536
        )
    taxon, endpoint = SCENARIOS[scenario_id]
    means = {**NOMINAL, taxon: float(endpoint)}
    context = {
        "protocol": binding,
        "scenario_id": scenario_id,
        "baseline_input_manifest": baseline,
    }
    index = deepcopy(values["inputs.json"])
    for position, row in enumerate(rows):
        name = row["directory"]
        parameters = deepcopy(values[name + "/parameters.json"])
        decision = deepcopy(values[name + "/decision.json"])
        experiment = deepcopy(values[name + "/experiment.json"])
        template = experiment["request_template"]
        require(
            parameters["PPE"] == list(NOMINAL.values())
            and parameters["PPE_SD"] == list(SD.values())
            and parameters["fallspeed_m_s"] == [0.024, 0.032]
            and decision["protocol"] == baseline_protocol
            and template["taxa"] == list(inputs.AXIS)
            and template["parameters"]
            == [
                {"taxon": t, "fallspeed_m_s": f, "ppe": NOMINAL[t], "ppe_sd": SD[t]}
                for t, f in zip(inputs.AXIS, (0.024, 0.032), strict=True)
            ],
            "Nominal parameter/decision authority differs",
        )
        parameters["PPE"] = [means[t] for t in inputs.AXIS]
        parameters["sensitivity"] = context
        decision["baseline_protocol"] = decision["protocol"]
        decision["protocol"] = protocol
        decision["sensitivity"] = {
            **context,
            "baseline_decision_sha256": old_pins[name + "/decision.json"]["sha256"],
        }
        for item in template["parameters"]:
            item["ppe"] = means[item["taxon"]]
        template["versions"]["parameters"] = SCHEMA
        for member, value in (("parameters", parameters), ("decision", decision)):
            raw = encoded(value)
            buffers[name + "/" + member + ".json"] = raw
            matches = [x for x in template["evidence"] if x["role"] == member]
            require(
                len(matches) == 1 and matches[0]["path"] == member + ".json",
                "Evidence role differs",
            )
            matches[0]["sha256"] = hashlib.sha256(raw).hexdigest()
        raw = encoded(experiment)
        buffers[name + "/experiment.json"] = raw
        index["experiments"][position]["experiment"]["sha256"] = hashlib.sha256(
            raw
        ).hexdigest()
    index["sensitivity"] = context
    buffers["inputs.json"] = encoded(index)
    require(
        len(buffers) == 80
        and all(len(raw) <= 65536 for raw in buffers.values())
        and sum(map(len, buffers.values())) <= 2097152,
        "Scenario input budget differs",
    )
    workflow.input_scope(nominal_root, nominal_manifest, nominal_manifest_sha256)
    return buffers, context


def materialize(
    repository: Path,
    nominal_root: Path,
    nominal_manifest: Path,
    nominal_manifest_sha256: str,
    output: Path,
    output_manifest: Path,
    *,
    scenario_id: str,
    protocol_sha256: str,
) -> dict[str, Any]:
    """Write one fresh 80-member scenario and exercise all 18 real request readers."""
    buffers, context = derive(
        repository,
        nominal_root,
        nominal_manifest,
        nominal_manifest_sha256,
        scenario_id,
        protocol_sha256,
    )
    for path in (output, output_manifest):
        workflow.physical(path)
        workflow.require(not path.exists(), "Absent scenario output required")
        workflow.require(
            path != nominal_root
            and nominal_root not in path.parents
            and path not in nominal_root.parents,
            "Scenario output overlaps nominal inputs",
        )
    workflow.require(
        output not in output_manifest.parents and output != output_manifest,
        "Manifest must be outside scenario inputs",
    )
    output.mkdir(parents=True)
    for name, raw in buffers.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
    manifest = [
        {"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        for name, raw in sorted(buffers.items())
    ]
    raw = encoded(manifest)
    with output_manifest.open("xb") as stream:
        stream.write(raw)
    workflow.input_scope(output, output_manifest, hashlib.sha256(raw).hexdigest())
    admission = inputs.admit(output)
    return {
        **context,
        "input_manifest": pin(output_manifest, raw),
        "reader_admission": admission,
    }


def run_scenario(
    repository: Path,
    nominal_root: Path,
    nominal_manifest: Path,
    nominal_manifest_sha256: str,
    input_root: Path,
    input_manifest: Path,
    input_manifest_sha256: str,
    output: Path,
    *,
    scenario_id: str,
    protocol_sha256: str,
    phase: str,
    execution_epoch: str,
    prediction_index: Path | None = None,
    prediction_index_sha256: str | None = None,
) -> dict[str, Any]:
    """Verify the entire derived scenario before delegating to the existing batch."""
    expected, context = derive(
        repository,
        nominal_root,
        nominal_manifest,
        nominal_manifest_sha256,
        scenario_id,
        protocol_sha256,
    )
    _, pins = workflow.input_scope(input_root, input_manifest, input_manifest_sha256)
    for row in pins:
        raw, _ = workflow.read(input_root / row["path"], row["sha256"], 65536)
        workflow.require(raw == expected[row["path"]], "Scenario derivation differs")
    return workflow.batch(
        input_root,
        input_manifest,
        input_manifest_sha256,
        output,
        phase=phase,
        execution_epoch=execution_epoch,
        prediction_index=prediction_index,
        prediction_index_sha256=prediction_index_sha256,
        protocol_binding=context["protocol"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("operation", choices=("materialize", "prepare", "score"))
    for name in (
        "repository",
        "nominal-root",
        "nominal-manifest",
        "input-root",
        "input-manifest",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--nominal-manifest-sha256", required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--scenario", choices=tuple(SCENARIOS), required=True)
    parser.add_argument("--input-manifest-sha256")
    parser.add_argument("--execution-epoch")
    parser.add_argument("--prediction-index", type=Path)
    parser.add_argument("--prediction-index-sha256")
    args = parser.parse_args()
    common = (
        args.repository,
        args.nominal_root,
        args.nominal_manifest,
        args.nominal_manifest_sha256,
    )
    if args.operation == "materialize":
        workflow.require(
            args.output == args.input_root,
            "Materializer output must name its input root",
        )
        result = materialize(
            *common,
            args.input_root,
            args.input_manifest,
            scenario_id=args.scenario,
            protocol_sha256=args.protocol_sha256,
        )
    else:
        workflow.require(
            args.input_manifest_sha256 is not None and args.execution_epoch is not None,
            "Input identity and epoch required",
        )
        result = run_scenario(
            *common,
            args.input_root,
            args.input_manifest,
            args.input_manifest_sha256,
            args.output,
            scenario_id=args.scenario,
            protocol_sha256=args.protocol_sha256,
            phase=args.operation,
            execution_epoch=args.execution_epoch,
            prediction_index=args.prediction_index,
            prediction_index_sha256=args.prediction_index_sha256,
        )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
