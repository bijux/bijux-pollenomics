from __future__ import annotations


def clean_optional_text(value: object) -> str:
    """Normalize optional text values used in normalized exports."""
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text in {"", "null", "None"} else text


def slugify(value: str) -> str:
    """Convert a label into a stable file slug."""
    slug = "".join(character.lower() if character.isalnum() else "-" for character in value)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")
