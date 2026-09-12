"""Stable reason codes for host LRA refusals."""

from __future__ import annotations


class LRARefusal(ValueError):
    """An unavailable or invalid reconstruction with an observable reason."""

    def __init__(
        self, reason_code: str, detail: str, *, diagnostics: object | None = None
    ) -> None:
        self.reason_code = reason_code
        self.diagnostics = diagnostics
        super().__init__(detail)

    def as_dict(self) -> dict[str, object]:
        """Return the public error envelope without losing the diagnostic."""
        result: dict[str, object] = {
            "status": "refused",
            "reason_code": self.reason_code,
            "detail": str(self),
        }
        if self.diagnostics is not None:
            result["diagnostics"] = self.diagnostics
        return result
