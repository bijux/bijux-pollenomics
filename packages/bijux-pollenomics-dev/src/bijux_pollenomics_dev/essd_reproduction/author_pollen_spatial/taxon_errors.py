"""Paired taxon errors on the observed, commonly scored author site bins."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from statistics import mean

from .source import _hash, _rows


def compare_taxon_errors(
    score_dirs: Mapping[str, Path],
    scored_keys: list[tuple[str, str]],
    score_rows: Mapping[str, Mapping[tuple[str, str], Mapping[str, str]]],
) -> tuple[list[dict[str, object]], dict[str, str]]:
    """Give each site equal weight; verify taxon rows against the scored totals."""
    expected = set(scored_keys)
    reference: dict[tuple[str, str, str], tuple[int, str]] = {}
    by_method: dict[str, dict[tuple[str, str, str], tuple[int, float]]] = {}
    receipts = {}
    for method, directory in score_dirs.items():
        path = directory / "scored-predictions.csv"
        rows = _rows(path)
        keyed: dict[tuple[str, str, str], tuple[int, float]] = {}
        for row in rows:
            site_bin = (row["target_site_id"], row["bin_id_bp"])
            key = (*site_bin, row["taxon"])
            if site_bin not in expected or key in keyed:
                raise ValueError(
                    "Taxon prediction axes differ from common scored support"
                )
            if row["block_grid_id"] != score_rows[method][site_bin]["block_grid_id"]:
                raise ValueError("Taxon prediction block differs from score row")
            count = int(row["observed_count"])
            fraction = float(row["predicted_fraction"])
            if count < 0 or not 0 <= fraction <= 1:
                raise ValueError("Taxon prediction has invalid count or fraction")
            keyed[key] = (count, fraction)
            if method == "training_mean":
                reference[key] = (count, row["block_grid_id"])
        by_method[method] = keyed
        receipts[method] = _hash(path)
    if not reference or any(
        set(values) != set(reference) for values in by_method.values()
    ):
        raise ValueError("Methods do not share complete taxon prediction axes")
    taxa = sorted({taxon for _, _, taxon in reference})
    if len(taxa) != 31 or len(reference) != len(expected) * len(taxa):
        raise ValueError("Expected one complete 31-taxon vector per scored site bin")
    for method, keyed in by_method.items():
        for site_bin in scored_keys:
            counts = [keyed[(*site_bin, taxon)][0] for taxon in taxa]
            if any(
                keyed[(*site_bin, taxon)][0] != reference[(*site_bin, taxon)][0]
                for taxon in taxa
            ):
                raise ValueError("Methods do not share observed taxon counts")
            total = sum(counts)
            if total <= 0 or total != int(
                score_rows[method][site_bin]["observed_total_count"]
            ):
                raise ValueError("Taxon counts differ from scored denominator")
            fractions = [keyed[(*site_bin, taxon)][1] for taxon in taxa]
            errors = [
                fraction - count / total
                for fraction, count in zip(fractions, counts, strict=True)
            ]
            if (
                abs(sum(fractions) - 1) > 1e-12
                or abs(
                    mean(map(abs, errors))
                    - float(score_rows[method][site_bin]["mae_fraction"])
                )
                > 1e-12
                or abs(
                    sum(map(abs, errors)) / 2
                    - float(score_rows[method][site_bin]["total_variation"])
                )
                > 1e-12
            ):
                raise ValueError("Taxon errors disagree with the scored composition")
    sites = sorted({site for site, _ in scored_keys})
    result: list[dict[str, object]] = []
    for taxon in taxa:
        methods: dict[str, dict[str, float]] = {}
        for method, keyed in by_method.items():
            per_site = []
            for site in sites:
                errors = []
                for site_bin in scored_keys:
                    if site_bin[0] != site:
                        continue
                    count, fraction = keyed[(*site_bin, taxon)]
                    total = int(score_rows[method][site_bin]["observed_total_count"])
                    errors.append(fraction - count / total)
                per_site.append((mean(map(abs, errors)), mean(errors)))
            methods[method] = {
                "site_macro_absolute_error_fraction": mean(row[0] for row in per_site),
                "site_macro_bias_fraction": mean(row[1] for row in per_site),
            }
        baseline = methods["training_mean"]["site_macro_absolute_error_fraction"]
        for metrics in methods.values():
            metrics["absolute_error_minus_training_mean_fraction"] = (
                metrics["site_macro_absolute_error_fraction"] - baseline
            )
        result.append({"taxon": taxon, "scored_sites": len(sites), "methods": methods})
    return result, receipts
