"""Derive a complete public packet and explicit original identity-only partitions."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any

from .contracts import GIT, require, strict_equal
from .execution import REF_NAMES, qualify_saved


def normalized_row(row: dict[str, Any]) -> dict[str, Any]:
    """Validate one exact retained-source identity row."""
    require(
        set(row) == {"path", "sha256", "bytes"}
        and type(row["path"]) is str
        and Path(row["path"]).is_absolute()
        and ".." not in Path(row["path"]).parts
        and type(row["sha256"]) is str
        and len(row["sha256"]) == 64
        and all(c in "0123456789abcdef" for c in row["sha256"])
        and type(row["bytes"]) is int
        and row["bytes"] >= 0,
        "Exact original identity row required",
    )
    return deepcopy(row)


def public_members(
    authority: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Resolve the public members explicitly declared by source authority."""
    documents = authority["documents"]
    identities = authority["identities"]
    qualify_saved(documents, identities, authority["original_references"])
    country = documents["country-plan"]
    saved = documents["saved-plan"]
    ledger = documents["owned-source-ledger"]
    owned = Path(country["owned_repository"])
    original_output = Path(country["output"])
    original_products = original_output / "producer/candidate"
    roles: dict[str, dict[str, Any]] = {}

    def add(name: str, row: dict[str, Any], role: str) -> None:
        logical = PurePosixPath(name)
        require(
            type(name) is str
            and logical.as_posix() == name
            and len(logical.parts) >= 2
            and not logical.is_absolute()
            and ".." not in logical.parts
            and "\\" not in name,
            "Closed public logical name required",
        )
        identity = normalized_row(row)
        value = {"logical_name": name, "source_identity": identity, "role": role}
        require(
            name not in roles or strict_equal(roles[name], value),
            "Conflicting public logical role",
        )
        roles[name] = value

    source_names = set()
    for row in ledger["copied_sources"]:
        path = Path(row["path"])
        require(path.is_relative_to(owned), "Owned public source escaped")
        relative = path.relative_to(owned).as_posix()
        require(
            relative.startswith("packages/")
            or relative in {"pyproject.toml", "configs/ci/report-ownership.json"},
            "Unknown owned source/root marker",
        )
        require(
            "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"},
            "Opaque cache cannot become source payload",
        )
        source_names.add(row["path"])
        add("source/" + relative, row, "complete-original-owned-public-source-resource")
    comparands = owned / "docs/report/countries/sweden"
    private_names = set()
    for row in ledger["copied_data_inputs"]:
        path = Path(row["path"])
        require(path.is_relative_to(owned), "Owned input row escaped")
        if path.is_relative_to(comparands):
            add(
                "comparands/" + path.relative_to(comparands).as_posix(),
                row,
                "original-published-country-comparand",
            )
        else:
            private_names.add(row["path"])
    for row in documents["saved-review"]["actual_products"]:
        path = Path(row["path"])
        require(
            path.is_relative_to(original_products),
            "Saved product must come from original country root",
        )
        add(
            "products/" + path.relative_to(original_products).as_posix(),
            row,
            "actual-original-normally-returned-country-product",
        )
    for name in REF_NAMES:
        add(
            "references/" + name + ".json",
            identities[name],
            "complete-native-reference-metadata",
        )
    for prefix in ("country", "saved"):
        source_root = Path(identities[prefix + "-controller-manifest"]["path"]).parent
        for row in documents[prefix + "-controller-manifest"]["files"]:
            path = Path(row["path"])
            require(
                path.is_relative_to(source_root), "Executed controller source escaped"
            )
            add(
                "controllers/"
                + prefix
                + "/"
                + path.relative_to(source_root).as_posix(),
                row,
                "actual-executed-reviewed-controller-source",
            )
        output = Path(documents[prefix + "-plan"]["output"])
        for stage in documents[prefix + "-inner"]["stages"]:
            for key in ("stdout", "stderr"):
                row = stage[key]
                require(
                    Path(row["path"]).parent == output, "Native stage stream escaped"
                )
                add(
                    "streams/" + prefix + "/" + Path(row["path"]).name,
                    row,
                    "original-complete-stage-stream",
                )
        for key, filename in (("stdout", "launch.stdout"), ("stderr", "launch.stderr")):
            row = documents[prefix + "-outer"][key]
            require(
                Path(row["path"]) == output / filename, "Late outer stream role differs"
            )
            add(
                "streams/" + prefix + "/" + filename,
                row,
                "outer-authenticated-complete-late-PIPE-stream",
            )
    early = documents["pre-country-history"]
    early_root = Path(early["original_complete_namespace"]["root"])
    early_names = {
        "plan.json",
        "sweden-country-semantic-terminal.json",
        "sweden-country-semantic-launch-terminal.json",
        "output-products.json",
        "stage-progress.json",
        "original-source-ledger.json",
        "maintained-full-Sweden-country-consumer.stdout",
        "maintained-full-Sweden-country-consumer.stderr",
        "launch.stdout",
        "launch.stderr",
    }
    retained_early = set()
    for row in early["original_outputs"]:
        path = Path(row["path"])
        if path.parent == early_root and path.name in early_names:
            add(
                "history/pre-country/" + path.name,
                row,
                "original-pre-country-failure-metadata-or-stream",
            )
            retained_early.add(path.name)
    require(retained_early == early_names, "Original pre-country history incomplete")
    early_controller = "sweden-country-semantic-custody"
    early_source = []
    for row in country["input_pins"]:
        path = Path(row["path"])
        if early_controller in path.parts:
            index = path.parts.index(early_controller)
            relative = Path(*path.parts[index + 1 :]).as_posix()
            add(
                "controllers/pre-country/" + relative,
                row,
                "original-pre-country-reviewed-source",
            )
            early_source.append(row["path"])
    require(early_source, "Original pre-country controller source absent")
    public_by_path: dict[str, dict[str, Any]] = {}
    for item in roles.values():
        row = item["source_identity"]
        require(
            row["path"] not in public_by_path or public_by_path[row["path"]] == row,
            "Conflicting original public source identity",
        )
        public_by_path[row["path"]] = row
    require(
        not set(public_by_path).intersection(private_names),
        "Private/normalized body entered public packet",
    )
    runtime_names = {row["path"] for row in documents["runtime-plan"]["input_pins"]}
    runtime_names.update(
        row["path"]
        for key, row in country["qualified_source_runtime"].items()
        if isinstance(row, dict) and set(row) == {"path", "sha256", "bytes"}
    )
    opaque_names = {row["path"] for row in ledger["omitted_unselected_cache_bytecode"]}
    generated_names = {
        row["path"] for row in ledger["omitted_configured_generated_metadata"]
    }
    omitted = {}
    for prefix, plan in (("country", country), ("saved", saved)):
        rows = []
        require(
            len({row["path"] for row in plan["input_pins"]}) == len(plan["input_pins"]),
            "Duplicate original ordered input",
        )
        for original in plan["input_pins"]:
            row = normalized_row(original)
            path = Path(row["path"])
            if row["path"] in public_by_path:
                require(
                    public_by_path[row["path"]] == row, "Public ordered input mismatch"
                )
                kind = "retained_public_source_control_or_result"
            elif row["path"] in private_names:
                kind = "private_or_normalized_owned_input_identity_only"
            elif row["path"] in opaque_names or path.suffix in {".pyc", ".pyo"}:
                kind = "original_opaque_bytecode_identity_only"
            elif row["path"] in generated_names:
                kind = "original_configured_generated_module_identity_only"
            elif row["path"] in runtime_names:
                kind = "qualified_runtime_input_identity_only"
            elif path == GIT:
                kind = "original_tool_identity_only"
            elif any(
                path.is_relative_to(Path(documents[key]["output"]) / "cache")
                for key in ("country-plan", "saved-plan")
            ) or path.is_relative_to(early_root / "cache"):
                kind = "original_runtime_generated_cache_identity_only"
            else:
                # Every permitted remaining input is already a row of an immutable
                # original native catalogue; omission never asserts runtime equivalence.
                require(
                    path.is_relative_to(early_root)
                    or path.is_relative_to(original_output)
                    or path.is_relative_to(Path(saved["output"])),
                    "Unknown original native input role",
                )
                kind = "original_native_history_identity_only"
            rows.append({"original": row, "role": kind})
        omitted[prefix] = rows
    return [roles[name] for name in sorted(roles)], {
        "ordered_original_input_roles": omitted,
        "original_first_party_source_identities": deepcopy(ledger["original_sources"]),
        "original_private_input_identities": deepcopy(ledger["original_data_inputs"]),
        "owned_private_input_identities": [
            normalized_row(row)
            for row in ledger["copied_data_inputs"]
            if row["path"] in private_names
        ],
        "original_omitted_bytecode_identities": deepcopy(
            ledger["omitted_unselected_cache_bytecode"]
        ),
        "original_omitted_generated_metadata_identities": deepcopy(
            ledger["omitted_configured_generated_metadata"]
        ),
        "private_runtime_bytecode_bodies_published": False,
        "cache_source_equivalence_claimed": False,
        "new_acquisition_or_rights_or_LRA_claimed": False,
    }
