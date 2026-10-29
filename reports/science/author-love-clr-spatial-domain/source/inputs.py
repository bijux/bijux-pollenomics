"""Authenticate admitted nominal compositions and join outcome-free spatial inputs."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import runpy
from typing import Any


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def decode(raw: bytes) -> Any:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in rows:
            require(key not in result, "Duplicate scientific metadata key")
            result[key] = value
        return result

    def refuse(value: str) -> None:
        raise ValueError("Nonfinite scientific metadata: " + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=refuse)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def checked(root: Path, row: dict[str, Any]) -> bytes:
    require(
        set(row) == {"path", "sha256", "bytes"}
        and type(row["bytes"]) is int
        and 0 <= row["bytes"] <= 32 * 1024**2,
        "Finite exact input pin required",
    )
    path: Path = root / row["path"]
    require(
        ".." not in path.parts
        and path.is_file()
        and path.stat().st_nlink == 1
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Independent physical scientific input required",
    )
    raw = path.read_bytes()
    require(
        len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"],
        "Scientific input identity changed",
    )
    return raw


def join(
    training: dict[str, Any],
    experiment: dict[str, Any],
    geometries: dict[str, Any],
    protocol: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, Any]]:
    from bijux_pollenomics.analysis.lra_validation.contracts import SiteRecord
    from bijux_pollenomics.analysis.lra_validation.spatial import SiteCoordinate
    from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out

    require(
        training["schema_version"] == "author-love-transport-training.v1"
        and training["method"] == "gpm neutral"
        and training["candidate"] == protocol["nominal_candidate"]
        and training["protocol_sha256"] == protocol["nominal_training_protocol_sha256"],
        "Exact admitted nominal training header required",
    )
    records = training["numerical_requests"]
    require(
        isinstance(records, dict)
        and len(records) == 39
        and isinstance(training["logical_requests"], list)
        and len(training["logical_requests"]) == 2715,
        "Complete39 requests/2715 logical rows required",
    )
    require(
        digest(training["logical_requests"]) == protocol["logical_ancestry_sha256"],
        "Original serialized fold ancestry changed",
    )
    sites = {row["record_id"]: row for row in experiment["sites"]}
    require(
        len(sites) == len(experiment["sites"]) == len(geometries) == 15
        and set(sites) == set(geometries),
        "Exact fifteen physical site identities required",
    )
    source_records = [
        SiteRecord(row["record_id"], row["site_id"], tuple(row["identity_keys"]))
        for row in sites.values()
    ]
    outer_folds = grouped_leave_one_out(source_records)
    require(len(outer_folds) == 15, "Fifteen original whole-site groups required")
    groups = {
        record: fold.test_group_ids[0]
        for fold in outer_folds
        for record in fold.test_record_ids
    }
    coordinates = {}
    for record, geometry in geometries.items():
        sample = geometry["sample_metadata"]
        require(
            sample["site_id"] == sites[record]["site_id"]
            and sample["bin_id"] == "author-TW5"
            and sample["age_type"] == "calendar_bp"
            and sample["age_support_bp"] == [[1250, 1750]],
            "Original source geometry/time identity required",
        )
        coordinates[record] = SiteCoordinate(
            geometry["latitude"], geometry["longitude"]
        )
    taxa = experiment["request_template"]["taxa"]
    require(len(taxa) == len(set(taxa)) == 30, "Exact thirty-taxon axis required")
    zero_counts = {}
    for request, row in records.items():
        require(
            row["request_sha256"] == request
            and row["taxa"] == taxa
            and isinstance(row["selections"], list)
            and len(row["selections"]) == 2,
            "Saved request/axis/two-ring container differs",
        )
        require(
            all(
                isinstance(selected, dict)
                and type(selected["ring_index"]) is int
                and selected["ring_index"] == ring
                and selected["request_sha256"] == request
                for ring, selected in enumerate(row["selections"])
            ),
            "Exact selected ring identities required",
        )
        values = row["selections"][1]["composition"]
        require(
            isinstance(values, dict)
            and set(values) == set(taxa)
            and all(
                type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1
                for value in values.values()
            )
            and abs(sum(values.values()) - 1) <= 1e-9,
            "Unmodified closed numeric composition dictionary required",
        )
        zero_counts[request] = sum(value == 0 for value in values.values())
    require(
        sum(value > 0 for value in zero_counts.values()) == 26
        and sum(zero_counts.values()) == 80,
        "Exact admitted zero-domain population changed",
    )
    logical: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in training["logical_requests"]:
        require(
            set(row)
            == {
                "kind",
                "outer_target",
                "target",
                "fold",
                "local_record_id",
                "regional_anchor_record_id",
                "request_sha256",
            },
            "Finite persisted logical row required",
        )
        logical[(row["kind"], row["outer_target"], row["target"])].append(row)
    support = {
        "support_profile": experiment["support_profile"],
        "local_support_radius_m": experiment["local_support_radius_m"],
        "taxa": taxa,
        "temporal_matching": experiment["request_template"]["temporal_matching"],
        "versions": experiment["request_template"]["versions"],
    }
    require(
        support["support_profile"] == "same-outer-radius-homogeneous-v1"
        and support["local_support_radius_m"] == 1000
        and experiment["local_ring_count"] == 2,
        "Original support estimand required",
    )
    support_id = "experiment-support:" + digest(support)
    contexts = []
    certificates = []
    for outer in outer_folds:
        target = outer.test_record_ids[0]
        inner = grouped_leave_one_out(
            [row for row in source_records if row.record_id in outer.train_record_ids]
        )
        for kind, fold in [("outer", outer), *(("inner", fold) for fold in inner)]:
            key = kind, target, fold.test_record_ids[0]
            require(
                key in logical and target not in fold.train_record_ids,
                "Outer site/core leaked into spatial training",
            )
            rows = logical.pop(key)
            anchor = next(
                record
                for record in experiment["regional_priority"]
                if record in fold.train_record_ids
            )
            expected = set(fold.train_record_ids) - {anchor}
            require(
                len(rows) == len(expected) == (13 if kind == "outer" else 12)
                and {row["local_record_id"] for row in rows} == expected
                and len({row["request_sha256"] for row in rows}) == len(rows),
                "Complete unique training local/anchor population required",
            )
            compositions = {}
            graph: dict[str, tuple[str, ...]] = dict.fromkeys(fold.train_record_ids, ())
            fit_ids = []
            for row in rows:
                request = row["request_sha256"]
                require(
                    request in records
                    and digest(row["fold"]) == digest(fold.as_dict())
                    and row["regional_anchor_record_id"] == anchor
                    and records[request]["item_id"] == row["local_record_id"],
                    "Saved native request/fold/anchor identity differs",
                )
                selected = records[request]["selections"][1]
                compositions[groups[row["local_record_id"]]] = dict(
                    selected["composition"]
                )
                node = "nominal-fit:" + digest(
                    {
                        "request": request,
                        "selected_attempt": selected["selected_attempt_sha256"],
                    }
                )
                require(node not in graph, "Repeated selected-fit lineage node")
                graph[node] = (row["local_record_id"], anchor)
                fit_ids.append(node)
            graph[support_id] = ()
            zero = sum(
                any(value == 0 for value in vector.values())
                for vector in compositions.values()
            )
            require(5 <= zero <= 11, "Original per-context zero domain changed")
            hashes = sorted(row["request_sha256"] for row in rows)
            certificate = {
                "kind": kind,
                "outer_target": target,
                "target": key[2],
                "fold_sha256": digest(fold.as_dict()),
                "request_sha256s": hashes,
                "zero_containing_predictors": zero,
            }
            certificates.append(certificate)
            contexts.append(
                {
                    **certificate,
                    "fold": fold,
                    "support_id": support_id,
                    "compositions": compositions,
                    "coordinates": {
                        groups[record]: coordinates[record] for record in expected
                    },
                    "input_ids": (*fold.train_record_ids, *fit_ids, support_id),
                    "dependency_graph": graph,
                    "admitted_external_ids": (*fit_ids, support_id),
                    "predictor_group_ids": tuple(sorted(compositions)),
                }
            )
    require(
        not logical
        and len(contexts) == 225
        and digest(
            sorted(
                certificates,
                key=lambda row: (row["kind"], row["outer_target"], row["target"]),
            )
        )
        == protocol["context_map_sha256"],
        "Exact complete225 context projection required",
    )
    return (
        contexts,
        groups,
        {
            "support": support,
            "zero_containing_requests": 26,
            "zero_cells": 80,
            "geometry_records": 15,
        },
    )


def load(
    repository: Path, prepared: Path, protocol: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, Any], list[dict[str, Any]]]:
    for row in protocol["source_pins"]:
        checked(repository, row)
    authority = decode(
        checked(repository, protocol["prior_evidence"]["nominal_authority"])
    )
    require(
        authority["source_candidate"] == protocol["nominal_candidate"]
        and authority["independent_semantics"]["approved"] is True
        and authority["independent_semantics"]["scientific_saved_products_admitted"]
        is True,
        "Admitted original nominal publication required",
    )
    descriptor = decode(
        checked(repository, protocol["prior_evidence"]["nominal_descriptor"])
    )
    nominal = [row for row in descriptor["shards"] if row["method"] == "gpm neutral"]
    require(
        len(nominal) == 1
        and nominal[0]["training"] == protocol["prior_evidence"]["nominal_training"],
        "Exact nominal saved-training authority required",
    )
    common = runpy.run_path(
        str(repository / protocol["borrowed_sources"]["common"]["path"])
    )
    scientific = runpy.run_path(
        str(repository / protocol["borrowed_sources"]["admission"]["path"])
    )
    admission = scientific["admit_shard"](
        common,
        repository,
        nominal[0],
        protocol["nominal_candidate"],
        protocol["nominal_training_protocol_sha256"],
    )
    require(
        {p.name for p in prepared.iterdir()}
        == {row["path"] for row in protocol["inputs"]}
        and len(protocol["inputs"]) == 37,
        "Exact original37 input namespace required",
    )
    bodies = {row["path"]: checked(prepared, row) for row in protocol["inputs"]}
    experiment = decode(bodies["experiment.json"])
    catalog = {row["path"]: row for row in protocol["inputs"]}
    require(
        len(catalog) == 37 and all(Path(name).name == name for name in catalog),
        "Unique basename input catalogue required",
    )
    for site in experiment["sites"]:
        require(
            site["geometry"]["sha256"] == catalog[site["geometry"]["path"]]["sha256"],
            "Native geometry reference differs from admitted catalogue",
        )
    geometries = {
        row["record_id"]: decode(bodies[row["geometry"]["path"]])
        for row in experiment["sites"]
    }
    training = decode(
        checked(repository, protocol["prior_evidence"]["nominal_training"])
    )
    contexts, groups, summary = join(training, experiment, geometries, protocol)
    return contexts, groups, summary, admission["references"]
