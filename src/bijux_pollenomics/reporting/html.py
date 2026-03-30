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
        --ink: #14213d;
        --muted: #5f6b85;
        --surface: rgba(251, 248, 242, 0.92);
        --surface-strong: rgba(255, 252, 247, 0.96);
        --surface-edge: rgba(27, 40, 64, 0.12);
        --blue: #2563eb;
        --teal: #0f766e;
        --gold: #b45309;
        --rose: #b91c1c;
        --shadow-lg: 0 24px 64px rgba(20, 33, 61, 0.18);
        --shadow-md: 0 10px 32px rgba(20, 33, 61, 0.12);
      }
      * { box-sizing: border-box; }
      html, body {
        margin: 0;
        min-height: 100%;
        background:
          radial-gradient(circle at top left, rgba(37, 99, 235, 0.16), transparent 30%),
          radial-gradient(circle at right center, rgba(180, 83, 9, 0.12), transparent 22%),
          linear-gradient(180deg, #f8f4ee 0%, #efe7dc 100%);
        color: var(--ink);
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      }
      body { min-height: 100vh; }
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
        border: 1px solid var(--surface-edge);
        border-radius: 28px;
        background: linear-gradient(180deg, rgba(255, 252, 247, 0.97), rgba(246, 241, 233, 0.92));
        backdrop-filter: blur(18px);
        box-shadow: var(--shadow-lg);
      }
      .map-stage { position: relative; min-height: 100vh; }
      #map { height: 100vh; width: 100%; }
      .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.12);
        color: var(--blue);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      h1 {
        margin: 16px 0 10px;
        font-family: "Avenir Next", "Segoe UI Semibold", "Helvetica Neue", Arial, sans-serif;
        font-size: clamp(32px, 4vw, 44px);
        line-height: 1;
      }
      .lede {
        margin: 0 0 22px;
        color: var(--muted);
        font-size: 15px;
        line-height: 1.7;
      }
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 18px;
      }
      .stat-card,
      .panel-card,
      .floating-legend,
      .map-topbar,
      .map-status {
        border: 1px solid var(--surface-edge);
        background: var(--surface);
        backdrop-filter: blur(16px);
        box-shadow: var(--shadow-md);
      }
      .stat-card { padding: 16px; border-radius: 18px; }
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
      .section-stack { display: grid; gap: 16px; }
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
        background: rgba(255, 255, 255, 0.88);
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
        box-shadow: 0 8px 24px rgba(20, 33, 61, 0.10);
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
      .basemap-switch,
      .map-actions {
        display: flex;
        flex-wrap: wrap;
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
      .search-input {
        padding: 12px 14px;
        border-radius: 14px;
        border: 1px solid rgba(20, 33, 61, 0.14);
        background: rgba(255, 255, 255, 0.95);
        color: var(--ink);
        font: inherit;
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
      .search-results,
      .summary-list,
      .legend-list,
      .layer-stack {
        display: grid;
        gap: 10px;
      }
      .search-result,
      .summary-item,
      .layer-card {
        padding: 12px 14px;
        border: 1px solid rgba(20, 33, 61, 0.10);
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.76);
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
      .layer-card-top {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: flex-start;
      }
      .layer-card label {
        display: flex;
        gap: 10px;
        align-items: flex-start;
        width: 100%;
      }
      .layer-card input { margin-top: 3px; }
      .layer-group {
        display: grid;
        gap: 10px;
      }
      .layer-group-head {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: baseline;
        padding: 0 2px;
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
      }
      .legend-title { font-size: 13px; font-weight: 700; margin-bottom: 10px; }
      .legend-list { margin-bottom: 14px; }
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
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        padding: 12px 16px;
        border-radius: 999px;
        color: var(--muted);
        font-size: 12px;
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
          justify-content: space-between;
        }
      }
      @media (max-width: 900px) {
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
        .topbar-row,
        .map-actions {
          justify-content: space-between;
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
        .sidebar:not(.is-collapsed) ~ .map-stage .map-status {
          opacity: 0;
          pointer-events: none;
          transform: translateY(12px);
        }
        .map-status {
          left: 10px;
          right: 10px;
          bottom: 10px;
          border-radius: 18px;
          justify-content: space-between;
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
        .stats-grid { grid-template-columns: 1fr 1fr; }
        .map-topbar {
          left: 8px;
          right: 8px;
          top: 8px;
        }
        .floating-legend {
          right: 8px;
          bottom: 72px;
          width: min(220px, calc(100vw - 16px));
          padding: 10px;
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
          <span class="eyebrow">Nordic Multi-Evidence Map</span>
          <h1>__TITLE__</h1>
          <p class="lede">
            A shared decision map for ancient DNA, pollen, environmental archaeology, and archaeology context.
            AADR `__VERSION__` is one input to this view, not the whole map. Use the filters, search, time-window, and acceptance-distance controls to compare evidence in one workspace.
          </p>
          <section class="stats-grid">
            <div class="stat-card"><span class="stat-label">Visible Points</span><strong class="stat-value" id="stat-visible-points">0</strong></div>
            <div class="stat-card"><span class="stat-label">Visible Overlays</span><strong class="stat-value" id="stat-visible-layers">0</strong></div>
            <div class="stat-card"><span class="stat-label">Active Countries</span><strong class="stat-value" id="stat-visible-countries">0</strong></div>
            <div class="stat-card"><span class="stat-label">Acceptance Radius</span><strong class="stat-value" id="stat-radius">0 km</strong></div>
            <div class="stat-card"><span class="stat-label">AADR Release</span><strong class="stat-value stat-value--compact">__VERSION__</strong></div>
            <div class="stat-card"><span class="stat-label">Context Sources</span><strong class="stat-value stat-value--compact" id="stat-context-sources">0</strong></div>
          </section>
          <div class="section-stack">
            <section class="panel-card">
              <div class="section-head"><h2>Map Scope</h2><span>What is included</span></div>
              <p class="panel-copy">This map combines one primary evidence layer with environmental and archaeological context. Coverage is not identical across sources, so every layer card states its geographic scope.</p>
              <div id="scope-summary" class="summary-list"></div>
            </section>
            <section class="panel-card">
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
            <section class="panel-card">
              <div class="section-head"><h2>Research Layers</h2><span id="layer-summary" aria-live="polite">All layers enabled</span></div>
              <p class="panel-copy">Layers are grouped by role so the map separates primary evidence, environmental context, archaeology context, and orientation aids.</p>
              <div id="layer-filters" class="layer-stack"></div>
            </section>
            <section class="panel-card">
              <div class="section-head"><h2>Search Visible Records</h2><span id="search-count" aria-live="polite">0 matches</span></div>
              <label class="sr-only" for="search-input">Search visible records</label>
              <input id="search-input" class="search-input" type="search" placeholder="Search by sample ID, locality, site name, or source" aria-describedby="search-meta">
              <div id="search-meta" class="search-meta">Search only scans records that are visible under the current country and layer filters. Press Enter to jump to the first visible match.</div>
              <div id="search-results" class="search-results"></div>
            </section>
            <section class="panel-card">
              <div class="section-head"><h2>Time Window</h2><span id="time-window-value">__INITIAL_TIME_START_BP__-__INITIAL_TIME_END_BP__ BP</span></div>
              <div class="field-label"><span>Window start (years BP)</span><span id="time-start-value">__INITIAL_TIME_START_BP__ BP</span></div>
              <label class="sr-only" for="time-start-slider">Time window start in years BP</label>
              <input id="time-start-slider" class="range-input" type="range" min="__TIME_MIN_BP__" max="__TIME_MAX_BP__" step="1" value="__INITIAL_TIME_START_BP__">
              <div class="field-label" style="margin-top: 16px;"><span>Window interval</span><span id="time-interval-value">__INITIAL_TIME_INTERVAL__ years</span></div>
              <label class="sr-only" for="time-interval-slider">Time window interval in years</label>
              <input id="time-interval-slider" class="range-input" type="range" min="1" max="__TIME_INTERVAL_MAX__" step="1" value="__INITIAL_TIME_INTERVAL__">
              <div id="time-help" class="search-meta">Point records with `Date mean in BP` are filtered to the active window. Default interval is `100 years` and can be adjusted.</div>
            </section>
            <section class="panel-card">
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
            <section class="panel-card">
              <div class="section-head"><h2>Active View</h2><span>Live provenance</span></div>
              <div id="active-summary" class="summary-list"></div>
            </section>
          </div>
        </div>
      </aside>
      <main class="map-stage">
        <div class="map-topbar">
          <div class="topbar-row">
            <button id="panel-toggle" class="toolbar-button" type="button">Hide panel</button>
            <div class="basemap-switch">
              <button class="basemap-button is-active" type="button" data-basemap="voyager">Voyager</button>
              <button class="basemap-button" type="button" data-basemap="light">Light</button>
              <button class="basemap-button" type="button" data-basemap="terrain">Terrain</button>
            </div>
          </div>
          <div class="map-actions">
            <button id="fit-active" class="toolbar-button is-primary" type="button">Fit active</button>
            <button id="reset-view" class="toolbar-button" type="button">Reset view</button>
            <button id="copy-link" class="toolbar-button" type="button">Copy link</button>
            <button id="fullscreen-toggle" class="toolbar-button" type="button">Fullscreen</button>
          </div>
        </div>
        <div id="map" aria-label="__TITLE__ research map"></div>
        <div id="empty-state" class="empty-state" hidden>
          <strong>No visible records</strong>
          <span>Change the country filters, re-enable one or more layers, or restore the default map state.</span>
        </div>
        <div id="floating-legend" class="floating-legend">
          <div class="legend-title">Legend</div>
          <div id="legend-items" class="legend-list"></div>
          <div id="density-ramp" class="density-ramp">
            <div class="legend-item"><span class="legend-swatch" style="background: rgba(37, 99, 235, 0.10); border-color: rgba(37, 99, 235, 0.45);"></span><span>Acceptance circles use semi-transparent fills so overlap remains visible.</span></div>
            <div class="legend-item"><span class="legend-swatch" style="background: rgba(239, 68, 68, 0.22); border-color: #7f1d1d;"></span><span>RAÄ archaeology density shows Swedish `Fornlämning` counts in 1° grid cells.</span></div>
            <div class="density-bar"><span></span><span></span><span></span><span></span><span></span><span></span></div>
            <div class="density-labels"><span>Lower density</span><span>Higher density</span></div>
          </div>
        </div>
        <div class="map-status">
          <span id="zoom-readout">Zoom --</span>
          <span id="cursor-readout">Cursor --</span>
          <span id="selection-readout">Visible --</span>
        </div>
      </main>
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
      const sidebar = document.getElementById('sidebar');
      const mobileLayoutQuery = window.matchMedia('(max-width: 900px)');
      const panelToggleButton = document.getElementById('panel-toggle');
      const countryFilters = document.getElementById('country-filters');
      const layerFilters = document.getElementById('layer-filters');
      const legendItems = document.getElementById('legend-items');
      const scopeSummary = document.getElementById('scope-summary');
      const searchInput = document.getElementById('search-input');
      const searchResults = document.getElementById('search-results');
      const searchCount = document.getElementById('search-count');
      const slider = document.getElementById('diameter-slider');
      const diameterValue = document.getElementById('diameter-value');
      const radiusValue = document.getElementById('radius-value');
      const timeStartSlider = document.getElementById('time-start-slider');
      const timeStartValue = document.getElementById('time-start-value');
      const timeIntervalSlider = document.getElementById('time-interval-slider');
      const timeIntervalValue = document.getElementById('time-interval-value');
      const timeWindowValue = document.getElementById('time-window-value');
      const densityOpacitySlider = document.getElementById('density-opacity-slider');
      const densityOpacityValue = document.getElementById('density-opacity-value');
      const emptyState = document.getElementById('empty-state');
      const densityRamp = document.getElementById('density-ramp');
      const countrySummary = document.getElementById('country-summary');
      const layerSummary = document.getElementById('layer-summary');
      const activeSummary = document.getElementById('active-summary');
      const selectionReadout = document.getElementById('selection-readout');
      const zoomReadout = document.getElementById('zoom-readout');
      const cursorReadout = document.getElementById('cursor-readout');
      const statVisiblePoints = document.getElementById('stat-visible-points');
      const statVisibleLayers = document.getElementById('stat-visible-layers');
      const statVisibleCountries = document.getElementById('stat-visible-countries');
      const statRadius = document.getElementById('stat-radius');
      const statContextSources = document.getElementById('stat-context-sources');
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
        document.querySelectorAll('.preset-button').forEach((button) => {
          button.classList.toggle('is-active', Number(button.dataset.km) === Number(slider.value));
        });
      }
      function updatePanelToggleLabel() {
        const collapsed = sidebar.classList.contains('is-collapsed');
        if (mobileLayoutQuery.matches) {
          panelToggleButton.textContent = collapsed ? 'Show filters' : 'Hide filters';
          return;
        }
        panelToggleButton.textContent = collapsed ? 'Show panel' : 'Hide panel';
      }
      function setPanelCollapsed(collapsed, persist = true) {
        sidebar.classList.toggle('is-collapsed', collapsed);
        updatePanelToggleLabel();
        window.setTimeout(() => map.invalidateSize(), 180);
        if (persist) syncHashState();
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
        const nextHash = params.toString();
        const desiredHash = nextHash ? `#${nextHash}` : '';
        if (window.location.hash !== desiredHash) window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}${desiredHash}`);
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
              return `<div class="layer-card"><label><input class="layer-checkbox" type="checkbox" value="${escapeHtml(layer.key)}" ${checked} aria-label="Toggle ${escapeHtml(layer.label)}"><div style="width:100%;"><div class="layer-card-top"><div><strong>${escapeHtml(layer.label)}</strong><span>${escapeHtml(layer.description)}</span></div><span class="layer-badge" id="layer-count-${escapeHtml(layer.key)}">${escapeHtml(String(layer.count))} ${escapeHtml(layerUnit(layer))}</span></div><div class="layer-meta"><span><strong>Source</strong> ${escapeHtml(layer.source_name || layer.label)}</span><span><strong>Coverage</strong> ${escapeHtml(layer.coverage_label || '')}</span><span><strong>Geometry</strong> ${escapeHtml(layer.geometry_label || layerUnit(layer))}</span></div></div></label></div>`;
            }).join('');
            return `<section class="layer-group"><div class="layer-group-head"><h3>${escapeHtml(layerGroupLabel(group))}</h3><span>${escapeHtml(layerGroupSummary(group))}</span></div>${cards}</section>`;
          })
          .join('');
        document.querySelectorAll('.layer-checkbox').forEach((checkbox) => {
          checkbox.addEventListener('change', () => {
            if (checkbox.checked) { activeLayerKeys.add(checkbox.value); } else { activeLayerKeys.delete(checkbox.value); }
            renderMapState();
          });
        });
      }
      function renderLegend() {
        const activeLegendLayers = ALL_LAYERS.filter((layer) => activeLayerKeys.has(layer.key));
        legendItems.innerHTML = activeLegendLayers.map((layer) => `<div class="legend-item"><span class="legend-swatch" style="background:${escapeHtml(layerColor(layer))};border-color:${escapeHtml(layer.style.stroke || layerColor(layer))};"></span><span>${escapeHtml(layer.label)}: ${escapeHtml(layer.description)} ${layer.coverage_label ? `(${escapeHtml(layer.coverage_label)})` : ''}</span></div>`).join('') || '<div class="legend-item"><span>No layers are visible. Restore defaults or enable one or more layers.</span></div>';
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
            clusterGroup.addLayer(marker);
            visiblePointEntries.push({ layer, feature, marker });
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
        statVisiblePoints.textContent = String(visiblePointEntries.length);
        statVisibleLayers.textContent = String(enabledLayers);
        statVisibleCountries.textContent = String(activeCountries.size);
        statRadius.textContent = `${(Number(slider.value) / 2).toFixed(1)} km`;
        statContextSources.textContent = String(ALL_LAYERS.filter((layer) => layer.key !== 'aadr').length);
        const visiblePolygonLayers = renderedPolygonLayers.length;
        selectionReadout.textContent = `Visible points ${visiblePointEntries.length} · overlays ${visiblePolygonLayers}`;
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
        if (!query) {
          const initial = visiblePointEntries.slice(0, 8);
          searchCount.textContent = `${visiblePointEntries.length} visible records`;
          searchResults.innerHTML = initial.map(({ layer, feature }, index) => `<button class="search-result" type="button" data-search-index="${index}"><strong>${escapeHtml(feature.title || '')}</strong><span>${escapeHtml(layer.label)} · ${escapeHtml(feature.subtitle || '')} · ${escapeHtml(feature.country || 'Unassigned')}</span></button>`).join('') || '<div class="summary-item"><span>No visible point records are available under the current filters.</span></div>';
          searchResults.querySelectorAll('[data-search-index]').forEach((button, index) => {
            button.addEventListener('click', () => {
              const match = initial[index];
              if (!match) return;
              map.flyTo([match.feature.latitude, match.feature.longitude], Math.max(map.getZoom(), 8), { duration: 0.7 });
              window.setTimeout(() => match.marker.openPopup(), 250);
            });
          });
          return;
        }
        const matches = visiblePointEntries.filter(({ layer, feature }) => `${feature.title || ''} ${feature.subtitle || ''} ${feature.country || ''} ${layer.label || ''}`.toLowerCase().includes(query)).slice(0, 12);
        searchCount.textContent = `${matches.length} matches`;
        searchResults.innerHTML = matches.map(({ layer, feature }, index) => `<button class="search-result" type="button" data-search-index="${index}"><strong>${escapeHtml(feature.title || '')}</strong><span>${escapeHtml(layer.label)} · ${escapeHtml(feature.subtitle || '')} · ${escapeHtml(feature.country || 'Unassigned')}</span></button>`).join('') || '<div class="summary-item"><span>No visible records match the current query.</span></div>';
        searchResults.querySelectorAll('[data-search-index]').forEach((button, index) => {
          button.addEventListener('click', () => {
            const match = matches[index];
            if (!match) return;
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
        updateStats();
        updateSummary();
        buildSearchResults();
        syncPresetButtons();
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
      slider.addEventListener('input', renderMapState);
      timeStartSlider.addEventListener('input', () => { timeStartBp = Number(timeStartSlider.value); renderMapState(); });
      timeIntervalSlider.addEventListener('input', () => { timeIntervalYears = Number(timeIntervalSlider.value); renderMapState(); });
      densityOpacitySlider.addEventListener('input', () => { densityOpacity = Number(densityOpacitySlider.value) / 100; renderMapState(); });
      document.querySelectorAll('.preset-button').forEach((button) => {
        button.addEventListener('click', () => {
          slider.value = button.dataset.km;
          renderMapState();
        });
      });
      searchInput.addEventListener('input', buildSearchResults);
      searchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
          const firstResult = searchResults.querySelector('[data-search-index]');
          if (firstResult) firstResult.click();
        }
      });
      map.on('zoomend', () => { zoomReadout.textContent = `Zoom ${map.getZoom().toFixed(1)}`; });
      map.on('mousemove', (event) => { cursorReadout.textContent = `Cursor ${event.latlng.lat.toFixed(3)}, ${event.latlng.lng.toFixed(3)}`; });
      document.addEventListener('fullscreenchange', () => window.setTimeout(() => map.invalidateSize(), 160));
      mobileLayoutQuery.addEventListener('change', () => {
        if (panelPreferenceFromHash() === null) {
          setPanelCollapsed(defaultPanelCollapsed(), false);
          return;
        }
        updatePanelToggleLabel();
      });
      window.addEventListener('resize', () => window.setTimeout(() => map.invalidateSize(), 120));
      densityOpacitySlider.value = String(Math.round(densityOpacity * 100));
      slider.value = String(Number(initialState.diameter || __INITIAL_DIAMETER__));
      setPanelCollapsed(panelPreferenceFromHash() ?? defaultPanelCollapsed(), false);
      renderScopeSummary();
      renderCountryControls();
      renderLayerControls();
      renderMapState();
      setBasemap(currentBasemap);
      resetView();
      zoomReadout.textContent = `Zoom ${map.getZoom().toFixed(1)}`;
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
