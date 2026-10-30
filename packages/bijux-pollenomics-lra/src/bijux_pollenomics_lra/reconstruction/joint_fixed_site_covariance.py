"""Joint conditional count/PPE covariance with explicit reused count support."""

from __future__ import annotations

from dataclasses import dataclass
import re

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import _reject_masked_values

PROFILE = "reveals-joint-fixed-site-delta-covariance"


@dataclass(frozen=True, slots=True)
class CountSupport:
    """Identity of one fixed native panel count observation in an age window."""

    collection_unit_id: int
    dataset_id: int
    chronology_id: int
    younger_cal_bp: float
    older_cal_bp: float
    source_sha256: str


@dataclass(frozen=True, slots=True)
class ConditionalResultInput:
    """One closed panel composition with frozen geometry and literal PPE axes."""

    result_id: str
    support: CountSupport
    parameter_ids: tuple[str, ...]
    counts: np.ndarray
    deposition: np.ndarray
    taxon_measured: np.ndarray


@dataclass(frozen=True, slots=True)
class JointFixedSiteCovariance:
    """Global result-axis cover and separate conditional covariance components."""

    result_ids: tuple[str, ...]
    result_slices: tuple[slice, ...]
    parameter_ids: tuple[str, ...]
    cover: np.ndarray
    count_jacobian: np.ndarray
    ppe_jacobian: np.ndarray
    counting_covariance: np.ndarray
    ppe_covariance: np.ndarray
    total_covariance: np.ndarray
    distinct_count_supports: int
    profile: str = PROFILE


