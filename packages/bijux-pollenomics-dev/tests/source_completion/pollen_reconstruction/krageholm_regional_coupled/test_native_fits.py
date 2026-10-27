"""Saved-coefficient controls retain signed local outputs without engine calls."""

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from .lineage import digest
from .native_fits import native_fit

TOLERANCE = {"scalar_absolute_tolerance": 2e-12, "scalar_relative_tolerance": 2e-10}


def synthetic_fit(
    directory: Path, *, altered: str | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    directory.mkdir(parents=True)
    request = {
        "parameters": [{"ppe": 1}, {"ppe": 1}],
        "regional": {"samples": [{"counts": [1, 1]}]},
        "local": {"samples": [{"counts": [3, 1]}]},
        "rings": [{"mean_m": 300}, {"mean_m": 750}],
    }
    files = {
        "request.json": json.dumps(request),
        "numerical/regional_reveals/deposition_factors.csv": "index,K\nBetula,1\nUlmus,1\n",
        "numerical/regional_reveals/reconstruction.csv": "Betula.mean,Ulmus.mean,Betula.median,Ulmus.median,Betula.q90,Ulmus.q90,Betula.q10,Ulmus.q10,Betula.sd,Ulmus.sd\n50,50,50,50,50,50,50,50,0,0\n",
        "numerical/local_love/aux_Kloc.csv": "index,Betula,Ulmus\n300,1,1\n750,1,1\n",
        "numerical/local_love/aux_Kreg.csv": "index,Betula,Ulmus\n300,1,1\n750,2,2\n",
        "numerical/local_love/cover_mean.csv": "index,Betula,Ulmus\n300,1,0\n750,1.25,-0.25\n",
        "numerical/local_love/run_manifest.json": json.dumps(
            {"parameters": {"paired_regional_cover_draws": True}}
        ),
    }
    if altered == "clip":
        files["numerical/local_love/cover_mean.csv"] = (
            "index,Betula,Ulmus\n300,1,0\n750,1,0\n"
        )
    elif altered == "coefficient":
        files["numerical/local_love/aux_Kreg.csv"] = (
            "index,Betula,Ulmus\n300,1,1\n750,1,1\n"
        )
    elif altered == "regional":
        files["numerical/regional_reveals/reconstruction.csv"] = files[
            "numerical/regional_reveals/reconstruction.csv"
        ].replace("50,50,50,50", "60,40,60,40")
    elif altered == "pairing":
        files["numerical/local_love/run_manifest.json"] = json.dumps(
            {"parameters": {"paired_regional_cover_draws": False}}
        )
    elif altered == "ring":
        files["numerical/local_love/cover_mean.csv"] = (
            "index,Betula,Ulmus\n300,1,0\n760,1.25,-0.25\n"
        )
    identity = {"fixture": "saved coefficient control"}
    science = sha256(
        (json.dumps(identity, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()
    inventory = {}
    for name, content in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        body = content.encode()
        path.write_bytes(body)
        inventory[name] = sha256(body).hexdigest()
    manifest = {
        "schema_version": "lra-product.v1",
        "scientific_acceptance": "not_evaluated",
        "scientific_identity": identity,
        "scientific_content_sha256": science,
        "request_sha256": digest(request),
        "files": inventory,
    }
    body = json.dumps(manifest).encode()
    (directory / "manifest.json").write_bytes(body)
    return {
        "manifest_sha256": sha256(body).hexdigest(),
        "scientific_content_sha256": science,
    }, request


def test_both_signed_native_rings_and_regional_rounding_are_independently_rebuilt(
    tmp_path: Path,
) -> None:
    pin, request = synthetic_fit(tmp_path / "native")
    result = native_fit(tmp_path / "native", pin, request, TOLERANCE)
    assert tuple(map(float, result["cover"])) == (1.25, -0.25)
    assert [tuple(map(float, values)) for values in result["all_signed_covers"]] == [
        (1, 0),
        (1.25, -0.25),
    ]
    assert tuple(map(float, result["regional"])) == (0.5, 0.5)


@pytest.mark.parametrize(
    "altered", ["clip", "coefficient", "regional", "pairing", "ring"]
)
def test_native_scalar_clipping_coefficient_rounding_or_pairing_tamper_refuses(
    tmp_path: Path, altered: str
) -> None:
    pin, request = synthetic_fit(tmp_path / "native", altered=altered)
    with pytest.raises(ValueError):
        native_fit(tmp_path / "native", pin, request, TOLERANCE)
