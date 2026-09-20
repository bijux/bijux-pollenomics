"""Digest-bound HYDE provider declarations; conflicts never grant admission."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from ...quarantine import IntakeRefusal
from .contracts import checked_path, digest, encode, sha256

SCHEMA = "hyde-native-metadata-review.v1"
_TEXT_LIMIT = 64 * 1024
_CUSTODY_LIMIT = 64 * 1024
_CUSTODY_FILES_LIMIT = 512 * 1024
_HEADER_LIMIT = 12 * 1024 * 1024
_SCENARIOS = ("base", "lower", "upper")


@dataclass(frozen=True)
class MetadataClaim:
    """One source-attributed declaration, retained without reconciliation."""

    topic: str
    source: str
    value: str
    context: str

    def payload(self) -> dict[str, str]:
        return {
            "topic": self.topic,
            "source": self.source,
            "value": self.value,
            "context": self.context,
        }


@dataclass(frozen=True)
class HydeMetadataReview:
    """Deterministic conflict review that is structurally unable to admit HYDE."""

    input_files: tuple[tuple[str, int, str], ...]
    custody_manifest_sha256: str
    dataset_inventory_sha256: str
    custody_counts: tuple[tuple[str, int], ...]
    claims: tuple[MetadataClaim, ...]
    scenarios: tuple[tuple[str, int], ...]
    conflicts: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA,
            "inputs": [
                {"role": role, "bytes": size, "sha256": checksum}
                for role, size, checksum in self.input_files
            ],
            "custody": {
                "manifest_sha256": self.custody_manifest_sha256,
                "dataset_inventory_sha256": self.dataset_inventory_sha256,
                "counts": dict(self.custody_counts),
            },
            "claims": [claim.payload() for claim in self.claims],
            "scenario_semantics": {
                "labels": [name for name, _ in self.scenarios],
                "netcdf_header_counts": dict(self.scenarios),
                "role": "provider_estimate_scenarios",
                "confidence_bounds_status": "not_declared",
                "pointwise_ordering_contract": "none",
            },
            "conflicts": list(self.conflicts),
            "admission": {
                "native_release_status": "refused_pending_review",
                "scientific_acceptance": "not_evaluated",
                "public_release_allowed": False,
                "country_projection_allowed": False,
                "canonical_calendar_conversion_allowed": False,
                "required_reviews": [
                    "qualified_release_identity",
                    "qualified_release_specific_rights",
                    "native_calendar_and_0ad_interpretation",
                    "coverage_end_year",
                    "scenario_uncertainty_semantics",
                ],
            },
        }

    @property
    def canonical_bytes(self) -> bytes:
        return encode(self.payload())

    @property
    def sha256(self) -> str:
        return sha256(self.canonical_bytes)


def review_hyde_native_metadata(
    *,
    license_path: Path,
    license_sha256: str,
    readme_path: Path,
    readme_sha256: str,
    yoda_path: Path,
    yoda_sha256: str,
    custody_receipt_path: Path,
    custody_receipt_sha256: str,
    custody_files_path: Path,
    custody_files_sha256: str,
    netcdf_headers_path: Path,
    netcdf_headers_sha256: str,
) -> HydeMetadataReview:
    """Review six compact, pinned inputs without opening native HYDE payloads.

    The provider license, README and Yoda records are deliberately kept as
    separate authorities. The historical custody receipt binds the external
    release identity, while retained NetCDF headers expose native declarations.
    Conflicts are reported, never resolved by precedence or majority vote.
    """
    contents = {
        "provider_license": _read_pinned(
            license_path, license_sha256, _TEXT_LIMIT, "provider_license"
        ),
        "provider_readme": _read_pinned(
            readme_path, readme_sha256, _TEXT_LIMIT, "provider_readme"
        ),
        "provider_yoda": _read_pinned(
            yoda_path, yoda_sha256, _TEXT_LIMIT, "provider_yoda"
        ),
        "custody_receipt": _read_pinned(
            custody_receipt_path,
            custody_receipt_sha256,
            _CUSTODY_LIMIT,
            "custody_receipt",
        ),
        "custody_files": _read_pinned(
            custody_files_path,
            custody_files_sha256,
            _CUSTODY_FILES_LIMIT,
            "custody_files",
        ),
        "netcdf_headers": _read_pinned(
            netcdf_headers_path,
            netcdf_headers_sha256,
            _HEADER_LIMIT,
            "netcdf_headers",
        ),
    }
    license_text = _utf8(contents["provider_license"], "provider_license")
    readme = _utf8(contents["provider_readme"], "provider_readme")
    yoda = _json_object(contents["provider_yoda"], "provider_yoda")
    custody = _json_object(contents["custody_receipt"], "custody_receipt")
    custody_files = _json_array(contents["custody_files"], "custody_files")
    headers = _json_array(contents["netcdf_headers"], "netcdf_headers")

    claims = _provider_claims(license_text, readme, yoda)
    claims.extend(_custody_file_claims(custody_files))
    header_claims, scenarios = _header_claims(headers)
    claims.extend(header_claims)
    counts = _custody_counts(custody)
    custody_header_count = counts.get("netcdf_named_file_count")
    conflicts = {
        "calendar_mapping_unresolved",
        "coverage_end_year_conflict",
        "license_declaration_conflict",
        "release_identity_conflict",
        "scenario_uncertainty_semantics_unresolved",
        "zero_ad_calendar_interpretation_unresolved",
    }
    if custody_header_count != len(headers):
        conflicts.add("custody_netcdf_header_count_conflict")
    if counts.get("dataset_file_count") != len(custody_files):
        conflicts.add("custody_dataset_file_count_conflict")
    if tuple(name for name, _ in scenarios) != _SCENARIOS:
        conflicts.add("scenario_inventory_conflict")
    return HydeMetadataReview(
        input_files=tuple(
            (role, len(content), sha256(content))
            for role, content in sorted(contents.items())
        ),
        custody_manifest_sha256=digest(custody.get("manifest_sha256")),
        dataset_inventory_sha256=digest(custody.get("dataset_inventory_sha256")),
        custody_counts=tuple(sorted(counts.items())),
        claims=tuple(sorted(claims, key=lambda claim: tuple(vars(claim).values()))),
        scenarios=scenarios,
        conflicts=tuple(sorted(conflicts)),
    )


def _read_pinned(path: Path, expected: str, limit: int, role: str) -> bytes:
    digest(expected)
    source = checked_path(path)
    if source.is_symlink() or not source.is_file():
        raise IntakeRefusal("hyde_metadata_input_invalid", role)
    try:
        with source.open("rb") as handle:
            content = handle.read(limit + 1)
    except OSError as exc:
        raise IntakeRefusal("hyde_metadata_input_unreadable", role) from exc
    if len(content) > limit:
        raise IntakeRefusal("hyde_metadata_input_limit", role)
    if sha256(content) != expected:
        raise IntakeRefusal("hyde_metadata_digest_mismatch", role)
    return content


def _utf8(content: bytes, role: str) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IntakeRefusal("hyde_metadata_text_invalid", role) from exc


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IntakeRefusal("hyde_metadata_json_duplicate_key", key)
        result[key] = value
    return result


def _json(content: bytes, role: str) -> object:
    try:
        return json.loads(_utf8(content, role), object_pairs_hook=_unique)
    except (TypeError, ValueError) as exc:
        if isinstance(exc, IntakeRefusal):
            raise
        raise IntakeRefusal("hyde_metadata_json_invalid", role) from exc


def _json_object(content: bytes, role: str) -> dict[str, Any]:
    value = _json(content, role)
    if not isinstance(value, Mapping):
        raise IntakeRefusal("hyde_metadata_json_object_required", role)
    return dict(value)


def _json_array(content: bytes, role: str) -> list[object]:
    value = _json(content, role)
    if not isinstance(value, list) or not value:
        raise IntakeRefusal("hyde_metadata_json_array_required", role)
    return list(value)


def _required_text(value: object, role: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise IntakeRefusal("hyde_metadata_claim_invalid", role)
    return value


def _provider_claims(
    license_text: str, readme: str, yoda: dict[str, Any]
) -> list[MetadataClaim]:
    if "Attribution-NonCommercial 4.0 International" not in license_text:
        raise IntakeRefusal("hyde_metadata_claim_missing", "provider license")
    yoda_license = _required_text(yoda.get("License"), "yoda License")
    description = _required_text(yoda.get("Description"), "yoda Description")
    normalized_readme = " ".join(readme.split())
    required_readme = (
        "CC BY 3.0",
        "Baseline estimate scenario",
        "Lower estimate scenario",
        "Upper estimate scenario",
    )
    if any(token not in normalized_readme for token in required_readme):
        raise IntakeRefusal("hyde_metadata_claim_missing", "provider README")
    readme_release = _matched_claim(
        normalized_readme,
        r"README release HYDE version ([0-9]+(?:\.[0-9]+)+)",
        "provider README title release",
    )
    readme_scenario_release = _matched_claim(
        normalized_readme,
        r"The HYDE ([0-9]+(?:\.[0-9]+)+) release contains",
        "provider README scenario release",
    )
    yoda_release = _matched_claim(
        description,
        r"This HYDE version ([0-9]+(?:\.[0-9]+)+)",
        "provider Yoda release",
    )
    claims = [
        MetadataClaim(
            "license",
            "provider_license",
            "CC-BY-NC-4.0",
            "full supplied license text",
        ),
        MetadataClaim("license", "provider_readme", "CC-BY-3.0", "disclaimer"),
        MetadataClaim("license", "provider_yoda", yoda_license, "License"),
        MetadataClaim("release", "provider_readme", readme_release, "title"),
        MetadataClaim(
            "release",
            "provider_readme",
            readme_scenario_release,
            "scenario section",
        ),
        MetadataClaim("release", "provider_yoda", yoda_release, "Description"),
    ]
    for source, text in (("provider_readme", readme), ("provider_yoda", description)):
        for context, pattern in (
            ("period covered", r"period covered is .*? to (\d{4}) CE"),
            ("extension", r"Extension of the database to year (\d{4})"),
        ):
            match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if match is None:
                raise IntakeRefusal(
                    "hyde_metadata_claim_missing", f"{source} {context}"
                )
            claims.append(MetadataClaim("coverage_end_year", source, match[1], context))
    return claims


def _matched_claim(text: str, pattern: str, role: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        raise IntakeRefusal("hyde_metadata_claim_missing", role)
    return match[1]


def _custody_file_claims(files: list[object]) -> list[MetadataClaim]:
    zero_ad_paths = []
    for index, value in enumerate(files):
        if not isinstance(value, Mapping):
            raise IntakeRefusal("hyde_metadata_custody_file_invalid", str(index))
        path = _required_text(value.get("path"), f"custody file {index} path")
        if re.search(r"(?:^|/)0AD(?:_|\.)", path):
            zero_ad_paths.append(path)
    if not zero_ad_paths:
        raise IntakeRefusal("hyde_metadata_claim_missing", "custody 0AD path")
    return [
        MetadataClaim(
            "calendar_label",
            "custody_files",
            "0AD",
            f"{len(zero_ad_paths)} native paths; interpretation not declared",
        )
    ]


def _header_claims(
    headers: list[object],
) -> tuple[list[MetadataClaim], tuple[tuple[str, int], ...]]:
    versions: Counter[str] = Counter()
    descriptions: Counter[str] = Counter()
    licenses: Counter[str] = Counter()
    calendars: Counter[str] = Counter()
    time_units: Counter[str] = Counter()
    scenarios: Counter[str] = Counter()
    for index, value in enumerate(headers):
        if not isinstance(value, Mapping):
            raise IntakeRefusal("hyde_metadata_header_invalid", str(index))
        row = dict(value)
        path = _required_text(row.get("path"), f"netcdf header {index} path")
        attributes = row.get("attributes")
        variables = row.get("variables")
        if not isinstance(attributes, Mapping) or not isinstance(variables, Mapping):
            raise IntakeRefusal("hyde_metadata_header_invalid", path)
        time = variables.get("time")
        if not isinstance(time, Mapping) or not isinstance(
            time.get("attributes"), Mapping
        ):
            raise IntakeRefusal("hyde_metadata_header_invalid", f"{path} time")
        time_attributes = time["attributes"]
        assert isinstance(time_attributes, Mapping)
        versions[_required_text(attributes.get("version"), f"{path} version")] += 1
        descriptions[
            _required_text(attributes.get("description"), f"{path} description")
        ] += 1
        licenses[_required_text(attributes.get("license"), f"{path} license")] += 1
        calendars[
            _required_text(time_attributes.get("calendar"), f"{path} calendar")
        ] += 1
        time_units[
            _required_text(time_attributes.get("units"), f"{path} time units")
        ] += 1
        found = re.search(r"gbc\d+_[^/]+_(base|lower|upper)/NetCDF/", path)
        if found is None:
            raise IntakeRefusal("hyde_metadata_scenario_path_invalid", path)
        scenarios[found[1]] += 1
    claims: list[MetadataClaim] = []
    for topic, values in (
        ("release", versions),
        ("release_description", descriptions),
        ("license", licenses),
        ("calendar", calendars),
        ("calendar_units", time_units),
    ):
        claims.extend(
            MetadataClaim(topic, "netcdf_headers", value, f"{count}_of_{len(headers)}")
            for value, count in sorted(values.items())
        )
    return claims, tuple(
        (name, scenarios[name]) for name in _SCENARIOS if scenarios[name]
    )


def _custody_counts(custody: dict[str, Any]) -> dict[str, int]:
    if custody.get("status") != "passed":
        raise IntakeRefusal(
            "hyde_metadata_custody_not_passed", repr(custody.get("status"))
        )
    if (
        custody.get("scientific_acceptance") != "not_evaluated"
        or custody.get("public_release_allowed") is not False
    ):
        raise IntakeRefusal("hyde_metadata_custody_posture_invalid", "admission")
    value = custody.get("counts")
    if not isinstance(value, Mapping):
        raise IntakeRefusal("hyde_metadata_custody_counts_invalid", "counts")
    result: dict[str, int] = {}
    for key, count in value.items():
        if not isinstance(key, str) or type(count) is not int or count < 0:
            raise IntakeRefusal("hyde_metadata_custody_counts_invalid", repr(key))
        result[key] = count
    required = {
        "file_count",
        "dataset_file_count",
        "archive_file_count",
        "archive_member_count",
        "netcdf_named_file_count",
    }
    if not required.issubset(result):
        raise IntakeRefusal("hyde_metadata_custody_counts_invalid", "missing fields")
    return result
