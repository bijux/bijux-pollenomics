"""Portable current human/animal scientific export evidence without publisher admission."""

from __future__ import annotations

from collections.abc import Callable
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any

from ...contracts import JsonObject, ReportRebuildError
from .animal_export import (
    CAPTURE as ANIMAL_CAPTURE,
)
from .animal_export import (
    PROOF_ROOT,
    animal_context,
    checked,
    exact_tree,
    physical,
    same_metadata,
)
from .animal_packet import json_object, member_name
from .current_export import (
    CAPTURE as HUMAN_CAPTURE,
)
from .current_export import (
    CAPTURE_SHA256 as HUMAN_CAPTURE_SHA,
)
from .current_export import (
    WITNESS as OLD_WITNESS,
)
from .current_export import (
    WITNESS_SHA256 as OLD_WITNESS_SHA,
)
from .current_export import (
    publisher_contract,
)
from .execution_packet import validate_packet as validate_human_packet

WITNESS = "reports/science/source-cohorts/adna-current-domain-evidence.json"
HOST = "packages/bijux-pollenomics/src/bijux_pollenomics/"
WATCHED_PREFIX = HOST + "adna/"
WATCHED_FILES = frozenset(
    {
        HOST + "__init__.py",
        HOST + "reporting/__init__.py",
        HOST + "reporting/rendering/__init__.py",
        HOST + "reporting/rendering/record_exports.py",
    }
)
MINIMUM_ORIGINS = frozenset(
    {
        "bijux_pollenomics.adna.api",
        "bijux_pollenomics.adna.workflow.runtime",
        "bijux_pollenomics.adna.domain.models.samples",
        "bijux_pollenomics.reporting.rendering.record_exports",
    }
)
MAX_PRODUCT_TOTAL_BYTES = 256 * 1024 * 1024
RESULT_IDENTITY = {
    "sha256": "49f1ff34d51e71dfa7c503f067f8d696f812f90e72a9bee84b335f392ddd39bb",
    "bytes": 783871,
}
HUMAN_SOURCE = "601112dd1f4b9e09d2cfdec7fa57d9f4ae3303a7"
ANIMAL_SOURCE = "ad591c301bcadb6a3f963caa836a2e38a16d0de4"
COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")
READERS = tuple(
    path
    for country in ("denmark", "finland", "norway", "sweden")
    for path in (
        f"docs/report/countries/{country}/README.md",
        f"docs/report/countries/{country}/{country}_aadr_v66_samples.md",
        f"docs/report/countries/{country}/{country}_animal_adna_v66_samples.md",
    )
)
BLOCKED_TAXA = (
    ("bos_taurus", "prjna705960:samn18106827", "Bos primigenius"),
    ("bos_taurus", "prjna705960:samn18106828", "Bos primigenius"),
    ("bos_taurus", "prjna705960:samn18106829", "Bos primigenius"),
    ("ovis_aries", "prjeb41594:samea8022722", "Capra hircus"),
)
CURRENT_FIELDS = (
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
)
SCHEMA: dict[str, Any] = {
    "typed_record_fields": [
        "identity",
        "locality_identity",
        "species_latin_name",
        "species_common_name",
        "source_family",
        "source_release",
        "record_modality",
        "review_strength",
        "provenance_quality",
        "master_id",
        "group_id",
        "locality",
        "political_entity",
        "coordinates",
        "publication",
        "year_first_published",
        "full_date",
        "chronology",
        "data_type",
        "molecular_sex",
        "datasets",
        "project_accession",
        "paper_doi",
        "paper_url",
        "supplementary_source",
        "inclusion_status",
        "inclusion_note",
        "chronology_strength",
        "chronology_normalization_status",
        "chronology_provenance_path",
        "chronology_provenance_kind",
        "chronology_provenance_locator",
        "chronology_provenance_text",
        "chronology_conflict_note",
        "sample_basis",
        "archive_native_sample_id",
        "paper_native_sample_label",
        "supplementary_table_sample_label",
        "sample_evidence_status",
        "sample_lineage_path",
        "sample_lineage_locator",
        "sample_lineage_excerpt",
        "sample_identity_resolution",
        "sample_ambiguity_note",
        "source_native_tax_id",
        "source_native_scientific_name",
        "taxon_alignment_status",
        "archive_native_experiment_id",
        "source_native_identity_kind",
    ],
    "typed_field_authority": {
        "repository_path": "packages/bijux-pollenomics/src/bijux_pollenomics/adna/domain/models/samples.py",
        "sha256": "35db235289c297c2154215af88c790cff68ff15703f19b96a256da0f8610c0fd",
        "bytes": 6826,
        "class": "AdnaSampleRecord",
        "method": "as_dict",
    },
    "forbidden_fields": [
        "pollen_count",
        "pollen_sum",
        "relative_pollen_percentage",
        "ppe",
        "fall_speed_m_s",
        "whole_pollen",
    ],
    "pollen_eligibility_flags_must_be_typed_false": [
        "pollen_eligible",
        "pollen_propagation_eligible",
        "pollen_measurement_field_leakage",
    ],
    "blocked_source_taxon_exceptions": [
        {
            "container_slug": "bos_taurus",
            "master_id": "prjna705960:samn18106827",
            "source_species": "Bos primigenius",
            "source_native_tax_id": "9909",
            "project_accession": "PRJNA705960",
        },
        {
            "container_slug": "bos_taurus",
            "master_id": "prjna705960:samn18106828",
            "source_species": "Bos primigenius",
            "source_native_tax_id": "9909",
            "project_accession": "PRJNA705960",
        },
        {
            "container_slug": "bos_taurus",
            "master_id": "prjna705960:samn18106829",
            "source_species": "Bos primigenius",
            "source_native_tax_id": "9909",
            "project_accession": "PRJNA705960",
        },
        {
            "container_slug": "ovis_aries",
            "master_id": "prjeb41594:samea8022722",
            "source_species": "Capra hircus",
            "source_native_tax_id": "9925",
            "project_accession": "PRJEB41594",
        },
    ],
    "record_modality_policy": {
        "allowed_by_domain": {
            "human": ["metadata_only"],
            "animal": ["archive_reads", "mitogenome_only"],
        },
        "source_authorities": [
            {
                "sha256": "ce4f71a89020d62000398734c54bd2309dc60f49ce94ded8e5042262afba64a1",
                "bytes": 1727,
                "repository_path": "packages/bijux-pollenomics/src/bijux_pollenomics/adna/projects/registry/sample_classification.py",
            },
            {
                "sha256": "8c3d6d3575cbd627c5974b254a834fca35aeb774dfc1dd82ed4d145b5d33d380",
                "bytes": 22265,
                "repository_path": "packages/bijux-pollenomics/src/bijux_pollenomics/adna/projects/registry/samples.py",
            },
            {
                "sha256": "3fa0bf8ca929bdfde2eea4d15bf910f613eef83fc000a12eadc78cdb61f4a2c7",
                "bytes": 14597,
                "repository_path": "packages/bijux-pollenomics/src/bijux_pollenomics/adna/workflow/normalization/samples.py",
            },
            {
                "sha256": "7db8367e5645089612ac516f2d627e251d53fff60f8d3817a7714abaf470444e",
                "bytes": 231,
                "repository_path": "packages/bijux-pollenomics/src/bijux_pollenomics/adna/species/homo_sapiens/constants.py",
            },
        ],
        "animal_classifier_function": "_record_modality_for",
        "animal_classifier_AST_sha256": "f13368e2862d9e478f95a1dd5bd8395b1c1787e6c10096acb1fd5be8bcd4508d",
        "meaning": "DNA source metadata: sequencing-target classification propagated from curated row unchanged into AdnaSampleRecord. Does not claim archive/genotype contents were read by this callback. Native independent full-source reconstruction preserves each exact source value; source-bundle summaries and capability matrices are not per-record modality authority.",
    },
}


