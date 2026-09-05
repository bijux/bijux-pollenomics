"""Tests for transparent compressed archive-metadata recovery."""

from __future__ import annotations

import gzip
from pathlib import Path
import tempfile

import pytest

from bijux_pollenomics.adna.projects.sample_master.archive import (
    _build_archive_sample_accession_lookup,
    _project_scope_archive_sample_accessions,
)

from .support import SampleMasterRecoveryTestCase

pytestmark = pytest.mark.generated_artifacts


class CompressedArchiveTests(SampleMasterRecoveryTestCase):
    def test_archive_accession_readers_accept_compressed_archive_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory) / "data"
            archive_dir = (
                output_root
                / "adna"
                / "governance"
                / "source_library"
                / "projects"
                / "PRJTEST"
            )
            archive_dir.mkdir(parents=True, exist_ok=True)
            with gzip.open(
                archive_dir / "archive_metadata.html.gz", "wt", encoding="utf-8"
            ) as handle:
                handle.write(
                    "sample_accession\tsubmitted_ftp\n"
                    "SAMEA1\tftp://example.org/Alpha_E1.fastq.gz\n"
                    "SAMEA2\tftp://example.org/Beta_i1.fastq.gz\n"
                )

            accessions = _project_scope_archive_sample_accessions(
                output_root,
                "PRJTEST",
            )
            lookup = _build_archive_sample_accession_lookup(
                output_root,
                "PRJTEST",
            )

        self.assertEqual(accessions, ("SAMEA1", "SAMEA2"))
        self.assertEqual(lookup["alpha"], "SAMEA1")
        self.assertEqual(lookup["beta"], "SAMEA2")
