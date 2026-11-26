from __future__ import annotations

import os
from pathlib import Path

import pytest

from bijux_pollenomics.adna import AdnaSampleQuery, load_species_samples
from bijux_pollenomics.adna.species.homo_sapiens import (
    build_homo_sapiens_runtime_manifest_for_version_dir,
)
from tests.support.aadr import write_anno_file


@pytest.mark.parametrize("country_only", [True, False])
def test_same_size_and_mtime_change_invalidates_release_cache(
    tmp_path: Path, country_only: bool
) -> None:
    path = tmp_path / "v66" / "ho" / "fixture.anno"
    write_anno_file(
        path, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(path.parent.parent)
    query = AdnaSampleQuery(political_entity="Sweden") if country_only else None
    before, _ = load_species_samples(manifest, query=query)
    stamp = path.stat()
    changed = path.read_bytes().replace(b"Kanaljorden", b"Xanaljorden")
    path.write_bytes(changed)
    os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    assert path.stat().st_size == stamp.st_size
    assert path.stat().st_mtime_ns == stamp.st_mtime_ns
    after, _ = load_species_samples(manifest, query=query)
    assert before[0].locality == "Kanaljorden"
    assert after[0].locality == "Xanaljorden"


def _manifest(tmp_path: Path, name: str = "v66"):
    path = tmp_path / name / "ho" / "fixture.anno"
    write_anno_file(
        path, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    return path, build_homo_sapiens_runtime_manifest_for_version_dir(path.parent.parent)


def test_parser_uses_captured_bytes_after_source_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.adna import homo_sapiens as runtime

    path, manifest = _manifest(tmp_path)
    parser = runtime.iter_homo_sapiens_samples_from_bytes

    def replace_then_parse(raw, **kwargs):
        path.write_bytes(path.read_bytes().replace(b"Kanaljorden", b"Xanaljorden"))
        return parser(raw, **kwargs)

    monkeypatch.setattr(
        runtime, "iter_homo_sapiens_samples_from_bytes", replace_then_parse
    )
    first, _ = load_species_samples(manifest)
    assert first[0].locality == "Kanaljorden"
    second, _ = load_species_samples(manifest)
    assert second[0].locality == "Xanaljorden"


def test_parser_failure_resets_context_and_does_not_poison_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.adna import homo_sapiens as runtime

    _, manifest = _manifest(tmp_path)
    parser = runtime.iter_homo_sapiens_samples_from_bytes

    def fail(*args, **kwargs):
        raise ValueError("parse failure")

    monkeypatch.setattr(runtime, "iter_homo_sapiens_samples_from_bytes", fail)
    with pytest.raises(ValueError, match="parse failure"):
        load_species_samples(manifest)
    assert runtime._CAPTURED_RELEASE.get() is None
    monkeypatch.setattr(runtime, "iter_homo_sapiens_samples_from_bytes", parser)
    assert load_species_samples(manifest)[0][0].locality == "Kanaljorden"


def test_nested_load_restores_outer_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.adna import homo_sapiens as runtime

    _, outer = _manifest(tmp_path, "outer")
    inner_path, inner = _manifest(tmp_path, "inner")
    inner_path.write_bytes(
        inner_path.read_bytes().replace(b"Kanaljorden", b"Xanaljorden")
    )
    parser = runtime.iter_homo_sapiens_samples_from_bytes
    entered = False

    def nested(raw, **kwargs):
        nonlocal entered
        if not entered:
            entered = True
            assert load_species_samples(inner)[0][0].locality == "Xanaljorden"
        return parser(raw, **kwargs)

    monkeypatch.setattr(runtime, "iter_homo_sapiens_samples_from_bytes", nested)
    assert load_species_samples(outer)[0][0].locality == "Kanaljorden"
    assert runtime._CAPTURED_RELEASE.get() is None


def test_concurrent_cache_misses_use_their_own_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from bijux_pollenomics.adna import homo_sapiens as runtime

    _, manifest = _manifest(tmp_path)
    parser = runtime.iter_homo_sapiens_samples_from_bytes
    barrier = Barrier(2, timeout=5)

    def synchronized(raw, **kwargs):
        barrier.wait()
        return parser(raw, **kwargs)

    monkeypatch.setattr(runtime, "iter_homo_sapiens_samples_from_bytes", synchronized)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(lambda _: load_species_samples(manifest)[0][0].locality, range(2))
        )
    assert results == ["Kanaljorden", "Kanaljorden"]


def test_lru_eviction_does_not_retain_captured_bodies(tmp_path: Path) -> None:
    from bijux_pollenomics.adna import homo_sapiens as runtime

    runtime._cached_release_samples.cache_clear()
    runtime._cached_country_records.cache_clear()
    for i in range(33):
        _, manifest = _manifest(tmp_path, f"v{i}")
        load_species_samples(manifest, query=AdnaSampleQuery(political_entity="Sweden"))
    assert runtime._cached_release_samples.cache_info().currsize == 32
    assert runtime._cached_country_records.cache_info().currsize == 32
    assert runtime._CAPTURED_RELEASE.get() is None


def test_mutation_during_capture_refuses_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.core.filesystem import regular_inputs

    path, manifest = _manifest(tmp_path)
    actual_read = regular_inputs.os.read
    changed = False

    def mutate_on_read(fd: int, size: int) -> bytes:
        nonlocal changed
        result = actual_read(fd, size)
        if result and not changed:
            changed = True
            path.write_bytes(path.read_bytes().replace(b"Kanaljorden", b"Xanaljorden"))
        return result

    monkeypatch.setattr(regular_inputs.os, "read", mutate_on_read)
    with pytest.raises(ValueError, match="changed"):
        load_species_samples(manifest)


def test_hardlinked_annotation_remains_supported(tmp_path: Path) -> None:
    path, manifest = _manifest(tmp_path)
    os.link(path, tmp_path / "linked.anno")
    assert load_species_samples(manifest)[0][0].locality == "Kanaljorden"
