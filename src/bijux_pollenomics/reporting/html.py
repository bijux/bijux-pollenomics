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
    <title>__TITLE__</title>
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
      .floating-legend,
      .map-topbar,
      .map-status,
      .focus-card {
        border: 1px solid var(--surface-edge);
        background: var(--surface);
        backdrop-filter: blur(16px);
        box-shadow: var(--shadow-md);
      }
      .floating-legend,
      .map-topbar,
      .map-status,
      .focus-card {
        position: relative;
        overflow: hidden;
      }
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
      }
      .chip-toggle.is-active,
      .toolbar-button.is-primary,
      .preset-button.is-active,
      .inline-button.is-primary,
      .basemap-button.is-active {
        border-color: rgba(37, 99, 235, 0.28);
        background: linear-gradient(180deg, rgba(37, 99, 235, 0.16), rgba(14, 122, 114, 0.10));
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.12);
      }
      .chip-toggle {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 8px 12px;
      }
      .chip-toggle input { margin: 0; }
      .chip-swatch,
      .legend-swatch {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        border: 1px solid rgba(24, 37, 61, 0.28);
        flex: 0 0 auto;
      }
      .chip-count {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 24px;
        padding: 3px 7px;
        border-radius: 999px;
        background: rgba(24, 37, 61, 0.08);
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
      }
      .toolbar-button,
      .preset-button,
      .inline-button {
        padding: 8px 12px;
        font-size: 12px;
        font-weight: 700;
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
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .inline-actions { margin-top: 12px; }
      .basemap-button {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        border-radius: 999px;
        text-align: left;
      }
      .basemap-preview {
        width: 18px;
        height: 18px;
        border-radius: 999px;
        border: 1px solid rgba(24, 37, 61, 0.10);
        flex: 0 0 auto;
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
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }
      .basemap-copy {
        display: none;
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
      .legend-list {
        display: grid;
        gap: 10px;
      }
      .search-result,
      .summary-item {
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
      .search-result strong { display: block; font-size: 14px; }
      .search-result span,
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
      .map-topbar {
        position: absolute;
        top: 16px;
        left: 16px;
        right: 16px;
        z-index: 1100;
        display: grid;
        gap: 10px;
        padding: 12px;
        border-radius: 22px;
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.56), rgba(255, 255, 255, 0)),
          var(--surface);
        overflow: visible;
      }
      .map-topbar-main {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
        gap: 14px;
        min-width: 0;
      }
      .topbar-search {
        position: relative;
        display: grid;
        gap: 8px;
        width: min(620px, 100%);
        min-width: 0;
      }
      .topbar-search-meta {
        margin: 0;
      }
      .search-results--floating {
        position: absolute;
        top: calc(100% + 8px);
        left: 0;
        width: min(560px, 100%);
        max-height: min(44vh, 420px);
        overflow: auto;
        padding: 10px;
        border-radius: 18px;
        border: 1px solid var(--surface-edge);
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.66), rgba(255, 255, 255, 0)),
          var(--surface-strong);
        backdrop-filter: blur(16px);
        box-shadow: var(--shadow-md);
      }
      .search-results--floating[hidden] {
        display: none;
      }
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
      .control-panel {
        position: absolute;
        top: 116px;
        right: 16px;
        z-index: 1120;
        width: min(288px, calc(100vw - 32px));
        max-height: calc(100vh - 208px);
        transition: transform 180ms ease, opacity 180ms ease;
      }
      .control-panel.is-collapsed {
        transform: translateX(calc(100% + 20px));
        opacity: 0;
        pointer-events: none;
      }
      .control-panel-card {
        position: relative;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        max-height: inherit;
        padding: 12px;
        border-radius: 24px;
        border: 1px solid var(--surface-edge);
        background:
          linear-gradient(180deg, rgba(255, 255, 255, 0.50), rgba(255, 255, 255, 0)),
          var(--surface-strong);
        backdrop-filter: blur(16px);
        box-shadow: var(--shadow-md);
      }
      .control-panel-card::before {
        content: "";
        position: absolute;
        inset: 0 0 auto;
        height: 1px;
        background: linear-gradient(90deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0));
        pointer-events: none;
      }
      .control-panel-head {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: flex-start;
        margin-bottom: 10px;
      }
      .control-panel-head-side {
        display: grid;
        justify-items: end;
        gap: 8px;
      }
      .control-panel-label,
      .control-group-label {
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .control-panel-title {
        margin: 4px 0 0;
        font-size: 15px;
        font-weight: 700;
      }
      .control-panel-summary,
      .control-group-summary {
        color: var(--muted);
        font-size: 11px;
      }
      .control-panel-body {
        display: grid;
        gap: 8px;
        overflow: auto;
        padding-right: 2px;
      }
      .control-group {
        display: grid;
        gap: 0;
        border: 1px solid rgba(24, 37, 61, 0.08);
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.68);
      }
      .control-group-head {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: center;
        padding: 10px 12px;
        cursor: pointer;
        list-style: none;
      }
      .control-group-head::-webkit-details-marker {
        display: none;
      }
      .control-group-head::marker {
        content: "";
      }
      .control-group-head::after {
        content: "+";
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        border-radius: 999px;
        background: rgba(20, 33, 61, 0.06);
        color: var(--ink-soft);
        font-size: 13px;
        font-weight: 700;
        flex: 0 0 auto;
      }
      .control-group[open] .control-group-head::after {
        content: "−";
      }
      .control-group-head h3 {
        margin: 4px 0 0;
        font-size: 13px;
      }
      .control-group-body {
        display: grid;
        gap: 10px;
        padding: 0 12px 12px;
      }
      .dock-actions,
      .dock-presets,
      .dock-layer-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .dock-layer-grid {
        align-items: stretch;
      }
      .dock-layer-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        border: 1px solid rgba(20, 33, 61, 0.12);
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.82);
        color: var(--ink-soft);
        font-size: 12px;
        font-weight: 600;
      }
      .dock-layer-chip input {
        margin: 0;
      }
      .dock-range-stack {
        display: grid;
        gap: 12px;
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
        .map-topbar {
          top: 12px;
          left: 12px;
          right: 12px;
        }
        .floating-legend {
          right: 12px;
          bottom: 76px;
        }
        .control-panel {
          top: 112px;
          right: 12px;
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
        .control-panel {
          position: fixed;
          left: 10px;
          right: 10px;
          top: auto;
          bottom: 10px;
          width: auto;
          max-height: min(72vh, 760px);
        }
        .control-panel.is-collapsed {
          transform: translateY(calc(100% + 24px));
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
        }
        .map-topbar-main {
          flex-direction: column;
          align-items: stretch;
          gap: 10px;
        }
        .topbar-row,
        .map-actions {
          justify-content: space-between;
        }
        .search-results--floating {
          width: 100%;
        }
        .floating-legend {
          right: 10px;
          bottom: 76px;
          width: min(248px, calc(100vw - 20px));
          max-height: min(34vh, 260px);
          padding: 12px;
          border-radius: 18px;
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
        .control-panel {
          left: 8px;
          right: 8px;
          bottom: 8px;
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
      <button id="mobile-scrim" class="mobile-scrim" type="button" aria-label="Close controls" aria-hidden="true"></button>
      <main class="map-stage">
        <div class="map-topbar">
          <div class="map-topbar-main">
            <div class="topbar-context">
              <span class="eyebrow">Nordic Atlas</span>
              <div class="topbar-title-row">
                <span class="topbar-title">__TITLE__</span>
                <span id="topbar-state-pill" class="topbar-state-pill">Loading live map state</span>
              </div>
            </div>
            <div class="topbar-row">
              <div class="basemap-switch">
                <button class="basemap-button is-active" type="button" data-basemap="voyager" title="Balanced roads, labels, and water detail."><span class="basemap-preview basemap-preview--voyager"></span><span class="basemap-title">Voyager</span></button>
                <button class="basemap-button" type="button" data-basemap="light" title="Minimal contrast for evidence-first inspection."><span class="basemap-preview basemap-preview--light"></span><span class="basemap-title">Light</span></button>
                <button class="basemap-button" type="button" data-basemap="terrain" title="Relief-focused context for landform reading."><span class="basemap-preview basemap-preview--terrain"></span><span class="basemap-title">Terrain</span></button>
              </div>
              <div class="map-actions">
                <button id="fit-active" class="toolbar-button is-primary" type="button">Fit active</button>
                <button id="reset-view" class="toolbar-button" type="button">Reset view</button>
                <button id="panel-toggle" class="toolbar-button" type="button">Hide controls</button>
                <button id="copy-link" class="toolbar-button" type="button">Copy link</button>
                <button id="help-toggle" class="toolbar-button" type="button">Help</button>
                <button id="fullscreen-toggle" class="toolbar-button" type="button">Fullscreen</button>
              </div>
            </div>
          </div>
          <div class="topbar-search">
            <label class="sr-only" for="search-input">Search points and sites</label>
            <div class="search-shell">
              <input id="search-input" class="search-input" type="search" placeholder="Search points and sites by sample, locality, source, or country" aria-describedby="search-count">
              <button id="search-clear" class="search-clear" type="button" aria-label="Clear search" hidden>×</button>
            </div>
            <div id="search-count" class="search-meta topbar-search-meta" aria-live="polite">Search points and sites</div>
            <div id="search-results" class="search-results search-results--floating" hidden></div>
          </div>
        </div>
        <div id="map" aria-label="__TITLE__"></div>
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
        <aside id="sidebar" class="control-panel" aria-label="Map controls">
          <div class="control-panel-card">
            <div class="control-panel-head">
              <div>
                <span class="control-panel-label">Map controls</span>
                <h2 class="control-panel-title">Filters</h2>
              </div>
              <div class="control-panel-head-side">
                <span id="control-panel-summary" class="control-panel-summary">Loading view state</span>
                <button id="mobile-panel-close" class="toolbar-button mobile-panel-close" type="button">Close</button>
              </div>
            </div>
            <div class="control-panel-body">
              <details class="control-group" open>
                <summary class="control-group-head">
                  <div>
                    <span class="control-group-label">Countries</span>
                    <h3>Country Filters</h3>
                  </div>
                  <span id="country-summary" class="control-group-summary" aria-live="polite">All countries visible</span>
                </summary>
                <div class="control-group-body">
                  <div id="country-filters" class="chip-grid"></div>
                  <div class="inline-actions">
                    <button id="countries-all" class="inline-button is-primary" type="button">Show all</button>
                    <button id="countries-none" class="inline-button" type="button">Hide all</button>
                    <button id="countries-fit" class="inline-button" type="button">Fit selected</button>
                  </div>
                </div>
              </details>
              <details class="control-group" open>
                <summary class="control-group-head">
                  <div>
                    <span class="control-group-label">Evidence</span>
                    <h3>Layer Selection</h3>
                  </div>
                  <span id="dock-layer-summary" class="control-group-summary">Loading enabled layers</span>
                </summary>
                <div class="control-group-body">
                  <div class="dock-actions">
                    <button class="inline-button" type="button" data-layer-preset="evidence">Evidence only</button>
                    <button class="inline-button" type="button" data-layer-preset="context">Context stack</button>
                    <button class="inline-button" type="button" data-layer-preset="orientation">Map framing</button>
                    <button class="inline-button is-primary" type="button" data-layer-preset="all">All layers</button>
                  </div>
                  <div id="dock-layer-filters" class="dock-layer-grid"></div>
                </div>
              </details>
              <details class="control-group" open>
                <summary class="control-group-head">
                  <div>
                    <span class="control-group-label">Time</span>
                    <h3>Date Window</h3>
                  </div>
                  <span id="dock-time-summary" class="control-group-summary">Loading BP range</span>
                </summary>
                <div class="control-group-body">
                  <div class="dock-range-stack">
                    <div>
                      <div class="field-label"><span>Window start</span><span id="time-start-value">__INITIAL_TIME_START_BP__ BP</span></div>
                      <label class="sr-only" for="time-start-slider">Time window start in years BP</label>
                      <input id="time-start-slider" class="range-input" type="range" min="__TIME_MIN_BP__" max="__TIME_MAX_BP__" step="1" value="__INITIAL_TIME_START_BP__">
                    </div>
                    <div>
                      <div class="field-label"><span>Window span</span><span id="time-interval-value">__INITIAL_TIME_INTERVAL__ years</span></div>
                      <label class="sr-only" for="time-interval-slider">Time window interval in years</label>
                      <input id="time-interval-slider" class="range-input" type="range" min="1" max="__TIME_INTERVAL_MAX__" step="1" value="__INITIAL_TIME_INTERVAL__">
                    </div>
                  </div>
                  <div class="dock-presets">
                    <button class="preset-button is-active" type="button" data-time-interval="100">100 years</button>
                    <button class="preset-button" type="button" data-time-interval="500">500 years</button>
                    <button class="preset-button" type="button" data-time-interval="1000">1000 years</button>
                    <button class="preset-button" type="button" data-time-interval="full">Full span</button>
                  </div>
                  <div id="time-record-count" class="search-meta">Calculating dated records in the active BP window.</div>
                </div>
              </details>
              <details class="control-group">
                <summary class="control-group-head">
                  <div>
                    <span class="control-group-label">Distance</span>
                    <h3>Acceptance Distance</h3>
                  </div>
                  <span id="diameter-value" class="control-group-summary">__INITIAL_DIAMETER__ km diameter</span>
                </summary>
                <div class="control-group-body">
                  <div class="field-label"><span>Search radius around visible point layers</span><span id="radius-value">__INITIAL_RADIUS__ km</span></div>
                  <label class="sr-only" for="diameter-slider">Acceptance diameter in kilometers</label>
                  <input id="diameter-slider" class="range-input" type="range" min="0" max="100" step="5" value="__INITIAL_DIAMETER__" aria-describedby="distance-help">
                  <div class="dock-presets">
                    <button class="preset-button" type="button" data-km="0">0 km</button>
                    <button class="preset-button" type="button" data-km="10">10 km</button>
                    <button class="preset-button is-active" type="button" data-km="20">20 km</button>
                    <button class="preset-button" type="button" data-km="30">30 km</button>
                    <button class="preset-button" type="button" data-km="50">50 km</button>
                  </div>
                  <div id="distance-help" class="search-meta">Distance circles are available only for point layers. Set to `0 km` to hide acceptance circles everywhere.</div>
                  <div class="field-label"><span>Archaeology density opacity</span><span id="density-opacity-value">60%</span></div>
                  <label class="sr-only" for="density-opacity-slider">Archaeology density opacity</label>
                  <input id="density-opacity-slider" class="range-input" type="range" min="0" max="100" step="5" value="60">
                  <div class="inline-actions">
                    <button id="restore-defaults" class="inline-button" type="button">Restore defaults</button>
                  </div>
                </div>
              </details>
            </div>
          </div>
        </aside>
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
              <div class="help-row"><span class="help-key">1</span><span>Use the short sidebar only for geography, search, and distance context.</span></div>
              <div class="help-row"><span class="help-key">2</span><span>Use the map dock above the status bar for frequent layer and BP-window changes.</span></div>
              <div class="help-row"><span class="help-key">3</span><span>Use the focus card to keep one selected record visible while the map continues moving.</span></div>
            </div>
          </section>
          <section class="help-card">
            <h3>Map dock</h3>
            <div class="help-list">
              <div class="help-row"><span class="help-key">Layers</span><span>Enable or disable evidence and context sources without reopening the sidebar.</span></div>
              <div class="help-row"><span class="help-key">Presets</span><span>`Evidence only`, `Context stack`, `Map framing`, and `All layers` reset the active layer stack quickly.</span></div>
              <div class="help-row"><span class="help-key">Time</span><span>The BP start and span sliders filter only layers that carry numeric BP dates.</span></div>
            </div>
          </section>
          <section class="help-card">
            <h3>Basemaps</h3>
            <div class="help-list">
              <div class="help-row"><span class="help-key">Voyager</span><span>Balanced roads, labels, and water detail.</span></div>
              <div class="help-row"><span class="help-key">Light</span><span>Minimal contrast for evidence-first inspection.</span></div>
              <div class="help-row"><span class="help-key">Terrain</span><span>Relief-focused context for landform reading.</span></div>
            </div>
          </section>
          <section class="help-card">
            <h3>Sidebar</h3>
            <div class="help-list">
              <div class="help-row"><span class="help-key">Workspace</span><span>Summarizes the active geography, evidence stack, and BP range without repeating every control on screen.</span></div>
              <div class="help-row"><span class="help-key">Countries</span><span>Country toggles affect every layer that carries country metadata.</span></div>
              <div class="help-row"><span class="help-key">Search</span><span>Search only scans currently visible point records, not hidden layers or filtered-out countries.</span></div>
            </div>
          </section>
          <section class="help-card">
            <h3>Status readout</h3>
            <div class="help-list">
              <div class="help-row"><span class="help-key">Zoom</span><span>The live Leaflet zoom level after fit, pan, or wheel interaction.</span></div>
              <div class="help-row"><span class="help-key">Center</span><span>The current map center in latitude and longitude.</span></div>
              <div class="help-row"><span class="help-key">Selection</span><span>The visible point and overlay count under the current workspace filters.</span></div>
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
      const mobilePanelCloseButton = document.getElementById('mobile-panel-close');
      const mobileScrim = document.getElementById('mobile-scrim');
      const mobileLayoutQuery = window.matchMedia('(max-width: 900px)');
      const panelToggleButton = document.getElementById('panel-toggle');
      const helpToggleButton = document.getElementById('help-toggle');
      const helpDialog = document.getElementById('help-dialog');
      const helpCloseButton = document.getElementById('help-close');
      const legendBody = document.getElementById('legend-body');
      const legendToggleButton = document.getElementById('legend-toggle');
      const countryFilters = document.getElementById('country-filters');
      const layerFilters = document.getElementById('dock-layer-filters');
      const legendItems = document.getElementById('legend-items');
      const searchInput = document.getElementById('search-input');
      const searchClearButton = document.getElementById('search-clear');
      const searchResults = document.getElementById('search-results');
      const searchCount = document.getElementById('search-count');
      const controlPanelSummary = document.getElementById('control-panel-summary');
      const dockLayerSummary = document.getElementById('dock-layer-summary');
      const dockTimeSummary = document.getElementById('dock-time-summary');
      const slider = document.getElementById('diameter-slider');
      const diameterValue = document.getElementById('diameter-value');
      const radiusValue = document.getElementById('radius-value');
      const timeStartSlider = document.getElementById('time-start-slider');
      const timeStartValue = document.getElementById('time-start-value');
      const timeIntervalSlider = document.getElementById('time-interval-slider');
      const timeIntervalValue = document.getElementById('time-interval-value');
      const timeRecordCount = document.getElementById('time-record-count');
      const densityOpacitySlider = document.getElementById('density-opacity-slider');
      const densityOpacityValue = document.getElementById('density-opacity-value');
      const emptyState = document.getElementById('empty-state');
      const densityRamp = document.getElementById('density-ramp');
      const countrySummary = document.getElementById('country-summary');
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
          dockTimeSummary.textContent = 'No BP dates available';
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
        dockTimeSummary.textContent = `${timeStartBp}-${endBp} BP`;
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
      function updatePanelToggleLabel() {
        const collapsed = sidebar.classList.contains('is-collapsed');
        if (mobileLayoutQuery.matches) {
          panelToggleButton.textContent = collapsed ? 'Show controls' : 'Hide controls';
          return;
        }
        panelToggleButton.textContent = collapsed ? 'Show controls' : 'Hide controls';
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
      function countActiveOverrides() {
        let count = 0;
        if (activeCountries.size !== COUNTRIES.length) count += 1;
        if (activeLayerKeys.size !== DEFAULT_LAYER_KEYS.length || DEFAULT_LAYER_KEYS.some((key) => !activeLayerKeys.has(key))) count += 1;
        if (TIME_HAS_DATA && (timeStartBp !== DEFAULT_TIME_START_BP || timeIntervalYears !== DEFAULT_TIME_INTERVAL_YEARS)) count += 1;
        if (Number(slider.value) !== __INITIAL_DIAMETER__) count += 1;
        if (Math.round(densityOpacity * 100) !== 60) count += 1;
        if (currentBasemap !== 'voyager') count += 1;
        return count;
      }
      function renderControlPanelSummary() {
        if (!controlPanelSummary) return;
        const activeOverrideCount = countActiveOverrides();
        controlPanelSummary.textContent = activeOverrideCount ? `${activeOverrideCount} active overrides` : 'Default view';
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
            const cards = layers.map((layer) => {
              const checked = activeLayerKeys.has(layer.key) ? 'checked' : '';
              const swatchColor = layerColor(layer);
              const swatchBorder = layer.style && layer.style.stroke ? layer.style.stroke : swatchColor;
              return `<label class="dock-layer-chip"><input class="layer-checkbox" type="checkbox" value="${escapeHtml(layer.key)}" ${checked} aria-label="Toggle ${escapeHtml(layer.label)}"><span class="chip-swatch" style="background:${escapeHtml(swatchColor)};border-color:${escapeHtml(swatchBorder)};"></span><span>${escapeHtml(layer.label)}</span></label>`;
            }).join('');
            return cards;
          })
          .join('');
        dockLayerSummary.textContent = activeLayerKeys.size ? `${activeLayerKeys.size} layers enabled` : 'No layers enabled';
        document.querySelectorAll('.layer-checkbox').forEach((checkbox) => {
          checkbox.addEventListener('change', () => {
            if (checkbox.checked) { activeLayerKeys.add(checkbox.value); } else { activeLayerKeys.delete(checkbox.value); }
            renderMapState();
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
        const datedVisibleCount = visiblePointEntries.filter(({ layer, feature }) => {
          if (!layer.applies_time_filter) return false;
          return Number.isFinite(Number(feature.time_year_bp));
        }).length;
        timeRecordCount.textContent = TIME_HAS_DATA
          ? `${datedVisibleCount} dated records are visible in the active BP window.`
          : 'No dated records are available for BP filtering.';
        const visiblePolygonLayers = renderedPolygonLayers.length;
        selectionReadout.textContent = `${visiblePointEntries.length} points · ${visiblePolygonLayers} overlays`;
        topbarStatePill.textContent = `${activeCountries.size} countries · ${enabledLayers} layers · ${visiblePointEntries.length} visible points`;
        countrySummary.textContent = activeCountries.size === COUNTRIES.length ? 'All countries visible' : activeCountries.size ? `${activeCountries.size} countries active` : 'No countries active';
      }
      function buildSearchResults() {
        const query = searchInput.value.trim().toLowerCase();
        searchClearButton.hidden = !query;
        if (!query) {
          searchCount.textContent = `${visiblePointEntries.length} visible points and sites`;
          searchResults.hidden = true;
          searchResults.innerHTML = '';
          return;
        }
        const matches = visiblePointEntries.filter(({ layer, feature }) => `${feature.title || ''} ${feature.subtitle || ''} ${feature.country || ''} ${layer.label || ''}`.toLowerCase().includes(query)).slice(0, 12);
        searchCount.textContent = `${matches.length} matches · ${visiblePointEntries.length} visible`;
        searchResults.hidden = false;
        searchResults.innerHTML = matches.map(({ layer, feature }, index) => `<button class="search-result" type="button" data-search-index="${index}"><strong>${escapeHtml(feature.title || '')}</strong><span>${escapeHtml(feature.subtitle || 'Unspecified type')}</span><div class="search-result-meta"><span class="search-badge">${escapeHtml(layer.label)}</span><span class="search-badge">${escapeHtml(feature.country || 'Unassigned')}</span></div></button>`).join('') || '<div class="summary-item"><span>No visible records match the current query.</span></div>';
        searchResults.querySelectorAll('[data-search-index]').forEach((button, index) => {
          button.addEventListener('click', () => {
            const match = matches[index];
            if (!match) return;
            focusPointAtVisibleIndex(visiblePointEntries.indexOf(match));
            map.flyTo([match.feature.latitude, match.feature.longitude], Math.max(map.getZoom(), 8), { duration: 0.7 });
            window.setTimeout(() => match.marker.openPopup(), 250);
            searchResults.hidden = true;
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
        renderControlPanelSummary();
        updateStats();
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
      searchInput.addEventListener('focus', buildSearchResults);
      searchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
          const firstResult = searchResults.querySelector('[data-search-index]');
          if (firstResult) firstResult.click();
        }
      });
      document.addEventListener('click', (event) => {
        if (!searchResults.contains(event.target) && event.target !== searchInput) {
          searchResults.hidden = true;
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
      document.querySelectorAll('[data-layer-preset]').forEach((button) => {
        button.addEventListener('click', () => applyLayerPreset(button.dataset.layerPreset));
      });
      legendToggleButton.addEventListener('click', () => setLegendCollapsed(!legendCollapsed));
      window.addEventListener('resize', () => window.setTimeout(() => map.invalidateSize(), 120));
      densityOpacitySlider.value = String(Math.round(densityOpacity * 100));
      slider.value = String(Number(initialState.diameter || __INITIAL_DIAMETER__));
      setPanelCollapsed(panelPreferenceFromHash() ?? defaultPanelCollapsed(), false);
      renderCountryControls();
      renderLayerControls();
      renderMapState();
      setBasemap(currentBasemap);
      setLegendCollapsed(legendCollapsed, false);
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