def require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("Current DNA domain evidence: " + reason)


def exact(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            exact(left[k], right[k]) for k in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            exact(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def identity(row: dict[str, Any]) -> dict[str, Any]:
    name = row["path"]
    checksum = row["sha256"]
    require(isinstance(name, str), "Text identity path required")
    path = PurePosixPath(name)
    require(
        path.is_absolute()
        and path.as_posix() == name
        and ".." not in path.parts
        and "\\" not in name,
        "Absolute normalized metadata identity required",
    )
    require(
        type(row["bytes"]) is int
        and row["bytes"] >= 0
        and isinstance(checksum, str)
        and len(checksum) == 64
        and all(c in "0123456789abcdef" for c in checksum),
        "Typed metadata SHA/size required",
    )
    return {key: row[key] for key in ("path", "sha256", "bytes")}


def index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for row in rows:
        item = identity(row)
        require(item["path"] not in result, "Duplicate expected input path")
        result[item["path"]] = item
    return result


def parse_object(raw: bytes) -> dict[str, Any]:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len(values) == len({k for k, _ in values}), "Duplicate metadata key")
        return dict(values)

    def constant(value: str) -> None:
        raise ValueError("Nonfinite metadata: " + value)

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    require(isinstance(result, dict), "Metadata object required")
    assert isinstance(result, dict)
    return result


def array_or_object(raw: bytes) -> Any:
    # Reuse the reviewed duplicate/nonfinite parser for both JSON container forms.
    return parse_object(b'{"value":' + raw + b"}")["value"]


def source_join(
    human: dict[str, Any],
    animal: dict[str, Any],
    native_h: dict[str, Any],
    native_a: dict[str, Any],
    schema: dict[str, Any],
    read: Callable[[dict[str, Any]], bytes],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    require(
        human["candidate"] != animal["candidate"],
        "Distinct actual human/animal source epochs required",
    )
    populations = []
    additional = []
    origin_sets = []
    for plan, native in ((human, native_h), (animal, native_a)):
        owned = PurePosixPath(plan["owned_repository"])
        pins = index(plan["input_pins"])
        selected = {}
        for name, row in pins.items():
            path = PurePosixPath(name)
            if not path.is_relative_to(owned):
                continue
            relative = path.relative_to(owned).as_posix()
            if (
                relative.startswith(WATCHED_PREFIX) and relative.endswith(".py")
            ) or relative in WATCHED_FILES:
                selected[relative] = {"sha256": row["sha256"], "bytes": row["bytes"]}
                read(row)
                additional.append(row)
        require(
            WATCHED_FILES.issubset(selected)
            and WATCHED_PREFIX + "api.py" in selected
            and WATCHED_PREFIX + "domain/models/samples.py" in selected,
            "Incomplete watched source interface population",
        )
        source_field = schema["typed_field_authority"]
        require(
            exact(
                selected[source_field["repository_path"]],
                {k: source_field[k] for k in ("sha256", "bytes")},
            ),
            "Typed field schema source differs from actual execution",
        )
        for authority in schema["record_modality_policy"]["source_authorities"]:
            require(
                exact(
                    selected.get(authority["repository_path"]),
                    {key: authority[key] for key in ("sha256", "bytes")},
                ),
                "Record modality rule source differs from actual execution",
            )
        origins = {}
        for row in native["actual_first_party_origins"]:
            name = row["module"]
            require(
                name not in origins
                and name.split(".")[0]
                in {"bijux_pollenomics", "bijux_pollenomics_dev"},
                "Repeated/foreign actual first-party origin",
            )
            require(
                exact(pins.get(row["path"]), identity(row))
                and PurePosixPath(row["path"]).is_relative_to(owned),
                "Actual source origin absent from owned plan pins",
            )
            relative = PurePosixPath(row["path"]).relative_to(owned).as_posix()
            origins[name] = {
                "repository_path": relative,
                "sha256": row["sha256"],
                "bytes": row["bytes"],
            }
        require(
            MINIMUM_ORIGINS.issubset(origins),
            "Actual loader/model/default-writer source origin missing",
        )
        origin_sets.append(origins)
        populations.append(selected)
    require(
        exact(populations[0], populations[1]),
        "Watched ADNA interfaces changed between source epochs",
    )
    common = sorted(set(origin_sets[0]).intersection(origin_sets[1]))
    for name in common:
        require(
            exact(origin_sets[0][name], origin_sets[1][name]),
            "Shared observed import origin differs between epochs",
        )
    return {
        "source_candidates": [human["candidate"], animal["candidate"]],
        "same_candidate_claimed": False,
        "watched_source_files": [
            {"repository_path": k, **v} for k, v in sorted(populations[0].items())
        ],
        "shared_observed_origins": {k: origin_sets[0][k] for k in common},
        "all_first_party_origin_memberships_verified": True,
    }, additional


def products(d: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for produced, observed in zip(
        d["raw_producer"]["countries"], d["raw_review"]["countries"], strict=True
    ):
        require(
            produced["country_query"] == observed["country_query"],
            "Human country product roles differ",
        )
        result.append(
            {
                "domain": "human",
                "species": {"latin_name": "Homo sapiens"},
                "query": produced["country_query"],
                "records": produced["sample_count"],
                "rows": produced["products"],
            }
        )
    plan = d["animal_plan"]
    require(
        [r["species"] for r in d["animal_producer"]["populations"]]
        == [r["species"] for r in d["animal_review"]["species"]]
        == plan["species"],
        "Animal complete species population/order differs",
    )
    for produced, observed in zip(
        d["animal_producer"]["populations"], d["animal_review"]["species"], strict=True
    ):
        expected_queries = [None, *COUNTRIES]
        require(
            [r["country_query"] for r in produced["results"]]
            == [r["country_query"] for r in observed["all_queries"]]
            == expected_queries,
            "Animal five direct query roles differ",
        )
        for p, o in zip(produced["results"], observed["all_queries"], strict=True):
            require(
                type(p["sample_count"]) is int
                and type(o["records"]) is int
                and p["sample_count"] == o["records"]
                and o["complete_typed_source_equal"] is True
                and o["both_default_writers_full_bytes_equal"] is True
                and exact(p["products"], o["products"]),
                "Animal complete generated product identity/population differs",
            )
            result.append(
                {
                    "domain": "animal",
                    "species": produced["species"],
                    "query": p["country_query"],
                    "records": p["sample_count"],
                    "rows": p["products"],
                }
            )
    require(
        len(result) == 54
        and all(
            type(r["records"]) is int
            and r["records"] >= 0
            and set(r["rows"]) == {"csv", "geojson", "typed"}
            for r in result
        ),
        "Complete four human/fifty animal product populations required",
    )
    names = [identity(row)["path"] for item in result for row in item["rows"].values()]
    require(
        len(names) == len(set(names)) == 162,
        "Exactly162 unique derived products required",
    )
    require(
        sum(row["bytes"] for item in result for row in item["rows"].values())
        <= MAX_PRODUCT_TOTAL_BYTES,
        "Total declared derived product read bound exceeded",
    )
    return result


def clean(value: Any, schema: dict[str, Any], keysets: set[tuple[str, ...]]) -> None:
    pending = [value]
    while pending:
        item = pending.pop()
        if type(item) is dict:
            require(
                not set(schema["forbidden_fields"]).intersection(
                    key.casefold() for key in item
                ),
                "Pollen measurement field leaked into derived metadata",
            )
            for name in schema["pollen_eligibility_flags_must_be_typed_false"]:
                if name in item:
                    require(
                        item[name] is False, "Pollen eligibility/leakage flag promoted"
                    )
            keysets.add(tuple(sorted(item)))
            pending.extend(item.values())
        elif type(item) is list:
            pending.extend(item)


def record_taxon(
    sample: dict[str, Any], item: dict[str, Any], schema: dict[str, Any]
) -> None:
    container = item["species"]["latin_name"]
    if sample["species_latin_name"] == container:
        return
    require(item["domain"] == "animal", "Unexpected human source taxon")
    allowed = [
        row
        for row in schema["blocked_source_taxon_exceptions"]
        if row["container_slug"] == item["species"]["slug"]
        and row["master_id"] == sample["master_id"]
    ]
    require(len(allowed) == 1, "Unknown source taxon exception")
    row = allowed[0]
    require(
        sample["species_latin_name"]
        == sample["source_native_scientific_name"]
        == row["source_species"]
        and sample["source_native_tax_id"] == row["source_native_tax_id"]
        and sample["project_accession"] == row["project_accession"]
        and sample["source_family"] == "ENA"
        and sample["source_native_identity_kind"] == "biological_sample_accession"
        and sample["taxon_alignment_status"] == "project_species_mismatch"
        and sample["inclusion_status"] == "sample_context_blocked",
        "Source-owned taxon block changed",
    )


def qualify_record_modality(
    sample: dict[str, Any], domain: str, schema: dict[str, Any]
) -> None:
    """Keep source-derived DNA modality distinct from the callback's metadata-only role."""
    require(domain in {"human", "animal"}, "Unknown typed evidence domain")
    modality = sample["record_modality"]
    require(
        type(modality) is str
        and modality in schema["record_modality_policy"]["allowed_by_domain"][domain],
        "Unknown or cross-domain source record modality",
    )


def scan_products(
    items: list[dict[str, Any]],
    schema: dict[str, Any],
    read: Callable[[dict[str, Any]], bytes],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    summaries = []
    additional = []
    for item in items:
        rows = item["rows"]
        payload = {role: read(row) for role, row in rows.items()}
        typed = parse_object(payload["typed"])
        expected_top = {
            "country_query",
            "actual_typed_records",
            "actual_dataset_row_counts",
        }
        if item["domain"] == "animal":
            expected_top.add("species")
            require(
                exact(typed["species"], item["species"]), "Typed animal species differs"
            )
        require(
            set(typed) == expected_top
            and typed["country_query"] == item["query"]
            and type(typed["actual_typed_records"]) is list
            and len(typed["actual_typed_records"]) == item["records"],
            "Complete typed record envelope/population differs",
        )
        for sample in typed["actual_typed_records"]:
            require(
                type(sample) is dict
                and set(sample) == set(schema["typed_record_fields"]),
                "Complete DNA-only typed fields differ",
            )
            qualify_record_modality(sample, item["domain"], schema)
            record_taxon(sample, item, schema)
        reader = csv.DictReader(io.StringIO(payload["csv"].decode("utf-8"), newline=""))
        require(
            reader.fieldnames == list(CURRENT_FIELDS),
            "Complete29 default CSV field names/order differ",
        )
        csv_rows = list(reader)
        require(
            len(csv_rows) == item["records"]
            and all(
                None not in row and all(v is not None for v in row.values())
                for row in csv_rows
            ),
            "CSV population or row shape differs",
        )
        for row, sample in zip(csv_rows, typed["actual_typed_records"], strict=True):
            require(
                row["schema_version"] == "adna-sample-record-export.v2"
                and row["species_latin_name"] == sample["species_latin_name"]
                and row["genetic_id"] == sample["identity"]["stable_token"],
                "CSV DNA schema/species/record identity differs",
            )
            for key in ("sample_chronology", "sample_identity"):
                row[key] = array_or_object(row[key].encode("utf-8"))
                require(
                    type(row[key]) is dict,
                    "Owned default CSV extension must be a JSON object",
                )
        geo = parse_object(payload["geojson"])
        require(
            set(geo) == {"schema_version", "type", "features"}
            and geo["schema_version"] == "adna-sample-geojson-collection.v2"
            and geo["type"] == "FeatureCollection"
            and type(geo["features"]) is list
            and len(geo["features"]) == item["records"],
            "Complete default GeoJSON envelope/population differs",
        )
        for feature, sample in zip(
            geo["features"], typed["actual_typed_records"], strict=True
        ):
            require(
                type(feature) is dict
                and set(feature) == {"schema_version", "type", "geometry", "properties"}
                and feature["schema_version"] == "adna-sample-geojson.v2"
                and feature["type"] == "Feature"
                and set(feature["properties"]) == set(CURRENT_FIELDS)
                and feature["properties"]["species_latin_name"]
                == sample["species_latin_name"]
                and feature["properties"]["genetic_id"]
                == sample["identity"]["stable_token"],
                "Complete GeoJSON feature/default fields differ",
            )
        keysets: set[tuple[str, ...]] = set()
        for value in (typed, csv_rows, geo):
            clean(value, schema, keysets)
        summaries.append(
            {
                "domain": item["domain"],
                "species": item["species"]["latin_name"],
                "country_query": item["query"],
                "records": item["records"],
                "whole_recursive_keysets": [list(keys) for keys in sorted(keysets)],
                "no_pollen_semantics_leakage": True,
                "products": rows,
            }
        )
        additional.extend(rows.values())
    return summaries, additional


def public_role(
    row: dict[str, Any], bindings: dict[str, dict[str, Any]], capture: str
) -> dict[str, Any]:
    wanted = identity(row)
    require(
        wanted["path"] in bindings, "Scientific product absent from retained capture"
    )
    binding = bindings[wanted["path"]]
    require(
        exact(identity(binding["original"]), wanted), "Scientific product pin differs"
    )
    member_name(binding["member"])
    require(
        binding["member"] == "payloads/" + wanted["sha256"],
        "Scientific member is not content-addressed",
    )
    return {
        "capture": capture,
        "member": binding["member"],
        "sha256": wanted["sha256"],
        "bytes": wanted["bytes"],
    }


def evidence_projection(
    observed: list[dict[str, Any]],
    watched: dict[str, Any],
    human_bindings: dict[str, dict[str, Any]],
    animal_bindings: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    require(
        len(observed) == 54
        and len(watched["watched_source_files"]) == 263
        and watched["all_first_party_origin_memberships_verified"] is True,
        "Complete current scientific observation/source scope required",
    )
    queries = []
    for row in observed:
        human = row["domain"] == "human"
        binding = human_bindings if human else animal_bindings
        capture = HUMAN_CAPTURE if human else ANIMAL_CAPTURE
        queries.append(
            {
                key: row[key]
                for key in (
                    "domain",
                    "species",
                    "country_query",
                    "records",
                    "whole_recursive_keysets",
                    "no_pollen_semantics_leakage",
                )
            }
            | {
                "products": {
                    role: public_role(pin, binding, capture)
                    for role, pin in row["products"].items()
                }
            }
        )
    return {
        "schema_version": "adna-current-human-animal-scientific-evidence.v1",
        "observation_identity": RESULT_IDENTITY,
        "source_epochs": {"human": HUMAN_SOURCE, "animal": ANIMAL_SOURCE},
        "current_queries": queries,
        "watched_source_correspondence": watched,
        "typed_record_fields": SCHEMA["typed_record_fields"],
        "current_default_CSV_fields": list(CURRENT_FIELDS),
        "current_software_domain_separation_observed": True,
        "four_source_owned_taxon_blocks": [list(row) for row in BLOCKED_TAXA],
        "generic_exports_relabelled_as_full_typed_science": False,
        "original_failed_native_stages": [0, 1],
        "original_failed_whole": 1,
        "earlier_partial_joint_result_rewritten": False,
        "historical_missing_native_receipts_recovered": False,
        "historical_saved_human_chronology_review_population": 1325,
        "missing_historical_backlink_digests": 3,
        "genotype_biology_rights_human_qualified_chronology_ecology_or_LRA_admitted": False,
        "publisher_ownership_changed": False,
    }


def human_context(
    repository: Path,
) -> tuple[dict[str, Any], Callable[[str], bytes], dict[str, Any]]:
    raw = physical(repository, HUMAN_CAPTURE).read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == HUMAN_CAPTURE_SHA,
        "Exact genuine human capture required",
    )
    packet = json_object(raw)
    root = (repository / HUMAN_CAPTURE).parent
    exact_tree(root, set(packet["members"]) | {"capture.json"}, {"payloads"})

    def read(name: str) -> bytes:
        member_name(name)
        return checked(
            repository,
            (root / name).relative_to(repository).as_posix(),
            packet["members"][name],
        )

    evidence = validate_human_packet(packet, read)
    return packet, read, evidence


def _validated_current_domain_evidence(
    repository: Path,
    owners: list[dict[str, Any]],
    earlier_human_evidence: JsonObject | None,
) -> JsonObject | None:
    present = [
        (repository / name).exists() or (repository / name).is_symlink()
        for name in (ANIMAL_CAPTURE, PROOF_ROOT, WITNESS)
    ]
    if not any(present):
        return None
    require(all(present), "Partial current animal/joint publication refused")
    publisher_contract(owners)
    for path in READERS:
        selected = [row for row in owners if path in row["paths"]]
        require(
            len(selected) == 1
            and selected[0]["owner_id"] == "publisher"
            and selected[0]["role"] == "publisher_partition",
            "Current observed route publisher contract differs",
        )
    require(
        earlier_human_evidence is not None
        and earlier_human_evidence["whole_ADNA_001_closed"] is False
        and earlier_human_evidence["publisher_entries_selected"] == 0,
        "Original human evidence and partial-result history required",
    )
    old_raw = physical(repository, OLD_WITNESS).read_bytes()
    require(
        hashlib.sha256(old_raw).hexdigest() == OLD_WITNESS_SHA,
        "Earlier partial joint observation changed",
    )
    old = json_object(old_raw)
    require(
        zero(old["actual_callback_exit"])
        and old["whole_ADNA_001_closed"] is False
        and old["saved_population_observation"][
            "fresh_current_animal_source_to_country_producer_executed"
        ]
        is False,
        "Earlier actual0/partialfalse observation changed",
    )
    failure = old["original_saved_failure_authority"]
    require(
        type(failure["original_whole_actual_exit"]) is int
        and failure["original_whole_actual_exit"] == 1
        and exact(failure["original_native_stages"], [0, 1])
        and failure["historical_six_stage_native_receipt_recovered"] is False,
        "Original failed native history was promoted",
    )
    animal, read_a, animal_evidence = animal_context(repository)
    human, read_h, human_evidence = human_context(repository)
    hb = {row["original"]["path"]: row for row in human["public_bindings"]}
    ab = {row["original"]["path"]: row for row in animal["public_bindings"]}

    def payload(row: dict[str, Any]) -> bytes:
        wanted = identity(row)
        matches = []
        for bindings, read in ((hb, read_h), (ab, read_a)):
            if wanted["path"] in bindings:
                binding = bindings[wanted["path"]]
                require(
                    exact(identity(binding["original"]), wanted),
                    "Required current source/product metadata identity differs",
                )
                matches.append(read(binding["member"]))
        require(
            bool(matches) and all(raw == matches[0] for raw in matches),
            "Required current public role absent or ambiguous",
        )
        return matches[0]

    documents = {}
    for prefix, packet in (("raw", human), ("animal", animal)):
        for role, target in (
            ("plan", "plan"),
            ("producer", "producer"),
            ("review", "review"),
        ):
            documents[prefix + "_" + target] = json_object(
                payload(packet["native_references"][role])
            )
    watched, _ = source_join(
        documents["raw_plan"],
        documents["animal_plan"],
        documents["raw_producer"],
        documents["animal_producer"],
        SCHEMA,
        payload,
    )
    require(
        len(watched["watched_source_files"]) == 263,
        "Exact current source resource population required",
    )
    source_names = {row["repository_path"] for row in watched["watched_source_files"]}
    opaque_names = original_opaque_cache_names(
        animal, documents["animal_plan"]["repository"]
    )
    current_source_namespace(repository, source_names, opaque_names)
    for row in watched["watched_source_files"]:
        name = row["repository_path"]
        p = PurePosixPath(name)
        require(
            not p.is_absolute() and ".." not in p.parts and p.as_posix() == name,
            "Source role must be repository-relative",
        )
        checked(repository, name, {"sha256": row["sha256"], "bytes": row["bytes"]})
    observed, _ = scan_products(products(documents), SCHEMA, payload)
    current_source_namespace(repository, source_names, opaque_names)
    projected = evidence_projection(observed, watched, hb, ab)
    witness = json_object(physical(repository, WITNESS).read_bytes())
    same_metadata(projected, witness)
    exact_tree(
        (repository / ANIMAL_CAPTURE).parent,
        set(animal["members"]) | {"capture.json"},
        {"payloads"},
    )
    exact_tree(
        (repository / HUMAN_CAPTURE).parent,
        set(human["members"]) | {"capture.json"},
        {"payloads"},
    )
    return {
        "schema_version": "adna-current-domain-portable-evidence.v1",
        "current_software_domain_separation_observed": True,
        "scientific_witness": {
            "path": WITNESS,
            "sha256": hashlib.sha256(
                physical(repository, WITNESS).read_bytes()
            ).hexdigest(),
        },
        "animal_capture_evidence": animal_evidence,
        "human_native_capture_evidence": human_evidence,
        "current_queries": 54,
        "current_products": 162,
        "source_candidates": [HUMAN_SOURCE, ANIMAL_SOURCE],
        "earlier_partial_joint_and_original_failed_native_preserved": True,
        "publisher_entries_selected": 0,
        "publisher_ownership_changed": False,
        "scientific_biology_rights_human_chronology_genotype_ecology_or_LRA_admitted": False,
    }


def validated_current_domain_evidence(
    repository: Path,
    owners: list[dict[str, Any]],
    earlier_human_evidence: JsonObject | None,
) -> JsonObject | None:
    """Validate portable current exports; select no publisher inventory entries."""
    try:
        return _validated_current_domain_evidence(
            repository, owners, earlier_human_evidence
        )
    except (KeyError, TypeError, ValueError, OSError) as error:
        raise ReportRebuildError(
            "Current human/animal source-domain evidence is malformed"
        ) from error


def zero(value: object) -> bool:
    return type(value) is int and value == 0


def current_source_namespace(
    repository: Path, expected_source_names: set[str], opaque_cache_names: set[str]
) -> None:
    prefix = "packages/bijux-pollenomics/src/bijux_pollenomics/adna/"
    selected = {name for name in expected_source_names if name.startswith(prefix)}
    require(
        bool(selected) and expected_source_names - selected == set(WATCHED_FILES),
        "Exact confined current ADNA/default-writer source namespace required",
    )
    require(
        all(
            name.startswith(prefix)
            and "/__pycache__/" in name
            and name.endswith(".pyc")
            for name in opaque_cache_names
        ),
        "Only original opaque bytecode names may be omitted",
    )
    root = repository / prefix
    require(
        root.is_dir()
        and root == root.resolve()
        and not any(p.is_symlink() for p in (root, *root.parents)),
        "Physical current ADNA namespace required",
    )
    directories = {
        parent.as_posix()
        for name in selected | opaque_cache_names
        for parent in PurePosixPath(name).parents
        if parent.as_posix().startswith(prefix.rstrip("/"))
    }
    actual: set[str] = set()
    pending = [root]
    while pending:
        for path in pending.pop().iterdir():
            name = path.relative_to(repository).as_posix()
            require(
                not path.is_symlink() and (path.is_file() or path.is_dir()),
                "Current ADNA source alias/special refused",
            )
            if path.is_dir():
                require(name in directories, "Unknown current ADNA source directory")
                pending.append(path)
            elif name in selected:
                actual.add(name)
            else:
                require(
                    name in opaque_cache_names,
                    "Current ADNA source/resource membership differs",
                )
    require(actual == selected, "Current ADNA source member omitted")
    for name in expected_source_names - selected:
        path = repository / name
        require(
            path.is_file()
            and path == path.resolve()
            and not any(p.is_symlink() for p in (path, *path.parents)),
            "Current default-writer source absent/aliased",
        )


def original_opaque_cache_names(
    packet: dict[str, Any], original_repository: str
) -> set[str]:
    result: set[str] = set()
    root = PurePosixPath(original_repository)
    for row in packet["original_source_join"]:
        if row["role"] != "bytecode_identity_only":
            continue
        path = PurePosixPath(row["original"]["path"])
        require(
            path.is_relative_to(root), "Original opaque cache escaped source repository"
        )
        name = path.relative_to(root).as_posix()
        if name.startswith("packages/bijux-pollenomics/src/bijux_pollenomics/adna/"):
            result.add(name)
    return result
