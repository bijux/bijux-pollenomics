"""Portable current animal API execution evidence; original data remains identity-only."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any

SCHEMA = "animal-current-export-execution-capture.v1"
PLAN_SHA = "9a9868b6dcdd6df31c94c0184a8623afbe4a360dd82144e44bbe0c162de0b8ef"
SOURCE_SHA = "2e3e7b578f8e823e5edbd4bbfbd493e55545103923aa5bbe5a5bcb748024b91a"
INNER_SHA = "10f9be9e75a77b22c589dc25170b40d2f5cfb38c60d6e0a0c1fba54a472e7509"
OUTER_SHA = "f79e745a567e0d86fe6021f52eafdf5ca9df47d4706dc492c7c93441821df993"
PRODUCER_SHA = "01bb9975bf9a0c80285918c837638db5b3a0040e87b1d45eb85881512858e8d6"
REVIEW_SHA = "af47fe009090ab841b711e389c9a24f4799b480d357a2a6aa414dd642051d31d"
CANDIDATE = "ad591c301bcadb6a3f963caa836a2e38a16d0de4"
SCOPE = {
    "current_animal_metadata_API_and_default_exports_only": True,
    "original162_authorities_and160_owned_data_identity_only": True,
    "raw_private_runtime_or_bytecode_redistributed": False,
    "new_acquisition_or_original_normalization_receipt_recovered": False,
    "genotype_biology_calibration_rights_human_ecology_LRA_admitted": False,
    "whole_ADNA_requirement_adjudicated_by_this_capture": False,
    "native_taxon_block_flags_exported_by_generic_writers": False,
}
CURRENT_FIELDS = [
    "schema_version",
    "species_latin_name",
    "species_common_name",
    "source_family",
    "sample_namespace",
    "genetic_id",
    "master_id",
    "group_id",
    "locality",
    "political_entity",
    "latitude",
    "longitude",
    "publication",
    "year_first_published",
    "full_date",
    "date_mean_bp",
    "date_stddev_bp",
    "time_start_bp",
    "time_end_bp",
    "time_mean_bp",
    "time_label",
    "dating_basis",
    "coordinate_confidence",
    "data_type",
    "molecular_sex",
    "datasets",
    "accession_lineage",
    "sample_chronology",
    "sample_identity",
]
COUNTRIES = ["Denmark", "Finland", "Norway", "Sweden"]


def require(value: object, text: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not value:
        raise ValueError(text)


def json_object(raw: bytes) -> dict[str, Any]:
    """Decode a retained JSON object while rejecting duplicate member names."""

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len(items) == len({key for key, _ in items}), "Duplicate metadata key")
        return dict(items)

    def constant(token: str) -> None:
        raise ValueError("Nonfinite metadata: " + token)

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    require(isinstance(result, dict), "Object required")
    assert isinstance(result, dict)
    return result


def normalized(row: dict[str, Any]) -> dict[str, Any]:
    """Validate the declared source path, byte length and digest."""
    path = PurePosixPath(row["path"])
    checksum = row["sha256"]
    require(
        path.is_absolute()
        and path.as_posix() == row["path"]
        and ".." not in path.parts
        and "\\" not in row["path"],
        "Absolute normalized identity required",
    )
    require(
        type(row["bytes"]) is int
        and row["bytes"] >= 0
        and isinstance(checksum, str)
        and len(checksum) == 64
        and all(c in "0123456789abcdef" for c in checksum),
        "Typed identity required",
    )
    return {k: row[k] for k in ("path", "sha256", "bytes")}


def indexed(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index declared members while refusing duplicate source paths."""
    result = {}
    for row in rows:
        value = normalized(row)
        require(value["path"] not in result, "Duplicate identity path")
        result[value["path"]] = value
    return result


def member_name(name: object) -> str:
    """Validate a literal confined member name."""
    require(isinstance(name, str), "Text member required")
    assert isinstance(name, str)
    path = PurePosixPath(name)
    require(
        bool(path.parts)
        and not path.is_absolute()
        and path.as_posix() == name
        and ".." not in path.parts
        and "\\" not in name
        and len(path.parts) == 2
        and path.parts[0] == "payloads"
        and len(path.parts[1]) == 64
        and all(c in "0123456789abcdef" for c in path.parts[1]),
        "Closed content-addressed member required",
    )
    return name


def blob(row: dict[str, Any]) -> str:
    """Return the content-addressed member name for the declared identity."""
    return member_name("payloads/" + normalized(row)["sha256"])


