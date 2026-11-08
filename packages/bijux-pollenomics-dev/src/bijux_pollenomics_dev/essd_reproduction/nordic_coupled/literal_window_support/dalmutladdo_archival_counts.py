"""Account for archival DALMUT counts on the unchanged native window owners.

This adjunct combines two archival count columns with an explicitly native
literal pollen total. It does not repair native records or select a chronology,
terrestrial denominator, physical profile or analytical-use permission.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import re
from typing import Any

from ...physical_forward.inputs import decode, require
from ..regional_source_support import (
    TAXA,
    WINDOWS,
    aggregate,
    count_metadata,
    finite,
    integer,
    objects,
)

NATIVE_SHA256 = "57926dede26a7f3b65c612255ffd7f765ca868bebd9976b8371805ac8e580ee2"
ARCHIVAL_SHA256 = "48b0dbdf0e557b726886a3be913a61f09bda427b9c0d32e93508f33e5c90d483"
DOI = "10.1594/PANGAEA.739158"
HEADERS = ("Depth sed [m]", "Bet [#] (Betula)", "Ulm [#] (Ulmus)")
COLUMNS = (9, 93)
WINDOW_OWNERS = (
    (175372, 175373, 175374, 175375, 175376),
    (175377, 175378, 175379, 175380),
    (175381, 175382, 175383),
    (175384,),
    (175385, 175386),
    (175387, 175388, 175389, 175390),
)
MISSING_WINDOW_OWNERS = (
    175372,
    175373,
    175374,
    175375,
    175378,
    175379,
    175381,
    175382,
    175384,
    175385,
    175387,
    175389,
)


@dataclass(frozen=True)
class _ArchivalRow:
    index: int
    depth_token_m: str
    line: str


def _column(line: str, index: int) -> str:
    """Select one token without interpreting other numerical columns."""
    start = 0
    for _ in range(index):
        start = line.index("\t", start) + 1
    end = line.find("\t", start)
    return line[start:] if end == -1 else line[start:end]


def _depth(token: str) -> Decimal:
    """Read a finite nonnegative recorded depth without rounding or offsets."""
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise ValueError("Invalid recorded depth") from exc
    require(value.is_finite() and value >= 0, "Invalid recorded depth")
    return value


def _table(raw: bytes) -> dict[Decimal, _ArchivalRow]:
    """Read only table identity, shape and the sediment-depth column."""
    lines = raw.decode("utf-8").splitlines()
    headers = [i for i, line in enumerate(lines) if line.startswith("Depth sed ")]
    require(len(headers) == 1, "One archival header required")
    header = headers[0]
    require(
        f"https://doi.org/{DOI}" in "\n".join(lines[:header])
        and lines[header].count("\t") == 97
        and tuple(_column(lines[header], i) for i in (0, *COLUMNS)) == HEADERS,
        "Archival DOI, depth unit or literal count headers differ",
    )
    rows = lines[header + 1 :]
    require(len(rows) == 72, "All 72 archival rows required")
    result: dict[Decimal, _ArchivalRow] = {}
    for index, line in enumerate(rows):
        require(line.count("\t") == 97, "Archival row width differs")
        token = _column(line, 0)
        depth_cm = _depth(token) * 100
        require(depth_cm not in result, "Duplicate archival depth")
        result[depth_cm] = _ArchivalRow(index, token, line)
    return result


def _native_owners(account: dict[str, Any]) -> dict[Decimal, dict[str, Any]]:
    """Bind the frozen complete owner population and its recorded cm depths."""
    require(
        account["schema_version"] == "nordic-literal-core-support.v1"
        and account["key"] == "dalmutladdo"
        and account["identity"]
        == {
            "collection_unit_id": 14989,
            "dataset_id": 20034,
            "handle": "DALMUT",
            "site_id": 13388,
            "source_sample_count": 72,
        }
        and account["chronology"]["selected_chronology_id"] == 11601,
        "Frozen DALMUT identity or chronology differs",
    )
    samples = objects(account["samples"])
    require(
        len(samples) == 72
        and all(type(s["sample_id"]) is int for s in samples)
        and [s["sample_id"] for s in samples] == list(range(175353, 175425)),
        "Complete ordered native owner population required",
    )
    result: dict[Decimal, dict[str, Any]] = {}
    for sample in samples:
        depth = sample["native_depth"]
        require(
            finite(depth),
            "Finite native cm depth required",
        )
        depth_cm = _depth(str(depth))
        require(depth_cm not in result, "Duplicate native depth")
        result[depth_cm] = sample
    require(
        len(account["windows"]) == 6
        and all(
            row["window"] == list(edge) and row["sample_ids"] == list(ids)
            for row, edge, ids in zip(
                account["windows"], WINDOWS, WINDOW_OWNERS, strict=True
            )
        )
        and all(
            [s["sample_id"] for s in samples if s["window"] == list(edge)] == list(ids)
            for edge, ids in zip(WINDOWS, WINDOW_OWNERS, strict=True)
        ),
        "Frozen nineteen-owner window membership differs",
    )
    return result


def _native_count(sample: dict[str, Any], axis: int) -> int | None:
    """Keep absent native Ulmus distinct from literal reported integer counts."""
    taxa = objects(sample["taxa"])
    require(len(taxa) == 2, "Exact two-label native panel required")
    taxon = taxa[axis]
    expected = TAXA[axis]
    require(
        taxon["label"] == expected["label"]
        and type(taxon["taxon_id"]) is int
        and taxon["taxon_id"] == expected["taxon_id"],
        "Native literal taxon identity differs",
    )
    matches = objects(taxon["native_matches"])
    if taxon["status"] == "missing_literal":
        require(axis == 1 and not matches, "Only genuinely absent Ulmus allowed")
        return None
    require(len(matches) == 1, "Unique reported native cell required")
    native = matches[0]["native"]
    require(
        native["variablename"] == expected["label"]
        and type(native["taxonid"]) is int
        and native["taxonid"] == expected["taxon_id"]
        and count_metadata(native)
        and integer(native.get("value"))
        and taxon["status"]
        == ("measured_zero" if native["value"] == 0 else "measured"),
        "Native count identity, type, state or unit differs",
    )
    return int(native["value"])


def _archival_count(row: _ArchivalRow, axis: int) -> tuple[str, int]:
    """Read a selected literal integer token, never blank or missing as zero."""
    token = _column(row.line, COLUMNS[axis])
    require(
        re.fullmatch(r"[0-9]+", token) is not None, "Explicit integer count required"
    )
    return token, int(token)


def _correspondence(
    account: dict[str, Any], table: dict[Decimal, _ArchivalRow]
) -> dict[int, _ArchivalRow]:
    """Validate the partial correspondence before inspecting absent counterparts."""
    native = _native_owners(account)
    shared = native.keys() & table.keys()
    require(
        len(shared) == 71
        and native.keys() - table.keys() == {Decimal("4.5")}
        and native[Decimal("4.5")]["sample_id"] == 175354
        and table.keys() - native.keys() == {Decimal("4.0")}
        and table[Decimal("4.0")].index == 1,
        "Expected partial depth intersection or unmatched owners differ",
    )
    pairs = {s["sample_id"]: table[d] for d, s in native.items() if d in shared}
    missing: list[tuple[int, _ArchivalRow]] = []
    compared = [0, 0]
    for sample in account["samples"]:
        owner = sample["sample_id"]
        if owner not in pairs:
            continue
        for axis in range(2):
            value = _native_count(sample, axis)
            if value is None:
                missing.append((owner, pairs[owner]))
            else:
                require(
                    _archival_count(pairs[owner], axis)[1] == value,
                    "Shared original/native count conflict",
                )
                compared[axis] += 1
    require(
        compared == [71, 28] and len(missing) == 43, "99 shared / 43 absent required"
    )
    require(
        tuple(owner for owner, _ in missing if 175372 <= owner <= 175390)
        == MISSING_WINDOW_OWNERS,
        "Twelve absent frozen-window counterparts required",
    )
    # All reported comparisons must succeed before any absent token is inspected.
    for _, row in missing:
        require(
            _archival_count(row, 1)[1] == 0, "Absent counterpart is not explicit zero"
        )
    return pairs


def _windows(
    account: dict[str, Any], pairs: dict[int, _ArchivalRow]
) -> list[dict[str, Any]]:
    """Aggregate new adjunct rows without changing the native account."""
    by_id = {s["sample_id"]: s for s in account["samples"]}
    windows = []
    for edge, ids in zip(WINDOWS, WINDOW_OWNERS, strict=True):
        members = []
        attribution = []
        for owner in ids:
            sample, row = by_id[owner], pairs[owner]
            selected = [_archival_count(row, axis) for axis in range(2)]
            counts = [value for _, value in selected]
            mass = sample["pollen_N"]
            mass_defined = sample["pollen_denominator_status"] == "complete"
            require(
                not mass_defined or (integer(mass) and sum(counts) <= mass),
                "Archival panel exceeds valid native literal pollen total",
            )
            members.append(
                {
                    "sample_id": owner,
                    "panel_complete": True,
                    "panel_counts": counts,
                    "pollen_denominator_status": "complete"
                    if mass_defined
                    else "refused",
                    "pollen_N": mass if mass_defined else None,
                }
            )
            attribution.append(
                {
                    "sample_id": owner,
                    "native_depth_cm": sample["native_depth"],
                    "archival_row_index": row.index,
                    "archival_depth_token_m": row.depth_token_m,
                    "cells": [
                        {
                            **taxon,
                            "doi": DOI,
                            "column_index": column,
                            "column_header": HEADERS[axis + 1],
                            "token": token,
                            "count": count,
                            "native_status": sample["taxa"][axis]["status"],
                        }
                        for axis, (taxon, column, (token, count)) in enumerate(
                            zip(TAXA, COLUMNS, selected, strict=True)
                        )
                    ],
                }
            )
        result = aggregate(members, [])
        result["native_pollen_N"] = result.pop("pollen_N")
        result["mixed_source_literal_nonpanel_N"] = result.pop("excluded_pollen_N")
        windows.append({"window": list(edge), **result, "source_cells": attribution})
    return windows


def archival_window_counts(
    native_account_bytes: bytes, original_table_bytes: bytes
) -> dict[str, Any]:
    """Qualify six mixed-source count adjuncts on frozen DALMUT membership.

    Only the exact retained native audit and archival table are accepted. Their
    71-depth intersection and all 99 shared counts are checked before the 43
    absent counterparts. Original native states and the whole-72 refusal remain
    unchanged. Full-pollen totals are native, not archival or LRA denominators.
    """
    for raw, length, sha in (
        (native_account_bytes, 133669, NATIVE_SHA256),
        (original_table_bytes, 40251, ARCHIVAL_SHA256),
    ):
        require(
            type(raw) is bytes
            and len(raw) == length
            and hashlib.sha256(raw).hexdigest() == sha,
            "Exact frozen DALMUT source bytes required",
        )
    account = decode(native_account_bytes)
    table = _table(original_table_bytes)
    pairs = _correspondence(account, table)
    return {
        "schema_version": "dalmutladdo-archival-window-counts.v1",
        "status": "archival_count_adjunct_accounted",
        "native_account_sha256": NATIVE_SHA256,
        "archival_table_sha256": ARCHIVAL_SHA256,
        "archival_doi": DOI,
        "taxon_identity_basis": "Native literal axis IDs; archival taxon identity is the exact column header, not an ontology or PPE crosswalk.",
        "shared_depth_pairs": 71,
        "shared_count_comparisons": 99,
        "archival_zero_counterparts": 43,
        "window_zero_counterparts": 12,
        "unmatched_native_sample_id": 175354,
        "unmatched_native_depth_cm": "4.5",
        "unmatched_archival_depth_m": "0.04",
        "windows": _windows(account, pairs),
        "native_account_modified": False,
        "whole_72_correspondence": False,
        "ages_or_windows_recomputed": False,
        "engine_calls": 0,
        "model_fits": 0,
        "scientific_or_field_admission": False,
        "scope": "Two archival literal count columns on nineteen frozen native owners only; native full-pollen totals and mixed-source nonpanel remainders are not archival whole-pollen, terrestrial or eligible LRA denominators. No historical-input, age uncertainty, basin, taxon/PPE or analytical-rights admission.",
        "rights_and_attribution": "Bjune (2010), PANGAEA.739158, archival EPD table; provider-declared CC BY-NC 3.0, local noncommercial development comparison only. Preserve separate archival, retrieval and native-capture epochs; no raw table redistribution or broader permission granted.",
    }
