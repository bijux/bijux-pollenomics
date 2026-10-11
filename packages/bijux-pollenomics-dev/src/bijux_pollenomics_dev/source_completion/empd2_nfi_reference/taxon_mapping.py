"""Authenticate source-native EMPD2 p_vars rows and taxon mappings."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, cast

from bijux_pollenomics.analysis.lra_validation.contracts import canonical_json

from .projection import digest, identities, identity, sha_identity

_MANIFEST_KEYS = {
    "schema_version",
    "pollen_source_sha256",
    "taxon_parameter_binding_sha256",
    "source_row_count",
    "rows",
}
_ROW_KEYS = {
    "var_",
    "acc_var_",
    "original_varname",
    "acc_varname",
    "groupid",
    "mapping_disposition",
    "taxon_id",
    "parameter_row_sha256",
    "reason_codes",
    "p_vars_row_sha256",
}


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a nonnegative integer")
    return value


def authenticated_taxon_mapping(
    content: bytes,
    pinned_sha256: str,
    projection: dict[str, Any],
    receipt: dict[str, Any],
    parameters: dict[str, dict[str, Any]],
) -> dict[int, str | None]:
    """Bind p_vars source rows to accepted parameterized taxa."""
    pinned = sha_identity(pinned_sha256, "taxon_mapping_manifest_sha256")
    if sha256(content).hexdigest() != pinned:
        raise ValueError("taxon mapping bytes differ from the external trust anchor")
    try:
        raw = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("taxon mapping manifest is not canonical JSON") from exc
    if (
        not isinstance(raw, dict)
        or set(raw) != _MANIFEST_KEYS
        or canonical_json(raw).encode() != content
        or raw.get("schema_version") != "empd2-p-vars-taxon-mapping.v1"
        or raw.get("pollen_source_sha256")
        != projection["source_identities"]["empd2_source"]
        or raw.get("taxon_parameter_binding_sha256")
        != receipt["parameter_binding_sha256"]
        or raw.get("source_row_count") != 5230
    ):
        raise ValueError("taxon mapping manifest differs from its exact schema")
    rows = raw.get("rows")
    if (
        not isinstance(rows, list)
        or len(rows) != 5230
        or any(not isinstance(row, dict) for row in rows)
    ):
        raise ValueError("taxon mapping rows must be an object array")
    mapped: dict[int, str | None] = {}
    for row in cast(list[dict[str, Any]], rows):
        if set(row) != _ROW_KEYS:
            raise ValueError("p_vars mapping row fields differ from the exact schema")
        source_var = _integer(row["var_"], "p_vars.var_")
        if row["acc_var_"] is not None:
            _integer(row["acc_var_"], "p_vars.acc_var_")
        identity(row["original_varname"], "p_vars original_varname")
        for nullable in ("acc_varname", "groupid"):
            if row[nullable] is not None:
                identity(row[nullable], f"p_vars {nullable}")
        native = {
            key: row[key]
            for key in (
                "var_",
                "acc_var_",
                "original_varname",
                "acc_varname",
                "groupid",
            )
        }
        if row["p_vars_row_sha256"] != digest(
            {"pollen_source_sha256": raw["pollen_source_sha256"], **native}
        ):
            raise ValueError("p_vars row digest differs from exact source values")
        identities(row["reason_codes"], "p_vars mapping reasons")
        if row["mapping_disposition"] == "accepted":
            taxon = identity(row["taxon_id"], "p_vars accepted taxon")
            parameter = parameters.get(taxon)
            if (
                parameter is None
                or row["parameter_row_sha256"] != parameter["parameter_row_sha256"]
            ):
                raise ValueError("p_vars accepted taxon lacks its pinned parameter row")
        elif row["mapping_disposition"] == "refused_unmapped":
            if row["taxon_id"] is not None or row["parameter_row_sha256"] is not None:
                raise ValueError(
                    "unmapped p_vars rows must not claim a taxon or parameter"
                )
            taxon = None
        else:
            raise ValueError("p_vars mapping disposition is unsupported")
        if source_var in mapped:
            raise ValueError("p_vars mapping identities are duplicated")
        mapped[source_var] = taxon
    if list(mapped) != sorted(mapped):
        raise ValueError("p_vars mapping rows must use canonical var_ order")
    expected_vars = set(range(1, 5231))
    if set(mapped) != expected_vars:
        raise ValueError("p_vars mapping does not close the exact 1..5230 denominator")
    for row in cast(list[dict[str, Any]], rows):
        if row["acc_var_"] is not None and row["acc_var_"] not in expected_vars:
            raise ValueError(
                "p_vars acc_var_ lies outside the exact source denominator"
            )
    typed_rows = cast(list[dict[str, Any]], rows)
    by_var = {row["var_"]: row for row in typed_rows}
    targets = {row["acc_var_"] for row in typed_rows}
    if None in targets or len(targets) != 1901:
        raise ValueError("p_vars must close exactly 1901 canonical acc_var_ groups")
    for row in typed_rows:
        target = by_var[row["acc_var_"]]
        if (
            target["acc_var_"] != target["var_"]
            or row["acc_varname"] != target["acc_varname"]
            or row["groupid"] != target["groupid"]
            or any(
                row[field] != target[field]
                for field in (
                    "mapping_disposition",
                    "taxon_id",
                    "parameter_row_sha256",
                )
            )
        ):
            raise ValueError("p_vars alias class differs from its canonical target")
    canonical_taxa = {
        by_var[target]["taxon_id"]
        for target in targets
        if by_var[target]["taxon_id"] is not None
    }
    if canonical_taxa != set(parameters):
        raise ValueError("canonical p_vars mappings do not close accepted taxa")
    return mapped
