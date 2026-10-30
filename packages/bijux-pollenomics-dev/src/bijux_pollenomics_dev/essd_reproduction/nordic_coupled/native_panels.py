"""Project admitted FLINK native panels into separate declared point-age windows."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..physical_forward.inputs import digest, require
from .native_panel_rows import (
    IDENTITY,
    NEGATIVE_SAMPLES,
    TAXA,
    WINDOWS,
    _age,
    _integer,
    _number,
    _object,
    _panel,
    encoded,
    read_native,
)


def project(source_object: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    """Retain the complete native cohort, then separately project point-age windows."""
    chronology_record, samples = read_native(source_object, protocol)
    chronology = _object(chronology_record["chronology"])
    projected: list[dict[str, Any]] = []
    for sample in samples:
        selected_age = _age(sample, chronology["chronologyname"])
        point = selected_age["age"]
        windows = [list(w) for w in WINDOWS if w[0] <= point < w[1]]
        require(len(windows) <= 1, "Overlapping window membership")
        projected.append(
            {
                "sample_id": sample["sampleid"],
                "analysisunit_id": _integer(sample["analysisunitid"]),
                "native_depth": _number(sample["depth"]),
                "native_thickness": sample["thickness"],
                "native_ages": deepcopy(sample["ages"]),
                "selected_age": selected_age,
                "nonnegative_age": point >= 0,
                "window": windows[0] if windows else None,
                "age_disposition": "negative_native_age_retained"
                if point < 0
                else "in_requested_window"
                if windows
                else "outside_requested_windows",
                "source_support_sha256": digest(encoded(sample)),
                **_panel(sample),
            }
        )
    negative = [r["sample_id"] for r in projected if not r["nonnegative_age"]]
    require(
        negative == list(NEGATIVE_SAMPLES) and len(projected) - len(negative) == 106,
        "Native nonnegative/negative population differs",
    )
    windows_out = []
    for window in WINDOWS:
        members = [
            r for r in projected if r["nonnegative_age"] and r["window"] == list(window)
        ]
        complete = bool(members) and all(r["panel_complete"] for r in members)
        counts = (
            [sum(r["panel_counts"][i] for r in members) for i in range(2)]
            if complete
            else None
        )
        pollen_n = (
            sum(r["pollen_N"] for r in members)
            if members and all(r["pollen_N"] is not None for r in members)
            else None
        )
        panel_n = sum(counts) if counts is not None else None
        windows_out.append(
            {
                "window_cal_bp_half_open": list(window),
                "sample_ids": [r["sample_id"] for r in members],
                "status": "empty"
                if not members
                else "refused_incomplete_literal_panel"
                if not complete
                else "refused_zero_panel"
                if panel_n == 0
                else "projected",
                "panel_counts": counts,
                "panel_N": panel_n,
                "pollen_N": pollen_n,
                "excluded_pollen_N": pollen_n - panel_n
                if pollen_n is not None and panel_n is not None
                else None,
                "support_sha256": digest(
                    encoded(
                        {
                            "window": window,
                            "protocol": protocol,
                            "members": [
                                {
                                    k: r[k]
                                    for k in (
                                        "sample_id",
                                        "selected_age",
                                        "source_support_sha256",
                                        "literal_states",
                                    )
                                }
                                for r in members
                            ],
                        }
                    )
                ),
            }
        )
    return {
        "schema_version": "flink-native-panel-results.v1",
        "source": deepcopy(protocol["source"]),
        "identity": dict(IDENTITY),
        "axis": deepcopy(list(TAXA)),
        "chronology": {
            "default_chronology_id": 38438,
            "native_metadata": deepcopy(chronology),
            "native_record_sha256": digest(encoded(chronology_record)),
            "declared_BP_reference_epoch_AD": 1950,
            "sample_bounds_are_not_model_endpoints": True,
        },
        "sample_count": 109,
        "nonnegative_age_count": 106,
        "negative_age_sample_ids": negative,
        "samples": projected,
        "windows": windows_out,
        "scope": "Literal native two-taxon pollen/NISP projection only. Pollen_N includes all literal pollen/NISP labels, not a certified terrestrial denominator; excluded_pollen_N is literal nonpanel pollen mass, not synonym mapping. Point-window membership is not age uncertainty or interpolation. No geometry, parameter, model, source-rights, historical workbook correction or qualified scientific acceptance.",
        "engine_calls": 0,
    }
