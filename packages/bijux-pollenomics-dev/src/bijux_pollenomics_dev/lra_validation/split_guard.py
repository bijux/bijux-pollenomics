"""Build label-free candidate site and spatial-block split manifests.

This is a preparation guard, not a reviewed eligibility or final-test freeze.
The caller must supply the complete alias and derived-product dependency graph.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

_FIELDS = {
    "record_id",
    "site_id",
    "core_id",
    "publication_id",
    "alias_ids",
    "country",
    "spatial_block_id",
    "kind",
    "dependency_ids",
}
_COUNTRIES = {"Sweden", "Denmark", "Norway", "Finland"}
_KINDS = {"pollen", "vegetation", "derived"}
_TARGETS = {"local_pollen_available", "withheld_pollen_prediction"}


class SplitGuardError(ValueError):
    """A reason-coded refusal to construct a leakage-safe candidate split."""

    def __init__(self, reason_code: str) -> None:
        """Initialize the refusal with its stable reason code."""
        super().__init__(reason_code)
        self.reason_code = reason_code


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _ids(value: object) -> bool:
    return isinstance(value, list) and all(_text(item) for item in value)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def build_candidate_split(
    records: list[dict[str, object]],
    *,
    test_record_id: str,
    target: str,
    local_pollen_record_id: str | None = None,
    holdout_spatial_block: bool = False,
) -> dict[str, Any]:
    """Refuse aliases and derived training inputs that expose the test group.

    Records contain identities and dependency IDs only. No outcome, pollen
    count, tree value, parameter, metric or fitted product may be supplied.
    Publication grouping is conservative: every record sharing a publication
    is held out together. A distinct reviewed publication/site relation may
    later justify a narrower versioned contract.
    """
    if target not in _TARGETS:
        raise SplitGuardError("invalid_target")
    if not records:
        raise SplitGuardError("empty_records")
    by_id: dict[str, dict[str, object]] = {}
    for row in records:
        if not isinstance(row, dict) or set(row) != _FIELDS:
            raise SplitGuardError("invalid_record_fields")
        if not all(
            _text(row[field])
            for field in ("record_id", "site_id", "country", "spatial_block_id")
        ):
            raise SplitGuardError("missing_identity")
        if any(
            row[field] is not None and not _text(row[field])
            for field in ("core_id", "publication_id")
        ):
            raise SplitGuardError("invalid_identity")
        if not _ids(row["alias_ids"]) or not _ids(row["dependency_ids"]):
            raise SplitGuardError("invalid_id_list")
        if row["country"] not in _COUNTRIES or row["kind"] not in _KINDS:
            raise SplitGuardError("invalid_country_or_kind")
        record_id = str(row["record_id"])
        if record_id in by_id:
            raise SplitGuardError("duplicate_record_id")
        by_id[record_id] = row
    if test_record_id not in by_id:
        raise SplitGuardError("unknown_test_record")
    if target == "local_pollen_available":
        if by_id[test_record_id]["kind"] != "vegetation":
            raise SplitGuardError("test_record_not_vegetation")
        if local_pollen_record_id not in by_id:
            raise SplitGuardError("missing_local_pollen_record")
        pollen = by_id[local_pollen_record_id]
        if pollen["kind"] != "pollen" or pollen["dependency_ids"]:
            raise SplitGuardError("local_pollen_not_raw")
    elif local_pollen_record_id is not None:
        raise SplitGuardError("withheld_pollen_must_not_be_supplied")
    elif by_id[test_record_id]["kind"] not in {"pollen", "vegetation"}:
        raise SplitGuardError("test_record_not_observation")
    for record_id, row in by_id.items():
        dependencies = row["dependency_ids"]
        assert isinstance(dependencies, list)
        if record_id in dependencies:
            raise SplitGuardError("self_dependency")
        if any(dependency not in by_id for dependency in dependencies):
            raise SplitGuardError("unresolved_dependency")

    parent = {record_id: record_id for record_id in by_id}

    def root(record_id: str) -> str:
        while parent[record_id] != record_id:
            parent[record_id] = parent[parent[record_id]]
            record_id = parent[record_id]
        return record_id

    def union(left: str, right: str) -> None:
        first, second = root(left), root(right)
        parent[max(first, second)] = min(first, second)

    identity_owner: dict[tuple[str, str], str] = {}
    identity_values: dict[str, set[str]] = {}
    alias_owners: dict[str, set[str]] = {}
    for record_id, row in sorted(by_id.items()):
        tokens = [("record_id", record_id), ("site_id", str(row["site_id"]))]
        for field in ("core_id", "publication_id"):
            if row[field] is not None:
                tokens.append((field, str(row[field])))
        for token in tokens:
            owner = identity_owner.setdefault(token, record_id)
            union(record_id, owner)
            identity_values.setdefault(token[1], set()).add(record_id)
        aliases = row["alias_ids"]
        assert isinstance(aliases, list)
        for alias in aliases:
            alias_owners.setdefault(str(alias), set()).add(record_id)
    for alias, owners in sorted(alias_owners.items()):
        targets = identity_values.get(alias, set())
        target_groups = {root(target) for target in targets}
        if len(target_groups) > 1:
            raise SplitGuardError("ambiguous_alias_reference")
        if not targets and len(owners) < 2:
            raise SplitGuardError("unresolved_alias_reference")
        members = sorted(owners | targets)
        for member in members[1:]:
            union(members[0], member)
    groups: dict[str, list[str]] = {}
    for record_id in by_id:
        groups.setdefault(root(record_id), []).append(record_id)
    for members in groups.values():
        if len({by_id[member]["spatial_block_id"] for member in members}) != 1:
            raise SplitGuardError("identity_crosses_spatial_blocks")
    test_root = root(test_record_id)
    if local_pollen_record_id is not None and root(local_pollen_record_id) != test_root:
        raise SplitGuardError("local_pollen_outside_test_group")
    test_block = by_id[test_record_id]["spatial_block_id"]
    test_ids = {
        record_id
        for record_id, row in by_id.items()
        if root(record_id) == test_root
        or (holdout_spatial_block and row["spatial_block_id"] == test_block)
    }
    train_ids = set(by_id) - test_ids
    if not train_ids:
        raise SplitGuardError("no_training_records")
    test_pollen_ids = sorted(
        record_id for record_id in test_ids if by_id[record_id]["kind"] == "pollen"
    )
    test_vegetation_ids = sorted(
        record_id for record_id in test_ids if by_id[record_id]["kind"] == "vegetation"
    )
    if target == "withheld_pollen_prediction" and not test_pollen_ids:
        raise SplitGuardError("missing_test_pollen_record")
    # A derived train product can include an intermediate derived product that
    # used a held-out row. Walk the full declared dependency closure.
    visiting: set[str] = set()
    resolved: dict[str, set[str]] = {}

    def ancestors(record_id: str) -> set[str]:
        if record_id in visiting:
            raise SplitGuardError("cyclic_dependency")
        if record_id in resolved:
            return resolved[record_id]
        visiting.add(record_id)
        dependencies = by_id[record_id]["dependency_ids"]
        assert isinstance(dependencies, list)
        result = set(dependencies)
        for dependency in dependencies:
            result.update(ancestors(str(dependency)))
        visiting.remove(record_id)
        resolved[record_id] = result
        return result

    for record_id in sorted(by_id):
        if ancestors(record_id) & test_ids and record_id in train_ids:
            raise SplitGuardError("contaminated_train_input")

    normalized = [by_id[key] for key in sorted(by_id)]
    group_rows = [
        {
            "group_id": key,
            "record_ids": sorted(members),
            "spatial_block_id": by_id[members[0]]["spatial_block_id"],
        }
        for key, members in sorted(groups.items())
    ]
    return {
        "schema_version": "lra-candidate-split.v1",
        "status": "candidate_unreviewed",
        "target": target,
        "holdout_spatial_block": holdout_spatial_block,
        "input_sha256": hashlib.sha256(_canonical(normalized)).hexdigest(),
        "test_record_id": test_record_id,
        "test_record_ids": sorted(test_ids),
        "test_pollen_record_ids": test_pollen_ids,
        "test_vegetation_record_ids": test_vegetation_ids,
        "train_record_ids": sorted(train_ids),
        "allowed_local_pollen_record_id": local_pollen_record_id,
        "groups": group_rows,
    }


def main(argv: list[str] | None = None) -> int:
    """Publish one candidate manifest from an identity-only JSON plan."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit(
            "usage: python -m bijux_pollenomics_dev.lra_validation.split_guard PLAN.json"
        )
    plan = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or set(plan) != {
        "records",
        "test_record_id",
        "target",
        "local_pollen_record_id",
        "holdout_spatial_block",
        "output_path",
    }:
        raise SplitGuardError("invalid_split_plan")
    if (
        not isinstance(plan["records"], list)
        or not _text(plan["test_record_id"])
        or not _text(plan["target"])
        or (
            plan["local_pollen_record_id"] is not None
            and not _text(plan["local_pollen_record_id"])
        )
        or not isinstance(plan["holdout_spatial_block"], bool)
        or not _text(plan["output_path"])
    ):
        raise SplitGuardError("invalid_split_plan")
    output = Path(plan["output_path"])
    if not output.is_absolute() or not output.parent.is_dir():
        raise SplitGuardError("invalid_output_path")
    manifest = build_candidate_split(
        plan["records"],
        test_record_id=plan["test_record_id"],
        target=plan["target"],
        local_pollen_record_id=plan["local_pollen_record_id"],
        holdout_spatial_block=plan["holdout_spatial_block"],
    )
    content = _canonical(manifest) + b"\n"
    with tempfile.NamedTemporaryFile(
        dir=output.parent, prefix=".candidate-split-", delete=False
    ) as stream:
        temporary = Path(stream.name)
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, output)
    except FileExistsError as exc:
        raise SplitGuardError("output_already_exists") from exc
    finally:
        temporary.unlink(missing_ok=True)
    print(
        json.dumps(
            {"output": str(output), "sha256": hashlib.sha256(content).hexdigest()},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
