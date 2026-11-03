"""Count-free original identities and finite footprints for a block screen."""

from __future__ import annotations

import csv
import hashlib
from io import StringIO
import math
from pathlib import Path
import re
from typing import Any

from ..source_audit import _decode, _groups, _same, _same_radius, _Sources


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Block source metadata: " + message)


def _number(value: Any, *, positive: bool = False) -> float:
    try:
        valid = (
            type(value) in (int, float)
            and math.isfinite(value)
            and (value > 0 if positive else value >= 0)
        )
    except OverflowError:
        valid = False
    _require(valid, "finite strict numerical metadata")
    return float(value)


def _metadata(
    data_root: Path, pin: dict[str, Any]
) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    _require(
        type(pin) is dict
        and set(pin) == {"path", "bytes", "sha256"}
        and type(pin["path"]) is str
        and bool(pin["path"])
        and type(pin["bytes"]) is int
        and 0 < pin["bytes"] <= 8 * 1024**2
        and type(pin["sha256"]) is str
        and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) is not None,
        "exact bounded primary metadata pin",
    )
    relative = Path(pin["path"])
    _require(
        not relative.is_absolute() and ".." not in relative.parts,
        "shared metadata path",
    )
    path = data_root.resolve(strict=True) / relative
    _require(
        path.is_file()
        and not any(part.is_symlink() for part in (path, *path.parents))
        and path.stat().st_size == pin["bytes"],
        "ordinary original primary metadata",
    )
    raw = path.read_bytes()
    _require(
        len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"],
        "primary metadata bytes changed",
    )
    reader = csv.DictReader(StringIO(raw.decode("utf-8-sig")), strict=True)
    _require(
        reader.fieldnames
        == [
            "metadata",
            "filename",
            "SiteName",
            "model",
            "radius",
            "londd",
            "latdd",
            "LCGRID_ID",
        ],
        "original primary metadata columns",
    )
    rows = list(reader)
    _require(
        len(rows) == 17
        and all(
            set(row) == set(reader.fieldnames or [])
            and all(type(value) is str and value for value in row.values())
            for row in rows
        ),
        "seventeen complete primary metadata rows",
    )
    owners = {row["filename"]: row for row in rows}
    _require(
        len(owners) == 17
        and all(
            row["metadata"] == "TRUE"
            and row["model"] == "2"
            and row["LCGRID_ID"] in {"512", "562"}
            for row in rows
        ),
        "unique declared original block owners",
    )
    return owners, {**pin, "storage": "shared_data"}


