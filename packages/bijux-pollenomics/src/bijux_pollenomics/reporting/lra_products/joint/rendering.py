"""Accessible non-geographic rendering of retained joint summaries."""

from __future__ import annotations

from html import escape
from typing import Any

from ..contracts import canonical


def _text(value: object) -> str:
    return escape("null" if value is None else str(value), quote=True)


def _fraction(value: dict[str, Any]) -> str:
    return _text(f"{value['numerator']}/{value['denominator']}")


def _coordinate(value: dict[str, Any]) -> str:
    ring = value["ring_mean_m"]
    return _text(
        f"{value['role']} / {value['taxon']} / "
        + ("ring=null" if ring is None else f"ring={ring} m")
    )


def _means(bin_id: str, rows: list[dict[str, Any]]) -> str:
    selected = [row for row in rows if row["bin_id"] == bin_id]
    body = "".join(
        "<tr>"
        f"<td>{row['coordinate_index']}</td>"
        f"<td>{_text(row['coordinate']['role'])}</td>"
        f"<td>{_text(row['coordinate']['taxon'])}</td>"
        f"<td>{_text(row['coordinate']['ring_mean_m'])}</td>"
        f"<td>{_text(row['coordinate']['source_unit'])}</td>"
        f"<td>{_text(row['coordinate']['conversion'])}</td>"
        f"<td>{_text(row['value'])}</td>"
        f"<td>{_text(row['unit'])}</td>"
        "</tr>"
        for row in selected
    )
    return (
        '<div class="table-scroll"><table><caption>Finite-law population means</caption>'
        "<thead><tr><th>Index</th><th>Role</th><th>Taxon</th><th>Native ring mean</th>"
        "<th>Source unit</th><th>Conversion</th><th>Mean</th><th>Unit</th></tr></thead>"
        f"<tbody>{body}</tbody></table></div>"
    )


