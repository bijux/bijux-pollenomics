"""Frontier publication preserves foreign entries and owned candidates on refusal."""

from pathlib import Path
from typing import Any

import pytest

from ..native_products import bindings
from .native_payloads import native_response
from .test_capture import capture_api


@pytest.mark.parametrize("occupied", ["final", "symlink", "staging"])
def test_occupied_or_aliased_output_preserves_foreign_bytes_without_get(
    chain_products: dict[str, Any], tmp_path: Path, occupied: str
) -> None:
    destination = tmp_path / "frontier"
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    marker = foreign / "unrelated.txt"
    marker.write_bytes(b"foreign bytes")
    if occupied == "symlink":
        destination.symlink_to(foreign, target_is_directory=True)
    else:
        target = destination if occupied == "final" else tmp_path / ".frontier.staging"
        target.mkdir()
        (target / "unrelated.txt").write_bytes(b"existing output")
    calls: list[str] = []
    with pytest.raises((ValueError, FileExistsError)):
        capture_api()(
            destination,
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=lambda url, **_: calls.append(url),
        )
    assert not calls and marker.read_bytes() == b"foreign bytes"
    if occupied != "symlink":
        assert (target / "unrelated.txt").read_bytes() == b"existing output"


def test_foreign_staging_replacement_during_get_retains_owned_candidate(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    destination = tmp_path / "frontier"
    staging = tmp_path / ".frontier.staging"
    retained = tmp_path / "retained-candidate"
    calls: list[str] = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        staging.rename(retained)
        staging.mkdir()
        (staging / "foreign.txt").write_bytes(b"foreign bytes")
        return native_response(chain_products, url, **kwargs)

    with pytest.raises(ValueError):
        capture_api()(
            destination,
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=fetch,
        )
    assert len(calls) == 1 and not destination.exists()
    assert (staging / "foreign.txt").read_bytes() == b"foreign bytes"
    assert sorted(path.name for path in staging.iterdir()) == ["foreign.txt"]
    assert (retained / "request-plan.json").is_file()


@pytest.mark.parametrize("location", ["staging", "final"])
def test_foreign_substitution_after_actual_consumer_readback_refuses(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, location: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        derive_neotoma_taxon_ancestry_chain,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.acquisition import (
        workflow,
    )

    original = derive_neotoma_taxon_ancestry_chain
    destination = tmp_path / "frontier"
    retained = tmp_path / "retained-candidate"
    reads: list[Path] = []

    def readback(**kwargs: Any) -> Any:
        result = original(**kwargs)
        pin = kwargs["new_capture_manifest_sha256s"][0]
        candidate = kwargs["sources"].ancestry_capture_sources[pin]
        reads.append(candidate)
        matches = candidate == (
            tmp_path / ".frontier.staging" if location == "staging" else destination
        )
        if matches:
            candidate.rename(retained)
            candidate.mkdir()
            (candidate / "foreign.txt").write_bytes(b"foreign bytes")
        return result

    monkeypatch.setattr(workflow, "derive_neotoma_taxon_ancestry_chain", readback)
    with pytest.raises(ValueError):
        capture_api()(
            destination,
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=lambda url, **kwargs: native_response(chain_products, url, **kwargs),
        )
    foreign = tmp_path / ".frontier.staging" if location == "staging" else destination
    assert (foreign / "foreign.txt").read_bytes() == b"foreign bytes"
    assert sorted(path.name for path in foreign.iterdir()) == ["foreign.txt"]
    assert (retained / "capture-manifest.json").is_file()
    assert len(reads) == (1 if location == "staging" else 2)


@pytest.mark.parametrize("first", ["session", "acquisition", "chain"])
def test_cold_import_order_opens_no_retained_data(first: str) -> None:
    import subprocess
    import sys

    from tests.support.repository import REPOSITORY_ROOT

    script = """
import importlib, os, sys
from pathlib import Path
data = Path(sys.argv[1]).absolute()
def audit(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)):
        path = Path(os.fsdecode(args[0])).absolute().resolve()
        if path == data or data in path.parents:
            raise AssertionError('Cold import cannot open retained data')
    if event in ('socket.connect', 'socket.getaddrinfo'):
        raise AssertionError('Cold import cannot access network')
sys.addaudithook(audit)
base = 'bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.'
paths = {'session':base + 'evidence_parts.session',
         'acquisition':base + 'ancestry.chain.acquisition',
         'chain':base + 'ancestry.chain'}
importlib.import_module(paths[sys.argv[2]])
module = importlib.import_module(paths['acquisition'])
assert callable(module.capture_neotoma_taxon_ancestry_frontier)
print(module.__file__)
"""
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            script,
            str(REPOSITORY_ROOT / "data"),
            first,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert str(REPOSITORY_ROOT / "packages/bijux-pollenomics/src") in result.stdout