def _support(value: CountSupport) -> None:
    if not isinstance(value, CountSupport) or any(
        type(key) is not int or key <= 0
        for key in (value.collection_unit_id, value.dataset_id, value.chronology_id)
    ):
        raise ValidationError("Joint count support requires positive native identities")
    if (
        type(value.younger_cal_bp) not in (int, float)
        or type(value.older_cal_bp) not in (int, float)
        or not np.isfinite([value.younger_cal_bp, value.older_cal_bp]).all()
        or not 0 <= value.younger_cal_bp < value.older_cal_bp
        or not isinstance(value.source_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", value.source_sha256) is None
    ):
        raise ValidationError("Joint count support window/source identity is invalid")


def _covariance(value: np.ndarray, size: int) -> np.ndarray:
    _reject_masked_values(value, "ppe_covariance")
    raw = np.asarray(value)
    if raw.dtype.kind not in "iuf" or raw.shape != (size, size):
        raise ValidationError("Joint PPE covariance axes/type differ")
    cov = np.asarray(raw, dtype=float)
    if not np.isfinite(cov).all():
        raise ValidationError("Joint PPE covariance is not finite")
    scale = float(np.max(np.abs(cov)))
    normalized = cov / scale if scale else cov
    diagonal = np.diag(cov)
    if (
        np.any(diagonal < 0)
        or np.any(cov[diagonal == 0] != 0)
        or np.any(cov[:, diagonal == 0] != 0)
        or not np.allclose(normalized, normalized.T, atol=1e-12, rtol=0)
        or np.linalg.eigvalsh(normalized).min() < -1e-12
    ):
        raise ValidationError("Joint PPE covariance is not symmetric PSD")
    return cov


def joint_fixed_site_covariance(
    results: tuple[ConditionalResultInput, ...],
    *,
    parameter_ids: tuple[str, ...],
    ppe: np.ndarray,
    ppe_covariance: np.ndarray,
    assume_disjoint_window_count_independence: bool,
    assume_distinct_unit_count_independence: bool,
) -> JointFixedSiteCovariance:
    """Propagate shared PPE and reused counts; hold all source support fixed.

    Every binary64 reciprocal deposition/PPE factor must remain finite and
    positive, including zero-count axes of the returned count derivative.
    Positive corrected counts must remain positive after closure; a taxon
    cannot disappear solely through numerical underflow.
    Overflow of the parameter product refuses even when an alternate
    evaluation could represent its reciprocal.
    Counts on identical support are one multinomial latent observation, even
    across geometry alternatives. Same-unit distinct windows are independent
    only under the explicit fixed-point/disjoint-window working assumption.
    Different native units are independent only under their separate declared
    counting assumption. Neither assumption establishes environmental or
    temporal independence. Overlapping or alternate-chronology same-unit
    observations refuse because their cross-count covariance is unresolved.
    Counts and PPE have zero cross-covariance under an explicit conditional
    working independence assumption; that relationship is not observed.
    Endogenous or count-correlated PPE requires cross terms not supplied by
    this conditional profile.
    """
    if (
        not isinstance(results, (tuple, list))
        or not results
        or len(results) > 256
        or any(not isinstance(item, ConditionalResultInput) for item in results)
        or any(
            not isinstance(item.result_id, str) or not item.result_id
            for item in results
        )
        or len({item.result_id for item in results}) != len(results)
        or not isinstance(parameter_ids, (tuple, list))
        or not parameter_ids
        or any(not isinstance(key, str) or not key for key in parameter_ids)
        or len(set(parameter_ids)) != len(parameter_ids)
        or type(assume_disjoint_window_count_independence) is not bool
        or type(assume_distinct_unit_count_independence) is not bool
    ):
        raise ValidationError("Joint result/parameter identities or assumptions differ")
    parameter_ids = tuple(parameter_ids)
    _reject_masked_values(ppe, "ppe")
    raw_p = np.asarray(ppe)
    if raw_p.dtype.kind not in "iuf" or raw_p.shape != (len(parameter_ids),):
        raise ValidationError("Joint PPE values do not bind the global parameter axis")
    p = np.asarray(raw_p, dtype=float)
    if not np.isfinite(p).all() or np.any(p <= 0):
        raise ValidationError("Joint PPE values must be finite and positive")
    cp = _covariance(ppe_covariance, len(parameter_ids))
    index = {key: column for column, key in enumerate(parameter_ids)}
    groups: dict[CountSupport, list[int]] = {}
    prepared = []
    offsets = [0]
    for number, item in enumerate(results):
        _support(item.support)
        if (
            not isinstance(item.parameter_ids, (tuple, list))
            or len(item.parameter_ids) < 2
            or any(not isinstance(key, str) or not key for key in item.parameter_ids)
            or len(set(item.parameter_ids)) != len(item.parameter_ids)
            or any(key not in index for key in item.parameter_ids)
        ):
            raise ValidationError("Joint literal panel parameter axis differs")
        _reject_masked_values(item.counts, "counts")
        _reject_masked_values(item.deposition, "deposition")
        _reject_masked_values(item.taxon_measured, "taxon_measured")
        raw_n = np.asarray(item.counts)
        raw_k = np.asarray(item.deposition)
        mask = np.asarray(item.taxon_measured)
        size = len(item.parameter_ids)
        if (
            raw_n.dtype.kind not in "iuf"
            or raw_k.dtype.kind not in "iuf"
            or raw_n.shape != (size,)
            or raw_k.shape != (size,)
            or mask.dtype != bool
            or mask.shape != (size,)
            or not mask.all()
            or (raw_n.dtype.kind in "iu" and any(abs(int(v)) >= 2**53 for v in raw_n))
        ):
            raise ValidationError("Joint count/deposition/measured axes differ")
        n = np.asarray(raw_n, dtype=float)
        k = np.asarray(raw_k, dtype=float)
        N = float(n.sum())
        if (
            not np.isfinite(n).all()
            or np.any(n < 0)
            or np.any(n >= 2**53)
            or np.any(n != np.floor(n))
            or not 0 < N < 2**53
            or not np.isfinite(k).all()
            or np.any(k <= 0)
        ):
            raise ValidationError("Joint count/deposition values are invalid")
        columns = [index[key] for key in item.parameter_ids]
        with np.errstate(
            over="ignore", under="ignore", divide="ignore", invalid="ignore"
        ):
            a = 1 / (k * p[columns])
        if not np.isfinite(a).all() or np.any(a <= 0):
            raise ValidationError(
                "Joint correction factors are not finite and positive"
            )
        with np.errstate(
            over="ignore", under="ignore", divide="ignore", invalid="ignore"
        ):
            w = n * a
            W = float(w.sum())
        if not np.isfinite(W) or W <= 0:
            raise ValidationError("Joint corrected count total is invalid")
        with np.errstate(
            over="ignore", under="ignore", divide="ignore", invalid="ignore"
        ):
            cover = w / W
        if np.any((w > 0) & (cover == 0)):
            raise ValidationError("Joint positive cover is not representable")
        B = np.eye(size) - cover[:, None]
        with np.errstate(
            over="ignore", under="ignore", divide="ignore", invalid="ignore"
        ):
            J = B * a[None, :] / W
            H = -B * (cover / p[columns])[None, :]
        if not np.isfinite(J).all() or not np.isfinite(H).all():
            raise ValidationError("Joint conditional derivatives are not finite")
        count_cov = N * (np.diag(n / N) - np.outer(n / N, n / N))
        if item.support in groups:
            earlier = results[groups[item.support][0]]
            if tuple(earlier.parameter_ids) != tuple(
                item.parameter_ids
            ) or not np.array_equal(earlier.counts, n):
                raise ValidationError(
                    "Identical native support has different panel/count bytes"
                )
        else:
            for existing in groups:
                if existing.source_sha256 == item.support.source_sha256:
                    raise ValidationError(
                        "Same count-source digest has different native support"
                    )
                if existing.collection_unit_id == item.support.collection_unit_id:
                    if (
                        existing.dataset_id != item.support.dataset_id
                        or existing.chronology_id != item.support.chronology_id
                        or max(existing.younger_cal_bp, item.support.younger_cal_bp)
                        < min(existing.older_cal_bp, item.support.older_cal_bp)
                    ):
                        raise ValidationError(
                            "Same-unit count support overlap is unresolved"
                        )
                    if not assume_disjoint_window_count_independence:
                        raise ValidationError(
                            "Disjoint-window counting independence is undeclared"
                        )
                elif not assume_distinct_unit_count_independence:
                    raise ValidationError(
                        "Distinct-unit counting independence is undeclared"
                    )
            groups[item.support] = []
        groups[item.support].append(number)
        prepared.append((cover, J, H, columns, count_cov))
        offsets.append(offsets[-1] + size)
    total_size = offsets[-1]
    if total_size > 1536:
        raise ValidationError(
            "Joint conditional covariance axis exceeds its finite budget"
        )
    slices = tuple(slice(offsets[i], offsets[i + 1]) for i in range(len(results)))
    cover = np.concatenate([row[0] for row in prepared])
    Hglobal = np.zeros((total_size, len(parameter_ids)))
    Jglobal = np.zeros(
        (
            total_size,
            sum(len(results[members[0]].counts) for members in groups.values()),
        )
    )
    counting = np.zeros((total_size, total_size))
    for i, row in enumerate(prepared):
        Hglobal[slices[i], row[3]] = row[2]
    count_column = 0
    for members in groups.values():
        size = len(results[members[0]].counts)
        embedding = np.zeros((total_size, size))
        for i in members:
            embedding[slices[i]] = prepared[i][1]
        covariance = prepared[members[0]][4]
        with np.errstate(
            over="ignore", under="ignore", divide="ignore", invalid="ignore"
        ):
            counting += embedding @ covariance @ embedding.T
        Jglobal[:, count_column : count_column + size] = embedding
        count_column += size
    with np.errstate(over="ignore", under="ignore", divide="ignore", invalid="ignore"):
        ppe_part = Hglobal @ cp @ Hglobal.T
        combined = counting + ppe_part
    for matrix in (counting, ppe_part, combined):
        if not np.isfinite(matrix).all():
            raise ValidationError("Joint propagated covariance is not finite PSD")
        scale = float(np.max(np.abs(matrix)))
        normalized = matrix / scale if scale else matrix
        if (
            not np.isfinite(matrix).all()
            or np.linalg.eigvalsh(normalized).min() < -1e-10
        ):
            raise ValidationError("Joint propagated covariance is not finite PSD")
    for value in (cover, Jglobal, Hglobal, counting, ppe_part, combined):
        value.setflags(write=False)
    return JointFixedSiteCovariance(
        tuple(item.result_id for item in results),
        slices,
        parameter_ids,
        cover,
        Jglobal,
        Hglobal,
        counting,
        ppe_part,
        combined,
        len(groups),
    )