def same(left: object, right: object) -> None:
    """Require exact nested values, native types and source membership."""
    require(type(left) is type(right), "Metadata types differ")
    if isinstance(left, dict) and isinstance(right, dict):
        require(list(left) == list(right), "Metadata keys/order differ")
        for key in left:
            same(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list):
        require(len(left) == len(right), "Metadata list sizes differ")
        for a, b in zip(left, right, strict=True):
            same(a, b)
    else:
        require(left == right, "Metadata values differ")


def output_namespace(
    plan: dict[str, Any],
    catalogue: dict[str, Any],
    refs: dict[str, Any],
    outer: dict[str, Any],
) -> dict[str, Any]:
    """Validate the native output namespace against its declared plan."""
    root = PurePosixPath(plan["output"])
    names = {row["path"] for row in catalogue["files"]}
    names.update(refs[key]["path"] for key in ("catalogue", "inner", "outer"))
    names.update(outer[key]["path"] for key in ("stdout", "stderr"))
    entries: dict[str, dict[str, str]] = {}
    for name in names:
        path = PurePosixPath(name)
        require(path.is_relative_to(root), "Native output escapes original root")
        relative = path.relative_to(root)
        entries[relative.as_posix()] = {"kind": "file"}
        for parent in relative.parents:
            if parent != PurePosixPath("."):
                entries[parent.as_posix()] = {"kind": "directory"}
    for snapshot in plan["owned_namespace_snapshots"]:
        prefix = PurePosixPath(snapshot["root"]).relative_to(root)
        for name, row in snapshot["entries"].items():
            if row["kind"] == "directory":
                entries[(prefix / name).as_posix()] = {"kind": "directory"}
    for name in ("scratch", "cache", "cache/matplotlib"):
        entries[name] = {"kind": "directory"}
    return {"root": str(root), "excluded": [], "entries": dict(sorted(entries.items()))}


def exact_public_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Select only source rows explicitly declared public by the capture."""
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        item = normalized(row)
        require(
            item["path"] not in result or result[item["path"]] == item,
            "Conflicting public role identity",
        )
        result[item["path"]] = item
    return result


def outer_stream_correspondence(
    catalogue: dict[str, Any], outer: dict[str, Any], inner_pin: dict[str, Any]
) -> dict[str, Any]:
    """The launcher writes PIPE buffers only after the inner catalogue is closed."""
    rows = indexed(catalogue["files"])
    stdout, stderr = normalized(outer["stdout"]), normalized(outer["stderr"])
    require(
        stdout["path"] != stderr["path"]
        and stdout["path"] not in rows
        and stderr["path"] not in rows,
        "Outer streams must be absent from the earlier inner catalogue",
    )
    tail = (
        json.dumps({"terminal": normalized(inner_pin), "actual_exit": 0}) + "\n"
    ).encode()
    require(
        stdout["bytes"] == len(tail)
        and stdout["sha256"] == hashlib.sha256(tail).hexdigest(),
        "Outer stdout must be the complete source-derived inner receipt line",
    )
    return {
        "stdout": stdout,
        "stderr": stderr,
        "outer_streams_absent_from_inner_catalogue": True,
        "streams_written_after_inner_catalogue": True,
        "stdout_is_exact_inner_receipt_print": True,
    }


def data_identity_rows(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Resolve declared data identities without deriving source values."""
    originals = indexed(plan["original_data_row_authority"])
    require(len(originals) == 162, "Exact162 source authorities required")
    root = PurePosixPath(plan["repository"])
    owned = PurePosixPath(plan["owned_repository"])
    rows = list(originals.values())
    copies = []
    for row in originals.values():
        path = PurePosixPath(row["path"])
        if path.is_relative_to(root / "data"):
            copies.append({**row, "path": str(owned / path.relative_to(root))})
    require(len(copies) == 160, "Exact160 owned data bodies required")
    return indexed(rows + copies)


