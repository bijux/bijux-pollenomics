"""Bind a supplied joint law to unchanged source catalogue and typed supports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..engine.errors import LRARefusal
from ..inputs.validation import validate_request
from .contracts import (
    JointLRAPlan,
    canonical,
    digest,
    number,
    parse_json,
    positive_integer,
    reference,
    refuse,
)


def read_bound(root: Path, ref: dict[str, Any]) -> bytes:
    reference({"path": ref["path"], "sha256": ref["sha256"]})
    path: Path = root / str(ref["path"])
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise LRARefusal("joint_source_unavailable", str(path))
    if not path.resolve().is_relative_to(root.resolve()):
        refuse("Source escapes the input root")
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise LRARefusal("joint_source_unavailable", str(path)) from exc
    if digest(data) != ref["sha256"]:
        raise LRARefusal("joint_source_changed", ref["path"])
    return data


@dataclass(frozen=True)
class AdmittedJointPlan:
    plan: JointLRAPlan
    base_json: str
    files: tuple[tuple[str, bytes], ...]

    def base(self) -> dict[str, Any]:
        return parse_json(self.base_json.encode("utf-8"))


def admit(plan: JointLRAPlan, input_root: Path) -> AdmittedJointPlan:
    payload = plan.payload()
    files: dict[str, bytes] = {}
    for key in ("base_request_ref", "law_evidence_ref"):
        ref = payload[key]
        data = read_bound(input_root, ref)
        if ref["path"] in files and files[ref["path"]] != data:
            refuse("Contradictory source reference")
        files[ref["path"]] = data
    base = parse_json(files[payload["base_request_ref"]["path"]])
    validate_request(base, input_root=input_root)
    if base["data_kind"] != "synthetic" or base["operation"] not in ("lra", "series"):
        refuse("Joint catalogue requires an admitted synthetic paired/series request")
    if base["configuration"].get("love", {}).get("method") != "analytical":
        refuse("Only analytical paired realizations are supported")
    config = base["configuration"]
    love = config.get("love")
    if not isinstance(love, dict) or "max_ring" not in love:
        refuse("Base LOVE configuration must explicitly declare max_ring")
    max_ring = positive_integer(love["max_ring"], len(base["rings"]))
    for ref in base["evidence"]:
        data = read_bound(input_root, ref)
        if ref["path"] in files and files[ref["path"]] != data:
            refuse("Contradictory retained evidence paths")
        files[ref["path"]] = data
    samples = {
        row["sample_id"]: row
        for role in ("regional", "local")
        for row in base[role]["samples"]
    }
    taxa = base["taxa"]
    if len(taxa) > 128 or len(samples) > 1024:
        refuse("Sample/taxon resource bounds exceeded")
    for sample in samples.values():
        if sample["age_type"] != "calendar_bp":
            refuse("Only known calendar_bp source support is supported")
        for interval in sample["age_support_bp"]:
            for endpoint in interval:
                number(endpoint)
    for draw in payload["realizations"]:
        if (
            set(draw["ppe_by_taxon"]) != set(taxa)
            or set(draw["ages_by_sample_id"]) != set(samples)
            or set(draw["counts_by_sample_id"]) != set(samples)
        ):
            refuse("Realization sample/taxon inventory differs from the full catalogue")
        for sample_id, sample in samples.items():
            counts = draw["counts_by_sample_id"][sample_id]
            if len(counts) != len(taxa) or sum(counts) != sum(sample["counts"]):
                refuse("Realized count denominator differs from its source sample")
            age = draw["ages_by_sample_id"][sample_id]
            if not any(
                younger <= age <= older for younger, older in sample["age_support_bp"]
            ):
                refuse("Realized age is outside its original closed support union")
    cells = len(payload["realizations"]) * (len(samples) * (len(taxa) + 1) + len(taxa))
    dimensions = len(taxa) * (1 + max_ring)
    if (
        cells > payload["limits"]["max_draw_cells"]
        or dimensions**2 * len(payload["bins"])
        > payload["limits"]["max_covariance_cells"]
    ):
        refuse("Joint storage/summary resource bounds exceeded")
    return AdmittedJointPlan(
        plan, canonical(base).decode("utf-8"), tuple(sorted(files.items()))
    )


def revalidate(admitted: AdmittedJointPlan, input_root: Path) -> None:
    if admit(admitted.plan, input_root) != admitted:
        raise LRARefusal("joint_source_changed", "Admitted source bytes changed")
