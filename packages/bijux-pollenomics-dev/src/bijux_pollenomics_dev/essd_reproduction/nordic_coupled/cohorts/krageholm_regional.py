"""Use a permanently training Krageholm source for conditional small-place prediction."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import time
from typing import Any, cast

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.essd_reproduction.author_lra_development import _rings
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import inputs as nominal
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import workflow as shared
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import (
    Core,
    buffer,
    decode,
    digest,
    load,
    require,
)

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/krageholm-regional-coupled/protocol.json"
)
SCHEMA = "krageholm-regional-coupled"
METHODS = shared.METHODS
NAMES = shared.NAMES
SMALL = ("BOKE", "BUS", "SOLSOE83")
AUDIT = {
    "path": "artifacts/physical-core/krageholm-regional-source-support/native-run/result.json",
    "bytes": 274758,
    "sha256": "7d19b911ffe54c0fe97b2de973bc85b7150ded6e37550d571ff838b108353c30",
}


def revision(repository: Path) -> str:
    """Require the maintained consumer and its directly consumed source to be committed."""
    paths = [
        str(PROTOCOL),
        str(Path(__file__).resolve().relative_to(repository)),
        "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra_validation",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/nordic_coupled/inputs.py",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/nordic_coupled/workflow.py",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/physical_forward/inputs.py",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/author_lra_development.py",
    ]
    git = ["git", "-C", str(repository)]
    head = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    subprocess.run(
        [*git, "ls-files", "--error-unmatch", "--", *paths[:2]],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [*git, "diff", "--exit-code", head, "--", *paths],
        check=True,
        capture_output=True,
    )
    return head


def pinned(repository: Path, pin: dict[str, Any], maximum: int = 4194304) -> Any:
    """Read a confined JSON source with its declared hash and byte count."""
    relative = Path(pin["path"])
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "Confined source pin required",
    )
    raw, value = shared.read(repository / relative, pin["sha256"], maximum)
    require(len(raw) == pin["bytes"], "Pinned source size differs")
    return value


def declaration(repository: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read the fixed-cohort protocol and check its axes and source audit."""
    raw = (repository / PROTOCOL).read_bytes()
    protocol = decode(raw)
    require(
        protocol["schema_version"] == SCHEMA + "-protocol.v1"
        and protocol["krag_audit"] == AUDIT
        and protocol["axis"] == list(nominal.AXIS)
        and protocol["windows_cal_bp"] == [list(w) for w in nominal.WINDOWS]
        and protocol["population"]["methods"] == list(METHODS),
        "Declared cohort contract differs",
    )
    return protocol, {"path": str(PROTOCOL), "sha256": digest(raw), "bytes": len(raw)}


