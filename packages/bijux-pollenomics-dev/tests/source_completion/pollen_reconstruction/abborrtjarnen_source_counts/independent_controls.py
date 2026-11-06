"""Small original/native source fixtures, with no retained measurement reads."""

from typing import Any

AXIS = (
    ("Betula", 29),
    ("Cyperaceae", 74),
    ("Juniperus communis", 4416),
    ("Pinus sylvestris", 1287),
    ("Poaceae", 417),
)
COLUMNS = ("Bet [#]", "Cypae [#]", "Jun.c [#]", "Pin.s [#]", "Poac [#]")


def original_control(second: str = "0") -> bytes:
    """Build a two-depth source-text fixture with an adjustable count token."""
    return (
        "/* DATA DESCRIPTION:\n"
        "Citation: Giesecke, Thomas (2010): Pollen profile ABBO, Abborrtjärnen, Sweden; PANGAEA.738429\n"
        "Date: 2010-05-11\n"
        "License: CC-BY-NC-3.0\n"
        "DEPTH, sediment/rock [m]\n"
        "Betula [#] (Bet) * COMMENT: Betula\n"
        "Cyperaceae [#] (Cypae) * COMMENT: Cyperaceae\n"
        "Pinus sylvestris [#] (Pin.s) * COMMENT: Pinus diploxylon-type\n"
        "Poaceae [#] (Poac) * COMMENT: Gramineae\n"
        "Juniperus communis [#] (Jun.c) * COMMENT: Juniperus-type\n"
        "*/\n"
        + "\t".join(("Depth sed [m]", *COLUMNS))
        + "\n1.01\t2\t0\t3\t4\t5\n1.02\t6\t"
        + second
        + "\t8\t9\t10\n"
    ).encode()


def native_control() -> dict[str, Any]:
    """Build a reordered two-sample native fixture with one absent count."""
    samples = []
    for sample_id, depth, values in [
        (20, 102, (6, None, 8, 9, 10)),
        (10, 101, (2, 0, 3, 4, 5)),
    ]:
        datum = [
            {
                "variablename": name,
                "taxonid": taxon_id,
                "value": value,
                "element": "pollen",
                "elementtype": "pollen",
                "units": "NISP",
            }
            for (name, taxon_id), value in zip(AXIS, values, strict=True)
            if value is not None
        ]
        samples.append({"sampleid": sample_id, "depth": depth, "datum": datum})
    return {
        "status": "success",
        "data": [
            {
                "site": {
                    "siteid": 13338,
                    "collectionunit": {
                        "collectionunitid": 14910,
                        "handle": "ABBO",
                        "dataset": {
                            "datasetid": 19913,
                            "samples": samples,
                            "database": "European Pollen Database",
                            "doi": ["10.21233/2vzb-bg61"],
                        },
                    },
                }
            }
        ],
    }


def producer_control_result(original: bytes, native: dict[str, Any]) -> dict[str, Any]:
    """Create only synthetic saved-result controls with the maintained consumer."""
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_source_counts.comparison import (
        compare_tables,
    )
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_source_counts.sources import (
        read_native,
        read_original,
    )

    return compare_tables(
        read_original(original.decode()),
        read_native(native),
        expected_samples=2,
        expected_reported=9,
    )
