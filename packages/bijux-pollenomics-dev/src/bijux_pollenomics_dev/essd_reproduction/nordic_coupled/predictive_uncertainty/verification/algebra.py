"""Independent scalar checks of a declared saved-kernel counting/PPE law.

NumPy supplies the specified PCG64 streams. Reconstruction, admission and
summary equations below do not call the draw or prediction producer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
import hashlib
import math
import struct
from typing import Any

import numpy as np

METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")
TOLERANCE = 1e-12


def require(condition: object, message: str) -> None:
    """Raise a prefixed refusal when an independent algebra condition fails."""
    if not condition:
        raise ValueError("Independent predictive uncertainty: " + message)


def finite(value: object) -> float:
    """Read a finite native integer or float while refusing other scalar types."""
    require(type(value) in (int, float), "finite native numeric scalar required")
    assert isinstance(value, int | float)
    result = float(value)
    require(math.isfinite(result), "finite native numeric scalar required")
    return result


def pair(
    values: Sequence[object], *, positive: bool = False
) -> tuple[Fraction, Fraction]:
    """Convert two native numbers to the required rational numeric domain."""
    require(len(values) == 2, "ordered two-taxon axis required")
    numbers = tuple(Fraction.from_float(finite(value)) for value in values)
    require(
        all(value > 0 if positive else value >= 0 for value in numbers), "pair domain"
    )
    return numbers[0], numbers[1]


def close(values: Sequence[Fraction]) -> tuple[Fraction, Fraction]:
    """Normalize a positive-mass nonnegative two-taxon composition."""
    require(
        len(values) == 2 and min(values) >= 0 and sum(values) > 0,
        "positive composition",
    )
    return values[0] / sum(values), values[1] / sum(values)


def rounded_percent(value: Fraction) -> float:
    """Compare the two adjacent decimal-grid floats, choosing the even tie."""
    scalar = float(value)
    integer = math.floor(abs(scalar) * 1000)
    lower, upper = integer / 1000, math.ceil(abs(scalar) * 1000) / 1000
    down, up = abs(scalar) - lower, upper - abs(scalar)
    selected = upper if up < down or (up == down and integer % 2) else lower
    return math.copysign(selected, scalar)


def regional_cover(
    counts: Sequence[object], ppe: Sequence[object], kernel: Sequence[object]
) -> tuple[Fraction, Fraction]:
    """Reconstruct two-taxon regional cover with the declared percent rounding."""
    n, alpha, k = pair(counts), pair(ppe, positive=True), pair(kernel, positive=True)
    composition = close([n[index] / (alpha[index] * k[index]) for index in range(2)])
    first, second = (
        Fraction.from_float(rounded_percent(100 * value)) / 100 for value in composition
    )
    return first, second


def signed_local(
    counts: Sequence[object],
    ppe: Sequence[object],
    regional: Sequence[Fraction],
    local_kernel: Sequence[object],
    regional_kernel: Sequence[object],
) -> tuple[Fraction, Fraction]:
    """Evaluate signed local cover without clipping its two outputs."""
    n, alpha = pair(counts), pair(ppe, positive=True)
    local, distant = pair(local_kernel), pair(regional_kernel)
    require(len(regional) == 2 and min(regional) >= 0, "regional cover axis/domain")
    relative = close([n[index] / alpha[index] for index in range(2)])
    denominator = sum(regional[index] * local[index] for index in range(2))
    require(denominator > 0, "positive LOVE background denominator")
    background = [regional[index] * distant[index] / denominator for index in range(2)]
    return (
        relative[0] * (1 + sum(background)) - background[0],
        relative[1] * (1 + sum(background)) - background[1],
    )


def admitted(values: Sequence[Fraction]) -> bool:
    """Check two-taxon cover bounds and the declared closure tolerance."""
    return (
        len(values) == 2
        and min(values) >= 0
        and max(values) <= 1
        and abs(float(sum(values) - 1)) <= TOLERANCE
    )


def weights(method: str, distances: Sequence[object]) -> tuple[Fraction, Fraction]:
    """Return fixed-baseline predictor weights while preserving distance ties."""
    require(method in METHODS, "unknown spatial method")
    distance = pair(distances)
    if method == "training_mean":
        return Fraction(1, 2), Fraction(1, 2)
    if method == "nearest_site" or min(distance) == 0:
        return close([Fraction(value == min(distance)) for value in distance])
    return close([1 / value**2 for value in distance])


def interpolated(
    covers: Sequence[Sequence[Fraction]], spatial_weights: Sequence[Fraction]
) -> tuple[Fraction, Fraction]:
    """Combine two admitted local covers with the declared spatial weights."""
    require(
        len(covers) == 2 and all(admitted(value) for value in covers),
        "both local predictors",
    )
    require(
        len(spatial_weights) == 2
        and min(spatial_weights) >= 0
        and sum(spatial_weights) == 1,
        "spatial weights",
    )
    return (
        sum(
            (spatial_weights[index] * covers[index][0] for index in range(2)),
            Fraction(),
        ),
        sum(
            (spatial_weights[index] * covers[index][1] for index in range(2)),
            Fraction(),
        ),
    )


def forward_pollen(
    cover: Sequence[Fraction],
    regional: Sequence[Fraction],
    ppe: Sequence[object],
    local_k: Sequence[Sequence[object]],
    local_fractions: Sequence[object],
    outer_k: Sequence[object],
) -> tuple[Fraction, Fraction]:
    """Combine local and regional deposition into closed pollen fractions."""
    require(admitted(cover), "forward local cover")
    alpha, distant = pair(ppe, positive=True), pair(outer_k)
    require(len(local_k) == len(local_fractions) == 2, "two local forward rings")
    rings = [pair(row) for row in local_k]
    land = [Fraction.from_float(finite(value)) for value in local_fractions]
    require(all(0 <= value <= 1 for value in land), "terrestrial fraction")
    return close(
        [
            alpha[taxon]
            * (
                regional[taxon] * distant[taxon]
                + cover[taxon]
                * sum(land[ring] * rings[ring][taxon] for ring in range(2))
            )
            for taxon in range(2)
        ]
    )


def owner_stream_key(owner_id: str) -> tuple[int, ...]:
    """Derive the fixed integer stream key from a source-owner identifier."""
    digest = hashlib.sha256(owner_id.encode("utf-8")).digest()
    return (
        0,
        *(
            int.from_bytes(digest[offset : offset + 4], "big")
            for offset in range(0, 32, 4)
        ),
    )


def replay_draws(
    owners: Mapping[str, Sequence[object]],
    means: Sequence[object],
    errors: Sequence[object],
    *,
    replicates: int,
    seed: int,
) -> tuple[list[list[float]], dict[str, list[list[int]]]]:
    """Recreate the specified library streams without the producer's helpers."""
    require(type(replicates) is int and replicates > 0, "positive replicate count")
    require(type(seed) is int and seed >= 0, "nonnegative seed")
    mu, sd = [finite(value) for value in means], [finite(value) for value in errors]
    require(
        len(mu) == len(sd) == 2 and min(sd) >= 0, "normal PPE parameter axis/domain"
    )
    require(
        all(not (mean < 0 and error == 0) for mean, error in zip(mu, sd, strict=True)),
        "impossible rejection law",
    )
    rng = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence(seed, spawn_key=(1,)))
    )
    ppe: list[list[float]] = []
    for _ in range(replicates):
        for _attempt in range(100_000):
            candidate = rng.normal(mu, sd)
            if all(value >= 0 for value in candidate):
                ppe.append([float(value) for value in candidate])
                break
        else:
            raise ValueError(
                "Independent predictive uncertainty: PPE rejection ceiling"
            )
    banks: dict[str, list[list[int]]] = {}
    for owner_id in sorted(owners):
        raw_counts = owners[owner_id]
        require(bool(owner_id) and len(raw_counts) == 2, "owner identity/count axis")
        require(
            all(type(value) is int and value >= 0 for value in raw_counts),
            "native integer owner counts",
        )
        counts: list[int] = []
        for value in raw_counts:
            assert isinstance(value, int)
            counts.append(value)
        total = sum(counts)
        require(total > 0 and total <= 2**53, "exact positive count total")
        generator = np.random.Generator(
            np.random.PCG64(
                np.random.SeedSequence(seed, spawn_key=owner_stream_key(owner_id))
            )
        )
        probability = np.array(counts, dtype=float) / total
        banks[owner_id] = [
            [int(value) for value in generator.multinomial(total, probability)]
            for _ in range(replicates)
        ]
    return ppe, banks


