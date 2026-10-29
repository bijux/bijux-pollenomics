"""Bind actual portable assembly and observer receipts without reopening historical inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from ....ownership import _regular_confined_file
from ....retained_source import SourceCapsule, validated_descriptor
from ....retained_source.objects import GitSourceMember, read_blob
from ...presentation_source_roles import HISTORICAL_RENDERING_SOURCES
from ...source_roles.documentation import _documented_source_matches
from .contracts import require, strict_equal

PROOF_IDENTITIES: dict[str, dict[str, Any]] = {
    "plan": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-sweden-retained-source-publication/plan.json",
        "sha256": "eb6ea543166a950038caebbef12836ea1be84367c799620a01f932ee406dd2dc",
        "bytes": 20893579,
    },
    "inner": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-sweden-retained-source-publication/sweden-country-semantic-terminal.json",
        "sha256": "162d25ba953097345843ea5067677bf7c33aca7b06fee3118b375b8e49c6f108",
        "bytes": 4845,
    },
    "outer": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-sweden-retained-source-publication/sweden-country-semantic-launch-terminal.json",
        "sha256": "2dc47a2cf61a290ce4ee33fa14a69b5c110505e7beeb779971f34e52227e20ad",
        "bytes": 2604,
    },
    "assembly": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-sweden-retained-source-publication/assembly-receipt.json",
        "sha256": "35433a4008b507899b6df3d133f5ef56a93668cf44f345acdfc13961a73ece2a",
        "bytes": 967,
    },
    "observer": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-sweden-retained-source-publication/independent-portable-country-review.json",
        "sha256": "03aa48f5a45bd25a52c389a0aa0b01eda2a8a0541f3043a064b9625b3c23d88d",
        "bytes": 823252,
    },
}
CONTROLLER_IDENTITIES: dict[str, dict[str, Any]] = {
    "assemble.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/assemble.py",
        "sha256": "1a2483264f8903e23caec0df2a3ce200035180a322f3f5afc97be5683d67bc9b",
        "bytes": 3882,
    },
    "call_evidence.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/call_evidence.py",
        "sha256": "226e5b6aaec5a778b4a6882faf1ff4f8e28efa443efbbdd23959020fc2872504",
        "bytes": 6737,
    },
    "callable_identity.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/callable_identity.py",
        "sha256": "76ab1a23fce193ae459dbda6b809b626e9861fc179dfd92d3231ef46c9f8cf8c",
        "bytes": 3846,
    },
    "check_admission.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/check_admission.py",
        "sha256": "6578009a4ddef2d20de7a4e23d9c22c330c0da39829c47e82516f3c5520ab39f",
        "bytes": 5479,
    },
    "check_controls.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/check_controls.py",
        "sha256": "003e776b38a01205b691f4c08b7d3e77e9e7f8d18a25d7686c599bfb0d800697",
        "bytes": 24004,
    },
    "check_style.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/check_style.py",
        "sha256": "d55d2bb9bd00cab656d05f4b92009a9b9b91489a75a117bb54a3070a0f275a44",
        "bytes": 945,
    },
    "clock_contract.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/clock_contract.py",
        "sha256": "8ee36763fba54234aadf65d71693c1241516134b843bba400c66c6f512888ad1",
        "bytes": 2853,
    },
    "contracts.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/contracts.py",
        "sha256": "cd31a96b26eb1fb113b821ae435f4117e86cad5de849157873301b3ed213e6ab",
        "bytes": 9101,
    },
    "country-authority.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/country-authority.json",
        "sha256": "b2d202e0cb62088cc9e754effcb8a10db9f2436aae8b1e25ad4429ff7fe8f1c5",
        "bytes": 3917,
    },
    "data_roles.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/data_roles.py",
        "sha256": "5517ae3d3b58a4e6632f49d2c875bb250d589c0b94a20cae343ef2a6f76d0385",
        "bytes": 7060,
    },
    "declared-inputs.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/declared-inputs.json",
        "sha256": "381384938e27b78b3caeb64675eecc5b32734cb5f9cfac27ecfa438b9c273364",
        "bytes": 27023,
    },
    "entry.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/entry.py",
        "sha256": "431bea6e0d45a0a01e466bbf179692c06cbb82bc182145cba721b77615c37160",
        "bytes": 5174,
    },
    "generated-source-omission.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/generated-source-omission.json",
        "sha256": "09055e3ce3b1ee6c6475c15d6d45c421cb64cd5360c0d8d00392b22a87787624",
        "bytes": 1163,
    },
    "launch.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/launch.py",
        "sha256": "2275bc2bfedc99c6b2ba33c5bee59360a4e70abce7d9b6bdd328547c4f5c795b",
        "bytes": 6380,
    },
    "members.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/members.py",
        "sha256": "531c0d1b08084823634029deef054c92e7044e7de37a41972e82a5123a4beb19",
        "bytes": 8948,
    },
    "observe.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/observe.py",
        "sha256": "0188b37c2a2eca67595d9650879747a3f2df881981719fc8c48abd711af5d5eb",
        "bytes": 3546,
    },
    "packet.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/packet.py",
        "sha256": "8c64c8f1fef7916adb0a2b01f08b29f7f7a2d476397fcefca200e410f6eea5d1",
        "bytes": 11101,
    },
    "preflight/sealed-controls.stderr": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/preflight/sealed-controls.stderr",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "preflight/sealed-controls.stdout": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/preflight/sealed-controls.stdout",
        "sha256": "da3fdd7a1c2d4767ff7541aeb2068c4705ffc587ac95d188b53e9b59561409ad",
        "bytes": 37,
    },
    "preflight/sealed-format.stderr": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/preflight/sealed-format.stderr",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "preflight/sealed-format.stdout": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/preflight/sealed-format.stdout",
        "sha256": "19c2e88957b1c3c58a4a7ed24fc196278e5a0541d48dc9f317a488583e59f74e",
        "bytes": 27,
    },
    "preflight/sealed-lint.stderr": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/preflight/sealed-lint.stderr",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "preflight/sealed-lint.stdout": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/preflight/sealed-lint.stdout",
        "sha256": "82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18",
        "bytes": 19,
    },
    "preflight/sealed-strict.stderr": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/preflight/sealed-strict.stderr",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "bytes": 0,
    },
    "preflight/sealed-strict.stdout": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/preflight/sealed-strict.stdout",
        "sha256": "fa935e779fe5886f2480e415c7e46616bdedad407f9da1cca28e7d341d95f4d7",
        "bytes": 44,
    },
    "preflight/source-controls.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/preflight/source-controls.json",
        "sha256": "4149743f00cbdfdcfd4f48a12b361e61b1c0e59de8b6ab5a578bd4970af31a3a",
        "bytes": 2138,
    },
    "prepare.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/prepare.py",
        "sha256": "cc88b28b7b36f6ac500d2babab41358b0c3f5222a8716b0df0796b55fc681504",
        "bytes": 7093,
    },
    "protocol.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/protocol.json",
        "sha256": "2e5c647c5dfc7eba6c59247ccadfaa1252824d59b752d68860cdc0c33e060107",
        "bytes": 4661,
    },
    "publication.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/publication.py",
        "sha256": "8efd774bb5ee52378ebb22f940bbe45c43f00b62780c6099d68293db2b62ec53",
        "bytes": 16838,
    },
    "recipe.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/recipe.json",
        "sha256": "5c1ab53a7dbbaaf43662e3604f465e417fa51390f26d352a1cbe5dcf8cd07ca5",
        "bytes": 1397,
    },
    "retained.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/retained.py",
        "sha256": "8d1c624976a5185cb8163a69035ba329dcfc93d6b605f6dfbc0ad2166af47991",
        "bytes": 9346,
    },
    "run.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/run.py",
        "sha256": "26e8e2c4381f5991e75fae37d07b9d69c875de7afc1c2df18ad9629bda53acdb",
        "bytes": 8173,
    },
    "runtime_contracts.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/runtime_contracts.py",
        "sha256": "40ca33563c15a3555ef0fb338dc4899f89f6d06168d7593b47b89ba30b6a9c28",
        "bytes": 16576,
    },
    "runtime_evidence.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/runtime_evidence.py",
        "sha256": "7dbd49f652e54cbcfccbf64ca6455e4c8ab8a638f40eff7018cda95bfe2ed9b1",
        "bytes": 3697,
    },
    "saved-authority.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/saved-authority.json",
        "sha256": "2e30ecdd2e64581afb30f8ad1c9990511c553db14c8a8626ca853ccdaed0bced",
        "bytes": 4361,
    },
    "source-correspondence.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/source-correspondence.json",
        "sha256": "31269ae757d4668cfce57ba74acbf57a76d88ff738d2d20ac6e51cda557db1bc",
        "bytes": 5746,
    },
    "source-design.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/source-design.json",
        "sha256": "18c81342605415e91c1f45960cdb6adbd8f57481be2d3e8779b3f838db8f0a75",
        "bytes": 1646,
    },
    "source-qualification.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/source-qualification.json",
        "sha256": "6db90eddf8c2bb39ac32c05611864ecea209fb75d61e294022e556cc2c3720c8",
        "bytes": 9842,
    },
    "source_admission.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/source_admission.py",
        "sha256": "8097ce28768fdcbc9edf4cfc1276be444f1a946ced9483f715de170ae52fa049",
        "bytes": 2788,
    },
    "source_inputs.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/source_inputs.py",
        "sha256": "6e899c7a1323dbb4d0d6e7080aab22a68d66e2563cc86280e0214fbe86f4732f",
        "bytes": 6994,
    },
    "source_projection.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/source_projection.py",
        "sha256": "fc94f84dd02447d2590738a7e2eca8e6f36db917dae99b20054e317b060e4edf",
        "bytes": 6937,
    },
    "source_runtime.py": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/source_runtime.py",
        "sha256": "e472bc68683c73af0155597f288f3d7475923332c67e80ade9b76b6c23ecdd32",
        "bytes": 8062,
    },
    "prepared-source-manifest.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/prepared-source-manifest.json",
        "sha256": "b8741579061bd856303277e07f07c2a9cd78cfb87092ac09ecb640affa058cd7",
        "bytes": 10487,
    },
    "independent-source-review.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/sweden-country-retained-source-custody/independent-source-review.json",
        "sha256": "0b4516770785748d9629196f5d1cba27372b07738f56307ac0df01af1aa97f29",
        "bytes": 8360,
    },
}
BASE = "data/source-custody/country-reports/sweden/current-retention/"


def exact_file(
    repository: Path,
    relative: str,
    identity: dict[str, Any],
    maximum: int = 128 * 1024**2,
) -> bytes:
    """Read the exact ordinary retained file within the declared root."""
    name = PurePosixPath(relative)
    require(
        name.as_posix() == relative
        and not name.is_absolute()
        and ".." not in name.parts
        and "\\" not in relative
        and bool(name.parts),
        "Confined retained metadata path required",
    )
    path = repository / relative
    require(
        repository.is_absolute()
        and repository == repository.resolve()
        and not any(node.is_symlink() for node in (path, *path.parents))
        and path.is_file()
        and path.stat().st_nlink == 1
        and type(identity["bytes"]) is int
        and 0 <= identity["bytes"] <= maximum
        and path.stat().st_size == identity["bytes"],
        "Physical bounded retained metadata required",
    )
    raw = path.read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == identity["sha256"],
        "Exact retained metadata buffer differs",
    )
    return raw


def object_buffer(raw: bytes) -> dict[str, Any]:
    """Decode retained JSON bytes while preserving unique member names."""

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        require(
            len(rows) == len({name for name, _ in rows}),
            "Duplicate retained metadata key",
        )
        return dict(rows)

    def refuse(value: str) -> None:
        raise ValueError("Nonfinite retained metadata: " + value)

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=refuse)
    require(type(result) is dict, "Retained metadata object required")
    assert isinstance(result, dict)
    return result


RETENTION_SOURCE_MEMBERS = {
    "sha256": "ffdfc5c864590c96f61f39250e6abc7fa11abb0c902f94f9ace7fb9ff189d263",
    "bytes": 7913,
}

DETACHED_SOURCE_MEMBERS = frozenset(
    [
        "controller/assemble.py",
        "controller/call_evidence.py",
        "controller/callable_identity.py",
        "controller/check_admission.py",
        "controller/check_controls.py",
        "controller/check_style.py",
        "controller/clock_contract.py",
        "controller/contracts.py",
        "controller/data_roles.py",
        "controller/entry.py",
        "controller/launch.py",
        "controller/members.py",
        "controller/observe.py",
        "controller/packet.py",
        "controller/prepare.py",
        "controller/publication.py",
        "controller/retained.py",
        "controller/run.py",
        "controller/runtime_contracts.py",
        "controller/runtime_evidence.py",
        "controller/source_admission.py",
        "controller/source_inputs.py",
        "controller/source_projection.py",
        "controller/source_runtime.py",
    ]
)


def _retention_sources(repository: Path, filenames: dict[str, str]) -> SourceCapsule:
    """Authenticate the explicitly derived catalogue against unchanged original identities."""
    expected_members = {
        filenames[name]: {key: identity[key] for key in ("sha256", "bytes")}
        for name, identity in PROOF_IDENTITIES.items()
    }
    expected_members.update(
        {
            "controller/" + name: {key: identity[key] for key in ("sha256", "bytes")}
            for name, identity in CONTROLLER_IDENTITIES.items()
        }
    )
    expected_members = dict(sorted(expected_members.items()))
    source_members = object_buffer(
        exact_file(repository, BASE + "source-members.json", RETENTION_SOURCE_MEMBERS)
    )
    require(
        strict_equal(source_members["members"], expected_members)
        and source_members["schema_version"]
        == "sweden-retained-proof-source-members.v1",
        "Exact original portable proof/member catalogue differs",
    )
    resolver = validated_descriptor(repository, BASE.rstrip("/"), expected_members)
    require(
        resolver.descriptor.capture_name == "source-members.json"
        and resolver.detached == DETACHED_SOURCE_MEMBERS,
        "Exact portable proof source detachment differs",
    )
    return resolver


def validate_metadata(
    repository: Path,
    capture: dict[str, Any],
    capture_identity: dict[str, Any],
    saved_plan: dict[str, Any],
) -> dict[str, Any]:
    """Join metadata to fixed proof identities and recorded native history."""
    require(
        set(PROOF_IDENTITIES) == {"plan", "inner", "outer", "assembly", "observer"}
        and {"prepared-source-manifest.json", "independent-source-review.json"}
        <= set(CONTROLLER_IDENTITIES),
        "No actual portable metadata authority has been assembled",
    )
    filenames = {
        "plan": "plan.json",
        "inner": "terminal.json",
        "outer": "launch-terminal.json",
        "assembly": "assembly.json",
        "observer": "independent-review.json",
    }
    resolver = _retention_sources(repository, filenames)
    documents = {
        name: object_buffer(resolver.read_source(filenames[name]))
        for name in PROOF_IDENTITIES
    }
    controller = {
        name: resolver.read_source("controller/" + name)
        for name in CONTROLLER_IDENTITIES
    }
    manifest = object_buffer(controller["prepared-source-manifest.json"])
    approval = object_buffer(controller["independent-source-review.json"])
    return qualify_retention(
        capture,
        capture_identity,
        saved_plan,
        documents,
        PROOF_IDENTITIES,
        CONTROLLER_IDENTITIES,
        manifest,
        approval,
    )


def qualify_retention(
    capture: dict[str, Any],
    capture_identity: dict[str, Any],
    saved_plan: dict[str, Any],
    documents: dict[str, Any],
    proof_identities: dict[str, dict[str, Any]],
    controller_identities: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
    approval: dict[str, Any],
) -> dict[str, Any]:
    """Check retained identities against recorded execution correspondence."""
    require(
        set(proof_identities) == {"plan", "inner", "outer", "assembly", "observer"}
        and {"prepared-source-manifest.json", "independent-source-review.json"}
        <= set(controller_identities),
        "Complete actual portable metadata proof roles required",
    )
    source_identity = controller_identities["prepared-source-manifest.json"]
    require(
        manifest["source_only"] is True
        and approval["approved"] is True
        and approval["source_manifest_sha256"] == source_identity["sha256"],
        "Exact portable controller source approval differs",
    )
    source_root = Path(source_identity["path"]).parent
    expected = {
        Path(row["path"]).relative_to(source_root).as_posix(): row
        for row in manifest["files"]
    }
    require(
        len(expected) == len(manifest["files"])
        and strict_equal(
            {
                name: row
                for name, row in controller_identities.items()
                if name
                not in {
                    "prepared-source-manifest.json",
                    "independent-source-review.json",
                }
            },
            expected,
        ),
        "Complete portable controller source membership differs",
    )
    plan = documents["plan"]
    inner = documents["inner"]
    outer = documents["outer"]
    assembly = documents["assembly"]
    observer = documents["observer"]
    for name, schema in {
        "inner": "sweden-country-semantic-terminal.v1",
        "outer": "sweden-country-semantic-owned-child-watchdog-terminal.v1",
        "assembly": "sweden-portable-returned-country-source-assembly.v1",
        "observer": "sweden-portable-returned-country-independent-review.v1",
    }.items():
        require(
            documents[name]["schema_version"] == schema,
            "Actual portable receipt schema differs",
        )
    digest = proof_identities["plan"]["sha256"]
    require(
        digest == capture["metadata_registered_plan_sha256"],
        "Capture is not bound to actual registered metadata plan",
    )
    inputs = {row["path"]: row for row in plan["input_pins"]}
    require(
        len(inputs) == len(plan["input_pins"])
        and all(inputs.get(row["path"]) == row for row in saved_plan["input_pins"])
        and all(
            inputs.get(row["path"]) == row for row in controller_identities.values()
        ),
        "Complete original saved inputs or portable controller roles lost",
    )
    resources = {
        "overall_timeout_seconds": 480,
        "outer_timeout_seconds": 540,
        "declared_memory_bytes": 4 * 1024**3,
        "declared_storage_bytes": 1024**3,
    }
    require(
        strict_equal(plan["resources"], resources),
        "Portable metadata resource contract differs",
    )
    for receipt in (inner, outer, assembly, observer):
        require(
            type(receipt["actual_exit"]) is int
            and receipt["actual_exit"] == 0
            and receipt["candidate"] == plan["candidate"],
            "Portable metadata did not complete natively",
        )
    require(
        plan["candidate"] == capture["metadata_candidate"]
        and inner["plan_sha256"]
        == outer["plan_sha256"]
        == assembly["registered_plan_sha256"]
        == observer["registered_plan_sha256"]
        == digest
        and outer["inner_terminal"] == proof_identities["inner"]
        and observer["assembly"] == proof_identities["assembly"],
        "Portable registered-plan/receipt joins differ",
    )
    require(
        inner["exception"] is None
        and inner["after_custody_error"] is None
        and inner["completed_whole_wall_bound_pass"] is True
        and outer["completed_outer_wall_bound_pass"] is True
        and outer["registered_plan_unchanged"] is True
        and outer["child_timed_out"] is False
        and type(outer["child_native_exit"]) is int
        and outer["child_native_exit"] == 0
        and all(
            receipt[key] is True
            for receipt in (inner, outer)
            for key in ("memory_bound_pass", "inclusive_storage_bound_pass")
        ),
        "Portable completed resources, native status or custody failed",
    )
    python = plan["qualified_source_runtime"]["lexical_python"]
    expected_stages = [
        {
            "id": name,
            "action": action,
            "timeout_seconds": 180,
            "argv": [
                python,
                "-I",
                "-B",
                str(source_root / "entry.py"),
                action,
                "--plan",
                proof_identities["plan"]["path"],
            ],
        }
        for name, action in (
            ("portable-returned-country-source-assembly", "assembler"),
            ("independent-portable-country-source-observer", "observer"),
        )
    ]
    require(
        strict_equal(plan["stages"], expected_stages) and len(inner["stages"]) == 2,
        "Only exact two metadata stages admitted",
    )
    for actual, expected_stage in zip(inner["stages"], expected_stages, strict=True):
        require(
            strict_equal({key: actual[key] for key in expected_stage}, expected_stage)
            and type(actual["actual_exit"]) is int
            and actual["actual_exit"] == 0
            and actual["timed_out"] is False,
            "Actual portable metadata stage differs",
        )
    for receipt in (assembly, observer):
        require(
            receipt["capture"] == capture_identity
            and receipt["country_receipt_sha256"]
            == capture["native_witness"]["current_receipt_sha256"]
            and receipt["private_runtime_bytecode_bodies_published"] is False
            and receipt["country_API_normalizer_model_R_or_HTTP_repeated"] is False,
            "Portable packet or privacy scope changed",
        )
    require(
        strict_equal(inner["resources"], resources)
        and strict_equal(outer["resources"], resources),
        "Actual portable receipt resource declarations differ",
    )
    for receipt in (assembly, observer):
        require(
            type(receipt["public_members"]) is int
            and receipt["public_members"] == len(capture["members"])
            and type(receipt["public_payload_bytes"]) is int
            and receipt["public_payload_bytes"]
            == sum(row["bytes"] for row in capture["members"].values()),
            "Complete public payload denominators differ",
        )
    require(
        strict_equal(
            observer["complete_original_ordered_input_counts"],
            {
                name: len(rows)
                for name, rows in capture["identity_only_roles"][
                    "ordered_original_input_roles"
                ].items()
            },
        ),
        "All original ordered input denominator roles must remain complete",
    )
    require(
        type(assembly["original_controller_actual_exit"]) is int
        and assembly["original_controller_actual_exit"] == 1
        and type(assembly["original_whole_actual_exit"]) is int
        and assembly["original_whole_actual_exit"] == 1
        and assembly["country_call_returned_normally"] is True
        and type(assembly["saved_observer_actual_exit"]) is int
        and assembly["saved_observer_actual_exit"] == 0
        and type(assembly["saved_whole_actual_exit"]) is int
        and assembly["saved_whole_actual_exit"] == 0,
        "Portable assembly relabeled original failed history",
    )
    require(
        observer["captured_code_imported_or_executed"] is False
        and observer["complete_public_namespace_and_all_member_bytes_verified"] is True
        and strict_equal(observer["native_witness"], capture["native_witness"]),
        "Portable source observer scope differs",
    )
    return {
        "registered_plan_sha256": digest,
        "candidate": plan["candidate"],
        "assembly_actual_exit": 0,
        "independent_actual_exit": 0,
        "whole_actual_exit": 0,
        "all_original_saved_input_identities_bound": len(saved_plan["input_pins"]),
        "source_manifest_sha256": source_identity["sha256"],
    }


def validate_recorded_source_contracts(
    repository: Path, rows: list[dict[str, Any]], resolver: SourceCapsule
) -> dict[str, Any]:
    """Authenticate old producer bytes and keep current scientific defaults strict."""
    require(
        repository.is_absolute()
        and repository == repository.resolve()
        and resolver.repository == repository
        and type(rows) is list
        and len(rows) == 51
        and all(type(row) is dict for row in rows),
        "Complete canonical Sweden source contract population required",
    )
    require(
        all(set(row) == {"path", "sha256", "bytes"} for row in rows)
        and all(type(row["path"]) is str for row in rows)
        and len({row["path"] for row in rows}) == 51,
        "Recorded Sweden source contract roles differ",
    )
    exact = 0
    documented: list[str] = []
    rendered: list[str] = []
    resolver.fresh()
    for row in rows:
        name = row["path"]
        relative = PurePosixPath(name)
        require(
            relative.as_posix() == name
            and not relative.is_absolute()
            and ".." not in relative.parts
            and "\\" not in name
            and bool(relative.parts)
            and type(row["bytes"]) is int
            and 0 <= row["bytes"] <= 128 * 1024**2
            and type(row["sha256"]) is str
            and len(row["sha256"]) == 64
            and all(value in "0123456789abcdef" for value in row["sha256"]),
            "Confined typed Sweden source contract required",
        )
        logical = "members/" + row["sha256"]
        identity = {key: row[key] for key in ("sha256", "bytes")}
        require(
            strict_equal(resolver.descriptor.members.get(logical), identity)
            and [
                path
                for group in resolver.descriptor.groups
                for member, path in group["resolved_paths"]
                if member == logical
            ]
            == [name],
            "Recorded Sweden source member/path binding differs",
        )
        captured = resolver.read_source(logical)
        require(
            len(captured) == row["bytes"]
            and hashlib.sha256(captured).hexdigest() == row["sha256"],
            "Original Sweden producer source bytes differ",
        )
        current = _regular_confined_file(repository, name, "current Sweden source")
        require(
            current.stat().st_nlink == 1 and current.stat().st_size <= 128 * 1024**2,
            "Current Sweden source must be bounded and single-link",
        )
        value = current.read_bytes()
        if (
            len(value) == row["bytes"]
            and hashlib.sha256(value).hexdigest() == row["sha256"]
        ):
            exact += 1
        elif name in HISTORICAL_RENDERING_SOURCES:
            rendered.append(name)
        elif _documented_source_matches(name, captured, value):
            documented.append(name)
        else:
            require(
                False, "Current Sweden scientific contract differs without a named role"
            )
    resolver.fresh()
    return {
        "original_source_contracts_authenticated": 51,
        "current_default_exact_sources": exact,
        "exact_named_documentation_sources": documented,
        "historical_renderer_sources": rendered,
        "current_browser_or_native_equivalence_claimed": False,
    }


HISTORICAL_READER_PATH = "docs/report/countries/sweden/land-use-replay/README.md"
HISTORICAL_READER_REVISION = "d029760ddf2f6853d07e9ac14091df8f041ecbb4"
HISTORICAL_READER_BLOB = "508a1d3e260e1da95483f664485909a14f2533b4"
HISTORICAL_READER_BYTES = 6879


def validate_historical_reader(repository: Path, expected_sha256: str) -> None:
    """Bind the old publication body without restoring a first-party snapshot."""
    body = read_blob(
        repository,
        GitSourceMember(
            HISTORICAL_READER_PATH,
            HISTORICAL_READER_PATH,
            HISTORICAL_READER_REVISION,
            HISTORICAL_READER_BLOB,
            expected_sha256,
            HISTORICAL_READER_BYTES,
        ),
    )
    require(
        len(body) == HISTORICAL_READER_BYTES
        and hashlib.sha256(body).hexdigest() == expected_sha256,
        "Historical Sweden reader body differs",
    )
