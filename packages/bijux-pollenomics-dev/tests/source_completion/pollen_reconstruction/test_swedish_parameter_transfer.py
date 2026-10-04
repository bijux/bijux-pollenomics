"""Guard assumption/source authority and retention of local presence evidence."""

from contextlib import contextmanager
import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_parameter_transfer import (
    producer,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_parameter_transfer.sources import (
    DECLARATION,
    PROTOCOL,
    load_scope,
)


ROOT = Path(__file__).resolve().parents[5]


@pytest.fixture(scope="module")
def repository(tmp_path_factory):
    source = Path(os.environ.get("POLLENOMICS_TRANSFER_SOURCE_ROOT", ROOT)).resolve()
    target = tmp_path_factory.mktemp("swedish-transfer-source")
    descriptor = json.loads((source / DECLARATION).read_bytes())
    for relative in [str(DECLARATION), *descriptor["source_files"]]:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, destination)
    shutil.copy2(source / "pyproject.toml", target / "pyproject.toml")
    (target / "artifacts").mkdir()
    return target


@contextmanager
def changed_protocol(repository, mutation, *, rebind):
    protocol_path, descriptor_path = repository / PROTOCOL, repository / DECLARATION
    protocol_before, descriptor_before = (
        protocol_path.read_bytes(),
        descriptor_path.read_bytes(),
    )
    try:
        protocol = json.loads(protocol_before)
        mutation(protocol)
        protocol_path.write_text(json.dumps(protocol, ensure_ascii=False) + "\n")
        if rebind:
            descriptor = json.loads(descriptor_before)
            descriptor["source_files"][str(PROTOCOL)] = {
                "sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
                "bytes": protocol_path.stat().st_size,
            }
            descriptor_path.write_text(json.dumps(descriptor) + "\n")
        yield
    finally:
        protocol_path.write_bytes(protocol_before)
        descriptor_path.write_bytes(descriptor_before)


def test_actual_raw_population_authority(repository):
    scenario, _, datasets, _, _ = load_scope(
        repository,
        json.loads((repository / DECLARATION).read_bytes())[
            "producer_source_candidate"
        ],
    )
    assert set(datasets) == {19913, 54001, 53995, 53980}
    for did, dataset in datasets.items():
        expected = scenario["native_source_population"][str(did)]
        assert len(dataset["samples"]) == expected["native_samples"]
        assert (
            sum(s["reported_all_pollen_NISP_sum"] for s in dataset["samples"])
            == expected["all_native_pollen_NISP_sum"]
        )


@pytest.mark.parametrize(
    "name", ["sparse_zero_hypothesis", "mutually_exclusive_partition_hypothesis"]
)
def test_bound_protocol_without_required_hypothesis_refuses(repository, name):
    with changed_protocol(repository, lambda p: p.update({name: False}), rebind=True):
        with pytest.raises(ValueError, match="explicitly declared"):
            load_scope(
                repository,
                json.loads((repository / DECLARATION).read_bytes())[
                    "producer_source_candidate"
                ],
            )


def test_protocol_bytes_changed_without_authority_refuses(repository):
    with changed_protocol(
        repository,
        lambda p: p.update(source_scope="changed source scope"),
        rebind=False,
    ):
        with pytest.raises(ValueError, match="identity mismatch"):
            load_scope(
                repository,
                json.loads((repository / DECLARATION).read_bytes())[
                    "producer_source_candidate"
                ],
            )


def test_declared_candidate_mismatch_refuses(repository):
    with pytest.raises(ValueError, match="candidate differs"):
        load_scope(repository, "0" * 40)


def test_bound_historical_claim_refuses(repository):
    with changed_protocol(
        repository, lambda p: p.update(historical_replay_claim=True), rebind=True
    ):
        with pytest.raises(ValueError, match="conditional historical"):
            load_scope(
                repository,
                json.loads((repository / DECLARATION).read_bytes())[
                    "producer_source_candidate"
                ],
            )


def test_upstream_native_loader_changed_refuses(repository):
    relative = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_reconstruction/swedish_static_basin/sources.py"
    path = repository / relative
    before = path.read_bytes()
    try:
        path.write_bytes(before + b"\n")
        with pytest.raises(ValueError, match="identity mismatch"):
            load_scope(
                repository,
                json.loads((repository / DECLARATION).read_bytes())[
                    "producer_source_candidate"
                ],
            )
    finally:
        path.write_bytes(before)


def test_failed_computation_keeps_output_absent(repository, monkeypatch):
    output = repository / "artifacts/test-failed-transfer-report"

    def fail(*args):
        raise ValueError("refused actual source mask")

    monkeypatch.setattr(producer, "reconstruct", fail)
    with pytest.raises(ValueError, match="source mask"):
        producer.publish(
            repository,
            repository,
            output,
            json.loads((repository / DECLARATION).read_bytes())[
                "producer_source_candidate"
            ],
        )
    assert not output.exists()
    assert list(output.parent.glob(".swedish-parameter-transfer-evidence-*"))


def test_report_serialization_is_independent_of_nested_mapping_order():
    first = {"source_to_parameter_map": {"Pinus": "Pinus sylvestris", "Betula": "Betula"}, "cover": [0.2, 0.8]}
    second = {"cover": [0.2, 0.8], "source_to_parameter_map": {"Betula": "Betula", "Pinus": "Pinus sylvestris"}}
    assert producer.serialize_report(first) == producer.serialize_report(second)
    assert json.loads(producer.serialize_report(first)) == first


def test_report_serialization_refuses_nonfinite_scientific_values():
    with pytest.raises(ValueError, match="Out of range float"):
        producer.serialize_report({"cover": [float("nan")]})
