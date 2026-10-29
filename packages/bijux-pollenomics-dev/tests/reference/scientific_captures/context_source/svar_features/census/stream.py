"""Read one GeoJSON feature at a time with strict bounded JSON decoding."""

from __future__ import annotations

import codecs
from collections.abc import Iterator
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any, BinaryIO

BLOCK_BYTES = 65536
MAX_VALUE_BYTES = 16 * 1024**2


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def unique(items: list[tuple[str, Any]]) -> dict[str, Any]:
    require(len(items) == len({k for k, _ in items}), "Duplicate JSON object key")
    return dict(items)


def invalid(value: str) -> None:
    raise ValueError("Nonstandard JSON constant: " + value)


class Cursor:
    def __init__(
        self, stream: BinaryIO, limit: int = MAX_VALUE_BYTES, block: int = BLOCK_BYTES
    ) -> None:
        self.stream = stream
        self.limit = limit
        self.block = block
        self.text = ""
        self.position = 0
        self.offset = 0
        self.read_bytes = 0
        self.eof = False
        self.utf8 = codecs.getincrementaldecoder("utf-8")("strict")
        self.decoder = json.JSONDecoder(
            object_pairs_hook=unique, parse_float=Decimal, parse_constant=invalid
        )

    def fill(self) -> bool:
        require(not self.eof, "JSON document ended unexpectedly")
        part = self.stream.read(self.block)
        self.read_bytes += len(part)
        self.eof = not part
        self.text += self.utf8.decode(part, final=self.eof)
        require(
            len(self.text[self.position :].encode()) <= self.limit + self.block,
            "Bounded JSON value capacity exceeded",
        )
        return bool(part)

    def compact(self) -> None:
        self.offset += len(self.text[: self.position].encode())
        self.text = self.text[self.position :]
        self.position = 0

    def peek(self, *, allow_eof: bool = False) -> str | None:
        while True:
            while (
                self.position < len(self.text) and self.text[self.position] in " \t\r\n"
            ):
                self.position += 1
            if self.position < len(self.text):
                return self.text[self.position]
            self.compact()
            if self.eof:
                require(allow_eof, "Unexpected JSON EOF")
                return None
            self.fill()

    def take(self, expected: str) -> None:
        require(self.peek() == expected, "Unexpected JSON punctuation")
        self.position += 1

    def value(self) -> tuple[Any, bytes]:
        self.peek()
        self.compact()
        while True:
            try:
                value, end = self.decoder.raw_decode(self.text, self.position)
                if (
                    end == len(self.text) or self.text[end] not in " \t\r\n,}]:"
                ) and not self.eof:
                    self.fill()
                    continue
                require(
                    end == len(self.text) or self.text[end] in " \t\r\n,}]:",
                    "Invalid JSON value terminator",
                )
                raw = self.text[self.position : end].encode()
                require(len(raw) <= self.limit, "JSON value exceeds bounded capacity")
                self.position = end
                return value, raw
            except json.JSONDecodeError:
                require(not self.eof, "Malformed/truncated JSON value")
                self.fill()


class Collection:
    def __init__(
        self, path: Path, limit: int = MAX_VALUE_BYTES, block: int = BLOCK_BYTES
    ) -> None:
        self.path = path
        self.limit = limit
        self.block = block
        self.metadata: dict[str, Any] = {}
        self.max_feature_bytes = 0
        self.total_feature_bytes = 0
        self.document_complete = False

    def features(self) -> Iterator[tuple[int, Any, str]]:
        with self.path.open("rb") as file:
            cursor = Cursor(file, self.limit, self.block)
            cursor.take("{")
            keys = set()
            seen = False
            index = 0
            if cursor.peek() == "}":
                raise ValueError("Feature collection has no fields")
            while True:
                key, _ = cursor.value()
                require(
                    type(key) is str and key not in keys,
                    "Wrapper key invalid/duplicate",
                )
                keys.add(key)
                cursor.take(":")
                if key == "features":
                    require(not seen, "Duplicate features array")
                    seen = True
                    cursor.take("[")
                    if cursor.peek() != "]":
                        while True:
                            feature, raw = cursor.value()
                            self.max_feature_bytes = max(
                                self.max_feature_bytes, len(raw)
                            )
                            self.total_feature_bytes += len(raw)
                            yield index, feature, hashlib.sha256(raw).hexdigest()
                            index += 1
                            token = cursor.peek()
                            if token == "]":
                                break
                            cursor.take(",")
                            require(cursor.peek() != "]", "Trailing feature comma")
                    cursor.take("]")
                else:
                    self.metadata[key] = cursor.value()[0]
                token = cursor.peek()
                if token == "}":
                    break
                cursor.take(",")
                require(cursor.peek() != "}", "Trailing wrapper comma")
            cursor.take("}")
            require(cursor.peek(allow_eof=True) is None, "Trailing JSON data")
            require(
                seen and self.metadata.get("type") == "FeatureCollection",
                "Named FeatureCollection wrapper required",
            )
            self.document_complete = True
