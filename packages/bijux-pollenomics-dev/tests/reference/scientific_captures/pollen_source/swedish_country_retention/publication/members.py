"""Build and validate a closed content-addressed public country-source packet."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from contracts import require, strict_equal
from packet import public_members
from publication import REF_NAMES, qualify_saved

MAX_CAPTURE = 128 * 1024**2
MAX_PAYLOAD = 512 * 1024**2
MAX_MEMBERS = 8192


def encoded(value: object) -> bytes:
    return (
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode()


def specification(
    authority: dict[str, Any], candidate: str, registered_plan_sha: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    require(
        type(candidate) is str
        and len(candidate) == 40
        and all(c in "0123456789abcdef" for c in candidate),
        "Literal metadata candidate required",
    )
    require(
        type(registered_plan_sha) is str
        and len(registered_plan_sha) == 64
        and all(c in "0123456789abcdef" for c in registered_plan_sha),
        "Registered metadata plan digest required",
    )
    witness = qualify_saved(
        authority["documents"],
        authority["identities"],
        authority["original_references"],
    )
    roles, omissions = public_members(authority)
    require(len(roles) <= MAX_MEMBERS, "Public role count exceeds ceiling")
    members: dict[str, dict[str, Any]] = {}
    payloads: dict[str, dict[str, Any]] = {}
    logical = {}
    rendered_roles = []
    for row in roles:
        identity = row["source_identity"]
        name = "members/" + identity["sha256"]
        expected = {key: identity[key] for key in ("sha256", "bytes")}
        require(
            name not in members or strict_equal(members[name], expected),
            "Content identity collision",
        )
        members[name] = expected
        payloads.setdefault(
            name, {"member": name, "source_identity": deepcopy(identity)}
        )
        logical[row["logical_name"]] = name
        rendered_roles.append({**deepcopy(row), "member": name})
    require(
        sum(row["bytes"] for row in members.values()) <= MAX_PAYLOAD,
        "Public payload bytes exceed ceiling",
    )
    capture = {
        "schema_version": "sweden-returned-country-retained-source-capture.v1",
        "metadata_candidate": candidate,
        "metadata_registered_plan_sha256": registered_plan_sha,
        "members": dict(sorted(members.items())),
        "references": {
            name: logical["references/" + name + ".json"] for name in REF_NAMES
        },
        "reference_original_identities": deepcopy(authority["identities"]),
        "original_country_references": deepcopy(authority["original_references"]),
        "public_roles": rendered_roles,
        "identity_only_roles": omissions,
        "native_witness": witness,
        "private_runtime_or_bytecode_bodies_published": False,
        "country_API_normalizer_model_R_or_HTTP_repeated": False,
    }
    require(
        len(encoded(capture)) <= MAX_CAPTURE, "Capture metadata bytes exceed ceiling"
    )
    return capture, [payloads[name] for name in sorted(payloads)]


def namespace(root: Path, members: dict[str, Any]) -> None:
    require(
        root.is_absolute()
        and root == root.resolve()
        and not any(p.is_symlink() for p in (root, *root.parents)),
        "Physical packet root required",
    )
    require(
        type(members) is dict and 0 < len(members) <= MAX_MEMBERS,
        "Bounded complete member dictionary required",
    )
    expected = {"capture.json"}
    for name, row in members.items():
        logical = PurePosixPath(name)
        require(
            type(name) is str
            and len(logical.parts) == 2
            and logical.parts[0] == "members"
            and type(row["sha256"]) is str
            and len(row["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in row["sha256"])
            and name == "members/" + row["sha256"]
            and type(row["bytes"]) is int
            and 0 <= row["bytes"] <= MAX_PAYLOAD,
            "Unsafe member name or identity",
        )
        expected.add(name)
    require(
        sum(row["bytes"] for row in members.values()) <= MAX_PAYLOAD,
        "Payload ceiling exceeded",
    )
    files = set()
    directories = set()
    pending = [root]
    while pending:
        directory = pending.pop()
        for path in directory.iterdir():
            require(
                not path.is_symlink() and (path.is_file() or path.is_dir()),
                "Packet alias/special member refused",
            )
            name = path.relative_to(root).as_posix()
            require(
                name in expected or name == "members",
                "Unknown public packet namespace entry",
            )
            if path.is_dir():
                require(name == "members", "Unexpected packet directory")
                directories.add(name)
                pending.append(path)
            else:
                require(
                    path.stat().st_nlink == 1,
                    "Hardlinked packet metadata/member refused",
                )
                if name == "capture.json":
                    require(
                        path.stat().st_size <= MAX_CAPTURE,
                        "Capture metadata ceiling exceeded",
                    )
                files.add(name)
    require(
        files == expected and directories == {"members"},
        "Complete packet namespace differs",
    )
    for name, row in members.items():
        path = root / name
        require(
            path.stat().st_nlink == 1 and path.stat().st_size == row["bytes"],
            "Packet member size/hardlink differs",
        )
        with path.open("rb") as stream:
            checksum = hashlib.file_digest(stream, "sha256").hexdigest()
        require(checksum == row["sha256"], "Original packet member bytes differ")


def load_reference(root: Path, name: str, capture: dict[str, Any]) -> Any:
    member = capture["references"][name]
    require(member in capture["members"], "Reference absent from public members")
    expected = capture["reference_original_identities"][name]
    require(
        strict_equal(
            capture["members"][member],
            {key: expected[key] for key in ("sha256", "bytes")},
        ),
        "Reference/member identity differs",
    )
    path = root / member
    require(
        type(expected["bytes"]) is int
        and 0 <= expected["bytes"] <= MAX_CAPTURE
        and path.stat().st_size == expected["bytes"],
        "Bounded metadata member required",
    )
    raw = path.read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == expected["sha256"],
        "Same-buffer metadata reference differs",
    )

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        require(
            len(rows) == len({key for key, _ in rows}),
            "Duplicate retained metadata key",
        )
        return dict(rows)

    def refused(value: str) -> None:
        raise ValueError("Nonfinite retained metadata: " + value)

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=refused)
    require(
        type(result) is dict or name == "country-progress" and type(result) is list,
        "Retained reference role differs",
    )
    return result


def validate_capture(root: Path, capture: dict[str, Any]) -> dict[str, Any]:
    require(
        capture["schema_version"]
        == "sweden-returned-country-retained-source-capture.v1",
        "Capture schema differs",
    )
    namespace(root, capture["members"])
    require(
        (root / "capture.json").read_bytes() == encoded(capture),
        "Exact capture buffer differs",
    )
    require(
        set(capture["references"])
        == set(capture["reference_original_identities"])
        == set(REF_NAMES),
        "Complete reference mapping required",
    )
    documents = {name: load_reference(root, name, capture) for name in REF_NAMES}
    authority = {
        "documents": documents,
        "identities": capture["reference_original_identities"],
        "original_references": capture["original_country_references"],
    }
    rebuilt, _ = specification(
        authority,
        capture["metadata_candidate"],
        capture["metadata_registered_plan_sha256"],
    )
    require(
        strict_equal(rebuilt, capture),
        "Complete packet/omission/native witness reconstruction differs",
    )
    return deepcopy(rebuilt["native_witness"])


def descriptor(
    capture: dict[str, Any], payloads: list[dict[str, Any]]
) -> dict[str, Any]:
    raw = encoded(capture)
    return {
        "capture_with_registered_digest_placeholder": {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        },
        "payloads": deepcopy(payloads),
    }