def compare(
    actual: object,
    expected: object,
    *,
    tolerance: float = TOLERANCE,
    relative_tolerance: float = 0,
    path: str = "packet",
) -> None:
    """Check every declared scalar, including nulls and strict integer/bool roles."""
    if isinstance(expected, Mapping):
        require(
            isinstance(actual, Mapping) and set(actual) == set(expected),
            path + " fields",
        )
        assert isinstance(actual, Mapping)
        for key, value in expected.items():
            compare(
                actual[key],
                value,
                tolerance=tolerance,
                relative_tolerance=relative_tolerance,
                path=f"{path}.{key}",
            )
    elif isinstance(expected, list | tuple):
        require(
            isinstance(actual, list | tuple) and len(actual) == len(expected),
            path + " length",
        )
        assert isinstance(actual, list | tuple)
        for index, value in enumerate(expected):
            compare(
                actual[index],
                value,
                tolerance=tolerance,
                relative_tolerance=relative_tolerance,
                path=f"{path}[{index}]",
            )
    elif type(expected) is float:
        require(
            abs(finite(actual) - expected)
            <= tolerance + relative_tolerance * abs(expected),
            path + " numeric disagreement",
        )
    else:
        require(
            type(actual) is type(expected) and actual == expected,
            path + " literal disagreement",
        )


