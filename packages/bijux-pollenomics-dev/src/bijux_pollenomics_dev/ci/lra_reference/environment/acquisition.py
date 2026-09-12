"""Acquire only exact source-lock URLs, with byte verification before cache admission."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from urllib.request import urlopen

from ..contracts import ReferenceRefusal, load_lock
from ..paths import local_path
from ..sources import sha256, verify_archive, verify_sources


def acquire(
    *, lock_path: Path, source_cache: Path, repository: Path, output: Path
) -> dict[str, object]:
    lock_path, source_cache, repository, output = (
        local_path(path) for path in (lock_path, source_cache, repository, output)
    )
    lock = load_lock(lock_path)
    if (
        output.exists()
        or output.is_relative_to(source_cache)
        or source_cache.is_relative_to(output)
    ):
        raise ReferenceRefusal(
            "Acquisition cache and new receipt directory must be disjoint"
        )
    output.mkdir(parents=True)
    source_cache.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    receipt: dict[str, object] = {
        "schema_version": "lra-r-acquisition.v1",
        "status": "incomplete",
        "lock_sha256": sha256(lock_path),
        "sources": records,
    }
    try:
        for source in lock.sources:
            destination = local_path(source_cache / source.archive_filename)
            if destination.exists():
                if (
                    destination.stat().st_size != source.byte_count
                    or sha256(destination) != source.sha256
                ):
                    raise ReferenceRefusal(
                        "Existing source cache entry has unexpected bytes"
                    )
                records.append(
                    {
                        "package": source.package,
                        "version": source.version,
                        "sha256": source.sha256,
                        "byte_count": source.byte_count,
                        "url": source.url,
                        "disposition": "verified_existing",
                    }
                )
                continue
            with tempfile.NamedTemporaryFile(
                dir=source_cache, prefix=".source-", delete=False
            ) as temporary:
                path = Path(temporary.name)
                started = time.monotonic()
                size = 0
                digest = hashlib.sha256()
                with urlopen(source.url, timeout=15) as response:
                    if not response.url.startswith("https://cran.r-project.org/"):
                        raise ReferenceRefusal(
                            "Source redirect left the authoritative CRAN host"
                        )
                    while True:
                        if time.monotonic() - started > 180:
                            raise ReferenceRefusal(
                                "Exact source acquisition exceeded deadline"
                            )
                        chunk = response.read1(min(65536, source.byte_count + 1 - size))
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > source.byte_count:
                            raise ReferenceRefusal(
                                "Downloaded source exceeds locked byte count"
                            )
                        digest.update(chunk)
                        temporary.write(chunk)
                temporary.flush()
                os.fsync(temporary.fileno())
            if size != source.byte_count or digest.hexdigest() != source.sha256:
                raise ReferenceRefusal(
                    "Downloaded source bytes disagree with the source lock"
                )
            verify_archive(path, source.package, source.version)
            os.link(path, destination)
            path.unlink()
            records.append(
                {
                    "package": source.package,
                    "version": source.version,
                    "sha256": source.sha256,
                    "byte_count": size,
                    "url": source.url,
                    "disposition": "acquired_exact",
                }
            )
            (output / "progress.json").write_text(json.dumps(receipt, indent=2) + "\n")
        verify_sources(lock, source_cache, repository)
        if sha256(lock_path) != receipt["lock_sha256"]:
            raise ReferenceRefusal("Source lock changed during acquisition")
        receipt["status"] = "passed"
    except BaseException as error:
        receipt.update(status="failed", error=type(error).__name__ + ": " + str(error))
        raise
    finally:
        (output / "report.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt
