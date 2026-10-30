"""Bind materialized roles and integer counts to their retained source products."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .exposure import count_free_evidence
from .reading import decode, exact, pinned, read_file, relative_file
from .scalar import AXIS, METHODS, require
from .source_accounts import SMALL, WINDOWS, checked_krag, integer

MATCHED_PROTOCOL = (
    "docs/report/pollen-reconstruction/matched-pollen-forward/assumptions/protocol.json"
)
MATCHED_SHA = "22355c28b91af19e23240ce8060761fc0f1f45d6be212d04f5432127eb2e7249"
NAMES = tuple(f"cal-bp-{low}-{high}" for low, high in WINDOWS)


def support_totals(rows: dict[tuple[str, str], dict[str, Any]]) -> dict[str, int]:
    """Sum the complete set of pinned positive-integer small-core supports."""
    require(
        set(rows) == {(name, code) for name in NAMES for code in SMALL},
        "all18 qualified small-source supports required",
    )
    totals = dict.fromkeys(SMALL, 0)
    for (_, code), row in rows.items():
        fingerprint = row["source_support_sha256"]
        require(
            integer(row["native_sample_count"], positive=True)
            and type(fingerprint) is str
            and len(fingerprint) == 64
            and all(char in "0123456789abcdef" for char in fingerprint),
            "positive integer qualified sample support and native fingerprint required",
        )
        totals[code] += row["native_sample_count"]
    return totals


def record_ids(protocol: dict[str, Any], name: str) -> dict[str, str]:
    """Build source record identifiers for the declared cores and bin."""
    rows = [
        *protocol["small_cores"],
        {"id": "KRAGMJNY", "dataset": 23013, "collection_unit": 16622},
    ]
    return {
        row["id"]: f"neotoma-{row['dataset']}-{row['collection_unit']}-{name}"
        for row in rows
    }


def retained_small(
    repository: Path, inputs: dict[str, Any], protocol: dict[str, Any]
) -> dict[tuple[str, str], dict[str, Any]]:
    """Check pinned small-core sources and recover their window support."""
    pins = inputs["qualified_source_inputs"]
    first = dict(pins[0])
    require(
        Path(first["path"]) == repository / MATCHED_PROTOCOL
        and first["sha256"] == MATCHED_SHA,
        "qualified matched-source authority differs",
    )
    first["path"] = MATCHED_PROTOCOL
    _, matched = pinned(repository, first, 4 * 1024**2)
    require(
        matched["source_epochs"] == protocol["small_source_epochs"],
        "qualified saved-source epochs differ",
    )
    expected_pins = [
        {
            "path": str(repository / MATCHED_PROTOCOL),
            "sha256": MATCHED_SHA,
            "bytes": first["bytes"],
        },
        *[
            {**pin, "path": str(repository / pin["path"])}
            for pin in matched["inputs"].values()
        ],
    ]
    exact(pins, expected_pins)
    values = {
        name: pinned(repository, pin, 32 * 1024**2)[1]
        for name, pin in matched["inputs"].items()
    }
    require(
        values["swedish_report"]["producer_candidate"]
        == protocol["small_source_epochs"]["swedish"]
        and values["nordic_report"]["candidate"]
        == protocol["small_source_epochs"]["nordic"],
        "qualified original producer revisions differ",
    )
    require(
        values["swedish_report"]["protocol_sha256"]
        == matched["inputs"]["swedish_protocol"]["sha256"]
        and values["swedish_report"]["source_identity_declaration_sha256"]
        == matched["inputs"]["swedish_identity"]["sha256"]
        and values["nordic_report"]["protocol"] == values["nordic_protocol"],
        "qualified source declarations differ",
    )
    result = {}
    for declaration in protocol["small_cores"]:
        code = declaration["id"]
        swedish = code != "SOLSOE83"
        candidates = (
            [
                row
                for row in values["swedish_report"]["cores"]
                if row["metadata_code"] == code
            ]
            if swedish
            else [
                row
                for row in values["nordic_report"]["cases"]
                if row["source_handle"] == code
                and row["static_geometry"]["id"] == "metadata_static_radius"
            ]
        )
        require(len(candidates) == 1, "one qualified small source profile required")
        core = candidates[0]
        require(
            (
                core["native_site_id"],
                core["native_dataset_id"],
                core["native_collection_unit_id"],
            )
            == (
                declaration["site"],
                declaration["dataset"],
                declaration["collection_unit"],
            ),
            "qualified small physical identity differs",
        )
        axis = core["parameter_taxa"]
        require(
            len(set(axis)) == len(axis) and all(taxon in axis for taxon in AXIS),
            "literal qualified source axis differs",
        )
        indices = [axis.index(taxon) for taxon in AXIS]
        ppe = core["ppe" if swedish else "PPE"]
        require(
            [ppe[i] for i in indices] == [5.106, 1.27], "fixed source PPE means differ"
        )
        for name, window in zip(NAMES, WINDOWS, strict=True):
            rows = [
                row
                for row in core["results"]
                if row["younger_cal_bp"] == window[0]
                and row["older_cal_bp_exclusive"] == window[1]
                and (not swedish or row["profile"] == "metadata_radius_wind_3")
            ]
            require(len(rows) == 1, "one exact qualified small-source window required")
            row = rows[0]
            require(
                type(row["counts"]) is list
                and len(row["counts"]) == 1
                and len(row["counts"][0]) == len(axis)
                and all(integer(value) for value in row["counts"][0]),
                "native integer small-source counts required",
            )
            raw = row["counts"][0]
            counts = [raw[index] for index in indices]
            support = row[
                "local_native_sample_support_sha256"
                if swedish
                else "local_actual_source_support_sha256"
            ]
            require(
                integer(row["native_sample_count"], positive=True)
                and row["panel_count_denominator"] == sum(raw)
                and 0 < sum(counts) <= 2**53,
                "qualified small-source sample/count support differs",
            )
            if not swedish:
                require(
                    row["actual_source_panel_presence"] is True
                    and row["assumed_zero_cells"] == 0,
                    "unmeasured Nordic source cells cannot become zero",
                )
            result[(name, code)] = {
                "counts": counts,
                "source_axis": axis,
                "source_panel_N": sum(raw),
                "projected_panel_N": sum(counts),
                "excluded_panel_N": sum(raw) - sum(counts),
                "source_support_sha256": support,
                "native_sample_count": row["native_sample_count"],
            }
            result[(name, code)]["qualified_source_support"] = {
                "window": [row["younger_cal_bp"], row["older_cal_bp_exclusive"]],
                "native_sample_count": row["native_sample_count"],
                "source_support_sha256": support,
                "source_report": matched["inputs"][
                    "swedish_report" if swedish else "nordic_report"
                ],
                "source_selector": f"cores[metadata_code=={code}].results[profile==metadata_radius_wind_3]"
                if swedish
                else "cases[case_id==4446.metadata_static_radius].results",
            }
    support_totals(result)
    return result


def geometry(
    declaration: dict[str, Any], metadata: dict[str, Any], *, regional: bool
) -> dict[str, Any]:
    """Build basin metadata and local-only reconstruction ring geometry."""
    radius = declaration["radius_m"]
    value = {
        "basin": {"diameter_m": 2 * radius, "site_type": "lake"},
        "sample_metadata": metadata,
        "longitude": declaration["longitude"],
        "latitude": declaration["latitude"],
    }
    if not regional:
        for key, edges in (
            ("inversion_rings", [radius + 1, 500, 1000]),
            ("forward_rings", [radius, 500, 1000, 10000, 100000]),
        ):
            value[key] = [
                {
                    "inner_m": low,
                    "outer_m": high,
                    "mean_m": (low + high) / 2,
                    "ring_area_m2": math.pi * (high**2 - low**2),
                    "terrestrial_area_m2": math.pi * (high**2 - low**2),
                }
                for low, high in zip(edges[:-1], edges[1:], strict=True)
            ]
    return value


def check_materialization(
    repository: Path, input_path: Path, inputs: dict[str, Any], protocol: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Check the input inventory against pinned source and geometry declarations."""
    _, audit = pinned(repository, protocol["krag_audit"], 2 * 1024**2)
    krag = checked_krag(audit)
    _, prior = pinned(repository, protocol["small_protocol"], 1024**2)
    exact(prior["cores"], protocol["small_cores"])
    exact(prior["source_epochs"], protocol["small_source_epochs"])
    small = retained_small(repository, inputs, protocol)
    _, coordinate_source = pinned(
        repository, protocol["krag_geometry"]["native_coordinate_source"], 1024**2
    )
    coordinates = [
        json.loads(row["source_payload"]["geography"])["coordinates"]
        for row in coordinate_source["rows"]
        if row["source_site_id"] == 3204
    ]
    require(
        coordinates == [[13.74492, 55.50078]]
        and protocol["krag_geometry"]["radius_m"] == 837.0,
        "declared native point/static basin hypothesis differs",
    )
    source_population = {
        "krag_original_owners": 96,
        "krag_selected_owners": 19,
        "krag_age_dispositions": audit["population"]["age_disposition_counts"],
        "krag_panel_complete_samples": audit["population"]["panel_complete_samples"],
        "krag_sourcewide_panel_status": audit["source_totals"]["status"],
        "small_selected_sample_supports": sum(
            row["native_sample_count"] for row in small.values()
        ),
    }
    exact(inputs["source_population"], source_population)
    require(
        inputs["schema_version"] == "krageholm-regional-coupled-inputs.v1"
        and inputs["krag_audit"] == protocol["krag_audit"]
        and inputs["scientific_acceptance"] == "not_evaluated",
        "materialization identity/posture differs",
    )
    members = inputs["members"]
    names = [row["path"] for row in members]
    expected_names = {
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
        len(names) == len(set(names)) == 90 and set(names) == expected_names,
        "exact90 owned input members required",
    )
    bodies = {row["path"]: pinned(input_path.parent, row, 65536)[1] for row in members}
    actual = {
        path.relative_to(input_path.parent).as_posix()
        for path in input_path.parent.rglob("*")
        if path.is_file()
    }
    require(
        actual == expected_names | {"inputs.json"}, "unlisted materialized input file"
    )
    require(
        [entry["directory"] for entry in inputs["experiments"]] == list(NAMES),
        "six ordered input experiments required",
    )
    output = {}
    for index, name in enumerate(NAMES):
        window = protocol["windows_cal_bp"][index]
        entry = inputs["experiments"][index]
        experiment = bodies[name + "/experiment.json"]
        require(
            entry["experiment"]["path"] == "experiment.json",
            "exact input experiment owner required",
        )
        exact(
            decode(
                read_file(
                    input_path.parent / name / "experiment.json",
                    65536,
                    entry["experiment"]["sha256"],
                )
            ),
            experiment,
        )
        ids = record_ids(protocol, name)
        require(
            entry["target_record_ids"]
            == experiment["target_record_ids"]
            == [ids[code] for code in SMALL]
            and entry["regional_source_record_id"] == ids["KRAGMJNY"]
            and experiment["regional_priority"] == [ids["KRAGMJNY"]]
            and experiment["baselines"] == list(METHODS),
            "permanent regional/target roles differ",
        )
        require(
            experiment["local_ring_count"] == 2
            and experiment["local_support_radius_m"] == 1000
            and experiment["support_profile"] == "same-outer-radius-homogeneous-v1",
            "fixed local reconstruction support differs",
        )
        require(
            [site["record_id"] for site in experiment["sites"]] == list(ids.values()),
            "four exact source families required",
        )
        template = experiment["request_template"]
        exact(template["parameters"], protocol["parameters"])
        exact(template["configuration"], protocol["configuration"])
        require(
            template["taxa"] == list(AXIS)
            and template["uncertainty_omissions"] == protocol["uncertainty_omissions"],
            "fixed response/uncertainty scope differs",
        )
        _, old_projection = pinned(repository, protocol["old_projections"][name], 65536)
        projection = bodies[name + "/projection.json"]
        require(len(projection) == 4, "complete source authority required")
        for site, code in zip(experiment["sites"], ids, strict=True):
            regional = code == "KRAGMJNY"
            declaration = (
                {"site": 3204, "collection_unit": 16622, **protocol["krag_geometry"]}
                if regional
                else protocol["small_cores"][SMALL.index(code)]
            )
            metadata = {
                "site_id": f"neotoma-site-{declaration['site']}",
                "sample_id": ids[code],
                "coordinate": window[0],
                "bin_id": name,
                "age_type": "calendar_bp",
                "age_support_bp": [window],
                "chronology_evidence_id": "chronology",
            }
            counts = (
                krag[name]["panel_counts"]
                if regional
                else small[(name, code)]["counts"]
            )
            exact(
                bodies[name + "/" + code + "-raw.json"],
                {
                    "data_kind": "source_observations",
                    "taxa": list(AXIS),
                    "sample": {**metadata, "counts": counts},
                },
            )
            require(
                site["site_id"] == metadata["site_id"]
                and site["identity_keys"]
                == [
                    metadata["site_id"],
                    f"neotoma-collection-{declaration['collection_unit']}",
                ],
                "literal source family aliases differ",
            )
            exact(
                bodies[name + "/" + code + "-geometry.json"],
                geometry(declaration, metadata, regional=regional),
            )
            for role in ("raw", "geometry"):
                relative = name + "/" + site[role]["path"]
                body = read_file(
                    relative_file(input_path.parent, relative),
                    65536,
                    site[role]["sha256"],
                )
                exact(
                    decode(body),
                    bodies[
                        name
                        + "/"
                        + code
                        + ("-raw.json" if role == "raw" else "-geometry.json")
                    ],
                )
            authority = projection[list(ids).index(code)]
            if regional:
                require(
                    authority["native_sample_ids"] == krag[name]["sample_ids"]
                    and authority["projected_panel_N"] == sum(counts)
                    and authority["reported_pollen_N"] == krag[name]["pollen_N"]
                    and authority["excluded_pollen_N"]
                    == krag[name]["excluded_pollen_N"]
                    and authority["source_audit"] == protocol["krag_audit"],
                    "KRAG literal pooled source proof differs",
                )
            else:
                proofs = [
                    row for row in old_projection if row["record_id"] == ids[code]
                ]
                require(len(proofs) == 1, "one exact old public projection required")
                for key, value in proofs[0].items():
                    exact(authority[key], value)
                for key in (
                    "source_axis",
                    "source_panel_N",
                    "projected_panel_N",
                    "excluded_panel_N",
                    "source_support_sha256",
                ):
                    exact(authority[key], small[(name, code)][key])
                exact(
                    authority["qualified_source_support"],
                    small[(name, code)]["qualified_source_support"],
                )
        for evidence in template["evidence"]:
            body = read_file(
                relative_file(input_path.parent / name, evidence["path"]),
                65536,
                evidence["sha256"],
            )
            count_free_evidence(decode(body))
        output[name] = {
            "experiment": experiment,
            "members": {
                key.removeprefix(name + "/"): value
                for key, value in bodies.items()
                if key.startswith(name + "/")
            },
            "ids": ids,
            "krag_window": krag[name],
            "small_source_sample_supports": {
                code: small[(name, code)]["native_sample_count"] for code in SMALL
            },
        }
    return output
