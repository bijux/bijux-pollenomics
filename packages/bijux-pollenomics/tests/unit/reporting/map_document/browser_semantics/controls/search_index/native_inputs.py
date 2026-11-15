"""Native names and repeated identities exercise published substring search."""

from __future__ import annotations

from typing import Any


def layers() -> list[dict[str, Any]]:
    return [
        {
            "key": f"layer:{i}",
            "label": "Pollen layer Åland",
            "features": [
                {
                    "record_id": f"shared:{j}",
                    "title": f"ÄLG 💠 punctuation.( {j}",
                    "subtitle": "Source-native context",
                    "country": "Sweden",
                    "latitude": 60,
                    "longitude": 18,
                    "time_start_bp": 0,
                    "time_end_bp": 100,
                    "time_label": "source C14 (uncalibrated)",
                }
                for j in range(15)
            ],
        }
        for i in range(2)
    ]
