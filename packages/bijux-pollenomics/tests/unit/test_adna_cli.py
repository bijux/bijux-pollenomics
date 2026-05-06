from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch

from bijux_pollenomics.command_line.runtime.handlers import run_adna_species


class AdnaCliUnitTests(unittest.TestCase):
    def test_adna_species_json_output_exposes_human_support_row(self) -> None:
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            exit_code = run_adna_species(type("Args", (), {"json": True})())

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        human_row = next(
            row for row in payload if row["latin_name"] == "Homo sapiens"
        )
        self.assertEqual(human_row["support_status"], "supported")
        self.assertEqual(human_row["source_families"], ["AADR"])


if __name__ == "__main__":
    unittest.main()
