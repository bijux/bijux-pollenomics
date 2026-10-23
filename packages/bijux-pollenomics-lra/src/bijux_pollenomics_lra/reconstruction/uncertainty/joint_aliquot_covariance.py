"""Conditional joint count/PPE covariance with explicit reused native aliquots."""

from __future__ import annotations

from dataclasses import dataclass
import re

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import _reject_masked_values
from bijux_pollenomics_lra.reconstruction.joint_fixed_site_covariance import _covariance

PROFILE = "reveals-joint-aliquot-delta-covariance"


@dataclass(frozen=True, slots=True)
class AliquotCountInput:
    """One counted native sample, before any chronology-window aggregation."""

    observation_id: str
    collection_unit_id: int
    dataset_id: int
    native_sample_id: int
    source_sha256: str
    parameter_ids: tuple[str, ...]
    counts: np.ndarray
    taxon_measured: np.ndarray


@dataclass(frozen=True, slots=True)
class AliquotResultInput:
    """One composition of the declared common panel on fixed sample membership."""

    result_id: str
    observation_ids: tuple[str, ...]
    parameter_ids: tuple[str, ...]
    deposition: np.ndarray


@dataclass(frozen=True, slots=True)
class JointAliquotCovariance:
    """Global result-axis covariance, retaining primitive count and PPE axes."""

    result_ids: tuple[str, ...]
    result_slices: tuple[slice, ...]
    observation_ids: tuple[str, ...]
    parameter_ids: tuple[str, ...]
    cover: np.ndarray
    count_jacobian: np.ndarray
    ppe_jacobian: np.ndarray
    counting_covariance: np.ndarray
    ppe_covariance: np.ndarray
    total_covariance: np.ndarray
    distinct_count_observations: int
    profile: str = PROFILE


