"""Common-evidence contamination and early-outcome access controls."""

import pytest

from .exposure import count_free_evidence, metadata_admission


def test_parameters_source_identity_and_geometry_are_count_free() -> None:
    count_free_evidence(
        {
            "parameters": [{"taxon": "Betula", "ppe": 5.106, "ppe_sd": 0.303}],
            "source_identities": [
                {"site": 3204, "dataset": 23013, "chronology": 13366}
            ],
            "window": [2700, 3200],
            "source_epochs": {"swedish": "a" * 40},
            "radius_m": 837,
        }
    )


@pytest.mark.parametrize(
    "value",
    [
        {"counts": [3, 2]},
        {"nested": [{"source_panel_N": 12}]},
        {"path": "cal-bp-2700-3200/projection.json"},
        {"path": "BOKE-raw.json"},
        {"source_support_sha256": "a" * 64},
        {"native_sample_ids": [1]},
        {
            "source": "reports/science/pollen-reconstruction/krageholm-regional-source-support/result.json"
        },
    ],
)
def test_target_quantities_and_quantitative_source_references_refuse(
    value: object,
) -> None:
    with pytest.raises(ValueError):
        count_free_evidence(value)


def test_prepare_member_admission_excludes_raw_and_accounting() -> None:
    names = [
        "bin/experiment.json",
        "bin/BOKE-geometry.json",
        "bin/BOKE-raw.json",
        "bin/KRAGMJNY-raw.json",
        "bin/projection.json",
        "bin/parameters.json",
    ]
    assert metadata_admission(names) == [
        "bin/BOKE-geometry.json",
        "bin/experiment.json",
        "bin/parameters.json",
    ]
