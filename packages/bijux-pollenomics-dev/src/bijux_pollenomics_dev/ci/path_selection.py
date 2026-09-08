"""Select mandatory verification gates from repository-relative changed paths."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

REQUIRED_SURFACE_IDS = frozenset(
    {
        "raw-data-and-receipts",
        "normalized-derived-and-review-data",
        "governed-data",
        "source-adapters-and-normalizers",
        "temporal-and-spatial-core",
        "taxon-group-role-classification",
        "scientific-scenarios-and-configuration",
        "country-boundaries-and-scope",
        "map-payload-template-and-provider",
        "evidence-contracts-and-manifests",
        "documentation-counts-and-claims",
        "ci-change-impact-contract",
    }
)
AVAILABILITY_VALUES = frozenset({"available", "unavailable"})


class ContractError(ValueError):
    """Raised when the change-impact contract is incomplete or malformed."""


@dataclass(frozen=True)
class Gate:
    """One verification gate and its current executable posture."""

    gate_id: str
    availability: str
    target: str | None
    reason: str | None


@dataclass(frozen=True)
class Surface:
    """A repository surface and the gates required when it changes."""

    surface_id: str
    paths: tuple[str, ...]
    gates: tuple[str, ...]


@dataclass(frozen=True)
class ChangeImpactContract:
    """Validated change-impact selection policy."""

    schema_version: str
    digest: str
    gate_order: tuple[str, ...]
    gates: dict[str, Gate]
    surfaces: tuple[Surface, ...]

    @property
    def available_gate_ids(self) -> tuple[str, ...]:
        """Return all locally executable gates in canonical order."""
        return tuple(
            gate_id
            for gate_id in self.gate_order
            if self.gates[gate_id].availability == "available"
        )


@dataclass(frozen=True)
class ChangeImpact:
    """Deterministic selection result for one changed-path set."""

    contract_digest: str
    changed_paths: tuple[str, ...]
    invalid_paths: tuple[str, ...]
    unknown_paths: tuple[str, ...]
    matched_surfaces: tuple[str, ...]
    selected_gates: tuple[str, ...]
    available_gates: tuple[str, ...]
    unavailable_gates: tuple[str, ...]
    unavailable_reasons: dict[str, str]
    fail_closed: bool

    def as_dict(self) -> dict[str, object]:
        """Return the stable machine-readable result."""
        return {
            "schema_version": "scientific-change-impact-result.v1",
            "contract_sha256": self.contract_digest,
            "changed_paths": list(self.changed_paths),
            "invalid_paths": list(self.invalid_paths),
            "unknown_paths": list(self.unknown_paths),
            "matched_surfaces": list(self.matched_surfaces),
            "selected_gates": list(self.selected_gates),
            "available_gates": list(self.available_gates),
            "unavailable_gates": list(self.unavailable_gates),
            "unavailable_reasons": self.unavailable_reasons,
            "fail_closed": self.fail_closed,
        }


def _required_mapping(value: object, *, field: str) -> dict[str, Any]:
    """Return a contract object or reject the named field."""
    if not isinstance(value, dict):
        raise ContractError(f"{field} must be an object")
    return value


def _required_string(value: object, *, field: str) -> str:
    """Return a non-empty contract string or reject the named field."""
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} must be a non-empty string")
    return value


def _required_string_list(value: object, *, field: str) -> tuple[str, ...]:
    """Return a unique non-empty string tuple from the named field."""
    if not isinstance(value, list) or not value:
        raise ContractError(f"{field} must be a non-empty array")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ContractError(f"{field} entries must be non-empty strings")
    entries = tuple(value)
    if len(set(entries)) != len(entries):
        raise ContractError(f"{field} entries must be unique")
    return entries


def _validate_pattern(pattern: str) -> None:
    """Reject path patterns that can escape repository-relative matching."""
    if (
        pattern.startswith("/")
        or "\\" in pattern
        or "\x00" in pattern
        or any(part in {"", ".", ".."} for part in pattern.split("/"))
    ):
        raise ContractError(f"invalid repository-relative path pattern: {pattern!r}")


def _parse_gate(gate_id: str, raw: object) -> Gate:
    """Parse one gate while enforcing its availability contract."""
    document = _required_mapping(raw, field=f"gates.{gate_id}")
    availability = _required_string(
        document.get("availability"), field=f"gates.{gate_id}.availability"
    )
    if availability not in AVAILABILITY_VALUES:
        raise ContractError(f"gates.{gate_id}.availability is unsupported")
    target = document.get("target")
    reason = document.get("reason")
    if availability == "available":
        target = _required_string(target, field=f"gates.{gate_id}.target")
        if reason is not None:
            raise ContractError(f"available gate {gate_id} must not have a reason")
    else:
        reason = _required_string(reason, field=f"gates.{gate_id}.reason")
        if target is not None:
            raise ContractError(f"unavailable gate {gate_id} must not have a target")
    return Gate(gate_id, availability, target, reason)


def _parse_surface(raw: object, *, gate_ids: frozenset[str]) -> Surface:
    """Parse one surface and require references to declared gates."""
    document = _required_mapping(raw, field="surfaces entry")
    surface_id = _required_string(document.get("id"), field="surfaces.id")
    paths = _required_string_list(
        document.get("paths"), field=f"surfaces.{surface_id}.paths"
    )
    gates = _required_string_list(
        document.get("gates"), field=f"surfaces.{surface_id}.gates"
    )
    unknown_gates = set(gates) - gate_ids
    if unknown_gates:
        raise ContractError(
            f"surface {surface_id} refers to unknown gates: {sorted(unknown_gates)}"
        )
    for pattern in paths:
        _validate_pattern(pattern)
    return Surface(surface_id, paths, gates)


def load_contract(path: Path) -> ChangeImpactContract:
    """Load and fully validate the repository change-impact contract."""
    payload = path.read_bytes()
    try:
        document = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ContractError(f"invalid JSON in {path}: {error}") from error
    root = _required_mapping(document, field="contract")
    schema_version = _required_string(
        root.get("schema_version"), field="schema_version"
    )
    if schema_version != "scientific-change-impact.v1":
        raise ContractError(f"unsupported schema_version: {schema_version}")
    if root.get("unknown_path_policy") != "all_declared_gates":
        raise ContractError("unknown_path_policy must be all_declared_gates")

    gate_order = _required_string_list(root.get("gate_order"), field="gate_order")
    raw_gates = _required_mapping(root.get("gates"), field="gates")
    if set(gate_order) != set(raw_gates):
        raise ContractError("gate_order must name every declared gate exactly once")
    gates = {
        gate_id: _parse_gate(gate_id, raw_gates[gate_id]) for gate_id in gate_order
    }

    raw_surfaces = root.get("surfaces")
    if not isinstance(raw_surfaces, list) or not raw_surfaces:
        raise ContractError("surfaces must be a non-empty array")
    gate_ids = frozenset(gates)
    surfaces = tuple(
        _parse_surface(raw_surface, gate_ids=gate_ids) for raw_surface in raw_surfaces
    )
    surface_ids = tuple(surface.surface_id for surface in surfaces)
    if len(set(surface_ids)) != len(surface_ids):
        raise ContractError("surface ids must be unique")
    missing_surfaces = REQUIRED_SURFACE_IDS - set(surface_ids)
    if missing_surfaces:
        raise ContractError(
            f"required repository surfaces are missing: {sorted(missing_surfaces)}"
        )
    return ChangeImpactContract(
        schema_version=schema_version,
        digest=hashlib.sha256(payload).hexdigest(),
        gate_order=gate_order,
        gates=gates,
        surfaces=surfaces,
    )


def _glob_regex(pattern: str) -> re.Pattern[str]:
    """Compile the contract's small slash-aware *, **, and ? glob language."""
    fragments = ["^"]
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if character == "*" and pattern[index : index + 2] == "**":
            index += 2
            if index < len(pattern) and pattern[index] == "/":
                fragments.append("(?:[^/]+/)*")
                index += 1
            else:
                fragments.append(".*")
            continue
        if character == "*":
            fragments.append("[^/]*")
        elif character == "?":
            fragments.append("[^/]")
        else:
            fragments.append(re.escape(character))
        index += 1
    fragments.append("$")
    return re.compile("".join(fragments))


