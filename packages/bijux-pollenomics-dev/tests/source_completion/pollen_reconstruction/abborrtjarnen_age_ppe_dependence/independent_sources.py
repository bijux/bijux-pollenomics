"""Authenticate the three qualified inputs without reopening counts or ages."""

from __future__ import annotations

from collections import Counter
import csv
from dataclasses import dataclass
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .independent_quadratic_forms import AXIS, BINS, TAXON_IDS, Array

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/common-covariance/protocol.json"
)


def component_axis() -> list[dict[str, Any]]:
    """List the fixed window and taxon identities for each cover component."""
    return [
        {"window_id": b, "taxon": name, "native_taxon_id": taxon}
        for b in BINS
        for name, taxon in zip(AXIS, TAXON_IDS, strict=True)
    ]


@dataclass(frozen=True)
class Inputs:
    """Authenticated protocol, reference, ledger, and original input buffers."""

    protocol: dict[str, Any]
    reference: dict[str, Any]
    ledger: bytes
    bodies: dict[Path, bytes]
    hashes: dict[str, str]

    def unchanged(self) -> None:
        """Refuse if any authenticated input bytes changed during verification."""
        if any(path.read_bytes() != body for path, body in self.bodies.items()):
            raise ValueError("Qualified observer input changed during verification")


def read_inputs(repository: Path) -> Inputs:
    """Authenticate the declared result, ledger, and independent-check inputs."""
    protocol_path = repository / PROTOCOL
    protocol_body = protocol_path.read_bytes()
    protocol = json.loads(protocol_body)
    pins = protocol["repository_inputs"]
    if len(pins) != 3 or set(pins) != {
        protocol[k] for k in ("source_result", "source_ledger", "source_verification")
    }:
        raise ValueError("Exactly three qualified scientific inputs required")
    bodies = {protocol_path: protocol_body}
    hashes = {}
    objects = []
    ledger = None
    for relative, pin in pins.items():
        path = (repository / relative).resolve(strict=True)
        if not path.is_relative_to(repository.resolve()):
            raise ValueError("Scientific input escapes repository")
        body = path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if len(body) != pin["bytes"] or digest != pin["sha256"]:
            raise ValueError("Qualified scientific input identity differs")
        bodies[path] = body
        hashes["repository/" + relative] = digest
        if path.suffix == ".gz":
            if ledger is not None:
                raise ValueError("Qualified ledger is ambiguous")
            ledger = body
        else:
            objects.append(json.loads(body))
    references = [value for value in objects if "component_axis" in value]
    checks = [value for value in objects if "result_sha256" in value]
    if len(references) != 1 or len(checks) != 1 or ledger is None:
        raise ValueError("Qualified result/ledger/check roles differ")
    reference, check = references[0], checks[0]
    reference_body = next(
        body
        for path, body in bodies.items()
        if path != protocol_path
        and path.suffix != ".gz"
        and json.loads(body) == reference
    )
    if (
        check["status"] != "passed"
        or check["result_sha256"] != hashlib.sha256(reference_body).hexdigest()
        or check["saved_joint_age_rows_checked"] != 32000
        or check["complete_rows"] != 31999
    ):
        raise ValueError("Independent source-supported result admission differs")
    if (
        reference["source_commit"] != check["producer_source_commit"]
        or check["producer_source_commit"] != protocol["producer_source_commit"]
        or check["observer_source_commit"] != protocol["observer_source_commit"]
        or check["count_profile"] != "pangaea_recorded_zeros_local_nc"
    ):
        raise ValueError("Qualified source/observer revisions differ")
    for name, expected in {
        "native_samples_checked": 107,
        "undefined_rows": 1,
        "original_count_slots_checked": 535,
        "native_reported_count_pairs_checked": 527,
        "source_zero_slots_checked": 8,
        "covariance_entries_checked": 2400,
        "contrasts_checked": 30,
        "model_fits": 0,
    }.items():
        if check.get(name) != expected:
            raise ValueError("Source-supported independent qualification is incomplete")
    for name in (
        "maximum_ledger_cover_gap",
        "maximum_moment_gap",
        "common_native_maximum_moment_gap",
        "maximum_profile_difference_gap",
    ):
        value = check[name]
        if (
            type(value) not in (int, float)
            or not np.isfinite(value)
            or not 0 <= value <= 1e-12
        ):
            raise ValueError("Source-supported numerical qualification differs")
    if (
        reference["component_axis"] != component_axis()
        or reference["count_profile"] != "pangaea_recorded_zeros_local_nc"
        or (
            reference["requested_draws"],
            reference["complete_draws"],
            reference["undefined_draws"],
        )
        != (32000, 31999, 1)
    ):
        raise ValueError("Qualified source-supported axes/population differ")
    if (
        [entry["seed"] for entry in reference["chain_summaries"]] != [314159, 271828]
        or reference["unconditional"]["status"] != "refused_undefined_mass"
        or reference["conditional_on_complete"]["status"] != "conditional_on_complete"
    ):
        raise ValueError("Qualified seed or estimand scope differs")
    if reference["draw_ledger"]["sha256"] != hashlib.sha256(
        ledger
    ).hexdigest() or reference["draw_ledger"]["bytes"] != len(ledger):
        raise ValueError("Source-supported result names another ledger")
    return Inputs(protocol, reference, ledger, bodies, hashes)


