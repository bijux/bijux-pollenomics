"""AADR annotation parsing behavior at the Homo sapiens boundary."""

from pathlib import Path

from bijux_pollenomics.adna.domain.models import AdnaSampleRecord
from bijux_pollenomics.adna.species.homo_sapiens import (
    iter_homo_sapiens_samples_from_anno,
)

from tests.support.aadr import AADR_HEADER, write_anno_file


def _parse(path: Path) -> list[AdnaSampleRecord]:
    return list(
        iter_homo_sapiens_samples_from_anno(
            path,
            dataset_name="ho",
            source_release="v-test",
            source_family="AADR",
            record_modality="metadata_only",
            review_strength="curated_release_metadata",
            provenance_quality="release_manifest_pinned",
        )
    )


def test_parser_skips_rows_without_valid_identity_or_coordinates(
    tmp_path: Path,
) -> None:
    path = tmp_path / "ho" / "test.anno"
    write_anno_file(
        path,
        [
            "\t".join(
                ["", "M1", "G1", "A", "Sweden", "59", "18", "P", "", "", "", "AG", "U"]
            ),
            "\t".join(
                [
                    "S2",
                    "M2",
                    "G2",
                    "B",
                    "Sweden",
                    "bad",
                    "18",
                    "P",
                    "",
                    "",
                    "",
                    "AG",
                    "U",
                ]
            ),
        ],
        header=AADR_HEADER + "\tDate standard deviation in BP",
    )

    assert _parse(path) == []


def test_parser_keeps_zero_bp_and_normalizes_source_whitespace(tmp_path: Path) -> None:
    path = tmp_path / "ho" / "test.anno"
    write_anno_file(
        path,
        [
            "\t".join(
                [
                    " S1 ",
                    " M1 ",
                    "G1",
                    " Upp  sala ",
                    " Sweden ",
                    "0",
                    "0",
                    " Paper  A ",
                    "2022",
                    "",
                    "0",
                    "AG",
                    "F",
                ]
            ),
        ],
        header=AADR_HEADER + "\tDate standard deviation in BP",
    )

    [sample] = _parse(path)

    assert sample.genetic_id == "S1"
    assert sample.locality == "Upp sala"
    assert sample.publication == "Paper A"
    assert sample.latitude == 0.0
    assert sample.longitude == 0.0
    assert sample.time_start_bp == 0
    assert sample.time_end_bp == 0
