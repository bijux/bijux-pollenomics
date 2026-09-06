"""Tests for recovered chronology text normalization."""

from __future__ import annotations

import pytest
from bijux_pollenomics.adna.projects.sample_master.identity import (
    _format_horse_age_text,
)

from .support import SampleMasterRecoveryTestCase

pytestmark = pytest.mark.generated_artifacts


class ChronologyTests(SampleMasterRecoveryTestCase):
    def test_horse_age_text_keeps_range_labels_stable(self) -> None:
        self.assertEqual(
            _format_horse_age_text("5500 - 5700"),
            "5500-5700 BP",
        )
        self.assertEqual(
            _format_horse_age_text("2300"),
            "2300 BP",
        )