def data_copy_correspondence(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Join recorded data copies to their exact original identities."""
    identities = data_identity_rows(plan)
    root = PurePosixPath(plan["repository"])
    owned = PurePosixPath(plan["owned_repository"])
    result: list[dict[str, Any]] = []
    for row in plan["original_data_row_authority"]:
        old = normalized(row)
        path = PurePosixPath(old["path"])
        copy = (
            identities[str(owned / path.relative_to(root))]
            if path.is_relative_to(root / "data")
            else None
        )
        result.append(
            {
                "original": old,
                "sealed_execution_copy": copy,
                "original_and_available_copy_inputs_required": True,
                "payload_member": None,
            }
        )
    return result


def retention_input_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve retained input roles against the frozen plan identities."""
    originals = indexed(plan["input_pins"])
    omitted = data_identity_rows(plan)
    require(
        len(originals) == 62435 and len(omitted) == 322,
        "Exact complete native/data identity populations required",
    )
    for path, row in omitted.items():
        same(originals[path], row)
    return [normalized(row) for row in plan["input_pins"]]


def selected_catalogue_rows(
    plan: dict[str, Any], catalogue: dict[str, Any]
) -> list[dict[str, Any]]:
    """Select the declared catalogue without silently restoring omitted inputs."""
    omitted = data_identity_rows(plan)
    rows = indexed(catalogue["files"])
    owned = PurePosixPath(plan["owned_repository"]) / "data"
    copies = {name for name in omitted if PurePosixPath(name).is_relative_to(owned)}
    require(
        len(copies) == 160 and copies <= set(rows),
        "Complete160 owned data omission required",
    )
    for name in copies:
        same(rows[name], omitted[name])
    require(
        {name for name in rows if PurePosixPath(name).is_relative_to(owned)} == copies,
        "Unknown owned data payload",
    )
    return [normalized(row) for row in catalogue["files"] if row["path"] not in omitted]


def source_join(plan: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, Any]]:
    """Join the source ledger to its declared frozen input identities."""
    same(ledger["canonical_identity"], plan["canonical_identity_at_source_freeze"])
    for key in (
        "original_data_row_authority",
        "new_current_metadata_epoch",
        "new_current_adapter_sources",
        "new_current_official_XML_sources",
        "current_place_hierarchy_sources",
        "logical_source_identities",
    ):
        same(ledger[key], plan[key])
    require(
        ledger["bytecode_payloads_copied_or_executed"] is False
        and ledger["bytecode_source_equivalence_claimed"] is False,
        "Opaque source promotion",
    )
    original, selected, copied, caches, generated = [
        indexed(ledger[k])
        for k in (
            "original_sources",
            "selected_execution_sources",
            "copied_sources",
            "omitted_unselected_cache_bytecode",
            "omitted_configured_generated_metadata",
        )
    ]
    require(
        tuple(map(len, (original, selected, copied, caches, generated)))
        == (6710, 2353, 2353, 4356, 1),
        "Exact source ledger populations differ",
    )
    require(
        set(original) == set(selected) | set(caches) | set(generated)
        and len(original) == sum(map(len, (selected, caches, generated))),
        "Source partition differs",
    )
    identities = data_identity_rows(plan)
    root = PurePosixPath(plan["repository"])
    owned = PurePosixPath(plan["owned_repository"])
    result: list[dict[str, Any]] = []
    omissions = {
        row["path"]: row
        for key in (
            "omitted_unselected_cache_bytecode",
            "omitted_configured_generated_metadata",
        )
        for row in ledger[key]
    }
    for row in ledger["original_sources"]:
        old = normalized(row)
        name = old["path"]
        if name in selected:
            relative = PurePosixPath(name).relative_to(root)
            copy = str(owned / relative)
            require(copy in copied, "Selected source copy absent")
            same(copied[copy], {**old, "path": copy})
            same(old, selected[name])
            if name in identities:
                same(old, identities[name])
                same(copied[copy], identities[copy])
                role = "declared_data_body_identity_only"
            else:
                allowed = (
                    len(relative.parts) >= 4
                    and relative.parts[0] == "packages"
                    and relative.parts[1]
                    in {
                        "bijux-pollenomics",
                        "bijux-pollenomics-lra",
                        "bijux-pollenomics-dev",
                        "pollenomics",
                    }
                    and relative.parts[2] == "src"
                ) or relative.as_posix() in {
                    "pyproject.toml",
                    "packages/bijux-pollenomics/pyproject.toml",
                    "packages/bijux-pollenomics-lra/pyproject.toml",
                    "packages/bijux-pollenomics-lra/.gitignore",
                }
                require(
                    allowed and relative.suffix not in {".pyc", ".pyo"},
                    "Public source escaped complete four-package scope",
                )
                role = "public_owned_source_resource"
            result.append(
                {"original": old, "execution_copy": copied[copy], "role": role}
            )
        else:
            item = omissions[name]
            require(
                item["executed_or_copied"] is False
                and item["source_equivalence_claimed"] is False,
                "Opaque source admitted",
            )
            same(old, normalized(item))
            result.append(
                {
                    "original": old,
                    "execution_copy": None,
                    "role": "bytecode_identity_only"
                    if name in caches
                    else "configured_generated_metadata_identity_only",
                }
            )
    require(
        sum(row["role"] == "public_owned_source_resource" for row in result) == 2193,
        "Exact2193 public code/resources required",
    )
    require(
        {r["execution_copy"]["path"] for r in result if r["execution_copy"] is not None}
        == set(copied),
        "Complete copied source set differs",
    )
    return result


