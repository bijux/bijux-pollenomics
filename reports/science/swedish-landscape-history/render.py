"""Render Swedish latitude-band figures from the saved public-model analysis.

Requires Matplotlib in a separate rendering environment. This script reads saved
means and coverage; it does not reconstruct pollen or calculate uncertainty.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib.patches import Polygon, Rectangle
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np

TREE = "#196748"
OPEN = "#9a6a25"
SHRUB = "#806192"
CEREAL = "#df721c"
SOURCE_OPEN = "#247aa5"
MISSING = "#e5e7e9"
FOOTER = (
    "Published REVEALS / PANGAEA 937075 · Swedish-centre grids · 31-taxon cover (%)\n"
    "Source windows, BP relative to 1950; youngest interval follows source coring support. "
    "No interpolation or regional confidence intervals."
)


def selected(
    rows: list[dict[str, Any]],
    *,
    n: int = 5,
    band: int = 0,
    policy: str = "available",
    weighting: str = "area",
    recent: bool = False,
) -> list[dict[str, Any]]:
    """Select an explicit saved support, preserving unavailable intervals."""
    return sorted(
        (
            r
            for r in rows
            if r["band_count"] == n
            and r["band_index"] == band
            and r["policy"] == policy
            and r["weighting"] == weighting
            and (not recent or r["older_bp"] <= 3200)
        ),
        key=lambda r: r["younger_bp"],
    )


def cereal_ceiling(rows: list[dict[str, Any]]) -> float:
    """Use one scale covering every plotted cereal mean, without clipping."""
    maximum = max((r["metrics"]["cereals"]["mean"] or 0 for r in rows), default=0)
    return max(5.0, float(np.ceil(maximum / 5) * 5))


def segments(
    rows: list[dict[str, Any]], metric: str, statistic: str = "mean"
) -> tuple[list[float], list[float]]:
    """Draw each saved mean over its original interval, with no gap bridging."""
    xs: list[float] = []
    ys: list[float] = []
    for r in rows:
        value = r["metrics"][metric][statistic]
        y = float("nan") if value is None else value
        xs.extend((r["younger_bp"], r["older_bp"], float("nan")))
        ys.extend((y, y, float("nan")))
    return xs, ys


def style(ax: Any, *, recent: bool = False, ylabel: str = "Cover (%)") -> None:
    """Set common scales without changing the saved temporal resolution."""
    ax.set_xlim(3200 if recent else 11700, 0)
    ax.set_ylim(0, 100)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color="#d9dddc", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.xaxis.set_major_locator(MaxNLocator(6))


def save(fig: Any, output: Path, name: str) -> None:
    """Export editable vector, portable PDF and raster preview of one figure."""
    for suffix in ("svg", "pdf", "png"):
        fig.savefig(
            output / f"{name}.{suffix}",
            dpi=160,
            facecolor="white",
            metadata={
                "Creator": "bijux-pollenomics",
                "CreationDate": None,
                "ModDate": None,
            }
            if suffix == "pdf"
            else ({"Date": None} if suffix == "svg" else None),
        )
    svg = output / f"{name}.svg"
    # Matplotlib emits trailing spaces in path data; line breaks preserve separators.
    svg.write_text(
        "\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n"
    )
    plt.close(fig)


def trajectory_figure(
    rows: list[dict[str, Any]], output: Path, *, recent: bool
) -> None:
    """Show the five-band composition and cereals on aligned, separate scales."""
    policy = "fixed_recent" if recent else "available"
    fig, axes = plt.subplots(
        5, 2, figsize=(14, 13.8), sharex=True, gridspec_kw={"width_ratios": [1.45, 1]}
    )
    fig.subplots_adjust(
        left=0.09, right=0.98, top=0.82, bottom=0.10, hspace=0.43, wspace=0.22
    )
    title = (
        "Recent Swedish landscape history"
        if recent
        else "Swedish landscape history through the Holocene"
    )
    fig.suptitle(title, x=0.09, ha="left", y=0.975, fontsize=20, weight="bold")
    subtitle = (
        "Primary comparison: identical grids across all eight recent source windows"
        if recent
        else "Descriptive extension: available grids change between source windows"
    )
    fig.text(0.09, 0.942, subtitle, fontsize=12)
    fig.text(
        0.09,
        0.916,
        "Five fixed latitude bands · spherical cell-area weights · tree cover is an operational taxon proxy",
        fontsize=10,
        color="#4b5552",
    )
    cereal_max = max(
        (
            r["metrics"]["cereals"]["mean"] or 0
            for r in rows
            if r["band_count"] == 5
            and r["weighting"] == "area"
            and r["policy"] == policy
            and (not recent or r["older_bp"] <= 3200)
        ),
        default=0,
    )
    upper = max(5, np.ceil(cereal_max / 5) * 5)
    handles: list[Any] = []
    for band in range(5):
        data = selected(rows, band=band, policy=policy, recent=recent)
        ax, cereal_ax = axes[band]
        for metric, label, color, line in (
            ("tree_assigned", "Tree-associated", TREE, "-"),
            ("non_tree", "All non-tree", OPEN, "-"),
            ("shrubs_heath", "Shrub / heath (within non-tree)", SHRUB, ":"),
            ("source_OL", "Published open land", SOURCE_OPEN, "--"),
        ):
            (h,) = ax.plot(
                *segments(data, metric),
                color=color,
                linestyle=line,
                linewidth=1.8,
                label=label,
            )
            if band == 0:
                handles.append(h)
        cereal_ax.plot(*segments(data, "cereals"), color=CEREAL, linewidth=2)
        for a in (ax, cereal_ax):
            style(a, recent=recent)
        cereal_ax.set_ylim(0, upper)
        cereal_ax.set_ylabel("Cereal cover (%)")
        south, north = 55 + 3 * band, 58 + 3 * band
        n_values = [r["count"] for r in data]
        support = (
            f"n = {min(n_values)} grids"
            if min(n_values) == max(n_values)
            else f"n = {min(n_values)}–{max(n_values)} grids"
        )
        ax.set_title(
            f"{south}–{north}°N  |  {support}", loc="left", fontsize=11, weight="bold"
        )
        cereal_ax.set_title("Cereals; separate shared scale", loc="left", fontsize=10)
        if not any(n_values):
            for a in (ax, cereal_ax):
                a.set_facecolor("#f4f5f4")
                a.text(
                    0.5,
                    0.5,
                    "No common valid grid\n350–700 BP zero composition\nGap retained"
                    if recent and band == 3
                    else "No common valid grid\nGap retained",
                    transform=a.transAxes,
                    ha="center",
                    va="center",
                    color="#626b67",
                    fontsize=12,
                )
    fig.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(0.08, 0.90),
        ncol=2,
        frameon=False,
        fontsize=9,
    )
    for a in axes[-1]:
        a.set_xlabel("Published age window (BP; older → younger)")
    fig.text(0.09, 0.035, FOOTER, fontsize=8.5, color="#4b5552", linespacing=1.7)
    save(fig, output, "recent-trajectories" if recent else "holocene-trajectories")


def coverage_figure(rows: list[dict[str, Any]], output: Path) -> None:
    """Show valid and high-quality grid counts without calling them site counts."""
    fig, axes = plt.subplots(2, 1, figsize=(15, 6.7))
    fig.subplots_adjust(left=0.10, right=0.94, top=0.83, bottom=0.19, hspace=0.42)
    fig.suptitle(
        "Where is Swedish reconstruction support available?",
        x=0.10,
        ha="left",
        y=0.97,
        fontsize=18,
        weight="bold",
    )
    fig.text(
        0.10,
        0.91,
        "Each entry is a valid grid count / all Swedish-centre grids in that band. Quality is source-defined.",
        fontsize=10,
    )
    for ax, policy, title in zip(
        axes,
        ("available", "high_quality"),
        ("All valid quality-eligible grids", "High-quality grids only"),
        strict=True,
    ):
        data = [selected(rows, band=b, policy=policy) for b in range(5)]
        numbers = np.array([[r["count"] for r in d] for d in data])
        ax.imshow(numbers, aspect="auto", cmap="YlGnBu", vmin=0, vmax=8)
        for b, series in enumerate(data):
            for j, r in enumerate(series):
                ax.text(
                    j,
                    b,
                    f"{r['count']}/{r['coverage']['total']}",
                    ha="center",
                    va="center",
                    fontsize=7.5,
                    color="white" if r["count"] >= 5 else "#233a35",
                )
        ax.set_yticks(range(5), [f"{55 + 3 * b}–{58 + 3 * b}°N" for b in range(5)])
        ax.set_xticks(
            range(25),
            [r["source_window"].removesuffix(" BP") for r in data[0]],
            rotation=60,
            ha="right",
            fontsize=7,
        )
        ax.set_title(title, loc="left", fontsize=11, weight="bold")
        ax.invert_xaxis()
        if policy == "available":
            ax.tick_params(axis="x", labelbottom=False)
    fig.text(
        0.10,
        0.035,
        "650 grid/windows: 567 valid, 82 source no-data, 1 invalid zero composition.\n"
        "Neither grid counts nor source quality codes establish independent site counts; no-data stays missing.",
        fontsize=9,
        color="#4b5552",
        linespacing=1.7,
    )
    save(fig, output, "coverage")


def boundary_figure(rows: list[dict[str, Any]], output: Path) -> None:
    """Compare geographical partitions; similarly numbered bands are not pairs."""
    fig, axes = plt.subplots(3, 2, figsize=(14, 10.5), sharex=True)
    fig.subplots_adjust(
        left=0.10, right=0.94, top=0.85, bottom=0.14, hspace=0.35, wspace=0.24
    )
    fig.suptitle(
        "Does the latitude partition change the picture?",
        x=0.10,
        ha="left",
        y=0.97,
        fontsize=19,
        weight="bold",
    )
    fig.text(
        0.10,
        0.925,
        "4, 5 and 6 bands share 55–70°N. Available-grid means; actual boundaries shown on each row.",
        fontsize=10,
    )
    fig.text(
        0.10,
        0.895,
        "White/grey means no valid estimate. Temporal blocks use their actual widths; no interpolation.",
        fontsize=10,
    )
    images: list[Any] = []
    for row_index, n in enumerate((4, 5, 6)):
        series = [selected(rows, n=n, band=b) for b in range(n)]
        edges = [series[0][0]["younger_bp"], *[r["older_bp"] for r in series[0]]]
        y_edges = np.linspace(55, 70, n + 1)
        for col, metric, vmax, label in (
            (0, "tree_assigned", 100, "Tree-associated cover (%)"),
            (1, "cereals", cereal_ceiling(rows), "Cereal cover (%)"),
        ):
            ax = axes[row_index, col]
            matrix = np.array(
                [
                    [
                        np.nan
                        if r["metrics"][metric]["mean"] is None
                        else r["metrics"][metric]["mean"]
                        for r in d
                    ]
                    for d in series
                ]
            )
            cmap = plt.get_cmap("YlGn" if col == 0 else "YlOrBr").copy()
            cmap.set_bad(MISSING)
            image = ax.pcolormesh(
                edges,
                y_edges,
                matrix,
                cmap=cmap,
                vmin=0,
                vmax=vmax,
                edgecolors="white",
                linewidth=0.3,
            )
            if row_index == 0:
                images.append(image)
            ax.set_yticks(
                (y_edges[:-1] + y_edges[1:]) / 2,
                [
                    f"{s:g}–{e:g}"
                    for s, e in zip(y_edges[:-1], y_edges[1:], strict=True)
                ],
                fontsize=8,
            )
            ax.set_ylabel(f"{n} bands · °N")
            ax.set_xlim(11700, 0)
            ax.set_title(label, loc="left", fontsize=11)
            if row_index == 2:
                ax.set_xlabel("Published age window (BP)")
    for col, image in enumerate(images):
        fig.colorbar(
            image, ax=axes[:, col], orientation="horizontal", fraction=0.025, pad=0.11
        )
    fig.text(0.10, 0.025, FOOTER, fontsize=8, color="#4b5552", linespacing=1.6)
    save(fig, output, "latitude-band-comparison")


def sensitivity_figure(rows: list[dict[str, Any]], output: Path) -> None:
    """Compare common support with changing support and a quality restriction."""
    fig, axes = plt.subplots(5, 2, figsize=(14, 12.6), sharex=True)
    fig.subplots_adjust(
        left=0.09, right=0.98, top=0.86, bottom=0.13, hspace=0.4, wspace=0.22
    )
    fig.suptitle(
        "Support choices matter for the Swedish curves",
        x=0.09,
        ha="left",
        y=0.975,
        fontsize=19,
        weight="bold",
    )
    fig.text(
        0.09,
        0.94,
        "Recent eight windows · five latitude bands · area weights within each selected cohort",
        fontsize=11,
    )
    handles: list[Any] = []
    for band in range(5):
        for policy, label, color, line in (
            ("fixed_recent", "Fixed common grids (primary)", TREE, "-"),
            ("available", "All available grids", SOURCE_OPEN, "--"),
            ("high_quality", "High-quality grids only", CEREAL, ":"),
        ):
            data = selected(rows, band=band, policy=policy, recent=True)
            for column, metric in enumerate(("tree_assigned", "cereals")):
                (h,) = axes[band, column].plot(
                    *segments(data, metric),
                    label=label,
                    color=color,
                    linestyle=line,
                    linewidth=1.9,
                )
                if band == 0 and column == 0:
                    handles.append(h)
        for column, label in ((0, "Tree-associated (%)"), (1, "Cereal cover (%)")):
            ax = axes[band, column]
            style(ax, recent=True, ylabel=label)
            if column:
                ax.set_ylim(0, cereal_ceiling(rows))
            ax.set_title(
                f"{55 + 3 * band}–{58 + 3 * band}°N",
                loc="left",
                fontsize=10,
                weight="bold",
            )
            if band == 3:
                ax.text(
                    0.02,
                    0.88,
                    "No fixed common cohort; no high-quality cells",
                    transform=ax.transAxes,
                    fontsize=8,
                    color="#626b67",
                )
    fig.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(0.08, 0.92),
        ncol=3,
        frameon=False,
        fontsize=9,
    )
    for ax in axes[-1]:
        ax.set_xlabel("Published age window (BP; older → younger)")
    fig.text(
        0.09,
        0.025,
        "Unavailable policies remain gaps; no substitution, smoothing or fallback. "
        "Quality selection changes support as well as source quality.\n" + FOOTER,
        fontsize=8,
        color="#4b5552",
        linespacing=1.6,
    )
    save(fig, output, "support-sensitivity")


def support_map(source: dict[str, Any], boundary: dict[str, Any], output: Path) -> None:
    """Locate the whole centre-selected cells and explicit latitude separators."""
    fig, ax = plt.subplots(figsize=(8.2, 10.8))
    fig.subplots_adjust(left=0.11, right=0.96, top=0.88, bottom=0.14)
    fig.suptitle(
        "Swedish grid support and latitude bands",
        x=0.11,
        ha="left",
        y=0.97,
        fontsize=18,
        weight="bold",
    )
    fig.text(
        0.11,
        0.928,
        "26 published grid centres; whole cells selected by centre containment",
        fontsize=10,
    )
    for feature in boundary["features"]:
        geom = feature["geometry"]
        polys = (
            [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        )
        for rings in polys:
            ax.add_patch(
                Polygon(
                    rings[0], facecolor="#eeefec", edgecolor="#9aaba1", linewidth=0.8
                )
            )
            for hole in rings[1:]:
                ax.add_patch(
                    Polygon(hole, facecolor="white", edgecolor="#9aaba1", linewidth=0.4)
                )
    seen: set[str] = set()
    palette = plt.get_cmap("viridis")
    for feature in source["features"]:
        p = feature["properties"]
        if p.get("dataset_id") != "937075" or p.get("country") != "Sweden":
            continue
        gid = p["parent_grid_record_id"]
        if gid in seen:
            continue
        seen.add(gid)
        coords = feature["geometry"]["coordinates"][0]
        lon = (min(x[0] for x in coords) + max(x[0] for x in coords)) / 2
        lat = (min(x[1] for x in coords) + max(x[1] for x in coords)) / 2
        band = min(4, int((lat - 55) / 3))
        ax.add_patch(
            Rectangle(
                (lon - 0.5, lat - 0.5),
                1,
                1,
                facecolor=palette(band / 4),
                alpha=0.32,
                edgecolor=palette(band / 4),
                linewidth=1,
            )
        )
        ax.plot(lon, lat, ".", color="#25483b", markersize=4)
        ax.text(lon + 0.08, lat + 0.1, gid, fontsize=6.5, color="#172c22")
    for lat in (55, 58, 61, 64, 67, 70):
        ax.axhline(lat, color="#4e675b", linestyle="--", linewidth=0.8)
    ax.set_xlim(10, 25)
    ax.set_ylim(54.8, 70.1)
    ax.set_aspect(1 / np.cos(np.deg2rad(62.5)))
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.11,
        0.045,
        "Cells can cross national borders and contain water. The curves describe\n"
        "represented Swedish-centre grids, not total Swedish land area. Latitude\n"
        "bands are summaries, not ecological regions or continuous spatial predictions.",
        fontsize=9,
        linespacing=1.7,
        color="#4b5552",
    )
    save(fig, output, "grid-support")


def main() -> None:
    """Render all saved-study figures to a new explicit output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Figure output must be absent")
    rows = json.loads((args.study / "trajectories.json").read_text())["rows"]
    if not rows:
        raise ValueError("Saved study has no trajectories")
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "svg.fonttype": "none",
            "svg.hashsalt": "bijux-swedish-landscape-history",
            "pdf.fonttype": 42,
            "axes.titlepad": 8,
        }
    )
    args.output.mkdir(parents=True)
    trajectory_figure(rows, args.output, recent=True)
    trajectory_figure(rows, args.output, recent=False)
    coverage_figure(rows, args.output)
    boundary_figure(rows, args.output)
    sensitivity_figure(rows, args.output)
    support_map(
        json.loads(
            (
                args.repository
                / "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson"
            ).read_text()
        ),
        json.loads(
            (args.repository / "data/boundaries/raw/sweden.geojson").read_text()
        ),
        args.output,
    )
    (args.output / "rendering.json").write_text(
        json.dumps(
            {
                "matplotlib": matplotlib.__version__,
                "figures": 6,
                "formats": ["svg", "pdf", "png"],
                "uncertainty_bands": False,
                "temporal_interpolation": False,
                "inputs": [
                    {
                        "path": str(path.relative_to(args.repository.resolve()))
                        if path.is_relative_to(args.repository.resolve())
                        else str(path),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                    for path in (
                        Path(__file__).resolve(),
                        args.study.resolve() / "trajectories.json",
                        args.repository.resolve()
                        / "data/boundaries/raw/sweden.geojson",
                        args.repository.resolve()
                        / "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson",
                    )
                ],
            },
            indent=2,
        )
        + "\n"
    )
    print(args.output)


if __name__ == "__main__":
    main()
