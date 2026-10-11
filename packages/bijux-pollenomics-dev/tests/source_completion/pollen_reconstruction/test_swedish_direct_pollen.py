"""Original Swedish direct-pollen source stages keep held-out counts inaccessible."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_reconstruction import (
    swedish_direct_pollen as subject,
)

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "configs/ci/report-ownership.json").is_file()
)
FIXTURES = ROOT / "artifacts/tests/pollen_reconstruction/swedish_direct_pollen"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SourceRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        FIXTURES.mkdir(parents=True, exist_ok=True)
        self.repository = FIXTURES / self._testMethodName
        if self.repository.exists():
            shutil.rmtree(self.repository)
        self.repository.mkdir()
        (self.repository / "artifacts").mkdir()
        for relative in (*subject.SOURCE_INPUTS, subject.ORIGINAL):
            target = self.repository / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.output = (
            self.repository / "artifacts/source/producer-output/source-products"
        )
        self.output.parent.mkdir(parents=True)
        self.calls: list[tuple[str, str | None]] = []

    def original_stage(
        self, _repository: Path, stage: Path, command: str, target: str | None = None
    ) -> None:
        self.calls.append((command, target))
        if command == "prepare":
            for relative in subject.PREPARED:
                source = ROOT / subject.FAMILY / relative
                dest = stage / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, dest)
        elif command == "predict":
            assert target is not None
            withheld = stage / f".withheld-dataset-{target}.json"
            self.assertTrue(withheld.is_file())
            self.assertFalse((stage / f"prepared/dataset-{target}.json").exists())
            site = subject.TARGETS[target]
            dest = stage / f"predictions/site-{site}.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / subject.FAMILY / "predictions" / dest.name, dest)
        elif command == "score":
            self.assertEqual(
                sorted(path.name for path in (stage / "predictions").iterdir()),
                ["site-13338.json", "site-28869.json", "site-28872.json"],
            )
            for relative in (*subject.PRODUCTS[9:], "REPORT.md"):
                shutil.copyfile(ROOT / subject.FAMILY / relative, stage / relative)
        else:
            raise AssertionError("Unknown stage")

    def test_original_stages_publish_only_twelve_computed_files(self) -> None:
        with patch.object(subject, "_run", side_effect=self.original_stage):
            result = subject.run(self.repository, self.output)
        self.assertEqual(
            self.calls,
            [
                ("prepare", None),
                ("predict", "19913"),
                ("predict", "53995"),
                ("predict", "54001"),
                ("score", None),
            ],
        )
        self.assertEqual(set(result["result_sha256"]), set(subject.PRODUCTS))
        self.assertEqual(len(result["complete_stage_sha256"]), 13)
        self.assertFalse((self.output / "REPORT.md").exists())
        for relative in subject.PRODUCTS:
            self.assertEqual(
                sha(self.output / relative), sha(ROOT / subject.FAMILY / relative)
            )

    def test_target_profile_access_is_physically_refused_during_prediction(
        self,
    ) -> None:
        def leaking(
            repository: Path, stage: Path, command: str, target: str | None = None
        ) -> None:
            self.original_stage(repository, stage, command, target)
            if command == "predict":
                assert target is not None
                (stage / f"prepared/dataset-{target}.json").read_bytes()

        with (
            patch.object(subject, "_run", side_effect=leaking),
            self.assertRaises(FileNotFoundError),
        ):
            subject.run(self.repository, self.output)
        self.assertTrue(
            (
                self.repository
                / "artifacts/source/retained-work/prepared/dataset-19913.json"
            ).is_file()
        )

    def test_prediction_changed_during_scoring_is_refused(self) -> None:
        def changed(
            repository: Path, stage: Path, command: str, target: str | None = None
        ) -> None:
            self.original_stage(repository, stage, command, target)
            if command == "score":
                path = stage / "predictions/site-13338.json"
                payload = json.loads(path.read_bytes())
                payload["fit_records"][0]["nearest_training_center_km"] += 1
                path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

        with (
            patch.object(subject, "_run", side_effect=changed),
            self.assertRaisesRegex(ValueError, "prediction changed after scoring"),
        ):
            subject.run(self.repository, self.output)

    def test_incomplete_score_stage_is_refused(self) -> None:
        def incomplete(
            repository: Path, stage: Path, command: str, target: str | None = None
        ) -> None:
            self.original_stage(repository, stage, command, target)
            if command == "score":
                (stage / "summary.json").unlink()

        with (
            patch.object(subject, "_run", side_effect=incomplete),
            self.assertRaisesRegex(ValueError, "stage file population differs"),
        ):
            subject.run(self.repository, self.output)

    def test_duplicate_score_key_is_refused_without_changing_row_count(self) -> None:
        def duplicated(
            repository: Path, stage: Path, command: str, target: str | None = None
        ) -> None:
            self.original_stage(repository, stage, command, target)
            if command == "score":
                path = stage / "scores.csv"
                with path.open(newline="") as stream:
                    reader = csv.DictReader(stream)
                    fields = list(reader.fieldnames or ())
                    rows = list(reader)
                rows[1] = dict(rows[0])
                with path.open("w", newline="") as stream:
                    writer = csv.DictWriter(
                        stream, fieldnames=fields, lineterminator="\n"
                    )
                    writer.writeheader()
                    writer.writerows(rows)

        with (
            patch.object(subject, "_run", side_effect=duplicated),
            self.assertRaisesRegex(ValueError, "score denominator"),
        ):
            subject.run(self.repository, self.output)

    def test_source_mutation_is_refused_after_original_score(self) -> None:
        def changed(
            repository: Path, stage: Path, command: str, target: str | None = None
        ) -> None:
            self.original_stage(repository, stage, command, target)
            if command == "score":
                source = repository / subject.FAMILY / "config.json"
                source.write_text(source.read_text() + "\n")

        with (
            patch.object(subject, "_run", side_effect=changed),
            self.assertRaisesRegex(ValueError, "original source changed"),
        ):
            subject.run(self.repository, self.output)

    def test_symlink_and_reused_output_refuse_before_original_stage(self) -> None:
        source = self.repository / subject.RAW / "part-004.json"
        source.unlink()
        source.symlink_to(ROOT / subject.RAW / "part-004.json")
        with (
            patch.object(subject, "_run") as original,
            self.assertRaisesRegex(ReportRebuildError, "not a real regular path"),
        ):
            subject.run(self.repository, self.output)
        original.assert_not_called()
        source.unlink()
        shutil.copyfile(ROOT / subject.RAW / "part-004.json", source)
        self.output.mkdir()
        with (
            patch.object(subject, "_run") as original,
            self.assertRaisesRegex(ReportRebuildError, "output must be absent"),
        ):
            subject.run(self.repository, self.output)
        original.assert_not_called()


if __name__ == "__main__":
    unittest.main()