def input_roles(
    plan: dict[str, Any],
    ledger: dict[str, Any],
    source: dict[str, Any],
    source_pin: dict[str, Any],
    peer_pin: dict[str, Any],
    runtime_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    """Classify inputs through their recorded source-role correspondence."""
    joins = source_join(plan, ledger)
    authority = plan["qualified_source_runtime"]
    groups = {
        "declared_data_body_identity_only": data_identity_rows(plan),
        "public_owned_source_resource": indexed(
            [
                r["execution_copy"]
                for r in joins
                if r["role"] == "public_owned_source_resource"
            ]
        ),
        "public_source_ledger": indexed([plan["source_ledger"]]),
        "public_native_source_controller": indexed(
            source["files"] + [source_pin, peer_pin]
        ),
        "public_runtime_authority_metadata": indexed(
            [authority[k] for k in ("plan", "outer", "common", "independent_review")]
        ),
        "runtime_identity_only": indexed(runtime_plan["input_pins"]),
    }
    originals = indexed(plan["input_pins"])
    require(
        len(originals) == 62435 and len(groups["runtime_identity_only"]) == 59882,
        "Exact native/runtime populations required",
    )
    result: list[dict[str, Any]] = []
    for index, row in enumerate(plan["input_pins"]):
        roles = [key for key, group in groups.items() if row["path"] in group]
        require(
            len(roles) == 1, "Exactly one native input role required: " + row["path"]
        )
        same(normalized(row), groups[roles[0]][row["path"]])
        result.append(
            {
                "original_index": index,
                "identity": normalized(row),
                "roles": roles,
                "payload_member": blob(row) if roles[0].startswith("public_") else None,
            }
        )
    require(
        set().union(*(set(rows) for rows in groups.values())) == set(originals),
        "Complete input role union differs",
    )
    return result


def object_same(left: object, right: object) -> None:
    """Scientific metadata objects are unordered; types and ordered sequences are exact."""
    require(type(left) is type(right), "Scientific metadata type differs")
    if isinstance(left, dict) and isinstance(right, dict):
        require(set(left) == set(right), "Scientific metadata keys differ")
        for key in left:
            object_same(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list):
        require(len(left) == len(right), "Scientific metadata list differs")
        for a, b in zip(left, right, strict=True):
            object_same(a, b)
    elif isinstance(left, float) and isinstance(right, float):
        require(
            __import__("math").isfinite(left) and left.hex() == right.hex(),
            "Finite binary64 metadata differs",
        )
    else:
        require(left == right, "Scientific metadata value differs")


def expected_calls(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the exact declared call sequence for retained input roles."""
    calls = []
    output = PurePosixPath(plan["output"]) / "producer"
    owned = PurePosixPath(plan["owned_repository"])
    for species in plan["species"]:
        calls.append(
            {
                "call": "build_species_runtime_manifest",
                "species": species["latin_name"],
                "data_root": str(owned / "data"),
            }
        )
        for country in (None, *COUNTRIES):
            label = "all" if country is None else country.casefold()
            calls.append(
                {
                    "call": "load_species_samples",
                    "species": species["latin_name"],
                    "political_entity": country,
                }
            )
            for form, name in [
                ("csv", "write_samples_csv"),
                ("geojson", "write_samples_geojson"),
            ]:
                calls.append(
                    {
                        "call": name,
                        "schema_argument": "omitted_default_v2",
                        "path": str(output / species["slug"] / (label + "." + form)),
                    }
                )
    return calls


def product_roles(
    plan: dict[str, Any], producer: dict[str, Any], review: dict[str, Any]
) -> list[dict[str, Any]]:
    """Check product identities against declared population and observer roles."""
    require(
        len(plan["species"])
        == len(producer["populations"])
        == len(review["species"])
        == 10,
        "Exact ten species required",
    )
    result: list[dict[str, Any]] = []
    seen = set()
    for species, actual, checked in zip(
        plan["species"], producer["populations"], review["species"], strict=True
    ):
        object_same(actual["species"], species)
        object_same(checked["species"], species)
        require(
            actual["runtime_manifest"]["schema_version"] == "adna-runtime-manifest.v1"
            and actual["runtime_manifest"]["runtime_ready"] is False,
            "Metadata export promoted scientific runtime readiness",
        )
        require(
            len(actual["results"]) == len(checked["all_queries"]) == 5,
            "Exact all/four country queries required",
        )
        for country, query, comparison in zip(
            (None, *COUNTRIES), actual["results"], checked["all_queries"], strict=True
        ):
            object_same(query["country_query"], country)
            object_same(comparison["country_query"], country)
            require(
                type(query["sample_count"]) is int and query["sample_count"] >= 0,
                "Typed API population required",
            )
            object_same(comparison["records"], query["sample_count"])
            require(
                comparison["complete_typed_source_equal"] is True
                and comparison["both_default_writers_full_bytes_equal"] is True,
                "Native typed/default writer proof missing",
            )
            require(
                all(
                    type(v) is int and v >= 0
                    for v in query["dataset_row_counts"].values()
                ),
                "Dataset denominators are typed counts",
            )
            object_same(query["products"], comparison["products"])
            require(
                set(query["products"]) == {"typed", "csv", "geojson"},
                "Exact three derived product forms required",
            )
            for form, suffix in [
                ("typed", "typed.json"),
                ("csv", "csv"),
                ("geojson", "geojson"),
            ]:
                row = normalized(query["products"][form])
                label = "all" if country is None else country.casefold()
                expected = str(
                    PurePosixPath(plan["output"])
                    / "producer"
                    / species["slug"]
                    / (label + "." + suffix)
                )
                require(
                    row["path"] == expected and expected not in seen,
                    "Derived product path reused/escaped",
                )
                seen.add(expected)
                result.append(
                    {
                        "species": species,
                        "country_query": country,
                        "form": form,
                        "identity": row,
                        "payload_member": blob(row),
                        "derived_source_metadata_not_biology_or_rights_admission": True,
                    }
                )
    require(len(result) == 150, "Exactly150 native derived products required")
    return result


def qualify_scope(
    plan: dict[str, Any],
    inner: dict[str, Any],
    outer: dict[str, Any],
    producer: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    """Check declared scope against captured execution and data roles."""
    require(
        plan["schema_version"] == "animal-owned-public-export-plan.v1"
        and plan["candidate"] == CANDIDATE,
        "Exact animal source epoch required",
    )
    for value in (inner, outer, producer, review):
        require(
            type(value["actual_exit"]) is int
            and value["actual_exit"] == 0
            and value["candidate"] == CANDIDATE,
            "Native stage/whole0 required",
        )
    require(
        inner["schema_version"] == "animal-animal-export-terminal.v1"
        and outer["schema_version"]
        == "animal-animal-export-owned-child-watchdog-terminal.v1",
        "Literal original native schema differs",
    )
    for value in (inner, outer):
        require(
            value["plan_sha256"] == PLAN_SHA
            and value["memory_bound_pass"] is True
            and value["inclusive_storage_bound_pass"] is True,
            "Native custody/resource failure",
        )
    require(
        inner["exception"] is None
        and inner["after_custody_error"] is None
        and inner["completed_whole_wall_bound_pass"] is True,
        "Native error or wall refusal",
    )
    require(
        type(outer["child_native_exit"]) is int
        and outer["child_native_exit"] == 0
        and outer["child_timed_out"] is False
        and outer["registered_plan_unchanged"] is True
        and outer["completed_outer_wall_bound_pass"] is True,
        "Outer watchdog refusal",
    )
    require(
        inner["live_canonical_equality_claimed"] is False
        and inner["OS_quota_or_full_descendant_RSS_claimed"] is False,
        "Native scope inflated",
    )
    expected = [
        ("maintained-animal-source-export", "producer", 300),
        ("independent-animal-default-export-observer", "observer", 180),
    ]
    require(
        len(plan["stages"]) == len(inner["stages"]) == 2,
        "Exact native two stages required",
    )
    python = plan["runtime_entry_lexical_paths"][0]
    source = str(PurePosixPath(plan["stages"][0]["argv"][3]).parent)
    for declaration, actual, (name, action, seconds) in zip(
        plan["stages"], inner["stages"], expected, strict=True
    ):
        same(
            declaration,
            {
                "id": name,
                "action": action,
                "timeout_seconds": seconds,
                "argv": [
                    python,
                    "-I",
                    "-B",
                    source + "/entry.py",
                    action,
                    "--plan",
                    plan["output"] + "/plan.json",
                ],
            },
        )
        for key in declaration:
            same(actual[key], declaration[key])
        require(
            type(actual["actual_exit"]) is int
            and actual["actual_exit"] == 0
            and actual["timed_out"] is False,
            "Native stage failed",
        )
    require(
        producer["schema_version"] == "animal-current-public-export-execution.v1"
        and review["schema_version"] == "animal-current-public-API-export-review.v1",
        "Scientific witness schemas differ",
    )
    same(producer["actual_argv"][1:], plan["stages"][0]["argv"][1:])
    require(producer["actual_executable"] == python, "Actual lexical Python differs")
    same(producer["maintained_public_calls"], expected_calls(plan))
    same(plan["countries"], COUNTRIES)
    same(
        producer["owned_package_search_roots"],
        [
            plan["owned_repository"] + "/packages/" + name + "/src"
            for name in (
                "bijux-pollenomics",
                "bijux-pollenomics-lra",
                "bijux-pollenomics-dev",
                "pollenomics",
            )
        ],
    )
    require(
        producer["actual_data_root"] == plan["owned_repository"] + "/data",
        "API data root borrowed",
    )
    require(
        producer["API_reads_saved_normalized_JSON_as_producer_input"] is False
        and producer["new_HTTP_genotype_model_R_or_full_requirement_admission"] is False
        and producer["numerical_import_attempts"] == producer["network_attempts"] == [],
        "Producer source behavior promoted",
    )
    protected = indexed(plan["input_pins"])
    modules = set()
    for row in producer["actual_first_party_origins"]:
        require(
            row["module"] not in modules
            and PurePosixPath(row["path"]).is_relative_to(
                PurePosixPath(plan["owned_repository"])
            ),
            "First-party source mixed/escaped",
        )
        modules.add(row["module"])
        same(normalized(row), protected[row["path"]])
    require(
        {
            "bijux_pollenomics.adna.workflow.runtime",
            "bijux_pollenomics.adna.workflow.normalization.samples",
            "bijux_pollenomics.reporting.rendering.record_exports",
        }
        <= modules,
        "Actual API/writer source missing",
    )
    same(
        normalized(producer["actual_XML_dependency_origin"]),
        protected[producer["actual_XML_dependency_origin"]["path"]],
    )
    require(
        type(producer["original_logical_source_identities_verified"]) is int
        and producer["original_logical_source_identities_verified"] == 8
        and len(plan["logical_source_identities"]) == 8,
        "Original logical role count differs",
    )
    for key, producer_key, count in [
        ("new_current_official_XML_sources", "current_official_XML_input_roles", 3),
        ("current_place_hierarchy_sources", "current_place_hierarchy_input_roles", 1),
    ]:
        require(len(plan[key]) == count, "Current source role denominator differs")
        object_same(producer[producer_key], plan[key])
        require(
            all(
                row["original_catalog_protection_claimed"] is False for row in plan[key]
            ),
            "Current role promoted to original catalogue",
        )
    observations = producer["current_adapter_logical_observations"]
    require(
        len(plan["new_current_adapter_sources"]) == len(observations) == 5,
        "Exact five current archive observations required",
    )
    for expected_archive, actual_archive in zip(
        plan["new_current_adapter_sources"], observations, strict=True
    ):
        for key in ("project_accession", "stored", "receipt", "logical_SHA_authority"):
            object_same(actual_archive[key], expected_archive[key])
        require(
            actual_archive["original_catalog_protection_claimed"] is False
            and expected_archive["original_catalog_protection_claimed"] is False,
            "Current archive original-epoch promotion",
        )
        logical = actual_archive["logical"]
        normalized({**logical, "path": "/controlled/logical"})
        require(
            logical["path"] == expected_archive["logical"]["path"]
            and logical["bytes"] == expected_archive["logical"]["bytes"]
            and (
                expected_archive["logical"]["sha256"] is None
                or logical["sha256"] == expected_archive["logical"]["sha256"]
            ),
            "Observed logical identity differs",
        )
    require(
        review["registered_plan_sha256"] == PLAN_SHA
        and review["producer_execution"]["sha256"] == PRODUCER_SHA,
        "Independent source joins differ",
    )
    for key in (
        "full_typed_identity_chronology_native_taxon_and_context_checked",
        "no_pollen_measurement_fields_in_typed_or_default_exports",
        "API_country_query_is_direct_political_entity_not_legacy_country_bundle_interpolation",
    ):
        require(review[key] is True, "Current behavioral proof incomplete")
    for key in (
        "whole_ADNA_requirement_current_default_or_rights_biology_LRA_acceptance_predeclared",
        "original_normalization_native_receipt_requalified",
        "new_HTTP_raw_archive_acquisition_genotype_model_or_R_executed",
    ):
        require(review[key] is False, "Historical or scientific admission inflated")
    require(
        type(review["complete_saved_source_population"]) is int
        and review["complete_saved_source_population"] == 1468
        and type(review["actual_API_source_admitted_population"]) is int
        and review["actual_API_source_admitted_population"] == 1468,
        "Exact observed source/API population differs",
    )
    same(
        review["typed_flags_preserved_but_not_exported_by_current_contract"],
        ["inclusion_status", "taxon_alignment_status"],
    )
    same(review["actual_default_export_fields"], CURRENT_FIELDS)
    require(
        len(review["source_owned_taxon_exceptions"]) == 4,
        "Four source-owned blocked native taxon contexts required",
    )
    expected_taxa = {
        ("bos_taurus", "prjna705960:samn18106827"): (
            "Bos primigenius",
            "9909",
            "PRJNA705960",
        ),
        ("bos_taurus", "prjna705960:samn18106828"): (
            "Bos primigenius",
            "9909",
            "PRJNA705960",
        ),
        ("bos_taurus", "prjna705960:samn18106829"): (
            "Bos primigenius",
            "9909",
            "PRJNA705960",
        ),
        ("ovis_aries", "prjeb41594:samea8022722"): (
            "Capra hircus",
            "9925",
            "PRJEB41594",
        ),
    }
    seen_taxa = set()
    for row in review["source_owned_taxon_exceptions"]:
        key = (
            row["container_namespace"].split(":", 1)[0],
            row["native_sample_id"].split(":sample:", 1)[1],
        )
        require(
            key in expected_taxa and key not in seen_taxa,
            "Reviewed native taxonomy context differs",
        )
        seen_taxa.add(key)
        taxon, tax_id, project = expected_taxa[key]
        require(
            row["source_species"] == taxon
            and row["source_native_tax_id"] == tax_id
            and row["project_accession"] == project
            and row["taxon_alignment_status"] == "project_species_mismatch"
            and row["inclusion_status"] == "sample_context_blocked"
            and row["cross_species_publication_admitted"] is False,
            "Source-owned taxon block promoted",
        )
    require(
        seen_taxa == set(expected_taxa), "Exact four native taxonomy blocks required"
    )
    product_roles(plan, producer, review)
    return {
        "source_candidate": CANDIDATE,
        "native_stage_exits": [0, 0],
        "native_inner_and_outer_exits": [0, 0],
        "species": 10,
        "manifest_calls": 10,
        "API_load_calls": 50,
        "default_writer_calls": 100,
        "derived_products": 150,
        "saved_source_population": 1468,
        "actual_API_population": 1468,
        "blocked_source_owned_taxon_contexts": 4,
        "typed_only_block_flags_preserved": True,
        "generic_exports_include_those_block_flags": False,
        "original_normalization_receipt_recovered": False,
        "rights_biology_human_calibration_LRA_or_whole_ADNA_admitted": False,
    }


def validate_packet(
    packet: dict[str, Any], read: Callable[[str], bytes]
) -> dict[str, Any]:
    """Validate retained packet roles and recorded native execution."""
    require(packet["schema_version"] == SCHEMA, "Exact animal capture schema required")
    same(packet["scope"], SCOPE)
    members = packet["members"]
    used = set()
    for name, row in members.items():
        member_name(name)
        require(
            set(row) == {"sha256", "bytes"}, "Exact public identity fields required"
        )
        normalized({"path": "/controlled/payload", **row})
        raw = read(name)
        require(
            hashlib.sha256(raw).hexdigest() == row["sha256"]
            and len(raw) == row["bytes"],
            "Public member changed",
        )
    bindings = exact_public_rows([row["original"] for row in packet["public_bindings"]])
    for row in packet["public_bindings"]:
        name = blob(row["original"])
        require(
            row["member"] == name
            and members[name] == {k: row["original"][k] for k in ("sha256", "bytes")},
            "Public binding differs",
        )
        used.add(name)
    require(used == set(members), "Unknown/unreferenced public member")

    def document(row: dict[str, Any]) -> dict[str, Any]:
        same(bindings[row["path"]], normalized(row))
        return json_object(read(blob(row)))

    refs = packet["native_references"]
    for key, checksum in [
        ("plan", PLAN_SHA),
        ("inner", INNER_SHA),
        ("outer", OUTER_SHA),
        ("producer", PRODUCER_SHA),
        ("review", REVIEW_SHA),
    ]:
        require(refs[key]["sha256"] == checksum, "Original native authority differs")
    plan, ledger, inner, outer, producer, review = [
        document(refs[k])
        for k in ("plan", "source_ledger", "inner", "outer", "producer", "review")
    ]
    same(plan["source_ledger"], refs["source_ledger"])
    same(inner["products_manifest"], refs["catalogue"])
    same(outer["inner_terminal"], refs["inner"])
    same(review["producer_execution"], refs["producer"])
    result = qualify_scope(plan, inner, outer, producer, review)
    same(packet["receipt_scope"], result)
    catalogue = document(refs["catalogue"])
    require(
        len(catalogue["files"]) == inner["products_count_before_manifest"] == 2512,
        "Complete native catalogue differs",
    )
    same(
        packet["outer_stream_catalogue_correspondence"],
        outer_stream_correspondence(catalogue, outer, refs["inner"]),
    )
    require(
        read(blob(outer["stdout"]))
        == (
            json.dumps({"terminal": normalized(refs["inner"]), "actual_exit": 0}) + "\n"
        ).encode(),
        "Complete source-derived late stdout differs",
    )
    original_source = packet["source_controller"]
    require(
        original_source["manifest"]["sha256"] == SOURCE_SHA,
        "Original source manifest differs",
    )
    source = document(original_source["manifest"])
    peer = document(original_source["review"])
    require(
        peer["approved"] is True and peer["source_manifest_sha256"] == SOURCE_SHA,
        "Original source peer absent",
    )
    same(packet["runtime_authority"], plan["qualified_source_runtime"])
    runtime_plan = document(plan["qualified_source_runtime"]["plan"])
    roles = input_roles(
        plan,
        ledger,
        source,
        original_source["manifest"],
        original_source["review"],
        runtime_plan,
    )
    same(packet["original_input_roles"], roles)
    same(packet["original_source_join"], source_join(plan, ledger))
    same(packet["original_data_copy_correspondence"], data_copy_correspondence(plan))
    same(
        packet["original_output_namespace"],
        output_namespace(plan, catalogue, refs, outer),
    )
    metadata = packet["metadata_source_controller"]
    manifest = document(metadata["manifest"])
    admission = document(metadata["review"])
    require(
        manifest["source_only"] is True
        and admission["approved"] is True
        and admission["source_manifest_sha256"] == metadata["manifest"]["sha256"],
        "Metadata source approval differs",
    )
    expected = exact_public_rows(
        selected_catalogue_rows(plan, catalogue)
        + [row["identity"] for row in roles if row["payload_member"] is not None]
        + list(refs.values())
        + [outer["stdout"], outer["stderr"]]
        + source["files"]
        + list(original_source.values())
        + [
            plan["qualified_source_runtime"][k]
            for k in ("plan", "outer", "common", "independent_review")
        ]
        + manifest["files"]
        + list(metadata.values())
    )
    require(bindings == expected, "Exact finite public roles differ")
    require(
        not set(data_identity_rows(plan)).intersection(bindings),
        "Original/owned data authority entered public payloads",
    )
    products = product_roles(plan, producer, review)
    originals = indexed(catalogue["files"])
    expected_paths = set()
    for row in products:
        identity = row["identity"]
        same(bindings[identity["path"]], identity)
        same(originals[identity["path"]], identity)
        expected_paths.add(identity["path"])
    require(
        {
            path
            for path in originals
            if PurePosixPath(path).is_relative_to(
                PurePosixPath(plan["output"]) / "producer"
            )
        }
        == expected_paths,
        "Complete150 native product catalogue differs",
    )
    return result