def anchor_windows(
    audit: dict[str, Any], protocol: dict[str, Any]
) -> list[dict[str, Any]]:
    """Validate all original owners before consuming only the qualified six bins."""
    identity = protocol["krag_identity"]
    require(
        audit["schema_version"] == "krageholm-regional-source-support.v1"
        and audit["status"] == "literal_source_support_accounted"
        and audit["identity"]
        == {
            key: identity[key]
            for key in (
                "site_id",
                "dataset_id",
                "collection_unit_id",
                "handle",
                "source_sample_count",
            )
        }
        and audit["chronology"]["selected_chronology_id"]
        == identity["selected_chronology_id"]
        == 13366
        and audit["chronology"]["native_collection_default_reference"]
        == identity["native_collection_default_reference"]
        == 13365,
        "Closed Krageholm source/chronology identity differs",
    )
    flags = {
        str(row["chronology_id"]): row["native_metadata"]["isdefault"]
        for row in audit["chronology"]["source_chronology_declarations"]
    }
    require(
        all(
            flags.get(key) is value
            for key, value in identity["source_default_flags"].items()
        ),
        "Native chronology flags differ",
    )
    samples = audit["samples"]
    require(
        type(samples) is list
        and len(samples) == 96
        and [row["native_sample_index"] for row in samples] == list(range(96))
        and all(type(row["sample_id"]) is int for row in samples)
        and len({row["sample_id"] for row in samples}) == 96,
        "Complete original96-owner population required",
    )
    for row in samples:
        require(
            row["selected_age_status"] == "selected_typed_point"
            and row["selected_age"]["chronologyid"] == 13366,
            "Unassignable selected age cannot be dropped",
        )
        age = row["selected_age"]["age"]
        matches = [
            list(window) for window in nominal.WINDOWS if window[0] <= age < window[1]
        ]
        require(
            row["window"] == (matches[0] if matches else None),
            "Source age/window membership differs",
        )
        expected = (
            "negative_native_age_retained"
            if age < 0
            else "in_requested_window"
            if matches
            else "outside_requested_windows"
        )
        require(
            row["age_disposition"] == expected, "Original source disposition differs"
        )
    windows = audit["windows"]
    require(
        [row["window"] for row in windows] == [list(w) for w in nominal.WINDOWS],
        "Six ordered Krageholm windows required",
    )
    for row in windows:
        members = [sample for sample in samples if sample["window"] == row["window"]]
        require(
            row["status"] == "supported"
            and not row["unassignable_source_sample_ids"]
            and row["sample_ids"] == [sample["sample_id"] for sample in members]
            and row["member_count"] == len(members)
            and bool(members),
            "Complete supported Krageholm membership required",
        )
        require(
            all(
                sample["panel_complete"] is True
                and sample["pollen_denominator_status"] == "complete"
                and [taxon["label"] for taxon in sample["taxa"]] == list(nominal.AXIS)
                and [taxon["taxon_id"] for taxon in sample["taxa"]] == [29, 310]
                and all(type(n) is int and n >= 0 for n in sample["panel_counts"])
                and len(sample["panel_counts"]) == 2
                and type(sample["pollen_N"]) is int
                and sample["pollen_N"] >= sum(sample["panel_counts"])
                for sample in members
            ),
            "Missing/invalid literal source count refused",
        )
        counts = [
            sum(sample["panel_counts"][axis] for sample in members) for axis in range(2)
        ]
        require(
            row["panel_counts"] == counts
            and row["panel_N"] == sum(counts)
            and 0 < sum(counts) <= 2**53
            and row["pollen_N"] == sum(sample["pollen_N"] for sample in members)
            and row["excluded_pollen_N"] == row["pollen_N"] - sum(counts),
            "Krageholm panel/full/excluded mass differs",
        )
    require(
        sum(row["member_count"] for row in windows) == 19,
        "Original selected19-owner support differs",
    )
    return cast(list[dict[str, Any]], windows)


