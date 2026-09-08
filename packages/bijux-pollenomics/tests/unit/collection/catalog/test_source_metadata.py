from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.collection.catalog.metadata import (
    build_repository_source_metadata,
    build_source_metadata,
)
from bijux_pollenomics.collection.contracts.models import SourceAcquisitionMetadata


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_sead_manifest(
    source_root: Path, source_run_id: str, *, directory_run_id: str | None = None
) -> None:
    _write_json(
        source_root
        / "normalized"
        / "acquisitions"
        / (directory_run_id or source_run_id)
        / "evidence_materialization_manifest.json",
        {
            "schema_version": "sead-evidence-materialization-manifest.v1",
            "source_run_id": source_run_id,
        },
    )


def _write_sead_receipt(
    source_root: Path,
    source_run_id: str,
    payload: dict[str, object],
    *,
    filename: str = "tbl_sites.json",
) -> None:
    _write_json(
        source_root / "raw" / "acquisitions" / source_run_id / "receipts" / filename,
        payload,
    )


def _complete_sead_receipt(
    *,
    completed_at: str = "2026-09-05T23:59:00Z",
    route: str = "postgrest_dependency_scoped",
) -> dict[str, object]:
    return {
        "schema_version": "sead-scoped-acquisition-receipt.v1",
        "source": "SEAD",
        "status": "complete",
        "completed_at": completed_at,
        "route": route,
    }


def _repository_metadata(source: str, source_root: Path) -> SourceAcquisitionMetadata:
    return build_repository_source_metadata(
        selected_sources=(source,),
        version="v66",
        source_output_roots={source: str(source_root)},
    )[source]


