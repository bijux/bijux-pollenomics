"""LandClim II archive temporal-grid extraction."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..grid import _required_landclim_ii_quality_class
from .landclim_ii_rows import (
    _landclim_ii_standard_errors as _landclim_ii_standard_errors,
)
from .landclim_ii_rows import (
    _published_headers,
    _published_identity,
    _read_landclim_ii_standard_errors,
    _require_exact_tokens,
)
from .values import _required_numeric_mapping


def _merge_landclim_ii_time_windows(
    features: dict[tuple[str, str, str], dict[str, object]],
    path: Path,
    *,
    quality_by_grid: dict[str, dict[str, str]],
    bbox: tuple[float, float, float, float],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> None:
    from . import (
        LANDCLIM_II_MEANS_DIRECTORY,
        TextIOWrapper,
        ZipFile,
        _properties,
        _require_uncertainty_pair,
        _temporal_grid_feature,
        classify_country,
        csv,
        grid_geometry_from_center,
        point_in_bbox,
        summarize_quality_labels,
        time_window_from_tw_filename,
    )

    with ZipFile(path) as archive:
        standard_errors = _read_landclim_ii_standard_errors(archive)
        mean_headers_by_window: dict[str, tuple[str, ...]] = {}
        mean_keys: set[tuple[str, str]] = set()
        published_features: dict[tuple[str, str, str], dict[str, object]] = {}
        for member_name in sorted(archive.namelist()):
            if not member_name.startswith(
                LANDCLIM_II_MEANS_DIRECTORY
            ) or not member_name.endswith(".csv"):
                continue
            time_window = time_window_from_tw_filename(member_name)
            with archive.open(member_name) as handle:
                reader = csv.DictReader(TextIOWrapper(handle, encoding="utf-8"))
                headers, variables = _published_headers(reader.fieldnames, member_name)
                if time_window in mean_headers_by_window:
                    raise ValueError(
                        "LandClim II means repeat time window "
                        f"{time_window}: {member_name}"
                    )
                mean_headers_by_window[time_window] = headers
                error_headers = standard_errors.headers_by_window.get(time_window)
                if error_headers != headers:
                    raise ValueError(
                        "LandClim II mean/standard-error headers differ for "
                        f"{time_window}: means={headers}, "
                        f"standard_errors={error_headers}"
                    )
                for row in reader:
                    _require_exact_tokens(row, headers, member_name=member_name)
                    cell_id, longitude, latitude = _published_identity(
                        row, member_name=member_name
                    )
                    key = (time_window, cell_id)
                    if key in mean_keys:
                        raise ValueError(
                            "LandClim II means contain duplicate (TW, LCGRID_ID) "
                            f"row {key}"
                        )
                    mean_keys.add(key)
                    record_id = f"{cell_id}:{time_window}"
                    estimates = _required_numeric_mapping(
                        row,
                        variables=variables,
                        dataset_id="937075",
                        record_id=record_id,
                        value_kind="mean",
                        require_nonnegative=False,
                    )
                    error_row = standard_errors.rows.get(key)
                    if error_row is None:
                        raise ValueError(
                            f"LandClim II standard-error row is missing for {record_id}"
                        )
                    if (longitude, latitude) != (
                        error_row.longitude,
                        error_row.latitude,
                    ):
                        raise ValueError(
                            "LandClim II mean/standard-error coordinates differ for "
                            f"{record_id}: means={(longitude, latitude)}, "
                            "standard_errors="
                            f"{(error_row.longitude, error_row.latitude)}"
                        )
                    _require_uncertainty_pair(
                        estimates,
                        error_row.values,
                        dataset_id="937075",
                        record_id=record_id,
                    )
                    if longitude is None or latitude is None:
                        continue
                    if not point_in_bbox(longitude, latitude, bbox):
                        continue
                    country = classify_country(longitude, latitude, country_boundaries)
                    if not country:
                        continue
                    geometry = grid_geometry_from_center(longitude, latitude)
                    feature = _temporal_grid_feature(
                        dataset_id="937075",
                        cell_id=cell_id,
                        cell_label=f"{longitude:.1f}E {latitude:.1f}N",
                        time_window=time_window,
                        country=country,
                        geometry=geometry,
                        provenance_path=f"data/landclim/raw/{path.name}",
                        provenance_locator=member_name,
                        value_unit="percentage_cover",
                    )
                    properties = _properties(feature)
                    properties["reconstruction_values"] = estimates
                    properties["standard_errors"] = error_row.values
                    quality_class = _required_landclim_ii_quality_class(
                        quality_by_grid,
                        grid_id=cell_id,
                        time_window=time_window,
                    )
                    properties["quality_class"] = summarize_quality_labels(
                        {quality_class}
                    )
                    published_features[("937075", cell_id, time_window)] = feature
        if mean_headers_by_window != standard_errors.headers_by_window:
            missing_windows = sorted(
                set(mean_headers_by_window) - set(standard_errors.headers_by_window)
            )
            unexpected_windows = sorted(
                set(standard_errors.headers_by_window) - set(mean_headers_by_window)
            )
            raise ValueError(
                "LandClim II mean/standard-error time-window headers differ: "
                f"missing={missing_windows}, unexpected={unexpected_windows}"
            )
        error_keys = set(standard_errors.rows)
        if mean_keys != error_keys:
            missing_rows = sorted(mean_keys - error_keys)
            unexpected_rows = sorted(error_keys - mean_keys)
            raise ValueError(
                "LandClim II mean/standard-error row denominators differ: "
                f"missing={missing_rows}, unexpected={unexpected_rows}"
            )
        features.update(published_features)
