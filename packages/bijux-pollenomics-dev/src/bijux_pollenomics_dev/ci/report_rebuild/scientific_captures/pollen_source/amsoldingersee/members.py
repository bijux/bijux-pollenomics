"""Validate exact content-addressed members and every ordered input omission role."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from ....contracts import ReportRebuildError
from ....retained_source import validate_capsule
from .execution import exact, require

PUBLIC = {"public_source", "public_control", "public_result"}
OMITTED = {"private_identity_only", "runtime_identity_only", "bytecode_identity_only"}


def load(path: Path) -> Any:
    """Decode retained JSON with duplicate and nonfinite refusals."""

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        require(
            len(rows) == len({key for key, _ in rows}), "Duplicate capsule JSON key"
        )
        return dict(rows)

    value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
    json.dumps(value, allow_nan=False)
    return value


def content(path: Path) -> dict[str, Any]:
    """Hash an ordinary retained member without interpreting its contents."""
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"sha256": digest, "bytes": path.stat().st_size}


def namespace(root: Path, members: dict[str, Any]) -> None:
    """Validate confined logical members against exact Git and physical custody."""
    prefix = "data/source-custody/landclim/amsoldingersee"
    require(root.as_posix().endswith("/" + prefix), "Exact capsule prefix required")
    repository = root.parents[len(PurePosixPath(prefix).parts) - 1]
    require(repository / prefix == root, "Exact repository capsule required")
    for name, expected in members.items():
        relative = PurePosixPath(name)
        require(
            relative.as_posix() == name
            and not relative.is_absolute()
            and ".." not in relative.parts
            and "\\" not in name
            and len(relative.parts) == 2
            and relative.parts[0] == "members",
            "Unsafe content member name",
        )
        require(
            name == "members/" + expected["sha256"]
            and type(expected["bytes"]) is int
            and expected["bytes"] >= 0,
            "Content member identity/name differs",
        )
    try:
        validate_capsule(repository, prefix, members)
    except ReportRebuildError as error:
        raise ValueError(str(error)) from error


def catalogs(
    root: Path, capture: dict[str, Any], jobs: dict[str, dict[str, Any]]
) -> None:
    """Rejoin each original source identity to its declared retention role."""
    members = capture["members"]
    retained = set()
    counts = {}
    for label, documents in jobs.items():
        rows = documents["plan.json"]["input_pins"]
        roles = capture["input_roles"][label]
        require(len(rows) == len(roles), "Ordered source catalog/role length differs")
        require(
            len({row["path"] for row in rows}) == len(rows),
            "Duplicate original input identity",
        )
        counter: Counter[str] = Counter()
        for row, role in zip(rows, roles, strict=True):
            kind = role["role"]
            require(kind in PUBLIC | OMITTED, "Unknown input role")
            counter[kind] += 1
            name = role["member"]
            if kind in PUBLIC:
                require(
                    name in members
                    and exact(
                        members[name], {key: row[key] for key in ("sha256", "bytes")}
                    ),
                    "Retained input original hash/size changed",
                )
                retained.add(name)
            else:
                require(name is None, "Omitted input payload was published")
            source = Path(row["path"])
            is_source = any(
                "/packages/" + package + "/src/" in str(source)
                for package in (
                    "bijux-pollenomics",
                    "bijux-pollenomics-dev",
                    "bijux-pollenomics-lra",
                    "pollenomics",
                )
            )
            if is_source:
                require(
                    kind
                    == (
                        "bytecode_identity_only"
                        if source.suffix in {".pyc", ".pyo"}
                        else "public_source"
                    ),
                    "Original first-party source/cache role changed",
                )
            repository = Path(documents["plan.json"]["repository"])
            private = source.is_relative_to(
                "/Users/bijan/bijux/-bijux-pollenomics-data"
            )
            if private:
                require(kind == "private_identity_only", "Private raw input copied")
            elif not source.is_relative_to(repository):
                require(
                    kind == "runtime_identity_only", "External runtime payload copied"
                )
            elif not is_source:
                control_roots = [
                    repository / "artifacts/science" / name
                    for name in (
                        "amsoldingersee-source-refusal-custody",
                        "amsoldingersee-saved-observation-custody",
                    )
                ]
                result_roots = [
                    repository / "artifacts/science" / name
                    for name in (
                        "current-amsoldingersee-source-refusal-replay",
                        "current-amsoldingersee-saved-source-observation",
                    )
                ]
                public_names = {
                    repository
                    / "data/landclim/review/amsoldingersee-source-inputs.json",
                    repository / "configs/ci/report-ownership.json",
                    repository
                    / "docs/report/publication-replay/landclim-amsoldingersee-source-review/report.json",
                }
                expected = (
                    "public_control"
                    if source in public_names
                    or any(source.is_relative_to(root) for root in control_roots)
                    else "public_result"
                    if any(source.is_relative_to(root) for root in result_roots)
                    else None
                )
                require(
                    expected is not None and kind == expected,
                    "Repository input role changed",
                )
        counts[label] = dict(counter)
    require(exact(counts, capture["role_counts"]), "Input role count claim differs")
    known_inputs = {
        row["path"] for doc in jobs.values() for row in doc["plan.json"]["input_pins"]
    }
    expected_extra: dict[str, dict[str, Any]] = {}
    for label, documents in jobs.items():
        output = Path(documents["plan.json"]["output"])
        rows = list(documents["terminal.json"]["products"])
        for name, member in capture["jobs"][label].items():
            rows.append({"path": str(output / name), **members[member]})
        for row in rows:
            require(
                Path(row["path"]).is_relative_to(output),
                "Native result catalog escaped original output",
            )
            if row["path"] not in known_inputs:
                require(
                    row["path"] not in expected_extra
                    or exact(expected_extra[row["path"]], row),
                    "Conflicting original result identity",
                )
                expected_extra[row["path"]] = row
    extra = set()
    seen = set()
    for record in capture["public_results"]:
        row = record["original"]
        name = record["member"]
        require(
            row["path"] not in seen and exact(expected_extra.get(row["path"]), row),
            "Unbound or duplicate native result identity",
        )
        seen.add(row["path"])
        require(
            name in members
            and exact(members[name], {key: row[key] for key in ("sha256", "bytes")}),
            "Native result member changed",
        )
        extra.add(name)
    require(seen == set(expected_extra), "Native result catalog omitted")
    for references in capture["jobs"].values():
        extra.update(references.values())
    require(retained | extra == set(members), "Unlisted or unbound public payload")
    require(
        capture["private_runtime_bytecode_payloads_copied"] is False
        and capture["bytecode_source_equivalence_claimed"] is False,
        "Payload omission scope changed",
    )
