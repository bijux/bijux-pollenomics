"""Keep first-party source identities outside retained scientific data."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path, PurePosixPath
import re
import subprocess

import pytest

REPOSITORY = Path(__file__).resolve().parents[5]
HISTORICAL_BUILD_RESOURCE = (
    "data/method-certification/source-locked-linux-r/reference-bundle/"
    "generated-sources/packages/bijux-pollenomics-lra/src/"
    "bijux_pollenomics_lra/_build_version.py"
)

EXECUTION_REFERENCE_PREFIX = (
    "packages/bijux-pollenomics-dev/tests/reference/scientific_captures/"
)
FROZEN_ADNA_AUTHORITY_IDENTITIES = frozenset(
    (
        (
            "data/adna/current-contract-authority/authority-index.json",
            "5315dd03e32a5d6cf79ba04700ab522c16ca55f6",
        ),
        (
            "data/adna/current-contract-authority/payloads/003ec3c3360a01cad862fbe3751c5a88eb947cf68b12a3e78ee927b34348cf31",
            "319617e33d6be0ddcad989c5428e876041e3f1c9",
        ),
        (
            "data/adna/current-contract-authority/payloads/0ff101326442a842f3a102beb99cc43c0ed435ab85b4616819bedc29c7f42896",
            "9857996327cb502dbf838acf770544dcc4e27f76",
        ),
        (
            "data/adna/current-contract-authority/payloads/2495da8f5a6ebc80c4275101e134017584cc5e8bf40e7e33fa564cbdd06df634",
            "d15445cff07e97a1f22ba7c8469f9471a7aa2a88",
        ),
        (
            "data/adna/current-contract-authority/payloads/2743dc07e289d822ba2433a572dba2bc7f87875f1756d1eed5e1a98347fda291",
            "38505317468be5e4b717d61031cae2a7b7376ca5",
        ),
        (
            "data/adna/current-contract-authority/payloads/2f760e5d40918dc8d9e543d9f9e1c4452c9232bdd95d8b55733822c9845ddc8c",
            "f0aee52365e21e2310df2be798b39041ffb586d5",
        ),
        (
            "data/adna/current-contract-authority/payloads/31a497ffa62cb26b106a30a612fa1b2335101442d4caa0955984af7f4981bc6c",
            "29eea51638e4c002a760919265d1cc9d74a72fe7",
        ),
        (
            "data/adna/current-contract-authority/payloads/3696408e9a3cc4277bdc408dc9cf77658d82407e5d6bbe91c7447b802943c064",
            "79e4467fa8250b0d3b7862e48ef168f6869f9067",
        ),
        (
            "data/adna/current-contract-authority/payloads/43e960d74e5ad02bd47edbd3690028605a95d52bcc6b7aa3e48408b8edeac496",
            "6438bac433a77edd159b015b30d5a736589baaff",
        ),
        (
            "data/adna/current-contract-authority/payloads/44c1b7def3202e3e14554d0d9de077f8dda2704bce999e4a16294fca6e6ebb8e",
            "025459347151961c0fd95d29c6414a134fa96232",
        ),
        (
            "data/adna/current-contract-authority/payloads/45258238c6529de971416f85b8fe6ecfbdf14b089c7606dcb137754382267447",
            "bb7d5ab2caa4fddd6a871b056cef9c836ff096cd",
        ),
        (
            "data/adna/current-contract-authority/payloads/50e3e807b6f64a29ccfd8f9ff508536738553f5a96f029bcf3adac54785f2e06",
            "901fa294422a1a4e365384961db134afa5c1a11c",
        ),
        (
            "data/adna/current-contract-authority/payloads/51f02e5e23b0286a07556534f07f2e4c6c8f409c36c71801e67fcb4cfb6d60a4",
            "bd811d0f6eacbaab8739b5780d4b7c2d3a14203e",
        ),
        (
            "data/adna/current-contract-authority/payloads/53be364e15ffb9b9c3c0ae91dd53258fc3a96311c1868f0e7631c57d78106fce",
            "01438cd1111b5f8bbd43103e7afad7e0bc0b9905",
        ),
        (
            "data/adna/current-contract-authority/payloads/5906f80ea8dfeaaa1e42b871809374a008ff8969c45cb59d3eba4badc409cb39",
            "ea0fb2bf24700bbb0ec4a3b38fb8631ca100e566",
        ),
        (
            "data/adna/current-contract-authority/payloads/5a30b0d40362271fb39a81868fa5a1702d18db67788db77fd8f872c409688a8c",
            "0bf613b25dac5437c1867de0b7887301b6b0b0e9",
        ),
        (
            "data/adna/current-contract-authority/payloads/5a5ec33b00b76889a2e088dc1fae68a90c07c67f8b5f3fb67193d04a84179206",
            "c8dfc0278886de10c498172d24a47a1ab986381e",
        ),
        (
            "data/adna/current-contract-authority/payloads/637fa5fddefb919b375f22a3048772dbe1535875523e8648d3be360946dc3fcd",
            "05d7b4298780d2809a34c71944fb1acd84d807e0",
        ),
        (
            "data/adna/current-contract-authority/payloads/66544e677c34cf2e2eb69eaf68cf25c6aee33bc6ea87c9ee818e5e7698c23d1d",
            "b04d07a58f62888db14ec730e677d040b0531096",
        ),
        (
            "data/adna/current-contract-authority/payloads/67dc29a576b914fe20606e4b2f516eb83e31bfd0581952b5b95e5f401535096e",
            "1f5fa6de0f773d2628e7a28cbaceef6abb617f6c",
        ),
        (
            "data/adna/current-contract-authority/payloads/6970c0731bc7a118ab1128bab95e0600a01a7d776bb5e04d578d2eb96d727b46",
            "dc29a75918a990806bd486b185f311d7717fcfcc",
        ),
        (
            "data/adna/current-contract-authority/payloads/6c66551db36a8351e0a2cd1347103d1e35756a05d7e98e105d1839d0d2306d42",
            "3cf7a000f7ecf41a7cfe710c6f70c4b2566a77f8",
        ),
        (
            "data/adna/current-contract-authority/payloads/6dfec7d70e7751e08a34637f4f0b8747356e7f9d746500c412ab09426fb10095",
            "25add794b6d5f00a5dd743ba26da6f8689bdd507",
        ),
        (
            "data/adna/current-contract-authority/payloads/6e591a709802303cac45d6d6b40954bf465ab48a4739321e382ca501d290653e",
            "28d2c8331e7d59159b9a8bea0f3d5e663edeb5bb",
        ),
        (
            "data/adna/current-contract-authority/payloads/7af5b2d87920e74b06fa38718fc230d8f1a0eb858e2cbb1713bc6909858d8f4b",
            "949fbce799c54ef051785a8ea850eb90a3771450",
        ),
        (
            "data/adna/current-contract-authority/payloads/7e33edb4bb0ad869985e3e1e7f694c15f3989b3cffd07624194e3d8e6f56fd72",
            "e32d7d40ce2cafcfe2fe164dc4afd9f84dd82305",
        ),
        (
            "data/adna/current-contract-authority/payloads/7e5846baf2ec7345576a951cbed943c129f62be10d38463a26bc1fae00dcc59f",
            "4baaa74e760bdd5d80c89a6f202504f19a9207ba",
        ),
        (
            "data/adna/current-contract-authority/payloads/8228fcc5ce46d42d01caf3cd941f4e9c5f2bcc372bb5b147a2f0572d2dd675a8",
            "f6784b584b00e1ead95409381271a914c93dd88f",
        ),
        (
            "data/adna/current-contract-authority/payloads/82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18",
            "1f5f344d054fae10f39140fb7199c99321d9190a",
        ),
        (
            "data/adna/current-contract-authority/payloads/8b40c958ee3c4ffe06e6c81f48664cb1a9cbc6ec356bd660eca1b3298a5d4a7d",
            "13524ca3765d6f510b233eced89347c985e5cc98",
        ),
        (
            "data/adna/current-contract-authority/payloads/8b83eb5851c30d24dc5061814d06694cf056cd7b39c5cab1d7724bdeada0825e",
            "d603866557ad01106280ae1bf8ed90837c16f5c0",
        ),
        (
            "data/adna/current-contract-authority/payloads/8b88f6d12bd312c1b024b66d07a7f7619a68482ac4d64e475759b1823199faa5",
            "01dae786023aebb7a359b3776c1a9485e8d9ac2a",
        ),
        (
            "data/adna/current-contract-authority/payloads/8ca05d2040684744eca0f7a2ed6b9733cb67f9368845457a028dd73d59cf00da",
            "04dcd96656f3cdea432898ac80879565802cd44e",
        ),
        (
            "data/adna/current-contract-authority/payloads/8f31491face0d9007dc9fcc2eade529504995f0a881174c44ee63a67f14ff916",
            "ac3eef6662ce2ba78f2993978b3ac2d96f4df96b",
        ),
        (
            "data/adna/current-contract-authority/payloads/971548a474a07c0203316024bf590fcb0ff23bfcd490bb5a86b517fda7bb7596",
            "071766f33549c39dc07584aa8e9fa63ca844922b",
        ),
        (
            "data/adna/current-contract-authority/payloads/9750f9559a1b62198d7e1e2ed47034d67cc6fdfb4888137af9ce3d154df8ab59",
            "fc2af86ed1c8d576a254fe96341e236247267614",
        ),
        (
            "data/adna/current-contract-authority/payloads/9bfd8859b090e2f9746b5d9eea95175b43b3828dd6843e28784e9400b3f787a2",
            "5405017ae3ec92373848a6b08e55358a77530a51",
        ),
        (
            "data/adna/current-contract-authority/payloads/9cc3add0b31c8c22e2384848e12e6ce0a35aa75809a6ee022176fe2ee614917a",
            "513aa65843b570f6657637f04e58409c79e513c5",
        ),
        (
            "data/adna/current-contract-authority/payloads/9e85b5c8f723ab2dfbec4f89a5aa07faecca74ba5e2d777b7f90a23005301d66",
            "72b0ef56c6b6261c833a9cfc1b3b38af1512a7d1",
        ),
        (
            "data/adna/current-contract-authority/payloads/a710cd0f6fc1778c53dd361b3ed55856af9c5f186d5d5d0e918b464bd4a7d7b3",
            "6d9cecb62bb386011cc047d979c0d0dc0deeb1b4",
        ),
        (
            "data/adna/current-contract-authority/payloads/be7d660b267283efda89b423846de4c6baba4a293217376b39682a2926efc412",
            "b77124c1fe9facf656591fe3f6566a5bcd79e1e3",
        ),
        (
            "data/adna/current-contract-authority/payloads/c13db70341a103a763a1e08e53d18317d0e1404039dc159b1c6bf960f26a21a6",
            "98d839728b381b1ca093b8ed3e510399f1c4a0c3",
        ),
        (
            "data/adna/current-contract-authority/payloads/c251a660be42218195f12d888c709cc79ffa3950156a2987db0f20748464c48f",
            "afc1909035f9fec8bb7651bc6c3d1c29a6edf1f7",
        ),
        (
            "data/adna/current-contract-authority/payloads/c3c01c048df9e9bf46789b42de403ee65cbe29a9a52f34ee041fc679f04a4f5c",
            "3bd31801fd1d7178bdd1778abf67427bcfb61472",
        ),
        (
            "data/adna/current-contract-authority/payloads/ca96113bbe7bc92c3cdc40b464987c9d068a51ff74c5f27e9fc0d8e89def9b6f",
            "e1c1bf87fe50d670fcf789fa35d21692db3810d3",
        ),
        (
            "data/adna/current-contract-authority/payloads/cfe5c6461b42a90595a492aed11f2c8e6eb98b7c4caf2cc9f47e3333185e3f33",
            "97115c42afc8cf799ded0ce27f1bdd17604aeb08",
        ),
        (
            "data/adna/current-contract-authority/payloads/d2c1eb85f2e296b4f66484d457bf8112b494c7c161807fb15f51290fb78288e8",
            "54d85c3fc673f54aee535246d4e7e0d956a57494",
        ),
        (
            "data/adna/current-contract-authority/payloads/d8f234a4d0c7275f585f1167bbab3d5a1258dcf49a1de86f9523c7c4a6374635",
            "c5807fe3c96e95e4d9dfc636ce2e22bc9ea0d34a",
        ),
        (
            "data/adna/current-contract-authority/payloads/d9f6338145371e3919a9989787f357b70c960d4959edb800e93b48e9789a55d2",
            "04b22f6e2d2ab13b0d1b9262c40348f3e2ee98e5",
        ),
        (
            "data/adna/current-contract-authority/payloads/e30749373ef9876411a374930b8ed00da53363eaaeb95e58fc91303e0ff08b5c",
            "13a7b7e2e2368ee1fde27a8fa2e958277d71acf0",
        ),
        (
            "data/adna/current-contract-authority/payloads/e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
        ),
        (
            "data/adna/current-contract-authority/payloads/e8fe5cf3819a96c2ccb9e2487ec169801a49d27e2c751b79eb19404505f2233a",
            "a9db51fcdf3962b8d98bd4d469984f7aee9a3999",
        ),
        (
            "data/adna/current-contract-authority/payloads/ed796794f0c862b217c9bec4c16801cf399aab431327b81cb61cd1c4cbc5d460",
            "a5bae11057c97306446ed24e6cd7ccc302433cb0",
        ),
        (
            "data/adna/current-contract-authority/payloads/eee76f865de5a9f2456950f710ae5d5f9b5bd0ea02aa54f614c5eed6642a0bfd",
            "8e4d504182979b9ad211fb7b88757897fbed0606",
        ),
        (
            "data/adna/current-contract-authority/payloads/f1ca884621c4ec645a99a23e91f21d44b769b06bfc1b5e3fef8539d1243ee670",
            "f49080d51f9f81b2ad78e3cbdbbe6a2a07175ddf",
        ),
        (
            "data/adna/current-contract-authority/payloads/f958d9e7a65b97cb06f2b6850221a7ffb93363e3576e17cd236b6588d07f7f6b",
            "cbb399790abffc8309cc489111ca67acbd7b77b8",
        ),
        (
            "data/adna/current-contract-authority/payloads/f95c0ad9f5b2015f8d3f0a035cb3d7129f5e2603e77a5e570077e8632cf8077a",
            "7da5d786907b74177896e1dc23b7bb006eb13a58",
        ),
        (
            "data/adna/current-contract-authority/payloads/f9f7725aa46bcd88911aa54dda404fa6c9459c5cf4d0f9a9940ffac2bfe31918",
            "44aacf8883da5fbd2f25c863a43e80ce1530af19",
        ),
        (
            "data/adna/current-contract-authority/payloads/fa0c963353ac202e89a697d13f4be84169beaa80eda4fdd96b8bb2e124851499",
            "b0b49619bc62cf5f4b86cd9ecd82443eaa8be61d",
        ),
        (
            "data/adna/current-contract-authority/payloads/fa23b4b1013e21ef485d6e81ba59ea05d82d91acdc692fb82ba944a616576cc6",
            "c54f17e8b1860f050c8c85f0655af08c16dced0b",
        ),
        (
            "data/adna/current-contract-authority/payloads/fcfbc4c4ae9953155f0f72119803492b872d28178a4132c45dd9924bca8a9254",
            "20a6f1ae20bd808cc34c76c8ed75fd9df930cb29",
        ),
    )
)


THIRD_PARTY_MAP_ASSET_PREFIXES = (
    "docs/assets/vendor/map/leaflet/",
    "docs/assets/vendor/map/markercluster/",
    "docs/report/countries/sweden/_map_assets/leaflet/",
    "docs/report/countries/sweden/_map_assets/markercluster/",
    "docs/report/nordic-atlas/_map_assets/leaflet/",
    "docs/report/nordic-atlas/_map_assets/markercluster/",
    "docs/report/nordic/_map_assets/leaflet/",
    "docs/report/nordic/_map_assets/markercluster/",
    "docs/report/regions/europe-plus/_map_assets/leaflet/",
    "docs/report/regions/europe-plus/_map_assets/markercluster/",
    "docs/report/regions/nordic/_map_assets/leaflet/",
    "docs/report/regions/nordic/_map_assets/markercluster/",
    "docs/report/world/_map_assets/leaflet/",
    "docs/report/world/_map_assets/markercluster/",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map/leaflet/",
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map/markercluster/",
)


def test_tracked_data_does_not_vendor_package_trees() -> None:
    """Inspect the real Git index so newly staged snapshots fail before commit."""
    tracked = subprocess.check_output(
        ["git", "--no-replace-objects", "ls-files", "--stage", "-z", "--", "data"],
        cwd=REPOSITORY,
        timeout=20,
    )
    entries = []
    for raw in tracked.split(b"\0"):
        if raw:
            metadata, name = raw.split(b"\t", 1)
            mode, blob, stage = metadata.decode().split()
            assert stage == "0", "Resolve unmerged source before checking retention"
            entries.append((name.decode(), mode, blob))
    forbidden = _package_snapshot_paths(entries)
    assert not forbidden, (
        f"{len(forbidden)} tracked package snapshot files under data; "
        "retain canonical Git source references instead: " + ", ".join(forbidden[:8])
    )


def _package_snapshot_paths(entries: list[tuple[str, str, str]]) -> list[str]:
    """Admit only the exact published regular build fixture inside data package paths."""
    return [
        name
        for name, mode, blob in entries
        if "packages" in PurePosixPath(name).parts
        and (name, mode, blob)
        != (
            HISTORICAL_BUILD_RESOURCE,
            "100644",
            "05d6713c0658290c2e88e7cf8c86fe547aba9d1e",
        )
    ]


def test_data_does_not_duplicate_package_source() -> None:
    """Join staged files to current and historical source identities without reading bodies."""
    tracked = subprocess.check_output(
        [
            "git",
            "--no-replace-objects",
            "ls-files",
            "--stage",
            "-z",
            "--",
            ".",
            ":(exclude)artifacts",
        ],
        cwd=REPOSITORY,
        timeout=20,
    )
    entries = []
    for raw in tracked.split(b"\0"):
        if raw:
            metadata, name = raw.split(b"\t", 1)
            _, blob, stage = metadata.decode().split()
            assert stage == "0", "Resolve unmerged source before checking retention"
            entries.append((name.decode(), blob))
    forbidden = _source_duplicates(
        _ordinary_source_entries(entries), _historical_source_entries()
    )
    assert not forbidden, "Data duplicates canonical first-party source: " + repr(
        forbidden[:8]
    )


def _canonical_source_path(name: str, blob: str = "") -> bool:
    """Own implementation/configuration sources, excluding scientific products and served assets."""
    path = PurePosixPath(name)
    if not path.parts or path.parts[0] in {"data", "artifacts", "reports", ".bijux"}:
        return False
    if "artifacts" in path.parts:
        return False
    if name.startswith(THIRD_PARTY_MAP_ASSET_PREFIXES) and path.suffix in {
        ".js",
        ".css",
        ".png",
    }:
        return False
    if path.name in {"LICENSE", "LICENSE.txt", "NOTICE", "NOTICE.txt", "COPYING"}:
        return False
    if re.fullmatch(
        r"docs/report/regions/nordic/nordic\.atlas-(details|indexes|nodes|provenance)\.\d{4}\.[0-9a-f]{16}\.js",
        name,
    ):
        return False
    # The live-R producer writes this exact oracle from inline scientific literals.
    if (name, blob) == (
        "docs/report/method-certification/linux-r-oracle/oracle/oracle.R",
        "ec8a62a656ea63b67d76ea22ccc5a37c7d093488",
    ):
        return False
    if name.startswith(EXECUTION_REFERENCE_PREFIX) and path.suffix in {
        ".patch",
        ".diff",
    }:
        return True
    if path.parts[0] in {"configs", "makes", "apis", "scripts", ".github"}:
        return True
    if len(path.parts) == 1 and (
        path.name
        in {
            "Makefile",
            "Dockerfile",
            "pyproject.toml",
            "uv.lock",
            "package.json",
            "package-lock.json",
            ".gitignore",
            ".gitattributes",
            ".pre-commit-config.yaml",
            "tox.ini",
        }
        or path.suffix in {".toml", ".yaml", ".yml", ".ini", ".cfg"}
    ):
        return True
    return path.suffix in {
        ".py",
        ".pyi",
        ".R",
        ".r",
        ".js",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".jsx",
        ".sh",
        ".bash",
        ".rs",
        ".c",
        ".cpp",
        ".h",
    } or name.endswith((".py.txt", ".R.txt"))


def _raw_history_entries(raw: bytes) -> tuple[tuple[str, str], ...]:
    """Keep every source-path alias from raw Git metadata, including relocated old modules."""
    fields = raw.split(b"\0")
    entries = set()
    position = 0
    while position < len(fields):
        metadata = fields[position].lstrip(b"\n")
        position += 1
        if not metadata:
            continue
        if len(metadata) == 40 and all(c in b"0123456789abcdef" for c in metadata):
            continue
        assert metadata.startswith(b":"), "Unexpected source-history metadata"
        parts = metadata.split()
        assert len(parts) == 5 and parts[4] in {b"A", b"M"}
        assert position < len(fields), "Source-history path missing"
        name = fields[position].decode()
        position += 1
        if _canonical_source_path(name, parts[3].decode()):
            entries.add((name, parts[3].decode()))
    return tuple(sorted(entries))


@lru_cache(maxsize=1)
def _historical_source_entries() -> tuple[tuple[str, str], ...]:
    """Cache one metadata-only history query per check process; never scan source bodies."""
    raw = subprocess.check_output(
        [
            "git",
            "--no-replace-objects",
            "log",
            "--format=%H%x00",
            "--raw",
            "-z",
            "--no-abbrev",
            "--no-renames",
            "--diff-filter=AM",
            "--root",
            "--full-history",
            "-m",
            "HEAD",
            "--",
            ".",
            ":(exclude)data",
            ":(exclude)artifacts",
            ":(exclude,glob)**/artifacts/**",
        ],
        cwd=REPOSITORY,
        timeout=60,
    )
    return _raw_history_entries(raw)


def _source_duplicates(
    entries: list[tuple[str, str]], history: tuple[tuple[str, str], ...] = ()
) -> list[tuple[str, str]]:
    """Reject exact first-party body copies under arbitrary data names, including stale versions."""
    modules = {
        blob: name
        for name, blob in sorted([*history, *entries])
        if _canonical_source_path(name, blob)
        and blob
        not in {
            "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
            "8b137891791fe96927ad78e64b0aad7bded08bdc",
        }
    }
    return [
        (name, modules[blob])
        for name, blob in entries
        if name.startswith("data/")
        and blob in modules
        and (name, blob)
        != (HISTORICAL_BUILD_RESOURCE, "05d6713c0658290c2e88e7cf8c86fe547aba9d1e")
    ]


@pytest.mark.parametrize(
    "name",
    [
        "capture/source.py",
        "capture/source.dat",
        "capture/artifacts/producer.py",
        "a" * 64,
    ],
)
def test_source_copy_guard_does_not_depend_on_data_filename(name: str) -> None:
    entries = [("packages/sample/src/model.py", "1" * 40), ("data/" + name, "1" * 40)]
    assert _source_duplicates(entries) == [
        ("data/" + name, "packages/sample/src/model.py")
    ]


def test_source_copy_guard_includes_maintained_reference_code() -> None:
    entries = [
        ("packages/sample/tests/reference/oracle.R", "1" * 40),
        ("data/result.bin", "1" * 40),
    ]
    assert _source_duplicates(entries)


@pytest.mark.parametrize(
    "blob",
    [
        "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
        "8b137891791fe96927ad78e64b0aad7bded08bdc",
    ],
)
def test_empty_source_bodies_do_not_make_data_placeholders_code(blob: str) -> None:
    assert not _source_duplicates(
        [("packages/sample/tests/__init__.py", blob), ("data/.gitkeep", blob)]
    )


@pytest.mark.parametrize(
    "capture",
    [
        "native-r/capture",
        "native-r-annulus/capture",
        "native-r-count-domain/capture",
        "source-locked-linux-r/reference-bundle",
    ],
)
@pytest.mark.parametrize(
    "name", ["r_support.R", "run_source_domains.py", "source_domains.R"]
)
def test_native_reference_captures_do_not_store_canonical_source(
    capture: str, name: str
) -> None:
    source = "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/" + name
    data = "data/method-certification/" + capture + "/source-domains/" + name
    assert _source_duplicates([(source, "1" * 40), (data, "1" * 40)]) == [
        (data, source)
    ]


@pytest.mark.parametrize("name", ["old.py.txt", "capture.bin", "a" * 64])
def test_old_relocated_source_copies_are_rejected(name: str) -> None:
    history = (("packages/sample/src/retired_api.py", "1" * 40),)
    assert _source_duplicates([("data/" + name, "1" * 40)], history)


@pytest.mark.parametrize(
    "source",
    [
        "configs/docs/maps/report-owner.json",
        "configs/docs/publication/README.md",
        "docs/reference/producer.py.txt",
    ],
)
def test_configuration_and_controller_sources_are_rejected(source: str) -> None:
    assert _source_duplicates([("data/opaque", "1" * 40)], ((source, "1" * 40),))


@pytest.mark.parametrize(
    "source",
    [
        "packages/sample/artifacts/lint/ruff.log",
        "packages/sample/NOTICE",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map/leaflet/leaflet.js",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map/markercluster/leaflet.markercluster.js",
        "packages/sample/report_portal/scientific_accounts.json",
        "docs/report/scientific_accounts.json",
        "docs/report/results.csv",
        "docs/report/regions/nordic/nordic.atlas-nodes.0010.0c87646354bb4659.js",
    ],
)
def test_captured_products_and_legal_inputs_are_not_implementation_source(
    source: str,
) -> None:
    assert not _source_duplicates([("data/input", "1" * 40)], ((source, "1" * 40),))


def test_generated_fixture_exception_is_exact_path_and_body() -> None:
    historical = (
        (
            "packages/sample/src/_build_version.py",
            "05d6713c0658290c2e88e7cf8c86fe547aba9d1e",
        ),
    )
    assert not _source_duplicates(
        [(HISTORICAL_BUILD_RESOURCE, historical[0][1])], historical
    )
    assert _source_duplicates([("data/other.py", historical[0][1])], historical)
    assert _source_duplicates(
        [(HISTORICAL_BUILD_RESOURCE, "1" * 40)], ((historical[0][0], "1" * 40),)
    )


def test_history_metadata_keeps_all_source_aliases() -> None:
    blob = "1" * 40
    raw = (
        f":000000 100644 {'0' * 40} {blob} A\0packages/sample/fixtures/plain.txt\0\n"
        f":000000 100644 {'0' * 40} {blob} A\0packages/sample/src/retired.py\0"
    ).encode()
    assert _raw_history_entries(raw) == (("packages/sample/src/retired.py", blob),)


@pytest.mark.parametrize(
    "source",
    [
        "pyproject.toml",
        "uv.lock",
        "Makefile",
        "makes/check.mk",
        "apis/lra/openapi.json",
        "scripts/capture.sh",
        ".github/workflows/tests.yml",
    ],
)
def test_build_and_interface_sources_are_owned_without_filename_shortcuts(
    source: str,
) -> None:
    assert _source_duplicates([("data/arbitrary", "1" * 40)], ((source, "1" * 40),))


def test_inline_scientific_oracle_product_is_exact_body_and_authority() -> None:
    source = "docs/report/method-certification/linux-r-oracle/oracle/oracle.R"
    oracle = "ec8a62a656ea63b67d76ea22ccc5a37c7d093488"
    assert not _source_duplicates(
        [("data/original-oracle.R", oracle)], ((source, oracle),)
    )
    assert _source_duplicates(
        [("data/changed-oracle.R", "1" * 40)], ((source, "1" * 40),)
    )


def test_package_fixture_exception_requires_exact_regular_index_identity() -> None:
    blob = "05d6713c0658290c2e88e7cf8c86fe547aba9d1e"
    assert not _package_snapshot_paths([(HISTORICAL_BUILD_RESOURCE, "100644", blob)])
    assert _package_snapshot_paths([(HISTORICAL_BUILD_RESOURCE, "100644", "1" * 40)])
    assert _package_snapshot_paths([(HISTORICAL_BUILD_RESOURCE, "120000", blob)])
    assert _package_snapshot_paths([(HISTORICAL_BUILD_RESOURCE, "100755", blob)])
    assert _package_snapshot_paths(
        [("data/source/packages/sample/model.py", "100644", blob)]
    )


@pytest.mark.parametrize(
    "directory", ["vendor", "vendored", "node_modules", "leaflet", "markercluster"]
)
def test_owned_code_is_not_exempt_by_misleading_directory_name(directory: str) -> None:
    source = "packages/sample/src/" + directory + "/model.py"
    assert _source_duplicates([("data/opaque", "1" * 40)], ((source, "1" * 40),))


def test_served_asset_owner_exemption_does_not_match_sibling_namespace() -> None:
    source = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map/leaflet_owned/model.py"
    assert _source_duplicates([("data/opaque", "1" * 40)], ((source, "1" * 40),))


def test_served_asset_owner_does_not_exempt_owned_python_source() -> None:
    source = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map/leaflet/model.py"
    assert _source_duplicates([("data/opaque", "1" * 40)], ((source, "1" * 40),))


@pytest.mark.parametrize("extension", [".py", ".patch", ".diff"])
@pytest.mark.parametrize("historical", [False, True])
def test_execution_reference_identity_rejects_renamed_data_copy(
    extension: str, historical: bool
) -> None:
    source = (
        EXECUTION_REFERENCE_PREFIX + "pollen_source/lake/observation/source" + extension
    )
    original = (source, "1" * 40)
    data = ("data/capture/arbitrary-payload.bin", "1" * 40)
    entries = [data] if historical else [original, data]
    history = (original,) if historical else ()
    assert _source_duplicates(entries, history) == [(data[0], source)]


def test_reference_patch_history_keeps_every_source_alias() -> None:
    blob = "1" * 40
    source = EXECUTION_REFERENCE_PREFIX + "pollen_source/lake/custody/source.patch"
    raw = (
        f":000000 100644 {'0' * 40} {blob} A\0packages/sample/fixtures/plain.txt\0\n"
        f":000000 100644 {'0' * 40} {blob} A\0{source}\0"
    ).encode()
    history = _raw_history_entries(raw)
    assert history == ((source, blob),)
    assert _source_duplicates([("data/opaque", blob)], history) == [
        ("data/opaque", source)
    ]


def test_execution_reference_match_does_not_depend_on_source_like_data_path() -> None:
    source = EXECUTION_REFERENCE_PREFIX + "context_source/land/observation/source.patch"
    data = "data/capture/source-code/artifacts/science/observer/source.diff"
    assert _source_duplicates([(data, "1" * 40)], ((source, "1" * 40),)) == [
        (data, source)
    ]


def test_original_upstream_reference_and_licence_are_not_execution_source() -> None:
    upstream = "packages/sample/tests/fixtures/upstream/original.patch"
    history = ((upstream, "1" * 40), ("packages/sample/LICENSE", "2" * 40))
    entries = [
        ("data/scientific-source/original.patch", "1" * 40),
        ("data/scientific-source/LICENSE", "2" * 40),
        ("data/scientific-source/original-author.R", "3" * 40),
    ]
    assert not _source_duplicates(entries, history)


def _ordinary_source_entries(entries: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Keep only the closed frozen evidence identities outside the ordinary copy rule."""
    return [row for row in entries if row not in FROZEN_ADNA_AUTHORITY_IDENTITIES]


