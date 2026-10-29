"""Qualify exact retained current aDNA metadata evidence without owning publisher outputs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ...contracts import JsonObject, ReportRebuildError
from ...retained_source import validate_capsule, validated_descriptor
from .contract_adjudication import evaluate
from .execution_packet import json_object, member_name, normalized, validate_packet

CAPTURE = "data/adna/current-default-export-capture/capture.json"
CAPTURE_SHA256 = "c3c4c2f14ebd7f3f5109a97c9fc8b3d6564d40139f8dd198f73a43ccce64cbe1"
WITNESS = "reports/science/source-cohorts/adna-current-contract-adjudication.json"
WITNESS_SHA256 = "7c1abf2b936ad95182ea3137c8e7a1df1f5553b2ceac2df7a9fe32a993e744a9"
AUTHORITY = "data/adna/current-contract-authority/authority-index.json"
AUTHORITY_SHA256 = "3d076ad23748f18962ea420eaf9c0e2e7c1b324b0542595677367e4c6aacbdd9"


def _require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("AADR current export evidence: " + reason)


def publisher_contract(owners: list[dict[str, Any]]) -> list[str]:
    """Declare maintained publisher inputs for the export scope."""
    paths = []
    for country in ("denmark", "finland", "norway", "sweden"):
        for suffix in ("csv", "geojson", "md"):
            paths.append(
                f"docs/report/countries/{country}/{country}_aadr_v66_samples.{suffix}"
            )
        paths.append(f"docs/report/countries/{country}/README.md")
    for path in paths:
        selected = [row for row in owners if path in row["paths"]]
        _require(
            len(selected) == 1
            and selected[0]["owner_id"] == "publisher"
            and selected[0]["role"] == "publisher_partition",
            "Exact unique existing publisher membership differs",
        )
    return paths


def physical(repository: Path, name: str) -> Path:
    """Resolve an ordinary retained-input file without following aliases."""
    path = repository / name
    _require(
        path.is_file()
        and path == path.resolve()
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Physical source member required: " + name,
    )
    return path


def checked(repository: Path, name: str, checksum: str) -> bytes:
    """Authenticate the declared identity of a retained member."""
    raw = physical(repository, name).read_bytes()
    _require(
        hashlib.sha256(raw).hexdigest() == checksum,
        "Retained source identity differs: " + name,
    )
    return raw


def exact_tree(root: Path, names: set[str]) -> None:
    """Require an exact, alias-free physical member inventory."""
    _require(
        root.is_dir() and not any(p.is_symlink() for p in (root, *root.parents)),
        "Physical capture root required",
    )
    actual = set()
    directories = set()
    for path in root.rglob("*"):
        _require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "Alias or special retained entry",
        )
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
        else:
            directories.add(path.relative_to(root).as_posix())
    _require(
        actual == names and directories == {"payloads"},
        "Retained namespace has missing/extra members",
    )


def _validated_aadr_current_export_evidence(
    repository: Path, owners: list[dict[str, Any]]
) -> JsonObject | None:
    present = [
        (repository / name).exists() or (repository / name).is_symlink()
        for name in (CAPTURE, WITNESS, AUTHORITY)
    ]
    if not any(present):
        return None
    _require(all(present), "Partial publication evidence is refused")
    publisher_contract(owners)
    packet = json_object(checked(repository, CAPTURE, CAPTURE_SHA256))
    resolver = validated_descriptor(
        repository, Path(CAPTURE).parent.as_posix(), packet["members"]
    )

    # Avoid resolving any original absolute source path; retained byte roles alone
    # choose a confined content-addressed member below this repository.
    def payload(name: str) -> bytes:
        return resolver.read_source(name)

    native = validate_packet(packet, payload)
    witness = json_object(checked(repository, WITNESS, WITNESS_SHA256))
    authority = json_object(checked(repository, AUTHORITY, AUTHORITY_SHA256))
    _require(
        authority["schema_version"] == "adna-current-contract-metadata-authority.v1",
        "Authority schema differs",
    )
    _require(
        authority["metadata_only_not_new_native_retention_exit"] is True
        and authority["raw_normalized_runtime_payloads_included"] is False,
        "Metadata authority scope inflated",
    )
    aux_root = (repository / AUTHORITY).parent
    exact_tree(aux_root, set(authority["members"]) | {"authority-index.json"})
    for name, row in authority["members"].items():
        member_name(name)
        raw = checked(
            repository,
            (aux_root / name).relative_to(repository).as_posix(),
            row["sha256"],
        )
        _require(len(raw) == row["bytes"], "Metadata payload length differs")
    raw_bindings = {r["original"]["path"]: r for r in packet["public_bindings"]}
    bindings = {r["original"]["path"]: r for r in authority["bindings"]}
    _require(
        len(bindings) == len(authority["bindings"]), "Repeated auxiliary metadata path"
    )

    def metadata(row: dict[str, Any]) -> dict[str, Any]:
        expected = normalized(row)
        name = expected["path"]
        if name in raw_bindings:
            binding = raw_bindings[name]
            _require(
                normalized(binding["original"]) == expected,
                "Raw capsule metadata identity differs",
            )
            raw = payload(binding["member"])
        else:
            _require(
                name in bindings, "Metadata authority omitted an exact required role"
            )
            binding = bindings[name]
            _require(
                normalized(binding["original"]) == expected,
                "Auxiliary metadata identity differs",
            )
            raw = checked(
                repository,
                (aux_root / binding["member"]).relative_to(repository).as_posix(),
                expected["sha256"],
            )
        _require(len(raw) == expected["bytes"], "Exact metadata size differs")
        return json_object(raw)

    refs = witness["authenticated_metadata_references"]
    docs = {
        name: metadata(row)
        for name, row in refs.items()
        if name != "requirement_source"
    }
    # The original workspace requirement file remains identity-only. Its frozen
    # literal clause is historical callback context, not a new backlog state.
    require_context = {
        "requirements": [
            {"id": "ADNA-001", "acceptance": "no pollen semantics leakage"}
        ]
    }
    evaluated = evaluate(docs, refs, require_context)
    for key, value in evaluated.items():
        _require(witness[key] == value, "Literal joint metadata result differs: " + key)
    _require(
        witness["whole_ADNA_001_closed"] is False, "Whole requirement was promoted"
    )
    for lane in ("raw_source_authority", "saved_source_authority"):
        declared = witness[lane]
        manifest = metadata(declared["manifest"])
        peer = metadata(declared["review"])
        _require(
            peer["approved"] is True
            and peer["source_manifest_sha256"] == declared["manifest"]["sha256"]
            and manifest["source_only"] is True,
            "Original source peer differs",
        )
        for row in manifest["files"]:
            name = row["path"]
            _require(
                name in raw_bindings or name in bindings,
                "Original public control source is missing",
            )
    callback_source = authority["joint_callback_source"]
    callback_manifest = metadata(callback_source["manifest"])
    callback_peer = metadata(callback_source["review"])
    _require(
        callback_manifest["source_only"] is True
        and callback_peer["approved"] is True
        and callback_peer["source_manifest_sha256"]
        == callback_source["manifest"]["sha256"],
        "Joint metadata callback source approval differs",
    )
    expected_rows = (
        [row for name, row in refs.items() if name != "requirement_source"]
        + witness["additional_authenticated_metadata"]
        + list(callback_source.values())
        + callback_manifest["files"]
    )
    for lane in ("raw_source_authority", "saved_source_authority"):
        expected_rows += metadata(witness[lane]["manifest"])["files"]
    expected: dict[str, dict[str, Any]] = {}
    for row in expected_rows:
        value = normalized(row)
        _require(
            value["path"] not in expected or expected[value["path"]] == value,
            "Conflicting expected public metadata identity",
        )
        expected[value["path"]] = value
    missing_from_raw = {name for name in expected if name not in raw_bindings}
    _require(
        set(bindings) == missing_from_raw,
        "Auxiliary metadata has missing/extra role payloads",
    )
    _require(
        {row["member"] for row in authority["bindings"]} == set(authority["members"]),
        "Auxiliary member role union differs",
    )
    for name, row in expected.items():
        binding = raw_bindings.get(name, bindings.get(name))
        _require(
            binding is not None and normalized(binding["original"]) == row,
            "Public metadata role differs",
        )
    _require(
        refs["requirement_source"]["path"] not in bindings,
        "Workspace backlog payload must remain identity-only",
    )
    history = witness["original_saved_failure_authority"]
    old = history["original_references"]
    old_plan = metadata(old["plan.json"])
    old_common = metadata(old["terminal.json"])
    old_outer = metadata(old["adna-domain-terminal.json"])
    _require(
        type(old_common["actual_exit"]) is int
        and old_common["actual_exit"] == 1
        and type(old_outer["actual_exit"]) is int
        and old_outer["actual_exit"] == 1
        and old_common["plan_sha256"]
        == old_outer["plan_sha256"]
        == old["plan.json"]["sha256"],
        "Original failed native epoch lost",
    )
    _require(
        [r["actual_exit"] for r in old_common["stages"]] == [0, 1]
        and len(old_plan["stages"]) == 2,
        "Original0/1 stages lost",
    )
    validate_capsule(repository, Path(CAPTURE).parent.as_posix(), packet["members"])
    exact_tree(aux_root, set(authority["members"]) | {"authority-index.json"})
    return {
        "schema_version": "adna-current-export-source-evidence.v1",
        "capture": {"path": CAPTURE, "sha256": CAPTURE_SHA256},
        "witness": {"path": WITNESS, "sha256": WITNESS_SHA256},
        "authority": {"path": AUTHORITY, "sha256": AUTHORITY_SHA256},
        "native_source": native,
        "observed_population_no_pollen_leakage": True,
        "whole_ADNA_001_closed": False,
        "publisher_entries_selected": 0,
        "publisher_ownership_changed": False,
        "historical_v1_products_or_lifecycle_relabelled": False,
        "scientific_chronology_biology_rights_genotype_ecology_PROP_004_or_LRA_admitted": False,
    }


def validated_aadr_current_export_evidence(
    repository: Path, owners: list[dict[str, Any]]
) -> JsonObject | None:
    """Validate portable retained evidence, without admitting a publisher output."""
    try:
        return _validated_aadr_current_export_evidence(repository, owners)
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise ReportRebuildError(
            "AADR current metadata evidence is malformed"
        ) from error
