"""Independent closed seven-core result and original-source reconciliation."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import re
import subprocess
import time
from typing import Any

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import (
    code_state,
)
from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.verification import (
    decode,
    same,
)

from .native_owners import require
from .population import expected_core, parameter_evidence

PROVENANCE = (
    "raw_manifest",
    "relational_baseline",
    "count_policy",
    "chronology_metadata",
    "collection_metadata",
    "author_parameter_binding",
)
AUTHOR = ("lookup", "mean", "covariance", "driver")
CORE_KEYS = (
    "abborrtjarnen",
    "bokesjon",
    "bussjosjon",
    "solsoe81",
    "solsoe83",
    "laihalampi",
    "dalmutladdo",
)
RUNNER = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/nordic_coupled/author_window_support/study.py"


def committed_protocol(repository: Path, path: Path) -> None:
    relative = str(path.relative_to(repository))
    for args in (
        ("ls-files", "--error-unmatch", "--", relative),
        ("diff", "--quiet", "HEAD", "--", relative),
    ):
        subprocess.run(
            ["git", "--no-optional-locks", *args],
            cwd=repository,
            check=True,
            capture_output=True,
        )


def ordinary(path: Path, *, directory: bool = False) -> None:
    require(
        path.exists()
        and path.resolve() == path.absolute()
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "ordinary unaliased path",
    )
    require(
        path.is_dir() if directory else path.is_file() and path.stat().st_nlink == 1,
        "ordinary file/directory",
    )


def read_pin(root: Path, pin: dict[str, Any], maximum: int) -> bytes:
    require(
        type(pin) is dict and set(pin) == {"path", "bytes", "sha256"},
        "closed input identity",
    )
    require(
        type(pin["path"]) is str
        and type(pin["bytes"]) is int
        and 0 < pin["bytes"] <= maximum
        and type(pin["sha256"]) is str
        and re.fullmatch("[0-9a-f]{64}", pin["sha256"]),
        "bounded input identity types",
    )
    relative = Path(pin["path"])
    require(
        not relative.is_absolute()
        and ".." not in relative.parts
        and bool(relative.parts),
        "confined relative input",
    )
    path = root / relative
    ordinary(path)
    require(path.stat().st_size == pin["bytes"], "source byte count")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    require(
        len(raw) == pin["bytes"] and sha256(raw).hexdigest() == pin["sha256"],
        "source byte identity",
    )
    return raw


def contract(
    repository: Path, original: Path, protocol: dict[str, Any]
) -> tuple[
    dict[str, Any],
    dict[str, list[dict[str, Any]]],
    dict[str, Any],
    list[dict[str, Any]],
]:
    require(
        protocol["schema_version"] == "nordic-author-window-support-protocol.v1"
        and protocol["taxa"] == ["Betula", "Pinus"]
        and protocol["windows"] == [[a, a + 500] for a in range(2700, 5700, 500)],
        "prospective selected author/window contract",
    )
    cores = protocol["cores"]
    require(
        [c["key"] for c in cores] == list(CORE_KEYS)
        and [c["identity"]["source_sample_count"] for c in cores]
        == [107, 52, 69, 66, 26, 150, 72]
        and len({c["physical_family"] for c in cores}) == 6
        and len({c["country"] for c in cores}) == 4
        and all(
            c["physical_family"] == f"neotoma:site:{c['identity']['site_id']}"
            for c in cores
        ),
        "seven complete cores/six source places/four countries",
    )
    expected_population = {
        "native_owner_count": 542,
        "core_sequence_count": 7,
        "physical_site_count": 6,
        "country_count": 4,
        "requested_window_count": 42,
    }
    same(
        {key: protocol["population"][key] for key in expected_population},
        expected_population,
    )
    same(
        protocol["limits"],
        {
            "producer_wall_seconds": 90,
            "observer_wall_seconds": 90,
            "max_rss_bytes": 1024**3,
            "max_output_bytes": 16 * 1024**2,
        },
    )
    require(
        protocol["source_max_bytes"] == 32 * 1024**2
        and set(protocol["provenance"]) == set(PROVENANCE)
        and set(protocol["author_sources"]) == set(AUTHOR),
        "bounded named authority inventory",
    )
    docs = {
        key: decode(read_pin(repository, protocol["provenance"][key], 1024**2))
        for key in PROVENANCE
    }
    manifest, archive = (
        docs["raw_manifest"],
        docs["relational_baseline"]["input_artifacts"]["raw_archive"],
    )
    require(
        archive["manifest_sha256"] == protocol["provenance"]["raw_manifest"]["sha256"]
        and docs["count_policy"]["schema_version"]
        == "krageholm-regional-literal-panel-protocol.v1",
        "retained manifest/count authority",
    )
    same(docs["count_policy"]["windows"], protocol["windows"])
    require(
        len({row["filename"] for row in manifest["parts"]}) == len(manifest["parts"]),
        "unique native parts",
    )
    countries = {"Sweden": "SE", "Denmark": "DK", "Finland": "FI", "Norway": "NO"}
    for core in cores:
        identity, chronology = core["identity"], core["chronology"]
        require(
            [axis["author_target"] for axis in core["native_axes"]] == protocol["taxa"]
            and all(
                type(axis["taxon_id"]) is int
                and axis["taxon_id"] >= 0
                and type(axis["source_name"]) is str
                and bool(axis["source_name"])
                for axis in core["native_axes"]
            ),
            "typed ordered native author axes",
        )
        part = Path(core["source"]["path"]).name
        require(
            core["source"]["path"] == str(Path(archive["path"]) / part)
            and archive["part_sha256"][part] == core["source"]["sha256"]
            and [
                row["filename"]
                for row in manifest["parts"]
                if identity["dataset_id"] in row["downloaded_dataset_ids"]
            ]
            == [part],
            "one exact native dataset/part authority",
        )
        unit_id = f"neotoma:collection-unit:{identity['collection_unit_id']}"
        site_id = f"neotoma:site:{identity['site_id']}"
        units = [
            row
            for row in docs["collection_metadata"]["rows"]
            if row["collection_unit_id"] == unit_id
        ]
        require(
            len(units) == 1
            and units[0]["site_id"] == site_id
            and units[0]["country_code"] == countries[core["country"]]
            and type(units[0]["source_collection_unit_id"]) is int
            and units[0]["source_collection_unit_id"] == identity["collection_unit_id"]
            and units[0]["source_payload"]["handle"] == identity["handle"],
            "retained native collection identity",
        )
        declarations = [
            row
            for row in docs["chronology_metadata"]["rows"]
            if row["collection_unit_id"] == unit_id
        ]
        require(
            {str(row["source_chronology_id"]) for row in declarations}
            == set(chronology["source_default_flags"])
            and len(declarations) == len(chronology["source_default_flags"]),
            "complete retained chronology declarations",
        )
        for row in declarations:
            code = row["source_chronology_id"]
            flag = chronology["source_default_flags"][str(code)]
            require(
                type(code) is int
                and row["site_id"] == site_id
                and row["country_code"] == countries[core["country"]]
                and type(flag) is bool
                and row["source_is_default_assertion"] is flag
                and row["source_payload"]["chronology"]["isdefault"] is flag
                and row["source_payload"]["chronologyid"] == code
                and row["selected_by_collection_unit_reference"]
                is (code == chronology["native_collection_default_reference"]),
                "literal chronology flag/reference metadata",
            )
            if code == chronology["selected_id"]:
                require(
                    row["source_payload"]["chronology"]["chronologyname"]
                    == chronology["selected_name"]
                    and row["source_payload"]["chronology"]["modelagetype"]
                    == chronology["selected_native_type"],
                    "retained selected chronology name/type",
                )
    bodies = {
        key: read_pin(original, protocol["author_sources"][key], 1024**2)
        for key in AUTHOR
    }
    parameters, lookup = parameter_evidence(
        bodies, protocol, docs["author_parameter_binding"]
    )
    for key in ("mean", "covariance", "driver"):
        pin = protocol["author_sources"][key]
        matches = [
            row
            for row in docs["author_parameter_binding"]["inputs"]
            if "landclim/author-reference/" + row["path"] == pin["path"]
        ]
        require(
            len(matches) == 1
            and all(matches[0][field] == pin[field] for field in ("bytes", "sha256")),
            "qualified parameter/driver source identity",
        )
    pins = [
        {**protocol["provenance"][key], "storage": "repository"} for key in PROVENANCE
    ] + [
        {**protocol["author_sources"][key], "storage": "original_data"}
        for key in AUTHOR
    ]
    for core in cores:
        pin = {**core["source"], "storage": "repository"}
        if pin not in pins:
            pins.append(pin)
    require(
        len({(p["storage"], p["path"]) for p in pins}) == len(pins) == 14,
        "four unique native part identities",
    )
    return (
        {
            **protocol,
            "scope": protocol["scientific_consumer"],
            "suppression_semantics": docs["count_policy"]["suppression_semantics"],
        },
        lookup,
        parameters,
        pins,
    )


def verify(
    repository: Path, original_data_root: Path, products: Path, protocol_path: Path
) -> dict[str, Any]:
    started = time.monotonic()
    repository, original_data_root = (
        repository.absolute(),
        original_data_root.absolute(),
    )
    ordinary(repository, directory=True)
    ordinary(original_data_root, directory=True)
    require(
        not original_data_root.is_relative_to(repository),
        "external shared originals root",
    )
    products = products if products.is_absolute() else repository / products
    protocol_path = (
        protocol_path if protocol_path.is_absolute() else repository / protocol_path
    )
    ordinary(products, directory=True)
    ordinary(protocol_path)
    require(
        products.is_relative_to(repository / "artifacts")
        and protocol_path.is_relative_to(repository),
        "confined result/protocol",
    )
    committed_protocol(repository, protocol_path)
    before = code_state(repository)
    protocol_raw = protocol_path.read_bytes()
    require(0 < len(protocol_raw) <= 1024**2, "bounded protocol")
    protocol = decode(protocol_raw)
    enriched, lookup, parameters, pins = contract(
        repository, original_data_root, protocol
    )
    cap = protocol["limits"]["max_output_bytes"]
    require((products / "result.json").stat().st_size <= cap, "bounded result")
    ordinary(products / "result.json")
    raw_result = (products / "result.json").read_bytes()
    result = decode(raw_result)
    fields = {
        "schema_version",
        "status",
        "source_commit",
        "index_sha256",
        "python_files_checked",
        "protocol",
        "runner",
        "source_guards_passed",
        "sourcepins",
        "products",
        "cores",
        "population",
        "window_status_counts",
        "engine_calls",
        "model_fits",
        "source_acquisition",
        "scientific_or_field_admission",
        "resources",
    }
    require(
        set(result) == fields
        and result["schema_version"] == "nordic-author-window-result.v1"
        and result["status"] == "produced_awaiting_independent_verification",
        "closed result schema",
    )
    require(
        result["source_commit"] == before["head"]
        and result["index_sha256"] == before["index_sha256"]
        and type(result["python_files_checked"]) is int
        and result["python_files_checked"] == len(before["python_files"])
        and result["source_guards_passed"] is True,
        "frozen source epoch",
    )
    same(result["sourcepins"], pins)
    same(
        result["protocol"],
        {
            "path": str(protocol_path.relative_to(repository)),
            "bytes": len(protocol_raw),
            "sha256": sha256(protocol_raw).hexdigest(),
        },
    )
    require(result["runner"]["path"] == RUNNER, "owning source producer runner")
    runner = read_pin(repository, result["runner"], 1024**2)
    for key, value in (
        ("engine_calls", 0),
        ("model_fits", 0),
        ("source_acquisition", False),
        ("scientific_or_field_admission", False),
    ):
        same(result[key], value)
        same(protocol[key], value)
    require(
        set(result["products"]) == {*CORE_KEYS, "parameters", "input_manifest"},
        "closed core/parameter/manifest products",
    )
    bodies = {}
    members = {"result.json"}
    for key, pin in result["products"].items():
        name = "input-manifest.json" if key == "input_manifest" else key + ".json"
        require(pin["path"] == name, "direct owned product filename")
        members.add(name)
        bodies[key] = read_pin(products, pin, cap)
    same(decode(bodies["parameters"]), parameters)
    same(
        decode(bodies["input_manifest"]),
        {
            "schema_version": "nordic-author-window-inputs.v1",
            "protocol": result["protocol"],
            "runner": result["runner"],
            "source_commit": before["head"],
            "index_sha256": before["index_sha256"],
            "python_files_checked": len(before["python_files"]),
            "sourcepins": pins,
        },
    )
    summaries: dict[str, Any] = {}
    owners: set[int] = set()
    statuses: Counter[str] = Counter()
    for source_path in sorted({c["source"]["path"] for c in protocol["cores"]}):
        cores = [c for c in protocol["cores"] if c["source"]["path"] == source_path]
        same([c["source"] for c in cores], [cores[0]["source"] for _ in cores])
        native = decode(
            read_pin(repository, cores[0]["source"], protocol["source_max_bytes"])
        )
        for core in cores:
            expected = expected_core(native, core, enriched, lookup)
            same(decode(bodies[core["key"]]), expected)
            ids = {r["sample_id"] for r in expected["samples"]}
            require(not owners.intersection(ids), "sample owner cannot cross sequences")
            owners.update(ids)
            statuses.update(expected["support_summary"]["window_status_counts"])
            summaries[core["key"]] = {
                key: expected[key]
                for key in (
                    "identity",
                    "country",
                    "physical_family",
                    "population",
                    "support_summary",
                )
            }
            del expected
        del native
    require(len(owners) == 542, "all native source owners")
    same(result["cores"], summaries)
    same(result["population"], protocol["population"])
    same(result["window_status_counts"], dict(statuses))
    require(
        {p.name for p in products.iterdir()} == members, "complete result inventory"
    )
    for path in products.iterdir():
        ordinary(path)
    output_bytes = sum(p.stat().st_size for p in products.iterdir())
    require(output_bytes <= cap, "total closed product bytes")
    account = result["resources"]
    require(
        set(account) == {"elapsed_seconds", "peak_rss_bytes", "output_bytes"}
        and type(account["elapsed_seconds"]) in (int, float, Decimal)
        and 0 <= float(account["elapsed_seconds"]) <= 90
        and type(account["peak_rss_bytes"]) is int
        and 0 < account["peak_rss_bytes"] <= 1024**3
        and type(account["output_bytes"]) is int
        and account["output_bytes"] == output_bytes - len(raw_result),
        "producer resource account",
    )
    for pin in pins:
        read_pin(
            repository if pin["storage"] == "repository" else original_data_root,
            {key: pin[key] for key in ("path", "bytes", "sha256")},
            protocol["source_max_bytes"],
        )
    require(
        protocol_path.read_bytes() == protocol_raw
        and (products / "result.json").read_bytes() == raw_result
        and read_pin(repository, result["runner"], 1024**2) == runner
        and code_state(repository) == before,
        "all source/code/epoch/result guards",
    )
    for key, body in bodies.items():
        require(
            read_pin(products, result["products"][key], cap) == body,
            "closed member unchanged",
        )
    return {
        "schema_version": "nordic-author-window-verification.v1",
        "status": "verified",
        "source_commit": before["head"],
        "index_sha256": before["index_sha256"],
        "python_files_checked": len(before["python_files"]),
        "producer_result_sha256": sha256(raw_result).hexdigest(),
        "protocol_sha256": sha256(protocol_raw).hexdigest(),
        "source_guards_passed": True,
        "native_sample_owners_checked": 542,
        "requested_windows_checked": 42,
        "physical_sites": 6,
        "countries": 4,
        "cores": summaries,
        "window_status_counts": dict(statuses),
        "author_parameter_rows_checked": 31,
        "author_covariance_cells_checked": 961,
        "source_files_checked": len(pins),
        "engine_calls": 0,
        "model_fits": 0,
        "source_acquisition": False,
        "scientific_or_field_admission": False,
        "elapsed_seconds": time.monotonic() - started,
        "scope": "Independent retained-source author harmonization/count/chronology/parameter accounting only; no field, geometry, historical, model or rights admission",
    }