def _pairs(
    nominal: dict[str, Any],
    experiment: dict[str, Any],
    geometries: dict[str, Any],
    geometry_pins: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    groups = _groups(experiment["sites"])
    _require(
        nominal["schema_version"] == "author-lra-spatial-inputs.v1",
        "qualified nominal input schema",
    )
    _same(nominal["groups"], groups, "block source group identity")
    taxa = experiment["request_template"]["taxa"]
    _require(
        type(taxa) is list and len(taxa) == len(set(taxa)) == 30,
        "original thirty-taxon identity axis",
    )
    _same(nominal["taxa"], taxa, "nominal source taxon identity")
    contexts = nominal["contexts"]
    _require(
        type(contexts) is list and len(contexts) == 225,
        "complete nominal metadata contexts",
    )
    seen_roles = set()
    pair_requests: dict[tuple[str, str], str] = {}
    request_pairs: dict[str, tuple[str, str]] = {}
    cutoffs: dict[str, float] = {}
    for context in contexts:
        outer, target, kind = (
            context["outer_target"],
            context["target"],
            context["kind"],
        )
        _require(
            outer in groups
            and target in groups
            and kind in {"outer", "inner"}
            and (kind == "outer") == (outer == target),
            "source outer/inner role identity",
        )
        role = (outer, target)
        _require(role not in seen_roles, "unique nominal context metadata")
        seen_roles.add(role)
        training = sorted(set(groups) - {outer, target})
        _same(
            context["fold"]["train_record_ids"],
            training,
            "source metadata training exclusion",
        )
        anchor = context["anchor"]
        _require(
            anchor
            == next(
                owner for owner in experiment["regional_priority"] if owner in training
            ),
            "original regional source priority",
        )
        predictors = context["predictors"]
        expected = set(training) - {anchor}
        _require(
            type(predictors) is list
            and len(predictors) == len(expected)
            and {row["record_id"] for row in predictors} == expected,
            "complete local metadata owners",
        )
        for predictor in predictors:
            local, request = predictor["record_id"], predictor["request_sha256"]
            _require(
                predictor["group_id"] == groups[local]
                and type(request) is str
                and re.fullmatch(r"[0-9a-f]{64}", request) is not None,
                "nominal pair identity",
            )
            pair = (local, anchor)
            _require(
                pair_requests.get(pair, request) == request
                and request_pairs.get(request, pair) == pair,
                "one request per physical pair and inverse",
            )
            pair_requests[pair], request_pairs[request] = request, pair
        # Only cutoff/identity metadata is consumed; forecasts and covers are not read.
        forward = context["forward"]
        cutoff = _number(forward["regional_cutoff_m"], positive=True)
        _require(
            cutoff == 100000.0 and cutoffs.get(target, cutoff) == cutoff,
            "qualified explicit finite regional cutoff",
        )
        _require(
            forward["target_geometry_sha256"] == geometry_pins[target]["sha256"],
            "nominal target geometry epoch",
        )
        cutoffs[target] = cutoff
    _require(
        len(seen_roles) == 225
        and set(cutoffs) == set(geometries)
        and len(pair_requests) == len(request_pairs) == 39,
        "complete pair/cutoff source population",
    )
    pairs = [
        {
            "local_record_id": local,
            "regional_anchor_record_id": anchor,
            "request_sha256": request,
        }
        for (local, anchor), request in sorted(pair_requests.items())
    ]
    return pairs, cutoffs


def load_block_inputs(
    repository: Path, archive: Path, data_root: Path, protocol: dict[str, Any]
) -> dict[str, Any]:
    """Authenticate original metadata without opening a raw observation object."""
    _require(
        protocol["schema_version"] == "author-lra-block-support-protocol.v1",
        "block support protocol",
    )
    _same(
        {key: protocol["expected"][key] for key in ("sites", "blocks", "saved_pairs")},
        {"sites": 15, "blocks": ["512", "562"], "saved_pairs": 39},
        "block source population",
    )
    policy = protocol["policy"]
    _require(
        _number(policy["minimum_buffer_m"], positive=True) == 20000.0
        and _number(policy["coordinate_uncertainty_m"]) == 0.0,
        "prospective diagnostic buffer/coordinate policy",
    )
    _require(
        policy["uncertainty_scope"]
        == "optimistic_zero_lower_bound_not_empirical_precision"
        and policy["support_scope"]
        == "declared_finite_cutoff_synthetic_not_empirical_independence",
        "explicit conditional support interpretation",
    )
    sources = protocol["sources"]
    _require(
        set(sources) == {"parent_protocol", "nominal_inputs", "site_metadata"},
        "count-free source inventory",
    )
    reader = _Sources(repository, archive)
    parent = _decode(reader.read(sources["parent_protocol"], authority=True))
    nominal = _decode(reader.read(sources["nominal_inputs"], authority=True))
    metadata, metadata_ref = _metadata(data_root, sources["site_metadata"])
    _require(
        parent["nominal_transport"] == "gpm neutral",
        "original fixed transport identity",
    )
    pins = parent["author_inputs"]
    _require(
        type(pins) is list and len(pins) == 37, "complete original author pin metadata"
    )
    catalogue = {pin["path"]: pin for pin in pins}
    _require(
        len(catalogue) == 37 and all(Path(name).name == name for name in catalogue),
        "unique original basename metadata",
    )
    # The remaining 21 author objects, including all 15 raw outcomes, are unopened.
    experiment = _decode(reader.read(catalogue["experiment.json"]))
    source_sites = experiment["sites"]
    groups = _groups(source_sites)
    priority = experiment["regional_priority"]
    _require(
        type(priority) is list
        and len(priority) == len(set(priority)) == 15
        and set(priority) == set(groups),
        "complete source regional priority",
    )
    target_radius = _number(experiment["local_support_radius_m"], positive=True)
    _same_radius(target_radius, 1000.0)
    geometries, geometry_pins = {}, {}
    for site in source_sites:
        name, record = site["geometry"]["path"], site["record_id"]
        _require(
            name in catalogue and name.endswith("-geometry.json"),
            "only source geometry objects may open",
        )
        pin = catalogue[name]
        _same(
            site["geometry"],
            {"path": name, "sha256": pin["sha256"]},
            "declared geometry original pin",
        )
        geometry = _decode(reader.read(pin))
        sample = geometry["sample_metadata"]
        _require(
            sample["site_id"] == site["site_id"]
            and sample["bin_id"] == "author-TW5"
            and sample["age_type"] == "calendar_bp"
            and sample["age_support_bp"] == [[1250, 1750]],
            "source TW5 identity and chronology",
        )
        geometries[record], geometry_pins[record] = geometry, pin
    pairs, cutoffs = _pairs(nominal, experiment, geometries, geometry_pins)
    selected_names = {site["site_id"] for site in source_sites}
    _require(
        set(metadata) - selected_names == {"EXEBRID", "WHH11"}
        and selected_names <= set(metadata),
        "exact source-only TW5 exclusions",
    )
    sites = []
    blocks: dict[str, int] = {}
    for site in sorted(source_sites, key=lambda row: row["record_id"]):
        record, name = site["record_id"], site["site_id"]
        _require(record == "author:" + name, "literal original author identity")
        geometry, source = geometries[record], metadata[name]
        latitude, longitude = float(source["latdd"]), float(source["londd"])
        _require(
            math.isfinite(latitude)
            and math.isfinite(longitude)
            and abs(latitude) <= 90
            and abs(longitude) <= 180,
            "finite primary coordinates",
        )
        _require(
            type(geometry["latitude"]) in (int, float)
            and type(geometry["longitude"]) in (int, float)
            and geometry["latitude"] == latitude
            and geometry["longitude"] == longitude,
            "source CSV/geometry coordinates",
        )
        shoreline = float(source["radius"])
        _same_radius(
            shoreline, _number(geometry["basin"]["diameter_m"], positive=True) / 2
        )
        outer: list[float] = []
        for key in ("inversion_rings", "forward_rings"):
            rings = geometry[key]
            _require(
                type(rings) is list and bool(rings), "explicit source ring support"
            )
            outer.extend(_number(ring["outer_m"], positive=True) for ring in rings)
        declared = experiment["request_template"]["configuration"]["reveals"]
        if "region_cutoff_m" in declared:
            outer.append(_number(declared["region_cutoff_m"], positive=True))
        radius = max([cutoffs[record], *outer])
        _require(radius >= 100000.0, "full declared source footprint, not basin radius")
        block = source["LCGRID_ID"]
        blocks[block] = blocks.get(block, 0) + 1
        sites.append(
            {
                "record_id": record,
                "group_id": groups[record],
                "block_id": block,
                "latitude": latitude,
                "longitude": longitude,
                "source_radius_m": radius,
                "target_radius_m": target_radius,
                "coordinate_uncertainty_m": 0.0,
                "geometry_reference": geometry_pins[record],
                "basin_shoreline_radius_m": shoreline,
            }
        )
    _require(blocks == {"512": 8, "562": 7}, "two complete disjoint source blocks")
    refs = [*reader.refs, metadata_ref]
    _require(
        len(refs) == 19 and reader.size + metadata_ref["bytes"] <= 192 * 1024**2,
        "complete bounded metadata custody",
    )
    return {
        "schema_version": "author-lra-spatial-block-inputs.v1",
        "sites": sites,
        "regional_priority": priority,
        "saved_pairs": pairs,
        "policy": dict(policy),
        "excluded_source_block_ids": ["EXEBRID", "WHH11"],
        "excluded_source_block_reasons": dict.fromkeys(
            ("EXEBRID", "WHH11"), "outside_author_TW5_cohort"
        ),
        "sources": refs,
        "summary": {
            "sites": 15,
            "blocks": blocks,
            "saved_pairs": 39,
            "source_objects": 19,
            "source_bytes": reader.size + metadata_ref["bytes"],
            "raw_outcomes_opened": 0,
            "prediction_values_consumed": 0,
            "support_basis": "maximum explicit saved regional cutoff and all declared inversion/forward ring outer radii",
        },
    }


def check_block_sources(
    repository: Path, archive: Path, data_root: Path, packet: dict[str, Any]
) -> None:
    """Stream-check the closed source inventory without decoding another document."""
    roots = {
        "repository": repository.resolve(strict=True),
        "shared_data": data_root.resolve(strict=True),
    }
    archive_root = archive.resolve(strict=True)
    rows = packet["sources"]
    _require(type(rows) is list and len(rows) == 19, "closed metadata source inventory")
    seen = set()
    for row in rows:
        _require(
            type(row) is dict and set(row) == {"path", "bytes", "sha256", "storage"},
            "source guard fields",
        )
        sha, size, storage = row["sha256"], row["bytes"], row["storage"]
        _require(
            type(sha) is str
            and re.fullmatch(r"[0-9a-f]{64}", sha) is not None
            and sha not in seen
            and type(size) is int
            and 0 < size <= 140 * 1024**2
            and type(row["path"]) is str
            and bool(row["path"]),
            "source guard identity",
        )
        seen.add(sha)
        if storage == "archive_object":
            path = archive_root / "objects" / sha[:2] / sha
        else:
            _require(storage in roots, "source guard storage")
            relative = Path(row["path"])
            _require(
                not relative.is_absolute() and ".." not in relative.parts,
                "source guard relative path",
            )
            path = roots[storage] / relative
        _require(
            path.is_file()
            and not any(part.is_symlink() for part in (path, *path.parents))
            and path.stat().st_size == size,
            "source guard ordinary exact-size file",
        )
        digest, consumed = hashlib.sha256(), 0
        with path.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                consumed += len(chunk)
                _require(consumed <= size, "source guard growing file")
                digest.update(chunk)
        _require(
            consumed == size and digest.hexdigest() == sha, "source guard bytes changed"
        )
