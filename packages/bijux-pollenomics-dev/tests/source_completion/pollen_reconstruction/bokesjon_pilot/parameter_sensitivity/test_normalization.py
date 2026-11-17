"""Generated source-scale controls; no empirical payloads or model calls."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.parameter_sensitivity import (
    normalization,
)


def encode(value):
    return json.dumps(value, sort_keys=True).encode()


def fixture():
    names = ["Betula", "Ulmus", "Poaceae"] + [f"Generated{i}" for i in range(28)]
    (authors, pairs, rows) = ([], [], [])
    for name in names:
        (alpha, nominal, speed) = {
            "Betula": ("5.10571", "5.106", "0.024"),
            "Ulmus": ("1.27", "1.27", "0.032"),
        }.get(name, ("1", "1", "0.02"))
        authors.append(
            {
                "author_target": name,
                "alpha_source_text": alpha,
                "fall_speed_source_text": speed,
            }
        )
        pairs.append(
            {
                "author_target": name,
                "published_parameter_name": name,
                "author_alpha": alpha,
                "published_ppe": nominal,
                "alpha_difference": "-0.00029" if name == "Betula" else "0",
                "author_vg": speed,
                "published_fsp": speed,
                "published_fsp_footnote": False,
            }
        )
        rows.append(
            {
                "parameter_source_name": name,
                "parameter_ppe_source_text": nominal + " (0.23)",
                "parameter_fsp_source_text": speed,
            }
        )
    docs = [
        {
            "schema_version": normalization.SCHEMAS[0],
            "author_target_count": 31,
            "parameters": authors,
        },
        {
            "schema_version": normalization.SCHEMAS[1],
            "parameter_count": 31,
            "rows": pairs,
            "sd_exceptions": ["generated-A", "generated-B", "generated-C"],
        },
        {
            "schema_version": normalization.SCHEMAS[2],
            "parameter_row_count": 31,
            "rows": rows,
        },
    ]
    request = {
        "parameters": [
            {"taxon": "Betula", "ppe": 5.106, "ppe_sd": 0.23, "fallspeed_m_s": 0.024},
            {"taxon": "Ulmus", "ppe": 1.27, "ppe_sd": 0.17, "fallspeed_m_s": 0.032},
        ]
    }
    raw_source = encode(
        {"statistical_semantics": {"rpp_units": "Poaceae-relative RPP"}}
    )
    metadata = {
        "/generated/" + name: {
            "sha256": sha256(
                raw_source if name == "source.json" else name.encode()
            ).hexdigest(),
            "bytes": len(raw_source if name == "source.json" else name.encode()),
        }
        for name in (
            "source.json",
            "original-study-estimates.csv",
            "synthesized-estimates.csv",
        )
    }
    reference = {
        "reference_normalization": "Poaceae-relative RPP",
        "source_pins": [
            dict(path=Path(path).name, **pin) for (path, pin) in metadata.items()
        ],
        "synthesized_rows": [
            {
                "taxon": "Poaceae",
                "taxonomic_level": "family",
                "region": "Europe",
                "source_workbook": "originals/synthesized-rpp.xlsx",
                "source_sheet": "Worksheet 1",
                "source_row": "81",
                "rpp_cell": "G81",
                "rpp_sd_cell": "H81",
                "nominal_rpp_available": True,
                "rpp": "1",
                "rpp_sd": "0",
            }
        ],
    }
    return (request, docs, reference, {"metadata": metadata}, raw_source)


def bind(parts, mutate=None):
    (request, docs, reference, scope, raw_source) = parts
    (pins, buffers) = ({}, {"reference-source": raw_source})
    for index in (0, 2, 1):
        role = normalization.ROLES[index]
        if index == 1:
            docs[1]["inputs"] = [
                {
                    "path": pins[r]["public_source_path"],
                    "sha256": pins[r]["sha256"],
                    "bytes": pins[r]["bytes"],
                }
                for r in (normalization.ROLES[0], normalization.ROLES[2])
            ]
        raw = encode(docs[index])
        buffers[role] = raw
        pins[role] = {
            "path": "/generated/" + role + ".json",
            "public_source_path": normalization.PUBLIC_PREFIX + role + "/report.json",
            "public_revision": "c198c998a2d7b6866d6fd10869a0bbe7321ad1fe",
            "sha256": sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    scope["normalization_evidence"] = pins
    packet = encode({"role": "parameters", "parameters": request["parameters"]})
    if mutate:
        packet = mutate(scope, buffers, packet)
    return normalization.bind(request, packet, reference, buffers, scope)


def test_preserves_rounding_sd_and_inputs():
    parts = fixture()
    prior = deepcopy(parts)
    result = bind(parts)
    assert result["baseline_rounding"]["substitution_performed"] is False
    assert result["baseline_display_trace"][0]["original_ppe_sd_unchanged"] == 0.23
    assert result["source_sd_correspondence_not_used"]["sd_exceptions"] == [
        "generated-A",
        "generated-B",
        "generated-C",
    ]
    assert result["SD_law_admitted"] is False
    assert result["native2025_fall_speed_used"] is False
    assert parts[0] == prior[0] and parts[2] == prior[2]


@pytest.mark.parametrize(
    "change",
    [
        "request_rounding",
        "author_nominal",
        "native_fsp",
        "axis_duplicate",
        "row_owner",
        "reference_rpp",
        "normalization_label",
        "reference_pin",
    ],
)
def test_incompatible_authenticated_structures_refuse(change):
    p = fixture()
    if change == "request_rounding":
        p[0]["parameters"][0]["ppe"] = 5.10571
    if change == "author_nominal":
        p[1][0]["parameters"][0]["alpha_source_text"] = "5.2"
    if change == "native_fsp":
        p[1][2]["rows"][0]["parameter_fsp_source_text"] = ".025"
    if change == "axis_duplicate":
        p[1][0]["parameters"][-1]["author_target"] = "Betula"
    if change == "row_owner":
        p[2]["synthesized_rows"][0]["source_row"] = "80"
    if change == "reference_rpp":
        p[2]["synthesized_rows"][0]["rpp"] = "2"
    if change == "normalization_label":
        p[2]["reference_normalization"] = "another reference"
    if change == "reference_pin":
        p[2]["source_pins"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        bind(p)


@pytest.mark.parametrize("change", ["missing", "changed_bytes", "parameter_packet"])
def test_missing_or_changed_bound_buffers_refuse(change):

    def mutate(scope, buffers, packet):
        if change == "missing":
            del scope["normalization_evidence"][normalization.ROLES[0]]
        if change == "changed_bytes":
            buffers[normalization.ROLES[0]] += b" "
        if change == "parameter_packet":
            return encode({"role": "parameters", "parameters": []})
        return packet

    with pytest.raises(ValueError):
        bind(fixture(), mutate)
