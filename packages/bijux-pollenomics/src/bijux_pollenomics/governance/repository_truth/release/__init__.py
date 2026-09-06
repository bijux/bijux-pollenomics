"""Repository product credibility, sustainability, and release posture."""

from __future__ import annotations

from pathlib import Path as Path

from ..documentation import (
    build_repository_docs_scope_validation as build_repository_docs_scope_validation,
)
from ..integrity import (
    build_repository_governance_artifact_review as build_repository_governance_artifact_review,
)
from ..metrics import (
    SCORE_MAX as SCORE_MAX,
)
from ..metrics import (
    _build_core_counts as _build_core_counts,
)
from ..metrics import (
    _count_suffix_files as _count_suffix_files,
)
from ..metrics import (
    _count_tree_files as _count_tree_files,
)
from ..metrics import (
    _load_json_or_default as _load_json_or_default,
)
from .credibility import (
    _credibility_row as _credibility_row,
)
from .credibility import (
    build_repository_credibility_dashboard,
    render_repository_credibility_dashboard_markdown,
)
from .extensibility import (
    build_repository_extension_review,
    render_repository_extension_review_markdown,
)
from .honesty import (
    build_repository_brutal_honesty_review,
    render_repository_brutal_honesty_review_markdown,
)
from .product_model import (
    build_repository_product_model,
    render_repository_product_model_markdown,
)
from .refusal import (
    _release_refusal_row as _release_refusal_row,
)
from .refusal import (
    build_repository_final_release_refusal,
    render_repository_final_release_refusal_markdown,
)
from .sustainability import (
    build_repository_output_sustainability_review,
    render_repository_output_sustainability_review_markdown,
)

__all__ = [
    "build_repository_brutal_honesty_review",
    "build_repository_credibility_dashboard",
    "build_repository_extension_review",
    "build_repository_final_release_refusal",
    "build_repository_output_sustainability_review",
    "build_repository_product_model",
    "render_repository_brutal_honesty_review_markdown",
    "render_repository_credibility_dashboard_markdown",
    "render_repository_extension_review_markdown",
    "render_repository_final_release_refusal_markdown",
    "render_repository_output_sustainability_review_markdown",
    "render_repository_product_model_markdown",
]