def allowed_identity(
    case: Mapping[str, Any], bank: Mapping[str, Any]
) -> dict[str, Any]:
    """Hash only the three permitted count members and the target-free PPE."""
    owner_ids = [
        case["regional_owner_id"],
        *(row["owner_id"] for row in case["local_owners"]),
    ]
    require(
        len(set(owner_ids)) == 3 and case["target_id"] not in owner_ids,
        "target-free training owners",
    )
    owners = {row["owner_id"]: row for row in bank["owners"]}
    return {
        "case": dict(case),
        "count_owners": [
            {
                "owner_id": owner_id,
                "counts": owners[owner_id]["counts"],
                "stream_index": owners[owner_id]["stream_index"],
                "samples_sha256": hashlib.sha256(
                    b"".join(
                        struct.pack("<q", value)
                        for row in owners[owner_id]["samples"]
                        for value in row
                    )
                ).hexdigest(),
            }
            for owner_id in owner_ids
        ],
        "ppe": {
            "seed": bank["seed"],
            "replicates": bank["replicates"],
            "means": bank["ppe_means"],
            "sds": bank["ppe_sds"],
            "samples_sha256": hashlib.sha256(
                b"".join(
                    struct.pack("<d", value) for row in bank["ppe"] for value in row
                )
            ).hexdigest(),
        },
    }


