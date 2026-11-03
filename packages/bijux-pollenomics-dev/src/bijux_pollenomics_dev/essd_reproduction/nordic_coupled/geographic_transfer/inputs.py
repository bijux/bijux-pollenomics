"""Project qualified coupled sources into a target-count-free transfer packet."""

from __future__ import annotations

import csv
import hashlib
from io import StringIO
import json
import math
from pathlib import Path
import re
import struct
from typing import Any

from ..predictive_uncertainty.inputs import _Reader

_AXIS = ["Betula", "Ulmus"]
_METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")
_WINDOW = "cal-bp-2700-3200"
_PLACES = {"BOKE", "BUS", "SOLSOE83", "KRAGMJNY"}


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Geographic source projection: " + message)


def _same(left: Any, right: Any, label: str) -> None:
    _require(
        json.dumps(left, sort_keys=True, allow_nan=False)
        == json.dumps(right, sort_keys=True, allow_nan=False),
        label,
    )


def _finite(value: Any) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _array(value: Any, shape: tuple[int, ...], kind: str) -> None:
    if shape:
        _require(
            type(value) is list and len(value) == shape[0],
            "complete source array shape",
        )
        for item in value:
            _array(item, shape[1:], kind)
    elif kind == "number":
        _require(value is None or _finite(value), "finite-or-null saved source value")
    elif kind == "reason":
        _require(
            value is None or (type(value) is str and bool(value)), "saved refusal label"
        )
    else:
        _require(type(value) is bool, "literal saved validity mask")


def _case_arrays(value: dict[str, Any]) -> None:
    _require(
        value["schema_version"] == "krageholm-predictive-ensemble.case.v1"
        and value["replicates"] == 1024
        and value["axis"] == _AXIS,
        "qualified source case header",
    )
    for field, shape, kind in (
        ("regional_cover", (1024, 2), "number"),
        ("regional_refusals", (1024,), "reason"),
        ("local_signed_cover", (1024, 2, 2, 2), "number"),
        ("local_ring_refusals", (1024, 2, 2), "reason"),
        ("local_refusals", (1024, 2), "reason"),
    ):
        _array(value[field], shape, kind)
    _require(
        set(value["methods"]) == set(_METHODS), "all original source method families"
    )
    for method in value["methods"].values():
        _array(method["valid_mask"], (1024,), "mask")
        _array(method["refusals"], (1024,), "reason")
        for field in ("cover", "pollen", "direct_pollen", "physical_minus_direct"):
            _array(method[field], (1024, 2), "number")
        _require(
            all(
                valid == (reason is None)
                for valid, reason in zip(
                    method["valid_mask"], method["refusals"], strict=True
                )
            ),
            "saved method mask/refusal agreement",
        )
        _require(
            method["summary"]["defined_replicates"] == sum(method["valid_mask"]),
            "saved method mask denominator",
        )


def _pin(reader: _Reader, path: Path) -> dict[str, Any]:
    return dict(reader.refs[path.relative_to(reader.repository).as_posix()])


def _member(
    reader: _Reader, base: Path, pin: dict[str, Any], *, decode: bool = True
) -> Any:
    _require(
        type(pin["path"]) is str and Path(pin["path"]).name == pin["path"],
        "direct closed source product member",
    )
    return reader.read(pin, base=base, decode=decode, maximum=8 * 1024**2)


def _rows_hash(rows: Any, *, integer: bool) -> str:
    _array(rows, (1024, 2), "number")
    digest = hashlib.sha256()
    for row in rows:
        _require(all(_finite(x) and x >= 0 for x in row), "nonnegative source draw")
        if integer:
            _require(
                all(type(x) is int and x <= 2**53 for x in row),
                "integer source count draw",
            )
        digest.update(struct.pack("<qq" if integer else "<dd", *row))
    return digest.hexdigest()


