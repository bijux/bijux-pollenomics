from __future__ import annotations


def cross_proxy_posture(*, sead_count: int, human_count: int, animal_count: int) -> str:
    if sead_count and human_count and animal_count:
        return "pollen_archaeology_human_animal_context"
    if sead_count and human_count:
        return "pollen_archaeology_human_context"
    if sead_count and animal_count:
        return "pollen_archaeology_animal_context"
    if sead_count:
        return "pollen_archaeology_context"
    if human_count or animal_count:
        return "pollen_adna_context"
    return "pollen_model_only"


def number(value) -> float:  # type: ignore[no-untyped-def]
    return round(float(value), 6) if isinstance(value, (int, float)) else 0.0
