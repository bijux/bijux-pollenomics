"""Bind the transfer hypotheses to the maintained native observation source."""

from __future__ import annotations
import json
from pathlib import Path
import re
from typing import Any
from ..swedish_static_basin.sources import load_inputs, read_bound

FAMILY = Path("docs/report/pollen-reconstruction/swedish-parameter-transfer-scenarios")
PROTOCOL = FAMILY / "assumptions/parameter-transfer.json"
DECLARATION = FAMILY / "inputs/source-identities.json"


def load_scope(repository: Path, candidate: str) -> tuple[dict[str, Any], ...]:
    if re.fullmatch(r"[0-9a-f]{40}", candidate) is None:
        raise ValueError("candidate must be an exact lowercase Git SHA")
    for relative in (DECLARATION, PROTOCOL):
        path = repository / relative
        if path.resolve() != path or not path.is_file():
            raise ValueError("transfer declaration must be a contained regular file")
    descriptor = json.loads((repository / DECLARATION).read_bytes())
    if descriptor["producer_source_candidate"] != candidate:
        raise ValueError("candidate differs from transfer source authority")
    identities = descriptor["source_files"]
    bound = {
        name: read_bound(repository, name, identity)
        for name, identity in identities.items()
    }
    scenario = json.loads(bound[str(PROTOCOL)])
    if (
        scenario.get("historical_replay_claim") is not False
        or scenario.get("accepted_taxonomy_mapping_claim") is not False
        or scenario.get("complete31source_measurement_claim") is not False
        or scenario.get("vegetation_accuracy_claim") is not False
    ):
        raise ValueError(
            "transfer protocol must retain conditional historical/taxonomy scope"
        )
    if (
        scenario.get("sparse_zero_hypothesis") is not True
        or scenario.get("mutually_exclusive_partition_hypothesis") is not True
    ):
        raise ValueError(
            "broader inputs require explicitly declared sparse-zero and partition hypotheses"
        )
    ids = [profile["id"] for profile in scenario["profiles"]]
    if len(ids) != 4 or len(set(ids)) != 4:
        raise ValueError("four distinct declared transfer profiles are required")
    physical, datasets, metadata, upstream = load_inputs(repository)
    for name, identity in upstream.items():
        if identities.get(name) != identity:
            raise ValueError("upstream observation source authority differs")
    return scenario, physical, datasets, metadata, identities
