from __future__ import annotations

import hashlib
import json

import pytest

from .repository_paths import REPO_ROOT

pytestmark = pytest.mark.generated_artifacts

PUBLICATION_ROOT = REPO_ROOT / "docs" / "gallery" / "nordic-atlas" / "chronology"
PAGE = (
    REPO_ROOT / "docs" / "public" / "nordic-atlas" / "chronology-playback" / "index.md"
)
EXPECTED_STORIES = (
    "neotoma-source-sample-presence",
    "neotoma-source-code-trsh",
    "neotoma-source-code-uphe",
    "neotoma-source-code-aqvp",
    "neotoma-source-taxon-967",
    "pangaea-937075-metric-cerealia-t",
    "pangaea-937075-metric-secale",
    "pangaea-937075-metric-ol",
)
EXPECTED_PUBLIC_ROWS = {
    "neotoma-source-sample-presence": {
        "node_count": 9988,
        "observation_denominator": 215903,
        "frame_count": 230,
        "first_interval": (22811, 22911),
        "last_interval": (0, 11),
        "page_row": "| all Neotoma pollen samples | 9,988 nodes / 215,903 observations | 230 contiguous windows; 100 years except the terminal window |",
    },
    "neotoma-source-code-trsh": {
        "node_count": 9978,
        "observation_denominator": 114225,
        "frame_count": 230,
        "first_interval": (22811, 22911),
        "last_interval": (0, 11),
        "page_row": "| TRSH — trees and shrubs | 9,978 nodes / 114,225 observations | 230 contiguous windows; 100 years except the terminal window |",
    },
    "neotoma-source-code-uphe": {
        "node_count": 9928,
        "observation_denominator": 91739,
        "frame_count": 230,
        "first_interval": (22811, 22911),
        "last_interval": (0, 11),
        "page_row": "| UPHE — upland herbs | 9,928 nodes / 91,739 observations | 230 contiguous windows; 100 years except the terminal window |",
    },
    "neotoma-source-code-aqvp": {
        "node_count": 4991,
        "observation_denominator": 9666,
        "frame_count": 192,
        "first_interval": (19090, 19190),
        "last_interval": (0, 90),
        "page_row": "| AQVP — aquatic vascular plants | 4,991 nodes / 9,666 observations | 192 contiguous windows; 100 years except the terminal window |",
    },
    "neotoma-source-taxon-967": {
        "node_count": 469,
        "observation_denominator": 469,
        "frame_count": 45,
        "first_interval": (4361, 4461),
        "last_interval": (2, 61),
        "page_row": "| exact taxon: *Secale* | 469 nodes / 469 observations | 45 contiguous windows; 100 years except the terminal window; source taxon 967 only |",
    },
    "pangaea-937075-metric-ol": {
        "node_count": None,
        "observation_denominator": None,
        "frame_count": 25,
        "first_interval": (11200, 11700),
        "last_interval": (0, 100),
        "page_row": "| open land (OL) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |",
    },
    "pangaea-937075-metric-cerealia-t": {
        "node_count": None,
        "observation_denominator": None,
        "frame_count": 25,
        "first_interval": (11200, 11700),
        "last_interval": (0, 100),
        "page_row": "| modeled cereal type (Cerealia.t) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |",
    },
    "pangaea-937075-metric-secale": {
        "node_count": None,
        "observation_denominator": None,
        "frame_count": 25,
        "first_interval": (11200, 11700),
        "last_interval": (0, 100),
        "page_row": "| modeled *Secale cereale* | 75 modeled cells per frame | 25 source-defined windows; no interpolation |",
    },
}


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def test_chronology_page_embeds_the_exact_governed_media_inventory() -> None:
    page = PAGE.read_text(encoding="utf-8")
    atlas_index = (
        REPO_ROOT / "docs" / "public" / "nordic-atlas" / "index.md"
    ).read_text(encoding="utf-8")
    manifest = json.loads(
        (PUBLICATION_ROOT / "publication-manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["schema_version"] == "atlas-media-publication.v2"
    assert manifest["story_count"] == len(EXPECTED_STORIES)
    assert tuple(row["story_id"] for row in manifest["stories"]) == EXPECTED_STORIES
    assert page.count(
        '<video controls preload="metadata" muted playsinline loop'
    ) == len(EXPECTED_STORIES)
    assert "autoplay" not in page
    assert 'href="./chronology-playback/"' in atlas_index
    for story in manifest["stories"]:
        expected = EXPECTED_PUBLIC_ROWS[story["story_id"]]
        assert story["node_count"] == expected["node_count"]
        assert story["observation_denominator"] == expected["observation_denominator"]
        assert story["frame_count"] == expected["frame_count"]
        assert (
            story["first_frame"]["time_start_bp"],
            story["first_frame"]["time_end_bp"],
        ) == expected["first_interval"]
        assert (
            story["last_frame"]["time_start_bp"],
            story["last_frame"]["time_end_bp"],
        ) == expected["last_interval"]
        assert expected["page_row"] in page
    for story_id in EXPECTED_STORIES:
        for suffix in (".poster.png", ".mp4"):
            relative = f"media/{story_id}{suffix}"
            assert (PUBLICATION_ROOT / relative).is_file()
            assert f"../../../gallery/nordic-atlas/chronology/{relative}" in page


def test_chronology_page_preserves_scientific_refusals() -> None:
    page = PAGE.read_text(encoding="utf-8")
    prose = " ".join(page.split())
    manifest = json.loads(
        (PUBLICATION_ROOT / "publication-manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["scientific_posture"] == {
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
        "null_not_zero": True,
        "interpolation_allowed": False,
        "observation_is_propagation": False,
        "modeled_context_is_observation": False,
    }
    assert manifest["candidate_succession"]["status"] == "refused"
    assert manifest["candidate_succession"]["reason_code"] == (
        "accepted_scientific_classifications_not_available"
    )
    for statement in (
        "not evidence of movement, migration, causation, or propagation",
        "not an observed pollen trajectory",
        "Null ages remain unavailable and are never converted to zero",
        "accepted_scientific_classifications_not_available",
    ):
        assert statement in prose


def test_publication_manifest_assets_match_the_published_bytes() -> None:
    manifest_path = PUBLICATION_ROOT / "publication-manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
    manifest = json.loads(manifest_bytes)

    assert (PUBLICATION_ROOT / "publication-manifest.sha256").read_text(
        encoding="utf-8"
    ) == f"{manifest_digest}  publication-manifest.json\n"
    content = {key: value for key, value in manifest.items() if key != "content_sha256"}
    assert (
        manifest["content_sha256"]
        == hashlib.sha256(_canonical_json_bytes(content)).hexdigest()
    )

    expected_files = {
        "publication-manifest.json",
        "publication-manifest.sha256",
    }
    for story in manifest["stories"]:
        for asset in story["assets"]:
            published = asset["published"]
            expected_files.add(published["path"])
            path = PUBLICATION_ROOT / published["path"]
            assert path.stat().st_size == published["byte_count"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == published["sha256"]

    observed_files = {
        path.relative_to(PUBLICATION_ROOT).as_posix()
        for path in PUBLICATION_ROOT.rglob("*")
        if path.is_file()
    }
    assert observed_files == expected_files
