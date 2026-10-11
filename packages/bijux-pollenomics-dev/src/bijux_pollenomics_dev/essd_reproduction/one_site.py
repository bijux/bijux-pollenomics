"""Build the bounded WHH05 author-example input slice.

This module authenticates and reconciles one row already prepared by the
LandClim II authors.  It deliberately does not execute REVEALS, infer LOVE
inputs, compare numerical estimates, or admit the material to another source
family.  The returned document is an input-lineage record, not a scientific
result.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
from typing import cast

JsonObject = dict[str, object]

SCHEMA_VERSION = "essd-whh05-author-example-input-slice.v1"
AUTHOR_REPOSITORY = "rmfyfe/landclimII"
AUTHOR_COMMIT = "57ead2e2fcc493d099be4e5a3092fc396e1c3d3a"
AUTHOR_ARCHIVE_SHA256 = (
    "cd6cc688e6c44dd61d0ed038f53d118f4aade0696c37dc6174d613a38097bb38"
)

_EXPECTED_FILES: dict[str, tuple[str, int, str]] = {
    "site_metadata": (
        "site.metadata.csv",
        1019,
        "72949e9e3faf417be0b7425fc111a9638b37c4a38aab8f8d82e0c3d8739da2de",
    ),
    "raw_counts": (
        "input/WHH05.csv",
        1037,
        "977b32b96578aeb701288e77e37ab137e0475acd99274ddbdcc05180a8a99469",
    ),
    "prepared_counts": (
        "run.REVEALS.files/LRAready_WHH05.csv",
        2309,
        "298b66d7033703ce42d27f933b4d3ccec3a16f68b35a6fbf7a61806c01c88273",
    ),
    "time_window_boundaries": (
        "bins.csv",
        130,
        "62cac73bafacb8be8d8b7007e9871494024e661ab1a2f28774dcf7cb7046a71f",
    ),
    "time_window_lookup": (
        "TWlookup.csv",
        200,
        "888a2d5d035c8a49bd957917ca0658bb08824240ac15c1da4b717c633ddae3dd",
    ),
    "taxon_lookup": (
        "LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv",
        329074,
        "3a745f9b7606e5d0b59feaba2683b930c8d3990e4810f8217b69160a29a1b507",
    ),
    "ppe_means": (
        "run.REVEALS.files/av-RPP.all.landclimII.csv",
        772,
        "066ebadbe6ab10aead80c74a184284e05b9db3cd1f5daff04249596170a663e2",
    ),
    "ppe_covariance": (
        "run.REVEALS.files/avar-RPP.all.landclimII.csv",
        2977,
        "8821de94682c454e3a751897b487c8bf1612cf60994dc6246fb33284a73e9918",
    ),
    "historical_r_source": (
        "run.REVEALS.files/LRA-REVEALS-release.R",
        14501,
        "7675b6e615cddba328bad506692b3a6a31e00d9273cef5ad4641a1737fddfd87",
    ),
}

_RAW_ID_COLUMNS = ("depth", "age.cal.BP")
_RAW_SUM_COLUMN = "Sum"
_RAW_NAMED_TAXON_COUNT = 30
_PREPARED_TAXON_COUNT = 31
_SOURCE_AGE_CAL_BP = 1320
_WINDOW_ID = 5
_WINDOW_LABEL_BP = 1500
_WINDOW_YOUNGER_BP = 1250
_WINDOW_OLDER_BP = 1750

_RETAINED_POSITIVE_CROSSWALK = {
    "Alnus  ": "Alnus.glutinosa",
    "Betula  ": "Betula",
    "Corylus  ": "Corylus.avellana",
    "Pinus  ": "Pinus",
    "Quercus  ": "Quercus.deciduous",
    "Ericaceae  ": "Ericaceae",
    "Calluna  ": "Calluna.vulgaris",
    "Poaceae  ": "Poaceae",
    "Cyperaceae  ": "Cyperaceae",
    "Plantago lanceolata ": "Plantago.lanceolata.type",
}
_EXCLUDED_POSITIVE_LABELS = (
    "Centaurea nigra ",
    "Lactuceae  ",
    "Ranunculus acris type",
    "Potentilla type ",
)


class OneSiteExampleError(ValueError):
    """Raised when the pinned author example no longer satisfies its contract."""


@dataclass(frozen=True, slots=True)
class OneSiteExampleSlice:
    """A deterministic, content-addressed one-site input-lineage document."""

    canonical_bytes: bytes

    def payload(self) -> JsonObject:
        """Return a fresh JSON object so callers cannot mutate the record."""
        value = json.loads(self.canonical_bytes)
        if not isinstance(value, dict):  # pragma: no cover - constructor invariant
            raise OneSiteExampleError("one-site document is not a JSON object")
        return cast(JsonObject, value)

    @property
    def sha256(self) -> str:
        """Return the digest of the canonical input-lineage document."""
        return hashlib.sha256(self.canonical_bytes).hexdigest()


def validate_host_basin_diameter(
    *, source_radius_m: int, host_basin_diameter_m: int
) -> None:
    """Reject passing an author radius directly to a host diameter field."""
    if type(source_radius_m) is not int or source_radius_m <= 0:
        raise OneSiteExampleError(
            "source radius must be a positive integer metre value"
        )
    if type(host_basin_diameter_m) is not int or host_basin_diameter_m <= 0:
        raise OneSiteExampleError(
            "host basin diameter must be a positive integer metre value"
        )
    expected = source_radius_m * 2
    if host_basin_diameter_m != expected:
        raise OneSiteExampleError(
            "host basin_diameter_m must equal twice the author radius: "
            f"expected {expected}, observed {host_basin_diameter_m}"
        )


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _read_pinned_inputs(
    source_root: Path,
) -> tuple[dict[str, bytes], list[JsonObject]]:
    if not source_root.is_dir():
        raise OneSiteExampleError(
            f"author source root is not a directory: {source_root}"
        )
    content: dict[str, bytes] = {}
    identities: list[JsonObject] = []
    for role, identity in _EXPECTED_FILES.items():
        relative_path, expected_bytes, expected_sha256 = identity
        path = source_root / relative_path
        if path.is_symlink() or not path.is_file():
            raise OneSiteExampleError(
                f"pinned input is absent or symlinked: {relative_path}"
            )
        observed = path.read_bytes()
        observed_sha256 = hashlib.sha256(observed).hexdigest()
        if len(observed) != expected_bytes or observed_sha256 != expected_sha256:
            raise OneSiteExampleError(
                f"pinned input identity mismatch for {relative_path}: "
                f"expected {expected_bytes} bytes/{expected_sha256}, "
                f"observed {len(observed)} bytes/{observed_sha256}"
            )
        content[role] = observed
        identities.append(
            {
                "role": role,
                "path": relative_path,
                "byte_count": expected_bytes,
                "sha256": expected_sha256,
            }
        )
    return content, identities


def _csv_rows(content: bytes, name: str) -> list[list[str]]:
    try:
        rows = list(csv.reader(io.StringIO(content.decode("utf-8-sig"), newline="")))
    except (UnicodeDecodeError, csv.Error) as error:
        raise OneSiteExampleError(f"cannot parse {name} as UTF-8 CSV") from error
    if not rows:
        raise OneSiteExampleError(f"{name} is empty")
    return rows


def _integer(value: str, locator: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise OneSiteExampleError(
            f"expected integer at {locator}: {value!r}"
        ) from error
    if str(parsed) != value or parsed < 0:
        raise OneSiteExampleError(
            f"expected canonical non-negative integer at {locator}: {value!r}"
        )
    return parsed


def _signed_integer(value: str, locator: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise OneSiteExampleError(
            f"expected signed integer at {locator}: {value!r}"
        ) from error
    if str(parsed) != value:
        raise OneSiteExampleError(
            f"expected canonical signed integer at {locator}: {value!r}"
        )
    return parsed


def _raw_projection(content: bytes) -> JsonObject:
    rows = _csv_rows(content, "input/WHH05.csv")
    header = rows[0]
    if (
        tuple(header[:2]) != _RAW_ID_COLUMNS
        or header[-1] != _RAW_SUM_COLUMN
        or len(header[2:-1]) != _RAW_NAMED_TAXON_COUNT
        or len(set(header[2:-1])) != _RAW_NAMED_TAXON_COUNT
    ):
        raise OneSiteExampleError(
            "WHH05 raw header must contain two identity columns, 30 distinct "
            "named taxa, and one separate declared Sum field"
        )
    matches = [row for row in rows[1:] if len(row) == len(header) and row[1] == "1320"]
    if len(matches) != 1:
        raise OneSiteExampleError("WHH05 must contain one age.cal.BP=1320 row")
    row = matches[0]
    if row[0] != "16":
        raise OneSiteExampleError("WHH05 age.cal.BP=1320 must retain source depth 16")
    named_counts = {
        label: _integer(value, f"input/WHH05.csv#age.cal.BP=1320/{label!r}")
        for label, value in zip(header[2:-1], row[2:-1], strict=True)
    }
    declared_sum = _integer(row[-1], "input/WHH05.csv#age.cal.BP=1320/Sum")
    if sum(named_counts.values()) != declared_sum or declared_sum != 301:
        raise OneSiteExampleError(
            "WHH05 raw named-taxon counts must sum exactly to 301"
        )
    positive = {label: count for label, count in named_counts.items() if count > 0}
    expected_positive = set(_RETAINED_POSITIVE_CROSSWALK) | set(
        _EXCLUDED_POSITIVE_LABELS
    )
    if set(positive) != expected_positive:
        raise OneSiteExampleError("WHH05 positive raw-taxon labels changed")
    return {
        "source_locator": "input/WHH05.csv#age.cal.BP=1320",
        "depth_raw": "16",
        "source_age_raw": "1320",
        "source_age_type": "cal BP",
        "measurement_kind": "count",
        "is_percentage": False,
        "named_taxon_count": len(named_counts),
        "count_field_count_including_declared_sum": len(named_counts) + 1,
        "declared_sum_is_taxon": False,
        "declared_sum": declared_sum,
        "positive_named_taxon_count": len(positive),
        "positive_named_taxa": [
            {"source_label_raw": label, "count": positive[label]}
            for label in header[2:-1]
            if label in positive
        ],
        "named_counts": named_counts,
    }


def _prepared_projection(content: bytes) -> JsonObject:
    rows = _csv_rows(content, "run.REVEALS.files/LRAready_WHH05.csv")
    header = rows[0]
    if not header or header[0] != "TW" or len(set(header[1:])) != len(header[1:]):
        raise OneSiteExampleError("WHH05 prepared time-window header is invalid")
    try:
        column = header.index(str(_WINDOW_LABEL_BP))
    except ValueError as error:
        raise OneSiteExampleError(
            "WHH05 prepared file lacks time-window label 1500"
        ) from error
    if len(rows) != _PREPARED_TAXON_COUNT + 3:
        raise OneSiteExampleError("WHH05 prepared file must contain exactly 31 taxa")
    if rows[1][0] != "radius" or rows[2][0] != "model":
        raise OneSiteExampleError("WHH05 prepared radius/model rows changed")
    radius = _integer(rows[1][column], "LRAready_WHH05.csv#radius/TW=1500")
    model = _integer(rows[2][column], "LRAready_WHH05.csv#model/TW=1500")
    taxa = rows[3:]
    if any(len(row) != len(header) for row in taxa):
        raise OneSiteExampleError("WHH05 prepared taxon row width changed")
    labels = [row[0] for row in taxa]
    if len(set(labels)) != _PREPARED_TAXON_COUNT:
        raise OneSiteExampleError("WHH05 prepared taxa are not 31 distinct labels")
    counts = {
        row[0]: _integer(row[column], f"LRAready_WHH05.csv#{row[0]}/TW=1500")
        for row in taxa
    }
    positive = {label: value for label, value in counts.items() if value > 0}
    if sum(counts.values()) != 297 or len(positive) != 10:
        raise OneSiteExampleError(
            "WHH05 prepared TW=1500 must total 297 across 10 positive taxa"
        )
    return {
        "source_locator": "run.REVEALS.files/LRAready_WHH05.csv#TW=1500",
        "taxon_count": len(taxa),
        "measurement_kind": "count",
        "is_percentage": False,
        "total_count": sum(counts.values()),
        "positive_taxon_count": len(positive),
        "positive_counts": positive,
        "all_counts": counts,
        "author_radius_m": radius,
        "author_model_code": model,
    }


def _window_projection(boundaries_content: bytes, lookup_content: bytes) -> JsonObject:
    boundaries = [
        _signed_integer(row[0], f"bins.csv#{index + 1}")
        for index, row in enumerate(_csv_rows(boundaries_content, "bins.csv"))
    ]
    lookup = _csv_rows(lookup_content, "TWlookup.csv")
    if len(boundaries) != 26 or lookup[0] != ["TW", "class"] or len(lookup) != 26:
        raise OneSiteExampleError("TWlookup.csv header changed")
    matches = [row for row in lookup[1:] if row == ["5", "1500"]]
    if len(matches) != 1:
        raise OneSiteExampleError("time-window 5 must have repository label 1500")
    younger = boundaries[_WINDOW_ID - 1]
    older = boundaries[_WINDOW_ID]
    if (younger, older) != (_WINDOW_YOUNGER_BP, _WINDOW_OLDER_BP):
        raise OneSiteExampleError("time-window 5 must retain [1250,1750) boundaries")
    if not younger <= _SOURCE_AGE_CAL_BP < older:
        raise OneSiteExampleError("source age 1320 cal BP no longer falls in window 5")
    if _SOURCE_AGE_CAL_BP == _WINDOW_LABEL_BP:
        raise OneSiteExampleError("source age must not be conflated with bin label")
    return {
        "repository_window_id": _WINDOW_ID,
        "younger_boundary_bp": younger,
        "older_boundary_bp": older,
        "interval_notation": "[1250,1750)",
        "repository_window_label_bp": _WINDOW_LABEL_BP,
        "source_age_cal_bp": _SOURCE_AGE_CAL_BP,
        "source_age_equals_window_label": False,
        "posture": (
            "source sample age is distinct from the repository bin support and label"
        ),
    }


def _site_projection(content: bytes) -> JsonObject:
    rows = _csv_rows(content, "site.metadata.csv")
    if rows[0] != [
        "metadata",
        "filename",
        "SiteName",
        "model",
        "radius",
        "londd",
        "latdd",
        "LCGRID_ID",
    ]:
        raise OneSiteExampleError("site.metadata.csv header changed")
    matches = [row for row in rows[1:] if len(row) == 8 and row[1] == "WHH05"]
    if len(matches) != 1:
        raise OneSiteExampleError("site.metadata.csv must contain one WHH05 row")
    row = matches[0]
    radius = _integer(row[4], "site.metadata.csv#WHH05/radius")
    model = _integer(row[3], "site.metadata.csv#WHH05/model")
    if radius != 150 or model != 2 or row[7] != "512":
        raise OneSiteExampleError("WHH05 site metadata identity changed")
    host_diameter = radius * 2
    validate_host_basin_diameter(
        source_radius_m=radius, host_basin_diameter_m=host_diameter
    )
    return {
        "site_id": "WHH05",
        "site_name_raw": row[2],
        "longitude_raw": row[5],
        "latitude_raw": row[6],
        "landclim_grid_id_raw": row[7],
        "author_model_code": model,
        "author_radius_m": radius,
        "host_basin_diameter_m": host_diameter,
        "author_radius_may_be_used_as_host_diameter": False,
    }


def _ppe_projection(mean_content: bytes, covariance_content: bytes) -> JsonObject:
    means = _csv_rows(mean_content, "av-RPP.all.landclimII.csv")
    covariance = _csv_rows(covariance_content, "avar-RPP.all.landclimII.csv")
    if len(means) != 32 or means[0] != ["A.series", "alpha", "vg"]:
        raise OneSiteExampleError("PPE mean table must retain 31 parameter taxa")
    if len(covariance) != 32 or any(len(row) != 32 for row in covariance):
        raise OneSiteExampleError("PPE covariance table must retain a 31 by 31 matrix")
    if [row[0] for row in means[1:]] != covariance[0][1:]:
        raise OneSiteExampleError("PPE mean/covariance taxon order changed")
    if [row[0] for row in covariance[1:]] != covariance[0][1:]:
        raise OneSiteExampleError("PPE covariance row/column labels differ")
    return {
        "parameter_taxon_count": 31,
        "mean_table_row_count": 31,
        "covariance_shape": [31, 31],
        "values_reinterpreted": False,
        "scientific_adequacy_approved": False,
    }


def _reconciliation(raw: JsonObject, prepared: JsonObject) -> JsonObject:
    raw_counts = cast(dict[str, int], raw["named_counts"])
    prepared_counts = cast(dict[str, int], prepared["all_counts"])
    retained = []
    for source_label, prepared_label in _RETAINED_POSITIVE_CROSSWALK.items():
        source_count = raw_counts[source_label]
        prepared_count = prepared_counts[prepared_label]
        if source_count <= 0 or source_count != prepared_count:
            raise OneSiteExampleError(
                f"retained WHH05 count changed for {source_label!r}/{prepared_label!r}"
            )
        retained.append(
            {
                "source_label_raw": source_label,
                "prepared_label": prepared_label,
                "count": source_count,
            }
        )
    exclusions = []
    for source_label in _EXCLUDED_POSITIVE_LABELS:
        count = raw_counts[source_label]
        if count != 1:
            raise OneSiteExampleError(
                f"WHH05 explicit exclusion changed for {source_label!r}"
            )
        exclusions.append(
            {
                "source_label_raw": source_label,
                "count": count,
                "reason_code": "absent_from_author_prepared_positive_projection",
                "ecological_judgment_asserted": False,
            }
        )
    raw_total = cast(int, raw["declared_sum"])
    prepared_total = cast(int, prepared["total_count"])
    excluded_total = sum(cast(int, row["count"]) for row in exclusions)
    if raw_total != prepared_total + excluded_total:
        raise OneSiteExampleError("WHH05 reconciliation must be 301 = 297 + 4")
    return {
        "equation": "301 raw = 297 prepared + 4 explicitly enumerated exclusions",
        "raw_declared_total": raw_total,
        "prepared_total": prepared_total,
        "explicit_exclusion_count": len(exclusions),
        "explicit_excluded_total": excluded_total,
        "retained_positive_crosswalk": retained,
        "explicit_exclusions": exclusions,
    }


def build_whh05_one_site_slice(source_root: Path) -> OneSiteExampleSlice:
    """Authenticate and reconcile the pinned WHH05/TW=1500 author example."""
    content, identities = _read_pinned_inputs(source_root)
    raw = _raw_projection(content["raw_counts"])
    prepared = _prepared_projection(content["prepared_counts"])
    window = _window_projection(
        content["time_window_boundaries"], content["time_window_lookup"]
    )
    site = _site_projection(content["site_metadata"])
    ppe = _ppe_projection(content["ppe_means"], content["ppe_covariance"])
    if (
        prepared["author_radius_m"] != site["author_radius_m"]
        or prepared["author_model_code"] != site["author_model_code"]
    ):
        raise OneSiteExampleError("prepared and metadata radius/model values differ")
    reconciliation = _reconciliation(raw, prepared)
    payload: JsonObject = {
        "schema_version": SCHEMA_VERSION,
        "scope": "single_site_author_example_input_reconstruction",
        "source": {
            "repository": AUTHOR_REPOSITORY,
            "commit": AUTHOR_COMMIT,
            "archive_sha256": AUTHOR_ARCHIVE_SHA256,
            "input_files": identities,
        },
        "selection": {
            "site": site,
            "raw_observation": raw,
            "prepared_observation": prepared,
            "repository_time_window": window,
            "ppe_parameters": ppe,
        },
        "denominators": {
            "raw_named_taxa": raw["named_taxon_count"],
            "raw_count_fields_including_declared_sum": raw[
                "count_field_count_including_declared_sum"
            ],
            "prepared_taxa": prepared["taxon_count"],
            "raw_positive_named_taxa": raw["positive_named_taxon_count"],
            "prepared_positive_taxa": prepared["positive_taxon_count"],
        },
        "count_reconciliation": reconciliation,
        "historical_r_execution": {
            "performed": False,
            "bounded_inputs_authenticated": True,
            "isolated_private_diagnostic_call_technically_possible": True,
            "output_must_be_treated_as_unvalidated_candidate": True,
            "unchanged_unmanaged_historical_call_safe": False,
            "managed_isolation_preconditions": [
                "network disabled",
                "dependencies preinstalled and version-recorded",
                "historical source auto-install branches prevented",
                "outputs retained as private diagnostic candidates",
            ],
            "redistribution_or_publication_rights_cleared": False,
            "native_r_parity_certified": False,
            "historical_source_behavior_approved": False,
        },
        "claims": {
            "single_site_author_example_input_reconstructed": True,
            "whole_paper_reproduction": False,
            "rootsi_admission": False,
            "love_reconstruction": False,
            "multi_site_reconstruction": False,
            "native_r_parity": False,
            "ecological_accuracy": False,
            "publication_or_redistribution_rights_cleared": False,
            "scientifically_approved": False,
            "scientific_acceptance": "not_evaluated",
        },
    }
    return OneSiteExampleSlice(canonical_bytes=_canonical_bytes(payload))
