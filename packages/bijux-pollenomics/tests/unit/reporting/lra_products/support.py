"""Declared saved-product fixtures; no numerical accuracy or source approval."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra.outputs.contracts import request_metadata
from tests.unit.analysis.lra.support import request_fixture


def encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def product_fixture(
    root: Path, *, operation: str = "lra"
) -> tuple[Path, dict[str, Any]]:
    inputs = root / "inputs"
    inputs.mkdir(parents=True)
    request = request_fixture(inputs, operation)
    product = root / "product"
    product.mkdir()
    result_roots: tuple[tuple[str, str], ...]
    if operation == "lra":
        numerical = {
            "regional_reveals/reconstruction.csv": (
                "Distance.weighting,Basin.type,coordinate,Alnus.mean,Betula.mean,Alnus.median,Betula.median,Alnus.q90,Betula.q90,Alnus.q10,Betula.q10,Alnus.sd,Betula.sd\n"
                "1,lake,1,0,100,0,100,0,100,0,100,,\n"
            ),
            "regional_reveals/deposition_factors.csv": "index,K\nAlnus,1\nBetula,1\n",
            "local_love/cover_mean.csv": "index,Alnus,Betula\n100,0.25,0.75\n",
            "local_love/cover_sd.csv": "index,Alnus,Betula\n100,,0\n",
            "local_love/cover_q10.csv": "index,Alnus,Betula\n100,0.2,0.7\n",
            "local_love/cover_q90.csv": "index,Alnus,Betula\n100,0.3,0.8\n",
            "local_love/aux_valid_ring.csv": "index,valid\n100,True\n",
        }
        result_roots = (("regional_reveals", "reveals"), ("local_love", "love"))
    else:
        numerical = {
            "reconstruction.csv": (
                "Distance.weighting,Basin.type,coordinate,Alnus.mean,Betula.mean,Alnus.median,Betula.median,Alnus.q90,Betula.q90,Alnus.q10,Betula.q10,Alnus.sd,Betula.sd\n"
                "1,lake,1,0,100,0,100,0,100,0,100,,\n"
            ),
            "deposition_factors.csv": "index,K\nAlnus,1\nBetula,1\n",
        }
        result_roots = (("", "reveals"),)
    for member, text in numerical.items():
        path = product / "numerical" / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    for relative, kind in result_roots:
        units = {
            "cover": "percent" if kind == "reveals" else "fraction",
            "distance": "metre",
        }
        if kind == "love":
            units["pollen_percentages"] = "percent"
        (product / "numerical" / relative / "result_contract.json").write_bytes(
            encoded(
                {
                    "schema_version": "1.0.0",
                    "result_type": kind,
                    "primary_artifact": "reconstruction.csv"
                    if kind == "reveals"
                    else "cover_mean.csv",
                    "units": units,
                    **({"method": "analytical"} if kind == "love" else {}),
                }
            )
        )
    rebind(product, request)
    return product, request


def rebind(product: Path, request: dict[str, Any]) -> dict[str, Any]:
    request_sha = sha(encoded(request).rstrip(b"\n"))
    (product / "request.json").write_bytes(encoded(request))
    scientific = {"fixture": "synthetic saved-table boundary only"}
    (product / "scientific_manifest.json").write_bytes(encoded(scientific))
    engine = {"package": "synthetic-test-engine"}
    numerical = {
        p.relative_to(product / "numerical").as_posix(): sha(p.read_bytes())
        for p in (product / "numerical").rglob("*")
        if p.is_file()
    }
    identity = {
        "request_sha256": request_sha,
        "engine": engine,
        "engine_scientific_manifest": scientific,
        "numerical_files": numerical,
    }
    manifest = {
        "schema_version": "lra-product.v1",
        "status": "generated_exploratory",
        "scientific_acceptance": "not_evaluated",
        **request_metadata(request),
        "request_sha256": request_sha,
        "scientific_content_sha256": sha(encoded(identity)),
        "scientific_identity": identity,
        "engine": engine,
        "files": {
            p.relative_to(product).as_posix(): sha(p.read_bytes())
            for p in product.rglob("*")
            if p.is_file() and p != product / "manifest.json"
        },
    }
    (product / "manifest.json").write_bytes(encoded(manifest))
    return manifest


def geometry_fixture(product: Path, request: dict[str, Any]) -> dict[str, Any]:
    manifest = json.loads((product / "manifest.json").read_bytes())
    return {
        "schema_version": "lra-display-geometry.v1",
        "data_kind": request["data_kind"],
        "product_manifest_sha256": sha((product / "manifest.json").read_bytes()),
        "request_sha256": manifest["request_sha256"],
        "scientific_content_sha256": manifest["scientific_content_sha256"],
        "crs": "OGC:CRS84",
        "coordinate_order": "longitude_latitude",
        "sites": [
            {
                "role": role,
                "site_id": request[role]["samples"][0]["site_id"],
                "disposition": "declared_anchor",
                "position": [0, 0] if role == "regional" else [18, 59],
                "basis": "synthetic_fixture",
                "source_locator": "Declared UI fixture; not numerical geometry",
            }
            for role in ("regional", "local")
            if role in request
        ],
    }
