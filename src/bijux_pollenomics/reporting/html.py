from __future__ import annotations

import json

from .utils import escape_html


def render_multi_country_map_html(
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    point_layers: list[dict[str, object]],
    polygon_layers: list[dict[str, object]],
    asset_base_path: str,
) -> str:
    """Render an advanced standalone interactive HTML map."""
    initial_diameter_km = 20
    initial_time_interval_years = 100
    map_points = [feature for layer in point_layers for feature in layer["features"]]
    time_candidates: set[int] = set()
    for layer in point_layers:
        for feature in layer["features"]:
            if not isinstance(feature, dict):
                continue
            raw = feature.get("time_year_bp")
            if raw is None:
                continue
            try:
                time_candidates.add(int(round(float(raw))))
            except (TypeError, ValueError):
                continue
    time_values = sorted(time_candidates)
    has_time_data = bool(time_values)
    if time_values:
        time_min_bp = min(time_values)
        time_max_bp = max(time_values)
        max_time_span = max(initial_time_interval_years, time_max_bp - time_min_bp)
        initial_time_start_bp = time_min_bp
    else:
        time_min_bp = 0
        time_max_bp = 0
        max_time_span = initial_time_interval_years
        initial_time_start_bp = 0
    initial_time_end_bp = min(time_max_bp, initial_time_start_bp + initial_time_interval_years)
    if map_points:
        latitude_values = [float(feature["latitude"]) for feature in map_points]
        longitude_values = [float(feature["longitude"]) for feature in map_points]
        bounds = [
            [min(latitude_values), min(longitude_values)],
            [max(latitude_values), max(longitude_values)],
        ]
    else:
        bounds = [[54.0, 4.0], [72.0, 35.0]]
    template = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>__TITLE__ Research Map</title>
    <link rel="stylesheet" href="__ASSET_BASE_PATH__/leaflet/leaflet.css">
    <link rel="stylesheet" href="__ASSET_BASE_PATH__/markercluster/MarkerCluster.css">
    <link rel="stylesheet" href="__ASSET_BASE_PATH__/markercluster/MarkerCluster.Default.css">
    <style>
      :root {
        --ink: #18253d;
        --ink-soft: #31425f;
        --muted: #61708d;
        --surface: rgba(252, 249, 244, 0.90);
        --surface-soft: rgba(255, 253, 250, 0.78);
        --surface-strong: rgba(255, 252, 247, 0.97);
        --surface-edge: rgba(24, 37, 61, 0.10);
        --surface-edge-strong: rgba(24, 37, 61, 0.18);
        --surface-wash: linear-gradient(180deg, rgba(255, 255, 255, 0.40), rgba(255, 255, 255, 0));
        --blue: #1f5ed8;
        --teal: #0e7a72;
        --gold: #ad6708;
        --rose: #b42344;
        --shadow-lg: 0 32px 96px rgba(24, 37, 61, 0.16);
        --shadow-md: 0 16px 40px rgba(24, 37, 61, 0.11);
        --shadow-sm: 0 8px 22px rgba(24, 37, 61, 0.08);
        --font-body: "Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        --font-display: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif;
      }
      * { box-sizing: border-box; }
      html, body {
        margin: 0;
        min-height: 100%;
        background:
          radial-gradient(circle at top left, rgba(31, 94, 216, 0.18), transparent 32%),
          radial-gradient(circle at 82% 18%, rgba(14, 122, 114, 0.10), transparent 20%),
          radial-gradient(circle at right center, rgba(173, 103, 8, 0.12), transparent 24%),
          linear-gradient(180deg, #f8f3eb 0%, #ece3d7 52%, #e5dacc 100%);
        color: var(--ink);
        font-family: var(--font-body);
      }
      body { min-height: 100vh; }
      body.has-mobile-panel-open {
        overflow: hidden;
      }
      .app-shell { position: relative; min-height: 100vh; }
      .sidebar {
        position: absolute;
        top: 16px;
        left: 16px;
        bottom: 16px;
        width: min(420px, calc(100vw - 32px));
        z-index: 1200;
        transition: transform 180ms ease, opacity 180ms ease;
      }
      .sidebar.is-collapsed {
        transform: translateX(calc(-100% - 24px));
        opacity: 0;
        pointer-events: none;
      }
      .sidebar-inner {
        height: 100%;
        overflow-y: auto;
        padding: 24px;
        border: 1px solid var(--surface-edge-strong);
        border-radius: 28px;
        background:
          var(--surface-wash),
          linear-gradient(180deg, rgba(255, 252, 247, 0.98), rgba(245, 239, 230, 0.92));
        backdrop-filter: blur(18px);
        box-shadow: var(--shadow-lg);
      }
      .sidebar-header {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        align-items: flex-start;
      }
      .sidebar-heading {
        min-width: 0;
      }
      .mobile-panel-close {
        display: none;
        align-items: center;
        justify-content: center;
        flex: 0 0 auto;
        min-width: 88px;
      }
      .mobile-scrim {
        position: fixed;
        inset: 0;
        z-index: 1180;
        border: 0;
        background: rgba(20, 33, 61, 0.28);
        opacity: 0;
        pointer-events: none;
        transition: opacity 180ms ease;
      }
      .mobile-scrim.is-visible {
        opacity: 1;
        pointer-events: auto;
      }
      .help-dialog {
        position: fixed;
        inset: 0;
        z-index: 1400;
        display: grid;
        place-items: center;
        padding: 24px;
        background: rgba(24, 37, 61, 0.34);
      }
      .help-dialog[hidden] {
        display: none;
      }
      .help-dialog-card {
        width: min(760px, 100%);
        max-height: min(88vh, 780px);
        overflow: auto;
        padding: 24px;
        border-radius: 28px;
        border: 1px solid rgba(24, 37, 61, 0.12);
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.52), rgba(255, 255, 255, 0)),
          rgba(255, 252, 247, 0.98);
        box-shadow: var(--shadow-lg);
      }
      .help-dialog-head {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        align-items: flex-start;
        margin-bottom: 18px;
      }
      .help-dialog-head h2 {
        margin: 6px 0 0;
        font-family: var(--font-display);
        font-size: 30px;
        line-height: 1.02;
      }
      .help-dialog-head p {
        margin: 10px 0 0;
        color: var(--muted);
        font-size: 14px;
        line-height: 1.7;
      }
      .help-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
      }
      .help-card {
        padding: 16px;
        border-radius: 18px;
        border: 1px solid rgba(24, 37, 61, 0.10);
        background: rgba(255, 255, 255, 0.74);
      }
      .help-card h3 {
        margin: 0 0 10px;
        font-size: 14px;
      }
      .help-list {
        display: grid;
        gap: 10px;
      }
      .help-row {
        display: grid;
        grid-template-columns: minmax(84px, auto) minmax(0, 1fr);
        gap: 12px;
        align-items: start;
      }
      .help-key {
        display: inline-flex;
        justify-content: center;
        padding: 6px 9px;
        border-radius: 12px;
        border: 1px solid rgba(24, 37, 61, 0.14);
        background: rgba(24, 37, 61, 0.06);
        color: var(--ink-soft);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .help-row span:last-child {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.6;
      }
      .map-stage { position: relative; min-height: 100vh; }
      #map { height: 100vh; width: 100%; }
      .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(31, 94, 216, 0.10);
        color: var(--blue);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      h1 {
        margin: 16px 0 10px;
        font-family: var(--font-display);
        font-size: clamp(32px, 4vw, 44px);
        font-weight: 700;
        letter-spacing: -0.03em;
        line-height: 0.98;
      }
      .lede {
        margin: 0 0 22px;
        color: var(--muted);
        font-size: 15px;
        line-height: 1.75;
        max-width: 60ch;
      }
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 18px;
      }
      .workspace-brief {
        display: grid;
        gap: 14px;
        padding: 18px;
        margin-bottom: 18px;
        border: 1px solid rgba(24, 37, 61, 0.10);
        border-radius: 22px;
        background:
          linear-gradient(135deg, rgba(31, 94, 216, 0.08), rgba(14, 122, 114, 0.04) 52%, rgba(173, 103, 8, 0.08)),
          rgba(255, 255, 255, 0.70);
        box-shadow: var(--shadow-sm);
      }
      .workspace-brief-head {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: baseline;
      }
      .workspace-brief-head strong {
        font-size: 15px;
      }
      .workspace-brief-head span {
        color: var(--muted);
        font-size: 12px;
      }
      .workspace-brief-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
      }
      .workspace-brief-card {
        padding: 12px 14px;
        border-radius: 18px;
        border: 1px solid rgba(24, 37, 61, 0.10);
        background: rgba(255, 255, 255, 0.70);
      }
      .workspace-brief-label {
        display: block;
        margin-bottom: 6px;
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .workspace-brief-value {
        display: block;
        font-size: 14px;
        font-weight: 700;
        line-height: 1.4;
      }
      .workspace-brief-note {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.6;
      }
      .stat-card,
      .panel-card,
      .floating-legend,
      .map-topbar,
      .map-status,
      .focus-card {
        border: 1px solid var(--surface-edge);
        background: var(--surface);
        backdrop-filter: blur(16px);
        box-shadow: var(--shadow-md);
      }
      .stat-card,
      .panel-card,
      .floating-legend,
      .map-topbar,
      .map-status,
      .focus-card {
        position: relative;
        overflow: hidden;
      }
      .stat-card::before,
      .panel-card::before,
      .floating-legend::before,
      .map-topbar::before,
      .map-status::before,
      .focus-card::before {
        content: "";
        position: absolute;
        inset: 0 0 auto;
        height: 1px;
        background: linear-gradient(90deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0));
        pointer-events: none;
      }
      .stat-card {
        padding: 16px;
        border-radius: 18px;
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0)),
          var(--surface);
      }
      .stat-label {
        display: block;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 11px;
        font-weight: 700;
        margin-bottom: 8px;
      }
      .stat-value { font-size: 24px; font-weight: 700; }
      .stat-value--compact { font-size: 18px; }
      .stat-support {
        display: block;
        margin-top: 8px;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.55;
      }
      .section-stack { display: grid; gap: 16px; }
      .section-nav {
        position: sticky;
        top: 0;
        z-index: 2;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 0 0 18px;
        padding: 10px 0 14px;
        background: linear-gradient(180deg, rgba(246, 241, 233, 0.98), rgba(246, 241, 233, 0.88), rgba(246, 241, 233, 0));
      }
      .section-nav-button {
        appearance: none;
        border: 1px solid rgba(20, 33, 61, 0.10);
        background: rgba(255, 255, 255, 0.84);
        color: var(--muted);
        border-radius: 999px;
        padding: 8px 12px;
        font: inherit;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.03em;
        cursor: pointer;
        transition: background 120ms ease, border-color 120ms ease, color 120ms ease, transform 120ms ease;
      }
      .section-nav-button:hover {
        transform: translateY(-1px);
      }
      .section-nav-button.is-active {
        background: rgba(37, 99, 235, 0.12);
        border-color: rgba(37, 99, 235, 0.28);
        color: var(--blue);
      }
      .panel-card { border-radius: 20px; padding: 18px; }
      .section-head {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: baseline;
        margin-bottom: 10px;
      }
      .section-head h2 { margin: 0; font-size: 17px; }
      .section-head span { color: var(--muted); font-size: 12px; }
      .panel-copy {
        margin: 0 0 14px;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.6;
      }
      .chip-grid { display: flex; flex-wrap: wrap; gap: 10px; }
      .chip-toggle,
      .toolbar-button,
      .preset-button,
      .inline-button,
      .basemap-button {
        appearance: none;
        border: 1px solid rgba(20, 33, 61, 0.12);
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 244, 238, 0.92));
        color: var(--ink);
        border-radius: 999px;
        font: inherit;
        cursor: pointer;
        transition: transform 120ms ease, background 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
      }
      .chip-toggle:hover,
      .toolbar-button:hover,
      .preset-button:hover,
      .inline-button:hover,
      .basemap-button:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-sm);
      }
      .chip-toggle {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
      }
      .chip-toggle input { margin: 0; }
      .chip-count {
        padding: 3px 8px;
        border-radius: 999px;
        background: rgba(20, 33, 61, 0.08);
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
      }
      .chip-swatch,
      .legend-swatch {
        width: 12px;
        height: 12px;
        border-radius: 999px;
        display: inline-block;
        border: 1px solid rgba(20, 33, 61, 0.35);
      }
      .inline-actions,
      .preset-row,
      .topbar-row,
      .map-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }
      .basemap-switch {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
      }
      .inline-actions { margin-top: 12px; }
      .inline-button,
      .preset-button,
      .toolbar-button,
      .basemap-button {
        padding: 10px 14px;
        font-size: 13px;
        font-weight: 600;
      }
      .basemap-button {
        display: grid;
        gap: 8px;
        padding: 10px;
        border-radius: 18px;
        text-align: left;
      }
      .basemap-preview {
        height: 36px;
        border-radius: 12px;
        border: 1px solid rgba(24, 37, 61, 0.10);
      }
      .basemap-preview--voyager {
        background:
          linear-gradient(135deg, rgba(196, 228, 248, 0.96), rgba(210, 236, 214, 0.88)),
          linear-gradient(90deg, transparent 0 22%, rgba(255, 255, 255, 0.28) 22% 25%, transparent 25% 100%);
      }
      .basemap-preview--light {
        background:
          linear-gradient(135deg, rgba(246, 244, 239, 0.96), rgba(231, 232, 234, 0.94)),
          linear-gradient(90deg, transparent 0 20%, rgba(196, 200, 207, 0.32) 20% 23%, transparent 23% 100%);
      }
      .basemap-preview--terrain {
        background:
          linear-gradient(135deg, rgba(220, 233, 213, 0.98), rgba(191, 208, 170, 0.90)),
          linear-gradient(90deg, transparent 0 24%, rgba(110, 133, 87, 0.20) 24% 27%, transparent 27% 100%);
      }
      .basemap-title {
        display: block;
        font-size: 12px;
        font-weight: 700;
      }
      .basemap-copy {
        display: block;
        color: var(--muted);
        font-size: 11px;
        line-height: 1.5;
      }
      .topbar-context {
        display: grid;
        gap: 6px;
        min-width: 0;
      }
      .topbar-label {
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .topbar-title-row {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 10px;
      }
      .topbar-title {
        font-size: 16px;
        font-weight: 700;
      }
      .topbar-state-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(20, 33, 61, 0.08);
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }
      .inline-button.is-primary,
      .toolbar-button.is-primary,
      .preset-button.is-active,
      .basemap-button.is-active {
        background: linear-gradient(135deg, #1d4ed8, #2563eb);
        color: white;
        border-color: transparent;
      }
      .field-label {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 8px;
      }
      .range-input,
      .search-input { width: 100%; }
      .range-input { accent-color: var(--gold); }
      .search-shell {
        position: relative;
      }
      .search-input {
        padding: 12px 14px;
        border-radius: 14px;
        border: 1px solid rgba(20, 33, 61, 0.14);
        background: rgba(255, 255, 255, 0.95);
        color: var(--ink);
        font: inherit;
        padding-right: 46px;
      }
      .search-clear {
        position: absolute;
        top: 50%;
        right: 10px;
        transform: translateY(-50%);
        appearance: none;
        border: 0;
        background: rgba(20, 33, 61, 0.08);
        color: var(--muted);
        width: 28px;
        height: 28px;
        border-radius: 999px;
        font: inherit;
        font-size: 16px;
        cursor: pointer;
      }
      .search-input:focus {
        outline: 2px solid rgba(37, 99, 235, 0.25);
        border-color: rgba(37, 99, 235, 0.40);
      }
      .search-meta {
        margin: 10px 0 12px;
        color: var(--muted);
        font-size: 12px;
      }
      .time-density {
        display: grid;
        gap: 10px;
        margin: 14px 0 10px;
      }
      .time-density-bars {
        display: grid;
        grid-template-columns: repeat(12, minmax(0, 1fr));
        align-items: end;
        gap: 6px;
        min-height: 84px;
      }
      .time-density-bar {
        min-height: 12px;
        border-radius: 999px 999px 4px 4px;
        background: rgba(24, 37, 61, 0.12);
      }
      .time-density-bar.is-active-window {
        background: linear-gradient(180deg, rgba(31, 94, 216, 0.92), rgba(14, 122, 114, 0.82));
      }
      .time-density-labels {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        color: var(--muted);
        font-size: 11px;
      }
      .search-results,
      .summary-list,
      .legend-list,
      .layer-stack,
      .filter-chip-list {
        display: grid;
        gap: 10px;
      }
      .coverage-matrix {
        display: grid;
        gap: 10px;
      }
      .coverage-row {
        display: grid;
        gap: 10px;
        padding: 14px;
        border: 1px solid rgba(20, 33, 61, 0.10);
        border-radius: 18px;
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.48), rgba(255, 255, 255, 0)),
          rgba(255, 255, 255, 0.74);
      }
      .coverage-row-head {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: baseline;
      }
      .coverage-row-head strong {
        font-size: 14px;
      }
      .coverage-row-head span {
        color: var(--muted);
        font-size: 12px;
      }
      .coverage-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .coverage-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 9px;
        border-radius: 999px;
        background: rgba(24, 37, 61, 0.08);
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
      }
      .search-result,
      .summary-item,
      .layer-card {
        padding: 12px 14px;
        border: 1px solid rgba(20, 33, 61, 0.10);
        border-radius: 16px;
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.52), rgba(255, 255, 255, 0)),
          rgba(255, 255, 255, 0.76);
      }
      .search-result {
        cursor: pointer;
        width: 100%;
        text-align: left;
        appearance: none;
        font: inherit;
        color: inherit;
      }
      .search-result strong,
      .layer-card strong { display: block; font-size: 14px; }
      .search-result span,
      .layer-card span,
      .summary-item span {
        display: block;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.55;
      }
      .search-result-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
      }
      .search-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 8px;
        border-radius: 999px;
        background: rgba(20, 33, 61, 0.08);
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
      }
      .layer-card-top {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: flex-start;
      }
      .layer-card.is-enabled {
        border-color: rgba(37, 99, 235, 0.22);
        box-shadow: 0 16px 34px rgba(31, 94, 216, 0.10);
      }
      .layer-card-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
      }
      .layer-card-title {
        display: flex;
        align-items: center;
        gap: 10px;
      }
      .layer-card-text {
        display: grid;
        gap: 4px;
      }
      .layer-card-text strong {
        margin: 0;
      }
      .layer-swatch-stack {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        border-radius: 999px;
        border: 1px solid rgba(20, 33, 61, 0.25);
        flex: 0 0 auto;
      }
      .layer-state-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 8px;
        border-radius: 999px;
        background: rgba(20, 33, 61, 0.08);
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }
      .layer-card.is-enabled .layer-state-pill {
        background: rgba(37, 99, 235, 0.12);
        color: var(--blue);
      }
      .layer-card label {
        display: flex;
        gap: 10px;
        align-items: flex-start;
        width: 100%;
      }
      .layer-card input { margin-top: 3px; }
      .filter-chip-list {
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      }
      .filter-chip {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        padding: 12px 14px;
        border: 1px solid rgba(20, 33, 61, 0.10);
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.8);
      }
      .filter-chip strong {
        display: block;
        margin-bottom: 4px;
        font-size: 13px;
      }
      .filter-chip span {
        display: block;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.5;
      }
      .filter-chip-remove {
        appearance: none;
        border: 0;
        background: transparent;
        color: var(--muted);
        font: inherit;
        font-size: 18px;
        line-height: 1;
        cursor: pointer;
      }
      .filter-chip-empty {
        padding: 12px 14px;
        border: 1px dashed rgba(20, 33, 61, 0.16);
        border-radius: 16px;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.6;
        background: rgba(255, 255, 255, 0.54);
      }
      .layer-group {
        display: grid;
        gap: 10px;
      }
      .layer-group.is-collapsed .layer-group-stack {
        display: none;
      }
      .layer-group-head {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: baseline;
        padding: 0 2px;
      }
      .layer-group-head-main {
        display: grid;
        gap: 4px;
        min-width: 0;
      }
      .layer-group-head h3 {
        margin: 0;
        font-size: 13px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }
      .layer-group-head span {
        color: var(--muted);
        font-size: 11px;
      }
      .layer-group-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
      }
      .layer-group-button {
        appearance: none;
        border: 1px solid rgba(24, 37, 61, 0.10);
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.82);
        color: var(--muted);
        padding: 6px 10px;
        font: inherit;
        font-size: 11px;
        font-weight: 700;
        cursor: pointer;
      }
      .layer-group-stack {
        display: grid;
        gap: 10px;
      }
      .layer-meta {
        margin-top: 8px;
        display: grid;
        gap: 6px;
      }
      .layer-meta span {
        display: block;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.5;
      }
      .layer-badge {
        padding: 5px 10px;
        border-radius: 999px;
        background: rgba(20, 33, 61, 0.08);
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }
      .map-topbar {
        position: absolute;
        top: 16px;
        left: max(452px, 26vw);
        right: 16px;
        z-index: 1100;
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: center;
        padding: 12px;
        border-radius: 20px;
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.50), rgba(255, 255, 255, 0)),
          var(--surface);
      }
      .map-topbar-main {
        display: flex;
        align-items: center;
        gap: 14px;
        min-width: 0;
      }
      .sidebar.is-collapsed ~ .map-stage .map-topbar { left: 16px; }
      .floating-legend {
        position: absolute;
        right: 16px;
        bottom: 88px;
        z-index: 1100;
        width: min(300px, calc(100vw - 32px));
        max-height: min(42vh, 360px);
        overflow: auto;
        padding: 16px;
        border-radius: 20px;
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.50), rgba(255, 255, 255, 0)),
          var(--surface);
      }
      .legend-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 10px;
      }
      .legend-title { font-size: 13px; font-weight: 700; }
      .legend-toggle {
        appearance: none;
        border: 1px solid rgba(20, 33, 61, 0.12);
        background: rgba(255, 255, 255, 0.84);
        color: var(--muted);
        border-radius: 999px;
        padding: 6px 10px;
        font: inherit;
        font-size: 11px;
        font-weight: 700;
        cursor: pointer;
      }
      .legend-body.is-collapsed {
        display: none;
      }
      .legend-group {
        display: grid;
        gap: 8px;
      }
      .legend-group + .legend-group {
        margin-top: 12px;
      }
      .legend-group-label {
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .legend-list { margin-bottom: 0; }
      .legend-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.5;
      }
      .density-ramp { display: grid; gap: 8px; }
      .density-bar {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        overflow: hidden;
        border-radius: 999px;
        height: 12px;
      }
      .density-bar span:nth-child(1) { background: #fee2e2; }
      .density-bar span:nth-child(2) { background: #fca5a5; }
      .density-bar span:nth-child(3) { background: #f87171; }
      .density-bar span:nth-child(4) { background: #ef4444; }
      .density-bar span:nth-child(5) { background: #b91c1c; }
      .density-bar span:nth-child(6) { background: #7f1d1d; }
      .density-labels {
        display: flex;
        justify-content: space-between;
        color: var(--muted);
        font-size: 11px;
      }
      .map-status {
        position: absolute;
        right: 16px;
        bottom: 24px;
        z-index: 1100;
        display: grid;
        grid-template-columns: repeat(4, minmax(0, auto));
        gap: 16px;
        padding: 12px 16px;
        border-radius: 22px;
        color: var(--muted);
        font-size: 12px;
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.46), rgba(255, 255, 255, 0)),
          var(--surface);
      }
      .status-pill {
        display: grid;
        gap: 3px;
        min-width: 92px;
      }
      .status-pill-label {
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .status-pill-value {
        color: var(--ink-soft);
        font-size: 12px;
        font-weight: 700;
      }
      .focus-card {
        position: absolute;
        left: 16px;
        bottom: 24px;
        z-index: 1100;
        width: min(360px, calc(100vw - 32px));
        padding: 16px;
        border-radius: 22px;
      }
      .focus-card[hidden] {
        display: none;
      }
      .focus-card-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 10px;
      }
      .focus-card-kicker {
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .focus-card-title {
        margin: 4px 0 0;
        font-size: 16px;
        font-weight: 700;
        line-height: 1.3;
      }
      .focus-card-subtitle {
        margin: 6px 0 0;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.5;
      }
      .focus-close {
        flex: 0 0 auto;
        min-width: auto;
        padding: 8px 10px;
      }
      .focus-meta {
        display: grid;
        gap: 8px;
        margin: 12px 0 14px;
      }
      .focus-meta-row {
        display: grid;
        grid-template-columns: minmax(88px, auto) minmax(0, 1fr);
        gap: 10px;
        padding: 10px 12px;
        border: 1px solid rgba(20, 33, 61, 0.10);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.78);
      }
      .focus-meta-label {
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }
      .focus-meta-value {
        font-size: 12px;
        line-height: 1.5;
        word-break: break-word;
      }
      .focus-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }
      .focus-nav {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 10px;
      }
      .focus-link {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
      }
      .empty-state {
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        z-index: 1150;
        width: min(460px, calc(100vw - 48px));
        padding: 18px 20px;
        border: 1px solid var(--surface-edge);
        border-radius: 22px;
        background: rgba(255, 252, 247, 0.96);
        box-shadow: var(--shadow-lg);
        text-align: center;
      }
      .empty-state strong {
        display: block;
        margin-bottom: 8px;
        font-size: 16px;
      }
      .empty-state span {
        display: block;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.6;
      }
      .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
      }
      button:focus-visible,
      input:focus-visible,
      .search-result:focus-visible {
        outline: 3px solid rgba(37, 99, 235, 0.28);
        outline-offset: 2px;
      }
      .leaflet-popup-content-wrapper { border-radius: 18px; }
      .popup-grid { display: grid; gap: 6px; font-size: 13px; }
      .popup-grid strong { display: inline-block; min-width: 96px; }
      .cluster-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 42px;
        height: 42px;
        border-radius: 999px;
        color: white;
        border: 3px solid rgba(255, 255, 255, 0.88);
        font-weight: 700;
        box-shadow: 0 10px 24px rgba(20, 33, 61, 0.20);
      }
      @media (max-width: 1080px) {
        .sidebar {
          width: min(400px, calc(100vw - 24px));
          top: 12px;
          left: 12px;
          bottom: auto;
          max-height: min(72vh, 920px);
        }
        .map-topbar {
          top: 12px;
          left: calc(min(400px, calc(100vw - 24px)) + 24px);
          right: 12px;
          bottom: auto;
        }
        .sidebar.is-collapsed ~ .map-stage .map-topbar {
          left: 12px;
        }
        .floating-legend {
          right: 12px;
          bottom: 76px;
        }
        .map-status {
          left: 12px;
          right: 12px;
          bottom: 12px;
          border-radius: 18px;
          grid-template-columns: repeat(4, minmax(0, 1fr));
        }
        .focus-card {
          left: 12px;
          bottom: 76px;
          width: min(340px, calc(100vw - 24px));
        }
      }
      @media (max-width: 900px) {
        body.has-mobile-panel-open .map-topbar,
        body.has-mobile-panel-open .floating-legend,
        body.has-mobile-panel-open .map-status {
          filter: blur(1px);
        }
        .sidebar {
          position: fixed;
          left: 10px;
          right: 10px;
          top: auto;
          bottom: 10px;
          width: auto;
          max-height: min(68vh, 720px);
        }
        .sidebar.is-collapsed {
          transform: translateY(calc(100% + 24px));
        }
        .sidebar-inner {
          padding: 18px;
          border-radius: 24px;
        }
        .mobile-panel-close {
          display: inline-flex;
        }
        .map-topbar {
          top: 10px;
          left: 10px;
          right: 10px;
          bottom: auto;
          padding: 10px;
          border-radius: 18px;
          flex-direction: column;
          align-items: stretch;
        }
        .map-topbar-main {
          justify-content: space-between;
        }
        .topbar-row,
        .map-actions {
          justify-content: space-between;
        }
        .basemap-switch {
          grid-template-columns: 1fr;
        }
        .floating-legend {
          right: 10px;
          bottom: 76px;
          width: min(248px, calc(100vw - 20px));
          max-height: min(34vh, 260px);
          padding: 12px;
          border-radius: 18px;
        }
        .sidebar:not(.is-collapsed) ~ .map-stage .floating-legend,
        .sidebar:not(.is-collapsed) ~ .map-stage .map-status,
        .sidebar:not(.is-collapsed) ~ .map-stage .focus-card {
          opacity: 0;
          pointer-events: none;
          transform: translateY(12px);
        }
        .focus-card {
          left: 10px;
          right: 10px;
          bottom: 76px;
          width: auto;
          transition: opacity 160ms ease, transform 160ms ease;
        }
        .map-status {
          left: 10px;
          right: 10px;
          bottom: 10px;
          border-radius: 18px;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          transition: opacity 160ms ease, transform 160ms ease;
        }
      }
      @media (max-width: 640px) {
        .sidebar {
          left: 8px;
          right: 8px;
          bottom: 8px;
          max-height: min(72vh, 760px);
        }
        .sidebar-inner { padding: 16px; }
        .workspace-brief-grid {
          grid-template-columns: 1fr;
        }
        .stats-grid { grid-template-columns: 1fr 1fr; }
        .map-topbar {
          left: 8px;
          right: 8px;
          top: 8px;
        }
        .map-topbar-main {
          flex-direction: column;
          align-items: stretch;
          gap: 10px;
        }
        .help-grid {
          grid-template-columns: 1fr;
        }
        .topbar-title {
          font-size: 14px;
        }
        .topbar-state-pill {
          width: fit-content;
        }
        .floating-legend {
          right: 8px;
          bottom: 72px;
          width: min(220px, calc(100vw - 16px));
          padding: 10px;
        }
        .focus-card {
          left: 8px;
          right: 8px;
          bottom: 72px;
        }
        .focus-meta-row {
          grid-template-columns: 1fr;
          gap: 4px;
        }
        .legend-title {
          font-size: 12px;
          margin-bottom: 8px;
        }
        .legend-item {
          gap: 8px;
          font-size: 11px;
        }
        .map-status {
          left: 8px;
          right: 8px;
          bottom: 8px;
          gap: 10px;
          padding: 10px 12px;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          font-size: 11px;
        }
        .inline-button,
        .preset-button,
        .toolbar-button,
        .basemap-button {
          padding: 9px 12px;
          font-size: 12px;
        }
      }
    </style>
  </head>
  <body>
    <div class="app-shell">
      <aside id="sidebar" class="sidebar">
        <div class="sidebar-inner">
          <div class="sidebar-header">
            <div class="sidebar-heading">
              <span class="eyebrow">Nordic Multi-Evidence Map</span>
              <h1>__TITLE__</h1>
              <p class="lede">
                A shared decision map for ancient DNA, pollen, environmental archaeology, and archaeology context.
                AADR `__VERSION__` is one input to this view, not the whole map. Use the filters, search, time-window, and acceptance-distance controls to compare evidence in one workspace.
              </p>
            </div>
            <button id="mobile-panel-close" class="toolbar-button mobile-panel-close" type="button">Close</button>
          </div>
          <section class="workspace-brief">
            <div class="workspace-brief-head">
              <strong>Workspace Brief</strong>
              <span id="workspace-brief-state" aria-live="polite">Loading live map state</span>
            </div>
            <div class="workspace-brief-grid">
              <div class="workspace-brief-card">
                <span class="workspace-brief-label">Geography</span>
                <span id="workspace-brief-geography" class="workspace-brief-value">Loading country scope</span>
              </div>
              <div class="workspace-brief-card">
                <span class="workspace-brief-label">Evidence Stack</span>
                <span id="workspace-brief-stack" class="workspace-brief-value">Loading evidence stack</span>
              </div>
              <div class="workspace-brief-card">
                <span class="workspace-brief-label">Time Window</span>
                <span id="workspace-brief-time" class="workspace-brief-value">__INITIAL_TIME_START_BP__-__INITIAL_TIME_END_BP__ BP</span>
              </div>
            </div>
            <div id="workspace-brief-note" class="workspace-brief-note">The initial HTML waits for live layer and filter state before describing the current workspace.</div>
          </section>
          <section class="stats-grid">
            <div class="stat-card"><span class="stat-label">Visible Points</span><strong class="stat-value" id="stat-visible-points">--</strong><span id="stat-visible-points-note" class="stat-support">Computed after the map loads enabled point layers.</span></div>
            <div class="stat-card"><span class="stat-label">Visible Overlays</span><strong class="stat-value" id="stat-visible-layers">--</strong><span id="stat-visible-layers-note" class="stat-support">Computed after polygon and boundary overlays initialize.</span></div>
            <div class="stat-card"><span class="stat-label">Active Countries</span><strong class="stat-value" id="stat-visible-countries">--</strong><span id="stat-visible-countries-note" class="stat-support">Derived from the current country filter state.</span></div>
            <div class="stat-card"><span class="stat-label">Acceptance Radius</span><strong class="stat-value" id="stat-radius">--</strong><span id="stat-radius-note" class="stat-support">Derived from the active diameter setting after initialization.</span></div>
            <div class="stat-card"><span class="stat-label">AADR Release</span><strong class="stat-value stat-value--compact">__VERSION__</strong><span class="stat-support">Primary evidence release loaded into this workspace.</span></div>
            <div class="stat-card"><span class="stat-label">Context Sources</span><strong class="stat-value stat-value--compact" id="stat-context-sources">--</strong><span id="stat-context-sources-note" class="stat-support">Counted from contextual layers that are present in this bundle.</span></div>
          </section>
          <nav id="section-nav" class="section-nav" aria-label="Sidebar sections">
            <button class="section-nav-button is-active" type="button" data-section-target="scope-panel">Scope</button>
            <button class="section-nav-button" type="button" data-section-target="coverage-panel">Coverage</button>
            <button class="section-nav-button" type="button" data-section-target="country-panel">Countries</button>
            <button class="section-nav-button" type="button" data-section-target="layer-panel">Layers</button>
            <button class="section-nav-button" type="button" data-section-target="filters-panel">Filters</button>
            <button class="section-nav-button" type="button" data-section-target="search-panel">Search</button>
            <button class="section-nav-button" type="button" data-section-target="time-panel">Time</button>
            <button class="section-nav-button" type="button" data-section-target="distance-panel">Distance</button>
            <button class="section-nav-button" type="button" data-section-target="active-panel">State</button>
          </nav>
          <div class="section-stack">
            <section id="scope-panel" class="panel-card">
              <div class="section-head"><h2>Map Scope</h2><span>What is included</span></div>
              <p class="panel-copy">This map combines one primary evidence layer with environmental and archaeological context. Coverage is not identical across sources, so every layer card states its geographic scope.</p>
              <div id="scope-summary" class="summary-list"></div>
            </section>
            <section id="coverage-panel" class="panel-card">
              <div class="section-head"><h2>Source Coverage</h2><span id="coverage-summary" aria-live="polite">Dataset scope</span></div>
              <p class="panel-copy">This matrix keeps geographic and geometry scope visible across sources so users do not mistake Sweden-only overlays for Nordic-wide evidence or confuse points with polygon summaries.</p>
              <div id="coverage-matrix" class="coverage-matrix"></div>
            </section>
            <section id="country-panel" class="panel-card">
              <div class="section-head"><h2>Country Filters</h2><span id="country-summary" aria-live="polite">All countries visible</span></div>
              <p class="panel-copy">These filters apply to every layer that carries country metadata. RAÄ archaeology density is Sweden-only and will disappear automatically when Sweden is excluded.</p>
              <div id="country-filters" class="chip-grid"></div>
              <div class="inline-actions">
                <button id="countries-all" class="inline-button is-primary" type="button">Show all</button>
                <button id="countries-none" class="inline-button" type="button">Hide all</button>
                <button id="countries-fit" class="inline-button" type="button">Fit selected countries</button>
                <button id="restore-defaults" class="inline-button" type="button">Restore defaults</button>
              </div>
            </section>
            <section id="layer-panel" class="panel-card">
              <div class="section-head"><h2>Research Layers</h2><span id="layer-summary" aria-live="polite">All layers enabled</span></div>
              <p class="panel-copy">Layers are grouped by role so the map separates primary evidence, environmental context, archaeology context, and orientation aids.</p>
              <div class="inline-actions" style="margin-top: 0; margin-bottom: 14px;">
                <button class="inline-button" type="button" data-layer-preset="evidence">Evidence only</button>
                <button class="inline-button" type="button" data-layer-preset="context">Context stack</button>
                <button class="inline-button" type="button" data-layer-preset="orientation">Map framing</button>
                <button class="inline-button is-primary" type="button" data-layer-preset="all">All layers</button>
              </div>
              <div id="layer-filters" class="layer-stack"></div>
            </section>
            <section id="filters-panel" class="panel-card">
              <div class="section-head"><h2>Active Filters</h2><span id="filter-chip-count" aria-live="polite">Defaults</span></div>
              <p class="panel-copy">This section surfaces only the filter groups that currently differ from the default map state. Remove a chip to reset that part of the view without disturbing the rest.</p>
              <div id="filter-chips" class="filter-chip-list"></div>
            </section>
            <section id="search-panel" class="panel-card">
              <div class="section-head"><h2>Search Visible Records</h2><span id="search-count" aria-live="polite">0 matches</span></div>
              <label class="sr-only" for="search-input">Search visible records</label>
              <div class="search-shell">
                <input id="search-input" class="search-input" type="search" placeholder="Search by sample ID, locality, site name, or source" aria-describedby="search-meta">
                <button id="search-clear" class="search-clear" type="button" aria-label="Clear search" hidden>×</button>
              </div>
              <div id="search-meta" class="search-meta">Search only scans records that are visible under the current country and layer filters. Press Enter to jump to the first visible match.</div>
              <div id="search-results" class="search-results"></div>
            </section>
            <section id="time-panel" class="panel-card">
              <div class="section-head"><h2>Time Window</h2><span id="time-window-value">__INITIAL_TIME_START_BP__-__INITIAL_TIME_END_BP__ BP</span></div>
              <div class="field-label"><span>Window start (years BP)</span><span id="time-start-value">__INITIAL_TIME_START_BP__ BP</span></div>
              <label class="sr-only" for="time-start-slider">Time window start in years BP</label>
              <input id="time-start-slider" class="range-input" type="range" min="__TIME_MIN_BP__" max="__TIME_MAX_BP__" step="1" value="__INITIAL_TIME_START_BP__">
              <div class="field-label" style="margin-top: 16px;"><span>Window interval</span><span id="time-interval-value">__INITIAL_TIME_INTERVAL__ years</span></div>
              <label class="sr-only" for="time-interval-slider">Time window interval in years</label>
              <input id="time-interval-slider" class="range-input" type="range" min="1" max="__TIME_INTERVAL_MAX__" step="1" value="__INITIAL_TIME_INTERVAL__">
              <div class="preset-row" style="margin-top: 12px;">
                <button class="preset-button is-active" type="button" data-time-interval="100">100 years</button>
                <button class="preset-button" type="button" data-time-interval="500">500 years</button>
                <button class="preset-button" type="button" data-time-interval="1000">1000 years</button>
                <button class="preset-button" type="button" data-time-interval="full">Full span</button>
              </div>
              <div id="time-record-count" class="search-meta">Calculating dated records in the active BP window.</div>
              <div class="time-density">
                <div id="time-density-bars" class="time-density-bars"></div>
                <div class="time-density-labels"><span>Earlier BP</span><span>Later BP</span></div>
              </div>
              <div id="time-help" class="search-meta">Point records with `Date mean in BP` are filtered to the active window. Default interval is `100 years` and can be adjusted.</div>
            </section>
            <section id="distance-panel" class="panel-card">
              <div class="section-head"><h2>Acceptance Distance</h2><span id="diameter-value">__INITIAL_DIAMETER__ km diameter</span></div>
              <div class="field-label"><span>Search radius around visible point layers</span><span id="radius-value">__INITIAL_RADIUS__ km</span></div>
              <label class="sr-only" for="diameter-slider">Acceptance diameter in kilometers</label>
              <input id="diameter-slider" class="range-input" type="range" min="0" max="100" step="5" value="__INITIAL_DIAMETER__" aria-describedby="distance-help">
              <div class="preset-row" style="margin-top: 12px;">
                <button class="preset-button" type="button" data-km="0">0 km</button>
                <button class="preset-button" type="button" data-km="10">10 km</button>
                <button class="preset-button is-active" type="button" data-km="20">20 km</button>
                <button class="preset-button" type="button" data-km="30">30 km</button>
                <button class="preset-button" type="button" data-km="50">50 km</button>
              </div>
              <div id="distance-help" class="search-meta">Distance circles are available only for point layers. Set to `0 km` to hide acceptance circles everywhere.</div>
              <div class="field-label" style="margin-top: 16px;"><span>Archaeology density opacity</span><span id="density-opacity-value">60%</span></div>
              <label class="sr-only" for="density-opacity-slider">Archaeology density opacity</label>
              <input id="density-opacity-slider" class="range-input" type="range" min="0" max="100" step="5" value="60">
            </section>
            <section id="active-panel" class="panel-card">
              <div class="section-head"><h2>Active View</h2><span>Live provenance</span></div>
              <div id="active-summary" class="summary-list"></div>
            </section>
          </div>
        </div>
      </aside>
      <button id="mobile-scrim" class="mobile-scrim" type="button" aria-label="Close filters" aria-hidden="true"></button>
      <main class="map-stage">
        <div class="map-topbar">
          <div class="map-topbar-main">
            <div class="topbar-context">
              <span class="topbar-label">Research Workspace</span>
              <div class="topbar-title-row">
                <span class="topbar-title">__TITLE__ map</span>
                <span id="topbar-state-pill" class="topbar-state-pill">Loading live map state</span>
              </div>
            </div>
            <div class="topbar-row">
              <button id="panel-toggle" class="toolbar-button" type="button">Hide panel</button>
              <div class="basemap-switch">
                <button class="basemap-button is-active" type="button" data-basemap="voyager"><span class="basemap-preview basemap-preview--voyager"></span><span class="basemap-title">Voyager</span><span class="basemap-copy">Balanced roads, labels, and water detail.</span></button>
                <button class="basemap-button" type="button" data-basemap="light"><span class="basemap-preview basemap-preview--light"></span><span class="basemap-title">Light</span><span class="basemap-copy">Minimal contrast for evidence-first inspection.</span></button>
                <button class="basemap-button" type="button" data-basemap="terrain"><span class="basemap-preview basemap-preview--terrain"></span><span class="basemap-title">Terrain</span><span class="basemap-copy">Relief-focused context for landform reading.</span></button>
              </div>
            </div>
          </div>
          <div class="map-actions">
            <button id="fit-active" class="toolbar-button is-primary" type="button">Fit active</button>
            <button id="reset-view" class="toolbar-button" type="button">Reset view</button>
            <button id="copy-link" class="toolbar-button" type="button">Copy link</button>
            <button id="help-toggle" class="toolbar-button" type="button">Help</button>
            <button id="fullscreen-toggle" class="toolbar-button" type="button">Fullscreen</button>
          </div>
        </div>
        <div id="map" aria-label="__TITLE__ research map"></div>
        <div id="empty-state" class="empty-state" hidden>
          <strong>No visible records</strong>
          <span>Change the country filters, re-enable one or more layers, or restore the default map state.</span>
        </div>
        <div id="floating-legend" class="floating-legend">
          <div class="legend-head">
            <div class="legend-title">Legend</div>
            <button id="legend-toggle" class="legend-toggle" type="button">Collapse</button>
          </div>
          <div id="legend-body" class="legend-body">
            <div id="legend-items" class="legend-list"></div>
            <div id="density-ramp" class="density-ramp">
              <div class="legend-item"><span class="legend-swatch" style="background: rgba(37, 99, 235, 0.10); border-color: rgba(37, 99, 235, 0.45);"></span><span>Acceptance circles use semi-transparent fills so overlap remains visible.</span></div>
              <div class="legend-item"><span class="legend-swatch" style="background: rgba(239, 68, 68, 0.22); border-color: #7f1d1d;"></span><span>RAÄ archaeology density shows Swedish `Fornlämning` counts in 1° grid cells.</span></div>
              <div class="density-bar"><span></span><span></span><span></span><span></span><span></span><span></span></div>
              <div class="density-labels"><span>Lower density</span><span>Higher density</span></div>
            </div>
          </div>
        </div>
        <section id="focus-card" class="focus-card" hidden aria-live="polite">
          <div class="focus-card-head">
            <div>
              <div class="focus-card-kicker">Focused Record</div>
              <h2 id="focus-title" class="focus-card-title">No record selected</h2>
              <p id="focus-subtitle" class="focus-card-subtitle">Choose a point, polygon, or search result to keep its details visible while you continue navigating the map.</p>
            </div>
            <button id="focus-close" class="toolbar-button focus-close" type="button">Clear</button>
          </div>
          <div id="focus-meta" class="focus-meta"></div>
          <div class="focus-nav">
            <button id="focus-previous" class="toolbar-button" type="button">Previous</button>
            <button id="focus-next" class="toolbar-button" type="button">Next</button>
          </div>
          <div class="focus-actions">
            <button id="focus-zoom" class="toolbar-button is-primary" type="button">Zoom to record</button>
            <a id="focus-source-link" class="toolbar-button focus-link" href="#" target="_blank" rel="noreferrer">Open source</a>
          </div>
        </section>
        <div class="map-status">
          <div class="status-pill"><span class="status-pill-label">Zoom</span><span id="zoom-readout" class="status-pill-value">--</span></div>
          <div class="status-pill"><span class="status-pill-label">Center</span><span id="center-readout" class="status-pill-value">--</span></div>
          <div class="status-pill"><span class="status-pill-label">Cursor</span><span id="cursor-readout" class="status-pill-value">Move over map</span></div>
          <div class="status-pill"><span class="status-pill-label">Selection</span><span id="selection-readout" class="status-pill-value">No selection</span></div>
        </div>
      </main>
    </div>
    <div id="help-dialog" class="help-dialog" hidden>
      <div class="help-dialog-card" role="dialog" aria-modal="true" aria-labelledby="help-title">
        <div class="help-dialog-head">
          <div>
            <span class="eyebrow">Workspace Guide</span>
            <h2 id="help-title">How to use this map</h2>
            <p>This shared map combines ancient DNA, pollen, archaeology, and orientation layers. These controls keep the interface learnable without leaving the map.</p>
          </div>
          <button id="help-close" class="toolbar-button" type="button">Close</button>
        </div>
        <div class="help-grid">
          <section class="help-card">
            <h3>Keyboard shortcuts</h3>
            <div class="help-list">
              <div class="help-row"><span class="help-key">?</span><span>Open this guide from anywhere in the report.</span></div>
              <div class="help-row"><span class="help-key">Esc</span><span>Close the guide, or close the mobile filter drawer when it is open.</span></div>
              <div class="help-row"><span class="help-key">Enter</span><span>Jump to the first visible match from the search field.</span></div>
            </div>
          </section>
          <section class="help-card">
            <h3>Recommended workflow</h3>
            <div class="help-list">
              <div class="help-row"><span class="help-key">1</span><span>Use the workspace brief and source coverage panel to understand the current evidence stack.</span></div>
              <div class="help-row"><span class="help-key">2</span><span>Narrow geography, time, and distance before inspecting individual records.</span></div>
              <div class="help-row"><span class="help-key">3</span><span>Use the focus card to keep one selected record visible while the map continues moving.</span></div>
            </div>
          </section>
        </div>
      </div>
    </div>
    <script src="__ASSET_BASE_PATH__/leaflet/leaflet.js"></script>
    <script src="__ASSET_BASE_PATH__/markercluster/leaflet.markercluster.js"></script>
    <script>
      const COUNTRIES = __COUNTRIES_JSON__;
      const POINT_LAYERS = __POINT_LAYERS_JSON__;
      const POLYGON_LAYERS = __POLYGON_LAYERS_JSON__;
      const INITIAL_BOUNDS = __BOUNDS_JSON__;
      const ALL_LAYERS = [...POINT_LAYERS, ...POLYGON_LAYERS];
      const DEFAULT_COUNTRIES = [...COUNTRIES];
      const DEFAULT_LAYER_KEYS = ALL_LAYERS.filter((layer) => layer.default_enabled !== false).map((layer) => layer.key);
      const TIME_MIN_BP = __TIME_MIN_BP__;
      const TIME_MAX_BP = __TIME_MAX_BP__;
      const TIME_HAS_DATA = __TIME_HAS_DATA__;
      const DEFAULT_TIME_START_BP = __INITIAL_TIME_START_BP__;
      const DEFAULT_TIME_INTERVAL_YEARS = __INITIAL_TIME_INTERVAL__;
      const TIME_INTERVAL_MAX = __TIME_INTERVAL_MAX__;
      const map = L.map('map', { preferCanvas: true, zoomControl: false });
      const basemaps = {
        voyager: L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', { attribution: '&copy; OpenStreetMap contributors &copy; CARTO', subdomains: 'abcd', maxZoom: 20 }),
        light: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; OpenStreetMap contributors &copy; CARTO', subdomains: 'abcd', maxZoom: 20 }),
        terrain: L.tileLayer('https://tile.opentopomap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors, SRTM &copy; OpenTopoMap', maxZoom: 17 })
      };
      basemaps.voyager.addTo(map);
      L.control.zoom({ position: 'bottomright' }).addTo(map);
      L.control.scale({ imperial: false }).addTo(map);
      map.createPane('pointPane').style.zIndex = 650;
      map.createPane('circlePane').style.zIndex = 500;
      map.createPane('polygonPane').style.zIndex = 420;
      map.createPane('boundaryPane').style.zIndex = 430;
      const circleLayerGroup = L.layerGroup().addTo(map);
      let renderedPointGroups = [];
      let renderedPolygonLayers = [];
      let visiblePointEntries = [];
      let highlightedPointEntry = null;
      const sidebar = document.getElementById('sidebar');
      const sidebarInner = document.querySelector('.sidebar-inner');
      const mobilePanelCloseButton = document.getElementById('mobile-panel-close');
      const mobileScrim = document.getElementById('mobile-scrim');
      const mobileLayoutQuery = window.matchMedia('(max-width: 900px)');
      const panelToggleButton = document.getElementById('panel-toggle');
      const helpToggleButton = document.getElementById('help-toggle');
      const helpDialog = document.getElementById('help-dialog');
      const helpCloseButton = document.getElementById('help-close');
      const legendBody = document.getElementById('legend-body');
      const legendToggleButton = document.getElementById('legend-toggle');
      const sectionNavButtons = Array.from(document.querySelectorAll('[data-section-target]'));
      const countryFilters = document.getElementById('country-filters');
      const layerFilters = document.getElementById('layer-filters');
      const legendItems = document.getElementById('legend-items');
      const scopeSummary = document.getElementById('scope-summary');
      const coverageSummary = document.getElementById('coverage-summary');
      const coverageMatrix = document.getElementById('coverage-matrix');
      const searchInput = document.getElementById('search-input');
      const searchClearButton = document.getElementById('search-clear');
      const searchResults = document.getElementById('search-results');
      const searchCount = document.getElementById('search-count');
      const workspaceBriefState = document.getElementById('workspace-brief-state');
      const workspaceBriefGeography = document.getElementById('workspace-brief-geography');
      const workspaceBriefStack = document.getElementById('workspace-brief-stack');
      const workspaceBriefTime = document.getElementById('workspace-brief-time');
      const workspaceBriefNote = document.getElementById('workspace-brief-note');
      const filterChips = document.getElementById('filter-chips');
      const filterChipCount = document.getElementById('filter-chip-count');
      const slider = document.getElementById('diameter-slider');
      const diameterValue = document.getElementById('diameter-value');
      const radiusValue = document.getElementById('radius-value');
      const timeStartSlider = document.getElementById('time-start-slider');
      const timeStartValue = document.getElementById('time-start-value');
      const timeIntervalSlider = document.getElementById('time-interval-slider');
      const timeIntervalValue = document.getElementById('time-interval-value');
      const timeWindowValue = document.getElementById('time-window-value');
      const timeRecordCount = document.getElementById('time-record-count');
      const timeDensityBars = document.getElementById('time-density-bars');
      const densityOpacitySlider = document.getElementById('density-opacity-slider');
      const densityOpacityValue = document.getElementById('density-opacity-value');
      const emptyState = document.getElementById('empty-state');
      const densityRamp = document.getElementById('density-ramp');
      const countrySummary = document.getElementById('country-summary');
      const layerSummary = document.getElementById('layer-summary');
      const activeSummary = document.getElementById('active-summary');
      const topbarStatePill = document.getElementById('topbar-state-pill');
      const focusCard = document.getElementById('focus-card');
      const focusTitle = document.getElementById('focus-title');
      const focusSubtitle = document.getElementById('focus-subtitle');
      const focusMeta = document.getElementById('focus-meta');
      const focusPreviousButton = document.getElementById('focus-previous');
      const focusNextButton = document.getElementById('focus-next');
      const focusZoomButton = document.getElementById('focus-zoom');
      const focusSourceLink = document.getElementById('focus-source-link');
      const focusCloseButton = document.getElementById('focus-close');
      const selectionReadout = document.getElementById('selection-readout');
      const zoomReadout = document.getElementById('zoom-readout');
      const centerReadout = document.getElementById('center-readout');
      const cursorReadout = document.getElementById('cursor-readout');
      const statVisiblePoints = document.getElementById('stat-visible-points');
      const statVisibleLayers = document.getElementById('stat-visible-layers');
      const statVisiblePointsNote = document.getElementById('stat-visible-points-note');
      const statVisibleLayersNote = document.getElementById('stat-visible-layers-note');
      const statVisibleCountries = document.getElementById('stat-visible-countries');
      const statVisibleCountriesNote = document.getElementById('stat-visible-countries-note');
      const statRadius = document.getElementById('stat-radius');
      const statRadiusNote = document.getElementById('stat-radius-note');
      const statContextSources = document.getElementById('stat-context-sources');
      const statContextSourcesNote = document.getElementById('stat-context-sources-note');
      function parseHashState() {
        const raw = window.location.hash.startsWith('#') ? window.location.hash.slice(1) : '';
        const params = new URLSearchParams(raw);
        return {
          countries: params.get('countries'),
          layers: params.get('layers'),
          diameter: params.get('diameter'),
          timeStart: params.get('time_start'),
          timeInterval: params.get('time_interval'),
          density: params.get('density'),
          basemap: params.get('basemap'),
          panel: params.get('panel'),
          legend: params.get('legend'),
        };
      }
      function normalizedSetFromList(raw, allowed, fallbackValues) {
        if (String(raw || '').trim() === 'none') return new Set();
        const allowedSet = new Set(allowed);
        const values = String(raw || '')
          .split(',')
          .map((value) => value.trim())
          .filter((value) => value && allowedSet.has(value));
        return new Set(values.length ? values : fallbackValues);
      }
      function clampTimeInterval(value) {
        return Math.max(1, Math.min(TIME_INTERVAL_MAX, Math.round(Number(value) || DEFAULT_TIME_INTERVAL_YEARS)));
      }
      function defaultPanelCollapsed() {
        return mobileLayoutQuery.matches;
      }
      function panelPreferenceFromHash() {
        const raw = window.location.hash.startsWith('#') ? window.location.hash.slice(1) : '';
        const panel = new URLSearchParams(raw).get('panel');
        if (panel === 'collapsed') return true;
        if (panel === 'open') return false;
        return null;
      }
      function clampTimeStart(value, intervalYears) {
        const maxStart = Math.max(TIME_MIN_BP, TIME_MAX_BP - intervalYears);
        return Math.max(TIME_MIN_BP, Math.min(maxStart, Math.round(Number(value) || DEFAULT_TIME_START_BP)));
      }
      function timeWindowEndBp() {
        return Math.min(TIME_MAX_BP, timeStartBp + timeIntervalYears);
      }
      function refreshTimeControls() {
        if (!TIME_HAS_DATA) {
          timeStartSlider.disabled = true;
          timeIntervalSlider.disabled = true;
          timeWindowValue.textContent = 'No BP dates available';
          timeStartValue.textContent = '--';
          timeIntervalValue.textContent = '--';
          return;
        }
        timeIntervalYears = clampTimeInterval(timeIntervalYears);
        timeStartBp = clampTimeStart(timeStartBp, timeIntervalYears);
        timeStartSlider.min = String(TIME_MIN_BP);
        timeStartSlider.max = String(Math.max(TIME_MIN_BP, TIME_MAX_BP - timeIntervalYears));
        timeStartSlider.value = String(timeStartBp);
        timeIntervalSlider.min = '1';
        timeIntervalSlider.max = String(TIME_INTERVAL_MAX);
        timeIntervalSlider.value = String(timeIntervalYears);
        const endBp = timeWindowEndBp();
        timeWindowValue.textContent = `${timeStartBp}-${endBp} BP`;
        timeStartValue.textContent = `${timeStartBp} BP`;
        timeIntervalValue.textContent = `${timeIntervalYears} years`;
      }
      const initialState = parseHashState();
      let activeCountries = normalizedSetFromList(initialState.countries, COUNTRIES, DEFAULT_COUNTRIES);
      let activeLayerKeys = normalizedSetFromList(initialState.layers, ALL_LAYERS.map((layer) => layer.key), DEFAULT_LAYER_KEYS);
      let timeIntervalYears = TIME_HAS_DATA ? clampTimeInterval(initialState.timeInterval) : DEFAULT_TIME_INTERVAL_YEARS;
      let timeStartBp = TIME_HAS_DATA ? clampTimeStart(initialState.timeStart, timeIntervalYears) : DEFAULT_TIME_START_BP;
      let densityOpacity = Math.max(0, Math.min(1, Number(initialState.density || '60') / 100 || 0.6));
      let currentBasemap = basemaps[initialState.basemap || ''] ? String(initialState.basemap) : 'voyager';
      let legendCollapsed = initialState.legend === 'collapsed';
      let collapsedLayerGroups = new Set();
      let focusState = null;
      const countryColors = {
        Sweden: { fill: '#2563eb', stroke: '#1d4ed8' },
        Norway: { fill: '#0f766e', stroke: '#115e59' },
        Finland: { fill: '#b45309', stroke: '#92400e' },
        Denmark: { fill: '#be123c', stroke: '#9f1239' }
      };
      function escapeHtml(value) {
        return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;');
      }
      function countryStyle(country) { return countryColors[country] || { fill: '#475569', stroke: '#1e293b' }; }
      function layerColor(layer) { return layer.style && layer.style.fill ? layer.style.fill : (layer.style && layer.style.stroke ? layer.style.stroke : '#475569'); }
      function layerUnit(layer) { if (layer.kind === 'density' || layer.kind === 'context-polygons') return 'cells'; if (layer.kind === 'country-boundaries') return 'countries'; return 'points'; }
      function layerGroupLabel(group) {
        return {
          'primary-evidence': 'Primary Evidence',
          'environmental-context': 'Environmental Context',
          'archaeology-context': 'Archaeology Context',
          'orientation': 'Orientation'
        }[group] || 'Other Layers';
      }
      function layerGroupSummary(group) {
        return {
          'primary-evidence': 'Core evidence used for ancient DNA site comparison.',
          'environmental-context': 'Pollen and environmental archaeology context layers.',
          'archaeology-context': 'Archaeological context layers and summarized national coverage.',
          'orientation': 'Reference layers used for framing and navigation.'
        }[group] || 'Supporting layers.';
      }
      function humanLayerList(keys) {
        return ALL_LAYERS
          .filter((layer) => keys.has(layer.key))
          .map((layer) => layer.label)
          .join(', ');
      }
      function syncPresetButtons() {
        document.querySelectorAll('[data-km]').forEach((button) => {
          button.classList.toggle('is-active', Number(button.dataset.km) === Number(slider.value));
        });
      }
      function syncTimePresetButtons() {
        document.querySelectorAll('[data-time-interval]').forEach((button) => {
          const preset = button.dataset.timeInterval;
          const active = preset === 'full' ? timeIntervalYears === TIME_INTERVAL_MAX : Number(preset) === Number(timeIntervalYears);
          button.classList.toggle('is-active', active);
        });
      }
      function updateSectionNav(activeSectionId) {
        sectionNavButtons.forEach((button) => {
          button.classList.toggle('is-active', button.dataset.sectionTarget === activeSectionId);
        });
      }
      function syncSectionNavWithScroll() {
        const cards = sectionNavButtons
          .map((button) => document.getElementById(button.dataset.sectionTarget))
          .filter(Boolean);
        if (!cards.length) return;
        let activeSectionId = cards[0].id;
        for (const card of cards) {
          if (card.offsetTop - sidebarInner.scrollTop <= 96) {
            activeSectionId = card.id;
          }
        }
        updateSectionNav(activeSectionId);
      }
      function updatePanelToggleLabel() {
        const collapsed = sidebar.classList.contains('is-collapsed');
        if (mobileLayoutQuery.matches) {
          panelToggleButton.textContent = collapsed ? 'Show filters' : 'Hide filters';
          return;
        }
        panelToggleButton.textContent = collapsed ? 'Show panel' : 'Hide panel';
      }
      function syncMobilePanelState() {
        const mobileOpen = mobileLayoutQuery.matches && !sidebar.classList.contains('is-collapsed');
        panelToggleButton.setAttribute('aria-expanded', String(!sidebar.classList.contains('is-collapsed')));
        panelToggleButton.setAttribute('aria-controls', 'sidebar');
        mobileScrim.classList.toggle('is-visible', mobileOpen);
        mobileScrim.setAttribute('aria-hidden', mobileOpen ? 'false' : 'true');
        document.body.classList.toggle('has-mobile-panel-open', mobileOpen);
      }
      function setPanelCollapsed(collapsed, persist = true) {
        sidebar.classList.toggle('is-collapsed', collapsed);
        updatePanelToggleLabel();
        syncMobilePanelState();
        window.setTimeout(() => map.invalidateSize(), 180);
        if (persist) syncHashState();
      }
      function setLegendCollapsed(collapsed, persist = true) {
        legendCollapsed = collapsed;
        legendBody.classList.toggle('is-collapsed', collapsed);
        legendToggleButton.textContent = collapsed ? 'Expand' : 'Collapse';
        if (persist) syncHashState();
      }
      function openHelpDialog() {
        helpDialog.hidden = false;
        document.body.classList.add('has-mobile-panel-open');
      }
      function closeHelpDialog() {
        helpDialog.hidden = true;
        syncMobilePanelState();
      }
      function syncHashState() {
        const params = new URLSearchParams();
        if (activeCountries.size !== COUNTRIES.length) params.set('countries', activeCountries.size ? [...activeCountries].join(',') : 'none');
        if (activeLayerKeys.size !== DEFAULT_LAYER_KEYS.length || DEFAULT_LAYER_KEYS.some((key) => !activeLayerKeys.has(key))) params.set('layers', activeLayerKeys.size ? [...activeLayerKeys].join(',') : 'none');
        if (Number(slider.value) !== __INITIAL_DIAMETER__) params.set('diameter', String(Number(slider.value)));
        if (TIME_HAS_DATA && timeStartBp !== DEFAULT_TIME_START_BP) params.set('time_start', String(timeStartBp));
        if (TIME_HAS_DATA && timeIntervalYears !== DEFAULT_TIME_INTERVAL_YEARS) params.set('time_interval', String(timeIntervalYears));
        if (Math.round(densityOpacity * 100) !== 60) params.set('density', String(Math.round(densityOpacity * 100)));
        if (currentBasemap !== 'voyager') params.set('basemap', currentBasemap);
        if (sidebar.classList.contains('is-collapsed') !== defaultPanelCollapsed()) {
          params.set('panel', sidebar.classList.contains('is-collapsed') ? 'collapsed' : 'open');
        }
        if (legendCollapsed) params.set('legend', 'collapsed');
        const nextHash = params.toString();
        const desiredHash = nextHash ? `#${nextHash}` : '';
        if (window.location.hash !== desiredHash) window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}${desiredHash}`);
      }
      function clearHighlightedPoint() {
        if (!highlightedPointEntry || !highlightedPointEntry.marker) return;
        const entry = highlightedPointEntry;
        entry.marker.setStyle({
          radius: entry.layer.key === 'aadr' ? 4.5 : 6,
          weight: 1.3,
          color: entry.layer.style.stroke,
          fillColor: entry.layer.style.fill,
          fillOpacity: 0.92,
        });
        highlightedPointEntry = null;
      }
      function highlightPointEntry(entry) {
        clearHighlightedPoint();
        if (!entry || !entry.marker) return;
        entry.marker.setStyle({
          radius: (entry.layer.key === 'aadr' ? 4.5 : 6) + 2,
          weight: 2.4,
          color: '#ffffff',
          fillColor: entry.layer.style.fill,
          fillOpacity: 1,
        });
        highlightedPointEntry = entry;
      }
      function setFocusState(nextState) {
        focusState = nextState;
        if (focusState && focusState.kind === 'point' && Number.isInteger(focusState.visiblePointIndex)) {
          highlightPointEntry(visiblePointEntries[focusState.visiblePointIndex] || null);
        } else {
          clearHighlightedPoint();
        }
        renderFocusCard();
      }
      function renderFocusCard() {
        const pointEntry = focusState && focusState.kind === 'point' && Number.isInteger(focusState.visiblePointIndex)
          ? visiblePointEntries[focusState.visiblePointIndex]
          : null;
        if (!focusState || !activeLayerKeys.has(focusState.layerKey) || (focusState.kind === 'point' && !pointEntry)) {
          focusCard.hidden = true;
          focusSourceLink.hidden = true;
          focusPreviousButton.disabled = true;
          focusNextButton.disabled = true;
          return;
        }
        focusCard.hidden = false;
        if (pointEntry) {
          highlightPointEntry(pointEntry);
        }
        focusTitle.textContent = focusState.title;
        focusSubtitle.textContent = focusState.subtitle;
        focusMeta.innerHTML = focusState.meta.map((row) => `<div class="focus-meta-row"><span class="focus-meta-label">${escapeHtml(row.label)}</span><span class="focus-meta-value">${escapeHtml(row.value)}</span></div>`).join('');
        focusSourceLink.hidden = !focusState.sourceUrl;
        focusSourceLink.href = focusState.sourceUrl || '#';
        const canStep = focusState.kind === 'point' && visiblePointEntries.length > 1;
        focusPreviousButton.disabled = !canStep;
        focusNextButton.disabled = !canStep;
      }
      function focusPointAtVisibleIndex(index) {
        const entry = visiblePointEntries[index];
        if (!entry) return;
        const meta = [
          { label: 'Layer', value: entry.layer.label },
          { label: 'Country', value: entry.feature.country || 'Unassigned' },
          { label: 'Coordinates', value: `${Number(entry.feature.latitude).toFixed(4)}, ${Number(entry.feature.longitude).toFixed(4)}` },
        ];
        if (entry.feature.time_year_bp !== null && entry.feature.time_year_bp !== undefined && entry.feature.time_year_bp !== '') {
          meta.splice(2, 0, { label: 'Date', value: `${entry.feature.time_year_bp} BP` });
        }
        setFocusState({
          kind: 'point',
          layerKey: entry.layer.key,
          visiblePointIndex: index,
          title: entry.feature.title || entry.layer.label,
          subtitle: entry.feature.subtitle || 'Point record',
          meta,
          sourceUrl: entry.feature.source_url || '',
          latitude: Number(entry.feature.latitude),
          longitude: Number(entry.feature.longitude),
        });
      }
      function renderScopeSummary() {
        const summaries = [
          `Primary evidence: ${POINT_LAYERS.find((layer) => layer.key === 'aadr')?.label || 'AADR'}`,
          `Environmental context: ${ALL_LAYERS.filter((layer) => layer.group === 'environmental-context').map((layer) => layer.source_name).join(', ') || 'none'}`,
          `Archaeology context: ${ALL_LAYERS.filter((layer) => layer.group === 'archaeology-context').map((layer) => layer.coverage_label).join(' ') || 'none'}`,
          `Orientation: ${ALL_LAYERS.filter((layer) => layer.group === 'orientation').map((layer) => layer.label).join(', ') || 'none'}`,
          TIME_HAS_DATA ? `AADR BP coverage: ${TIME_MIN_BP}-${TIME_MAX_BP}` : 'AADR BP coverage: no numeric BP years available'
        ];
        scopeSummary.innerHTML = summaries.map((item) => `<div class="summary-item"><span>${escapeHtml(item)}</span></div>`).join('');
      }
      function renderCoverageMatrix() {
        const groupedSources = [...new Set(ALL_LAYERS.map((layer) => layer.source_name || layer.label))].map((sourceName) => {
          const layers = ALL_LAYERS.filter((layer) => (layer.source_name || layer.label) === sourceName);
          return { sourceName, layers };
        });
        coverageSummary.textContent = `${groupedSources.length} tracked sources`;
        coverageMatrix.innerHTML = groupedSources.map(({ sourceName, layers }) => {
          const coverage = [...new Set(layers.map((layer) => layer.coverage_label || 'Map-wide coverage'))];
          const geometry = [...new Set(layers.map((layer) => layer.geometry_label || layerUnit(layer)))];
          const enabledCount = layers.filter((layer) => activeLayerKeys.has(layer.key)).length;
          return `<div class="coverage-row"><div class="coverage-row-head"><strong>${escapeHtml(sourceName)}</strong><span>${enabledCount}/${layers.length} layers enabled</span></div><div class="coverage-tags">${coverage.map((item) => `<span class="coverage-tag">${escapeHtml(item)}</span>`).join('')}${geometry.map((item) => `<span class="coverage-tag">${escapeHtml(item)}</span>`).join('')}</div></div>`;
        }).join('');
      }
      function renderTimeDensity() {
        if (!TIME_HAS_DATA) {
          timeDensityBars.innerHTML = '<div class="filter-chip-empty">No dated records are available for the current workspace.</div>';
          return;
        }
        const bins = 12;
        const span = Math.max(1, TIME_MAX_BP - TIME_MIN_BP);
        const bucketSize = Math.max(1, Math.ceil(span / bins));
        const counts = new Array(bins).fill(0);
        POINT_LAYERS
          .filter((layer) => activeLayerKeys.has(layer.key) && layer.applies_time_filter)
          .forEach((layer) => {
            layer.features.forEach((feature) => {
              const yearBp = Number(feature.time_year_bp);
              if (!Number.isFinite(yearBp)) return;
              if (feature.country && !activeCountries.has(feature.country)) return;
              const index = Math.min(bins - 1, Math.max(0, Math.floor((yearBp - TIME_MIN_BP) / bucketSize)));
              counts[index] += 1;
            });
          });
        const maxCount = Math.max(...counts, 1);
        const activeEnd = timeWindowEndBp();
        timeDensityBars.innerHTML = counts.map((count, index) => {
          const binStart = TIME_MIN_BP + (index * bucketSize);
          const binEnd = index === bins - 1 ? TIME_MAX_BP : Math.min(TIME_MAX_BP, binStart + bucketSize);
          const height = count > 0 ? Math.max(16, Math.round((count / maxCount) * 80)) : 12;
          const overlapsWindow = binEnd >= timeStartBp && binStart <= activeEnd;
          return `<div class="time-density-bar ${overlapsWindow ? 'is-active-window' : ''}" style="height:${height}px" title="${escapeHtml(`${count} dated records from ${binStart} to ${binEnd} BP`)}"></div>`;
        }).join('');
      }
      function renderWorkspaceBrief() {
        const activeGroups = [...new Set(ALL_LAYERS.filter((layer) => activeLayerKeys.has(layer.key)).map((layer) => layerGroupLabel(layer.group)))];
        const geographySummary = activeCountries.size === COUNTRIES.length
          ? 'All Nordic countries'
          : activeCountries.size
            ? [...activeCountries].join(', ')
            : 'No countries selected';
        const timeSummary = TIME_HAS_DATA
          ? `${timeStartBp}-${timeWindowEndBp()} BP`
          : 'No dated records';
        workspaceBriefState.textContent = filterChipCount.textContent === 'Defaults' ? 'Default map state' : `${filterChipCount.textContent} override map defaults`;
        workspaceBriefGeography.textContent = geographySummary;
        workspaceBriefStack.textContent = activeGroups.length ? activeGroups.join(' + ') : 'No active layers';
        workspaceBriefTime.textContent = timeSummary;
        workspaceBriefNote.textContent = TIME_HAS_DATA
          ? `${visiblePointEntries.length} visible point records sit inside the current evidence stack and BP window.`
          : `${visiblePointEntries.length} visible point records are available under the current layer and geography filters.`;
      }
      function renderCountryControls() {
        const pointCountsByCountry = Object.fromEntries(
          COUNTRIES.map((country) => [
            country,
            POINT_LAYERS
              .filter((layer) => activeLayerKeys.has(layer.key))
              .reduce((count, layer) => count + layer.features.filter((feature) => pointFeatureVisible(layer, feature) && feature.country === country).length, 0),
          ])
        );
        countryFilters.innerHTML = COUNTRIES.map((country) => {
          const style = countryStyle(country);
          const checked = activeCountries.has(country) ? 'checked' : '';
          return `<label class="chip-toggle"><input class="country-checkbox" type="checkbox" value="${escapeHtml(country)}" ${checked} aria-label="Toggle ${escapeHtml(country)}"><span class="chip-swatch" style="background:${escapeHtml(style.fill)};border-color:${escapeHtml(style.stroke)};"></span><span>${escapeHtml(country)}</span><span class="chip-count">${escapeHtml(String(pointCountsByCountry[country] || 0))}</span></label>`;
        }).join('');
        document.querySelectorAll('.country-checkbox').forEach((checkbox) => {
          checkbox.addEventListener('change', () => {
            if (checkbox.checked) { activeCountries.add(checkbox.value); } else { activeCountries.delete(checkbox.value); }
            renderMapState();
          });
        });
      }
      function renderLayerControls() {
        const groupOrder = ['primary-evidence', 'environmental-context', 'archaeology-context', 'orientation'];
        layerFilters.innerHTML = groupOrder
          .map((group) => {
            const layers = ALL_LAYERS.filter((layer) => layer.group === group);
            if (!layers.length) return '';
            const enabledCount = layers.filter((layer) => activeLayerKeys.has(layer.key)).length;
            const collapsed = collapsedLayerGroups.has(group);
            const cards = layers.map((layer) => {
              const checked = activeLayerKeys.has(layer.key) ? 'checked' : '';
              const stateLabel = activeLayerKeys.has(layer.key) ? 'Enabled' : 'Hidden';
              const swatchColor = layerColor(layer);
              const swatchBorder = layer.style && layer.style.stroke ? layer.style.stroke : swatchColor;
              return `<div class="layer-card ${activeLayerKeys.has(layer.key) ? 'is-enabled' : ''}"><label><input class="layer-checkbox" type="checkbox" value="${escapeHtml(layer.key)}" ${checked} aria-label="Toggle ${escapeHtml(layer.label)}"><div style="width:100%;"><div class="layer-card-top"><div class="layer-card-head"><div class="layer-card-title"><span class="layer-swatch-stack" style="background:${escapeHtml(swatchColor)}; border-color:${escapeHtml(swatchBorder)};"></span><div class="layer-card-text"><strong>${escapeHtml(layer.label)}</strong><span>${escapeHtml(layer.description)}</span></div></div><span class="layer-state-pill">${escapeHtml(stateLabel)}</span></div><span class="layer-badge" id="layer-count-${escapeHtml(layer.key)}">${escapeHtml(String(layer.count))} ${escapeHtml(layerUnit(layer))}</span></div><div class="layer-meta"><span><strong>Source</strong> ${escapeHtml(layer.source_name || layer.label)}</span><span><strong>Coverage</strong> ${escapeHtml(layer.coverage_label || '')}</span><span><strong>Geometry</strong> ${escapeHtml(layer.geometry_label || layerUnit(layer))}</span></div></div></label></div>`;
            }).join('');
            return `<section class="layer-group ${collapsed ? 'is-collapsed' : ''}"><div class="layer-group-head"><div class="layer-group-head-main"><h3>${escapeHtml(layerGroupLabel(group))}</h3><span>${escapeHtml(layerGroupSummary(group))} ${enabledCount}/${layers.length} enabled.</span></div><div class="layer-group-actions"><button class="layer-group-button" type="button" data-group-toggle="${escapeHtml(group)}">${enabledCount === layers.length ? 'Hide group' : 'Show group'}</button><button class="layer-group-button" type="button" data-group-collapse="${escapeHtml(group)}">${collapsed ? 'Expand' : 'Collapse'}</button></div></div><div class="layer-group-stack">${cards}</div></section>`;
          })
          .join('');
        document.querySelectorAll('.layer-checkbox').forEach((checkbox) => {
          checkbox.addEventListener('change', () => {
            if (checkbox.checked) { activeLayerKeys.add(checkbox.value); } else { activeLayerKeys.delete(checkbox.value); }
            renderMapState();
          });
        });
        document.querySelectorAll('[data-group-toggle]').forEach((button) => {
          button.addEventListener('click', () => {
            const group = button.dataset.groupToggle;
            const layers = ALL_LAYERS.filter((layer) => layer.group === group);
            const allEnabled = layers.every((layer) => activeLayerKeys.has(layer.key));
            layers.forEach((layer) => {
              if (allEnabled) {
                activeLayerKeys.delete(layer.key);
              } else {
                activeLayerKeys.add(layer.key);
              }
            });
            renderMapState();
          });
        });
        document.querySelectorAll('[data-group-collapse]').forEach((button) => {
          button.addEventListener('click', () => {
            const group = button.dataset.groupCollapse;
            if (collapsedLayerGroups.has(group)) {
              collapsedLayerGroups.delete(group);
            } else {
              collapsedLayerGroups.add(group);
            }
            renderLayerControls();
          });
        });
      }
      function applyLayerPreset(preset) {
        if (preset === 'evidence') {
          activeLayerKeys = new Set(ALL_LAYERS.filter((layer) => layer.group === 'primary-evidence').map((layer) => layer.key));
        }
        if (preset === 'context') {
          activeLayerKeys = new Set(
            ALL_LAYERS
              .filter((layer) => ['primary-evidence', 'environmental-context', 'archaeology-context'].includes(layer.group))
              .map((layer) => layer.key)
          );
        }
        if (preset === 'orientation') {
          activeLayerKeys = new Set(
            ALL_LAYERS
              .filter((layer) => ['primary-evidence', 'orientation'].includes(layer.group))
              .map((layer) => layer.key)
          );
        }
        if (preset === 'all') {
          activeLayerKeys = new Set(ALL_LAYERS.map((layer) => layer.key));
        }
        renderLayerControls();
        renderMapState();
      }
      function renderLegend() {
        const activeLegendLayers = ALL_LAYERS.filter((layer) => activeLayerKeys.has(layer.key));
        const pointLayers = activeLegendLayers.filter((layer) => Object.prototype.hasOwnProperty.call(layer, 'features'));
        const polygonLayers = activeLegendLayers.filter((layer) => !Object.prototype.hasOwnProperty.call(layer, 'features'));
        const renderGroup = (label, layers) => layers.length
          ? `<div class="legend-group"><div class="legend-group-label">${escapeHtml(label)}</div><div class="legend-list">${layers.map((layer) => `<div class="legend-item"><span class="legend-swatch" style="background:${escapeHtml(layerColor(layer))};border-color:${escapeHtml(layer.style.stroke || layerColor(layer))};"></span><span>${escapeHtml(layer.label)}: ${escapeHtml(layer.description)} ${layer.coverage_label ? `(${escapeHtml(layer.coverage_label)})` : ''}</span></div>`).join('')}</div></div>`
          : '';
        legendItems.innerHTML = [
          renderGroup('Point layers', pointLayers),
          renderGroup('Polygon overlays', polygonLayers),
        ].join('') || '<div class="legend-item"><span>No layers are visible. Restore defaults or enable one or more layers.</span></div>';
        densityRamp.hidden = !activeLayerKeys.has('raa-archaeology');
      }
      function renderFilterChips() {
        const chips = [];
        if (activeCountries.size !== COUNTRIES.length) {
          chips.push({
            kind: 'countries',
            title: 'Countries',
            value: activeCountries.size ? [...activeCountries].join(', ') : 'No countries selected',
          });
        }
        if (activeLayerKeys.size !== DEFAULT_LAYER_KEYS.length || DEFAULT_LAYER_KEYS.some((key) => !activeLayerKeys.has(key))) {
          chips.push({
            kind: 'layers',
            title: 'Layers',
            value: activeLayerKeys.size ? humanLayerList(activeLayerKeys) : 'No layers enabled',
          });
        }
        if (TIME_HAS_DATA && (timeStartBp !== DEFAULT_TIME_START_BP || timeIntervalYears !== DEFAULT_TIME_INTERVAL_YEARS)) {
          chips.push({
            kind: 'time',
            title: 'Time window',
            value: `${timeStartBp}-${timeWindowEndBp()} BP · ${timeIntervalYears} years`,
          });
        }
        if (Number(slider.value) !== __INITIAL_DIAMETER__) {
          chips.push({
            kind: 'distance',
            title: 'Acceptance diameter',
            value: `${Number(slider.value)} km`,
          });
        }
        if (Math.round(densityOpacity * 100) !== 60) {
          chips.push({
            kind: 'density',
            title: 'Archaeology opacity',
            value: `${Math.round(densityOpacity * 100)}%`,
          });
        }
        if (currentBasemap !== 'voyager') {
          chips.push({
            kind: 'basemap',
            title: 'Basemap',
            value: currentBasemap.charAt(0).toUpperCase() + currentBasemap.slice(1),
          });
        }

        filterChipCount.textContent = chips.length ? `${chips.length} active` : 'Defaults';
        filterChips.innerHTML = chips.length
          ? chips.map((chip) => `<div class="filter-chip"><div><strong>${escapeHtml(chip.title)}</strong><span>${escapeHtml(chip.value)}</span></div><button class="filter-chip-remove" type="button" data-clear-kind="${escapeHtml(chip.kind)}" aria-label="Reset ${escapeHtml(chip.title)}">×</button></div>`).join('')
          : '<div class="filter-chip-empty">No filter groups are currently overriding the default map state.</div>';

        filterChips.querySelectorAll('[data-clear-kind]').forEach((button) => {
          button.addEventListener('click', () => {
            const kind = button.dataset.clearKind;
            if (kind === 'countries') activeCountries = new Set(DEFAULT_COUNTRIES);
            if (kind === 'layers') activeLayerKeys = new Set(DEFAULT_LAYER_KEYS);
            if (kind === 'time') {
              timeStartBp = DEFAULT_TIME_START_BP;
              timeIntervalYears = DEFAULT_TIME_INTERVAL_YEARS;
            }
            if (kind === 'distance') slider.value = String(__INITIAL_DIAMETER__);
            if (kind === 'density') {
              densityOpacity = 0.6;
              densityOpacitySlider.value = '60';
            }
            if (kind === 'basemap') setBasemap('voyager');
            renderCountryControls();
            renderLayerControls();
            renderMapState();
          });
        });
      }
      function popupHtml(feature) {
        const rows = Array.isArray(feature.popup_rows) ? feature.popup_rows : [];
        const rowHtml = rows.filter((row) => row && row.value).map((row) => `<div><strong>${escapeHtml(row.label || '')}</strong> ${escapeHtml(row.value || '')}</div>`).join('');
        return `<div class="popup-grid"><div><strong>Name</strong> ${escapeHtml(feature.title || '')}</div><div><strong>Type</strong> ${escapeHtml(feature.subtitle || '')}</div>${rowHtml}<div><strong>Coords</strong> ${Number(feature.latitude).toFixed(6)}, ${Number(feature.longitude).toFixed(6)}</div>${feature.source_url ? `<div><strong>Source</strong> <a href="${escapeHtml(feature.source_url)}" target="_blank" rel="noreferrer">Open</a></div>` : ''}</div>`;
      }
      function polygonPopupHtml(layer, properties) {
        const rows = Array.isArray(properties.popup_rows) ? properties.popup_rows : [];
        const rowHtml = rows.filter((row) => row && row.value).map((row) => `<div><strong>${escapeHtml(row.label || '')}</strong> ${escapeHtml(row.value || '')}</div>`).join('');
        return `<div class="popup-grid"><div><strong>Layer</strong> ${escapeHtml(layer.label)}</div><div><strong>Name</strong> ${escapeHtml(properties.name || '')}</div><div><strong>Type</strong> ${escapeHtml(properties.category || properties.geometry_type || '')}</div>${rowHtml}${properties.source_url ? `<div><strong>Source</strong> <a href="${escapeHtml(properties.source_url)}" target="_blank" rel="noreferrer">Open</a></div>` : ''}</div>`;
      }
      function densityFillColor(count, maxCount) {
        if (!maxCount || count <= 0) return '#fee2e2';
        const ratio = count / maxCount;
        if (ratio >= 0.75) return '#7f1d1d';
        if (ratio >= 0.55) return '#b91c1c';
        if (ratio >= 0.35) return '#ef4444';
        if (ratio >= 0.20) return '#f87171';
        if (ratio >= 0.08) return '#fca5a5';
        return '#fee2e2';
      }
      function pointFeatureInTimeWindow(layer, feature) {
        if (!layer.applies_time_filter || !TIME_HAS_DATA) return true;
        const yearBp = Number(feature.time_year_bp);
        if (!Number.isFinite(yearBp)) return true;
        const endBp = timeWindowEndBp();
        return yearBp >= timeStartBp && yearBp <= endBp;
      }
      function pointFeatureVisible(layer, feature) {
        return (
          activeLayerKeys.has(layer.key)
          && (!layer.applies_country_filter || !feature.country || activeCountries.has(feature.country))
          && pointFeatureInTimeWindow(layer, feature)
        );
      }
      function polygonFeatureVisible(layer, properties) {
        const country = properties.country || '';
        return activeLayerKeys.has(layer.key) && (!layer.applies_country_filter || !country || activeCountries.has(country));
      }
      function removeRenderedLayers() {
        renderedPointGroups.forEach((group) => map.removeLayer(group));
        renderedPolygonLayers.forEach((layer) => map.removeLayer(layer));
        renderedPointGroups = [];
        renderedPolygonLayers = [];
        circleLayerGroup.clearLayers();
        visiblePointEntries = [];
        highlightedPointEntry = null;
      }
      function createClusterGroup(layer) {
        return L.markerClusterGroup({
          showCoverageOnHover: false,
          spiderfyOnMaxZoom: true,
          maxClusterRadius: 46,
          disableClusteringAtZoom: 10,
          iconCreateFunction(cluster) {
            const count = cluster.getChildCount();
            const size = count > 100 ? 50 : count > 25 ? 44 : 38;
            return L.divIcon({ html: `<div class="cluster-pill" style="width:${size}px;height:${size}px;background:${layer.style.fill};">${count}</div>`, className: '', iconSize: [size, size] });
          }
        });
      }
      function renderPointLayers() {
        const diameterKm = Number(slider.value);
        const radiusMeters = (diameterKm * 1000) / 2;
        POINT_LAYERS.forEach((layer) => {
          const clusterGroup = createClusterGroup(layer);
          layer.features.forEach((feature) => {
            if (!pointFeatureVisible(layer, feature)) return;
            const marker = L.circleMarker([feature.latitude, feature.longitude], { pane: 'pointPane', radius: layer.key === 'aadr' ? 4.5 : 6, color: layer.style.stroke, weight: 1.3, fillColor: layer.style.fill, fillOpacity: 0.92 });
            marker.bindPopup(popupHtml(feature), { maxWidth: 360 });
            const entry = { layer, feature, marker };
            marker.on('click', () => {
              focusPointAtVisibleIndex(visiblePointEntries.indexOf(entry));
            });
            clusterGroup.addLayer(marker);
            visiblePointEntries.push(entry);
            if (layer.circle_enabled && diameterKm > 0) {
              const circle = L.circle([feature.latitude, feature.longitude], { pane: 'circlePane', radius: radiusMeters, color: layer.style.circleStroke, weight: 1, opacity: 0.55, fillColor: layer.style.circleFill, fillOpacity: 0.12, interactive: false });
              circleLayerGroup.addLayer(circle);
            }
          });
          if (clusterGroup.getLayers().length > 0) { clusterGroup.addTo(map); renderedPointGroups.push(clusterGroup); }
        });
      }
      function renderPolygonLayers() {
        POLYGON_LAYERS.forEach((layer) => {
          const visibleFeatures = (layer.geojson.features || []).filter((feature) => polygonFeatureVisible(layer, feature.properties || {}));
          if (!visibleFeatures.length) return;
          let geoJsonLayer;
          if (layer.kind === 'country-boundaries') {
            geoJsonLayer = L.geoJSON({ type: 'FeatureCollection', features: visibleFeatures }, {
              pane: 'boundaryPane',
              style(feature) {
                const country = feature.properties.country || '';
                const style = countryStyle(country);
                return { color: style.stroke, weight: activeCountries.has(country) ? 2.2 : 1.2, fillColor: style.fill, fillOpacity: activeCountries.has(country) ? 0.10 : 0.02, opacity: activeCountries.has(country) ? 0.95 : 0.45 };
              },
              onEachFeature(feature, featureLayer) {
                featureLayer.bindPopup(`<div class="popup-grid"><div><strong>Country</strong> ${escapeHtml(feature.properties.name || '')}</div><div><strong>Filter state</strong> ${activeCountries.has(feature.properties.country) ? 'Visible' : 'Hidden'}</div></div>`);
                featureLayer.on('click', () => {
                  const bounds = featureLayer.getBounds();
                  setFocusState({
                    kind: 'polygon',
                    layerKey: layer.key,
                    title: feature.properties.name || layer.label,
                    subtitle: 'Country boundary',
                    meta: [
                      { label: 'Layer', value: layer.label },
                      { label: 'Country', value: feature.properties.country || 'Unassigned' },
                      { label: 'State', value: activeCountries.has(feature.properties.country) ? 'Visible' : 'Hidden' },
                    ],
                    sourceUrl: '',
                    bounds: bounds.isValid() ? [[bounds.getSouth(), bounds.getWest()], [bounds.getNorth(), bounds.getEast()]] : null,
                  });
                });
              }
            });
          } else if (layer.kind === 'density') {
            geoJsonLayer = L.geoJSON({ type: 'FeatureCollection', features: visibleFeatures }, {
              pane: 'polygonPane',
              style(feature) {
                const count = Number(feature.properties.count || 0);
                return { color: layer.style.stroke, weight: 1.1, fillColor: densityFillColor(count, Number(layer.max_count || 0)), fillOpacity: densityOpacity, opacity: 0.75 };
              },
              onEachFeature(feature, featureLayer) {
                featureLayer.bindPopup(`<div class="popup-grid"><div><strong>Layer</strong> ${escapeHtml(layer.label)}</div><div><strong>Country</strong> ${escapeHtml(feature.properties.country || '')}</div><div><strong>Records</strong> ${escapeHtml(String(feature.properties.count_label || feature.properties.count || '0'))}</div></div>`);
                featureLayer.on('click', () => {
                  const bounds = featureLayer.getBounds();
                  setFocusState({
                    kind: 'polygon',
                    layerKey: layer.key,
                    title: feature.properties.country || layer.label,
                    subtitle: 'Density cell',
                    meta: [
                      { label: 'Layer', value: layer.label },
                      { label: 'Country', value: feature.properties.country || 'Unassigned' },
                      { label: 'Records', value: String(feature.properties.count_label || feature.properties.count || '0') },
                    ],
                    sourceUrl: '',
                    bounds: bounds.isValid() ? [[bounds.getSouth(), bounds.getWest()], [bounds.getNorth(), bounds.getEast()]] : null,
                  });
                });
              }
            });
          } else {
            geoJsonLayer = L.geoJSON({ type: 'FeatureCollection', features: visibleFeatures }, {
              pane: 'polygonPane',
              style() {
                return { color: layer.style.stroke, weight: 1.1, fillColor: layer.style.fill || 'rgba(100, 116, 139, 0.14)', fillOpacity: 0.28, opacity: 0.85 };
              },
              onEachFeature(feature, featureLayer) {
                featureLayer.bindPopup(polygonPopupHtml(layer, feature.properties || {}));
                featureLayer.on('click', () => {
                  const properties = feature.properties || {};
                  const bounds = featureLayer.getBounds();
                  setFocusState({
                    kind: 'polygon',
                    layerKey: layer.key,
                    title: properties.name || layer.label,
                    subtitle: properties.category || properties.geometry_type || 'Polygon record',
                    meta: [
                      { label: 'Layer', value: layer.label },
                      { label: 'Country', value: properties.country || 'Unassigned' },
                      { label: 'Type', value: properties.category || properties.geometry_type || 'Polygon record' },
                    ],
                    sourceUrl: properties.source_url || '',
                    bounds: bounds.isValid() ? [[bounds.getSouth(), bounds.getWest()], [bounds.getNorth(), bounds.getEast()]] : null,
                  });
                });
              }
            });
          }
          geoJsonLayer.addTo(map);
          renderedPolygonLayers.push(geoJsonLayer);
        });
      }
      function activeBounds() {
        const latLngs = visiblePointEntries.map((entry) => [entry.feature.latitude, entry.feature.longitude]);
        renderedPolygonLayers.forEach((layer) => {
          const bounds = layer.getBounds();
          if (bounds.isValid()) {
            latLngs.push([bounds.getSouth(), bounds.getWest()]);
            latLngs.push([bounds.getNorth(), bounds.getEast()]);
          }
        });
        return latLngs.length ? L.latLngBounds(latLngs) : null;
      }
      function updateStats() {
        const enabledLayers = ALL_LAYERS.filter((layer) => activeLayerKeys.has(layer.key)).length;
        const enabledPointLayers = POINT_LAYERS.filter((layer) => activeLayerKeys.has(layer.key)).length;
        const datedVisibleCount = visiblePointEntries.filter(({ layer, feature }) => {
          if (!layer.applies_time_filter) return false;
          return Number.isFinite(Number(feature.time_year_bp));
        }).length;
        statVisiblePoints.textContent = String(visiblePointEntries.length);
        statVisibleLayers.textContent = String(enabledLayers);
        statVisibleCountries.textContent = String(activeCountries.size);
        statRadius.textContent = `${(Number(slider.value) / 2).toFixed(1)} km`;
        statContextSources.textContent = String(ALL_LAYERS.filter((layer) => layer.key !== 'aadr').length);
        statVisiblePointsNote.textContent = `${enabledPointLayers} point layers currently contribute visible records.`;
        statVisibleLayersNote.textContent = `${renderedPolygonLayers.length} polygon overlays are currently drawn on the map.`;
        statVisibleCountriesNote.textContent = activeCountries.size === COUNTRIES.length
          ? 'All configured countries are visible.'
          : activeCountries.size
            ? `${COUNTRIES.length - activeCountries.size} countries are currently excluded.`
            : 'No countries are currently selected.';
        statRadiusNote.textContent = Number(slider.value) > 0
          ? `${Number(slider.value)} km diameter acceptance circles are active for point layers.`
          : 'Acceptance circles are currently hidden.';
        statContextSourcesNote.textContent = `${ALL_LAYERS.filter((layer) => layer.key !== 'aadr' && activeLayerKeys.has(layer.key)).length} context sources are currently enabled.`;
        timeRecordCount.textContent = TIME_HAS_DATA
          ? `${datedVisibleCount} dated records are visible in the active BP window.`
          : 'No dated records are available for BP filtering.';
        const visiblePolygonLayers = renderedPolygonLayers.length;
        selectionReadout.textContent = `${visiblePointEntries.length} points · ${visiblePolygonLayers} overlays`;
        topbarStatePill.textContent = `${activeCountries.size} countries · ${enabledLayers} layers · ${visiblePointEntries.length} visible points`;
        countrySummary.textContent = activeCountries.size === COUNTRIES.length ? 'All countries visible' : activeCountries.size ? `${activeCountries.size} countries active` : 'No countries active';
        layerSummary.textContent = enabledLayers ? `${enabledLayers} layers enabled` : 'No layers enabled';
        ALL_LAYERS.forEach((layer) => {
          const badge = document.getElementById(`layer-count-${layer.key}`);
          if (!badge) return;
          if (Object.prototype.hasOwnProperty.call(layer, 'features')) {
            const count = layer.features.filter((feature) => pointFeatureVisible(layer, feature)).length;
            badge.textContent = `${count} ${layerUnit(layer)}`;
          } else {
            const count = (layer.geojson.features || []).filter((feature) => polygonFeatureVisible(layer, feature.properties || {})).length;
            badge.textContent = `${count} ${layerUnit(layer)}`;
          }
        });
      }
      function updateSummary() {
        const visibleCountriesText = activeCountries.size ? [...activeCountries].join(', ') : 'none selected';
        const visibleLayersText = activeLayerKeys.size ? humanLayerList(activeLayerKeys) : 'none selected';
        const timeWindowText = TIME_HAS_DATA
          ? `${timeStartBp}-${timeWindowEndBp()} BP (${timeIntervalYears} years)`
          : 'No numeric BP dates available';
        const items = [
          `Visible countries: ${visibleCountriesText}`,
          `Visible layers: ${visibleLayersText}`,
          `Time window: ${timeWindowText}`,
          `Acceptance diameter: ${Number(slider.value)} km`,
          `Acceptance radius: ${(Number(slider.value) / 2).toFixed(1)} km`,
          `Archaeology opacity: ${Math.round(densityOpacity * 100)}%`,
          `Map build date: __GENERATED_ON__`,
          `AADR release: __VERSION__`,
          `Archaeology coverage note: Sweden only in the current RAÄ layer`
        ];
        activeSummary.innerHTML = items.map((item) => `<div class="summary-item"><span>${escapeHtml(item)}</span></div>`).join('');
      }
      function buildSearchResults() {
        const query = searchInput.value.trim().toLowerCase();
        searchClearButton.hidden = !query;
        if (!query) {
          const initial = visiblePointEntries.slice(0, 8);
          searchCount.textContent = `${visiblePointEntries.length} visible records`;
          searchResults.innerHTML = initial.map(({ layer, feature }, index) => `<button class="search-result" type="button" data-search-index="${index}"><strong>${escapeHtml(feature.title || '')}</strong><span>${escapeHtml(feature.subtitle || 'Unspecified type')}</span><div class="search-result-meta"><span class="search-badge">${escapeHtml(layer.label)}</span><span class="search-badge">${escapeHtml(feature.country || 'Unassigned')}</span></div></button>`).join('') || '<div class="summary-item"><span>No visible point records are available under the current filters.</span></div>';
          searchResults.querySelectorAll('[data-search-index]').forEach((button, index) => {
            button.addEventListener('click', () => {
            const match = initial[index];
            if (!match) return;
            focusPointAtVisibleIndex(visiblePointEntries.indexOf(match));
            map.flyTo([match.feature.latitude, match.feature.longitude], Math.max(map.getZoom(), 8), { duration: 0.7 });
            window.setTimeout(() => match.marker.openPopup(), 250);
          });
          });
          return;
        }
        const matches = visiblePointEntries.filter(({ layer, feature }) => `${feature.title || ''} ${feature.subtitle || ''} ${feature.country || ''} ${layer.label || ''}`.toLowerCase().includes(query)).slice(0, 12);
        searchCount.textContent = `${matches.length} matches · ${visiblePointEntries.length} visible`;
        searchResults.innerHTML = matches.map(({ layer, feature }, index) => `<button class="search-result" type="button" data-search-index="${index}"><strong>${escapeHtml(feature.title || '')}</strong><span>${escapeHtml(feature.subtitle || 'Unspecified type')}</span><div class="search-result-meta"><span class="search-badge">${escapeHtml(layer.label)}</span><span class="search-badge">${escapeHtml(feature.country || 'Unassigned')}</span></div></button>`).join('') || '<div class="summary-item"><span>No visible records match the current query.</span></div>';
        searchResults.querySelectorAll('[data-search-index]').forEach((button, index) => {
          button.addEventListener('click', () => {
            const match = matches[index];
            if (!match) return;
            focusPointAtVisibleIndex(visiblePointEntries.indexOf(match));
            map.flyTo([match.feature.latitude, match.feature.longitude], Math.max(map.getZoom(), 8), { duration: 0.7 });
            window.setTimeout(() => match.marker.openPopup(), 250);
          });
        });
      }
      function renderMapState() {
        refreshTimeControls();
        removeRenderedLayers();
        renderPointLayers();
        renderPolygonLayers();
        renderCountryControls();
        renderLegend();
        renderFilterChips();
        renderWorkspaceBrief();
        renderCoverageMatrix();
        renderTimeDensity();
        updateStats();
        updateSummary();
        buildSearchResults();
        renderFocusCard();
        syncPresetButtons();
        syncTimePresetButtons();
        diameterValue.textContent = `${Number(slider.value)} km diameter`;
        radiusValue.textContent = `${(Number(slider.value) / 2).toFixed(1)} km`;
        densityOpacityValue.textContent = `${Math.round(densityOpacity * 100)}%`;
        emptyState.hidden = visiblePointEntries.length > 0 || renderedPolygonLayers.length > 0;
        syncHashState();
      }
      function setBasemap(name) {
        if (name === currentBasemap || !basemaps[name]) return;
        map.removeLayer(basemaps[currentBasemap]);
        basemaps[name].addTo(map);
        currentBasemap = name;
        document.querySelectorAll('.basemap-button').forEach((button) => button.classList.toggle('is-active', button.dataset.basemap === name));
        syncHashState();
      }
      function fitToActive() {
        const bounds = activeBounds();
        if (bounds && bounds.isValid()) map.fitBounds(bounds, { padding: [36, 36] });
      }
      function resetView() { map.fitBounds(INITIAL_BOUNDS, { padding: [36, 36] }); }
      function restoreDefaults() {
        activeCountries = new Set(DEFAULT_COUNTRIES);
        activeLayerKeys = new Set(DEFAULT_LAYER_KEYS);
        slider.value = __INITIAL_DIAMETER__;
        timeStartBp = DEFAULT_TIME_START_BP;
        timeIntervalYears = DEFAULT_TIME_INTERVAL_YEARS;
        densityOpacity = 0.6;
        densityOpacitySlider.value = '60';
        setPanelCollapsed(defaultPanelCollapsed(), false);
        searchInput.value = '';
        if (currentBasemap !== 'voyager') setBasemap('voyager');
        renderCountryControls();
        renderLayerControls();
        renderMapState();
        resetView();
      }
      document.getElementById('countries-all').addEventListener('click', () => { activeCountries = new Set(COUNTRIES); renderCountryControls(); renderMapState(); });
      document.getElementById('countries-none').addEventListener('click', () => { activeCountries = new Set(); renderCountryControls(); renderMapState(); });
      document.getElementById('countries-fit').addEventListener('click', fitToActive);
      document.getElementById('fit-active').addEventListener('click', fitToActive);
      document.getElementById('reset-view').addEventListener('click', resetView);
      document.getElementById('restore-defaults').addEventListener('click', restoreDefaults);
      document.getElementById('copy-link').addEventListener('click', async () => {
        syncHashState();
        const button = document.getElementById('copy-link');
        const previous = button.textContent;
        try {
          await navigator.clipboard.writeText(window.location.href);
          button.textContent = 'Link copied';
        } catch (error) {
          button.textContent = 'Copy failed';
        }
        window.setTimeout(() => { button.textContent = previous; }, 1400);
      });
      document.getElementById('fullscreen-toggle').addEventListener('click', async () => {
        const target = document.querySelector('.map-stage');
        if (!document.fullscreenElement) { await target.requestFullscreen(); } else { await document.exitFullscreen(); }
      });
      document.querySelectorAll('.basemap-button').forEach((button) => button.addEventListener('click', () => setBasemap(button.dataset.basemap)));
      panelToggleButton.addEventListener('click', () => setPanelCollapsed(!sidebar.classList.contains('is-collapsed')));
      helpToggleButton.addEventListener('click', openHelpDialog);
      helpCloseButton.addEventListener('click', closeHelpDialog);
      helpDialog.addEventListener('click', (event) => {
        if (event.target === helpDialog) closeHelpDialog();
      });
      mobilePanelCloseButton.addEventListener('click', () => setPanelCollapsed(true));
      mobileScrim.addEventListener('click', () => setPanelCollapsed(true));
      slider.addEventListener('input', renderMapState);
      timeStartSlider.addEventListener('input', () => { timeStartBp = Number(timeStartSlider.value); renderMapState(); });
      timeIntervalSlider.addEventListener('input', () => { timeIntervalYears = Number(timeIntervalSlider.value); renderMapState(); });
      densityOpacitySlider.addEventListener('input', () => { densityOpacity = Number(densityOpacitySlider.value) / 100; renderMapState(); });
      document.querySelectorAll('[data-km]').forEach((button) => {
        button.addEventListener('click', () => {
          slider.value = button.dataset.km;
          renderMapState();
        });
      });
      document.querySelectorAll('[data-time-interval]').forEach((button) => {
        button.addEventListener('click', () => {
          const preset = button.dataset.timeInterval;
          timeIntervalYears = preset === 'full' ? TIME_INTERVAL_MAX : Number(preset);
          renderMapState();
        });
      });
      searchInput.addEventListener('input', buildSearchResults);
      searchClearButton.addEventListener('click', () => {
        searchInput.value = '';
        searchInput.focus();
        buildSearchResults();
      });
      searchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
          const firstResult = searchResults.querySelector('[data-search-index]');
          if (firstResult) firstResult.click();
        }
      });
      focusCloseButton.addEventListener('click', () => setFocusState(null));
      focusPreviousButton.addEventListener('click', () => {
        if (!focusState || focusState.kind !== 'point' || !visiblePointEntries.length) return;
        const nextIndex = (focusState.visiblePointIndex - 1 + visiblePointEntries.length) % visiblePointEntries.length;
        focusPointAtVisibleIndex(nextIndex);
      });
      focusNextButton.addEventListener('click', () => {
        if (!focusState || focusState.kind !== 'point' || !visiblePointEntries.length) return;
        const nextIndex = (focusState.visiblePointIndex + 1) % visiblePointEntries.length;
        focusPointAtVisibleIndex(nextIndex);
      });
      focusZoomButton.addEventListener('click', () => {
        if (!focusState) return;
        if (focusState.kind === 'polygon' && focusState.bounds) {
          map.fitBounds(focusState.bounds, { padding: [32, 32] });
          return;
        }
        if (Number.isFinite(focusState.latitude) && Number.isFinite(focusState.longitude)) {
          map.flyTo([focusState.latitude, focusState.longitude], Math.max(map.getZoom(), 8), { duration: 0.7 });
        }
      });
      map.on('zoomend', () => {
        zoomReadout.textContent = map.getZoom().toFixed(1);
        centerReadout.textContent = `${map.getCenter().lat.toFixed(3)}, ${map.getCenter().lng.toFixed(3)}`;
      });
      map.on('moveend', () => { centerReadout.textContent = `${map.getCenter().lat.toFixed(3)}, ${map.getCenter().lng.toFixed(3)}`; });
      map.on('mousemove', (event) => { cursorReadout.textContent = `${event.latlng.lat.toFixed(3)}, ${event.latlng.lng.toFixed(3)}`; });
      document.addEventListener('fullscreenchange', () => window.setTimeout(() => map.invalidateSize(), 160));
      document.addEventListener('keydown', (event) => {
        if (event.key === '?') {
          event.preventDefault();
          openHelpDialog();
          return;
        }
        if (event.key === 'Escape' && !helpDialog.hidden) {
          closeHelpDialog();
          return;
        }
        if (event.key === 'Escape' && mobileLayoutQuery.matches && !sidebar.classList.contains('is-collapsed')) {
          setPanelCollapsed(true);
        }
      });
      mobileLayoutQuery.addEventListener('change', () => {
        if (panelPreferenceFromHash() === null) {
          setPanelCollapsed(defaultPanelCollapsed(), false);
          return;
        }
        updatePanelToggleLabel();
      });
      sectionNavButtons.forEach((button) => {
        button.addEventListener('click', () => {
          const target = document.getElementById(button.dataset.sectionTarget);
          if (!target) return;
          sidebarInner.scrollTo({ top: Math.max(target.offsetTop - 72, 0), behavior: 'smooth' });
          updateSectionNav(button.dataset.sectionTarget);
        });
      });
      document.querySelectorAll('[data-layer-preset]').forEach((button) => {
        button.addEventListener('click', () => applyLayerPreset(button.dataset.layerPreset));
      });
      legendToggleButton.addEventListener('click', () => setLegendCollapsed(!legendCollapsed));
      sidebarInner.addEventListener('scroll', syncSectionNavWithScroll);
      window.addEventListener('resize', () => window.setTimeout(() => map.invalidateSize(), 120));
      densityOpacitySlider.value = String(Math.round(densityOpacity * 100));
      slider.value = String(Number(initialState.diameter || __INITIAL_DIAMETER__));
      setPanelCollapsed(panelPreferenceFromHash() ?? defaultPanelCollapsed(), false);
      renderScopeSummary();
      renderCountryControls();
      renderLayerControls();
      renderMapState();
      setBasemap(currentBasemap);
      setLegendCollapsed(legendCollapsed, false);
      syncSectionNavWithScroll();
      resetView();
      zoomReadout.textContent = map.getZoom().toFixed(1);
      centerReadout.textContent = `${map.getCenter().lat.toFixed(3)}, ${map.getCenter().lng.toFixed(3)}`;
    </script>
  </body>
</html>
"""
    return (
        template
        .replace("__TITLE__", escape_html(title))
        .replace("__VERSION__", escape_html(version))
        .replace("__GENERATED_ON__", escape_html(generated_on))
        .replace("__COUNTRIES_JSON__", json.dumps(list(countries), ensure_ascii=False))
        .replace("__POINT_LAYERS_JSON__", json.dumps(point_layers, ensure_ascii=False))
        .replace("__POLYGON_LAYERS_JSON__", json.dumps(polygon_layers, ensure_ascii=False))
        .replace("__BOUNDS_JSON__", json.dumps(bounds))
        .replace("__ASSET_BASE_PATH__", asset_base_path)
        .replace("__INITIAL_DIAMETER__", str(initial_diameter_km))
        .replace("__INITIAL_RADIUS__", f"{initial_diameter_km / 2:.1f}")
        .replace("__TIME_MIN_BP__", str(time_min_bp))
        .replace("__TIME_MAX_BP__", str(time_max_bp))
        .replace("__TIME_HAS_DATA__", str(has_time_data).lower())
        .replace("__INITIAL_TIME_START_BP__", str(initial_time_start_bp))
        .replace("__INITIAL_TIME_END_BP__", str(initial_time_end_bp))
        .replace("__INITIAL_TIME_INTERVAL__", str(initial_time_interval_years))
        .replace("__TIME_INTERVAL_MAX__", str(max_time_span))
    )
