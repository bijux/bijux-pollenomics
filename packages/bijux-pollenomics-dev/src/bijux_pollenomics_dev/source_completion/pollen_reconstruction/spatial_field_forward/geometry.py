"""Count-free, frozen receiver geometry and independent radial-step brackets."""

from __future__ import annotations

from dataclasses import asdict
import math
from typing import Any

from pyproj import CRS, Transformer

from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus
from bijux_pollenomics_lra.dispersal.two_anchor_bounds import (
    two_anchor_annulus_step_bounds,
)
from bijux_pollenomics_lra.dispersal.two_anchor_receiver import (
    two_anchor_circular_receiver_annulus,
)

from .sources import AXIS, require


def geometry_inputs(
    protocol: dict[str, Any], fall: list[float]
) -> list[dict[str, Any]]:
    """Evaluate six taxon/place geometries without observations or scores."""
    declarations = {c["id"]: c for c in protocol["cores"]}
    numerical, physical = protocol["geometry_qualification"], protocol["physical"]
    rows = []
    for name, target in sorted(declarations.items()):
        lon, lat = target["analysis_centre_lon_lat"]
        frame = CRS.from_proj4(
            f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m"
        )
        transform = Transformer.from_crs("EPSG:4326", frame, always_xy=True)
        anchors = [c for key, c in sorted(declarations.items()) if key != name]
        xy = [transform.transform(*a["analysis_centre_lon_lat"]) for a in anchors]
        require(
            all(math.isfinite(v) for p in xy for v in p) and xy[0] != xy[1],
            "Distinct finite source anchors required",
        )
        squared = [math.fsum(v * v for v in p) for p in xy]
        require(min(squared) > 0, "Source place coincides with target place")
        weights = [squared[1] / sum(squared), squared[0] / sum(squared)]
        row: dict[str, Any] = {
            "core": name,
            "anchor_order": [a["id"] for a in anchors],
            "anchor_xy_m": xy,
            "centre_weights": weights,
            "radius_m": target["radius_m"],
            "status": "qualified",
            "taxa": [],
            "homogeneous_taxa": [],
        }
        for taxon, speed in zip(AXIS, fall, strict=True):
            arguments: dict[str, Any] = {
                "first_anchor_xy_m": xy[0],
                "second_anchor_xy_m": xy[1],
                "receiver_radius_m": target["radius_m"],
                "inner_radius_m": target["radius_m"],
                "outer_radius_m": physical["regional_extent_m"],
                "fall_speed_m_s": speed,
                "diffusion_coefficient": physical["diffusion_coefficient"],
                "turbulence_parameter": physical["turbulence_parameter"],
                "wind_speed_m_s": physical["wind_speed_m_s"],
                "absolute_tolerance": numerical["primary_absolute_tolerance"],
                "relative_tolerance": numerical["primary_relative_tolerance"],
                "quadrature_limit": numerical["quadrature_limit"],
            }
            homogeneous_arguments = {
                k: v
                for k, v in arguments.items()
                if k not in {"first_anchor_xy_m", "second_anchor_xy_m"}
            }
            try:
                old = circular_receiver_annulus(**homogeneous_arguments)
                require(
                    old.factor > 0 and math.isfinite(old.factor),
                    "Invalid homogeneous response",
                )
                row["homogeneous_taxa"].append(
                    {"taxon": taxon, "status": "qualified", **asdict(old)}
                )
            except (ValueError, ArithmeticError, RuntimeError) as error:
                row["homogeneous_taxa"].append(
                    {
                        "taxon": taxon,
                        "status": "refused_geometry",
                        "reason": f"{type(error).__name__}: {error}",
                    }
                )
            try:
                primary = two_anchor_circular_receiver_annulus(**arguments)
                reference = two_anchor_annulus_step_bounds(
                    **arguments, annulus_count=numerical["independent_annuli"]
                )
                tolerance = numerical["primary_absolute_tolerance"] + numerical[
                    "primary_relative_tolerance"
                ] * abs(primary.homogeneous_factor)
                require(
                    abs(primary.partition_residual) <= tolerance,
                    "Primary coefficient partition failed",
                )
                require(
                    primary.homogeneous_factor > 0
                    and all(x > 0 and math.isfinite(x) for x in primary.anchor_factors),
                    "Nonpositive or nonfinite physical coefficient",
                )
                require(
                    all(
                        lo - tolerance <= value <= hi + tolerance
                        for value, (lo, hi) in zip(
                            primary.anchor_factors,
                            reference.anchor_factor_bounds,
                            strict=True,
                        )
                    ),
                    "Primary coefficient outside fixed step bracket",
                )
                row["taxa"].append(
                    {
                        "taxon": taxon,
                        "fall_speed_m_s": speed,
                        "primary": asdict(primary),
                        "step_bounds": asdict(reference),
                    }
                )
            except (ValueError, ArithmeticError, RuntimeError) as error:
                row["status"] = "refused_geometry"
                row["taxa"].append(
                    {
                        "taxon": taxon,
                        "fall_speed_m_s": speed,
                        "status": "refused_geometry",
                        "reason": f"{type(error).__name__}: {error}",
                    }
                )
        rows.append(row)
    return rows
