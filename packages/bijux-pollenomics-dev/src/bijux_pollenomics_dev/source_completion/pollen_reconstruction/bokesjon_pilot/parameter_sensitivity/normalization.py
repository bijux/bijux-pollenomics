"""Bind the original displayed parameters to authenticated common-reference metadata."""

from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

ROLES = ("author-parameter-binding", "parameter-correspondence", "parameter-candidates")
SCHEMAS = (
    "swedish-landclim-author-parameter-binding.v1",
    "landclim-author-published-parameter-correspondence.v1",
    "neotoma-landclim-parameter-candidates.v1",
)
PUBLIC_PREFIX = "docs/report/source-relations/neotoma/"
PPE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*\(\s*([0-9]+(?:\.[0-9]+)?)\s*\)\s*$")


def require(value: object, message: str) -> None:
    """Refuse an incompatible source contract without mutating its evidence."""
    if not value:
        raise ValueError(message)


def number(value: Any, *, positive: bool = False) -> Decimal:
    """Parse finite literal decimal metadata, excluding boolean values."""
    require(
        type(value) in (str, int, float), "Literal finite numeric metadata required"
    )
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("Invalid numeric metadata") from error
    require(
        result.is_finite() and (not positive or result > 0),
        "Finite positive parameter metadata required",
    )
    return result


def unique(rows: Any, key: str) -> dict[str, Any]:
    """Check the complete source correspondence axis before selecting two taxa."""
    require(type(rows) is list and len(rows) == 31, "Exact31-row source axis required")
    require(
        all(
            type(row) is dict and type(row.get(key)) is str and row[key] for row in rows
        ),
        "Literal source row names required",
    )
    result = {row[key]: row for row in rows}
    require(len(result) == 31, "Unique31-row source names required")
    return result


def declarations(scope: dict[str, Any]) -> dict[str, Any]:
    """Validate independent bridge pins without opening their declared locations."""
    pins = scope.get("normalization_evidence")
    if not isinstance(pins, dict) or set(pins) != set(ROLES):
        raise ValueError("All three independent normalization bridge reports required")
    for role in ROLES:
        pin = pins[role]
        require(
            pin.get("public_source_path") == PUBLIC_PREFIX + role + "/report.json"
            and pin.get("public_revision") == "c198c998a2d7b6866d6fd10869a0bbe7321ad1fe"
            and Path(pin["path"]).name == role + ".json"
            and type(pin["bytes"]) is int
            and 0 < pin["bytes"] <= 65536
            and re.fullmatch("[0-9a-f]{64}", pin["sha256"]) is not None,
            "Canonical independently pinned public report declaration required",
        )
    return dict(pins)


