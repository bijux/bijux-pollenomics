"""Independently isolate raw features with a byte-lexical JSON container scanner."""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from typing import Any, BinaryIO

MAX_VALUE_BYTES = 16 * 1024**2
SCALAR_END = re.compile(rb"[\x09\x0a\x0d ,\]}:]")
STRING_SPECIAL = re.compile(rb'["\\]')
CONTAINER_SPECIAL = re.compile(rb'["\[\]{}]')


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def unique(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in items:
        require(key not in result, "Duplicate JSON field")
        result[key] = value
    return result


def bad(value: str) -> None:
    raise ValueError("Nonfinite JSON constant: " + value)


def decode(raw: bytes) -> Any:
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=unique,
        parse_float=Decimal,
        parse_constant=bad,
    )


class Bytes:
    def __init__(
        self, stream: BinaryIO, block: int = 65536, limit: int = MAX_VALUE_BYTES
    ) -> None:
        self.stream = stream
        self.block = block
        self.limit = limit
        self.buffer = b""
        self.position = 0
        self.eof = False

    def byte(self) -> int | None:
        if self.position == len(self.buffer):
            self.buffer = self.stream.read(self.block)
            self.position = 0
            if not self.buffer:
                self.eof = True
                return None
        return self.buffer[self.position]

    def pop(self) -> int:
        value = self.byte()
        require(value is not None, "Unexpected byte EOF")
        assert value is not None
        self.position += 1
        return value

    def space(self) -> int | None:
        while self.byte() in (9, 10, 13, 32):
            self.pop()
        return self.byte()

    def take(self, byte: int) -> None:
        require(self.space() == byte, "JSON byte punctuation differs")
        self.pop()

    def atom(self) -> bytes:
        first = self.space()
        require(first is not None, "JSON value absent")
        output = bytearray()
        stack: list[int] = []
        quoted = False
        container = first in (91, 123)
        string = first == 34

        def append(part: bytes) -> None:
            output.extend(part)
            require(
                len(output) <= self.limit, "Lexical JSON value exceeds bounded capacity"
            )

        if not container and not string:
            while self.byte() is not None:
                match = SCALAR_END.search(self.buffer, self.position)
                end = len(self.buffer) if match is None else match.start()
                append(self.buffer[self.position : end])
                self.position = end
                if match is not None:
                    break
            require(bool(output), "Empty JSON primitive")
            return bytes(output)
        while True:
            require(self.byte() is not None, "Truncated JSON value")
            pattern = STRING_SPECIAL if quoted else CONTAINER_SPECIAL
            match = pattern.search(self.buffer, self.position)
            end = len(self.buffer) if match is None else match.start()
            append(self.buffer[self.position : end])
            self.position = end
            if match is None:
                continue
            b = self.pop()
            append(bytes((b,)))
            if quoted:
                if b == 92:
                    append(bytes((self.pop(),)))
                elif b == 34:
                    quoted = False
                    if string and not container:
                        break
            elif b == 34:
                quoted = True
            elif b in (91, 123):
                stack.append(93 if b == 91 else 125)
            else:
                require(bool(stack) and stack.pop() == b, "Mismatched JSON container")
                if container and not stack:
                    break
        require(bool(output) and not quoted and not stack, "Incomplete JSON atom")
        return bytes(output)


class CollectionScanner:
    def __init__(
        self, path: Path, limit: int = MAX_VALUE_BYTES, block: int = 65536
    ) -> None:
        self.path = path
        self.limit = limit
        self.block = block
        self.metadata: dict[str, Any] = {}
        self.document_complete = False
        self.max_feature_bytes = 0
        self.total_feature_bytes = 0

    def features(self) -> Iterator[tuple[int, Any, str]]:
        with self.path.open("rb") as source:
            data = Bytes(source, self.block, self.limit)
            data.take(123)
            keys = set()
            index = 0
            found = False
            while True:
                key = decode(data.atom())
                require(
                    type(key) is str and key not in keys,
                    "Invalid/duplicate collection key",
                )
                keys.add(key)
                data.take(58)
                if key == "features":
                    require(not found, "Features field repeated")
                    found = True
                    data.take(91)
                    if data.space() != 93:
                        while True:
                            raw = data.atom()
                            self.max_feature_bytes = max(
                                self.max_feature_bytes, len(raw)
                            )
                            self.total_feature_bytes += len(raw)
                            value = decode(raw)
                            yield index, value, hashlib.sha256(raw).hexdigest()
                            index += 1
                            if data.space() == 93:
                                break
                            data.take(44)
                            require(data.space() != 93, "Trailing features comma")
                    data.take(93)
                else:
                    self.metadata[key] = decode(data.atom())
                if data.space() == 125:
                    break
                data.take(44)
                require(data.space() != 125, "Trailing wrapper comma")
            data.take(125)
            require(data.space() is None, "Extra data after collection")
            require(
                found and self.metadata.get("type") == "FeatureCollection",
                "Missing FeatureCollection authority",
            )
            self.document_complete = True
