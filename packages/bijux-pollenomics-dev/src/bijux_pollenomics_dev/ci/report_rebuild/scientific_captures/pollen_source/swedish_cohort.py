"""Retain metadata source custody while preserving the refused fresh-cohort claim."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import ReportOwnershipError, _regular_confined_file
from ...retained_source import validate_capsule

CAPTURE: Any = "data/surface-reference/swedish-cohort-source-capture/capture.json"
CAPTURE_SHA256: Any = "a777339c3eb30ea62669b1054aea12a9363cf82d8cef57da907bb8a29727379e"
OWNER: Any = "source-relations/neotoma/swedish-cohort-availability/source-screen"

ORIGINAL_OWNER: JsonObject = {
    "owner_id": "source-relations/neotoma/swedish-cohort-availability/source-screen",
    "role": "unresolved",
    "paths": [
        "docs/report/source-relations/neotoma/swedish-cohort-availability/report.json"
    ],
    "producer_paths": [
        "docs/report/source-relations/neotoma/swedish-cohort-availability/replay.py"
    ],
    "producer_inputs": [
        "data/neotoma/relational/manifest.json",
        "data/neotoma/relational/surfaces/collection_units/part-00001.json",
        "data/neotoma/relational/surfaces/datasets/part-00001.json",
        "data/neotoma/relational/surfaces/sites/part-00001.json",
        "docs/report/source-relations/neotoma/swedish-cohort-availability/sources.json",
    ],
    "verification": "Replay requires --private-root: private source-manifest.json plus "
    "seven source records, EPD source-manifest.json and 17 "
    "metadata/age-table files. Those are not repository-confined; keep "
    "unresolved until exact private capture custody, permission and byte "
    "comparison are independently bound. Metadata-only refusal is not "
    "fresh-cohort acceptance.",
}
CORRECTION_WITNESS = (
    "reports/science/source-cohorts/swedish-cohort-original-acceptance.json"
)
CORRECTION_WITNESS_SHA256 = (
    "8a9e26bcc8aa17431e4cb3547c702537920b464c027d2880b25930b12cbdb3d3"
)
REPORT: Any = (
    "docs/report/source-relations/neotoma/swedish-cohort-availability/report.json"
)
SOURCE_DECLARATION = str(Path(REPORT).with_name("sources.json"))
ORIGINAL_CANDIDATE: Any = "c292dafa60f9d992f162c92dd327207d9aefd76b"
EXPECTED_MEMBERS: Any = {
    "execution/original/independent-swedish-cohort-metadata-observer.stderr": {
        "sha256": "58562cba88db2fb86820b029417db7d483714f25461da44ccb1f2efee183e60e",
        "bytes": 1159,
    },
    "execution/original/independent-swedish-cohort-metadata-observer.stdout": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/original/maintained-swedish-cohort-source.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/original/maintained-swedish-cohort-source.stdout": {
        "sha256": "0f5a2ab4dea5d15883a2725880fb6cd8e856705b9ea8c5c76b62c33ed7f470fb",
        "bytes": 531,
    },
    "execution/original/plan.json": {
        "sha256": "686e9b4c0a73735bfd5dac7e081832e5e94fc33c827be86c729a0519b2f3e652",
        "bytes": 1451833,
    },
    "execution/original/preparation.json": {
        "sha256": "00bf3198ee503f60f621613d6dbfe4c0718331f49a6f342212ff290fb096731f",
        "bytes": 388,
    },
    "execution/original/producer/report.json": {
        "sha256": "dc915089ee968411dafb97c269693613b89dbcbfecbd3e92a580405ea50cad89",
        "bytes": 7767,
    },
    "execution/original/root-launch.log": {
        "sha256": "f69991a9e1009163e04e107b7074d2fe43da577a6ea4b232682c2a3d7332261b",
        "bytes": 813,
    },
    "execution/original/source-runtime-observation.json": {
        "sha256": "d44dae393306840c26d655033afa4b73b617e7521a218c8ec87afcf610531311",
        "bytes": 96247,
    },
    "execution/original/stage-progress.json": {
        "sha256": "cb75cc7d7a44ea9af5afaa0795f132523711d27437e0e1865c83fbc62a05647f",
        "bytes": 2341,
    },
    "execution/original/swedish-cohort-terminal.json": {
        "sha256": "9baf18964647c6a0d2a66d9d6d546362f3da7daff2adb62aed6a982925b2113f",
        "bytes": 1330,
    },
    "execution/original/terminal.json": {
        "sha256": "324e7e084d6a111608b84f2863f6536ee6d03ae69cb53adcc9936390107ac02a",
        "bytes": 7398,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/check_contracts.py": {
        "sha256": "a40bab653e2e6fd1395ba4b84c15d38f7c99892d162f1e9744223cf8fd00a871",
        "bytes": 15310,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/common_runner.py": {
        "sha256": "9062395231bd7a4ec19bfe41df1587281c06e143b146119fe445a6eb0ce7ce8a",
        "bytes": 6924,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/contracts.py": {
        "sha256": "35f11e526c613aea57f0f64d10055f6bf4e687e994c1f6c231ca0af09b1a3c5f",
        "bytes": 7658,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/custody.py": {
        "sha256": "ebdfd4212f719336d382808974a0cca8e2d042208941c38aede8eeee5b5fb9eb",
        "bytes": 6798,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/declared-inputs.json": {
        "sha256": "2285665dc8cea9788440ff961069cb957f40f9240b3cfad35a6adeedf3d24911",
        "bytes": 8751,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/execute_source.py": {
        "sha256": "4c92f6c1828c889bb5c661e903758f2845706ead675496b2d6b4dd84f579b137",
        "bytes": 3839,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/independent-source-review.json": {
        "sha256": "886b93fc77b12ad6b16a350005ae56b9dc9b112fd5dd37e837eb40a6df8e0953",
        "bytes": 2290,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/metadata-input-shape.json": {
        "sha256": "9d06a928e1e9b93209d1a67a05e4fde8aa75c607ddbdc4b9821c6c00985c5df6",
        "bytes": 753,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/metadata.py": {
        "sha256": "8be89912194e5fa18b2b7c8a15834ea7e5fe40f49bbf368f4f4dc5e8cc32eaf7",
        "bytes": 18349,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/observe.py": {
        "sha256": "828f9a8d66e19962be5aaffa37ad3f83be42b4f959aafe079f7c29213380eb32",
        "bytes": 5850,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/predecessor-independent-source-review.json": {
        "sha256": "3ec08600391a04feae2b2616cdfb6c187cb44feb109f8a1fb89a7453cf8f2b7c",
        "bytes": 4069,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/predecessor-prepared-source-manifest.json": {
        "sha256": "8b7e3f52baee6f1cfdd1b654cc7d0992504ad838b910c5e798ea2c351528b08a",
        "bytes": 5976,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/predecessor-source-qualification.json": {
        "sha256": "53319462cd9b93ebe44059fda606af1766ddf813c6cd7f9e8e9d680944eb6df6",
        "bytes": 5522,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/formatted-common-construction.py": {
        "sha256": "77b7fc3ded403a7437ae45de6897fed079435ebe5b6e93c2314c640bb4f9d391",
        "bytes": 8921,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/guards.log": {
        "sha256": "981c078f4dd6e0c47b04dd89b5a6ab9dc6496bac75c0eb9c8b4bda5c66636399",
        "bytes": 1389,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/held-format.log": {
        "sha256": "b48e12b0ac584e7c68a8aeb6afced03a949cda9a80ed53778f3ac0f5adac636a",
        "bytes": 163,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/qualified-source-controls/receipt.json": {
        "sha256": "838876d3d3a04a6e556545186c4f4310da4f141474d0269a89cbde9b9fca79ea",
        "bytes": 1930,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/qualified-strict.log": {
        "sha256": "86e23024e49aa369f88aed51aebfbdc37eff6356d0a51c9cff8ac2b6950b24a9",
        "bytes": 1881,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/source-Ruff.log": {
        "sha256": "82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18",
        "bytes": 19,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/source-correspondence.json": {
        "sha256": "3ba900f170634116e722963ae53da0313ed48c8cbaa8731d0f8459188cef4585",
        "bytes": 1481,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/source-format.log": {
        "sha256": "2ce9758b9f8abd876ec3e76c589e099e8b05377b1e7ea2331e81ee80f07bdff8",
        "bytes": 26,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/source-guards.log": {
        "sha256": "60f19e9f223116a50b3dd7f05a848f4405c9ff12610e1ebfc9cee7f585f540ba",
        "bytes": 62,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/source-strict.log": {
        "sha256": "46984ca20bf69f7b14ec1fd9bd82101d56a4e109e68f016fd2a04f22481b09b3",
        "bytes": 43,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/strict.log": {
        "sha256": "3bb32ff0f3a0d9114bc12851f51745b6ca65ec054cdf5f15ad2afe1f1561eebb",
        "bytes": 284,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/preparation-recipe.json": {
        "sha256": "f0a51b01eabc5a5a857b422a1af6460c9158af75af3c1cfc6deb09ca21fb2f38",
        "bytes": 894,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/prepare.py": {
        "sha256": "252550b83a589a23c96b6f205409a12844b58d14dcc26ee314e1991303f84179",
        "bytes": 6502,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/prepared-source-manifest.json": {
        "sha256": "ee6c018f2667a41e79978abed7b08e30bf49cf8232ca0c222043a973bc46045b",
        "bytes": 6746,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/protocol.json": {
        "sha256": "e4c38c9562cf26a0e9fb2687a9e85b2485885a137cb4bad72df1eb829297dfde",
        "bytes": 3220,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/run.py": {
        "sha256": "2e30d8401899f9bda0ba0bdae27d9948775d21ed57b323de3ef4a5c4c71bfb01",
        "bytes": 8518,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/runtime.py": {
        "sha256": "403f378400b8236aecc001406aa2e7837eef20b0b3202c13e661ebe3e4d0de98",
        "bytes": 17236,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/source-observer.diff": {
        "sha256": "1306ca60cbc1c32a564be815b58f8cd93186a281e5e890663e1c700e41765339",
        "bytes": 23488,
    },
    "source-code/artifacts/science/swedish-cohort-nested-source-custody/source-qualification.json": {
        "sha256": "5f02811aa9398c02ac21ff1a4b5fed1217dfaae605df658cb6962d425091b44b",
        "bytes": 6919,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/check_contracts.py": {
        "sha256": "0c4538d7f9fece8605404decb2ed52697dcbf745f1477026f2d34c5516ca583b",
        "bytes": 11760,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/common_runner.py": {
        "sha256": "9062395231bd7a4ec19bfe41df1587281c06e143b146119fe445a6eb0ce7ce8a",
        "bytes": 6924,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/contracts.py": {
        "sha256": "616902d4a03bd0dfccd25c927465c2fa263adadd125d2b878d623bde4aede92b",
        "bytes": 7640,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/declared-inputs.json": {
        "sha256": "2285665dc8cea9788440ff961069cb957f40f9240b3cfad35a6adeedf3d24911",
        "bytes": 8751,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/execute_source.py": {
        "sha256": "d4212ecebaf682f4a3b7a82c2d5b86f5eb10963ddc00ece34334f14ed7517883",
        "bytes": 3821,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/independent-source-review.json": {
        "sha256": "3ec08600391a04feae2b2616cdfb6c187cb44feb109f8a1fb89a7453cf8f2b7c",
        "bytes": 4069,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/inherited-source-custody.json": {
        "sha256": "cdf305b3867a3cd7386c5a1252317296bbfe5a6f5eb2a8f733ac180c661009c2",
        "bytes": 2704,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/metadata.py": {
        "sha256": "d8996588abe6d4e6ec54d25a1aed9477a11670b0065f4ccab44dc7ca967febdd",
        "bytes": 17591,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/observe.py": {
        "sha256": "60d1631f4e65df30ee7f1f0b089b5221f4c8ae57defcce43f2d9127792f2f079",
        "bytes": 4944,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/preflight/CLI-and-source-custody.json": {
        "sha256": "4569803381632cbe81516dd1b0a5e46b7485e2029d5349deccc8f075c419b22f",
        "bytes": 716,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/preflight/check_tools.py": {
        "sha256": "3fec86eb3aa48b41980f12ce267f4601ab7e0f2c379f24f8611990678928c3fe",
        "bytes": 1174,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/preflight/closed-entry-configured-style.log": {
        "sha256": "a8575dd9c1fb27c2bb53d534e93fc74462b392760ff85d93556f611075b6baef",
        "bytes": 122,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/preflight/closed-entry-guards.log": {
        "sha256": "8fc436ce6f66a2f68ced8c320337acdd981422ae02f9f63e37a7fa2f775c7251",
        "bytes": 62,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/preflight/closed-entry-source-controls/receipt.json": {
        "sha256": "52772b8585777354375f2addbdf50b43e0131bd6740bf857131984f1d6a59177",
        "bytes": 1539,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/preflight/closed-entry-strict.log": {
        "sha256": "157a09cfcdfdfb5977479c5a1c08345149263a3e990a2ec976ef28aaeec9cae6",
        "bytes": 43,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/preparation-recipe.json": {
        "sha256": "4052109ceac4374799af1b0edde8305f504e84fd375b5e5427503a16c1dd2bdf",
        "bytes": 1127,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/prepare.py": {
        "sha256": "fa796beb4c77c03009963507d9dcebb01c41e17512e476e1b2d5ea434f7b1313",
        "bytes": 8235,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/prepared-source-manifest.json": {
        "sha256": "8b7e3f52baee6f1cfdd1b654cc7d0992504ad838b910c5e798ea2c351528b08a",
        "bytes": 5976,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/protocol.json": {
        "sha256": "61ebbfcf26c101ec9f52b85cf02c1363950acbd6c93bd91d5b0f3b544fedbad2",
        "bytes": 4477,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/run.py": {
        "sha256": "df448db63fc8af05e47a03321c57b161c0679c26374b212e7d6319a1e768d43a",
        "bytes": 7979,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/runtime.py": {
        "sha256": "403f378400b8236aecc001406aa2e7837eef20b0b3202c13e661ebe3e4d0de98",
        "bytes": 17236,
    },
    "source-code/artifacts/science/swedish-cohort-source-custody/source-qualification.json": {
        "sha256": "53319462cd9b93ebe44059fda606af1766ddf813c6cd7f9e8e9d680944eb6df6",
        "bytes": 5522,
    },
    "source-code/configs/ci/report-ownership.json": {
        "sha256": "8f18d4a69e6eab167a4c9559cada8ec1532d02e75124d9f024bbfadec00950d3",
        "bytes": 9617683,
    },
    "source-code/docs/report/source-relations/neotoma/swedish-cohort-availability/replay.py": {
        "sha256": "115dc864fe0688d839148ae0aed17dbca839dc29b88318466a4e628dfde33d63",
        "bytes": 20461,
    },
    "publication/report.json": {
        "sha256": "dc915089ee968411dafb97c269693613b89dbcbfecbd3e92a580405ea50cad89",
        "bytes": 7767,
    },
    "execution/corrected/independent-nested-swedish-metadata-observer.stderr": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/corrected/preparation.json": {
        "sha256": "71e5b2ba2333659ce89bba01e4c550130cdb062e2a002b9daa286a49fd2df0fb",
        "bytes": 810,
    },
    "execution/corrected/plan.json": {
        "sha256": "31dd70673048842d4d2ae84efaa6a09ffdda6f6f8e41b6966266b956fa732084",
        "bytes": 1464228,
    },
    "execution/corrected/stage-progress.json": {
        "sha256": "7f7bf2ed6643bcdf80700c50285815dbef888d4ec6436cd1588ca6cd0b10a007",
        "bytes": 1193,
    },
    "execution/corrected/swedish-metadata-observer-terminal.json": {
        "sha256": "008b666005bc4a6d3ce03ce5b0f88b7bff1f457582999eb06472debb664ea639",
        "bytes": 1659,
    },
    "execution/corrected/independent-nested-swedish-metadata-observer.stdout": {
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "execution/corrected/root-launch.log": {
        "sha256": "9c1096b4d3202f926a4cb6fc86f834612c6c4e6021751eb275d13acc23e74c51",
        "bytes": 664,
    },
    "execution/corrected/terminal.json": {
        "sha256": "54f36853e26e11953dad149910df838820693f2ee5772cff08cbbca0b7a8e8df",
        "bytes": 5425,
    },
    "execution/corrected/independent-source-review.json": {
        "sha256": "fb55d556c11a414e61f2ea0a8aa07100248958ad825e9195b0eb87c470046d3a",
        "bytes": 96091,
    },
}
EXPECTED_SCOPE: Any = {
    "new_native_retention_execution_claimed": False,
    "raw_private_metadata_redistributed": False,
    "runtime_payloads_redistributed": False,
    "new_network_acquisition_or_rights_human_acceptance": False,
    "pollen_count_observations_opened": False,
    "fresh_distinct_physical_cohort_admitted": False,
    "selected_calibrated_sample_chronology_admitted": False,
    "ecological_or_LRA_admission": False,
}
INPUT_SCOPE_COUNTS: Any = {
    "runtime_identity_only": 3481,
    "private_source_identity_only": 26,
    "retained_prior_execution_product": 12,
    "retained_execution_source": 56,
    "existing_public_relation_reference": 5,
    "retained_produced_product": 1,
}


def _require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("Swedish metadata source custody: " + reason)


def _exact(left: object, right: object) -> None:
    _require(type(left) is type(right), "metadata type differs")
    if isinstance(left, dict) and isinstance(right, dict):
        _require(left.keys() == right.keys(), "metadata fields differ")
        for key in left:
            _exact(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list):
        _require(len(left) == len(right), "metadata list membership differs")
        for a, b in zip(left, right, strict=True):
            _exact(a, b)
    else:
        _require(left == right, "metadata value differs")


def _object(value: object) -> dict[str, Any]:
    _require(
        isinstance(value, dict) and all(isinstance(k, str) for k in value),
        "JSON object required",
    )
    assert isinstance(value, dict)
    return value


def _file(root: Path, name: str) -> Path:
    try:
        return _regular_confined_file(root, name, "Swedish metadata source custody")
    except (ReportOwnershipError, OSError) as error:
        raise ReportRebuildError(
            "Swedish member missing, linked or unconfined"
        ) from error


def _json(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in items:
            _require(key not in value, "duplicate JSON key")
            value[key] = item
        return value

    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
        json.dumps(value, allow_nan=False)
        return _object(value)
    except (OSError, ValueError) as error:
        raise ReportRebuildError("Swedish JSON is invalid") from error


def _same(left: object, right: object) -> bool:
    try:
        _exact(left, right)
    except ReportRebuildError:
        return False
    return True


def validate_report(report: dict[str, Any]) -> None:
    """Validate the historical metadata result retained by the original capture."""
    _require(
        report["schema_version"] == "swedish-cohort-availability.v1",
        "Report schema differs",
    )
    inventory, screen = report["neotoma_inventory"], report["epd_metadata_screen"]
    for key, value in {
        "records": 102,
        "unique_site_ids": 99,
        "retained_site_ids": 200,
        "site_ids_outside_retained_snapshot": [],
    }.items():
        _require(
            _same(inventory[key], value),
            "Complete Neotoma metadata inventory differs: " + key,
        )
    for key, value in {
        "pangaea_metadata_search_hits": 66,
        "retained_neotoma_all_country_core_handles": 206,
        "search_hits_matching_retained_handles": 62,
        "screened_retained_country_unassigned_handles": 3,
        "unmatched_named_core_handles": 3,
        "checked_epd_final_age_swedish_events": 37,
        "checked_epd_final_age_events_matching_retained_handles": 37,
        "generic_unbound_profile_doi": "10.1594/PANGAEA.761854",
        "result": "three_unmatched_handles_three_retained_unassigned_cores_no_fresh_cohort_qualified",
    }.items():
        _require(
            _same(screen[key], value),
            "Complete all-country/EPD metadata scope differs: " + key,
        )
    _require(
        report["result"] == "no_fresh_physical_site_in_checked_metadata_surfaces",
        "No-fresh-cohort result changed",
    )
    _require(
        [row["core_handle"] for row in report["cross_archive_leads"]]
        == ["SAMBOTOT", "KLOT"],
        "Cross-archive identities differ",
    )
    _require(
        report["cross_archive_leads"][0][
            "selected_calibrated_age_model_in_checked_pangaea_metadata"
        ]
        is False,
        "A calibrated age selection was invented",
    )
    leads = screen["named_leads"]
    _require(
        [row["core_handle"] for row in leads]
        == ["ADRAN", "GARASEL", "HAKULLA5", "LEVEANIE", "NDRAKET", "VUOLEPAL"],
        "Complete ordered named leads differ",
    )
    for row in leads:
        _require(
            row["in_checked_epd_final_age_events"] is False
            and row["selected_sample_age_sequence_identified"] is False,
            "Unqualified sample-age admission",
        )
        identity = row["retained_neotoma_identity"]
        if row["core_handle"] in {"HAKULLA5", "NDRAKET", "VUOLEPAL"}:
            _require(
                identity is not None
                and identity["retained_country_code"] == "UNASSIGNED"
                and "Sweden" in identity["source_geopolitical"]
                and row["decision"]
                == "refused_as_fresh_retained_core_country_unassigned",
                "UNASSIGNED collision excluded or promoted",
            )
        else:
            _require(
                identity is None
                and row["decision"]
                == "metadata_lead_only_core_alias_and_selected_age_model_unresolved",
                "Unmatched handle incorrectly admitted",
            )
    _require(
        screen["hakulla5_chronology_reference"]["selected_sample_age_sequence_in_table"]
        is False,
        "Chronology reference promoted to sample ages",
    )


def _garasel_exposure(repository: Path) -> dict[str, Any]:
    """Read completed-processing metadata without reopening workbook observations."""
    declared = _json(_file(repository, SOURCE_DECLARATION))
    evidence = _object(declared.get("prior_processing_evidence"))
    paths = {
        "crosswalk": "data/landclim/review/rootsi-candidate-inputs/rootsi-crosswalk.csv",
        "census": "reports/science/publication-correspondence/rootsi-feature-census/report.json",
    }
    _exact(set(evidence), set(paths))
    sources = {}
    for role, relative in paths.items():
        pin = _object(evidence[role])
        _exact(set(pin), {"path", "sha256"})
        _exact(pin["path"], relative)
        source = _file(repository, relative)
        _exact(hashlib.sha256(source.read_bytes()).hexdigest(), pin["sha256"])
        sources[role] = source
    with sources["crosswalk"].open(encoding="utf-8", newline="") as stream:
        identities = [
            row
            for row in csv.DictReader(stream)
            if row.get("rootsi_sequence_label_raw", "").upper() == "GARASEL"
        ]
    _require(len(identities) == 1, "One GARASEL crosswalk identity required")
    identity = identities[0]
    census = _json(sources["census"])
    _exact(census.get("canonical_crosswalk"), evidence["crosswalk"])
    _exact(census.get("schema_version"), "rootsi-cached-feature-census.v1")
    _exact(census.get("source_commit"), "6bc07eb8e6b1599739473ff1478f45cb68fa9333")
    workbooks = census.get("workbooks")
    _require(isinstance(workbooks, list), "Completed workbook metadata required")
    assert isinstance(workbooks, list)
    entries = [
        _object(row)
        for row in workbooks
        if _object(row).get("archive_member") == "rootsi/GARASEL.xls"
    ]
    _require(len(entries) == 1, "One completed GARASEL workbook required")
    entry = entries[0]
    origin = "decoded cached values; literal/formula origin unavailable"
    for key, expected in {
        "archive_member": "rootsi/GARASEL.xls",
        "bytes": 19968,
        "metadata_source_locator": "rootsi/Metadata table_SWE_climate.xlsx!25",
        "status": "computed",
        "sheet": "Sheet1",
        "value_origin": origin,
    }.items():
        _exact(entry.get(key), expected)
    _exact(identity.get("typed_workbook_member"), entry["archive_member"])
    _exact(identity.get("typed_workbook_bytes"), str(entry["bytes"]))
    _exact(identity.get("typed_workbook_sha256"), entry.get("sha256"))
    _exact(identity.get("rootsi_source_locator"), entry["metadata_source_locator"])
    workbook_sha = entry.get("sha256")
    _require(
        isinstance(workbook_sha, str)
        and len(workbook_sha) == 64
        and all(char in "0123456789abcdef" for char in workbook_sha),
        "Workbook data identity required",
    )
    return {
        "status": "prior_numeric_source_processing_recorded",
        "workbook_member": entry["archive_member"],
        "workbook_sha256": workbook_sha,
        "workbook_bytes": entry["bytes"],
        "sheet": entry["sheet"],
        "metadata_source_locator": entry["metadata_source_locator"],
        "site_name_raw": identity.get("rootsi_site_name_raw"),
        "latitude_raw": identity.get("rootsi_latitude_raw"),
        "longitude_raw": identity.get("rootsi_longitude_raw"),
        "completed_census_source_commit": census["source_commit"],
        "evidence_inputs": evidence,
        "processing_scope": origin,
        "fitting_or_tuning_exposure": "not_established_by_these_records",
        "target_measurement_values_opened_by_this_check": False,
    }


def validate_current_report(
    repository: Path, historical: dict[str, Any], current: dict[str, Any]
) -> None:
    """Permit only the metadata-supported stricter refusal beyond captured history."""
    validate_report(historical)
    _exact(set(current), set(historical))
    _require(
        isinstance(current["scope"], str) and bool(current["scope"].strip()),
        "Current scope wording required",
    )
    historical_screen = _object(historical["epd_metadata_screen"])
    current_screen = _object(current["epd_metadata_screen"])
    _exact(set(current_screen), set(historical_screen))
    old_leads, new_leads = (
        historical_screen["named_leads"],
        current_screen["named_leads"],
    )
    _require(isinstance(new_leads, list), "Current lead population required")
    assert isinstance(new_leads, list)
    _exact(len(new_leads), len(old_leads))
    normalized_leads = []
    exposure = _garasel_exposure(repository)
    for old, new in zip(old_leads, new_leads, strict=True):
        new = _object(new)
        if old["core_handle"] == "GARASEL":
            expected = {
                **old,
                "decision": "refused_as_untouched_prior_numeric_source_processing",
                "prior_source_processing": exposure,
                "untouched_confirmation_eligible": False,
                "untouched_status_restored_by_age_or_rights_repair": False,
            }
            _exact(new, expected)
        else:
            _exact(new, old)
        normalized_leads.append(old)
    normalized = {
        **current,
        "scope": historical["scope"],
        "epd_metadata_screen": {
            **current_screen,
            "named_leads": normalized_leads,
        },
    }
    _exact(normalized, historical)


def _stages(plan: dict[str, Any], common: dict[str, Any], exits: list[int]) -> None:
    _exact(len(common["stages"]), len(exits))
    _exact(len(plan["stages"]), len(exits))
    for declared, actual, code in zip(
        plan["stages"], common["stages"], exits, strict=True
    ):
        for key in ("id", "argv", "timeout_seconds", "must_succeed"):
            _exact(actual[key], declared[key])
        _exact(actual["actual_exit"], code)
        _exact(actual["timed_out"], False)
    _exact(common["before_pin_mismatches"], [])
    _exact(common["after_pin_mismatches"], [])
    _exact(common["absent_input_paths_unchanged"], True)
    _exact(common["canonical_before"], plan["canonical_identity"])
    _exact(common["canonical_after"], plan["canonical_identity"])


def validate_native_records(
    original: dict[str, Any],
    failed: dict[str, Any],
    failed_outer: dict[str, Any],
    current: dict[str, Any],
    common: dict[str, Any],
    outer: dict[str, Any],
    review: dict[str, Any],
    runtime: dict[str, Any],
) -> None:
    """Keep original source0/observer1 separate from the corrected observer-only0."""
    old_sha = EXPECTED_MEMBERS["execution/original/plan.json"]["sha256"]
    new_sha = EXPECTED_MEMBERS["execution/corrected/plan.json"]["sha256"]
    for row in (
        original,
        failed,
        failed_outer,
        current,
        common,
        outer,
        review,
        runtime,
    ):
        _exact(row["candidate"], ORIGINAL_CANDIDATE)
    _stages(original, failed, [0, 1])
    _stages(current, common, [0])
    _exact(failed["actual_exit"], 1)
    _exact(failed_outer["actual_exit"], 1)
    _exact(failed["plan_sha256"], old_sha)
    _exact(failed_outer["plan_sha256"], old_sha)
    _exact(failed_outer["actual_native_stage_exits"], [0, 1])
    _exact(failed_outer["tracked_byte_checker_exit"], None)
    _exact(failed_outer["independent_review"], None)
    _exact(len(original["input_pins"]), 3537)
    _exact(len({p["path"] for p in original["input_pins"]}), 3537)
    _exact(len(current["input_pins"]), 3581)
    _exact(len({p["path"] for p in current["input_pins"]}), 3581)
    _exact(original["declared_owner"]["owner_id"], OWNER)
    _exact(original["declared_owner"]["role"], "unresolved")
    _exact(
        [r["id"] for r in original["stages"]],
        [
            "maintained-swedish-cohort-source",
            "independent-swedish-cohort-metadata-observer",
        ],
    )
    _exact(
        [r["id"] for r in current["stages"]],
        ["independent-nested-swedish-metadata-observer"],
    )
    for key, name in (
        ("original_plan", "plan.json"),
        ("original_common", "terminal.json"),
        ("original_outer", "swedish-cohort-terminal.json"),
    ):
        _exact(
            current[key]["sha256"],
            EXPECTED_MEMBERS["execution/original/" + name]["sha256"],
        )
        _exact(
            review[key]["sha256"],
            EXPECTED_MEMBERS["execution/original/" + name]["sha256"],
        )
    _exact(common["actual_exit"], 0)
    _exact(outer["actual_exit"], 0)
    _exact(common["plan_sha256"], new_sha)
    _exact(outer["plan_sha256"], new_sha)
    _exact(outer["actual_native_stage_exits"], [0])
    _exact(outer["tracked_byte_checker_exit"], 0)
    for terminal, code in ((failed_outer, 1), (outer, 0)):
        _exact(terminal["common_actual_exit"], code)
        _exact(terminal["outer_timed_out"], False)
        for key in (
            "completed_whole_wall_bound_pass",
            "framework_membership_unchanged",
            "absent_paths_unchanged",
            "memory_bound_pass",
            "storage_bound_pass",
        ):
            _exact(terminal[key], True)
    for row in (current, outer, review):
        _exact(row["original_whole_actual_exit"], 1)
        _exact(row["retained_producer_native_exit"], 0)
    for row in (outer, review):
        _exact(row["producer_rerun"], False)
    _exact(review["actual_exit"], 0)
    _exact(review["plan"]["sha256"], new_sha)
    _exact(review["tracked_byte_checker_exit"], 0)
    _exact(review["complete_independent_metadata_join_typed_and_bytes_exact"], True)
    for key, value in (
        ("private_metadata_members", 26),
        ("metadata_dataset_count", 102),
        ("metadata_site_count", 99),
        ("all_country_core_handles", 206),
        ("metadata_title_population", 66),
        ("retained_handle_hits", 62),
        ("unmatched_named", 3),
        ("generic_unbound", 1),
        ("checked_final_age_events", 37),
        ("fresh_distinct_cohort_admitted", False),
        ("selected_sample_age_sequence_admitted", False),
        ("acquisition_rights_human_ecological_or_LRA_admitted", False),
        ("raw_private_bytes_redistributed", False),
    ):
        _exact(review[key], value)
    _exact(
        outer["independent_review"]["sha256"],
        EXPECTED_MEMBERS["execution/corrected/independent-source-review.json"][
            "sha256"
        ],
    )
    _exact(
        review["generated"]["sha256"],
        EXPECTED_MEMBERS["publication/report.json"]["sha256"],
    )
    _exact(review["canonical"], original["historical_report"])
    _exact(
        review["source_runtime"]["sha256"],
        EXPECTED_MEMBERS["execution/original/source-runtime-observation.json"][
            "sha256"
        ],
    )
    _exact(runtime["plan"]["sha256"], old_sha)
    _exact(runtime["source"], original["maintained_source"])
    _exact(runtime["executed_source_argv"], original["maintained_source_argv"])
    _exact(runtime["source_exit"], 0)
    _exact(runtime["metadata_exit"], 0)
    _exact(runtime["metadata_error"], None)
    _exact(runtime["interpreter_flags"], ["-I", "-S", "-B"])
    _require(
        type(runtime["before"]["pid"]) is int and runtime["before"]["pid"] > 0,
        "Actual source PID required",
    )
    _exact(runtime["before"]["pid"], runtime["after"]["pid"])
    for snapshots, pins in (
        ((runtime["before"], runtime["after"]), original["input_pins"]),
        ((review["observer_before"], review["observer_after"]), current["input_pins"]),
    ):
        names = {r["path"] for r in pins}
        for snapshot in snapshots:
            for origin in snapshot["namespace"]:
                _require(
                    origin["file"] is None or origin["file"] in names,
                    "Unpinned source/stdlib origin",
                )
            for image in snapshot["native_images"]:
                _require(
                    image in names
                    or image.startswith(
                        (
                            "/usr/lib/",
                            "/System/Library/",
                            "/System/Volumes/Preboot/Cryptexes/OS/usr/lib/",
                            "/System/Volumes/Preboot/Cryptexes/OS/System/Library/",
                        )
                    ),
                    "Unpinned native image",
                )


def _validate_original_owner(owners: list[JsonObject]) -> None:
    """Require the complete original unresolved contract, including unchanged criteria."""
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    _require(len(selected) == 1, "One exact original owner required")
    _exact(selected[0], ORIGINAL_OWNER)
    owned_paths = ORIGINAL_OWNER["paths"]
    assert isinstance(owned_paths, list)
    for other in owners:
        if other is selected[0]:
            continue
        paths = other.get("paths", [])
        _require(
            isinstance(paths, list)
            and all(isinstance(path, str) for path in paths)
            and not set(owned_paths).intersection(paths),
            "Another owner overlaps current evidence paths",
        )


def _capture_required(repository: Path) -> bool:
    """A published correction keeps its existing physical evidence mandatory."""
    capture = repository / CAPTURE
    present = bool(capture.exists() or capture.is_symlink())
    witness = repository / CORRECTION_WITNESS
    _require(
        not any(node.is_symlink() for node in (witness, *witness.parents)),
        "Original-acceptance witness ancestry alias",
    )
    if witness.exists() or witness.is_symlink():
        path = _file(repository, CORRECTION_WITNESS)
        _exact(hashlib.sha256(path.read_bytes()).hexdigest(), CORRECTION_WITNESS_SHA256)
        _require(present, "Published partial evidence requires its exact capture")
    return present


DETACHED_SOURCE_MEMBERS = frozenset(
    [
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/check_contracts.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/common_runner.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/contracts.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/custody.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/execute_source.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/metadata.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/observe.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/preflight/formatted-common-construction.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/prepare.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/run.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/runtime.py",
        "source-code/artifacts/science/swedish-cohort-nested-source-custody/source-observer.diff",
        "source-code/artifacts/science/swedish-cohort-source-custody/check_contracts.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/common_runner.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/contracts.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/execute_source.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/metadata.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/observe.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/preflight/check_tools.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/prepare.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/run.py",
        "source-code/artifacts/science/swedish-cohort-source-custody/runtime.py",
        "source-code/configs/ci/report-ownership.json",
        "source-code/docs/report/source-relations/neotoma/swedish-cohort-availability/replay.py",
    ]
)


def _validate_source_members(repository: Path, prefix: str) -> None:
    """Validate original identities once and detach only exact maintained source."""
    detached = validate_capsule(repository, prefix, EXPECTED_MEMBERS)
    _exact(sorted(detached), sorted(DETACHED_SOURCE_MEMBERS))


def validated_swedish_cohort_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Validate partial current evidence while original owner acceptance stays unresolved."""
    present = _capture_required(repository)
    selected = [row for row in owners if row.get("owner_id") == OWNER]
    if not selected and not present:
        return (), {}
    _validate_original_owner(owners)
    if not present:
        return (), {}
    path = _file(repository, CAPTURE)
    _exact(hashlib.sha256(path.read_bytes()).hexdigest(), CAPTURE_SHA256)
    packet = _json(path)
    for key, value in (
        ("schema_version", "swedish-cohort-source-capture.v1"),
        ("owner_id", OWNER),
        ("publication_paths", [REPORT]),
        ("original_input_count", 3537),
        ("observer_input_count", 3581),
        ("member_count", 78),
        ("members", EXPECTED_MEMBERS),
        ("scope", EXPECTED_SCOPE),
        ("observer_input_scope_counts", INPUT_SCOPE_COUNTS),
    ):
        _exact(packet[key], value)
    _exact(
        packet["original_source_execution"],
        {
            "candidate": ORIGINAL_CANDIDATE,
            "plan_sha256": EXPECTED_MEMBERS["execution/original/plan.json"]["sha256"],
            "native_stage_exits": [0, 1],
            "whole_actual_exit": 1,
        },
    )
    _exact(
        packet["corrected_observer_execution"],
        {
            "candidate": ORIGINAL_CANDIDATE,
            "plan_sha256": EXPECTED_MEMBERS["execution/corrected/plan.json"]["sha256"],
            "native_stage_exits": [0],
            "whole_actual_exit": 0,
        },
    )
    _exact(
        packet["joint_completed_roles"],
        {
            "retained_producer_native_exit": 0,
            "corrected_independent_metadata_observer_exit": 0,
            "corrected_tracked_byte_checker_exit": 0,
            "producer_rerun": False,
        },
    )
    prefix = path.parent.relative_to(repository).as_posix()
    _validate_source_members(repository, prefix)

    def record(name: str) -> dict[str, Any]:
        return _json(_file(repository, prefix + "/execution/" + name))

    records = [
        record(n)
        for n in (
            "original/plan.json",
            "original/terminal.json",
            "original/swedish-cohort-terminal.json",
            "corrected/plan.json",
            "corrected/terminal.json",
            "corrected/swedish-metadata-observer-terminal.json",
            "corrected/independent-source-review.json",
            "original/source-runtime-observation.json",
        )
    ]
    validate_native_records(*records)
    original, current = records[0], records[3]
    _exact(
        [r["original"] for r in packet["original_input_custody"]],
        original["input_pins"],
    )
    _exact(
        [r["original"] for r in packet["observer_input_custody"]], current["input_pins"]
    )
    count: dict[str, int] = {}
    for row in packet["observer_input_custody"]:
        count[row["scope"]] = count.get(row["scope"], 0) + 1
        if row["member"] is not None:
            _exact(
                EXPECTED_MEMBERS[row["member"]],
                {k: row["original"][k] for k in ("sha256", "bytes")},
            )
        elif row["scope"] == "existing_public_relation_reference":
            relative = (
                Path(row["original"]["path"])
                .relative_to(Path(original["repository"]))
                .as_posix()
            )
            source = _file(repository, relative)
            payload = source.read_bytes()
            if relative == SOURCE_DECLARATION:
                # Only the independently checked exposure addendum may extend
                # this historical declaration of original metadata identities.
                declared = _json(source)
                _require(
                    "prior_processing_evidence" in declared,
                    "Current exposure declaration required",
                )
                del declared["prior_processing_evidence"]
                payload = (
                    json.dumps(declared, ensure_ascii=False, indent=2) + "\n"
                ).encode("utf-8")
            _exact(
                {
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "bytes": len(payload),
                },
                {k: row["original"][k] for k in ("sha256", "bytes")},
            )
        else:
            _require(
                row["scope"]
                in {"private_source_identity_only", "runtime_identity_only"},
                "Undeclared source omission",
            )
            _require(
                not Path(row["original"]["path"]).is_relative_to(
                    Path(original["repository"])
                ),
                "First-party source cannot be omitted",
            )
    _exact(count, INPUT_SCOPE_COUNTS)
    publication = _file(repository, REPORT)
    historical = _file(repository, prefix + "/publication/report.json")
    validate_current_report(
        repository,
        _json(historical),
        _json(publication),
    )
    current_bytes = publication.read_bytes()
    wanted = {
        "sha256": hashlib.sha256(current_bytes).hexdigest(),
        "bytes": len(current_bytes),
    }
    entry = tracked_by_path.get(REPORT)
    _require(entry is not None, "Tracked report required")
    assert entry is not None
    for actual, expected in (
        (entry.path, REPORT.removeprefix("docs/report/")),
        (entry.kind, "file"),
        (entry.sha256, wanted["sha256"]),
        (entry.canonical_sha256, wanted["sha256"]),
        (entry.size, wanted["bytes"]),
    ):
        _exact(actual, expected)
    return (), {
        "selected_retained_entries": 0,
        "original_owner_acceptance_discharged": False,
        "owner_remains_unresolved": True,
        "original_acceptance_criterion": ORIGINAL_OWNER["verification"],
        "owner_id": OWNER,
        "capture_sha256": CAPTURE_SHA256,
        "original_source_whole_exit": 1,
        "original_source_stages": [0, 1],
        "corrected_observer_whole_exit": 0,
        "corrected_observer_stages": [0],
        "joint_producer_and_independent_exit": [0, 0],
        "paths": [entry.path],
        "scope": dict(EXPECTED_SCOPE),
    }
