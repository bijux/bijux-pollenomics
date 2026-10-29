"""Package exact cached wheel payloads into new offline transport archives."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    confined_output,
    create_root,
    digest,
    json_value,
    require,
    validate_payload,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json_value(args.plan)
    destination = confined_output(Path(plan["output"]) / "wheels", absent=True)
    create_root(destination)
    manifest = []
    for expected in plan["selected_payloads"]:
        actual = validate_payload(expected)
        require(actual == expected, "Cached input authority changed after preparation")
        archive = destination / expected["wheel_filename"]
        with zipfile.ZipFile(
            archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6
        ) as wheel:
            for row in expected["members"]:
                source = Path(row["path"])
                require(
                    digest(source) == row["sha256"]
                    and source.stat().st_size == row["bytes"],
                    "Cached payload changed",
                )
                info = zipfile.ZipInfo(row["name"], (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (row["mode"] | 0o100000) << 16
                with source.open("rb") as incoming, wheel.open(info, "w") as outgoing:
                    while chunk := incoming.read(1024 * 1024):
                        outgoing.write(chunk)
        with zipfile.ZipFile(archive) as wheel:
            require(
                wheel.namelist() == [r["name"] for r in expected["members"]],
                "Transport member order or membership differs",
            )
            for row in expected["members"]:
                with wheel.open(row["name"]) as stream:
                    hasher = hashlib.sha256()
                    while chunk := stream.read(1024 * 1024):
                        hasher.update(chunk)
                    h = hasher.hexdigest()
                require(
                    h == row["sha256"]
                    and wheel.getinfo(row["name"]).file_size == row["bytes"],
                    "Transport changed original wheel payload",
                )
        manifest.append(
            {
                "name": expected["name"],
                "version": expected["version"],
                "path": str(archive),
                "sha256": digest(archive),
                "bytes": archive.stat().st_size,
                "original_cached_RECORD_sha256": expected["record_sha256"],
                "original_METADATA_sha256": expected["metadata_sha256"],
                "original_WHEEL_sha256": expected["wheel_sha256"],
                "complete_original_WHEEL_tags": expected["complete_wheel_tags"],
                "original_archive_zip_identity_claimed": False,
            }
        )
    requirements = destination / "requirements.txt"
    with requirements.open("x") as stream:
        for row in manifest:
            stream.write(
                Path(row["path"]).as_uri() + " --hash=sha256:" + row["sha256"] + "\n"
            )
    write_json(
        destination / "transport-manifest.json",
        {
            "schema_version": "offline-source-runtime-wheel-transport.v1",
            "distributions": manifest,
            "requirements_sha256": digest(requirements),
            "original_cached_payload_metadata_and_RECORD_preserved": True,
            "transport_zip_SHA_is_new_not_original_download_receipt": True,
            "network_requests": 0,
            "source_builds": 0,
        },
    )


if __name__ == "__main__":
    main()
