from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.adna import (
    AdnaSampleQuery,
    build_species_runtime_manifest,
    load_species_samples,
)
from tests.support.aadr import AADR_HEADER, write_anno_file


class AdnaRuntimeUnitTests(unittest.TestCase):
    def test_homo_sapiens_runtime_manifest_uses_species_owned_aadr_layout(self) -> None:
        manifest = build_species_runtime_manifest("Homo sapiens", version="v66")

        self.assertTrue(manifest.runtime_ready)
        self.assertEqual(manifest.species.latin_name, "Homo sapiens")
        self.assertEqual(manifest.source_bundles[0].tracked_root, "data/adna/species/homo_sapiens/raw/aadr/v66")
        self.assertEqual(
            manifest.source_bundles[0].release_manifest_path,
            "data/aadr/v66/release_manifest.json",
        )
        self.assertIn("metadata normalization only", manifest.analysis_boundary)

    def test_nonhuman_runtime_manifest_exposes_curated_sample_master_rows(self) -> None:
        manifest = build_species_runtime_manifest("horse")

        self.assertFalse(manifest.runtime_ready)
        self.assertGreaterEqual(len(manifest.source_bundles), 1)
        self.assertEqual(
            manifest.source_bundles[0].review_strength,
            "primary_paper_pinned",
        )
        self.assertEqual(
            manifest.source_bundles[0].release_manifest_path,
            "data/adna/species/equus_caballus/manifests/curation_manifest.json",
        )
        self.assertIn("Paper-pinned core domestication support exists", manifest.analysis_boundary)
        self.assertIn("curated accession-backed sample loading is available", manifest.analysis_boundary)
        samples, dataset_counts = load_species_samples(
            manifest,
            query=AdnaSampleQuery(review_strengths=("primary_paper_pinned",)),
        )

        self.assertTrue(samples)
        self.assertEqual(samples[0].species_latin_name, "Equus caballus")
        self.assertTrue(all(sample.paper_doi for sample in samples))
        self.assertTrue(dataset_counts)

    def test_comparator_runtime_manifest_preserves_comparator_review_strength(self) -> None:
        manifest = build_species_runtime_manifest("donkey")

        self.assertFalse(manifest.runtime_ready)
        self.assertGreaterEqual(len(manifest.source_bundles), 1)
        self.assertTrue(
            all(bundle.review_strength == "comparator_only" for bundle in manifest.source_bundles)
        )
        self.assertIn("comparator support", manifest.analysis_boundary)

    def test_species_loader_filters_homo_sapiens_samples_by_country_and_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            release_dir = data_root / "aadr" / "v99.1"
            write_anno_file(
                release_dir / "ho" / "v99.1.HO.aadr.PUB.anno",
                [
                    "\t".join(
                        [
                            "SE1",
                            "M1",
                            "G1",
                            "Uppsala",
                            "Sweden",
                            "59.8",
                            "17.6",
                            "PaperA",
                            "2022",
                            "500 BCE",
                            "2450",
                            "AG",
                            "F",
                        ]
                    ),
                    "\t".join(
                        [
                            "NO1",
                            "M2",
                            "G2",
                            "Oslo",
                            "Norway",
                            "59.9",
                            "10.7",
                            "PaperB",
                            "2021",
                            "600 BCE",
                            "2550",
                            "AG",
                            "M",
                        ]
                    ),
                ],
                header=AADR_HEADER + "\tDate standard deviation in BP",
            )
            (release_dir / "release_manifest.json").write_text(
                (
                    '{"anno_files":[{"dataset_name":"ho"}],'
                    '"source":"AADR","requested_version":"v99.1"}'
                ),
                encoding="utf-8",
            )
            adna_root = data_root / "adna" / "species" / "homo_sapiens" / "raw"
            adna_root.mkdir(parents=True, exist_ok=True)
            (adna_root / "aadr").symlink_to(Path("../../../../aadr"))

            manifest = build_species_runtime_manifest(
                "Homo sapiens",
                data_root=data_root,
                version="v99.1",
            )
            samples, dataset_counts = load_species_samples(
                manifest,
                query=AdnaSampleQuery(
                    political_entity="Sweden",
                    dataset_names=("ho",),
                    modalities=("metadata_only",),
                    provenance_qualities=("release_manifest_pinned",),
                ),
            )

            self.assertEqual(len(samples), 1)
            self.assertEqual(samples[0].political_entity, "Sweden")
            self.assertEqual(samples[0].source_release, "v99.1")
            self.assertEqual(samples[0].record_modality, "metadata_only")
            self.assertEqual(dataset_counts["ho"], 1)


if __name__ == "__main__":
    unittest.main()
