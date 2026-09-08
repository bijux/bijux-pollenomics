"""Differential contracts for aurochs filename identity matching."""

from __future__ import annotations

import csv
from dataclasses import asdict
from hashlib import sha256
from io import StringIO
import json
import re
from unittest.mock import patch

from bijux_pollenomics.adna.projects.sample_master.tables.aurochs_natural_history import (
    ARCHIVE_IDENTITIES,
    _parse_archive_evidence,
)
from bijux_pollenomics.adna.projects.sample_master.tables.aurochs_natural_history.source_values import (
    _basename_has_label,
    _submitted_basenames,
)

from .support import governed_inputs


def _regex_reference_match(basename: str, label: str) -> bool:
    return re.match(rf"^{re.escape(label)}(?:[_\-.]|$)", basename) is not None


def test_literal_matcher_is_differentially_equal_to_anchored_regex_contract() -> None:
    labels = ("", "A", "a", "A.1", "A-1", "A_1", "A[1]", "A$", "Å\nB", ".")
    suffixes = ("", "_R1", "-R1", ".fastq", "X", "\n", "\nX", "\r\n", "/R1")
    basenames = {
        candidate
        for label in labels
        for candidate in (
            *(f"{label}{suffix}" for suffix in suffixes),
            f"prefix{label}",
            label.swapcase(),
        )
    }

    assert all(
        _basename_has_label(basename, label) == _regex_reference_match(basename, label)
        for basename in basenames
        for label in labels
    )


def test_governed_archive_output_is_byte_stable_after_claim_indexing() -> None:
    _, _, archive_text = governed_inputs()
    evidence = _parse_archive_evidence(archive_text)
    payload = json.dumps(
        {label: asdict(row) for label, row in sorted(evidence.items())},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()

    assert len(evidence) == 34
    assert sum(len(row.run_accessions) for row in evidence.values()) == 572
    assert sha256(payload).hexdigest() == (
        "4e72f4f14568ff2e7bdcce3426e83bacd007f9dbe8b30cc3408d7315342ced05"
    )


def test_each_archive_label_claim_is_scanned_only_once_per_parse() -> None:
    _, _, archive_text = governed_inputs()
    archive_rows = tuple(csv.DictReader(StringIO(archive_text), delimiter="\t"))
    basename_count = sum(
        len(_submitted_basenames(row["submitted_ftp"])) for row in archive_rows
    )

    with patch(
        "bijux_pollenomics.adna.projects.sample_master.tables."
        "aurochs_natural_history.source_evidence._basename_has_label",
        wraps=_basename_has_label,
    ) as matcher:
        _parse_archive_evidence(archive_text)

    label_count = len(ARCHIVE_IDENTITIES) + 1
    assert matcher.call_count <= basename_count * (label_count + 1)