def case_arrays(case: Mapping[str, Any], bank: Mapping[str, Any]) -> dict[str, Any]:
    """Replay every saved-kernel realization using scalar rational equations."""
    from .summaries import ensemble_summary

    identity = allowed_identity(case, bank)
    require(
        len(case["local_owners"]) == 2
        and type(case["selected_ring_index"]) is int
        and case["selected_ring_index"] == 1,
        "fixed two local owners/final ring",
    )
    owner_counts = {row["owner_id"]: row["samples"] for row in bank["owners"]}
    regional_rows, signed_rows, regional_refusals, ring_refusals, local_refusals = (
        [],
        [],
        [],
        [],
        [],
    )
    methods: dict[str, Any] = {}
    for method in METHODS:
        methods[method] = {
            "weights": [
                float(value) for value in weights(method, case["distances_km"])
            ],
            "cover": [],
            "pollen": [],
            "direct_pollen": [],
            "physical_minus_direct": [],
            "valid_mask": [],
            "refusals": [],
        }
    for index, alpha in enumerate(bank["ppe"]):
        reason = "ppe_nonpositive" if min(alpha) <= 0 else None
        regional = (
            regional_cover(
                owner_counts[case["regional_owner_id"]][index],
                alpha,
                case["regional_deposition"],
            )
            if reason is None
            else None
        )
        signed: list[list[list[float | None]]] = []
        selected: list[tuple[Fraction, Fraction]] = []
        ring_errors: list[list[str | None]] = []
        local_errors: list[str | None] = []
        for local in case["local_owners"]:
            if regional is None:
                signed.append([[None, None], [None, None]])
                ring_errors.append(["regional_undefined", "regional_undefined"])
                local_errors.append("regional_undefined")
                continue
            local_values = [
                signed_local(
                    owner_counts[local["owner_id"]][index],
                    alpha,
                    regional,
                    local["local_k"][ring],
                    local["regional_k"][ring],
                )
                for ring in range(2)
            ]
            signed.append([[float(value) for value in row] for row in local_values])
            ring_errors.append([None, None])
            final = local_values[1]
            local_errors.append(
                "local_selected_cover_out_of_bounds"
                if min(final) < 0 or max(final) > 1
                else "local_selected_cover_not_closed"
                if abs(float(sum(final) - 1)) > 1e-9
                else None
            )
            selected.append(final)
        regional_rows.append(
            [float(value) for value in regional]
            if regional is not None
            else [None, None]
        )
        signed_rows.append(signed)
        regional_refusals.append(reason)
        ring_refusals.append(ring_errors)
        local_refusals.append(local_errors)
        direct_covers = [
            close(pair(owner_counts[local["owner_id"]][index]))
            for local in case["local_owners"]
        ]
        for method, values in methods.items():
            weight = weights(method, case["distances_km"])
            direct = interpolated(direct_covers, weight)
            refusal = reason or (
                "required_local_predictor_undefined" if any(local_errors) else None
            )
            cover = interpolated(selected, weight) if refusal is None else None
            pollen = (
                forward_pollen(
                    cover,
                    regional,
                    alpha,
                    case["forward_local_k"],
                    case["terrestrial_fraction"],
                    case["forward_regional_k"],
                )
                if cover is not None and regional is not None
                else None
            )
            values["cover"].append(
                [float(value) for value in cover] if cover is not None else [None, None]
            )
            values["pollen"].append(
                [float(value) for value in pollen]
                if pollen is not None
                else [None, None]
            )
            values["direct_pollen"].append([float(value) for value in direct])
            values["physical_minus_direct"].append(
                [float(pollen[taxon] - direct[taxon]) for taxon in range(2)]
                if pollen is not None
                else [None, None]
            )
            values["valid_mask"].append(refusal is None)
            values["refusals"].append(refusal)
    for values in methods.values():
        values["summary"] = ensemble_summary(values["pollen"], values["valid_mask"])
        values["direct_summary"] = ensemble_summary(
            values["direct_pollen"], [True] * bank["replicates"]
        )
        values["matched_difference_summary"] = ensemble_summary(
            values["physical_minus_direct"], values["valid_mask"]
        )
    return {
        "schema_version": "krageholm-predictive-ensemble.case.v1",
        "case_id": case["case_id"],
        "target_id": case["target_id"],
        "axis": ["Betula", "Ulmus"],
        "replicates": bank["replicates"],
        "allowed_inputs": identity,
        "regional_cover": regional_rows,
        "regional_refusals": regional_refusals,
        "local_signed_cover": signed_rows,
        "local_ring_refusals": ring_refusals,
        "local_refusals": local_refusals,
        "methods": methods,
    }