def bind(
    request: dict[str, Any],
    parameter_bytes: bytes,
    reference: dict[str, Any],
    buffers: dict[str, bytes],
    scope: dict[str, Any],
) -> dict[str, Any]:
    """Check authenticated buffers without opening paths or assigning SD laws."""
    pins = declarations(scope)
    require(
        type(buffers) is dict and set(buffers) == set(ROLES) | {"reference-source"},
        "Complete authenticated normalization input buffers required",
    )
    documents = {}
    for role, schema in zip(ROLES, SCHEMAS, strict=True):
        raw = buffers[role]
        pin = pins[role]
        require(
            type(raw) is bytes
            and len(raw) == pin["bytes"]
            and sha256(raw).hexdigest() == pin["sha256"],
            "Normalization report bytes differ from independent source hash",
        )
        document = json.loads(raw)
        require(
            document.get("schema_version") == schema,
            "Normalization source schema differs",
        )
        documents[role] = document
    authored, paired, candidates = (documents[role] for role in ROLES)
    for document, field in (
        (authored, "author_target_count"),
        (paired, "parameter_count"),
        (candidates, "parameter_row_count"),
    ):
        require(
            type(document.get(field)) is int and document[field] == 31,
            "Declared31-row source population differs",
        )
    expected_inputs = {
        pins[role]["public_source_path"]: {
            "path": pins[role]["public_source_path"],
            "sha256": pins[role]["sha256"],
            "bytes": pins[role]["bytes"],
        }
        for role in ("author-parameter-binding", "parameter-candidates")
    }
    require(
        type(paired.get("inputs")) is list
        and len(paired["inputs"]) == 2
        and {row.get("path"): row for row in paired["inputs"]} == expected_inputs,
        "Correspondence must bind exact author/published report paths, hashes and sizes",
    )
    author_rows = unique(authored["parameters"], "author_target")
    pairs = unique(paired["rows"], "author_target")
    published = unique(candidates["rows"], "parameter_source_name")
    require(
        set(author_rows) == set(pairs)
        and {row["published_parameter_name"] for row in pairs.values()}
        == set(published),
        "Source axes are missing, duplicated or assigned to another owner",
    )
    for target, author in author_rows.items():
        pair = pairs[target]
        row = published[pair["published_parameter_name"]]
        match = PPE.fullmatch(row["parameter_ppe_source_text"])
        if match is None:
            raise ValueError("Published nominal/SD display cell required")
        alpha = number(author["alpha_source_text"], positive=True)
        nominal = number(match[1], positive=True)
        require(
            alpha == number(pair["author_alpha"], positive=True)
            and nominal == number(pair["published_ppe"], positive=True)
            and number(pair["alpha_difference"]) == alpha - nominal
            and abs(alpha - nominal) <= Decimal("0.00050001"),
            "Author and published displayed nominal values do not correspond",
        )
        fsp = row["parameter_fsp_source_text"]
        footnote = fsp.endswith("*")
        fsp = number(fsp.removesuffix("*"), positive=True)
        require(
            fsp
            == number(author["fall_speed_source_text"], positive=True)
            == number(pair["author_vg"], positive=True)
            == number(pair["published_fsp"], positive=True)
            and pair["published_fsp_footnote"] is footnote,
            "Exact source fall-speed or footnote correspondence differs",
        )
    for target in ("Betula", "Ulmus", "Poaceae"):
        require(
            target in pairs and pairs[target]["published_parameter_name"] == target,
            "Literal selected/reference taxon identity required; no synonym mapping",
        )
    require(
        number(author_rows["Poaceae"]["alpha_source_text"])
        == number(pairs["Poaceae"]["published_ppe"])
        == 1,
        "Baseline source reference must be Poaceae RPP1",
    )
    packet = json.loads(parameter_bytes)
    require(
        packet.get("role") == "parameters"
        and packet.get("parameters") == request["parameters"],
        "Original selected parameter evidence must equal the authenticated request",
    )
    selected = {row["taxon"]: row for row in request["parameters"]}
    require(
        len(request["parameters"]) == 2 and set(selected) == {"Betula", "Ulmus"},
        "Unchanged conditional two-tree parameter axis required",
    )
    trace = []
    for target in ("Betula", "Ulmus"):
        active = selected[target]
        pair = pairs[target]
        require(
            number(active["ppe"], positive=True)
            == number(pair["published_ppe"], positive=True)
            and number(active["fallspeed_m_s"], positive=True)
            == number(pair["published_fsp"], positive=True),
            "Baseline modeled values must retain the published display and exact FSP",
        )
        trace.append(
            {
                "taxon": target,
                "modeled_ppe": active["ppe"],
                "published_ppe_source_text": pair["published_ppe"],
                "author_unrounded_alpha_source_text": pair["author_alpha"],
                "fallspeed_m_s": active["fallspeed_m_s"],
                "original_ppe_sd_unchanged": active["ppe_sd"],
            }
        )
    require(
        number(selected["Betula"]["ppe"]) == Decimal("5.106")
        and number(author_rows["Betula"]["alpha_source_text"]) == Decimal("5.10571")
        and number(author_rows["Betula"]["alpha_source_text"]).quantize(Decimal(".001"))
        == number(selected["Betula"]["ppe"]),
        "Explicit baseline displayed rounding must not substitute unrounded author alpha",
    )
    metadata = {Path(path).name: pin for path, pin in scope["metadata"].items()}
    require(
        set(metadata)
        == {"source.json", "original-study-estimates.csv", "synthesized-estimates.csv"},
        "Exact independently qualified2025metadata members required",
    )
    seen = reference.get("source_pins", [])
    require(
        len(seen) == 3
        and {pin["path"] for pin in seen} == set(metadata)
        and all(
            pin["sha256"] == metadata[pin["path"]]["sha256"]
            and pin["bytes"] == metadata[pin["path"]]["bytes"]
            for pin in seen
        ),
        "Adapted2025reference no longer has its independently bound source identities",
    )
    raw = buffers["reference-source"]
    pin = metadata["source.json"]
    require(
        type(raw) is bytes
        and len(raw) == pin["bytes"]
        and sha256(raw).hexdigest() == pin["sha256"],
        "2025source metadata identity differs",
    )
    declared = json.loads(raw)["statistical_semantics"]["rpp_units"]
    require(
        reference["reference_normalization"] == declared,
        "Reference normalization label differs from authenticated declaration",
    )
    rows = [
        row
        for row in reference["synthesized_rows"]
        if all(
            row.get(key) == value
            for key, value in {
                "taxon": "Poaceae",
                "taxonomic_level": "family",
                "region": "Europe",
                "source_workbook": "originals/synthesized-rpp.xlsx",
                "source_sheet": "Worksheet 1",
                "source_row": "81",
                "rpp_cell": "G81",
                "rpp_sd_cell": "H81",
            }.items()
        )
    ]
    require(
        len(rows) == 1
        and rows[0]["nominal_rpp_available"] is True
        and number(rows[0]["rpp"]) == 1,
        "Exact European2025Poaceae row81/G81 reference RPP1 required",
    )
    return {
        "reference_taxon": "Poaceae",
        "nominal_reference_rpp": "1",
        "source_reports": {
            role: {
                key: pins[role][key]
                for key in ("public_source_path", "public_revision", "sha256", "bytes")
            }
            for role in ROLES
        },
        "baseline_display_trace": trace,
        "baseline_rounding": {
            "Betula_modeled": "5.106",
            "Betula_author_unrounded": "5.10571",
            "substitution_performed": False,
        },
        "reference_normalization_declaration": declared,
        "europe2025_reference_row": rows[0],
        "source_sd_correspondence_not_used": {
            "sd_within_display_count": paired.get("sd_within_display_count"),
            "sd_exceptions": paired.get("sd_exceptions", []),
            "nominal_scope_does_not_require_sd_equality": True,
        },
        "native2025_fall_speed_used": False,
        "SD_law_admitted": False,
        "scope": "Shared nominal Poaceae scale only; mixed-source two-tree contrast, no applicability, full-panel denominator or scientific admission.",
    }