def joint_aliquot_covariance(
    observations: tuple[AliquotCountInput, ...],
    results: tuple[AliquotResultInput, ...],
    *,
    parameter_ids: tuple[str, ...],
    ppe: np.ndarray,
    ppe_covariance: np.ndarray,
    assume_distinct_aliquot_count_independence: bool,
    assume_count_ppe_independence: bool,
) -> JointAliquotCovariance:
    """Propagate one common measured-panel multinomial per native sample.

    Membership and responses are fixed. A sample used in multiple results is
    one latent count vector, even when different chronology fields select its
    windows. Its multinomial total is the declared common panel sum; changing
    panels requires a different model, rather than per-result renormalization.
    Distinct samples have independent conditional counting error, without an
    environmental or temporal independence claim. One global PPE vector is
    shared across every result. Count/PPE cross terms are declared zero.
    No chronology probability, site bootstrap or interval calibration is fitted.
    """
    if (
        not isinstance(observations, (tuple, list))
        or not 0 < len(observations) <= 512
        or not isinstance(results, (tuple, list))
        or not 0 < len(results) <= 256
        or any(not isinstance(x, AliquotCountInput) for x in observations)
        or any(not isinstance(x, AliquotResultInput) for x in results)
        or not isinstance(parameter_ids, (tuple, list))
        or not 2 <= len(parameter_ids) <= 64
        or any(not isinstance(x, str) or not x for x in parameter_ids)
        or len(set(parameter_ids)) != len(parameter_ids)
        or type(assume_distinct_aliquot_count_independence) is not bool
        or not assume_distinct_aliquot_count_independence
        or type(assume_count_ppe_independence) is not bool
        or not assume_count_ppe_independence
    ):
        raise ValidationError("Joint aliquot axes, budget or assumptions differ")
    parameter_ids = tuple(parameter_ids)
    size = len(parameter_ids)
    if (
        size * len(results) > 1536
        or size * size * len(results) * len(observations) > 16_777_216
    ):
        raise ValidationError("Joint aliquot result axis exceeds its finite budget")
    _reject_masked_values(ppe, "ppe")
    raw_p = np.asarray(ppe)
    if raw_p.dtype.kind not in "iuf" or raw_p.shape != (size,):
        raise ValidationError("Joint aliquot PPE axis/type differs")
    p = np.asarray(raw_p, dtype=float)
    if not np.isfinite(p).all() or np.any(p <= 0):
        raise ValidationError("Joint aliquot PPE must be finite and positive")
    cp = _covariance(ppe_covariance, size)
    observed: dict[str, int] = {}
    native: set[tuple[int, int]] = set()
    counts = []
    covariances = []
    for i, row in enumerate(observations):
        identity = (row.collection_unit_id, row.dataset_id, row.native_sample_id)
        if (
            not isinstance(row.observation_id, str)
            or not row.observation_id
            or row.observation_id in observed
            or any(type(x) is not int or x <= 0 for x in identity)
            or (row.dataset_id, row.native_sample_id) in native
            or not isinstance(row.source_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", row.source_sha256) is None
            or not isinstance(row.parameter_ids, (tuple, list))
            or tuple(row.parameter_ids) != parameter_ids
        ):
            raise ValidationError("Joint aliquot observation identity/axis differs")
        if not isinstance(row.counts, np.ndarray):
            raise ValidationError(
                "Joint aliquot counts require an explicit numeric array"
            )
        _reject_masked_values(row.counts, "counts")
        _reject_masked_values(row.taxon_measured, "taxon_measured")
        raw = np.asarray(row.counts)
        measured = np.asarray(row.taxon_measured)
        if (
            raw.dtype.kind not in "iuf"
            or raw.shape != (size,)
            or measured.dtype != bool
            or measured.shape != (size,)
            or not measured.all()
            or (raw.dtype.kind in "iu" and any(abs(int(x)) >= 2**53 for x in raw))
        ):
            raise ValidationError("Joint aliquot count/measured axis differs")
        n = np.asarray(raw, dtype=float)
        total = float(n.sum())
        if (
            not np.isfinite(n).all()
            or np.any(n < 0)
            or np.any(n >= 2**53)
            or np.any(n != np.floor(n))
            or not 0 < total < 2**53
        ):
            raise ValidationError("Joint aliquot counts are not finite panel integers")
        observed[row.observation_id] = i
        native.add((row.dataset_id, row.native_sample_id))
        counts.append(n)
        covariances.append(np.diag(n) - np.outer(n, n) / total)
    output_size = size * len(results)
    J = np.zeros((output_size, size * len(observations)))
    H = np.zeros((output_size, size))
    cover = np.empty(output_size)
    identifiers: set[str] = set()
    used: set[str] = set()
    slices = tuple(slice(i * size, (i + 1) * size) for i in range(len(results)))
    for result, sl in zip(results, slices, strict=True):
        if (
            not isinstance(result.result_id, str)
            or not result.result_id
            or result.result_id in identifiers
            or not isinstance(result.observation_ids, (tuple, list))
            or not result.observation_ids
            or any(
                not isinstance(x, str) or x not in observed
                for x in result.observation_ids
            )
            or len(set(result.observation_ids)) != len(result.observation_ids)
            or not isinstance(result.parameter_ids, (tuple, list))
            or tuple(result.parameter_ids) != parameter_ids
        ):
            raise ValidationError("Joint aliquot result membership/axis differs")
        identifiers.add(result.result_id)
        used.update(result.observation_ids)
        _reject_masked_values(result.deposition, "deposition")
        raw_k = np.asarray(result.deposition)
        if raw_k.dtype.kind not in "iuf" or raw_k.shape != (size,):
            raise ValidationError("Joint aliquot deposition axis/type differs")
        k = np.asarray(raw_k, dtype=float)
        if not np.isfinite(k).all() or np.any(k <= 0):
            raise ValidationError(
                "Joint aliquot deposition must be finite and positive"
            )
        members = [observed[x] for x in result.observation_ids]
        n = np.sum([counts[i] for i in members], axis=0)
        if not float(n.sum()) < 2**53:
            raise ValidationError(
                "Joint aliquot aggregate count total exceeds precision"
            )
        with np.errstate(
            over="ignore", under="ignore", divide="ignore", invalid="ignore"
        ):
            a = 1 / (k * p)
            w = n * a
        with np.errstate(
            over="ignore", under="ignore", divide="ignore", invalid="ignore"
        ):
            W = float(w.sum())
            if (
                not np.isfinite(a).all()
                or np.any(a <= 0)
                or not np.isfinite(W)
                or W <= 0
            ):
                raise ValidationError(
                    "Joint aliquot correction is not finite and positive"
                )
            q = w / W
            B = np.eye(size) - q[:, None]
            derivative = B * a[None, :] / W
        cover[sl] = q
        with np.errstate(
            over="ignore", under="ignore", divide="ignore", invalid="ignore"
        ):
            H[sl] = -B * (q / p)[None, :]
        for i in members:
            J[sl, i * size : (i + 1) * size] = derivative
    if used != set(observed):
        raise ValidationError("Joint aliquot observation is unreferenced")
    if not np.isfinite(J).all() or not np.isfinite(H).all():
        raise ValidationError("Joint aliquot derivatives are not finite")
    counting = np.zeros((output_size, output_size))
    with np.errstate(over="ignore", under="ignore", divide="ignore", invalid="ignore"):
        for i, covariance in enumerate(covariances):
            embedding = J[:, i * size : (i + 1) * size]
            counting += embedding @ covariance @ embedding.T
        ppe_part = H @ cp @ H.T
        combined = counting + ppe_part
    for matrix in (counting, ppe_part, combined):
        if not np.isfinite(matrix).all():
            raise ValidationError("Joint aliquot covariance is not finite symmetric")
        scale = float(np.max(np.abs(matrix)))
        normalized = matrix / scale if scale else matrix
        if not np.isfinite(matrix).all() or not np.allclose(
            normalized, normalized.T, atol=1e-12, rtol=0
        ):
            raise ValidationError("Joint aliquot covariance is not finite symmetric")
        if np.linalg.eigvalsh(normalized).min() < -1e-10:
            raise ValidationError("Joint aliquot covariance is not finite PSD")
    for value in (cover, J, H, counting, ppe_part, combined):
        value.setflags(write=False)
    return JointAliquotCovariance(
        tuple(x.result_id for x in results),
        slices,
        tuple(x.observation_id for x in observations),
        parameter_ids,
        cover,
        J,
        H,
        counting,
        ppe_part,
        combined,
        len(observations),
    )
