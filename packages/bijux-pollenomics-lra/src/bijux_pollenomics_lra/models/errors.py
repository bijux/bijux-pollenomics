"""Models errors for the LRA engine."""

from __future__ import annotations


class LRAError(Exception):
    """Base class for package-specific failures."""


class ValidationError(LRAError, ValueError):
    """Input violates a scientific, dimensional, or labelling contract."""

    def __init__(self, message: str, *, reason_code: str = "invalid_input") -> None:
        self.reason_code = reason_code
        super().__init__(message)


class ParityError(LRAError, RuntimeError):
    """A reference-parity comparison could not be completed or failed."""


class ReferenceUnavailableError(ParityError):
    """The requested R reference runtime or package is unavailable."""


class UpstreamUndefinedBehavior(ValidationError):
    """The source package has no well-defined result for this input branch."""


class NativeOptimizerWarning(UserWarning):
    """A native optimizer is used; its trajectory is not R-optimizer parity."""


class SourceCompatibilityWarning(UserWarning):
    """A known source quirk is deliberately retained for parity."""


class ConvergenceError(LRAError, RuntimeError):
    """Optimization ended without convergence; diagnostics remain inspectable."""

    reason_code = "optimizer_nonconvergence"

    def __init__(self, diagnostics: list[dict[str, object]]) -> None:
        self.diagnostics = diagnostics
        failed = sum(not bool(item["success"]) for item in diagnostics)
        super().__init__(
            f"{failed} of {len(diagnostics)} optimization runs did not converge"
        )