def _nominal_fit(
    reader: _Reader,
    fold: dict[str, Any],
    owner: str,
    regional: str,
    geometries: dict[str, Any],
) -> tuple[list[list[float]], list[float], dict[str, Any]]:
    refs = [
        row
        for row in fold["kernel_refs"]
        if row["local_owner_id"] == owner
        and row["path"].endswith("/numerical/local_love/aux_Kloc.csv")
    ]
    _require(len(refs) == 1, "one original local native product")
    directory = reader.path(refs[0]["path"]).parents[2]
    manifest_path = directory / "manifest.json"
    key = manifest_path.relative_to(reader.repository).as_posix()
    _require(
        key in reader.refs,
        "native manifest belongs to original qualified source closure",
    )
    manifest = reader.read(reader.refs[key])
    _require(
        manifest["schema_version"] == "lra-product.v1"
        and manifest["retained_taxa"] == _AXIS,
        "native fit axis",
    )
    request_path = directory / "request.json"
    request = reader.member(directory, manifest["files"], "request.json")
    _require(
        request["taxa"] == _AXIS
        and len(request["local"]["samples"]) == len(request["regional"]["samples"]) == 1
        and request["local"]["samples"][0]["sample_id"] == owner
        and request["regional"]["samples"][0]["sample_id"] == regional,
        "nominal original local/regional ownership",
    )
    cover_name = "numerical/local_love/cover_mean.csv"
    raw = reader.member(directory, manifest["files"], cover_name, decode=False)
    table = csv.DictReader(StringIO(raw.decode("utf-8-sig")))
    _require(table.fieldnames == ["index", *_AXIS], "nominal cover source columns")
    rows = list(table)
    _require(len(rows) == 2, "both nominal signed rings retained")
    covers = []
    for ring, row in enumerate(rows):
        index = float(row["index"])
        expected = geometries[owner]["inversion_rings"][ring]["mean_m"]
        _require(_finite(index) and index == expected, "nominal source ring index")
        values = [float(row[taxon]) for taxon in _AXIS]
        _require(
            all(_finite(x) for x in values) and abs(sum(values) - 1) <= 1e-9,
            "signed nominal cover closure",
        )
        covers.append(values)
    _require(
        float(rows[1]["index"]) == 750.0 and all(0 <= x <= 1 for x in covers[1]),
        "selected nominal ring1 composition",
    )
    # Negative ring0 is authenticated diagnostic evidence, not an admission gate.
    regional_name = "numerical/regional_reveals/reconstruction.csv"
    raw = reader.member(directory, manifest["files"], regional_name, decode=False)
    regional_rows = list(csv.DictReader(StringIO(raw.decode("utf-8-sig"))))
    _require(len(regional_rows) == 1, "one nominal regional reconstruction")
    row = regional_rows[0]
    _require(
        row["Distance.weighting"] == "gpm neutral"
        and row["Basin.type"] == "lake"
        and float(row["coordinate"]) == 2700.0,
        "nominal regional method/support",
    )
    cover = [float(row[taxon + ".mean"]) / 100 for taxon in _AXIS]
    _require(
        all(_finite(x) and 0 <= x <= 1 for x in cover) and abs(sum(cover) - 1) <= 1e-9,
        "source percentage regional cover",
    )
    return (
        covers,
        cover,
        {
            "owner_id": owner,
            "native_manifest": _pin(reader, manifest_path),
            "request": _pin(reader, request_path),
            "cover_csv": _pin(reader, directory / cover_name),
            "regional_csv": _pin(reader, directory / regional_name),
        },
    )