def parameters(reference: dict[str, Any]) -> tuple[Array, Array]:
    """Read parameter arrays with the declared taxon axes and numeric domain."""
    rows = reference["parameters"]
    if [(row["name"], row["native_taxon_id"]) for row in rows] != list(
        zip(AXIS, TAXON_IDS, strict=True)
    ):
        raise ValueError("Qualified parameter axes differ")
    ppe = np.array([row["ppe"] for row in rows], dtype=float)
    sd = np.array([row["published_sd"] for row in rows], dtype=float)
    if (
        not np.isfinite(ppe).all()
        or not np.isfinite(sd).all()
        or (ppe <= 0).any()
        or (sd[:4] <= 0).any()
        or sd[4] != 0
    ):
        raise ValueError("Qualified positive-PPE/four-SD domain differs")
    return ppe, sd


@dataclass(frozen=True)
class Population:
    """Complete cover rows and their per-chain population counts."""

    covers: Array
    rows: int
    chains: dict[int, int]


def read_ledger(
    body: bytes,
    reference: dict[str, Any],
    *,
    chain_rows: int = 16000,
    first_native_row: int = 3502,
) -> Population:
    """Use every saved identity, then condition only on the existing C mask."""
    chains = reference["chain_summaries"]
    seeds = [entry["seed"] for entry in chains]
    if (
        len(seeds) != 2
        or len(set(seeds)) != 2
        or reference["component_axis"] != component_axis()
    ):
        raise ValueError("Qualified chain/component axes differ")
    sample_ids = [row["sample_id"] for row in reference["sample_accounts"]]
    if len(sample_ids) != 107 or len(set(sample_ids)) != 107:
        raise ValueError("Qualified sample identity population differs")
    expected_ids = [
        (seed, n)
        for seed in seeds
        for n in range(first_native_row, first_native_row + chain_rows)
    ]
    covers = []
    complete_by_seed: Counter[int] = Counter()
    supports: dict[int, Counter[str]] = {b: Counter() for b in BINS}
    rows = csv.DictReader(io.StringIO(gzip.decompress(body).decode()))
    if rows.fieldnames is None or len(rows.fieldnames) != len(set(rows.fieldnames)):
        raise ValueError("Saved ledger column identities differ")
    count = 0
    for count, row in enumerate(rows, 1):
        if (
            count > len(expected_ids)
            or (int(row["seed"]), int(row["native_row"])) != expected_ids[count - 1]
        ):
            raise ValueError("Saved ledger seed/native-row identities differ")
        if row["complete"] not in ("0", "1"):
            raise ValueError("Saved complete-case mask is not binary")
        complete = row["complete"] == "1"
        values = []
        defined = []
        members_seen: set[int] = set()
        for b in BINS:
            status = row[f"bin_{b}_status"]
            if status not in (
                "defined",
                "empty_native_window",
                "missing_explicit_five_taxon_member",
                "nonempty_zero_panel_mass",
            ):
                raise ValueError("Saved support status differs")
            members = json.loads(row[f"bin_{b}_sample_ids"])
            if (
                len(members) != int(row[f"bin_{b}_sample_count"])
                or len(set(members)) != len(members)
                or not set(members).issubset(sample_ids)
                or members_seen.intersection(members)
            ):
                raise ValueError("Saved per-window sample identities differ")
            members_seen.update(members)
            if (status == "empty_native_window") != (not members):
                raise ValueError("Saved empty-window support differs")
            supports[b][status] += 1
            defined.append(status == "defined")
            raw = [row[f"cover_{b}_{taxon}"] for taxon in TAXON_IDS]
            if status == "defined":
                if any(value == "" for value in raw):
                    raise ValueError("Defined window has missing cover")
                parsed = [float(value) for value in raw]
                if (
                    any(
                        not math.isfinite(value) or not 0 <= value <= 1
                        for value in parsed
                    )
                    or abs(math.fsum(parsed) - 1) > 1e-12
                ):
                    raise ValueError("Saved partial or complete cover simplex differs")
                values.extend(parsed)
            elif any(value != "" for value in raw):
                raise ValueError("Undefined window invents cover")
        if complete != all(defined):
            raise ValueError("Saved complete-case mask differs from all-window support")
        if complete:
            covers.append(values)
            complete_by_seed[int(row["seed"])] += 1
    if (
        count != len(expected_ids)
        or count != reference["requested_draws"]
        or len(covers) != reference["complete_draws"]
        or count - len(covers) != reference["undefined_draws"]
    ):
        raise ValueError("Saved complete/population denominator differs")
    if any(
        complete_by_seed[entry["seed"]] != entry["complete_draws"]
        or entry["requested_draws"] != chain_rows
        for entry in chains
    ):
        raise ValueError("Saved chain conditional population differs")
    if any(
        reference["support_by_window"][str(b)]["status_counts"] != dict(supports[b])
        or reference["support_by_window"][str(b)]["probability_denominator"] != count
        for b in BINS
    ):
        raise ValueError("Saved per-window support denominator differs")
    return Population(np.asarray(covers, dtype=float), count, dict(complete_by_seed))
