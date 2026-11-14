"""Literal parameter-label coverage, keeping source applicability unadmitted."""

from __future__ import annotations

from collections.abc import Sequence
from math import isfinite
import re
from typing import Any

PPE = re.compile(r"^\s*([0-9.eE+\-]+)\s*\(\s*([0-9.eE+\-]+)\s*\)\s*$")


def _number(text: str, *, positive: bool) -> bool:
    try:
        value = float(text)
    except (ValueError, TypeError):
        return False
    return isfinite(value) and (value > 0 if positive else value >= 0)


def _landclim(row: dict[str, str]) -> dict[str, Any]:
    ppe, fsp = row.get("PPE (SD)", ""), row.get("FSP (m/s)", "")
    match = PPE.fullmatch(ppe)
    return {
        **row,
        "nominal_rpp_fsp_available": bool(
            match
            and _number(match[1], positive=True)
            and _number(fsp.removesuffix("*"), positive=True)
        ),
        "uncertainty_available": bool(match and _number(match[2], positive=False)),
        "fsp_footnote_present": fsp.endswith("*"),
        "uncertainty_semantics": "source_label_SD",
    }


def _europe(row: dict[str, str]) -> dict[str, Any]:
    if row.get("region") != "Europe" or row.get("dataset_version") not in {"v1", "v2"}:
        raise ValueError("European v1/v2 reference authority required")
    n_estimates = row.get("n_estimates")
    if not isinstance(n_estimates, str) or re.fullmatch(r"[0-9]+", n_estimates) is None:
        raise ValueError("Reference n_estimates must be a nonnegative integer string")
    return {
        **row,
        "nominal_rpp_fsp_available": _number(row.get("rpp", ""), positive=True)
        and _number(row.get("fall_speed_m_s", ""), positive=True)
        and int(n_estimates) > 0,
        "uncertainty_available": _number(row.get("rpp_se", ""), positive=False),
        "uncertainty_semantics": "compiled_mean_SE",
    }


def parameter_coverage(
    native_audit: dict[str, Any],
    landclim_rows: Sequence[dict[str, str]],
    europe_rows: Sequence[dict[str, str]],
    *,
    workbook_audit: dict[str, Any] | None = None,
    author_lookup_rows: Sequence[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Return exact matches and every target without applying taxonomic aliases."""
    targets = [row["Plant taxa/Pollen-morphological types"] for row in landclim_rows]
    if len(targets) != len(set(targets)):
        raise ValueError("Duplicated LandClim parameter target")
    lc = [_landclim(r) for r in landclim_rows]
    eu = [_europe(r) for r in europe_rows]
    reference_axis = [(row["dataset_version"], row["taxon"]) for row in europe_rows]
    if len(reference_axis) != len(set(reference_axis)):
        raise ValueError("Duplicate European reference version/taxon")
    lookup: dict[str, str] = {}
    for witness in author_lookup_rows or ():
        source, target = witness["oldvar"], witness["RPP.LANDCLIMII"]
        if not source or not target or (source in lookup and lookup[source] != target):
            raise ValueError("Conflicting or empty author lookup route")
        lookup[source] = target
    witness_mass = {
        "known_native_nisp": 0,
        "assigned_candidate_nisp": 0,
        "author_excluded_nisp": 0,
        "unmapped_nisp": 0,
    }
    native = []
    for taxon in native_audit["taxon_axis"]:
        label = taxon["native_label"]
        native.append(
            {
                "native_label": label,
                "taxon_id": taxon["taxon_id"],
                "known_NISP_sum": taxon["known_NISP_sum"],
                "landclim": [
                    r for r in lc if r["Plant taxa/Pollen-morphological types"] == label
                ],
                "europe_2020": [r for r in eu if r["taxon"] == label],
                "author_lookup_candidate": lookup.get(label),
            }
        )
        if author_lookup_rows is not None:
            count = taxon["known_NISP_sum"]
            witness_mass["known_native_nisp"] += count
            candidate_target = lookup.get(label)
            if candidate_target in {"zz.do not use", "aage.cal.BP"}:
                disposition = "author_excluded_nisp"
            else:
                disposition = (
                    "assigned_candidate_nisp"
                    if candidate_target is not None
                    else "unmapped_nisp"
                )
            witness_mass[disposition] += count
    workbook_labels = {
        c["source_label"]
        for row in (workbook_audit or {}).get("rows", [])
        for c in row["cells"]
        if c["source_role"] == "specimen_variable_unclassified"
    }
    target_rows = [
        {
            "target_label": label,
            "source_parameter": row,
            "native_exact_matches": [
                {"taxon_id": t["taxon_id"], "native_label": t["native_label"]}
                for t in native_audit["taxon_axis"]
                if t["native_label"] == label
            ],
            "workbook_literal_exact_matches": sorted(
                w for w in workbook_labels if w == label
            ),
            "workbook_whitespace_candidate_matches": sorted(
                w for w in workbook_labels if w != label and w.strip() == label
            ),
        }
        for label, row in zip(targets, lc, strict=True)
    ]
    return {
        "schema_version": "bokesjon-pilot-parameter-label-coverage.v1",
        "native_taxa": native,
        "landclim_target_count": len(target_rows),
        "landclim_targets": target_rows,
        "europe_2020_reference_rows": eu,
        "author_lookup_mass": witness_mass if author_lookup_rows is not None else None,
        "author_lookup_interpretation": "Source-owned literal routes are version-bound candidate witnesses only; no author mapping is applied and no biological or numerical admission is granted.",
        "scientific_admission": False,
        "lookup_rule": "Literal exact source labels only. Whitespace candidates are retained separately, not applied. Genus/species, pollen-type and family mappings require a declared source-owned crosswalk and applicability review; no missing RPP, FSP or SE becomes zero.",
        "normalization": "A Poaceae reference RPP of1 with missing SE supports only its stated nominal reference value; no SD/SE0 is invented. LandClim SD labels and2020compiled-mean SE labels remain distinct.",
        "cereal_compatibility": "LandClim separates Cerealia-t excluding rye and Secale, whereas2020Cerealia is harmonised jointly. No automatic merge, split, generic grass substitution or full terrestrial denominator follows from label coverage.",
    }
