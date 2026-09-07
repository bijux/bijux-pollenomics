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
            "\tM1\tG1\tA\tSweden\t59\t18\tP\t\t\t\tAG\tU",
            "S2\tM2\tG2\tB\tSweden\tbad\t18\tP\t\t\t\tAG\tU",
        ],
        header=AADR_HEADER + "\tDate standard deviation in BP",
    )

    assert _parse(path) == []


def test_parser_keeps_zero_bp_and_normalizes_source_whitespace(tmp_path: Path) -> None:
    path = tmp_path / "ho" / "test.anno"
    write_anno_file(
        path,
        [
            " S1 \t M1 \tG1\t Upp  sala \t Sweden \t0\t0\t Paper  A \t2022\t\t0\tAG\tF",
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


def test_parser_refuses_negative_interval_but_preserves_source_dating_values(
    tmp_path: Path,
) -> None:
    path = tmp_path / "ho" / "test.anno"
    write_anno_file(
        path,
        [
            "CGG_2_105338.SG\tM1\tG1\tAssistens Kirkegård\tDenmark\t55.69\t12.55\tPaper\t2022\thistorical\t146\tHO\tU\t89"
        ],
        header=AADR_HEADER + "\tDate standard deviation in BP",
    )

    [sample] = _parse(path)

    assert sample.time_start_bp is None
    assert sample.time_end_bp is None
    assert sample.time_mean_bp is None
    assert sample.date_mean_bp == "146"
    assert sample.date_stddev_bp == "89"
    assert sample.dating_basis == "bp_mean_and_stddev"
    semantics = sample.chronology.as_temporal_semantics(source_family="AADR")
    assert semantics["comparability_posture"] == "refused"
    assert semantics["refusal_reason_code"] == "negative_bp"