def test_frozen_authority_namespace_has_exact_regular_objects() -> None:
    """Bind the entire historical evidence namespace without executing its programs."""
    raw = subprocess.check_output(
        [
            "git",
            "--no-replace-objects",
            "ls-files",
            "--stage",
            "-z",
            "--",
            "data/adna/current-contract-authority",
        ],
        cwd=REPOSITORY,
        timeout=20,
    )
    seen = set()
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, name = record.split(b"\t", 1)
        mode, blob, stage = metadata.decode().split()
        assert mode == "100644" and stage == "0"
        seen.add((name.decode(), blob))
    assert seen == FROZEN_ADNA_AUTHORITY_IDENTITIES


@pytest.mark.parametrize("entry", sorted(FROZEN_ADNA_AUTHORITY_IDENTITIES))
def test_frozen_authority_exception_requires_exact_member_identity(
    entry: tuple[str, str],
) -> None:
    path, blob = entry
    source = "packages/own/source/retained_authority.py"
    history = ((source, blob),)
    assert not _source_duplicates(_ordinary_source_entries([entry]), history)
    changed_path = ("data/unregistered/" + path.rsplit("/", 1)[-1], blob)
    assert _ordinary_source_entries([changed_path]) == [changed_path]
    expected_duplicates = (
        []
        if blob
        in {
            "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391",
            "8b137891791fe96927ad78e64b0aad7bded08bdc",
        }
        else [(changed_path[0], source)]
    )
    assert (
        _source_duplicates(_ordinary_source_entries([changed_path]), history)
        == expected_duplicates
    )
    changed_blob = (path, "0" * 40 if blob != "0" * 40 else "1" * 40)
    assert _ordinary_source_entries([changed_blob]) == [changed_blob]
