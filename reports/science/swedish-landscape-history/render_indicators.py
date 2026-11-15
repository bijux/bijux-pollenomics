"""Pair supported crop components and open-land context with published OL cover."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
from render import band_label, paired_panel, save, selected, support_label

# Limits are shared across all bands and both support views, and checked below.
INDICATORS = (
    (
        "rye",
        "Rye",
        "Rye",
        25.0,
        "Crop component: source Secale; part of total cereal-associated cover.",
    ),
    (
        "other_cereals",
        "Non-rye cereal type",
        "Cereal type",
        15.0,
        "Pooled Cerealia type excluding rye; individual wheat, barley and oats are unresolved.",
    ),
    (
        "plantain",
        "Ribwort plantain type",
        "Plantain",
        2.0,
        "Open-land context: Plantago lanceolata-type; not pasture area or grazing intensity.",
    ),
    (
        "non_cereal_herbs",
        "Non-cereal herbs",
        "Herbs",
        100.0,
        "Open-land context: seven herb types, including plantain and natural/wetland vegetation.",
    ),
)


def footer(fig: Any, note: str, *, y: float) -> None:
    """Describe the shared graphical grammar and the indicator's interpretation."""
    fig.text(
        0.10,
        y,
        "Lines: area-weighted mean · Shading: spatial grid min–max, not confidence or prediction limits.\n"
        "Joined window midpoints guide the eye; gaps stay missing. Green: open land, left axis. Orange: indicator, right.\n"
        + note
        + "\nPublished REVEALS modeled cover · Fyfe et al. 2021, PANGAEA 937075 · Githumbi et al. 2022 · CC BY 4.0.",
        fontsize=7.6,
        color="#626d66",
        linespacing=1.5,
    )


def overview(
    rows: list[dict[str, Any]],
    output: Path,
    spec: tuple[str, str, str, float, str],
    *,
    recent: bool,
) -> None:
    """Keep one comparison per band, with exactly two means and their ranges."""
    key, label, axis_label, limit, note = spec
    policy = "fixed_recent" if recent else "available"
    fig, axes = plt.subplots(5, 1, figsize=(11.8, 12.4), sharex=True)
    fig.subplots_adjust(left=0.10, right=0.90, top=0.84, bottom=0.13, hspace=0.58)
    fig.suptitle(
        f"Open land and {label.lower()}",
        x=0.10,
        ha="left",
        y=0.975,
        fontsize=20,
        weight="bold",
    )
    subtitle = (
        "Recent comparison · the same grids in every window"
        if recent
        else "Holocene history · available grids change between windows"
    )
    fig.text(0.10, 0.937, subtitle, fontsize=11, color="#626d66")
    handles = None
    for band, ax in enumerate(axes):
        data = selected(rows, band=band, policy=policy, recent=recent)
        pair = paired_panel(
            ax,
            data,
            limit,
            recent=recent,
            indicator=key,
            indicator_label=label,
            axis_label=axis_label,
        )
        if handles is None:
            handles = pair
    fig.legend(
        handles=handles,
        labels=["Open land", label],
        loc="upper left",
        bbox_to_anchor=(0.09, 0.91),
        ncol=2,
        frameon=False,
        fontsize=11,
    )
    axes[-1].set_xlabel("Age (cal BP, relative to 1950) · older → younger", labelpad=10)
    footer(fig, note, y=0.025)
    save(fig, output, "recent" if recent else "holocene")


def regional(
    rows: list[dict[str, Any]], output: Path, spec: tuple[str, str, str, float, str]
) -> None:
    """Export the same readable pair separately for every latitude band."""
    key, label, axis_label, limit, note = spec
    for band in range(5):
        data = selected(rows, band=band)
        fig, ax = plt.subplots(figsize=(11.8, 6.4))
        fig.subplots_adjust(left=0.10, right=0.90, top=0.77, bottom=0.25)
        fig.suptitle(
            f"Sweden · {band_label(data)}",
            x=0.10,
            ha="left",
            y=0.96,
            fontsize=22,
            weight="bold",
        )
        fig.text(
            0.10,
            0.885,
            f"Open land and {label.lower()} through the Holocene",
            fontsize=12,
            color="#626d66",
        )
        pair = paired_panel(
            ax,
            data,
            limit,
            recent=False,
            indicator=key,
            indicator_label=label,
            axis_label=axis_label,
        )
        ax.set_title("", loc="left")
        ax.set_title(
            f"Available support: {support_label(data)}", loc="right", fontsize=9
        )
        fig.legend(
            handles=pair,
            labels=["Open land", label],
            loc="upper left",
            bbox_to_anchor=(0.09, 0.855),
            ncol=2,
            frameon=False,
            fontsize=11,
        )
        ax.set_xlabel("Age (cal BP, relative to 1950) · older → younger", labelpad=10)
        footer(fig, note, y=0.045)
        save(fig, output, f"latitude-{55 + 3 * band}-{58 + 3 * band}")


def main() -> None:
    """Render a saved, source-bound indicator study without changing its values."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Absent figure output required")
    rows = json.loads((args.study / "trajectories.json").read_text())["rows"]
    if len(rows) != 2250:
        raise ValueError("Complete indicator cohort inventory required")
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "svg.fonttype": "none",
            "svg.hashsalt": "bijux-swedish-crop-context",
            "pdf.fonttype": 42,
            "axes.titlepad": 8,
        }
    )
    args.output.mkdir(parents=True)
    maxima = {}
    for spec in INDICATORS:
        key, _, _, limit, _ = spec
        maximum = max(r["metrics"][key]["maximum"] or 0 for r in rows)
        if maximum > limit:
            raise ValueError(f"Source maximum exceeds shared {key} axis")
        maxima[key] = maximum
        destination = args.output / key.replace("_", "-")
        destination.mkdir()
        overview(rows, destination, spec, recent=False)
        overview(rows, destination, spec, recent=True)
        regional(rows, destination, spec)
    files = [
        Path(__file__).resolve(),
        Path(__file__).resolve().with_name("render.py"),
        Path(__file__).resolve().with_name("figure_series.py"),
        args.study.resolve() / "trajectories.json",
    ]
    receipt = {
        "matplotlib": matplotlib.__version__,
        "figures": 28,
        "formats": ["png", "svg", "pdf"],
        "spatial_range_maxima": maxima,
        "fixed_right_axis_limits": {spec[0]: spec[3] for spec in INDICATORS},
        "numerical_temporal_interpolation": False,
        "confidence_intervals": False,
        "inputs": [
            {"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in files
        ],
    }
    (args.output / "rendering.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