class SourceMetadataUnitTests(unittest.TestCase):
    def test_build_source_metadata_covers_selected_sources(self) -> None:
        metadata = build_source_metadata(
            selected_sources=("aadr", "landclim", "raa"), version="v62.0"
        )

        self.assertEqual(tuple(metadata), ("aadr", "landclim", "raa"))
        self.assertEqual(metadata["aadr"].version, "v62.0")
        self.assertEqual(metadata["aadr"].acquisition_method, "collector_pipeline")
        self.assertTrue(metadata["raa"].license)

    def test_boundary_metadata_uses_its_source_version_and_terms(self) -> None:
        metadata = build_source_metadata(
            selected_sources=("aadr", "boundaries"), version="v66"
        )

        self.assertEqual(metadata["aadr"].version, "v66")
        self.assertEqual(metadata["boundaries"].version, "5.1.1")
        self.assertEqual(metadata["boundaries"].license, "Natural Earth public domain")

    def test_repository_metadata_reads_only_recognized_source_receipt_dates(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            source_roots = {
                source: str(data_root / source)
                for source in (
                    "aadr",
                    "boundaries",
                    "landclim",
                    "neotoma",
                    "raa",
                    "svar",
                )
            }
            receipts = {
                "boundaries/raw/source_manifest.json": {
                    "schema_version": "natural-earth-boundary-receipt.v1",
                    "source": "Natural Earth",
                    "generated_on": "2026-09-04",
                },
                "landclim/raw/landclim_sources.json": {
                    "schema_version": "landclim-raw-receipt.v1",
                    "source": "LandClim",
                    "generated_on": "2026-03-31",
                },
                "neotoma/raw/neotoma_pollen_dataset_downloads/manifest.json": {
                    "source": "Neotoma",
                    "endpoint_template": (
                        "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}"
                    ),
                    "generated_on": "2026-04-01",
                },
                "svar/raw/svar_lake_registry_manifest.json": {
                    "source": "SMHI SVAR",
                    "wfs_url": "https://vattenwebb.smhi.se/svarwebb/svar.map",
                    "generated_on": "2026-06-22",
                },
            }
            for relative_path, payload in receipts.items():
                path = data_root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(payload), encoding="utf-8")

            metadata = build_repository_source_metadata(
                selected_sources=tuple(source_roots),
                version="v66",
                source_output_roots=source_roots,
            )

        self.assertEqual(metadata["boundaries"].retrieved_on, "2026-09-04")
        self.assertEqual(metadata["landclim"].retrieved_on, "2026-03-31")
        self.assertEqual(metadata["neotoma"].retrieved_on, "2026-04-01")
        self.assertEqual(metadata["svar"].retrieved_on, "2026-06-22")
        for source in source_roots:
            self.assertEqual(metadata[source].acquisition_method, "unavailable")
        self.assertEqual(metadata["aadr"].retrieved_on, "unavailable")
        self.assertEqual(metadata["raa"].retrieved_on, "unavailable")

    def test_repository_metadata_fails_closed_for_malformed_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "boundaries"
            receipt_path = source_root / "raw" / "source_manifest.json"
            receipt_path.parent.mkdir(parents=True)
            receipt_path.write_text(
                json.dumps(
                    {
                        "schema_version": "unexpected-schema",
                        "source": "Natural Earth",
                        "generated_on": "2026-09-04",
                    }
                ),
                encoding="utf-8",
            )

            metadata = build_repository_source_metadata(
                selected_sources=("boundaries",),
                version="v66",
                source_output_roots={"boundaries": str(source_root)},
            )["boundaries"]

        self.assertEqual(metadata.retrieved_on, "unavailable")
        self.assertEqual(metadata.acquisition_method, "unavailable")

    def test_repository_metadata_fails_closed_for_invalid_receipt_content(self) -> None:
        cases = {
            "invalid date": b'{"schema_version":"natural-earth-boundary-receipt.v1",'
            b'"source":"Natural Earth","generated_on":"not-a-date"}',
            "invalid json": b"{not-json",
            "invalid utf-8": b"\xff",
        }
        for label, content in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                source_root = Path(tmp) / "boundaries"
                receipt_path = source_root / "raw" / "source_manifest.json"
                receipt_path.parent.mkdir(parents=True)
                receipt_path.write_bytes(content)

                metadata = _repository_metadata("boundaries", source_root)

                self.assertEqual(metadata.retrieved_on, "unavailable")
                self.assertEqual(metadata.acquisition_method, "unavailable")

    def test_repository_metadata_rejects_ambiguous_or_mismatched_sead_manifest(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "sead"
            _write_sead_manifest(source_root, "run-a")
            _write_sead_manifest(source_root, "run-b")

            ambiguous = _repository_metadata("sead", source_root)

        self.assertEqual(ambiguous.retrieved_on, "unavailable")
        self.assertEqual(ambiguous.acquisition_method, "unavailable")

        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "sead"
            _write_sead_manifest(
                source_root, "declared-run", directory_run_id="different-run"
            )

            mismatched = _repository_metadata("sead", source_root)

        self.assertEqual(mismatched.retrieved_on, "unavailable")
        self.assertEqual(mismatched.acquisition_method, "unavailable")

    def test_repository_metadata_rejects_untrustworthy_sead_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "sead"
            _write_sead_manifest(source_root, "sead-test")

            missing = _repository_metadata("sead", source_root)

        self.assertEqual(missing.retrieved_on, "unavailable")
        self.assertEqual(missing.acquisition_method, "unavailable")

        cases = {
            "incomplete": {**_complete_sead_receipt(), "status": "incomplete"},
            "missing completion": {
                key: value
                for key, value in _complete_sead_receipt().items()
                if key != "completed_at"
            },
            "naive completion": _complete_sead_receipt(
                completed_at="2026-09-05T23:59:00"
            ),
        }
        for label, receipt in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                source_root = Path(tmp) / "sead"
                source_run_id = "sead-test"
                _write_sead_manifest(source_root, source_run_id)
                _write_sead_receipt(source_root, source_run_id, receipt)

                metadata = _repository_metadata("sead", source_root)

                self.assertEqual(metadata.retrieved_on, "unavailable")
                self.assertEqual(metadata.acquisition_method, "unavailable")

    def test_repository_metadata_rejects_conflicting_sead_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "sead"
            source_run_id = "sead-test"
            _write_sead_manifest(source_root, source_run_id)
            _write_sead_receipt(
                source_root,
                source_run_id,
                _complete_sead_receipt(route="postgrest_dependency_scoped"),
            )
            _write_sead_receipt(
                source_root,
                source_run_id,
                _complete_sead_receipt(route="alternate_route"),
                filename="tbl_datasets.json",
            )

            metadata = _repository_metadata("sead", source_root)

        self.assertEqual(metadata.retrieved_on, "unavailable")
        self.assertEqual(metadata.acquisition_method, "unavailable")

    def test_repository_metadata_normalizes_sead_completion_to_utc_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "sead"
            source_run_id = "sead-test"
            _write_sead_manifest(source_root, source_run_id)
            _write_sead_receipt(
                source_root,
                source_run_id,
                _complete_sead_receipt(completed_at="2026-09-06T00:30:00+02:00"),
            )

            metadata = _repository_metadata("sead", source_root)

        self.assertEqual(metadata.retrieved_on, "2026-09-05")
        self.assertEqual(metadata.acquisition_method, "postgrest_dependency_scoped")

    def test_repository_metadata_uses_linked_sead_acquisition_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "sead"
            source_run_id = "sead-full-evidence-test"
            _write_sead_manifest(source_root, source_run_id)
            for filename, completed_at in (
                ("tbl_sites.json", "2026-09-05T23:59:00Z"),
                ("tbl_datasets.json", "2026-09-06T00:01:00Z"),
            ):
                _write_sead_receipt(
                    source_root,
                    source_run_id,
                    _complete_sead_receipt(completed_at=completed_at),
                    filename=filename,
                )

            metadata = build_repository_source_metadata(
                selected_sources=("sead",),
                version="v66",
                source_output_roots={"sead": str(source_root)},
            )["sead"]

        self.assertEqual(metadata.retrieved_on, "2026-09-06")
        self.assertEqual(metadata.acquisition_method, "postgrest_dependency_scoped")


if __name__ == "__main__":
    unittest.main()