def _covariance(
    bin_id: str, coordinates: list[dict[str, Any]], rows: list[dict[str, Any]]
) -> str:
    selected = [row for row in rows if row["bin_id"] == bin_id]
    cells = {(row["row_index"], row["column_index"]): row for row in selected}
    header = "".join(f"<th>{_coordinate(item)}</th>" for item in coordinates)
    body = ""
    for row_index, coordinate in enumerate(coordinates):
        values = "".join(
            f"<td>{_text(cells[(row_index, column_index)]['value'])}</td>"
            for column_index in range(len(coordinates))
        )
        body += f"<tr><th>{_coordinate(coordinate)}</th>{values}</tr>"
    return (
        '<div class="table-scroll"><table><caption>Full ordered population covariance '
        "(fraction_squared)</caption><thead><tr><th>Row / column</th>"
        f"{header}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def render_report(projection: dict[str, Any], manifest: dict[str, Any]) -> str:
    """Render every bin and row; incomplete moments remain visibly null."""
    sections = []
    for band in projection["bins"]:
        counts = band["counts"]
        masses = band["masses"]
        status = "complete" if band["complete"] else "incomplete"
        moments = (
            _means(band["bin_id"], projection["means"])
            + _covariance(band["bin_id"], band["coordinates"], projection["covariance"])
            if band["complete"]
            else (
                '<p class="warning"><strong>Incomplete bin:</strong> mean and covariance '
                "remain null. Successful subsets were not renormalized.</p>"
            )
        )
        sections.append(
            f'<section id="bin-{band["bin_index"]}"><h2>Bin {_text(band["bin_id"])}</h2>'
            f'<p class="status {status}">Status: {status}. Product interrupted: '
            f"{_text(projection['interrupted'])}.</p>"
            f"<p>Allocation support: [{_text(band['younger_bp'])}, "
            f"{_text(band['older_bp'])}) BP; {_text(band['membership'])}. "
            "The reconstruction is conditioned on declared stationarity within this bin.</p>"
            '<div class="table-scroll"><table><caption>Draw/bin accounting</caption>'
            "<thead><tr><th>Partition</th><th>Rows</th><th>Exact mass</th></tr></thead><tbody>"
            f"<tr><th>Requested</th><td>{counts['requested']}</td><td>{_fraction(masses['requested'])}</td></tr>"
            f"<tr><th>Successful</th><td>{counts['successful']}</td><td>{_fraction(masses['successful'])}</td></tr>"
            f"<tr><th>Refused</th><td>{counts['refused']}</td><td>{_fraction(masses['refused'])}</td></tr>"
            f"<tr><th>Not run</th><td>{counts['not_run']}</td><td>{_fraction(masses['not_run'])}</td></tr>"
            "<tr><th>Combined unsuccessful</th><td>—</td>"
            f"<td>{_fraction(masses['combined_unsuccessful'])}</td></tr>"
            f"</tbody></table></div>{moments}</section>"
        )
    ledger = "".join(
        "<tr>"
        f"<td>{row['row_index']}</td><td>{_text(row['draw_id'])}</td>"
        f"<td>{_text(row['bin_id'])}</td><td>{_fraction(row['mass'])}</td>"
        f"<td>{_text(row['selected_samples'])}</td><td>{_text(row['status'])}</td>"
        f"<td>{_text(row['reason_code'])}</td><td>{_text(row['diagnostic'])}</td>"
        f"<td>{_text(row['child'])}</td></tr>"
        for row in projection["draw_bin_ledger"]
    )
    links = (
        ("product/manifest.json", "Exact retained joint manifest"),
        ("product/plan.json", "Exact retained finite-law plan"),
        ("product.zip", "Exact retained product archive"),
        ("joint-summary.json", "Complete generated projection (JSON)"),
        ("means.csv", "Complete-bin means (CSV)"),
        ("covariance.csv", "Full ordered covariance (CSV)"),
        ("draw-bin-ledger.csv", "All draw/bin outcomes (CSV)"),
        ("bin-accounting.csv", "Exact count and mass partitions (CSV)"),
        ("manifest.json", "Presentation identities and file hashes"),
    )
    downloads = "".join(
        f'<li><a href="{path}">{_text(label)}</a></li>' for path, label in links
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Retained joint LRA report</title><link rel="stylesheet" href="report.css">'
        "</head><body><main><h1>Retained joint LRA report</h1>"
        '<p class="warning">Exploratory retained finite-law pushforward. Scientific '
        "acceptance is not evaluated and publication is not authorized.</p>"
        "<p>This report preserves supplied joint PPE, calendar-BP and count realizations "
        "through the paired regional-to-local calculation. It provides no geometry, map, "
        "posterior, empirical coverage, calibrated interval, Monte Carlo standard error, "
        "vegetation accuracy or total-uncertainty claim.</p>"
        f"<p>Joint status: {_text(projection['product_status'])}; interrupted: "
        f"{_text(projection['interrupted'])}; requested draw/bin rows: "
        f"{_text(projection['denominators']['requested_draw_bins'])}.</p>"
        + "".join(sections)
        + '<section><h2>Complete draw/bin ledger</h2><div class="table-scroll"><table>'
        "<caption>Every requested retained outcome</caption><thead><tr><th>Index</th>"
        "<th>Draw</th><th>Bin</th><th>Mass</th><th>Selected samples</th><th>Status</th>"
        "<th>Reason</th><th>Diagnostic</th><th>Child</th></tr></thead>"
        f"<tbody>{ledger}</tbody></table></div></section>"
        f"<section><h2>Downloads</h2><ul>{downloads}</ul></section>"
        "<section><h2>Retained uncertainty scope</h2><pre>"
        + _text(canonical(projection["uncertainty_scope"]).decode("utf-8"))
        + "</pre></section><section><h2>Retained product metadata</h2><pre>"
        + _text(canonical(manifest).decode("utf-8"))
        + "</pre></section></main></body></html>"
    )


__all__ = ["render_report"]