def load_inputs(repository: Path, protocol: dict[str, Any]) -> dict[str, Any]:
    """Authenticate old sources once and expose no target counts to prediction."""
    _require(
        protocol["schema_version"] == "krageholm-geographic-transfer-protocol.v1",
        "prospective transfer protocol",
    )
    sources = protocol["sources"]
    _require(
        set(sources)
        == {
            "parent_protocol",
            "source_result",
            "prediction_manifest",
            "source_verification",
        },
        "four qualified source authorities",
    )
    reader = _Reader(repository)
    parent, result, manifest, verification = (
        reader.read(sources[name])
        for name in (
            "parent_protocol",
            "source_result",
            "prediction_manifest",
            "source_verification",
        )
    )
    _require(
        result["schema_version"] == "coupled-pollen-bootstrap-result.v1"
        and result["status"] == "produced_awaiting_independent_verification"
        and result["source_guards_passed"] is True,
        "qualified parent result",
    )
    _same(result["protocol"], sources["parent_protocol"], "parent protocol identity")
    _require(
        verification["schema_version"] == "coupled-pollen-bootstrap-verification.v1"
        and verification["source_commit"] == result["source_commit"]
        and verification["source_observation"]["status"] == "passed"
        and verification["source_observation"]["source_files_verified"] == 141
        and verification["numerical_observation"]["status"] == "passed"
        and verification["numerical_observation"]["accounting_verified"] is True,
        "existing independent source and numerical qualification",
    )
    _same(
        result["prediction_manifest"],
        {
            **sources["prediction_manifest"],
            "path": Path(sources["prediction_manifest"]["path"]).name,
        },
        "old prediction manifest binding",
    )
    _require(
        manifest["schema_version"] == "coupled-pollen-bootstrap-freeze.v1",
        "closed source prediction manifest",
    )
    _same(
        manifest["files"],
        {key: result["products"][key] for key in ("inputs", "draws", "predictions")},
        "original frozen product identities",
    )
    base = reader.path(sources["source_result"]["path"]).parent
    original, draws, predictions = (
        _member(reader, base, result["products"][key])
        for key in ("inputs", "draws", "predictions")
    )
    _require(
        predictions["schema_version"] == "krageholm-predictive-ensemble.v1",
        "original ensemble schema",
    )
    _member(reader, base, result["products"]["summary"], decode=False)
    _same(original["protocol"], parent, "original uncertainty protocol")
    _require(
        len(original["owners"]) == 24
        and len(original["folds"]) == 18
        and len(original["dispositions"]) == 54
        and len(original["cases"]) == 3,
        "complete retained source accounting",
    )
    _same(
        predictions["original_dispositions"],
        original["dispositions"],
        "all original dispositions retained",
    )
    files = original["source_files"]
    _require(
        type(files) is list
        and len(files) == len({row["path"] for row in files}) == 141,
        "141 original source files",
    )
    for pin in files:
        reader.read(pin, decode=False)
    prep_pins = [
        pin for pin in files if pin["path"].endswith(f"/{_WINDOW}/preparations.json")
    ]
    _require(len(prep_pins) == 1, "one original first-window preparation packet")
    preparations = reader.read(prep_pins[0])
    _require(
        len(preparations) == 3
        and all(
            _finite(row["regional_cutoff_m"])
            and row["regional_cutoff_m"] == 100000.0
            and _finite(row["local_support_radius_m"])
            and row["local_support_radius_m"] == 1000.0
            for row in preparations
        ),
        "original finite regional/local source support",
    )
    declared = parent["sources"]
    coupled = reader.read(declared["coupled_protocol"])
    _require(coupled["axis"] == _AXIS, "source physical axis")
    geometry_policy = protocol["geography"]
    _same(
        geometry_policy["blocks"],
        {"sweden": ["BOKE", "BUS", "KRAGMJNY"], "solsoe": ["SOLSOE83"]},
        "fixed geographic source roles",
    )
    _require(
        geometry_policy["source_only_places"] == ["KRAGMJNY"]
        and geometry_policy["target_places"] == ["BOKE", "BUS", "SOLSOE83"],
        "three targets and region-only KRAG",
    )
    _require(
        geometry_policy["source_radius_m"] == 100000.0
        and geometry_policy["target_radius_m"] == 1000.0
        and type(geometry_policy["coordinate_uncertainty_m"]) in (int, float)
        and geometry_policy["coordinate_uncertainty_m"] == 0,
        "declared conditional geographic support",
    )
    active_ids = original["accounting"]["active_draw_owner_ids"]
    lineage = original["accounting"]["owner_lineage"]
    _require(
        len(active_ids) == len(set(active_ids)) == 4
        and {lineage[owner]["core"] for owner in active_ids} == _PLACES,
        "four active original owners",
    )
    geometries, sites, owner_places = {}, [], {}
    observations = []
    for owner in active_ids:
        core, raw_pin = lineage[owner]["core"], lineage[owner]["raw"]
        _require(
            _WINDOW in owner
            and raw_pin["path"].endswith(f"/{_WINDOW}/{core}-raw.json"),
            "source physical owner/window",
        )
        _require(
            raw_pin["path"] in reader.refs, "source observation in qualified closure"
        )
        _same(raw_pin, reader.refs[raw_pin["path"]], "original observation reference")
        geometry_path = raw_pin["path"].removesuffix("-raw.json") + "-geometry.json"
        _require(geometry_path in reader.refs, "geometry in original source closure")
        geometry_pin = reader.refs[geometry_path]
        geometry = reader.read(geometry_pin)
        _require(
            geometry["sample_metadata"]["sample_id"] == owner,
            "geometry sample identity",
        )
        latitude, longitude = geometry["latitude"], geometry["longitude"]
        _require(
            _finite(latitude)
            and _finite(longitude)
            and abs(latitude) <= 90
            and abs(longitude) <= 180,
            "source geographic coordinates",
        )
        target = core != "KRAGMJNY"
        if not target:
            _require(
                set(geometry) == {"basin", "sample_metadata", "longitude", "latitude"},
                "no invented KRAG local geometry",
            )
        else:
            _require(
                max(row["outer_m"] for row in geometry["forward_rings"]) == 100000
                and max(row["outer_m"] for row in geometry["inversion_rings"]) == 1000,
                "original local/forward footprint",
            )
        geometries[owner], owner_places[owner] = geometry, core
        sites.append(
            {
                "owner_id": owner,
                "place_id": core,
                "block_id": "solsoe" if core == "SOLSOE83" else "sweden",
                "target_eligible": target,
                "latitude": latitude,
                "longitude": longitude,
                "source_radius_m": 100000.0,
                "target_radius_m": 1000.0 if target else None,
                "coordinate_uncertainty_m": 0.0,
            }
        )
        if target:
            observations.append(
                {
                    "target_id": owner,
                    "raw": dict(raw_pin),
                    "geometry": dict(geometry_pin),
                }
            )
    _require(
        draws["replicates"] == 1024
        and draws["seed"] == 20261027
        and draws["ppe_means"] == [5.106, 1.27]
        and draws["ppe_sds"] == [0.303, 0.05],
        "unchanged source working law",
    )
    _require(
        len(draws["owners"]) == 4
        and {row["owner_id"] for row in draws["owners"]} == set(active_ids),
        "four original draw owners accounted separately",
    )
    ppe_hash = _rows_hash(draws["ppe"], integer=False)
    cases = {case["case_id"]: case for case in original["cases"]}
    old_cases = {case["case_id"]: case for case in predictions["cases"]}
    _require(
        len(cases) == len(old_cases) == len(predictions["cases"]) == 3
        and set(cases) == set(old_cases),
        "source active case identities",
    )
    _require(
        {case["target_id"] for case in cases.values()}
        == {site["owner_id"] for site in sites if site["target_eligible"]},
        "three distinct original local targets",
    )
    target_roles, candidates = [], []
    for case_id, case in cases.items():
        old = old_cases[case_id]
        _case_arrays(old)
        _require(
            old["target_id"] == case["target_id"] and case["selected_ring_index"] == 1,
            "unchanged selected-ring owner",
        )
        allowed = old["allowed_inputs"]
        _same(allowed["case"], case, "original case scientific input")
        required = [
            case["regional_owner_id"],
            *(local["owner_id"] for local in case["local_owners"]),
        ]
        _require(
            len(required) == len(set(required)) == 3
            and case["target_id"] not in required
            and all(owner in owner_places for owner in required),
            "three required target-excluded source owners",
        )
        _require(
            owner_places[case["regional_owner_id"]] == "KRAGMJNY"
            and all(
                owner_places[local["owner_id"]] != "KRAGMJNY"
                for local in case["local_owners"]
            ),
            "KRAG remains regional source only",
        )
        _same(
            [row["owner_id"] for row in allowed["count_owners"]],
            required,
            "ordered source stream parents",
        )
        _require(
            allowed["ppe"]["samples_sha256"] == ppe_hash
            and allowed["ppe"]["replicates"] == 1024,
            "same-index shared PPE identity",
        )
        held = "solsoe" if owner_places[case["target_id"]] == "SOLSOE83" else "sweden"
        target_roles.append(
            {
                "case_id": case_id,
                "target_id": case["target_id"],
                "required_source_owner_ids": required,
                "heldout_block_id": held,
            }
        )
        if any(
            ("solsoe" if owner_places[owner] == "SOLSOE83" else "sweden") == held
            for owner in required
        ):
            continue
        # This is role-disjoint eligibility only. The caller must still screen distance.
        _require(
            owner_places[case["target_id"]] == "SOLSOE83",
            "only original role-disjoint candidate",
        )
        masks = [old["methods"][method]["valid_mask"] for method in _METHODS]
        _require(
            all(mask == masks[0] for mask in masks) and sum(masks[0]) == 860,
            "unchanged common860/164 source population",
        )
        for source in allowed["count_owners"]:
            bank_rows = [
                row for row in draws["owners"] if row["owner_id"] == source["owner_id"]
            ]
            _require(len(bank_rows) == 1, "one original allowed count stream")
            bank = bank_rows[0]
            _same(source["counts"], bank["counts"], "source counted denominator")
            _same(
                source["stream_index"], bank["stream_index"], "source stream metadata"
            )
            _require(
                source["samples_sha256"] == _rows_hash(bank["samples"], integer=True)
                and all(sum(row) == sum(bank["counts"]) for row in bank["samples"]),
                "same-index fixed-total source count stream",
            )
        fold = next(row for row in original["folds"] if row["case_id"] == case_id)
        nominal_covers, nominal_refs, nominal_regional = [], [], None
        for local in case["local_owners"]:
            covers, regional, refs = _nominal_fit(
                reader, fold, local["owner_id"], case["regional_owner_id"], geometries
            )
            nominal_covers.append(covers)
            nominal_refs.append(refs)
            if nominal_regional is None:
                nominal_regional = regional
            _same(regional, nominal_regional, "common nominal regional source")
        references = [
            row for row in original["nominal_predictions"] if row["case_id"] == case_id
        ]
        _require(
            len(references) == 3
            and {row["method"] for row in references} == set(_METHODS),
            "three original nominal baseline references",
        )
        for row in references:
            _same(
                row["regional_cover"],
                nominal_regional,
                "original nominal regional handoff",
            )
        candidates.append(
            {
                "case": case,
                "cached_fit": old,
                "ppe_samples": draws["ppe"],
                "nominal": {
                    "local_covers_by_ring": nominal_covers,
                    "regional_cover": nominal_regional,
                    "ppe": draws["ppe_means"],
                    "reference_predictions": references,
                },
                "scientific_refs": {
                    "allowed_inputs": allowed,
                    "nominal_fits": nominal_refs,
                },
            }
        )
    _require(
        len(candidates) == 1 and len(target_roles) == len(observations) == 3,
        "one role-disjoint candidate and three retained targets",
    )
    return {
        "schema_version": "krageholm-geographic-transfer-inputs.v1",
        "axis": _AXIS,
        "replicates": 1024,
        "sites": sites,
        "target_roles": target_roles,
        "candidate_cases": candidates,
        "observation_refs": observations,
        "prior_dispositions": original["dispositions"],
        "sources": list(reader.refs.values()),
        "summary": {
            "source_files_reauthenticated": 141,
            "prior_owners": 24,
            "prior_folds": 18,
            "prior_dispositions": 54,
            "target_roles": 3,
            "role_disjoint_candidates": 1,
            "inherited_defined_replicates": 860,
            "inherited_undefined_replicates": 164,
            "source_bytes": reader.total,
            "raw_target_files_decoded": 0,
            "scope": "Previously exposed source intake; whole-file hashes are accounting, source masks are inherited, and geometric admission remains pending",
        },
    }


def check_sources(repository: Path, packet: dict[str, Any]) -> None:
    """Stream-verify all consumed originals without decoding observations or products."""
    root = repository.resolve(strict=True)
    seen = set()
    for pin in packet["sources"]:
        relative = Path(pin["path"])
        _require(
            not relative.is_absolute()
            and ".." not in relative.parts
            and pin["path"] not in seen
            and type(pin["bytes"]) is int
            and pin["bytes"] > 0
            and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) is not None,
            "closed source guard identity",
        )
        seen.add(pin["path"])
        path = root / relative
        _require(
            path.is_file()
            and not any(part.is_symlink() for part in (path, *path.parents))
            and path.stat().st_size == pin["bytes"],
            "ordinary unchanged source guard",
        )
        digest, count = hashlib.sha256(), 0
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                count += len(chunk)
                _require(count <= pin["bytes"], "source grew during guard")
                digest.update(chunk)
        _require(
            count == pin["bytes"] and digest.hexdigest() == pin["sha256"],
            "source bytes changed after projection",
        )
