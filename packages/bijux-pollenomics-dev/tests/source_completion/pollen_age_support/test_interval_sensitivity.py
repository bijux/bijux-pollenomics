"""The ABBO age-interval source route keeps preparation, prediction and score separate."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_age_support import (
    interval_sensitivity as subject,
)

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "configs/ci/report-ownership.json").is_file()
)
FIXTURES = ROOT / "artifacts/tests/pollen_age_support/interval_sensitivity"
REPORT = Path("docs/report/pollen-reconstruction/age-interval-sensitivity")
PARENT = Path("docs/report/pollen-reconstruction/swedish-direct-pollen")


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
        required = set(subject.SOURCE_INPUTS) | {subject.REPLAY, subject.DIRECT}
        for relative in required:
            target = self.repository / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.output = (
            self.repository / "artifacts/source/producer-output/source-products"
        )
        self.output.parent.mkdir(parents=True)
        self.commands: list[tuple[str, str | None]] = []

    def copy_stage(
        self, _repository: Path, stage: Path, name: str, target: str | None = None
    ) -> None:
        self.commands.append((name, target))
        if name == "prepare":
            for relative in subject.PREPARED:
                source = (
                    ROOT
                    / (
                        PARENT
                        if relative
                        in {
                            "prepared/dataset-53995.json",
                            "prepared/dataset-54001.json",
                        }
                        else REPORT
                    )
                    / relative
                )
                destination = stage / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
        elif name == "predict":
            assert target is not None
            site = subject.TARGETS[target]
            destination = stage / "predictions" / f"site-{site}.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(
                ROOT / REPORT / "predictions" / destination.name, destination
            )
        else:
            for relative in (
                "scores.csv",
                "predictions-scored.csv",
                "summary.json",
                "comparison.json",
            ):
                shutil.copyfile(ROOT / REPORT / relative, stage / relative)

    def test_five_original_stages_expose_seven_exact_outputs(self) -> None:
        with patch.object(subject, "_run", side_effect=self.copy_stage):
            result = subject.run(self.repository, self.output)
        self.assertEqual(
            self.commands,
            [
                ("prepare", None),
                ("predict", "19913"),
                ("predict", "53995"),
                ("predict", "54001"),
                ("score", None),
            ],
        )
        self.assertEqual(set(result["result_sha256"]), set(subject.PRODUCTS))
        self.assertEqual(len(result["complete_stage_sha256"]), 12)
        for relative in subject.PRODUCTS:
            self.assertEqual(sha(self.output / relative), sha(ROOT / REPORT / relative))

    def test_crossed_prediction_identity_is_refused(self) -> None:
        def crossed(
            repository: Path, stage: Path, name: str, target: str | None = None
        ) -> None:
            self.copy_stage(repository, stage, name, target)
            if name == "score":
                shutil.copyfile(
                    stage / "predictions/site-13338.json",
                    stage / "predictions/site-28869.json",
                )

        with (
            patch.object(subject, "_run", side_effect=crossed),
            self.assertRaisesRegex(ValueError, "saved prediction population differs"),
        ):
            subject.run(self.repository, self.output)

    def test_mutated_original_comparison_source_is_refused(self) -> None:
        def mutate(
            repository: Path, stage: Path, name: str, target: str | None = None
        ) -> None:
            self.copy_stage(repository, stage, name, target)
            if name == "score":
                source = repository / PARENT / "scores.csv"
                source.write_text(source.read_text() + "\n")

        with (
            patch.object(subject, "_run", side_effect=mutate),
            self.assertRaisesRegex(ValueError, "source or original comparison changed"),
        ):
            subject.run(self.repository, self.output)

    def test_incomplete_stage_is_refused(self) -> None:
        def incomplete(
            repository: Path, stage: Path, name: str, target: str | None = None
        ) -> None:
            self.copy_stage(repository, stage, name, target)
            if name == "score":
                (stage / "summary.json").unlink()

        with (
            patch.object(subject, "_run", side_effect=incomplete),
            self.assertRaisesRegex(ValueError, "stage file population differs"),
        ):
            subject.run(self.repository, self.output)

    def test_fresh_preparation_population_is_required_without_retained_prepared_refs(
        self,
    ) -> None:
        self.assertFalse((self.repository / REPORT / "age-bin-support.csv").exists())

        def incomplete(
            repository: Path, stage: Path, name: str, target: str | None = None
        ) -> None:
            self.copy_stage(repository, stage, name, target)
            if name == "prepare":
                manifest = stage / "input-manifest.json"
                payload = json.loads(manifest.read_bytes())
                payload["admitted_abbo_samples"] = 7
                manifest.write_text(
                    json.dumps(payload, indent=2, sort_keys=True) + "\n"
                )

        with (
            patch.object(subject, "_run", side_effect=incomplete),
            self.assertRaisesRegex(ValueError, "fresh preparation source population"),
        ):
            subject.run(self.repository, self.output)

    def test_prediction_modified_during_scoring_is_refused(self) -> None:
        def changed(
            repository: Path, stage: Path, name: str, target: str | None = None
        ) -> None:
            self.copy_stage(repository, stage, name, target)
            if name == "score":
                prediction = stage / "predictions/site-13338.json"
                payload = json.loads(prediction.read_bytes())
                payload["fit_records"][0]["nearest_training_center_km"] += 1
                prediction.write_text(
                    json.dumps(payload, indent=2, sort_keys=True) + "\n"
                )
                comparison = stage / "comparison.json"
                reference = json.loads(comparison.read_bytes())
                reference["prediction_sha256_before_target_scoring"][
                    prediction.name
                ] = sha(prediction)
                comparison.write_text(
                    json.dumps(reference, indent=2, sort_keys=True) + "\n"
                )
                score_path = stage / "scores.csv"
                with score_path.open(newline="") as stream:
                    reader = csv.DictReader(stream)
                    fields = list(reader.fieldnames or ())
                    rows = list(reader)
                for row in rows:
                    if row["target_dataset_id"] == "19913":
                        row["prediction_sha256"] = sha(prediction)
                with score_path.open("w", newline="") as stream:
                    writer = csv.DictWriter(
                        stream, fieldnames=fields, lineterminator="\n"
                    )
                    writer.writeheader()
                    writer.writerows(rows)

        with (
            patch.object(subject, "_run", side_effect=changed),
            self.assertRaisesRegex(ValueError, "prediction changed after scoring"),
        ):
            subject.run(self.repository, self.output)

    def test_outside_and_reused_output_are_refused_before_original_call(self) -> None:
        with patch.object(subject, "_run") as run:
            with self.assertRaisesRegex(
                ReportRebuildError, "below repository artifacts"
            ):
                subject.run(
                    self.repository, self.repository / "elsewhere/source-products"
                )
            self.output.mkdir()
            with self.assertRaisesRegex(ReportRebuildError, "output must be absent"):
                subject.run(self.repository, self.output)
            run.assert_not_called()

    def test_source_symlink_is_refused_before_original_call(self) -> None:
        source = self.repository / PARENT / "scores.csv"
        source.unlink()
        source.symlink_to(ROOT / PARENT / "scores.csv")
        with patch.object(subject, "_run") as run:
            with self.assertRaisesRegex(ReportRebuildError, "not a real regular path"):
                subject.run(self.repository, self.output)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
