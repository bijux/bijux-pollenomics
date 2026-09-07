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
    "neotoma-source-taxon-416",
    "neotoma-source-taxon-427",
    "neotoma-source-taxon-1947",
    "neotoma-source-taxon-3924",
    "neotoma-source-taxon-967",
    "neotoma-source-taxon-3926",
    "neotoma-source-taxon-488",
    "neotoma-source-taxon-969",
    "pangaea-937075-metric-cerealia-t",
    "pangaea-937075-metric-secale",
    "pangaea-937075-metric-ol",
    "pangaea-937075-metric-et",
    "pangaea-937075-metric-st",
    "pangaea-937075-metric-lse",
    "pangaea-937075-metric-gl",
    "pangaea-937075-metric-al",
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
    "neotoma-source-taxon-416": {
        "node_count": 28,
        "observation_denominator": 28,
        "frame_count": 24,
        "first_interval": (2237, 2337),
        "last_interval": (0, 37),
        "page_row": "| exact taxon: Poaceae (Cerealia) | 28 nodes / 28 observations | 24 contiguous windows; 2,337–0 BP; source taxon 416 only |",
    },
    "neotoma-source-taxon-427": {
        "node_count": 257,
        "observation_denominator": 257,
        "frame_count": 90,
        "first_interval": (8854.761, 8954.761),
        "last_interval": (0, 54.76100000000042),
        "page_row": "| exact taxon: Poaceae (Cerealia) undiff. | 257 nodes / 257 observations | 90 contiguous windows; 8,954.761–0 BP; source taxon 427 only |",
    },
    "neotoma-source-taxon-1947": {
        "node_count": 375,
        "observation_denominator": 375,
        "frame_count": 119,
        "first_interval": (11791, 11891),
        "last_interval": (2, 91),
        "page_row": "| exact taxon: Poaceae (Cerealia-type) | 375 nodes / 375 observations | 119 contiguous windows; 11,891–2 BP; source taxon 1947 only |",
    },
    "neotoma-source-taxon-3924": {
        "node_count": 2,
        "observation_denominator": 2,
        "frame_count": 14,
        "first_interval": (1651, 1751),
        "last_interval": (376, 451),
        "page_row": "| exact taxon: *Hordeum/Secale* | 2 nodes / 2 observations | 14 contiguous windows; 1,751–376 BP; source taxon 3924 only |",
    },
    "neotoma-source-taxon-967": {
        "node_count": 469,
        "observation_denominator": 469,
        "frame_count": 45,
        "first_interval": (4361, 4461),
        "last_interval": (2, 61),
        "page_row": "| exact taxon: *Secale* | 469 nodes / 469 observations | 45 contiguous windows; 100 years except the terminal window; source taxon 967 only |",
    },
    "neotoma-source-taxon-3926": {
        "node_count": 191,
        "observation_denominator": 191,
        "frame_count": 31,
        "first_interval": (2967, 3067),
        "last_interval": (0, 67),
        "page_row": "| exact taxon: *Secale cereale* | 191 nodes / 191 observations | 31 contiguous windows; 3,067–0 BP; source taxon 3926 only |",
    },
    "neotoma-source-taxon-488": {
        "node_count": 45,
        "observation_denominator": 45,
        "frame_count": 38,
        "first_interval": (3708, 3808),
        "last_interval": (29, 108),
        "page_row": "| exact taxon: *Secale*-type | 45 nodes / 45 observations | 38 contiguous windows; 3,808–29 BP; source taxon 488 only |",
    },
    "neotoma-source-taxon-969": {
        "node_count": 153,
        "observation_denominator": 153,
        "frame_count": 72,
        "first_interval": (7097.5, 7197.5),
        "last_interval": (11, 97.5),
        "page_row": "| exact taxon: *Triticum* | 153 nodes / 153 observations | 72 contiguous windows; 7,197.5–11 BP; source taxon 969 only |",
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
    "pangaea-937075-metric-et": {
        "node_count": None,
        "observation_denominator": None,
        "frame_count": 25,
        "first_interval": (11200, 11700),
        "last_interval": (0, 100),
        "page_row": "| evergreen trees (ET) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |",
    },
    "pangaea-937075-metric-st": {
        "node_count": None,
        "observation_denominator": None,
        "frame_count": 25,
        "first_interval": (11200, 11700),
        "last_interval": (0, 100),
        "page_row": "| summer-green trees (ST) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |",
    },
    "pangaea-937075-metric-lse": {
        "node_count": None,
        "observation_denominator": None,
        "frame_count": 25,
        "first_interval": (11200, 11700),
        "last_interval": (0, 100),
        "page_row": "| low shrub, broadleaved evergreen (LSE) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |",
    },
    "pangaea-937075-metric-gl": {
        "node_count": None,
        "observation_denominator": None,
        "frame_count": 25,
        "first_interval": (11200, 11700),
        "last_interval": (0, 100),
        "page_row": "| grassland — all herbs (GL) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |",
    },
    "pangaea-937075-metric-al": {
        "node_count": None,
        "observation_denominator": None,
        "frame_count": 25,
        "first_interval": (11200, 11700),
        "last_interval": (0, 100),
        "page_row": "| agricultural land — cereals (AL) | 75 modeled cells per frame | 25 source-defined windows; no interpolation |",
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

    assert manifest["schema_version"] == "atlas-media-publication.v4"
    assert manifest["story_count"] == len(EXPECTED_STORIES)
    assert manifest["publication_budget"]["published_asset_count"] == (
        2 * len(EXPECTED_STORIES)
    )
    assert tuple(row["story_id"] for row in manifest["stories"]) == EXPECTED_STORIES
    assert page.count(
        '<video controls preload="metadata" muted playsinline loop'
    ) == len(EXPECTED_STORIES)
    assert "autoplay" not in page
    assert 'href="./chronology-playback/"' in atlas_index
    assert "provides 20 pre-rendered views" in " ".join(atlas_index.split())
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
