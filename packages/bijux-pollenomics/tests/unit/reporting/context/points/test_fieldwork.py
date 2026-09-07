"""Fieldwork context-point projection coverage."""

from __future__ import annotations

from pathlib import Path
import tempfile
from typing import cast
import unittest

from bijux_pollenomics.reporting.context import build_context_layers
from bijux_pollenomics.reporting.geography import build_published_geography_plan


class FieldworkLayerTests(unittest.TestCase):
    def test_build_context_layers_adds_fieldwork_point_when_gallery_media_exists(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            docs_root = Path(tmp) / "docs"
            output_dir = docs_root / "report" / "nordic-atlas"
            gallery_root = docs_root / "gallery"
            output_dir.mkdir(parents=True, exist_ok=True)
            gallery_root.mkdir(parents=True, exist_ok=True)
            (gallery_root / "2026-02-26-data-collection.JPG").write_bytes(b"jpeg")
            (gallery_root / "2026-02-26-data-collection.mp4").write_bytes(b"mp4")

            point_layers, polygon_layers, extra_artifacts = build_context_layers(
                samples=(),
                version="v66",
                output_dir=output_dir,
                context_root=None,
            )

        self.assertEqual(len(polygon_layers), 0)
        self.assertEqual(extra_artifacts, [])
        self.assertEqual(point_layers[1]["key"], "fieldwork-documentation")
        fieldwork_features = cast(list[dict[str, object]], point_layers[1]["features"])
        media_links = cast(
            list[dict[str, object]], fieldwork_features[0]["media_links"]
        )
        self.assertEqual(fieldwork_features[0]["title"], "Lyngsjön Lake field sampling")
        self.assertEqual(
            fieldwork_features[0]["record_id"],
            "bijux:fieldwork:lyngsjon-lake:2026-02-26",
        )
        self.assertEqual(
            media_links[0]["url"],
            "../../gallery/2026-02-26-data-collection.JPG",
        )
        self.assertEqual(
            media_links[1]["url"],
            "../../gallery/2026-02-26-data-collection.mp4",
        )

    def test_fieldwork_layer_uses_public_path_during_isolated_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs_root = root / "docs"
            published_output_dir = docs_root / "report" / "regions" / "nordic"
            gallery_root = docs_root / "gallery"
            physical_output_dir = root / "artifacts" / "isolated-report"
            gallery_root.mkdir(parents=True, exist_ok=True)
            physical_output_dir.mkdir(parents=True, exist_ok=True)
            (gallery_root / "2026-02-26-data-collection.JPG").write_bytes(b"jpeg")

            point_layers, _, _ = build_context_layers(
                samples=(),
                version="v66",
                output_dir=physical_output_dir,
                published_output_dir=published_output_dir,
                context_root=None,
                geography_scope=build_published_geography_plan(
                    ("Sweden", "Denmark", "Norway", "Finland")
                ).regional_scopes[-1],
            )

        fieldwork_features = cast(list[dict[str, object]], point_layers[1]["features"])
        media_links = cast(
            list[dict[str, object]], fieldwork_features[0]["media_links"]
        )
        self.assertEqual(
            media_links[0]["url"],
            "../../../gallery/2026-02-26-data-collection.JPG",
        )


if __name__ == "__main__":
    unittest.main()
