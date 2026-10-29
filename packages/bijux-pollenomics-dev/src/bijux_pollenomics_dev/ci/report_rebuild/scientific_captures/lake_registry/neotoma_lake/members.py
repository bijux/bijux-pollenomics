"""Confine public source/metadata capsule members and preserve all omitted input identities."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any

from ....retained_source import validate_capsule
from .execution import exact, require

ADDITIONAL_DETACHED_SOURCE_MEMBERS = frozenset(
    [
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/check_controls.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/check_tools.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/common_runner.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/contracts.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/controller-budget-delta.diff",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/execute_projection.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/execute_reader.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/lake_review.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/observe.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/prepare.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/projection_review.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/run.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/runtime_contracts.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/source_admission.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/source_entry.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/source_inputs.py",
        "source/artifacts/science/neotoma-lakeparameter-runtime-budget-custody/source_runtime.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/check_contracts.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/check_tools.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/contracts.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/install.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/observe.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/pip_entry.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/prepare.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/run.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/run_account_qualification.py",
        "source/artifacts/science/source-runtime-isolated-install-custody/transport.py",
        "source/artifacts/science/source-runtime-native-observation-custody/check_contracts.py",
        "source/artifacts/science/source-runtime-native-observation-custody/check_tools.py",
        "source/artifacts/science/source-runtime-native-observation-custody/contracts.py",
        "source/artifacts/science/source-runtime-native-observation-custody/observe.py",
        "source/artifacts/science/source-runtime-native-observation-custody/prepare.py",
        "source/artifacts/science/source-runtime-native-observation-custody/run.py",
        "source/artifacts/science/source-runtime-native-observation-custody/run_account_qualification.py",
    ]
)


def validate_members(repository: Path, root: Path, members: dict[str, Any]) -> None:
    """Keep the exact original logical source set with closed physical/Git custody."""
    for name in members:
        relative = PurePosixPath(name)
        require(
            not relative.is_absolute()
            and ".." not in relative.parts
            and "\\" not in name
            and relative.as_posix() == name,
            "Member path escapes capsule",
        )
        require(
            relative.suffix != ".pyc" and "__pycache__" not in relative.parts,
            "Bytecode remains identity-only",
        )
    prefix = root.relative_to(repository).as_posix()
    detached = validate_capsule(
        repository,
        prefix,
        members,
    )
    exact(
        sorted(detached),
        sorted(
            name
            for name in members
            if name in ADDITIONAL_DETACHED_SOURCE_MEMBERS
            or name.startswith("source/packages/")
            or name
            in {
                "source/configs/ci/report-ownership.json",
                "source/docs/report/source-relations/neotoma/lakeparameters/verify.py",
            }
        ),
    )


def validate_catalog(
    catalog: list[dict[str, Any]],
    original: list[dict[str, Any]],
    members: dict[str, Any],
    *,
    private_root: str,
    repository: str,
    public_paths: set[str],
    runtime_paths: set[str],
    raw_relational_paths: set[str] | None = None,
) -> dict[str, int]:
    """Classify original rows without treating omitted source/runtime bytes as newly observed."""
    exact(len(catalog), len(original))
    require(
        len({row["path"] for row in original}) == len(original),
        "Duplicate original identity",
    )
    counts: dict[str, int] = {}
    for index, (row, pin) in enumerate(zip(catalog, original, strict=True)):
        exact(row["original_index"], index)
        exact({key: row[key] for key in ("path", "sha256", "bytes")}, pin)
        role = row["retention_role"]
        name = row["retained_member"]
        path = Path(pin["path"])
        if role in {
            "public_first_party_source_or_resource",
            "public_control_or_declared_metadata",
        }:
            require(
                pin["path"] in public_paths
                and not path.is_relative_to(Path(private_root)),
                "Unreviewed retained public source",
            )
            require(
                type(name) is str and name in members,
                "Retained input lacks capsule member",
            )
            exact(members[name], {key: pin[key] for key in ("sha256", "bytes")})
        elif role == "private_source_identity_only":
            exact(name, None)
            require(
                path.is_relative_to(Path(private_root)),
                "Undeclared omitted private source",
            )
        elif role == "bytecode_identity_only":
            exact(name, None)
            require(
                path.is_relative_to(Path(repository) / "packages")
                and (path.suffix == ".pyc" or "__pycache__" in path.parts),
                "Omitted nonbytecode source",
            )
        elif role == "raw_relational_input_identity_only":
            exact(name, None)
            require(
                raw_relational_paths is not None
                and pin["path"] in raw_relational_paths
                and path.is_relative_to(Path(repository) / "data/neotoma"),
                "Unreviewed raw/relational omission",
            )
        elif role == "operational_tool_identity_only":
            exact(name, None)
            exact(
                pin,
                {
                    "path": "/Library/Developer/CommandLineTools/usr/bin/git",
                    "sha256": "a73bf622a2e470d5d57a4b1d5aef1e8680e67278018d4858a2f93825b7d595c7",
                    "bytes": 3837392,
                },
            )
        else:
            exact(role, "runtime_dependency_identity_only")
            exact(name, None)
            require(pin["path"] in runtime_paths, "Unqualified omitted runtime input")
        counts[role] = counts.get(role, 0) + 1
    return counts
