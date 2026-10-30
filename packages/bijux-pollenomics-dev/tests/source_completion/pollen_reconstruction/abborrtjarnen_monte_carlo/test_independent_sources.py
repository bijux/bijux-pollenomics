"""Synthetic native-clock guards never read the actual saved ledger."""

import csv
import gzip
import io

import pytest

from .independent_sampling import BINS, TAXON_IDS
from .independent_sources import ordered_rows


def fixture_rows() -> list[dict[str, str]]:
    return [
        {
            "seed": str(seed),
            "native_row": str(3502 + row),
            "complete": "0" if seed == 271828 and row == 1 else "1",
            **{
                f"cover_{b}_{taxon}": str(j / 10)
                for b in BINS
                for j, taxon in enumerate(TAXON_IDS)
            },
        }
        for seed in (314159, 271828)
        for row in range(4)
    ]


def encode(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return gzip.compress(stream.getvalue().encode())


def test_undefined_state_retains_its_chain_native_position() -> None:
    result = ordered_rows(encode(fixture_rows()), rows_per_chain=4)
    assert len(result[0]) == len(result[1]) == 4
    assert result[1][1] is None
    assert sum(row is None for chain in result for row in chain) == 1


@pytest.mark.parametrize(
    "change", ["reorder", "duplicate", "missing", "extra", "nonbinary"]
)
def test_native_identity_or_mask_mutation_refuses(change: str) -> None:
    rows = fixture_rows()
    if change == "reorder":
        rows[0], rows[1] = rows[1], rows[0]
    elif change == "duplicate":
        rows[1] = dict(rows[0])
    elif change == "missing":
        rows.pop()
    elif change == "extra":
        rows.append(dict(rows[-1]))
    else:
        rows[0]["complete"] = "2"
    with pytest.raises(ValueError):
        ordered_rows(encode(rows), rows_per_chain=4)
