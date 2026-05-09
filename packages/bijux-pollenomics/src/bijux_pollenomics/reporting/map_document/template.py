from __future__ import annotations

MAP_DOCUMENT_TEMPLATE = """
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
      .topbar-note {
        margin: 10px 0 0;
        max-width: 720px;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.6;
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
      .legend-item--compact {
        gap: 8px;
        font-size: 11px;
      }
      .legend-item-copy {
        display: grid;
        gap: 2px;
      }
      .legend-item-title {
        color: var(--ink-soft);
        font-weight: 700;
      }
      .legend-item-meta {
        color: var(--muted);
        font-size: 11px;
      }
      .legend-pill-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .legend-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 10px;
        border: 1px solid rgba(20, 33, 61, 0.10);
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.82);
        color: var(--ink-soft);
        font-size: 11px;
        font-weight: 600;
      }
      .legend-pill-note {
        color: var(--muted);
        font-weight: 500;
      }
      .animal-insight-panel {
        display: grid;
        gap: 14px;
        padding: 14px;
        border: 1px solid rgba(20, 33, 61, 0.10);
        border-radius: 18px;
        background:
          linear-gradient(180deg, rgba(255, 252, 247, 0.98), rgba(255, 255, 255, 0.90)),
          rgba(255, 255, 255, 0.92);
      }
      .animal-insight-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
      }
      .animal-insight-kicker {
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .animal-insight-title {
        margin: 4px 0 0;
        color: var(--ink-soft);
        font-size: 15px;
        font-weight: 700;
      }
      .animal-insight-state {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(20, 33, 61, 0.06);
        color: var(--ink-soft);
        font-size: 11px;
        font-weight: 700;
        text-align: center;
      }
      .animal-insight-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
      }
      .animal-insight-stat {
        display: grid;
        gap: 4px;
        padding: 10px 12px;
        border-radius: 14px;
        border: 1px solid rgba(20, 33, 61, 0.08);
        background: rgba(255, 255, 255, 0.88);
      }
      .animal-insight-stat-value {
        color: var(--ink-soft);
        font-size: 16px;
        font-weight: 800;
      }
      .animal-insight-stat-label {
        color: var(--muted);
        font-size: 11px;
        line-height: 1.4;
      }
      .animal-insight-subsection {
        display: grid;
        gap: 8px;
      }
      .animal-insight-subtitle {
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .animal-insight-mix {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .animal-insight-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 7px 10px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.90);
        border: 1px solid rgba(20, 33, 61, 0.08);
        color: var(--ink-soft);
        font-size: 11px;
        font-weight: 600;
      }
      .animal-insight-chip strong {
        font-size: 12px;
      }
      .animal-insight-copy {
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
      .popup-card {
        display: grid;
        gap: 12px;
        min-width: 260px;
      }
      .popup-kicker {
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .popup-headline {
        display: grid;
        gap: 4px;
      }
      .popup-title {
        color: var(--ink-soft);
        font-size: 16px;
        font-weight: 800;
        line-height: 1.3;
      }
      .popup-subtitle {
        color: var(--muted);
        font-size: 12px;
        line-height: 1.5;
      }
      .popup-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .popup-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 9px;
        border-radius: 999px;
        background: rgba(20, 33, 61, 0.06);
        color: var(--ink-soft);
        font-size: 11px;
        font-weight: 700;
      }
      .popup-badge--warning {
        background: rgba(180, 83, 9, 0.12);
        color: #9a3412;
      }
      .popup-section {
        display: grid;
        gap: 8px;
        padding: 10px 12px;
        border-radius: 14px;
        border: 1px solid rgba(20, 33, 61, 0.08);
        background: rgba(255, 255, 255, 0.92);
      }
      .popup-section-title {
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .popup-row {
        display: grid;
        gap: 2px;
      }
      .popup-row-label {
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
      }
      .popup-row-value {
        color: var(--ink-soft);
        font-size: 12px;
        line-height: 1.5;
        word-break: break-word;
      }
      .popup-warning-list {
        display: grid;
        gap: 8px;
      }
      .popup-warning {
        padding: 9px 10px;
        border-radius: 12px;
        background: rgba(180, 83, 9, 0.10);
        color: #9a3412;
        font-size: 12px;
        line-height: 1.5;
      }
      .popup-media-list {
        display: inline-flex;
        flex-wrap: wrap;
        gap: 8px;
        vertical-align: middle;
      }
      .popup-media-link {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 9px;
        border-radius: 999px;
        border: 1px solid rgba(37, 99, 235, 0.18);
        background: rgba(37, 99, 235, 0.08);
        color: #1e3a8a;
        text-decoration: none;
        font-weight: 600;
      }
      .popup-media-link:hover {
        background: rgba(37, 99, 235, 0.14);
      }
      .popup-media-link svg {
        width: 14px;
        height: 14px;
        flex: 0 0 auto;
      }
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
          width: min(264px, calc(100vw - 20px));
          max-height: min(38vh, 300px);
          padding: 12px;
          border-radius: 18px;
        }
        .animal-insight-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .popup-card {
          min-width: 0;
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
          width: min(236px, calc(100vw - 16px));
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
        .animal-insight-grid {
          grid-template-columns: 1fr;
        }
        .animal-insight-head {
          flex-direction: column;
          align-items: flex-start;
        }
        .animal-insight-state {
          width: fit-content;
        }
        .popup-title {
          font-size: 15px;
        }
        .popup-subtitle,
        .popup-row-value,
        .popup-warning {
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
              <span class="eyebrow">__SCOPE_BADGE__</span>
              <div class="topbar-title-row">
                <span class="topbar-title">__TITLE__</span>
                <span id="topbar-state-pill" class="topbar-state-pill">Loading live map state</span>
              </div>
              <p class="topbar-note">__SCOPE_NOTE__</p>
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
                    <span class="control-group-label">Animal aDNA</span>
                    <h3>Animal Evidence</h3>
                  </div>
                  <span id="animal-filter-summary" class="control-group-summary">All animal evidence visible</span>
                </summary>
                <div class="control-group-body">
                  <div>
                    <div class="field-label"><span>Animal Scope</span><span>Domesticated-core or comparator</span></div>
                    <div id="animal-scope-filters" class="dock-presets"></div>
                  </div>
                  <div>
                    <div class="field-label"><span>Species Focus</span><span>One species at a time if needed</span></div>
                    <div id="animal-species-filters" class="dock-layer-grid"></div>
                  </div>
                  <div>
                    <div class="field-label"><span>Coordinate Confidence</span><span>Keep point trust visible while filtering</span></div>
                    <div id="animal-confidence-filters" class="dock-presets"></div>
                  </div>
                  <div>
                    <div class="field-label"><span>Temporal Windows</span><span>Inspect temporal structure without forcing false precision</span></div>
                    <div id="animal-temporal-window-filters" class="dock-presets"></div>
                  </div>
                  <label class="chip-toggle">
                    <input id="animal-nordic-only" type="checkbox" aria-label="Restrict animal evidence to Nordic leads only">
                    <span class="chip-swatch" style="background: rgba(8, 145, 178, 0.18); border-color: rgba(14, 116, 144, 0.78);"></span>
                    <span>Nordic animal leads only</span>
                  </label>
                  <section class="animal-insight-panel" aria-live="polite" aria-label="Animal evidence summary">
                    <div class="animal-insight-head">
                      <div>
                        <span class="animal-insight-kicker">Atlas-side summary</span>
                        <h4 class="animal-insight-title">Visible animal evidence</h4>
                      </div>
                      <span id="animal-evidence-state" class="animal-insight-state">Loading evidence posture</span>
                    </div>
                    <div id="animal-evidence-metrics" class="animal-insight-grid"></div>
                    <div class="animal-insight-subsection">
                      <span class="animal-insight-subtitle">Coordinate trust mix</span>
                      <div id="animal-evidence-confidence" class="animal-insight-mix"></div>
                    </div>
                  </section>
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
                    <button class="preset-button" type="button" data-time-interval="100">100 years</button>
                    <button class="preset-button" type="button" data-time-interval="500">500 years</button>
                    <button class="preset-button" type="button" data-time-interval="1000">1000 years</button>
                    <button class="preset-button is-active" type="button" data-time-interval="full">Full span</button>
                  </div>
                  <div id="time-record-count" class="search-meta">Calculating time-aware records in the active BP window.</div>
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
              <div class="help-row"><span class="help-key">Time</span><span>The BP start and span sliders filter layers that carry BP dates or BP coverage ranges.</span></div>
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
      const LAYER_GROUP_DEFINITIONS = [
        { key: 'primary-evidence', label: 'Human aDNA' },
        { key: 'animal-domesticated-evidence', label: 'Domesticated animal aDNA' },
        { key: 'animal-comparator-evidence', label: 'Comparator animal aDNA' },
        { key: 'environmental-context', label: 'Environmental context' },
        { key: 'archaeology-context', label: 'Archaeology context' },
        { key: 'orientation', label: 'Orientation layers' },
      ];
      const ANIMAL_LAYER_GROUPS = new Set(['animal-domesticated-evidence', 'animal-comparator-evidence']);
      const ANIMAL_SPECIES = Array.from(
        new Map(
          POINT_LAYERS
            .filter((layer) => ANIMAL_LAYER_GROUPS.has(layer.group) && layer.species_latin_name)
            .map((layer) => [
              layer.species_latin_name,
              {
                latinName: layer.species_latin_name,
                commonName: layer.species_common_name || layer.label || layer.species_latin_name,
                fill: layer.style && layer.style.fill ? layer.style.fill : '#475569',
                stroke: layer.style && layer.style.stroke ? layer.style.stroke : '#1e293b',
                animalScope: layer.animal_scope || '',
              },
            ])
        ).values()
      );
      const ANIMAL_COORDINATE_CONFIDENCES = Array.from(
        new Set(
          POINT_LAYERS
            .filter((layer) => ANIMAL_LAYER_GROUPS.has(layer.group))
            .flatMap((layer) => (layer.features || []).map((feature) => String(feature.coordinate_confidence || '').trim()).filter(Boolean))
        )
      );
      const ANIMAL_TEMPORAL_WINDOWS = Array.from(
        new Set(
          POINT_LAYERS
            .filter((layer) => ANIMAL_LAYER_GROUPS.has(layer.group))
            .flatMap((layer) => (layer.features || []).map((feature) => feature.temporal_window_label).filter(Boolean))
        )
      );
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
      basemaps.__INITIAL_BASEMAP__.addTo(map);
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
      const animalFilterSummary = document.getElementById('animal-filter-summary');
      const animalScopeFilters = document.getElementById('animal-scope-filters');
      const animalSpeciesFilters = document.getElementById('animal-species-filters');
      const animalConfidenceFilters = document.getElementById('animal-confidence-filters');
      const animalTemporalWindowFilters = document.getElementById('animal-temporal-window-filters');
      const animalNordicOnlyCheckbox = document.getElementById('animal-nordic-only');
      const animalEvidenceMetrics = document.getElementById('animal-evidence-metrics');
      const animalEvidenceConfidence = document.getElementById('animal-evidence-confidence');
      const animalEvidenceState = document.getElementById('animal-evidence-state');
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
          animalSpecies: params.get('animal_species'),
          animalScope: params.get('animal_scope'),
          animalConfidence: params.get('animal_confidence'),
          animalTemporalWindow: params.get('animal_time_window') || params.get('animal_chronology'),
          animalNordic: params.get('animal_nordic'),
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
      function normalizedSingleValue(raw, allowed, fallbackValue) {
        const value = String(raw || '').trim();
        return allowed.includes(value) ? value : fallbackValue;
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
      let activeAnimalSpecies = normalizedSingleValue(
        initialState.animalSpecies,
        ['all', ...ANIMAL_SPECIES.map((species) => species.latinName)],
        'all'
      );
      let activeAnimalScope = normalizedSingleValue(
        initialState.animalScope,
        ['all', 'domesticated_core', 'comparator'],
        'all'
      );
      let activeAnimalConfidence = normalizedSingleValue(
        initialState.animalConfidence,
        ['all', ...ANIMAL_COORDINATE_CONFIDENCES],
        'all'
      );
      let activeAnimalTemporalWindow = normalizedSingleValue(
        initialState.animalTemporalWindow,
        ['all', ...ANIMAL_TEMPORAL_WINDOWS],
        'all'
      );
      let animalNordicOnly = initialState.animalNordic === 'only';
      let timeIntervalYears = TIME_HAS_DATA ? clampTimeInterval(initialState.timeInterval) : DEFAULT_TIME_INTERVAL_YEARS;
      let timeStartBp = TIME_HAS_DATA ? clampTimeStart(initialState.timeStart, timeIntervalYears) : DEFAULT_TIME_START_BP;
      let densityOpacity = Math.max(0, Math.min(1, Number(initialState.density || '60') / 100 || 0.6));
      let currentBasemap = basemaps[initialState.basemap || ''] ? String(initialState.basemap) : '__INITIAL_BASEMAP__';
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
      function normalizedMediaLinks(value) {
        if (!Array.isArray(value)) return [];
        return value.filter((link) => link && link.label && link.url);
      }
      function mediaIconSvg(kind) {
        if (kind === 'video') {
          return '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M4 6h11a2 2 0 0 1 2 2v1.2l3.4-2.26A1 1 0 0 1 22 7.77v8.46a1 1 0 0 1-1.6.83L17 14.8V16a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2Zm0 2v8h11V8H4Z"/></svg>';
        }
        return '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M9 4.5 7.5 6H5a2 2 0 0 0-2 2v8.5a2.5 2.5 0 0 0 2.5 2.5h13a2.5 2.5 0 0 0 2.5-2.5V8a2 2 0 0 0-2-2h-2.5L15 4.5H9Zm3 3a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Zm0 2a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5Z"/></svg>';
      }
      function mediaLinksHtml(value) {
        const links = normalizedMediaLinks(value);
        if (!links.length) return '';
        const items = links
          .map((link) => `<a class="popup-media-link" href="${escapeHtml(link.url)}" target="_blank" rel="noreferrer">${mediaIconSvg(String(link.kind || '').toLowerCase())}<span>${escapeHtml(link.label)}</span></a>`)
          .join('');
        return `<div><strong>Media</strong> <span class="popup-media-list">${items}</span></div>`;
      }
      function titleCaseWords(value) {
        return String(value || '')
          .split(/[_-]+/)
          .filter(Boolean)
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
      }
      function formatAnimalScope(scope) {
        if (scope === 'domesticated_core') return 'Domesticated-core';
        if (scope === 'comparator') return 'Comparator';
        return titleCaseWords(scope) || 'Unspecified';
      }
      function formatCoordinateConfidence(confidence) {
        if (confidence === 'exact') return 'Exact';
        if (confidence === 'approximate') return 'Approximate';
        if (confidence === 'inferred') return 'Inferred';
        return titleCaseWords(confidence) || 'Unspecified';
      }
      function formatCoordinateBasis(basis) {
        if (basis === 'named_site_geocoded') return 'Named-site geocoded';
        if (basis === 'named_site_geocoding') return 'Named-site geocoded';
        if (basis === 'direct_coordinates') return 'Direct coordinates';
        if (basis === 'supplementary_coordinates') return 'Supplementary coordinates';
        if (basis === 'archive_coordinates') return 'Archive coordinates';
        if (basis === 'region_only_refusal') return 'Region-only refusal';
        if (basis === 'unresolved_location') return 'Unresolved location';
        return titleCaseWords(basis) || 'Unspecified';
      }
      function animalFilterState(overrides = {}) {
        return {
          species: Object.prototype.hasOwnProperty.call(overrides, 'species') ? overrides.species : activeAnimalSpecies,
          scope: Object.prototype.hasOwnProperty.call(overrides, 'scope') ? overrides.scope : activeAnimalScope,
          confidence: Object.prototype.hasOwnProperty.call(overrides, 'confidence') ? overrides.confidence : activeAnimalConfidence,
          temporalWindow: Object.prototype.hasOwnProperty.call(overrides, 'temporalWindow') ? overrides.temporalWindow : activeAnimalTemporalWindow,
          nordicOnly: Object.prototype.hasOwnProperty.call(overrides, 'nordicOnly') ? overrides.nordicOnly : animalNordicOnly,
        };
      }
      function animalCandidateEntries() {
        const entries = [];
        POINT_LAYERS.forEach((layer) => {
          if (!isAnimalLayer(layer) || !activeLayerKeys.has(layer.key)) return;
          (layer.features || []).forEach((feature) => {
            if (layer.applies_country_filter && feature.country && !activeCountries.has(feature.country)) return;
            if (!pointFeatureInTimeWindow(layer, feature)) return;
            entries.push({ layer, feature });
          });
        });
        return entries;
      }
      function animalEntryMatchesFilters(entry, overrides = {}) {
        const state = animalFilterState(overrides);
        const feature = entry.feature;
        if (state.species !== 'all' && String(feature.species_latin_name || '') !== state.species) return false;
        if (state.scope !== 'all' && String(feature.animal_scope || '') !== state.scope) return false;
        if (state.confidence !== 'all' && String(feature.coordinate_confidence || '') !== state.confidence) return false;
        if (state.temporalWindow !== 'all' && String(feature.temporal_window_label || '') !== state.temporalWindow) return false;
        if (state.nordicOnly && !feature.nordic_inclusion) return false;
        return true;
      }
      function animalVisibleEntries() {
        return animalCandidateEntries().filter((entry) => animalEntryMatchesFilters(entry));
      }
      function summarizeAnimalMetrics() {
        const candidateEntries = animalCandidateEntries();
        const visibleEntries = candidateEntries.filter((entry) => animalEntryMatchesFilters(entry));
        const visibleSpecies = new Set(
          visibleEntries
            .map(({ feature }) => String(feature.species_latin_name || '').trim())
            .filter(Boolean)
        );
        const confidenceCounts = {};
        visibleEntries.forEach(({ feature }) => {
          const key = String(feature.coordinate_confidence || '').trim() || 'unspecified';
          confidenceCounts[key] = (confidenceCounts[key] || 0) + 1;
        });
        const activeFilters = [
          activeAnimalSpecies !== 'all' ? ANIMAL_SPECIES.find((species) => species.latinName === activeAnimalSpecies)?.commonName || activeAnimalSpecies : '',
          activeAnimalScope !== 'all' ? formatAnimalScope(activeAnimalScope) : '',
          activeAnimalConfidence !== 'all' ? formatCoordinateConfidence(activeAnimalConfidence) : '',
          activeAnimalTemporalWindow !== 'all' ? activeAnimalTemporalWindow : '',
          animalNordicOnly ? 'Nordic leads only' : '',
        ].filter(Boolean);
        return {
          candidateEntries,
          visibleEntries,
          visibleSpecies,
          confidenceCounts,
          activeFilters,
        };
      }
      function countryStyle(country) { return countryColors[country] || { fill: '#475569', stroke: '#1e293b' }; }
      function layerColor(layer) { return layer.style && layer.style.fill ? layer.style.fill : (layer.style && layer.style.stroke ? layer.style.stroke : '#475569'); }
      function isAnimalLayer(layer) {
        return ANIMAL_LAYER_GROUPS.has(layer.group);
      }
      function featureMatchesAnimalFilters(layer, feature) {
        if (!isAnimalLayer(layer)) return true;
        return animalEntryMatchesFilters({ layer, feature });
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
        if (activeAnimalSpecies !== 'all') params.set('animal_species', activeAnimalSpecies);
        if (activeAnimalScope !== 'all') params.set('animal_scope', activeAnimalScope);
        if (activeAnimalConfidence !== 'all') params.set('animal_confidence', activeAnimalConfidence);
        if (activeAnimalTemporalWindow !== 'all') params.set('animal_time_window', activeAnimalTemporalWindow);
        if (animalNordicOnly) params.set('animal_nordic', 'only');
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
        focusSourceLink.textContent = focusState.sourceLabel || 'Open source';
        focusSourceLink.hidden = !focusState.sourceUrl;
        focusSourceLink.href = focusState.sourceUrl || '#';
        const canStep = focusState.kind === 'point' && visiblePointEntries.length > 1;
        focusPreviousButton.disabled = !canStep;
        focusNextButton.disabled = !canStep;
      }
      function focusPointAtVisibleIndex(index) {
        const entry = visiblePointEntries[index];
        if (!entry) return;
        const mediaLinks = normalizedMediaLinks(entry.feature.media_links);
        const primaryAction = entry.feature.source_url
          ? { label: 'Open source', url: entry.feature.source_url }
          : (mediaLinks[0] ? { label: `Open ${mediaLinks[0].kind === 'video' ? 'video' : 'media'}`, url: mediaLinks[0].url } : null);
        const meta = [
          { label: 'Layer', value: entry.layer.label },
          { label: 'Country', value: entry.feature.country || 'Unassigned' },
          { label: 'Coordinates', value: `${Number(entry.feature.latitude).toFixed(4)}, ${Number(entry.feature.longitude).toFixed(4)}` },
        ];
        const timeLabel = featureTimeLabel(entry.feature);
        if (timeLabel) {
          meta.splice(2, 0, { label: 'Date', value: timeLabel });
        }
        setFocusState({
          kind: 'point',
          layerKey: entry.layer.key,
          visiblePointIndex: index,
          title: entry.feature.title || entry.layer.label,
          subtitle: entry.feature.subtitle || 'Point record',
          meta,
          sourceUrl: primaryAction ? primaryAction.url : '',
          sourceLabel: primaryAction ? primaryAction.label : 'Open source',
          latitude: Number(entry.feature.latitude),
          longitude: Number(entry.feature.longitude),
        });
      }
      function countActiveOverrides() {
        let count = 0;
        if (activeCountries.size !== COUNTRIES.length) count += 1;
        if (activeLayerKeys.size !== DEFAULT_LAYER_KEYS.length || DEFAULT_LAYER_KEYS.some((key) => !activeLayerKeys.has(key))) count += 1;
        if (activeAnimalSpecies !== 'all') count += 1;
        if (activeAnimalScope !== 'all') count += 1;
        if (activeAnimalConfidence !== 'all') count += 1;
        if (activeAnimalTemporalWindow !== 'all') count += 1;
        if (animalNordicOnly) count += 1;
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
        layerFilters.innerHTML = LAYER_GROUP_DEFINITIONS
          .map((group) => {
            const layers = ALL_LAYERS.filter((layer) => layer.group === group.key);
            if (!layers.length) return '';
            const cards = layers.map((layer) => {
              const checked = activeLayerKeys.has(layer.key) ? 'checked' : '';
              const swatchColor = layerColor(layer);
              const swatchBorder = layer.style && layer.style.stroke ? layer.style.stroke : swatchColor;
              return `<label class="dock-layer-chip"><input class="layer-checkbox" type="checkbox" value="${escapeHtml(layer.key)}" ${checked} aria-label="Toggle ${escapeHtml(layer.label)}"><span class="chip-swatch" style="background:${escapeHtml(swatchColor)};border-color:${escapeHtml(swatchBorder)};"></span><span>${escapeHtml(layer.label)}</span></label>`;
            }).join('');
            return `<div class="legend-group"><div class="legend-group-label">${escapeHtml(group.label)}</div><div class="dock-layer-grid">${cards}</div></div>`;
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
      function renderAnimalEvidencePanel(metrics) {
        if (!animalEvidenceMetrics || !animalEvidenceConfidence || !animalEvidenceState) return;
        const confidenceEntries = Object.entries(metrics.confidenceCounts).sort((left, right) => right[1] - left[1]);
        animalEvidenceMetrics.innerHTML = [
          { value: metrics.visibleEntries.length, label: 'Visible atlas points' },
          { value: metrics.visibleSpecies.size, label: 'Visible species' },
          { value: metrics.candidateEntries.length - metrics.visibleEntries.length, label: 'Filtered out by current posture' },
        ]
          .map((item) => `<div class="animal-insight-stat"><span class="animal-insight-stat-value">${escapeHtml(String(item.value))}</span><span class="animal-insight-stat-label">${escapeHtml(item.label)}</span></div>`)
          .join('');
        animalEvidenceConfidence.innerHTML = confidenceEntries.length
          ? confidenceEntries
              .map(([confidence, count]) => `<span class="animal-insight-chip"><span>${escapeHtml(formatCoordinateConfidence(confidence))}</span><strong>${escapeHtml(String(count))}</strong></span>`)
              .join('')
          : '<span class="animal-insight-copy">No animal points remain visible under the current filter state.</span>';
        animalEvidenceState.textContent = metrics.activeFilters.length
          ? metrics.activeFilters.join(' · ')
          : 'Default animal posture';
      }
      function renderAnimalControls() {
        if (!ANIMAL_SPECIES.length) {
          animalFilterSummary.textContent = 'No mapped animal evidence shipped';
          animalScopeFilters.innerHTML = '<span class="search-meta">No mapped animal layers available.</span>';
          animalSpeciesFilters.innerHTML = '';
          animalConfidenceFilters.innerHTML = '';
          animalTemporalWindowFilters.innerHTML = '';
          animalEvidenceMetrics.innerHTML = '';
          animalEvidenceConfidence.innerHTML = '<span class="animal-insight-copy">No mapped animal points are available in this bundle.</span>';
          animalEvidenceState.textContent = 'No animal evidence';
          animalNordicOnlyCheckbox.checked = false;
          animalNordicOnlyCheckbox.disabled = true;
          return;
        }
        const metrics = summarizeAnimalMetrics();
        animalNordicOnlyCheckbox.disabled = false;
        const scopeOptions = [
          { value: 'all', label: 'All animal evidence' },
          { value: 'domesticated_core', label: 'Domesticated-core only' },
          { value: 'comparator', label: 'Comparator only' },
        ];
        animalScopeFilters.innerHTML = scopeOptions
          .map((option) => {
            const count = metrics.candidateEntries.filter((entry) => animalEntryMatchesFilters(entry, { scope: option.value })).length;
            return `<button class="preset-button ${activeAnimalScope === option.value ? 'is-active' : ''}" type="button" data-animal-scope="${escapeHtml(option.value)}">${escapeHtml(option.label)} <span class="chip-count">${escapeHtml(String(count))}</span></button>`;
          })
          .join('');
        const speciesButtons = [
          `<button class="preset-button ${activeAnimalSpecies === 'all' ? 'is-active' : ''}" type="button" data-animal-species="all">All species <span class="chip-count">${escapeHtml(String(metrics.candidateEntries.filter((entry) => animalEntryMatchesFilters(entry, { species: 'all' })).length))}</span></button>`,
          ...ANIMAL_SPECIES.map((species) => {
            const count = metrics.candidateEntries.filter((entry) => animalEntryMatchesFilters(entry, { species: species.latinName })).length;
            return `<button class="preset-button ${activeAnimalSpecies === species.latinName ? 'is-active' : ''}" type="button" data-animal-species="${escapeHtml(species.latinName)}"><span class="chip-swatch" style="background:${escapeHtml(species.fill)};border-color:${escapeHtml(species.stroke)};"></span>${escapeHtml(String(species.commonName))} <span class="chip-count">${escapeHtml(String(count))}</span></button>`;
          }),
        ];
        animalSpeciesFilters.innerHTML = speciesButtons.join('');
        const confidenceButtons = [
          `<button class="preset-button ${activeAnimalConfidence === 'all' ? 'is-active' : ''}" type="button" data-animal-confidence="all">All confidence <span class="chip-count">${escapeHtml(String(metrics.candidateEntries.filter((entry) => animalEntryMatchesFilters(entry, { confidence: 'all' })).length))}</span></button>`,
          ...ANIMAL_COORDINATE_CONFIDENCES.map((confidence) => {
            const count = metrics.candidateEntries.filter((entry) => animalEntryMatchesFilters(entry, { confidence })).length;
            return `<button class="preset-button ${activeAnimalConfidence === confidence ? 'is-active' : ''}" type="button" data-animal-confidence="${escapeHtml(confidence)}">${escapeHtml(formatCoordinateConfidence(confidence))} <span class="chip-count">${escapeHtml(String(count))}</span></button>`;
          }),
        ];
        animalConfidenceFilters.innerHTML = confidenceButtons.join('');
        const temporalWindowButtons = [
          `<button class="preset-button ${activeAnimalTemporalWindow === 'all' ? 'is-active' : ''}" type="button" data-animal-temporal-window="all">All temporal windows</button>`,
          ...ANIMAL_TEMPORAL_WINDOWS.map((label) => `<button class="preset-button ${activeAnimalTemporalWindow === label ? 'is-active' : ''}" type="button" data-animal-temporal-window="${escapeHtml(label)}">${escapeHtml(label)}</button>`),
        ];
        animalTemporalWindowFilters.innerHTML = temporalWindowButtons.join('');
        animalNordicOnlyCheckbox.checked = animalNordicOnly;
        animalFilterSummary.textContent = `${metrics.visibleEntries.length} animal points · ${metrics.visibleSpecies.size} species visible`;
        renderAnimalEvidencePanel(metrics);
        document.querySelectorAll('[data-animal-scope]').forEach((button) => {
          button.addEventListener('click', () => {
            activeAnimalScope = button.dataset.animalScope;
            renderMapState();
          });
        });
        document.querySelectorAll('[data-animal-species]').forEach((button) => {
          button.addEventListener('click', () => {
            activeAnimalSpecies = button.dataset.animalSpecies;
            renderMapState();
          });
        });
        document.querySelectorAll('[data-animal-confidence]').forEach((button) => {
          button.addEventListener('click', () => {
            activeAnimalConfidence = button.dataset.animalConfidence;
            renderMapState();
          });
        });
        document.querySelectorAll('[data-animal-temporal-window]').forEach((button) => {
          button.addEventListener('click', () => {
            activeAnimalTemporalWindow = button.dataset.animalTemporalWindow;
            renderMapState();
          });
        });
      }
      function applyLayerPreset(preset) {
        if (preset === 'evidence') {
          activeLayerKeys = new Set(
            ALL_LAYERS
              .filter((layer) => ['primary-evidence', 'animal-domesticated-evidence', 'animal-comparator-evidence'].includes(layer.group))
              .map((layer) => layer.key)
          );
        }
        if (preset === 'context') {
          activeLayerKeys = new Set(
            ALL_LAYERS
              .filter((layer) => ['primary-evidence', 'animal-domesticated-evidence', 'animal-comparator-evidence', 'environmental-context', 'archaeology-context'].includes(layer.group))
              .map((layer) => layer.key)
          );
        }
        if (preset === 'orientation') {
          activeLayerKeys = new Set(
            ALL_LAYERS
              .filter((layer) => ['primary-evidence', 'animal-domesticated-evidence', 'animal-comparator-evidence', 'orientation'].includes(layer.group))
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
        const activeAnimalLayers = activeLegendLayers.filter((layer) => isAnimalLayer(layer));
        const animalMetrics = summarizeAnimalMetrics();
        const renderGroup = (label, layers) => layers.length
          ? `<div class="legend-group"><div class="legend-group-label">${escapeHtml(label)}</div><div class="legend-list">${layers.map((layer) => `<div class="legend-item"><span class="legend-swatch" style="background:${escapeHtml(layerColor(layer))};border-color:${escapeHtml(layer.style.stroke || layerColor(layer))};"></span><span>${escapeHtml(layer.label)}: ${escapeHtml(layer.description)} ${layer.coverage_label ? `(${escapeHtml(layer.coverage_label)})` : ''}</span></div>`).join('')}</div></div>`
          : '';
        const animalLegendSections = activeAnimalLayers.length
          ? [
              `<div class="legend-group"><div class="legend-group-label">Animal scope</div><div class="legend-pill-list"><span class="legend-pill"><span class="legend-swatch" style="background: rgba(176, 133, 42, 0.18); border-color: #8a5b11;"></span><span>Domesticated-core</span><span class="legend-pill-note">tracked support surface</span></span><span class="legend-pill"><span class="legend-swatch" style="background: rgba(20, 184, 166, 0.18); border-color: #0f766e;"></span><span>Comparator</span><span class="legend-pill-note">comparison only</span></span></div></div>`,
              `<div class="legend-group"><div class="legend-group-label">Coordinate trust</div><div class="legend-list">${Object.entries(animalMetrics.confidenceCounts).sort((left, right) => right[1] - left[1]).map(([confidence, count]) => `<div class="legend-item legend-item--compact"><span class="legend-swatch" style="background: rgba(20, 33, 61, 0.08); border-color: rgba(20, 33, 61, 0.22);"></span><span class="legend-item-copy"><span class="legend-item-title">${escapeHtml(formatCoordinateConfidence(confidence))}</span><span class="legend-item-meta">${escapeHtml(String(count))} visible points</span></span></div>`).join('') || '<div class="legend-item"><span>No visible animal points for the current filter state.</span></div>'}</div></div>`,
              `<div class="legend-group"><div class="legend-group-label">Tracked species</div><div class="legend-list">${activeAnimalLayers.map((layer) => `<div class="legend-item legend-item--compact"><span class="legend-swatch" style="background:${escapeHtml(layerColor(layer))};border-color:${escapeHtml(layer.style.stroke || layerColor(layer))};"></span><span class="legend-item-copy"><span class="legend-item-title">${escapeHtml(layer.species_common_name || layer.label)}</span><span class="legend-item-meta">${escapeHtml(formatAnimalScope(layer.animal_scope || ''))} · ${escapeHtml(String(layer.count || 0))} mapped point${Number(layer.count || 0) === 1 ? '' : 's'}</span></span></div>`).join('')}</div></div>`,
            ].join('')
          : '';
        legendItems.innerHTML = `${animalLegendSections}${LAYER_GROUP_DEFINITIONS
          .map((group) => renderGroup(group.label, activeLegendLayers.filter((layer) => layer.group === group.key)))
          .join('')}` || '<div class="legend-item"><span>No layers are visible. Restore defaults or enable one or more layers.</span></div>';
        densityRamp.hidden = !activeLayerKeys.has('raa-archaeology');
      }
      function popupHtml(feature) {
        const rows = Array.isArray(feature.popup_rows) ? feature.popup_rows : [];
        if (feature.species_latin_name) {
          const warningRows = rows.filter((row) => row && row.label === 'Warning' && row.value);
          const detailRows = rows.filter((row) => row && row.value && row.label !== 'Warning');
          const primaryRows = [
            { label: 'Paper', value: feature.paper_title || '' },
            { label: 'DOI', value: feature.paper_doi || '' },
            { label: 'Project accession', value: Array.isArray(feature.project_accessions) ? feature.project_accessions.join(', ') : '' },
            { label: 'Coordinate basis', value: formatCoordinateBasis(feature.coordinate_basis || '') },
            { label: 'Coordinate confidence', value: formatCoordinateConfidence(feature.coordinate_confidence || '') },
            { label: 'Source locator', value: feature.source_locator || '' },
          ].filter((row) => row.value);
          const secondaryRows = [
            { label: 'Chronology', value: feature.time_label || '' },
            { label: 'Mapped sample identifiers', value: Array.isArray(feature.sample_record_ids) ? feature.sample_record_ids.join(', ') : '' },
            { label: 'Original place text', value: feature.original_place_text || '' },
            { label: 'Resolved place text', value: feature.resolved_place_text || '' },
            { label: 'Source support', value: feature.source_support_status || '' },
            { label: 'Interpretation', value: detailRows.find((row) => row.label === 'Interpretation')?.value || '' },
            { label: 'Source evidence text', value: feature.exact_source_text || '' },
          ].filter((row) => row.value);
          const renderRows = (items) => items.map((row) => `<div class="popup-row"><span class="popup-row-label">${escapeHtml(row.label)}</span><span class="popup-row-value">${escapeHtml(row.value)}</span></div>`).join('');
          return `<div class="popup-card"><div class="popup-headline"><span class="popup-kicker">Animal atlas evidence</span><div class="popup-title">${escapeHtml(feature.title || '')}</div><div class="popup-subtitle">${escapeHtml(feature.subtitle || '')}</div></div><div class="popup-badges"><span class="popup-badge">${escapeHtml(feature.species_common_name || feature.species_latin_name || 'Animal evidence')}</span><span class="popup-badge">${escapeHtml(formatAnimalScope(feature.animal_scope || ''))}</span><span class="popup-badge">${escapeHtml(formatCoordinateConfidence(feature.coordinate_confidence || ''))}</span>${feature.nordic_inclusion ? '<span class="popup-badge">Nordic lead</span>' : '<span class="popup-badge popup-badge--warning">Non-Nordic context</span>'}</div><div class="popup-section"><span class="popup-section-title">Citation and provenance</span>${renderRows(primaryRows)}</div><div class="popup-section"><span class="popup-section-title">Sample and locality detail</span>${renderRows(secondaryRows)}<div class="popup-row"><span class="popup-row-label">Coordinates</span><span class="popup-row-value">${Number(feature.latitude).toFixed(6)}, ${Number(feature.longitude).toFixed(6)}</span></div>${mediaLinksHtml(feature.media_links)}</div>${warningRows.length ? `<div class="popup-section"><span class="popup-section-title">Warnings and caveats</span><div class="popup-warning-list">${warningRows.map((row) => `<div class="popup-warning">${escapeHtml(row.value || '')}</div>`).join('')}</div></div>` : ''}${feature.source_url ? `<div class="popup-section"><span class="popup-section-title">Source link</span><div class="popup-row"><span class="popup-row-value"><a href="${escapeHtml(feature.source_url)}" target="_blank" rel="noreferrer">Open article or source record</a></span></div></div>` : ''}</div>`;
        }
        const rowHtml = rows.filter((row) => row && row.value).map((row) => `<div><strong>${escapeHtml(row.label || '')}</strong> ${escapeHtml(row.value || '')}</div>`).join('');
        return `<div class="popup-grid"><div><strong>Name</strong> ${escapeHtml(feature.title || '')}</div><div><strong>Type</strong> ${escapeHtml(feature.subtitle || '')}</div>${rowHtml}<div><strong>Coords</strong> ${Number(feature.latitude).toFixed(6)}, ${Number(feature.longitude).toFixed(6)}</div>${mediaLinksHtml(feature.media_links)}${feature.source_url ? `<div><strong>Source</strong> <a href="${escapeHtml(feature.source_url)}" target="_blank" rel="noreferrer">Open</a></div>` : ''}</div>`;
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
      function featureTimeWindow(feature) {
        const start = Number(feature.time_start_bp);
        const end = Number(feature.time_end_bp);
        if (Number.isFinite(start) && Number.isFinite(end)) {
          return { start: Math.min(start, end), end: Math.max(start, end) };
        }
        const mean = Number(feature.time_mean_bp);
        if (Number.isFinite(mean)) {
          return { start: mean, end: mean };
        }
        const year = Number(feature.time_year_bp);
        if (Number.isFinite(year)) {
          return { start: year, end: year };
        }
        return null;
      }
      function featureInTimeWindow(layer, feature) {
        if (!layer.applies_time_filter || !TIME_HAS_DATA) return true;
        const featureWindow = featureTimeWindow(feature);
        if (!featureWindow) return true;
        const activeWindow = { start: timeStartBp, end: timeWindowEndBp() };
        return featureWindow.end >= activeWindow.start && featureWindow.start <= activeWindow.end;
      }
      function featureTimeLabel(feature) {
        if (feature.time_label) return String(feature.time_label);
        const window = featureTimeWindow(feature);
        if (!window) return '';
        return window.start === window.end ? `${window.start} BP` : `${window.start}-${window.end} BP`;
      }
      function pointFeatureInTimeWindow(layer, feature) {
        return featureInTimeWindow(layer, feature);
      }
      function pointFeatureVisible(layer, feature) {
        return (
          activeLayerKeys.has(layer.key)
          && (!layer.applies_country_filter || !feature.country || activeCountries.has(feature.country))
          && pointFeatureInTimeWindow(layer, feature)
          && featureMatchesAnimalFilters(layer, feature)
        );
      }
      function polygonFeatureVisible(layer, properties) {
        const country = properties.country || '';
        return (
          activeLayerKeys.has(layer.key)
          && (!layer.applies_country_filter || !country || activeCountries.has(country))
          && featureInTimeWindow(layer, properties)
        );
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
                    ].concat(featureTimeLabel(properties) ? [{ label: 'Date', value: featureTimeLabel(properties) }] : []),
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
        const visibleAnimalCount = visiblePointEntries.filter(({ layer }) => isAnimalLayer(layer)).length;
        const timedVisiblePoints = visiblePointEntries.filter(({ layer, feature }) => layer.applies_time_filter && featureTimeWindow(feature)).length;
        const timedVisiblePolygons = POLYGON_LAYERS.reduce((count, layer) => {
          if (!activeLayerKeys.has(layer.key) || !layer.applies_time_filter) return count;
          const features = Array.isArray(layer.geojson && layer.geojson.features) ? layer.geojson.features : [];
          return count + features.filter((feature) => {
            const properties = feature && feature.properties ? feature.properties : {};
            return featureTimeWindow(properties) && polygonFeatureVisible(layer, properties);
          }).length;
        }, 0);
        const timedVisibleCount = timedVisiblePoints + timedVisiblePolygons;
        timeRecordCount.textContent = TIME_HAS_DATA
          ? `${timedVisibleCount} time-aware records are visible in the active BP window.`
          : 'No time-aware records are available for BP filtering.';
        const visiblePolygonLayers = renderedPolygonLayers.length;
        selectionReadout.textContent = `${visiblePointEntries.length} points · ${visibleAnimalCount} animal · ${visiblePolygonLayers} overlays`;
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
        const matches = visiblePointEntries.filter(({ layer, feature }) => `${feature.title || ''} ${feature.subtitle || ''} ${feature.country || ''} ${layer.label || ''} ${featureTimeLabel(feature)}`.toLowerCase().includes(query)).slice(0, 12);
        searchCount.textContent = `${matches.length} matches · ${visiblePointEntries.length} visible`;
        searchResults.hidden = false;
        searchResults.innerHTML = matches.map(({ layer, feature }, index) => `<button class="search-result" type="button" data-search-index="${index}"><strong>${escapeHtml(feature.title || '')}</strong><span>${escapeHtml(feature.subtitle || 'Unspecified type')}</span><div class="search-result-meta"><span class="search-badge">${escapeHtml(layer.label)}</span><span class="search-badge">${escapeHtml(feature.country || 'Unassigned')}</span>${featureTimeLabel(feature) ? `<span class="search-badge">${escapeHtml(featureTimeLabel(feature))}</span>` : ''}</div></button>`).join('') || '<div class="summary-item"><span>No visible records match the current query.</span></div>';
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
        renderAnimalControls();
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
      document.querySelectorAll('.basemap-button').forEach((button) => button.classList.toggle('is-active', button.dataset.basemap === currentBasemap));
      function fitToActive() {
        const bounds = activeBounds();
        if (bounds && bounds.isValid()) map.fitBounds(bounds, { padding: [36, 36] });
      }
      function resetView() { map.fitBounds(INITIAL_BOUNDS, { padding: [36, 36] }); }
      function restoreDefaults() {
        activeCountries = new Set(DEFAULT_COUNTRIES);
        activeLayerKeys = new Set(DEFAULT_LAYER_KEYS);
        activeAnimalSpecies = 'all';
        activeAnimalScope = 'all';
        activeAnimalConfidence = 'all';
        activeAnimalTemporalWindow = 'all';
        animalNordicOnly = false;
        animalNordicOnlyCheckbox.checked = false;
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
      animalNordicOnlyCheckbox.addEventListener('change', () => {
        animalNordicOnly = animalNordicOnlyCheckbox.checked;
        renderMapState();
      });
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

__all__ = ["MAP_DOCUMENT_TEMPLATE"]
