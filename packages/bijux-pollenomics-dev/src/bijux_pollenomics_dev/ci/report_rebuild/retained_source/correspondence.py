"""Bind the exact reviewed source-reader adapters without admitting numerical drift."""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

from ..contracts import JsonObject, ReportRebuildError
from ..ownership import _regular_confined_file
from .index import read_source_path
from .objects import environment, git_executable

# Only these existing current-source assertions include their own custody readers.
# The exact pairs are reviewed IO changes; they do not authorize arbitrary source edits.
SOURCE_PAIRS: dict[str, dict[str, JsonObject]] = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/atlas_source_views.py": {
        "current": {
            "bytes": 20078,
            "sha256": "46a00520485a18dc27c01e11052dfb3255a2298782122856063393194aed256e",
        },
        "historical": {
            "bytes": 20205,
            "sha256": "024fe24976b3590c8c8a40e76f774ac60cb3effdb5ba1ade88dc40379f6565fe",
        },
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/linux_r_reference.py": {
        "current": {
            "bytes": 12844,
            "sha256": "dcfa93e2e821246093310824616d2b7ed61d36d76f8091cbe5a07d157dd266b7",
        },
        "historical": {
            "bytes": 12720,
            "sha256": "68024f8768c32d69ad897f7d91c41b57bec78399a36e52f5624bc550a7c7a40f",
        },
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/sample_chronology_capture.py": {
        "current": {
            "bytes": 22073,
            "sha256": "2b4884885eea045109562567e50cfb37f88a963e6deee470d026ec9e6a6cb5b8",
        },
        "historical": {
            "bytes": 22265,
            "sha256": "b271061a3b04f4a41baf53e98076747e8e5620ab64cd7e146fac26c691e34fe5",
        },
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/source_layout_adoption.py": {
        "current": {
            "bytes": 7960,
            "sha256": "0bfb911212b801ed5cf09c56fd25a945ac23660f1e05629eec5fd2582d0a8b6c",
        },
        "historical": {
            "bytes": 7080,
            "sha256": "f0c340faca10b48ec3b9036659ffec26e37bc36719605a98eea7acec2e404272",
        },
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/annulus_capture.py": {
        "historical": {
            "sha256": "47af109200a23537843078d241628273f08270e30150c34e1bbfdf76ffd0603b",
            "bytes": 10937,
        },
        "current": {
            "sha256": "f59fa57a686f22c9362e6dfa424614c402d7086d8f13597faf094b9458df6871",
            "bytes": 12944,
        },
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/capture.py": {
        "historical": {
            "sha256": "873b8a968223ca88f8235f999ad803d7f0b66c36dc503850e69478a23506849b",
            "bytes": 6846,
        },
        "current": {
            "sha256": "3e1e2999877e6183cd530641ce6cb6b105561fd922ea3021b0cfc5ea57c501a4",
            "bytes": 8853,
        },
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/count_domain_capture.py": {
        "historical": {
            "sha256": "256ba71ff27976534da4b4c7a5fc496270a4e59c9a2af5100f078cccff8cc761",
            "bytes": 23947,
        },
        "current": {
            "sha256": "bd485cda6a289c509df942a103c2e576ed873ff267c205841e3cd59b2fa9ade7",
            "bytes": 25830,
        },
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/diagnostics.py": {
        "historical": {
            "sha256": "ca844dca8751054f17055c99c227c8a54084981da745e8c13e3071d2093e911e",
            "bytes": 12514,
        },
        "current": {
            "sha256": "befd87e2ea44125ea72a748d5c1c855af2c38fa08fda2b16ed8659938f583203",
            "bytes": 12652,
        },
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/diagnostics_verification.py": {
        "historical": {
            "sha256": "c8abeb8902e199073e61e9860535605c17c9d882205729562bc058d9a01c51bd",
            "bytes": 15067,
        },
        "current": {
            "sha256": "b00c19581443c615598b4ad05f4413f70507e450cb25990a1a92b6e4cb94950e",
            "bytes": 15612,
        },
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/finite_covariance_capture.py": {
        "historical": {
            "sha256": "59b4770fbf38efe60633b540edf5925d09be56fe1c1c2795d6cf0af206edefee",
            "bytes": 9194,
        },
        "current": {
            "sha256": "b8addfcef4b4c4bc52604a65a885d95802cf9eca641989197514c9b2ddd3898e",
            "bytes": 11852,
        },
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/retained_reference/identity.py": {
        "historical": {
            "sha256": "bab7252e9e0b8059a58aa486555163b1cbde321bf1b870da719b23a3253f44bf",
            "bytes": 4875,
        },
        "current": {
            "sha256": "6f6f57ec79258c1a64ec0fdf2ada1d1abe0ed0e43e48243cd14fcdd18c85343a",
            "bytes": 7580,
        },
    },
}


def validated_transport_correspondence(
    repository: Path, historical: JsonObject, retained_source: Path
) -> JsonObject:
    """Authenticate original bytes and the exact current committed reader adapter."""
    name = historical.get("path")
    if not isinstance(name, str) or name not in SOURCE_PAIRS:
        raise ReportRebuildError("No reviewed retained-source transport correspondence")
    pair = SOURCE_PAIRS[name]
    if (
        historical != {"path": name, **pair["historical"]}
        or type(historical.get("bytes")) is not int
    ):
        raise ReportRebuildError("Original projected source identity differs")
    old = read_source_path(repository, retained_source)
    current = _regular_confined_file(
        repository, name, "current source transport adapter"
    )
    new = current.read_bytes()
    for body, expected in ((old, pair["historical"]), (new, pair["current"])):
        if (
            len(body) != expected["bytes"]
            or hashlib.sha256(body).hexdigest() != expected["sha256"]
        ):
            raise ReportRebuildError("Reviewed source transport pair differs")
    try:
        committed = subprocess.check_output(
            [
                str(git_executable()),
                "--no-replace-objects",
                "-C",
                str(repository),
                "show",
                "HEAD:" + name,
            ],
            env=environment(),
            timeout=20,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ReportRebuildError(
            "Source transport adapter has no committed identity"
        ) from error
    if committed != new:
        raise ReportRebuildError("Source transport adapter differs from current Git")
    return {
        "path": name,
        "historical": pair["historical"],
        "current": pair["current"],
        "classification": "exact-retained-source-reader-transport-correspondence",
        "numerical_reexecution_claimed": False,
        "whole_current_tree_equivalence_claimed": False,
        "scope": "Exact reviewed custody IO only: original source members are authenticated through reachable canonical Git blobs instead of duplicated package files. Scientific predicates, original native outcomes and publication admission remain unchanged.",
    }
