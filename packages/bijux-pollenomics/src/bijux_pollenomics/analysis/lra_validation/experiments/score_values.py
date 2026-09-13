"""Shared descriptive observation decoding; no source or outcome-access authority."""

from __future__ import annotations

from ..contracts import ValidationRefusal, finite_number
from ..metrics import score_pollen, score_vegetation
from .configuration import object_mapping


def score_observation(
    target: str, prediction: dict[str, object], outcome: dict[str, object] | None
) -> dict[str, object]:
    if outcome is None:
        return {
            "status": "missing_observation",
            "mae_fraction": None,
            "reason": "target_not_supplied",
        }
    expected_unit = "fraction" if target == "vegetation_cover" else "count"
    unit_field = "vegetation_unit" if target == "vegetation_cover" else "pollen_unit"
    value_field = (
        "vegetation_fraction" if target == "vegetation_cover" else "pollen_count"
    )
    prediction_field = (
        "vegetation_fraction" if target == "vegetation_cover" else "pollen_fraction"
    )
    if outcome[unit_field] != expected_unit:
        raise ValidationRefusal("observation_unit_mismatch", target)
    if outcome[value_field] is None:
        return {
            "status": "missing_observation",
            "mae_fraction": None,
            "reason": "target_not_supplied",
        }
    predicted = {
        key: finite_number(value)
        for key, value in object_mapping(
            prediction[prediction_field], "prediction"
        ).items()
    }
    observed = object_mapping(outcome[value_field], value_field)
    if target == "vegetation_cover":
        values = {
            key: None if value is None else finite_number(value)
            for key, value in observed.items()
        }
        return score_vegetation(predicted, values).as_dict()
    counts: dict[str, int | None] = {}
    for key, value in observed.items():
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int)
        ):
            raise ValidationRefusal("invalid_pollen_counts", key)
        counts[key] = value
    return score_pollen(predicted, counts).as_dict()
