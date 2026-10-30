"""Artificial exact-identity joins; no retained counts or scientific scores read."""

import copy
from pathlib import Path
from typing import Any
import unittest

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.outputs import publish_phase
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import comparison as M


class TestComparison(unittest.TestCase):
    def fixture(self) -> list[Any]:
        window = [2700.0, 3200.0]
        cells = {
            name: {"record": name, "counts": [3, 7], "support": "1" * 64}
            for name in M.CORES
        }
        identity = {
            "core": "BOKE",
            "physical_site": 28872,
            "dataset": 54001,
            "collection_unit": 39241,
            "window_cal_bp": window,
            "axis": list(M.AXIS),
            "scope": "pooled_eligible_nordic",
        }
        sources = [
            {
                "core": c,
                "physical_site": M.CORES[c][0],
                "dataset": M.CORES[c][1],
                "collection_unit": M.CORES[c][2],
                "window_cal_bp": window,
                "source_support_sha256": "1" * 64,
                "projected_panel_N": 10,
            }
            for c in ("BUS", "SOLSOE83")
        ]
        context = {
            "identity": identity,
            "training_sources": sources,
            "source_refusals": [
                {"core": "BOKE", "reason": "whole_target_physical_site_excluded"}
            ],
            "families": {"direct_panel_mean": {"status": "predicted"}},
        }
        direct = {
            "identity": identity,
            "status": "scored",
            "target_counts": {"Betula": 3, "Ulmus": 7},
            "target_panel_N": 10,
            "target_source_support_sha256": "1" * 64,
            "mae_fraction": 0.2,
            "total_variation": 0.2,
        }
        current = {
            "score": {"status": "scored", "mae_fraction": 0.1, "total_variation": 0.1},
            "observation": {"pollen_count": {"Betula": 3, "Ulmus": 7}},
        }
        training = {
            "outer_fold": {
                "train_record_ids": ["BUS", "SOLSOE83"],
                "test_record_ids": ["BOKE"],
            },
            "regional_anchor_record_id": "SOLSOE83",
            "training_products": [{"record_id": "BUS"}],
        }
        return [
            "BOKE",
            "pooled_eligible_nordic",
            window,
            current,
            context,
            direct,
            cells,
            copy.deepcopy(cells),
            training,
        ]

    def test_complete_both_training_comparison(self) -> None:
        row = M.joined(*self.fixture())
        self.assertEqual(row["status"], "paired")
        self.assertEqual(
            row["training_roles"],
            {
                "regional_proxy": "SOLSOE83",
                "local_predictor": "BUS",
                "direct_sources": ["BUS", "SOLSOE83"],
            },
        )
        self.assertEqual(row["direct"]["mae_fraction"], 0.2)
        self.assertEqual(row["coupled"]["mae_fraction"], 0.1)

    def test_complete_local_only_keeps_anchor_in_physical_lineage(self) -> None:
        args = self.fixture()
        args[1] = "swedish_only"
        args[4]["identity"]["scope"] = "swedish_only"
        args[4]["training_sources"] = args[4]["training_sources"][:1]
        row = M.joined(*args)
        self.assertEqual(row["status"], "paired")
        self.assertEqual(row["training_roles"]["direct_sources"], ["BUS"])
        self.assertEqual(row["training_roles"]["regional_proxy"], "SOLSOE83")

    def test_exact_mismatch_and_failure_refusals(self) -> None:
        for mutation in (
            "count",
            "support",
            "eligibility",
            "axis",
            "native",
            "target_leak",
            "score_refusal",
            "nonfinite",
        ):
            with self.subTest(mutation=mutation):
                args = self.fixture()
                if mutation == "count":
                    args[7]["BUS"]["counts"] = [4, 6]
                elif mutation == "support":
                    args[7]["BUS"]["support"] = "2" * 64
                elif mutation == "eligibility":
                    args[4]["training_sources"].append(
                        copy.deepcopy(args[4]["training_sources"][0])
                    )
                elif mutation == "axis":
                    args[4]["identity"]["axis"] = ["Ulmus", "Betula"]
                elif mutation == "native":
                    args[5]["identity"]["dataset"] = 1
                elif mutation == "target_leak":
                    args[8]["outer_fold"]["train_record_ids"] = ["BOKE", "BUS"]
                elif mutation == "score_refusal":
                    args[3]["score"]["status"] = "prediction_failed"
                else:
                    args[3]["score"]["mae_fraction"] = float("nan")
                self.assertEqual(M.joined(*args)["status"], "unmatched")


@pytest.fixture
def nested_product(tmp_path: Path) -> tuple[Path, str]:
    """Publish a genuine tiny nested inventory without an engine or model call."""
    stage = tmp_path / "stage"
    stage.mkdir()
    (stage / "training.json").write_text("[]\n")
    nested = stage / "batches" / "fold" / "items" / "record"
    nested.mkdir(parents=True)
    (nested / "receipt.json").write_text('{"status":"artificial"}\n')
    destination = tmp_path / "product"
    native = publish_phase(
        stage,
        destination,
        phase="predictions",
        scientific={"training": []},
        profile="source-observations-withheld-site-baselines-v1",
    )
    return destination, native.manifest_sha256


def test_complete_nested_native_product(nested_product: tuple[Path, str]) -> None:
    directory, checksum = nested_product
    manifest = M.product(directory, checksum)
    assert "batches/fold/items/record/receipt.json" in manifest["files"]
    assert manifest["scientific_payload"]["training"] == []


def test_tampered_nested_native_member(nested_product: tuple[Path, str]) -> None:
    directory, checksum = nested_product
    (directory / "batches/fold/items/record/receipt.json").write_text("{}\n")
    with pytest.raises(
        ValidationRefusal, match="Product byte inventory changed"
    ) as error:
        M.product(directory, checksum)
    assert error.value.reason_code == "invalid_experiment_product"
