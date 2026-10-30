"""Authenticate seven native core ledgers and the coherent author parameter profile."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import signal
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ...author_lra_spatial.products import code_state, resources, write
from ...physical_forward.inputs import decode, physical, require
from ..literal_window_support.study import read_pin
from ..regional_source_support import WINDOWS, integer, mapping, objects
from .parameters import bind_parameters, lookup_rows
from .projection import project as project

PROVENANCE = (
    "raw_manifest",
    "relational_baseline",
    "count_policy",
    "chronology_metadata",
    "collection_metadata",
    "author_parameter_binding",
)
AUTHOR_SOURCES = ("lookup", "mean", "covariance", "driver")
CORE_KEYS = (
    "abborrtjarnen",
    "bokesjon",
    "bussjosjon",
    "solsoe81",
    "solsoe83",
    "laihalampi",
    "dalmutladdo",
)
COUNTRIES = {"Sweden": "SE", "Denmark": "DK", "Finland": "FI", "Norway": "NO"}


def validate_protocol(protocol: dict[str, Any]) -> None:
    """Reject another axis, population, chronology role or resource profile."""
    require(
        protocol["schema_version"] == "nordic-author-window-support-protocol.v1"
        and set(protocol["provenance"]) == set(PROVENANCE)
        and set(protocol["author_sources"]) == set(AUTHOR_SOURCES)
        and protocol["taxa"] == ["Betula", "Pinus"]
        and protocol["windows"] == [list(edge) for edge in WINDOWS]
        and tuple(c["key"] for c in protocol["cores"]) == CORE_KEYS,
        "Exact seven-core author panel/window profile required",
    )
    cores = objects(protocol["cores"])
    lookup = protocol["author_lookup_contract"]
    require(
        lookup["encoding"] == "latin-1"
        and lookup["source_fields"] == ["oldvar", "RPP.LANDCLIMII"]
        and lookup["selected_targets"] == protocol["taxa"]
        and lookup["excluded_targets"] == ["zz.do not use", "aage.cal.BP"]
        and all(
            type(lookup[k]) is int and lookup[k] == v
            for k, v in (
                ("data_rows", 10788),
                ("unique_source_names", 9731),
                ("parameter_targets", 31),
            )
        ),
        "Exact full author lookup contract required",
    )
    require(
        all(integer(c["identity"]["source_sample_count"]) for c in cores)
        and sum(c["identity"]["source_sample_count"] for c in cores) == 542
        and len({c["identity"]["dataset_id"] for c in cores}) == 7
        and len({c["identity"]["collection_unit_id"] for c in cores}) == 7
        and len({c["physical_family"] for c in cores}) == 6
        and len({c["country"] for c in cores}) == 4
        and all(
            c["country"] in COUNTRIES
            and c["physical_family"] == f"neotoma:site:{c['identity']['site_id']}"
            and [a["author_target"] for a in c["native_axes"]] == protocol["taxa"]
            and all(
                type(a["source_name"]) is str and integer(a["taxon_id"])
                for a in c["native_axes"]
            )
            for c in cores
        ),
        "Complete native owner and physical-family population required",
    )
    for key, expected in (
        ("native_owner_count", 542),
        ("core_sequence_count", 7),
        ("physical_site_count", 6),
        ("country_count", 4),
        ("requested_window_count", 42),
    ):
        require(
            type(protocol["population"][key]) is int
            and protocol["population"][key] == expected,
            "Declared population differs",
        )
    require(
        protocol["source_max_bytes"] == 32 * 1024**2
        and protocol["limits"]
        == {
            "producer_wall_seconds": 90,
            "observer_wall_seconds": 90,
            "max_rss_bytes": 1024**3,
            "max_output_bytes": 16 * 1024**2,
        }
        and all(type(v) is int for v in protocol["limits"].values())
        and type(protocol["engine_calls"]) is int
        and protocol["engine_calls"] == 0
        and type(protocol["model_fits"]) is int
        and protocol["model_fits"] == 0
        and protocol["source_acquisition"] is False
        and protocol["scientific_or_field_admission"] is False,
        "Source-only scope and original budgets required",
    )


def metadata_contract(core: dict[str, Any], documents: dict[str, Any]) -> None:
    """Join explicit native IDs/default assertions to retained relational metadata."""
    owner, chronology = core["identity"], core["chronology"]
    unit_id, site_id = (
        f"neotoma:collection-unit:{owner['collection_unit_id']}",
        core["physical_family"],
    )
    units = [
        r
        for r in objects(documents["collection_metadata"]["rows"])
        if r["collection_unit_id"] == unit_id
    ]
    require(
        len(units) == 1
        and units[0]["site_id"] == site_id
        and units[0]["country_code"] == COUNTRIES[core["country"]]
        and type(units[0]["source_collection_unit_id"]) is int
        and units[0]["source_collection_unit_id"] == owner["collection_unit_id"]
        and units[0]["source_payload"]["handle"] == owner["handle"],
        "Retained collection metadata ownership differs",
    )
    rows = [
        r
        for r in objects(documents["chronology_metadata"]["rows"])
        if r["collection_unit_id"] == unit_id
    ]
    flags = chronology["source_default_flags"]
    require(
        len(rows) == len(flags)
        and len({r["source_chronology_id"] for r in rows}) == len(rows)
        and {str(r["source_chronology_id"]) for r in rows} == set(flags),
        "Complete retained chronology declarations differ",
    )
    for row in rows:
        code = row["source_chronology_id"]
        payload = mapping(row["source_payload"])
        require(
            type(code) is int
            and type(payload["chronologyid"]) is int
            and code == payload["chronologyid"]
            and row["site_id"] == site_id
            and row["country_code"] == COUNTRIES[core["country"]]
            and type(flags[str(code)]) is bool
            and row["source_is_default_assertion"] is flags[str(code)]
            and payload["chronology"]["isdefault"] is flags[str(code)]
            and row["selected_by_collection_unit_reference"]
            is (code == chronology["native_collection_default_reference"]),
            "Literal chronology flag/reference ownership differs",
        )
        if code == chronology["selected_id"]:
            require(
                payload["chronology"]["chronologyname"] == chronology["selected_name"]
                and payload["chronology"]["modelagetype"]
                == chronology["selected_native_type"],
                "Selected retained chronology name/type differs",
            )
    require(
        any(r["source_chronology_id"] == chronology["selected_id"] for r in rows),
        "Selected retained chronology declaration missing",
    )


def load_contract(
    repository: Path, original_data_root: Path, protocol: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    """Read only declared source metadata and author inputs before native count parts."""
    validate_protocol(protocol)
    documents = {
        key: decode(read_pin(repository, protocol["provenance"][key], 1024**2))
        for key in PROVENANCE
    }
    manifest, baseline, policy = (documents[k] for k in PROVENANCE[:3])
    require(
        policy["schema_version"] == "krageholm-regional-literal-panel-protocol.v1"
        and policy["windows"] == protocol["windows"]
        and baseline["input_artifacts"]["raw_archive"]["manifest_sha256"]
        == protocol["provenance"]["raw_manifest"]["sha256"],
        "Retained count policy/manifest authority differs",
    )
    parts = {r["filename"]: r for r in manifest["parts"]}
    require(
        len(parts) == len(manifest["parts"]), "Unique retained source parts required"
    )
    for core in protocol["cores"]:
        source, owner = core["source"], core["identity"]
        name = Path(source["path"]).name
        archive = baseline["input_artifacts"]["raw_archive"]
        require(
            name in parts
            and archive["part_sha256"][name] == source["sha256"]
            and source["path"] == str(Path(archive["path"]) / name)
            and [
                r["filename"]
                for r in manifest["parts"]
                if owner["dataset_id"] in r["downloaded_dataset_ids"]
            ]
            == [name],
            "Dataset lacks one exact retained native part",
        )
        metadata_contract(core, documents)
    author = {
        key: read_pin(original_data_root, protocol["author_sources"][key], 1024**2)
        for key in AUTHOR_SOURCES
    }
    lookup = lookup_rows(author["lookup"], protocol["author_lookup_contract"])
    parameters = bind_parameters(
        author["mean"],
        author["covariance"],
        lookup,
        protocol,
        documents["author_parameter_binding"],
    )
    for role in ("mean", "covariance", "driver"):
        pin = protocol["author_sources"][role]
        matches = [
            r
            for r in documents["author_parameter_binding"]["inputs"]
            if pin["path"] == "landclim/author-reference/" + r["path"]
        ]
        require(
            len(matches) == 1
            and all(matches[0][k] == pin[k] for k in ("bytes", "sha256")),
            "Full parameter report source identity differs",
        )
    pins = [
        {**deepcopy(protocol["provenance"][key]), "storage": "repository"}
        for key in PROVENANCE
    ]
    pins += [
        {**deepcopy(protocol["author_sources"][key]), "storage": "original_data"}
        for key in AUTHOR_SOURCES
    ]
    for core in protocol["cores"]:
        pin = {**deepcopy(core["source"]), "storage": "repository"}
        if pin not in pins:
            pins.append(pin)
    contract = {
        **deepcopy(protocol),
        "scope": protocol["scientific_consumer"],
        "suppression_semantics": policy["suppression_semantics"],
    }
    return contract, lookup, parameters, pins


def produce(
    repository: Path, original_data_root: Path, protocol_path: Path, output: Path
) -> dict[str, Any]:
    """Close all 542 owners and 42 windows without constructing model requests."""
    started = time.monotonic()
    physical(repository)
    physical(original_data_root)
    physical(protocol_path)
    require(
        original_data_root.is_dir()
        and not original_data_root.is_relative_to(repository),
        "Shared external original-data root required",
    )
    output = require_absent_artifact_output(repository, output)
    state = code_state(repository)
    raw_protocol = protocol_path.read_bytes()
    runner = Path(__file__).read_bytes()
    protocol = decode(raw_protocol)
    contract, lookup, parameters, pins = load_contract(
        repository, original_data_root, protocol
    )
    maximum = protocol["limits"]["max_output_bytes"]
    output.mkdir()
    products = {"parameters": write(output, "parameters.json", parameters, maximum)}
    summaries = {}
    seen_owners: set[int] = set()
    parts = sorted({c["source"]["path"] for c in contract["cores"]})
    for part in parts:
        cores = [c for c in contract["cores"] if c["source"]["path"] == part]
        require(
            all(c["source"] == cores[0]["source"] for c in cores),
            "Shared source pins differ",
        )
        native = decode(
            read_pin(repository, cores[0]["source"], protocol["source_max_bytes"])
        )
        for core in cores:
            ledger = project(native, core, contract, lookup)
            owners = {r["sample_id"] for r in ledger["samples"]}
            require(
                not owners & seen_owners, "Native sample owner crosses core sequences"
            )
            seen_owners.update(owners)
            products[core["key"]] = write(
                output, core["key"] + ".json", ledger, maximum
            )
            summaries[core["key"]] = {
                "identity": ledger["identity"],
                "country": core["country"],
                "physical_family": core["physical_family"],
                "population": ledger["population"],
                "support_summary": ledger["support_summary"],
            }
            resources(started, output, protocol["limits"])
            del ledger
        del native
    require(
        len(seen_owners) == 542 and set(summaries) == set(CORE_KEYS),
        "Complete seven-core native population differs",
    )
    protocol_pin = {
        "path": str(protocol_path.relative_to(repository)),
        "bytes": len(raw_protocol),
        "sha256": hashlib.sha256(raw_protocol).hexdigest(),
    }
    runner_pin = {
        "path": str(Path(__file__).resolve().relative_to(repository)),
        "bytes": len(runner),
        "sha256": hashlib.sha256(runner).hexdigest(),
    }
    manifest = {
        "schema_version": "nordic-author-window-inputs.v1",
        "protocol": protocol_pin,
        "runner": runner_pin,
        "source_commit": state["head"],
        "index_sha256": state["index_sha256"],
        "python_files_checked": len(state["python_files"]),
        "sourcepins": pins,
    }
    products["input_manifest"] = write(output, "input-manifest.json", manifest, maximum)
    for pin in pins:
        root = repository if pin["storage"] == "repository" else original_data_root
        read_pin(
            root,
            {k: pin[k] for k in ("path", "bytes", "sha256")},
            protocol["source_max_bytes"],
        )
    require(
        protocol_path.read_bytes() == raw_protocol
        and Path(__file__).read_bytes() == runner
        and code_state(repository) == state,
        "Consumed source, protocol, runner, Python, HEAD or index changed",
    )
    require(
        {p.name for p in output.iterdir()}
        == {pin["path"] for pin in products.values()},
        "Unowned file in closed output inventory",
    )
    for pin in products.values():
        read_pin(output, pin, maximum)
    result = {
        "schema_version": "nordic-author-window-result.v1",
        "status": "produced_awaiting_independent_verification",
        "source_commit": state["head"],
        "index_sha256": state["index_sha256"],
        "python_files_checked": len(state["python_files"]),
        "protocol": protocol_pin,
        "runner": runner_pin,
        "source_guards_passed": True,
        "sourcepins": pins,
        "products": products,
        "cores": {key: summaries[key] for key in CORE_KEYS},
        "population": deepcopy(protocol["population"]),
        "window_status_counts": dict(
            sum(
                (
                    Counter(r["support_summary"]["window_status_counts"])
                    for r in summaries.values()
                ),
                Counter(),
            )
        ),
        "engine_calls": 0,
        "model_fits": 0,
        "source_acquisition": False,
        "scientific_or_field_admission": False,
        "resources": resources(started, output, protocol["limits"]),
    }
    require(
        set(products) == {*CORE_KEYS, "parameters", "input_manifest"},
        "Closed output inventory differs",
    )
    write(output, "result.json", result, maximum)
    resources(started, output, protocol["limits"])
    return result


def main() -> None:
    """Run the explicitly bounded source-only projection in an absent artifact directory."""
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in ("repository", "original-data-root", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()

    def timeout(*_: object) -> None:
        raise TimeoutError("90 second author source projection ceiling")

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(90)
    try:
        result = produce(
            args.repository.absolute(),
            args.original_data_root.absolute(),
            args.protocol.absolute(),
            args.output.absolute(),
        )
        print(
            json.dumps({"status": result["status"], "resources": result["resources"]})
        )
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    main()