def _normalize_path(raw_path: str) -> str | None:
    """Return a canonical repository-relative path or ``None`` if unsafe."""
    if not raw_path or raw_path != raw_path.strip():
        return None
    if "\\" in raw_path or "\x00" in raw_path or "//" in raw_path:
        return None
    candidate = PurePosixPath(raw_path)
    if candidate.is_absolute() or any(
        part in {"", ".", ".."} for part in candidate.parts
    ):
        return None
    normalized = candidate.as_posix()
    return normalized if normalized == raw_path else None


def _ordered_subset(order: tuple[str, ...], selected: set[str]) -> tuple[str, ...]:
    """Project selected identifiers through their canonical order."""
    return tuple(item for item in order if item in selected)


def select_changed_paths(
    contract: ChangeImpactContract,
    changed_paths: list[str] | tuple[str, ...],
    *,
    select_all: bool = False,
) -> ChangeImpact:
    """Select every mandatory gate, failing closed for unclassified input."""
    normalized: set[str] = set()
    invalid: set[str] = set()
    for raw_path in changed_paths:
        candidate = _normalize_path(raw_path)
        if candidate is None:
            invalid.add(raw_path)
        else:
            normalized.add(candidate)

    matched_surface_ids: set[str] = set()
    selected_gate_ids: set[str] = set()
    unknown_paths: set[str] = set()
    compiled = {
        surface.surface_id: tuple(_glob_regex(pattern) for pattern in surface.paths)
        for surface in contract.surfaces
    }
    paths_to_match = tuple(sorted(normalized))
    if select_all:
        paths_to_match = ()
        for surface in contract.surfaces:
            matched_surface_ids.add(surface.surface_id)
            selected_gate_ids.update(surface.gates)
    else:
        for changed_path in paths_to_match:
            path_matched = False
            for surface in contract.surfaces:
                if any(
                    pattern.fullmatch(changed_path)
                    for pattern in compiled[surface.surface_id]
                ):
                    path_matched = True
                    matched_surface_ids.add(surface.surface_id)
                    selected_gate_ids.update(surface.gates)
            if not path_matched:
                unknown_paths.add(changed_path)

    fail_closed = bool(invalid or unknown_paths or (not normalized and not select_all))
    if fail_closed:
        selected_gate_ids.update(contract.gate_order)

    selected = _ordered_subset(contract.gate_order, selected_gate_ids)
    available = tuple(
        gate_id
        for gate_id in selected
        if contract.gates[gate_id].availability == "available"
    )
    unavailable = tuple(
        gate_id
        for gate_id in selected
        if contract.gates[gate_id].availability == "unavailable"
    )
    return ChangeImpact(
        contract_digest=contract.digest,
        changed_paths=tuple(sorted(normalized)),
        invalid_paths=tuple(sorted(invalid)),
        unknown_paths=tuple(sorted(unknown_paths)),
        matched_surfaces=tuple(
            surface.surface_id
            for surface in contract.surfaces
            if surface.surface_id in matched_surface_ids
        ),
        selected_gates=selected,
        available_gates=available,
        unavailable_gates=unavailable,
        unavailable_reasons={
            gate_id: contract.gates[gate_id].reason or "unavailable"
            for gate_id in unavailable
        },
        fail_closed=fail_closed,
    )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    """Write stable indented JSON, creating its parent directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_github_outputs(path: Path, impact: ChangeImpact) -> None:
    """Append compact gate selections to a GitHub Actions output file."""
    outputs = {
        "selected_gates": list(impact.selected_gates),
        "available_gates": list(impact.available_gates),
        "unavailable_gates": list(impact.unavailable_gates),
    }
    with path.open("a", encoding="utf-8") as handle:
        for name, value in outputs.items():
            handle.write(f"{name}={json.dumps(value, separators=(',', ':'))}\n")
        handle.write(f"has_available={'true' if impact.available_gates else 'false'}\n")
        handle.write(
            f"has_unavailable={'true' if impact.unavailable_gates else 'false'}\n"
        )


def _parser() -> argparse.ArgumentParser:
    """Build the command-line parser for change-impact selection."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--changed-path", action="append", default=[])
    parser.add_argument("--changed-paths-file", type=Path)
    parser.add_argument("--all", action="store_true", dest="select_all")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the change-impact selector CLI."""
    args = _parser().parse_args(argv)
    changed_paths = list(args.changed_path)
    if args.changed_paths_file is not None:
        changed_paths.extend(
            args.changed_paths_file.read_text(encoding="utf-8").splitlines()
        )
    contract = load_contract(args.contract)
    impact = select_changed_paths(
        contract, changed_paths, select_all=bool(args.select_all)
    )
    payload = impact.as_dict()
    _write_json(args.output, payload)
    if args.github_output is not None:
        _write_github_outputs(args.github_output, impact)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
