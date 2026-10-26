"""Run the physical inverse and retain shared-PPE contrast dependence."""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
import math
from typing import Any

import numpy as np

from bijux_pollenomics_dev.essd_reproduction.pft_covariance.lengths import (
    LengthInterval,
    sum_length_range,
)
from bijux_pollenomics_lra.api import fixed_site_cover_covariance
from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus

from .sources import TAXA, require


def sharp_ppe_variance(gradient: np.ndarray, sd: np.ndarray) -> dict[str, Any]:
    """Reuse exact vector-sum feasibility for fixed-marginal delta variance."""
    require(
        bool(
            gradient.shape == sd.shape == (len(TAXA),)
            and np.isfinite(gradient).all()
            and np.isfinite(sd).all()
            and np.all(sd >= 0)
        ),
        "Finite paired gradient/SD axes required",
    )
    magnitudes = [
        abs(Fraction.from_float(float(g)) * Fraction.from_float(float(s)))
        for g, s in zip(gradient, sd, strict=True)
    ]
    lengths = sum_length_range(tuple(LengthInterval(a, a) for a in magnitudes))
    lower, upper = lengths.lower**2, lengths.upper**2
    return {
        "lower": float(lower),
        "upper": float(upper),
        "exact_lower": str(lower),
        "exact_upper": str(upper),
    }


def ppe_jacobian(cover: np.ndarray, ppe: np.ndarray) -> np.ndarray:
    """Differentiate normalized inverse weights on the declared fixed panel."""
    return np.asarray(
        cover[:, None] * (cover[None, :] - np.eye(len(cover))) / ppe[None, :]
    )


def calculate(inputs: dict[str, Any]) -> dict[str, Any]:
    """Produce four conditional moments and all thirty predeclared contrasts."""
    protocol = inputs["protocol"]
    physical = protocol["physical"]
    radius = math.sqrt(physical["source_reported_area_ha"] * 10000 / math.pi)
    ppe = np.array([p["ppe"] for p in inputs["parameters"]])
    sd = np.array([p["published_sd"] for p in inputs["parameters"]])
    cp = np.diag(sd**2)
    response = [
        circular_receiver_annulus(
            receiver_radius_m=radius,
            inner_radius_m=radius,
            outer_radius_m=physical["regional_extent_m"],
            fall_speed_m_s=p["fall_speed_m_s"],
            diffusion_coefficient=physical["diffusion_coefficient"],
            turbulence_parameter=physical["turbulence_parameter"],
            wind_speed_m_s=physical["wind_speed_m_s"],
            absolute_tolerance=physical["quadrature_absolute_tolerance"],
            relative_tolerance=physical["quadrature_relative_tolerance"],
        )
        for p in inputs["parameters"]
    ]
    deposition = np.array([[r.factor for r in response]])
    windows, moments, gradients, count_vectors = [], [], [], []
    for source in inputs["windows"]:
        counts = np.array([source["pooled_panel_counts"]], dtype=np.int64)
        result = fixed_site_cover_covariance(
            counts,
            deposition,
            ppe,
            cp,
            taxon_measured=np.ones(counts.shape, dtype=bool),
        )
        gradient = ppe_jacobian(result.cover, ppe)
        require(
            np.allclose(
                result.ppe_covariance, gradient @ cp @ gradient.T, atol=1e-12, rtol=0
            ),
            "Physical API/PPE gradient mismatch",
        )
        windows.append(
            {
                **source,
                "cover": result.cover.tolist(),
                "counting_covariance": result.counting_covariance.tolist(),
                "ppe_gradient": gradient.tolist(),
                "ppe_covariance_diagonal": result.ppe_covariance.tolist(),
                "total_covariance_diagonal": result.total_covariance.tolist(),
                "standard_error_diagonal": result.standard_error.tolist(),
            }
        )
        moments.append(result)
        gradients.append(gradient)
        count_vectors.append(counts)
    stacked = np.vstack(gradients)
    joint = stacked @ cp @ stacked.T
    width = len(TAXA)
    for index, moment in enumerate(moments):
        section = slice(index * width, (index + 1) * width)
        joint[section, section] += moment.counting_covariance
    require(
        np.allclose(joint, joint.T, atol=1e-12, rtol=0)
        and np.linalg.eigvalsh(joint).min() >= -1e-12,
        "Shared-PPE joint covariance is not PSD",
    )
    contrasts = []
    for young, old in combinations(range(len(windows)), 2):
        for taxon, name in enumerate(TAXA):
            gradient = gradients[old][taxon] - gradients[young][taxon]
            count = float(
                moments[old].counting_covariance[taxon, taxon]
                + moments[young].counting_covariance[taxon, taxon]
            )
            diagonal = float(gradient @ cp @ gradient)
            bounds = sharp_ppe_variance(gradient, sd)
            signed_sd = np.where(gradient < 0, -sd, sd)
            witness = np.outer(signed_sd, signed_sd)
            paired_moments = [
                fixed_site_cover_covariance(
                    count_vectors[i],
                    deposition,
                    ppe,
                    witness,
                    taxon_measured=np.ones(count_vectors[i].shape, dtype=bool),
                )
                for i in (young, old)
            ]
            cross = gradients[young] @ witness @ gradients[old].T
            attained = float(
                paired_moments[0].total_covariance[taxon, taxon]
                + paired_moments[1].total_covariance[taxon, taxon]
                - 2 * cross[taxon, taxon]
            )
            require(
                abs(attained - count - bounds["upper"]) <= 1e-12
                and bounds["lower"] - 1e-12 <= diagonal <= bounds["upper"] + 1e-12,
                "Sharp PPE bound/physical API witness mismatch",
            )
            total = {"lower": count + bounds["lower"], "upper": count + bounds["upper"]}
            contrasts.append(
                {
                    "younger_window_id": windows[young]["window_id"],
                    "older_window_id": windows[old]["window_id"],
                    "taxon": name,
                    "cover_difference_older_minus_younger": float(
                        moments[old].cover[taxon] - moments[young].cover[taxon]
                    ),
                    "count_variance": count,
                    "shared_ppe_gradient": gradient.tolist(),
                    "ppe_variance_diagonal": diagonal,
                    "ppe_variance_bounds": bounds,
                    "total_variance_diagonal": count + diagonal,
                    "total_variance_bounds": total,
                    "standard_error_bounds": {
                        k: math.sqrt(v) for k, v in total.items()
                    },
                    "upper_witness_ppe_covariance": witness.tolist(),
                    "upper_witness_total_contrast_variance": attained,
                }
            )
    require(
        len(windows) == 4 and len(contrasts) == 30,
        "Declared numerical population differs",
    )
    return {
        "windows": windows,
        "contrasts": contrasts,
        "receiver_radius_m": radius,
        "physical_response": [
            {
                "taxon": name,
                "factor": r.factor,
                "estimated_absolute_error": r.estimated_absolute_error,
                "rigorous_error_bound": False,
            }
            for name, r in zip(TAXA, response, strict=True)
        ],
        "shared_diagonal_joint_covariance": joint.tolist(),
        "fixed_site_covariance_api_calls": 4 + 2 * len(contrasts),
        "receiver_response_calls": len(response),
    }
