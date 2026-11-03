"""Independent original-source joins for cached geographic transfer."""

from __future__ import annotations

import csv
import hashlib
from io import StringIO
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.inputs import decode

from ...predictive_uncertainty.verification.sources import bind_sources
from ..inputs import check_sources


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent geographic transfer: " + message)


def _read(repository: Path, pin: dict[str, Any], *, raw: bool = False) -> Any:
    relative = Path(pin["path"])
    _require(
        not relative.is_absolute() and ".." not in relative.parts,
        "source relative path",
    )
    path = repository / relative
    _require(
        path.is_file() and not any(part.is_symlink() for part in (path, *path.parents)),
        "ordinary source file",
    )
    body = path.read_bytes()
    _require(
        len(body) == pin["bytes"] and hashlib.sha256(body).hexdigest() == pin["sha256"],
        "exact original source bytes",
    )
    return body if raw else decode(body)


def _member(repository: Path, base: Path, pin: dict[str, Any]) -> Any:
    _require(Path(pin["path"]).name == pin["path"], "direct original product member")
    return _read(repository, {**pin, "path": (base / pin["path"]).as_posix()})


def bind_projection(
    repository: Path, protocol: dict[str, Any], packet: dict[str, Any]
) -> tuple[dict[str, dict[str, int]], dict[str, Any]]:
    """Reopen original source lineage after authenticating the new prediction freeze."""
    parent_result = _read(repository, protocol["sources"]["source_result"])
    manifest = _read(repository, protocol["sources"]["prediction_manifest"])
    base = Path(protocol["sources"]["source_result"]["path"]).parent
    _require(
        manifest["files"]
        == {
            key: parent_result["products"][key]
            for key in ("inputs", "draws", "predictions")
        },
        "old frozen members",
    )
    original, draws, old_predictions = (
        _member(repository, base, manifest["files"][key])
        for key in ("inputs", "draws", "predictions")
    )
    source_facts = bind_sources(repository, original)
    old_cases = {row["case_id"]: row for row in original["cases"]}
    old_cached = {row["case_id"]: row for row in old_predictions["cases"]}
    lineage = original["accounting"]["owner_lineage"]
    original_pins = {row["path"]: row for row in original["source_files"]}
    sites = {site["owner_id"]: site for site in packet["sites"]}
    owners = {row["owner_id"]: row["counts"] for row in original["owners"]}
    active = {case["regional_owner_id"] for case in old_cases.values()} | {
        local["owner_id"]
        for case in old_cases.values()
        for local in case["local_owners"]
    }
    _require(set(sites) == active and len(sites) == 4, "complete active source sites")
    expected_observations, expected_roles = [], []
    for owner in sorted(active):
        raw_pin = lineage[owner]["raw"]
        geometry_pin = original_pins[
            raw_pin["path"].removesuffix("-raw.json") + "-geometry.json"
        ]
        geometry = _read(repository, geometry_pin)
        place = lineage[owner]["core"]
        target = place != "KRAGMJNY"
        expected_site = {
            "owner_id": owner,
            "place_id": place,
            "block_id": "solsoe" if place == "SOLSOE83" else "sweden",
            "target_eligible": target,
            "latitude": geometry["latitude"],
            "longitude": geometry["longitude"],
            "source_radius_m": 100000.0,
            "target_radius_m": 1000.0 if target else None,
            "coordinate_uncertainty_m": 0.0,
        }
        _require(
            sites[owner] == expected_site
            and geometry["sample_metadata"]["sample_id"] == owner,
            "original site/geometry role projection",
        )
        if target:
            _require(
                max(row["outer_m"] for row in geometry["forward_rings"]) == 100000
                and max(row["outer_m"] for row in geometry["inversion_rings"]) == 1000,
                "original explicit finite rings",
            )
            expected_observations.append(
                {"target_id": owner, "raw": raw_pin, "geometry": geometry_pin}
            )
    for case in old_cases.values():
        expected_roles.append(
            {
                "case_id": case["case_id"],
                "target_id": case["target_id"],
                "required_source_owner_ids": [
                    case["regional_owner_id"],
                    *(row["owner_id"] for row in case["local_owners"]),
                ],
                "heldout_block_id": sites[case["target_id"]]["block_id"],
            }
        )
    _require(
        sorted(packet["target_roles"], key=lambda row: row["case_id"])
        == sorted(expected_roles, key=lambda row: row["case_id"]),
        "complete original three-source forecast roles",
    )
    _require(
        sorted(packet["observation_refs"], key=lambda row: row["target_id"])
        == sorted(expected_observations, key=lambda row: row["target_id"]),
        "original target observation/geometry refs",
    )
    _require(
        packet["prior_dispositions"] == original["dispositions"]
        and len(packet["prior_dispositions"]) == 54,
        "all prior dispositions retained",
    )
    eligible_ids = {
        role["case_id"]
        for role in expected_roles
        if all(
            sites[owner]["block_id"] != role["heldout_block_id"]
            for owner in role["required_source_owner_ids"]
        )
    }
    _require(
        {row["case"]["case_id"] for row in packet["candidate_cases"]} == eligible_ids
        and len(eligible_ids) == 1,
        "role-disjoint source projection",
    )
    for candidate in packet["candidate_cases"]:
        case = candidate["case"]
        _require(
            case == old_cases[case["case_id"]]
            and candidate["cached_fit"] == old_cached[case["case_id"]]
            and candidate["ppe_samples"] == draws["ppe"],
            "unchanged case-scoped cached fit draws and PPE",
        )
        _require(
            candidate["scientific_refs"]["allowed_inputs"]
            == candidate["cached_fit"]["allowed_inputs"],
            "original scientific allowed inputs",
        )
        _require(
            candidate["nominal"]["reference_predictions"]
            == [
                row
                for row in original["nominal_predictions"]
                if row["case_id"] == case["case_id"]
            ]
            and candidate["nominal"]["ppe"] == draws["ppe_means"],
            "original nominal handoff references",
        )
        local_covers: list[list[list[float]]] = []
        regional: list[float] | None = None
        nominal_refs = candidate["scientific_refs"]["nominal_fits"]
        _require(len(nominal_refs) == 2, "two original local native fits")
        for local, refs in zip(case["local_owners"], nominal_refs, strict=True):
            _require(
                refs["owner_id"] == local["owner_id"]
                and refs["native_manifest"]
                == original_pins[refs["native_manifest"]["path"]],
                "source-qualified nominal manifest",
            )
            native = _read(repository, refs["native_manifest"])
            native_root = Path(refs["native_manifest"]["path"]).parent
            _require(
                refs["request"]["path"] == (native_root / "request.json").as_posix()
                and refs["request"] == original_pins[refs["request"]["path"]]
                and refs["request"]["sha256"] == native["files"]["request.json"],
                "original manifest-bound request member",
            )
            request = _read(repository, refs["request"])
            _require(
                request["local"]["samples"][0]["sample_id"] == local["owner_id"]
                and request["regional"]["samples"][0]["sample_id"]
                == case["regional_owner_id"],
                "nominal native source ownership",
            )
            for key, relative in (
                ("cover_csv", "numerical/local_love/cover_mean.csv"),
                ("regional_csv", "numerical/regional_reveals/reconstruction.csv"),
            ):
                _require(
                    refs[key]["path"] == (native_root / relative).as_posix(),
                    "exact native fit member responsibility",
                )
                entry = native["files"][relative]
                _require(
                    type(entry) is str and entry == refs[key]["sha256"],
                    "manifest-bound new CSV member",
                )
            cover_rows = list(
                csv.DictReader(
                    StringIO(
                        _read(repository, refs["cover_csv"], raw=True).decode(
                            "utf-8-sig"
                        )
                    )
                )
            )
            _require(
                len(cover_rows) == 2 and float(cover_rows[1]["index"]) == 750.0,
                "both original nominal local rings",
            )
            local_covers.append(
                [[float(row[taxon]) for taxon in packet["axis"]] for row in cover_rows]
            )
            region_rows = list(
                csv.DictReader(
                    StringIO(
                        _read(repository, refs["regional_csv"], raw=True).decode(
                            "utf-8-sig"
                        )
                    )
                )
            )
            _require(len(region_rows) == 1, "one original regional CSV row")
            values = [
                float(region_rows[0][taxon + ".mean"]) / 100 for taxon in packet["axis"]
            ]
            _require(
                regional is None or values == regional, "shared original nominal region"
            )
            regional = values
        _require(
            candidate["nominal"]["local_covers_by_ring"] == local_covers
            and candidate["nominal"]["regional_cover"] == regional,
            "original nominal cover projection",
        )
    check_sources(repository, packet)
    return {
        target: dict(zip(packet["axis"], owners[target], strict=True))
        for target in (role["target_id"] for role in expected_roles)
    }, source_facts
