"""Dataset authority and membership validation for LandClim receipts."""

from __future__ import annotations

from ..catalog import LANDCLIM_DATASET_METADATA
from .model import LandClimRawReceiptError
from .receipt_structure import object_rows, safe_receipt_filename


def validate_landclim_receipt_datasets(
    receipt: dict[str, object], declared_names: set[str]
) -> dict[str, str]:
    dataset_rows = object_rows(receipt.get("datasets"), field_name="datasets")
    dataset_by_file: dict[str, str] = {}
    seen_dataset_ids: set[str] = set()
    for dataset in dataset_rows:
        dataset_id = _validated_dataset_id(dataset)
        if dataset_id in seen_dataset_ids:
            raise LandClimRawReceiptError(
                f"Duplicate LandClim receipt dataset: {dataset_id}"
            )
        seen_dataset_ids.add(dataset_id)
        _validate_dataset_authority(dataset, dataset_id)
        for value in _validated_dataset_files(dataset, dataset_id):
            filename = safe_receipt_filename(value)
            if filename in dataset_by_file:
                raise LandClimRawReceiptError(
                    f"LandClim asset belongs to multiple datasets: {filename}"
                )
            dataset_by_file[filename] = dataset_id
    if set(dataset_by_file) != declared_names:
        raise LandClimRawReceiptError(
            "LandClim dataset file inventory does not cover every declared asset"
        )
    return dataset_by_file


def _validated_dataset_id(dataset: dict[str, object]) -> str:
    dataset_id = dataset.get("dataset_id")
    if not isinstance(dataset_id, str) or dataset_id not in LANDCLIM_DATASET_METADATA:
        raise LandClimRawReceiptError("LandClim receipt dataset_id is invalid")
    return dataset_id


def _validate_dataset_authority(dataset: dict[str, object], dataset_id: str) -> None:
    metadata = LANDCLIM_DATASET_METADATA[dataset_id]
    if (
        dataset.get("doi") != metadata["doi"]
        or dataset.get("source_url") != metadata["doi"]
        or dataset.get("label") != metadata["label"]
    ):
        raise LandClimRawReceiptError(
            f"LandClim dataset authority is invalid for {dataset_id}"
        )


def _validated_dataset_files(
    dataset: dict[str, object], dataset_id: str
) -> list[object]:
    files = dataset.get("files")
    if not isinstance(files, list) or not files:
        raise LandClimRawReceiptError(
            f"LandClim dataset files are invalid for {dataset_id}"
        )
    return files
