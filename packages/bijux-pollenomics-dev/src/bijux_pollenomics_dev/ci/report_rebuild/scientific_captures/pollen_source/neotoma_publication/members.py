"""Validate a closed public capsule and complete ordered, explicitly omitted input identities."""

from __future__ import annotations

from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from ....retained_source import validate_capsule
from .execution import exact, require

ADDITIONAL_DETACHED_SOURCE_MEMBERS = frozenset(
    [
        "observer-inputs/artifacts/science/neotoma-publication-execution-source-retention/retain_source.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/check_contracts.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/check_observation.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/common_runner.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/contracts.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/execute_source.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/metadata.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/observation_custody.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/observe.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/preflight/qualify.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/prepare.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/run.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/runtime_contracts.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/runtime_guarded_runner.py",
        "observer-inputs/artifacts/science/neotoma-publication-observed-source-custody/source_runtime.py",
        "source/artifacts/science/neotoma-publication-source-custody/check_contracts.py",
        "source/artifacts/science/neotoma-publication-source-custody/common_runner.py",
        "source/artifacts/science/neotoma-publication-source-custody/contracts.py",
        "source/artifacts/science/neotoma-publication-source-custody/execute_source.py",
        "source/artifacts/science/neotoma-publication-source-custody/metadata.py",
        "source/artifacts/science/neotoma-publication-source-custody/observe.py",
        "source/artifacts/science/neotoma-publication-source-custody/preflight/api_and_input_contract.py",
        "source/artifacts/science/neotoma-publication-source-custody/preflight/author_source.py",
        "source/artifacts/science/neotoma-publication-source-custody/preflight/complete_source.py",
        "source/artifacts/science/neotoma-publication-source-custody/preflight/freeze_source.py",
        "source/artifacts/science/neotoma-publication-source-custody/preflight/install_entry_sources.py",
        "source/artifacts/science/neotoma-publication-source-custody/preflight/qualify_source.py",
        "source/artifacts/science/neotoma-publication-source-custody/preflight/source_style.py",
        "source/artifacts/science/neotoma-publication-source-custody/prepare.py",
        "source/artifacts/science/neotoma-publication-source-custody/run.py",
        "source/artifacts/science/neotoma-publication-source-custody/runtime_contracts.py",
        "source/artifacts/science/neotoma-publication-source-custody/runtime_guarded_runner.py",
        "source/artifacts/science/neotoma-publication-source-custody/source_runtime.py",
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
            or name == "source/configs/ci/report-ownership.json"
        ),
    )


def validate_catalog(
    catalog: list[dict[str, Any]],
    original: list[dict[str, Any]],
    members: dict[str, Any],
    *,
    original_roles: dict[str, dict[str, Any]],
    runtime_paths: set[str],
    repository: str,
    retained_aliases: dict[str, str],
) -> dict[str, int]:
    """No omitted input is silently converted into a fresh source or runtime-equivalence claim."""
    exact(len(catalog), len(original))
    require(
        len({row["path"] for row in original}) == len(original),
        "Duplicate original pin",
    )
    counts: Counter[str] = Counter()
    for index, (row, pin) in enumerate(zip(catalog, original, strict=True)):
        exact(row["original_index"], index)
        exact({key: row[key] for key in ("path", "sha256", "bytes")}, pin)
        role, member = row["retention_role"], row["retained_member"]
        name = pin["path"]
        if role == "retained_original_public_source":
            if name in original_roles:
                exact(original_roles[name]["retained_member"], member)
                require(member is not None, "Original private/runtime payload promoted")
            else:
                require(name in retained_aliases, "Unreviewed original source copy")
                exact(retained_aliases[name], member)
            exact(members[member], {key: pin[key] for key in ("sha256", "bytes")})
        elif role == "retained_observer_control_or_public_metadata":
            path = Path(name)
            require(
                path.is_relative_to(Path(repository) / "artifacts/science")
                or path.is_relative_to(Path(repository) / "packages"),
                "Undeclared retained observer input",
            )
            require(
                type(member) is str and member in members,
                "Missing observer input member",
            )
            exact(members[member], {key: pin[key] for key in ("sha256", "bytes")})
        else:
            exact(member, None)
            require(
                role
                in {
                    "private_source_identity_only",
                    "runtime_dependency_identity_only",
                    "bytecode_identity_only",
                },
                "Unknown omission role",
            )
            if name in original_roles:
                expected = {
                    "omitted_private_capture_payload_identity_only": "private_source_identity_only",
                    "omitted_runtime_or_dependency_identity_only": "runtime_dependency_identity_only",
                    "omitted_first_party_bytecode_identity_only": "bytecode_identity_only",
                }
                require(
                    original_roles[name]["retention_role"] in expected,
                    "Original public input omitted",
                )
                exact(role, expected[original_roles[name]["retention_role"]])
            else:
                exact(role, "runtime_dependency_identity_only")
                require(name in runtime_paths, "Unreviewed omitted runtime input")
        counts[role] += 1
    return dict(sorted(counts.items()))
