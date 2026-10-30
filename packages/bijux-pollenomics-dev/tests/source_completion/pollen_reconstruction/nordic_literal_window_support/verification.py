"""Independent exact-source custody and complete closed-result comparison."""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import re
import time
from typing import Any

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import (
    code_state,
)
from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.verification import (
    decode,
    same,
    source_bytes,
)

from .native_owners import require
from .population import expected_core

PROVENANCE = ("raw_manifest", "relational_baseline", "literal_policy")
INHERITED = (
    "count_policy",
    "literal_status_precedence",
    "full_mass_policy",
    "age_numeric_interpretation",
    "suppression_semantics",
)


def read_pin(repository: Path, pin: dict[str, Any], maximum: int) -> bytes:
    require(
        type(pin) is dict and set(pin) == {"path", "bytes", "sha256"},
        "closed scientific byte identity",
    )
    require(
        type(pin["path"]) is str
        and type(pin["bytes"]) is int
        and 0 < pin["bytes"] <= maximum
        and type(pin["sha256"]) is str
        and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]),
        "bounded scientific pin",
    )
    relative = Path(pin["path"])
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "repository-relative source",
    )
    return source_bytes(repository / relative, pin, maximum)


def contract(
    repository: Path, protocol: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    require(
        protocol["schema_version"] == "nordic-literal-window-support-protocol.v1"
        and set(protocol["provenance"]) == set(PROVENANCE)
        and protocol["inherited_policy_fields"] == list(INHERITED)
        and protocol["source_max_bytes"] == 32 * 1024**2,
        "prospective two-core source contract",
    )
    cores = protocol["cores"]
    require(
        [c["key"] for c in cores] == ["laihalampi", "dalmutladdo"]
        and [c["identity"]["source_sample_count"] for c in cores] == [150, 72],
        "declared complete source populations",
    )
    documents = {
        key: decode(read_pin(repository, protocol["provenance"][key], 1024**2))
        for key in PROVENANCE
    }
    manifest, baseline, policy = (documents[key] for key in PROVENANCE)
    require(
        policy["schema_version"] == "krageholm-regional-literal-panel-protocol.v1",
        "inherited literal policy",
    )
    same(policy["taxa"], protocol["taxa"])
    same(policy["windows"], protocol["windows"])
    archive = baseline["input_artifacts"]["raw_archive"]
    require(
        archive["manifest_sha256"] == protocol["provenance"]["raw_manifest"]["sha256"],
        "relational authority authenticates manifest",
    )
    parts = manifest["parts"]
    names = [r["filename"] for r in parts]
    require(
        len(names) == len(set(names))
        and all(type(n) is str and Path(n).name == n for n in names),
        "unique direct manifest parts",
    )
    for core in cores:
        source, identity = core["source"], core["identity"]
        name = Path(source["path"]).name
        require(
            type(identity["dataset_id"]) is int
            and type(identity["source_sample_count"]) is int,
            "native integer ownership declaration",
        )
        containing = [
            r for r in parts if identity["dataset_id"] in r["downloaded_dataset_ids"]
        ]
        require(
            len(containing) == 1
            and containing[0]["filename"] == name
            and sum(
                x == identity["dataset_id"]
                for x in containing[0]["downloaded_dataset_ids"]
            )
            == 1,
            "one manifest part membership per dataset",
        )
        require(
            all(type(x) is int for x in containing[0]["downloaded_dataset_ids"]),
            "literal native manifest dataset IDs",
        )
        require(
            source["path"] == str(Path(archive["path"]) / name)
            and archive["part_sha256"][name] == source["sha256"],
            "baseline authenticates exact source part",
        )
    enriched = {**protocol, **{field: policy[field] for field in INHERITED}}
    sourcepins = [protocol["provenance"][key] for key in PROVENANCE] + [
        c["source"] for c in cores
    ]
    require(
        len({p["path"] for p in sourcepins}) == 5,
        "five distinct source/provenance paths",
    )
    return enriched, sourcepins


def verify(repository: Path, products: Path, protocol_path: Path) -> dict[str, Any]:
    """Read each native part sequentially and compare every owner and aggregate."""
    started = time.monotonic()
    repository = repository.resolve(strict=True)
    require(
        ".." not in products.parts and ".." not in protocol_path.parts,
        "unaliased input locators",
    )
    products = products if products.is_absolute() else repository / products
    protocol_path = (
        protocol_path if protocol_path.is_absolute() else repository / protocol_path
    )
    require(
        products.is_dir()
        and products.resolve().is_relative_to(repository / "artifacts")
        and not any(p.is_symlink() for p in (products, *products.parents)),
        "ordinary closed products below artifacts",
    )
    require(
        protocol_path.is_file()
        and protocol_path.resolve().is_relative_to(repository)
        and not any(p.is_symlink() for p in (protocol_path, *protocol_path.parents)),
        "ordinary repository protocol",
    )
    before = code_state(repository)
    protocol_raw = protocol_path.read_bytes()
    require(0 < len(protocol_raw) <= 1024**2, "bounded prospective protocol")
    protocol = decode(protocol_raw)
    enriched, sourcepins = contract(repository, protocol)
    limits = protocol["limits"]
    require(
        limits
        == {
            "producer_wall_seconds": 90,
            "observer_wall_seconds": 90,
            "max_rss_bytes": 1024**3,
            "max_output_bytes": 8 * 1024**2,
        },
        "prospective source-only resource limits",
    )
    result_path = products / "result.json"
    require(
        result_path.is_file()
        and not result_path.is_symlink()
        and result_path.stat().st_size <= limits["max_output_bytes"],
        "closed bounded result",
    )
    result_raw = result_path.read_bytes()
    result = decode(result_raw)
    expected_keys = {
        "schema_version",
        "status",
        "source_commit",
        "protocol_sha256",
        "index_sha256",
        "python_files_checked",
        "source_guards_passed",
        "sourcepins",
        "products",
        "engine_calls",
        "model_fits",
        "source_acquisition",
        "scientific_or_field_admission",
        "resources",
    }
    require(
        set(result) == expected_keys
        and result["schema_version"] == "nordic-literal-window-result.v1"
        and result["status"] == "produced_awaiting_independent_verification",
        "closed result schema/status",
    )
    require(
        result["source_commit"] == before["head"]
        and result["index_sha256"] == before["index_sha256"]
        and type(result["python_files_checked"]) is int
        and result["python_files_checked"] == len(before["python_files"])
        and result["protocol_sha256"] == sha256(protocol_raw).hexdigest()
        and result["source_guards_passed"] is True,
        "same frozen producer/observer source epoch",
    )
    same(result["sourcepins"], sourcepins)
    for field, expected_claim in (
        ("engine_calls", 0),
        ("model_fits", 0),
        ("source_acquisition", False),
        ("scientific_or_field_admission", False),
    ):
        same(result[field], expected_claim)
        same(protocol[field], expected_claim)
    require(
        set(result["products"]) == {c["key"] for c in protocol["cores"]},
        "two exact core products",
    )
    members = {"result.json"}
    summaries = []
    closed_core_bytes: dict[str, str] = {}
    for core in enriched["cores"]:
        pin = result["products"][core["key"]]
        require(pin["path"] == core["key"] + ".json", "owned direct core product")
        members.add(pin["path"])
        product_body = read_pin(products, pin, limits["max_output_bytes"])
        native_body = read_pin(repository, core["source"], protocol["source_max_bytes"])
        native = decode(native_body)
        expected = expected_core(native, core, enriched)
        actual = decode(product_body)
        same(actual, expected)
        summaries.append(
            {
                "key": core["key"],
                "native_sample_owners_checked": len(expected["samples"]),
                "selected_chronology_id": expected["chronology"][
                    "selected_chronology_id"
                ],
                "native_collection_default_reference": expected["chronology"][
                    "native_collection_default_reference"
                ],
                "fixed_windows_checked": 6,
                "population": expected["population"],
                "support_summary": expected["support_summary"],
                "source_sha256": core["source"]["sha256"],
                "result_sha256": sha256(product_body).hexdigest(),
            }
        )
        closed_core_bytes[pin["path"]] = sha256(product_body).hexdigest()
        del native_body, native, expected, actual, product_body
    require(
        {p.name for p in products.iterdir()} == members
        and all(p.is_file() and not p.is_symlink() for p in products.iterdir()),
        "complete closed output inventory",
    )
    output_bytes = sum(p.stat().st_size for p in products.iterdir())
    require(output_bytes <= limits["max_output_bytes"], "complete output byte cap")
    produced = result["resources"]
    require(
        set(produced) == {"elapsed_seconds", "peak_rss_bytes", "output_bytes"},
        "resource account fields",
    )
    require(
        type(produced["elapsed_seconds"]) in (int, float, Decimal),
        "finite elapsed scalar",
    )
    require(
        0 <= float(produced["elapsed_seconds"]) <= 90
        and type(produced["peak_rss_bytes"]) is int
        and 0 < produced["peak_rss_bytes"] <= 1024**3
        and type(produced["output_bytes"]) is int
        and produced["output_bytes"] == output_bytes - len(result_raw),
        "producer resource accounting",
    )
    for pin in sourcepins:
        read_pin(repository, pin, protocol["source_max_bytes"])
    require(
        protocol_path.read_bytes() == protocol_raw
        and result_path.read_bytes() == result_raw
        and code_state(repository) == before,
        "consumed code/source/protocol/result changed",
    )
    for name, expected_sha in closed_core_bytes.items():
        require(
            sha256((products / name).read_bytes()).hexdigest() == expected_sha,
            "closed core result changed",
        )
    return {
        "schema_version": "nordic-literal-window-verification.v1",
        "status": "verified",
        "source_commit": before["head"],
        "index_sha256": before["index_sha256"],
        "python_files_checked": len(before["python_files"]),
        "protocol_sha256": sha256(protocol_raw).hexdigest(),
        "producer_result_sha256": sha256(result_raw).hexdigest(),
        "source_guards_passed": True,
        "native_sample_owners_checked": sum(
            c["native_sample_owners_checked"] for c in summaries
        ),
        "cores": summaries,
        "engine_calls": 0,
        "model_fits": 0,
        "source_acquisition": False,
        "scientific_or_field_admission": False,
        "elapsed_seconds": time.monotonic() - started,
        "scope": "Independent literal two-core source/chronology/panel/mass accounting; no reconstruction, score, model, acquisition, geometry or field admission",
    }
