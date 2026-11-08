"""Bind a compact native registration table to its declared transport resources."""

import re
from pathlib import PurePosixPath

from .contract import AdmissionError

_DOMAINS = {"nodes", "details", "provenance", "edges", "sequences", "indexes"}
_PREFIX = [
    "domain",
    "sha256",
    "payload_sha256",
    "decoded_byte_count",
    "byte_count",
    "record_count",
]
_METADATA = {
    "layer_index",
    "layer_key",
    "layer_kind",
    "country_keys",
    "bounds",
    "time_min_bp",
    "time_max_bp",
    "untimed_record_count",
    "chronology_absent_record_count",
    "refused_chronology_record_count",
    "contextual_chronology_record_count",
    "scientific_signal_ids",
}
_CAPS = {
    "bootstrap_max_bytes": 262144,
    "chunk_max_bytes": 4194304,
    "document_max_bytes": 524288,
    "static_assets_max_bytes": 134217728,
    "static_assets_max_files": 512,
    "initial_max_requests": 4,
    "initial_max_bytes": 1048576,
}


def _require(condition, message):
    if not condition:
        raise AdmissionError(message)


def _integer(value, maximum):
    return type(value) is int and 0 <= value <= maximum


def verify_registration_graph(
    bootstrap, resources, output, payloads, binding_bytes, bootstrap_bytes
):
    """Check transport identity and resource budgets without interpreting scientific fields."""
    table = bootstrap.get("assets")
    _require(
        isinstance(table, dict)
        and table.get("schema_version")
        in {"atlas-static-asset-table.v3", "atlas-static-asset-table.v4"},
        "external runtime requires a supported compact registration table",
    )
    fields, records = table.get("fields"), table.get("records")
    _require(
        isinstance(fields, list)
        and all(isinstance(field, str) for field in fields)
        and fields[: len(_PREFIX)] == _PREFIX
        and len(fields) == len(set(fields))
        and set(fields[len(_PREFIX) :]) <= _METADATA,
        "external registration table fields differ from finite transport contract",
    )
    _require(
        isinstance(records, list)
        and len(records) <= 512
        and type(table.get("record_count")) is int
        and table["record_count"] == len(records),
        "external registration table population differs",
    )
    scope = bootstrap.get("scope_slug")
    _require(
        isinstance(scope, str)
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", scope)
        and table.get("scope_slug") == scope,
        "external registration scope differs",
    )
    expected = set()
    counts = []
    initial = []
    for sequence, record in enumerate(records):
        _require(
            isinstance(record, list) and len(record) == len(fields),
            "external registration row shape differs",
        )
        row = dict(zip(fields, record))
        domain, sha = row["domain"], row["sha256"]
        _require(
            isinstance(domain, str)
            and domain in _DOMAINS
            and isinstance(sha, str)
            and re.fullmatch(r"[0-9a-f]{64}", sha)
            and isinstance(row["payload_sha256"], str)
            and re.fullmatch(r"[0-9a-f]{64}", row["payload_sha256"])
            and _integer(row["byte_count"], 4194304)
            and _integer(row["decoded_byte_count"], 4194304)
            and row["decoded_byte_count"] > 0,
            "external registration transport identity differs",
        )
        name = f"{scope}.atlas-{domain}.{sequence:04d}.{sha[:16]}.js"
        path = (PurePosixPath(output).parent / name).as_posix()
        resource = resources.get(path)
        _require(
            isinstance(resource, dict)
            and resource.get("kind") == "data-registration"
            and resource.get("source") == "docs/" + path
            and resource.get("sha256") == sha
            and resource.get("bytes") == row["byte_count"],
            "external registration resource differs from bootstrap",
        )
        registration = resource.get("registration", {})
        _require(
            registration.get("variable") == "__BIJUX_ATLAS_RAW_CHUNKS__"
            and registration.get("asset_key") == f"{domain}:{sequence}"
            and registration.get("payload_sha256") == row["payload_sha256"]
            and registration.get("decoded_bytes") == row["decoded_byte_count"],
            "external registration payload/key differs from bootstrap",
        )
        expected.add(path)
        counts.append(row["byte_count"])
        if domain not in {"nodes", "details", "indexes"}:
            initial.append(row["byte_count"])
    observed = {
        name
        for name, resource in resources.items()
        if resource["kind"] == "data-registration"
    }
    _require(
        expected == observed,
        "external registration graph has missing or extra resources",
    )
    budgets = bootstrap.get("budgets", {})
    _require(
        isinstance(budgets, dict)
        and all(
            type(budgets.get(name)) is int and 0 < budgets[name] <= cap
            for name, cap in _CAPS.items()
        ),
        "external runtime declared budgets exceed original limits",
    )
    _require(
        bootstrap_bytes <= budgets["bootstrap_max_bytes"]
        and all(
            0 < len(payload) <= budgets["document_max_bytes"] for payload in payloads
        )
        and all(size <= budgets["chunk_max_bytes"] for size in counts),
        "external runtime member exceeds its declared byte budget",
    )
    _require(
        len(initial) + 1 <= budgets["initial_max_requests"]
        and sum(initial) + len(payloads[0]) + binding_bytes
        <= budgets["initial_max_bytes"],
        "external runtime initial resource budget exceeded",
    )
    _require(
        len(records) + len(payloads) <= budgets["static_assets_max_files"]
        and sum(counts) + sum(len(payload) for payload in payloads) + binding_bytes
        <= budgets["static_assets_max_bytes"],
        "external runtime total resource budget exceeded",
    )
    return {"registrations": len(records), "registration_bytes": sum(counts)}