def small_windows(
    cores: tuple[Core, ...],
    protocol: dict[str, Any],
    references: dict[str, list[dict[str, Any]]],
    supports: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Reuse exact qualified count tokens and membership fingerprints, never rounded fractions."""
    selected = {core.id: core for core in cores if core.id in SMALL}
    require(
        len(selected) == 3 and len([core for core in cores if core.id in SMALL]) == 3,
        "Three unique qualified small cores required",
    )
    result: dict[str, list[dict[str, Any]]] = {}
    for expected in protocol["small_cores"]:
        core = selected[expected["id"]]
        require(
            (core.site, core.dataset, core.collection_unit)
            == (expected["site"], expected["dataset"], expected["collection_unit"]),
            "Small physical source identity differs",
        )
        require(
            all(taxon in core.axis for taxon in nominal.AXIS),
            "Small source literal axis missing",
        )
        indices = [core.axis.index(taxon) for taxon in nominal.AXIS]
        require(
            [core.ppe[i] for i in indices] == [5.106, 1.27]
            and [core.sd[i] for i in indices] == [0.303, 0.05],
            "Old fixed parameters differ",
        )
        rows = []
        for name, window in zip(NAMES, nominal.WINDOWS, strict=True):
            cells = [cell for cell in core.cells if cell.window == window]
            require(len(cells) == 1, "One exact old source window required")
            cell = cells[0]
            require(
                len(cell.counts) == len(core.axis)
                and all(type(n) is int and n >= 0 for n in cell.counts),
                "Native integer small source counts required",
            )
            counts = [cell.counts[i] for i in indices]
            require(0 < sum(counts) <= 2**53, "Positive measured panel required")
            proofs = [
                row
                for row in references[name]
                if row["native_dataset"] == core.dataset
                and row["native_collection_unit"] == core.collection_unit
            ]
            require(len(proofs) == 1, "One exact original public projection required")
            proof = proofs[0]
            require(
                proof["native_site"] == core.site
                and all(
                    type(proof[field]) is int
                    for field in (
                        "source_panel_N",
                        "projected_panel_N",
                        "excluded_panel_N",
                    )
                )
                and proof["selected_chronology"] == expected["chronology"]
                and proof["source_axis"] == list(core.axis)
                and proof["projected_axis"] == list(nominal.AXIS)
                and proof["source_panel_N"] == sum(cell.counts)
                and proof["projected_panel_N"] == sum(counts)
                and proof["excluded_panel_N"] == sum(cell.counts) - sum(counts)
                and proof["source_support_sha256"] == cell.source_support_sha256,
                "Old count/membership projection changed",
            )
            source_support = [
                row for row in supports[core.id] if row["window"] == list(window)
            ]
            require(
                len(source_support) == 1
                and type(source_support[0]["native_sample_count"]) is int
                and source_support[0]["native_sample_count"] > 0
                and source_support[0]["source_support_sha256"]
                == cell.source_support_sha256,
                "Qualified native sample support count differs",
            )
            rows.append(
                {
                    "window": list(window),
                    "counts": counts,
                    "original_projection": deepcopy(proof),
                    "qualified_source_support": deepcopy(source_support[0]),
                }
            )
        result[core.id] = rows
    return result


def project(
    cores: tuple[Core, ...],
    audit: dict[str, Any],
    protocol: dict[str, Any],
    references: dict[str, list[dict[str, Any]]],
    supports: dict[str, list[dict[str, Any]]],
    output: Path,
) -> dict[str, Any]:
    """Create only the minimal current native inputs; no archived executable namespace."""
    shared.physical(output)
    require(not output.exists(), "Fresh input destination required")
    anchor = anchor_windows(audit, protocol)
    small = small_windows(cores, protocol, references, supports)
    require(
        [row["id"] for row in protocol["small_cores"]] == list(SMALL),
        "Small target population differs",
    )
    output.mkdir()
    experiments = []
    for index, name in enumerate(NAMES):
        directory = output / name
        directory.mkdir()
        window = list(nominal.WINDOWS[index])
        authority = [
            {
                "core": code,
                **small[code][index]["original_projection"],
                "qualified_source_support": small[code][index][
                    "qualified_source_support"
                ],
            }
            for code in SMALL
        ]
        authority.append(
            {
                "core": "KRAGMJNY",
                "native_site": 3204,
                "native_dataset": 23013,
                "native_collection_unit": 16622,
                "selected_chronology": 13366,
                "native_collection_default_reference": 13365,
                "source_default_flags": {"13365": True, "13366": True},
                "native_sample_ids": anchor[index]["sample_ids"],
                "projected_panel_N": anchor[index]["panel_N"],
                "reported_pollen_N": anchor[index]["pollen_N"],
                "excluded_pollen_N": anchor[index]["excluded_pollen_N"],
                "source_audit": protocol["krag_audit"],
            }
        )
        evidence = []
        for role in ("chronology", "taxa", "parameters", "dependency_lock", "decision"):
            value = {
                "role": role,
                "protocol": str(PROTOCOL),
                "fixed_source_identities": [
                    {
                        "core": source["id"],
                        "site": source["site"],
                        "dataset": source["dataset"],
                        "collection_unit": source["collection_unit"],
                        "chronology": source["chronology"],
                    }
                    for source in protocol["small_cores"]
                ]
                + [
                    {
                        "core": "KRAGMJNY",
                        "site": 3204,
                        "dataset": 23013,
                        "collection_unit": 16622,
                        "chronology": 13366,
                        "native_collection_default_reference": 13365,
                        "source_default_flags": {"13365": True, "13366": True},
                    }
                ],
                "window_cal_bp": window,
                "source_epochs": protocol["small_source_epochs"],
                "scope": protocol["scientific_scope"],
            }
            if role == "decision":
                value["declared_assumptions"] = {
                    key: protocol[key]
                    for key in (
                        "roles",
                        "geometry_and_method",
                        "uncertainty_omissions",
                        "rights",
                        "comparison_scope",
                    )
                }
            if role == "parameters":
                value["parameters"] = protocol["parameters"]
            if role == "dependency_lock":
                value["actual_dependency_lock"] = protocol["dependency_lock"]
            reference = nominal.store(directory, role + ".json", value)
            evidence.append({"evidence_id": role, "role": role, **reference})
        sites = []
        for code in (*SMALL, "KRAGMJNY"):
            regional = code == "KRAGMJNY"
            source = (
                {
                    "id": code,
                    "site": 3204,
                    "dataset": 23013,
                    "collection_unit": 16622,
                    **protocol["krag_geometry"],
                }
                if regional
                else protocol["small_cores"][SMALL.index(code)]
            )
            record = f"neotoma-{source['dataset']}-{source['collection_unit']}-{name}"
            metadata = {
                "site_id": f"neotoma-site-{source['site']}",
                "sample_id": record,
                "coordinate": window[0],
                "bin_id": name,
                "age_type": "calendar_bp",
                "age_support_bp": [window],
                "chronology_evidence_id": "chronology",
            }
            radius = source["radius_m"]
            geometry = {
                "basin": {"diameter_m": 2 * radius, "site_type": "lake"},
                "sample_metadata": metadata,
                "longitude": source["longitude"],
                "latitude": source["latitude"],
            }
            if not regional:
                geometry.update(
                    inversion_rings=_rings(radius, inversion=True)[:2],
                    forward_rings=_rings(radius, inversion=False),
                )
            counts = (
                anchor[index]["panel_counts"]
                if regional
                else small[code][index]["counts"]
            )
            sites.append(
                {
                    "record_id": record,
                    "site_id": metadata["site_id"],
                    "identity_keys": [
                        metadata["site_id"],
                        f"neotoma-collection-{source['collection_unit']}",
                    ],
                    "raw": nominal.store(
                        directory,
                        code + "-raw.json",
                        {
                            "data_kind": "source_observations",
                            "taxa": list(nominal.AXIS),
                            "sample": {**metadata, "counts": counts},
                        },
                    ),
                    "geometry": nominal.store(
                        directory, code + "-geometry.json", geometry
                    ),
                }
            )
        targets = [site["record_id"] for site in sites[:-1]]
        template = {
            "schema_version": "lra-request.v1",
            "operation": "lra",
            "data_kind": "source_observations",
            "purpose": "exploratory",
            "method_profile": "disqover-0.9.14-source-compatible",
            "taxa": list(nominal.AXIS),
            "pollen_unit": "count",
            "configuration": deepcopy(protocol["configuration"]),
            "parameters": protocol["parameters"],
            "evidence": evidence,
            "exclusions": [],
            "uncertainty_omissions": protocol["uncertainty_omissions"],
            "temporal_matching": {
                "rule": "declared_bin_stationarity",
                "decision_evidence_id": "decision",
                "bins": [
                    {"bin_id": name, "younger_bp": window[0], "older_bp": window[1]}
                ],
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
            "target_record_ids": targets,
            "regional_priority": [sites[-1]["record_id"]],
            "baselines": list(METHODS),
            "local_ring_count": 2,
            "local_support_radius_m": 1000,
            "support_profile": "same-outer-radius-homogeneous-v1",
            "request_template": template,
        }
        reference = nominal.store(directory, "experiment.json", payload)
        nominal.store(directory, "projection.json", authority)
        experiments.append(
            {
                "directory": name,
                "experiment": reference,
                "target_record_ids": targets,
                "regional_source_record_id": sites[-1]["record_id"],
            }
        )
    members = [
        {
            "path": path.relative_to(output).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": digest(path.read_bytes()),
        }
        for path in sorted(output.rglob("*.json"))
    ]
    return {
        "schema_version": SCHEMA + "-inputs.v1",
        "experiments": experiments,
        "members": members,
        "source_population": {
            "krag_original_owners": 96,
            "krag_selected_owners": 19,
            "krag_age_dispositions": audit["population"]["age_disposition_counts"],
            "krag_panel_complete_samples": audit["population"][
                "panel_complete_samples"
            ],
            "krag_sourcewide_panel_status": audit["source_totals"]["status"],
            "small_selected_sample_supports": sum(
                row["qualified_source_support"]["native_sample_count"]
                for rows in small.values()
                for row in rows
            ),
        },
        "krag_audit": protocol["krag_audit"],
        "scientific_acceptance": "not_evaluated",
    }


def qualified_supports(
    repository: Path, matched: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    """Retain the original aggregate sample counts and their explicit saved selectors."""
    result = {}
    for kind, codes in (
        ("swedish_report", ("BOKE", "BUS")),
        ("nordic_report", ("SOLSOE83",)),
    ):
        pin = matched["inputs"][kind]
        report = pinned(repository, pin)
        for code in codes:
            candidates = (
                [row for row in report["cores"] if row["metadata_code"] == code]
                if kind == "swedish_report"
                else [
                    row
                    for row in report["cases"]
                    if row["source_handle"] == code
                    and row["case_id"] == "4446.metadata_static_radius"
                ]
            )
            require(len(candidates) == 1, "Qualified source support owner differs")
            rows = candidates[0]["results"]
            if kind == "swedish_report":
                rows = [
                    row for row in rows if row["profile"] == "metadata_radius_wind_3"
                ]
            key = (
                "local_native_sample_support_sha256"
                if kind == "swedish_report"
                else "local_actual_source_support_sha256"
            )
            selector = (
                f"cores[metadata_code=={code}].results[profile==metadata_radius_wind_3]"
                if kind == "swedish_report"
                else "cases[case_id==4446.metadata_static_radius].results"
            )
            result[code] = [
                {
                    "window": [row["younger_cal_bp"], row["older_cal_bp_exclusive"]],
                    "native_sample_count": row["native_sample_count"],
                    "source_support_sha256": row[key],
                    "source_report": pin,
                    "source_selector": selector,
                }
                for row in rows
                if (row["younger_cal_bp"], row["older_cal_bp_exclusive"])
                in nominal.WINDOWS
            ]
    return result


def materialize(repository: Path, output: Path) -> dict[str, Any]:
    """Project pinned source support into the fixed-regional input inventory."""
    started = time.monotonic()
    repository = repository.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    head = revision(repository)
    protocol, protocol_pin = declaration(repository)
    audit = pinned(repository, protocol["krag_audit"])
    require(type(audit) is dict, "Literal audit object required")
    old = pinned(repository, protocol["small_protocol"])
    require(
        type(old) is dict
        and old["cores"] == protocol["small_cores"]
        and old["source_epochs"] == protocol["small_source_epochs"],
        "Old source/geometry declaration differs",
    )
    metadata = pinned(repository, protocol["krag_geometry"]["native_coordinate_source"])
    require(type(metadata) is dict, "Native metadata object required")
    matching = [
        row["source_payload"]
        for row in metadata["rows"]
        if row["source_site_id"] == 3204
    ]
    require(
        len(matching) == 1
        and json.loads(matching[0]["geography"])["coordinates"]
        == [
            protocol["krag_geometry"]["longitude"],
            protocol["krag_geometry"]["latitude"],
        ],
        "Native Krageholm coordinate identity differs",
    )
    references = {
        name: pinned(repository, protocol["old_projections"][name]) for name in NAMES
    }
    lock = protocol["dependency_lock"]
    buffer(repository / lock["path"], lock["sha256"], lock["bytes"])
    cores, matched, source_pins = load(repository)
    require(
        matched["source_epochs"] == protocol["small_source_epochs"],
        "Qualified source epochs differ",
    )
    supports = qualified_supports(repository, matched)
    result = project(cores, audit, protocol, references, supports, output)
    result.update(
        source_commit=head, protocol=protocol_pin, qualified_source_inputs=source_pins
    )
    for pin in source_pins:
        buffer(Path(pin["path"]), pin["sha256"], pin["bytes"])
    for pin in (
        protocol["small_protocol"],
        protocol["krag_geometry"]["native_coordinate_source"],
        *protocol["old_projections"].values(),
    ):
        pinned(repository, pin)
    buffer(repository / lock["path"], lock["sha256"], lock["bytes"])
    require(
        revision(repository) == head
        and pinned(repository, protocol["krag_audit"]) == audit,
        "Consumed source changed during input projection",
    )
    result["elapsed_seconds"] = time.monotonic() - started
    nominal.store(output, "inputs.json", result)
    enforce_budget(
        output, protocol["resources"]["materialize"], result["elapsed_seconds"]
    )
    return result


def read_inputs(
    repository: Path, index: Path, checksum: str, *, include_observations: bool = False
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Open structural members only unless all prediction products have closed."""
    protocol, protocol_pin = declaration(repository)
    raw, data = shared.read(index, checksum, 2097152)
    require(
        data["schema_version"] == SCHEMA + "-inputs.v1"
        and data["protocol"] == protocol_pin
        and data["krag_audit"] == AUDIT
        and [row["directory"] for row in data["experiments"]] == list(NAMES),
        "Frozen input index differs",
    )
    expected = {
        f"{name}/{member}.json"
        for name in NAMES
        for member in (
            "chronology",
            "taxa",
            "parameters",
            "dependency_lock",
            "decision",
            "experiment",
            "projection",
            *[
                code + suffix
                for code in (*SMALL, "KRAGMJNY")
                for suffix in ("-raw", "-geometry")
            ],
        )
    }
    require(
        len(data["members"]) == len(expected) == 90
        and {row["path"] for row in data["members"]} == expected,
        "Complete minimal90-member input namespace required",
    )
    quantitative = {
        name for name in expected if name.endswith(("-raw.json", "/projection.json"))
    }
    for member in data["members"]:
        if include_observations or member["path"] not in quantitative:
            pinned(index.parent, member, 65536)
    actual = {
        path.relative_to(index.parent).as_posix()
        for path in index.parent.rglob("*")
        if path.is_file()
    }
    require(actual == expected | {"inputs.json"}, "Unlisted input member refused")
    require(
        data["source_commit"] == revision(repository),
        "Prepared inputs use another source revision",
    )
    return data, protocol, {"path": str(index), "sha256": checksum, "bytes": len(raw)}


def enforce_budget(output: Path, budget: dict[str, Any], elapsed: float) -> None:
    """Check artifact file types and declared wall-time and byte limits."""
    sizes = []
    for path in output.rglob("*"):
        shared.physical(path)
        require(path.is_dir() or path.is_file(), "Special owned artifact refused")
        if path.is_file():
            require(path.stat().st_nlink == 1, "Hard-linked owned artifact refused")
            sizes.append(path.stat().st_size)
    require(
        elapsed <= budget["wall_seconds"] and sum(sizes) <= budget["output_bytes"],
        "Declared wall/output resource budget exceeded",
    )


def run(
    repository: Path,
    index: Path,
    checksum: str,
    output: Path,
    *,
    operation: str,
    prediction_index: Path | None = None,
    prediction_sha256: str | None = None,
) -> dict[str, Any]:
    """Separate complete prediction publication from subsequent outcome access."""
    started = time.monotonic()
    repository, index = repository.resolve(strict=True), index.absolute()
    output = require_absent_artifact_output(repository, output)
    require(operation in {"prepare", "score"}, "Declared native operation required")
    head = revision(repository)
    inputs, protocol, input_pin = read_inputs(repository, index, checksum)
    api = shared.apis()
    specs = []
    from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out

    for row in inputs["experiments"]:
        directory = index.parent / row["directory"]
        _, payload = shared.read(
            directory / row["experiment"]["path"], row["experiment"]["sha256"], 65536
        )
        spec = api["spec"](payload)
        require(
            spec.target_record_ids == tuple(row["target_record_ids"])
            and spec.regional_priority == (row["regional_source_record_id"],)
            and len(spec.sites) == 4,
            "Exact source and target roles required",
        )
        folds = grouped_leave_one_out(
            [site.record for site in spec.sites],
            target_record_ids=spec.target_record_ids,
        )
        require(
            len(folds) == 3
            and all(
                len(fold.train_record_ids) == 3 and len(fold.test_record_ids) == 1
                for fold in folds
            ),
            "Three complete target folds required",
        )
        specs.append((row, spec, folds))
    prior = None
    if operation == "score":
        require(
            prediction_index is not None and prediction_sha256 is not None,
            "Closed prediction batch identity required",
        )
        assert prediction_index is not None and prediction_sha256 is not None
        _, prior = shared.read(prediction_index.absolute(), prediction_sha256, 2097152)
        require(
            prior["schema_version"] == SCHEMA + "-batch.v1"
            and prior["operation"] == "prepare"
            and prior["all_bins_accounted"] is True
            and prior["source_commit"] == head
            and prior["input_index"] == input_pin
            and [row["bin"] for row in prior["bins"]] == list(NAMES),
            "Closed complete prediction batch differs",
        )
        for row in prior["bins"]:
            if "prediction" in row:
                require(
                    Path(row["prediction"]["directory"])
                    == prediction_index.absolute().parent / row["bin"],
                    "Prediction directory ownership differs",
                )
                shared.prediction_receipt(
                    Path(row["prediction"]["directory"]),
                    row["prediction"]["manifest_sha256"],
                    api,
                )
        read_inputs(repository, index, checksum, include_observations=True)
    output.mkdir()
    result: dict[str, Any] = {
        "schema_version": SCHEMA + "-batch.v1",
        "operation": operation,
        "source_commit": head,
        "protocol": inputs["protocol"],
        "input_index": input_pin,
        "bins": [],
        "method_dispositions": [],
        "all_bins_accounted": False,
        "scientific_acceptance": "not_evaluated",
        "exposure": "prior_exposed_development",
    }
    if prior is not None:
        result["prediction_index"] = {
            "path": str(prediction_index),
            "sha256": prediction_sha256,
        }
        result["ordering"] = (
            "all_available_six_bin_prediction_products_authenticated_before_any_score_api"
        )
    shared.write(output, result)
    for bin_index, (entry, spec, folds) in enumerate(specs):
        name = entry["directory"]
        row = {"bin": name, "folds": [fold.as_dict() for fold in folds]}
        try:
            if operation == "prepare":
                product = api["prepare"](
                    spec,
                    input_root=index.parent / name,
                    cache_root=output / "cache" / name,
                    destination=output / name,
                    workers=1,
                )
                receipt = shared.prediction_receipt(
                    product.directory, product.manifest_sha256, api
                )
                row["prediction"] = receipt
                row["method_dispositions"] = receipt["method_dispositions"]
                _, manifest = api["product"](
                    product.directory, expected_manifest_sha256=product.manifest_sha256
                )
                row["native_batch_members"] = {
                    key: value
                    for key, value in manifest["files"].items()
                    if key.startswith("batches/")
                }
            else:
                assert prior is not None
                original = prior["bins"][bin_index]
                if "prediction" not in original:
                    row["method_dispositions"] = deepcopy(
                        original["method_dispositions"]
                    )
                    row["status"] = "prediction_unavailable"
                else:
                    prediction = original["prediction"]
                    inventory = {
                        "schema_version": "lra-source-pollen-outcomes.v1",
                        "data_kind": "source_observations",
                        "records": {
                            site.record.record_id: {
                                "path": site.raw.path,
                                "sha256": site.raw.sha256,
                            }
                            for site in spec.sites
                            if site.record.record_id in spec.target_record_ids
                        },
                    }
                    product = api["score"](
                        Path(prediction["directory"]),
                        expected_manifest_sha256=prediction["manifest_sha256"],
                        outcome_root=index.parent / name,
                        outcome_inventory=inventory,
                        destination=output / name,
                    )
                    _, manifest = api["product"](
                        product.directory,
                        expected_manifest_sha256=product.manifest_sha256,
                    )
                    scores = manifest["scientific_payload"]["scores"]
                    require(
                        len(scores) == 9, "All nine method score dispositions required"
                    )
                    row["scores"] = {
                        "directory": str(product.directory),
                        "manifest_sha256": product.manifest_sha256,
                        "scientific_content_sha256": product.scientific_content_sha256,
                    }
                    row["method_dispositions"] = [
                        {
                            "fold_id": score["fold_id"],
                            "method": score["baseline"],
                            "status": score["score"]["status"],
                        }
                        for score in scores
                    ]
            row.setdefault("status", "completed")
        except (*api["refusals"], ValueError) as error:
            row.update(
                status="refused",
                reason_code=getattr(error, "reason_code", "native_bin_refused"),
                detail=str(error),
                exception_type=type(error).__name__,
            )
            row["method_dispositions"] = [
                {
                    "fold_id": fold.fold_id,
                    "method": method,
                    "status": "refused",
                    "reason_code": row["reason_code"],
                }
                for fold in folds
                for method in METHODS
            ]
        require(
            len(row["method_dispositions"]) == 9
            and {
                (item["fold_id"], item["method"]) for item in row["method_dispositions"]
            }
            == {(fold.fold_id, method) for fold in folds for method in METHODS},
            "Exact nine-method disposition population required",
        )
        result["bins"].append(row)
        result["method_dispositions"].extend(
            {"bin": name, **item} for item in row["method_dispositions"]
        )
        shared.write(output, result)
    require(
        revision(repository) == head,
        "Consumed source revision changed during native computation",
    )
    read_inputs(repository, index, checksum)
    result.update(
        all_bins_accounted=True,
        requested_folds=18,
        requested_method_dispositions=54,
        status_counts=dict(
            Counter(item["status"] for item in result["method_dispositions"])
        ),
        elapsed_seconds=time.monotonic() - started,
    )
    shared.write(output, result)
    enforce_budget(output, protocol["resources"][operation], result["elapsed_seconds"])
    return result


def main() -> int:
    """Dispatch the fixed-regional operation and print its source summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("materialize", "prepare", "score"))
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--input-index", type=Path)
    parser.add_argument("--input-index-sha256")
    parser.add_argument("--prediction-index", type=Path)
    parser.add_argument("--prediction-index-sha256")
    args = parser.parse_args()
    if args.operation == "materialize":
        result = materialize(args.repository, args.output)
    else:
        require(
            args.input_index is not None and args.input_index_sha256 is not None,
            "Frozen input index required",
        )
        result = run(
            args.repository,
            args.input_index,
            args.input_index_sha256,
            args.output,
            operation=args.operation,
            prediction_index=args.prediction_index,
            prediction_sha256=args.prediction_index_sha256,
        )
    print(
        json.dumps(
            {
                key: result[key]
                for key in ("schema_version", "source_commit", "elapsed_seconds")
            }
            | {
                key: result[key]
                for key in (
                    "requested_folds",
                    "requested_method_dispositions",
                    "status_counts",
                )
                if key in result
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
