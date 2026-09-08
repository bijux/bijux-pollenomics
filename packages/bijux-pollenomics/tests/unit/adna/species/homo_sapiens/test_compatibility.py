"""Compatibility and ownership checks for the Homo sapiens facade."""

import inspect
from pathlib import Path

from bijux_pollenomics.adna import homo_sapiens


def test_facade_preserves_public_and_cache_seams() -> None:
    expected_public = {
        "build_homo_sapiens_runtime_manifest",
        "build_homo_sapiens_runtime_manifest_for_version_dir",
        "discover_homo_sapiens_anno_files",
        "iter_homo_sapiens_samples_from_anno",
        "load_homo_sapiens_country_samples",
        "load_homo_sapiens_samples",
    }

    assert set(homo_sapiens.__all__) == expected_public
    assert homo_sapiens._cached_release_samples.cache_parameters() == {
        "maxsize": 32,
        "typed": False,
    }
    assert homo_sapiens._cached_country_records.cache_parameters() == {
        "maxsize": 32,
        "typed": False,
    }
    assert str(inspect.signature(homo_sapiens.load_homo_sapiens_samples)) == (
        "(*, manifest: 'AdnaSpeciesRuntimeManifest', "
        "query: 'AdnaSampleQuery | None' = None) -> "
        "'tuple[list[AdnaSampleRecord], Counter[str]]'"
    )


def test_runtime_is_grouped_by_intent_with_bounded_modules() -> None:
    package_root = Path(homo_sapiens.__file__).parent
    modules = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in package_root.glob("*.py")
    }

    assert set(modules) == {
        "__init__.py",
        "chronology.py",
        "constants.py",
        "loading.py",
        "manifest.py",
        "records.py",
        "release.py",
        "release_manifest.py",
        "text.py",
    }
    assert max(modules.values()) <= 220
