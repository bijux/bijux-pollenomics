"""Filename-based source artifact classification."""

from __future__ import annotations


def _artifact_kind_from_filename(filename: str) -> str:
    lowered = filename.lower()
    if lowered.endswith(".zip"):
        return "supplementary_zip"
    if lowered.endswith((".pdf", ".docx")):
        return "supplementary_pdf"
    if lowered.endswith((".xlsx", ".xls", ".csv", ".tsv")):
        return "supplementary_table"
    if lowered.endswith((".jpg", ".jpeg", ".png")):
        return "supplementary_image"
    return "supplementary_other"


def _content_type_from_filename(filename: str) -> str:
    lowered = filename.lower()
    if lowered.endswith(".pdf"):
        return "application/pdf"
    if lowered.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if lowered.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if lowered.endswith(".xls"):
        return "application/vnd.ms-excel"
    if lowered.endswith(".csv"):
        return "text/csv"
    if lowered.endswith(".json"):
        return "application/json"
    if lowered.endswith(".tsv"):
        return "text/tab-separated-values"
    if lowered.endswith(".zip"):
        return "application/zip"
    if lowered.endswith(".xml"):
        return "application/xml"
    if lowered.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lowered.endswith(".png"):
        return "image/png"
    return "application/octet-stream"
