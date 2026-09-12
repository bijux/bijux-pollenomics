"""Per-fold observation admission and outcome-free geometric support."""

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    ValidationRefusal,
    grouped_leave_one_out,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    ExperimentSpec,
    InputReference,
    object_list,
    object_mapping,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
    make_request,
    read_geometry,
    read_reference,
    read_training_observation,
)


def store(root: Path, name: str, value: object) -> dict[str, str]:
    data = (json.dumps(value, sort_keys=True) + "\n").encode()
    (root / name).write_bytes(data)
    return {"path": name, "sha256": hashlib.sha256(data).hexdigest()}


def fixture_inputs(root: Path, count: int = 4) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    evidence = []
    for role in ("chronology", "taxa", "parameters", "dependency_lock", "decision"):
        ref = store(root, role + ".json", {"synthetic_role": role})
        evidence.append({"evidence_id": role, "role": role, **ref})
    template = {
        "schema_version": "lra-request.v1",
        "operation": "lra",
        "data_kind": "synthetic",
        "purpose": "exploratory",
        "method_profile": "disqover-0.9.14-source-compatible",
        "taxa": ["Alnus", "Betula"],
        "pollen_unit": "count",
        "configuration": {
            "seed": 7,
            "love": {
                "method": "analytical",
                "stochastic": False,
                "max_ring": 2,
                "repeats": 2,
            },
            "reveals": {"stochastic": False, "iterations": 2},
        },
        "parameters": [
            {"taxon": "Alnus", "fallspeed_m_s": 0.024, "ppe": 4, "ppe_sd": 0},
            {"taxon": "Betula", "fallspeed_m_s": 0.024, "ppe": 3, "ppe_sd": 0},
        ],
        "evidence": evidence,
        "exclusions": [],
        "uncertainty_omissions": [
            "chronology",
            "basin_geometry",
            "parameter_domain",
            "spatial_model",
            "ppe_covariance",
        ],
        "temporal_matching": {
            "rule": "declared_bin_stationarity",
            "decision_evidence_id": "decision",
            "bins": [{"bin_id": "test-bin", "younger_bp": 5400, "older_bp": 5600}],
        },
        "versions": dict.fromkeys(
            ("binning", "chronology", "geometry", "parameters", "taxonomy"),
            "synthetic-v1",
        ),
    }
    sites = []
    for i in range(count):
        name = f"p{i + 1:02}"
        radius = 20 + 2 * i
        metadata = {
            "site_id": name,
            "sample_id": name + "-sample",
            "coordinate": 1,
            "bin_id": "test-bin",
            "age_type": "calendar_bp",
            "age_support_bp": [[5400, 5600]],
            "chronology_evidence_id": "chronology",
        }
        edges = [radius, (radius + 1000) / 2, 1000, 10000, 100000]
        forward = [
            {
                "inner_m": lo,
                "outer_m": hi,
                "mean_m": (lo + hi) / 2,
                "ring_area_m2": math.pi * (hi**2 - lo**2),
                "terrestrial_area_m2": math.pi * (hi**2 - lo**2),
            }
            for lo, hi in zip(edges[:-1], edges[1:], strict=True)
        ]
        inversion = json.loads(json.dumps(forward[:2]))
        inversion[0]["inner_m"] = radius + 1
        inversion[0]["ring_area_m2"] = math.pi * (
            inversion[0]["outer_m"] ** 2 - (radius + 1) ** 2
        )
        inversion[0]["terrestrial_area_m2"] = inversion[0]["ring_area_m2"]
        geo = {
            "basin": {"diameter_m": radius * 2, "site_type": "lake"},
            "inversion_rings": inversion,
            "forward_rings": forward,
            "sample_metadata": metadata,
            "longitude": 15 + i * 0.025,
            "latitude": 57 + i * 0.01,
        }
        sites.append(
            {
                "record_id": name,
                "site_id": name,
                "identity_keys": [],
                "geometry": store(root, name + "-geometry.json", geo),
                "raw": store(
                    root,
                    name + "-raw.json",
                    {
                        "data_kind": "synthetic",
                        "taxa": template["taxa"],
                        "sample": dict(metadata, counts=[600 + i, 400 - i]),
                    },
                ),
            }
        )
    return {
        "schema_version": "lra-experiment.v1",
        "profile": "synthetic-withheld-site-baselines-v1",
        "sites": sites,
        "regional_priority": [site["record_id"] for site in sites],
        "baselines": ["training_mean", "nearest_site", "inverse_distance_squared"],
        "local_ring_count": 2,
        "local_support_radius_m": 1000,
        "support_profile": "same-outer-radius-homogeneous-v1",
        "request_template": template,
    }


def test_withheld_raw_is_refused_before_file_access(tmp_path: Path) -> None:
    spec = ExperimentSpec(fixture_inputs(tmp_path))
    fold = grouped_leave_one_out([site.record for site in spec.sites])[0]
    heldout = next(
        site for site in spec.sites if site.record.record_id in fold.test_record_ids
    )
    (tmp_path / heldout.raw.path).unlink()
    with pytest.raises(ValidationRefusal) as error:
        read_training_observation(tmp_path, heldout, fold, spec)
    assert error.value.reason_code == "withheld_input_leakage"


def test_inversion_and_forward_keep_distinct_shore_support(tmp_path: Path) -> None:
    spec = ExperimentSpec(fixture_inputs(tmp_path))
    geometry = read_geometry(tmp_path, spec.sites[0], spec)
    assert geometry["inversion_rings"] != geometry["forward_rings"]
    fold = next(
        fold
        for fold in grouped_leave_one_out([site.record for site in spec.sites])
        if spec.sites[-1].record.record_id in fold.test_record_ids
    )
    request = make_request(spec, spec.sites[0], spec.sites[1], fold, tmp_path)
    assert len(object_list(request["evidence"], "evidence")) == 9
    assert (
        object_mapping(object_list(request["rings"], "rings")[0], "ring")["inner_m"]
        == 21
    )


@pytest.mark.parametrize("mutation", ["extra_count", "support", "shore"])
def test_invalid_geometry_is_refused(tmp_path: Path, mutation: str) -> None:
    payload = fixture_inputs(tmp_path)
    path = payload["sites"][0]["geometry"]["path"]
    geo = json.loads((tmp_path / path).read_text())
    if mutation == "extra_count":
        geo["sample_metadata"]["counts"] = [1, 2]
    elif mutation == "support":
        geo["forward_rings"][1]["outer_m"] = 999
    else:
        geo["inversion_rings"][0]["inner_m"] = 20
    payload["sites"][0]["geometry"] = store(tmp_path, path, geo)
    spec = ExperimentSpec(payload)
    with pytest.raises(ValidationRefusal):
        read_geometry(tmp_path, spec.sites[0], spec)


@pytest.mark.parametrize("content", [b'{"a":1,"a":2}', b'{"a":NaN}'])
def test_bad_json_refused_even_with_matching_hash(
    tmp_path: Path, content: bytes
) -> None:
    (tmp_path / "bad.json").write_bytes(content)
    with pytest.raises(ValidationRefusal):
        read_reference(
            tmp_path, InputReference("bad.json", hashlib.sha256(content).hexdigest())
        )
