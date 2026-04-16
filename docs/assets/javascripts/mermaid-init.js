function isDarkScheme() {
  return document.body.getAttribute("data-md-color-scheme") === "slate";
}

function getMermaidThemeVariables() {
  if (isDarkScheme()) {
    return {
      darkMode: true,
      primaryColor: "#112838",
      primaryTextColor: "#eaf2fa",
      primaryBorderColor: "#6fc7c2",
      lineColor: "#a9c8d4",
      secondaryColor: "#0f2332",
      tertiaryColor: "#132c3d",
      background: "#0b1120",
      mainBkg: "#122b3c",
      secondBkg: "#0f2434",
      tertiaryBkg: "#0d2030",
      textColor: "#eaf2fa",
      labelTextColor: "#eaf2fa",
      edgeLabelBackground: "#102334",
      nodeBorder: "#6fc7c2",
      clusterBkg: "#0f2536",
      clusterBorder: "#4ba8a2",
      titleColor: "#f4f8ff",
      actorTextColor: "#eaf2fa",
      actorLineColor: "#a9c8d4",
      signalColor: "#a9c8d4",
      signalTextColor: "#eaf2fa",
      noteTextColor: "#eaf2fa",
      noteBkgColor: "#132b3c",
      noteBorderColor: "#6fc7c2",
      activationBorderColor: "#6fc7c2",
      sequenceNumberColor: "#eaf2fa",
    };
  }

  return {
    primaryColor: "#d9f2ef",
    primaryTextColor: "#142033",
    primaryBorderColor: "#0f766e",
    lineColor: "#356275",
    secondaryColor: "#ebf7f6",
    tertiaryColor: "#f3fbfb",
    background: "#ffffff",
    mainBkg: "#e7f5f2",
    secondBkg: "#eef8f7",
    tertiaryBkg: "#f5fbfa",
    textColor: "#142033",
    labelTextColor: "#142033",
    edgeLabelBackground: "#eef8f7",
    nodeBorder: "#0f766e",
    clusterBkg: "#f3fbfa",
    clusterBorder: "#5b9ba8",
    titleColor: "#10213b",
    actorTextColor: "#142033",
    actorLineColor: "#356275",
    signalColor: "#356275",
    signalTextColor: "#142033",
    noteTextColor: "#142033",
    noteBkgColor: "#eef8f7",
    noteBorderColor: "#5b9ba8",
    activationBorderColor: "#0f766e",
    sequenceNumberColor: "#142033",
  };
}

function buildMermaidConfig() {
  const darkThemeCss = `
    .label, .label text, .nodeLabel, .edgeLabel, .edgeLabel p,
    span.nodeLabel, .cluster-label text {
      fill: #eaf2fa !important;
      color: #eaf2fa !important;
    }
    foreignObject div, foreignObject span, .labelBkg {
      color: #eaf2fa !important;
      fill: #eaf2fa !important;
      background: transparent !important;
    }
    .edgeLabel rect {
      fill: #102334 !important;
      opacity: 1 !important;
    }
    .cluster rect {
      fill: #0f2536 !important;
      stroke: #4ba8a2 !important;
    }
    .node rect, .node circle, .node ellipse, .node polygon, .node path,
    .classBox, .stateGroup rect, .stateGroup path,
    rect.basic, rect.label-container {
      fill: #122b3c !important;
      stroke: #6fc7c2 !important;
    }
    .flowchart-link, .marker, .marker path, .path, .edgePath .path {
      stroke: #a9c8d4 !important;
    }
    .relationshipLabelBox {
      fill: #102334 !important;
      opacity: 1 !important;
    }
    .legend text, .classTitle, .state-title {
      fill: #eaf2fa !important;
    }
  `;

  return {
    startOnLoad: false,
    securityLevel: "loose",
    theme: "base",
    themeVariables: getMermaidThemeVariables(),
    themeCSS: isDarkScheme() ? darkThemeCss : "",
  };
}

function parseColor(value) {
  if (!value) {
    return null;
  }

  const color = value.trim().toLowerCase();

  if (color === "none" || color === "transparent") {
    return null;
  }

  const hex = color.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
  if (hex) {
    let raw = hex[1];
    if (raw.length === 3) {
      raw = raw
        .split("")
        .map((ch) => ch + ch)
        .join("");
    }
    return {
      r: parseInt(raw.slice(0, 2), 16),
      g: parseInt(raw.slice(2, 4), 16),
      b: parseInt(raw.slice(4, 6), 16),
    };
  }

  const rgb = color.match(
    /^rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)(?:\s*,\s*[0-9.]+\s*)?\)$/,
  );
  if (rgb) {
    return {
      r: Number(rgb[1]),
      g: Number(rgb[2]),
      b: Number(rgb[3]),
    };
  }

  return null;
}

function relativeLuminance(rgb) {
  if (!rgb) {
    return 0;
  }

  const channels = [rgb.r, rgb.g, rgb.b].map((v) => {
    const c = Math.max(0, Math.min(255, v)) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });

  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function firstColorValue(element, cssName) {
  const inlineStyle = element.style && element.style[cssName];
  if (inlineStyle) {
    return inlineStyle;
  }

  const attr = element.getAttribute(cssName);
  if (attr) {
    return attr;
  }

  const computed = window.getComputedStyle(element)[cssName];
  if (computed) {
    return computed;
  }

  return "";
}

function applyContrastNormalization(root) {
  const dark = isDarkScheme();
  const palettes = dark
    ? {
        nodeFill: "#122b3c",
        nodeStroke: "#5dbbb5",
        clusterFill: "#0f2536",
        clusterStroke: "#4a9f9a",
        lineStroke: "#9ab9c6",
        edgeLabelBg: "#0f2334",
        text: "#e6eef7",
      }
    : {
        nodeFill: "#dceef3",
        nodeStroke: "#4a8a99",
        clusterFill: "#ebf5f8",
        clusterStroke: "#6ea4b0",
        lineStroke: "#5c7f8f",
        edgeLabelBg: "#edf5f8",
        text: "#1c3443",
      };

  for (const svg of root.querySelectorAll(".mermaid svg")) {
    const shapes = svg.querySelectorAll("rect, circle, ellipse, polygon, path, line, polyline");
    for (const el of shapes) {
      const className = (el.getAttribute("class") || "").toLowerCase();
      const fill = firstColorValue(el, "fill");
      const stroke = firstColorValue(el, "stroke");
      const fillLum = relativeLuminance(parseColor(fill));
      const hasFill = !!fill && fill !== "none" && fill !== "transparent";
      const hasStroke = !!stroke && stroke !== "none" && stroke !== "transparent";

      const inEdgeLabel =
        !!el.closest(".edgeLabel") ||
        className.includes("edgelabel") ||
        className.includes("labelbkg") ||
        className.includes("relationshiplabelbox");
      const inCluster = !!el.closest(".cluster") || className.includes("cluster");
      const inNode =
        !!el.closest(".node, .classGroup, .stateGroup") ||
        className.includes("node") ||
        className.includes("classbox") ||
        className.includes("label-container") ||
        className.includes("basic");

      if (inEdgeLabel) {
        el.style.fill = palettes.edgeLabelBg;
        el.style.opacity = "1";
      } else if (inCluster) {
        el.style.fill = palettes.clusterFill;
      } else if (inNode) {
        el.style.fill = palettes.nodeFill;
      } else if (hasFill && ((dark && fillLum > 0.24) || (!dark && fillLum < 0.55))) {
        // Generic fallback for unknown Mermaid shape classes with poor mode contrast.
        el.style.fill = palettes.nodeFill;
      }

      if (inCluster) {
        el.style.stroke = palettes.clusterStroke;
      } else if (inNode) {
        el.style.stroke = palettes.nodeStroke;
      } else if (hasStroke || !hasFill) {
        el.style.stroke = palettes.lineStroke;
      }
    }

    const labels = svg.querySelectorAll(
      "text, tspan, .label, .label text, .nodeLabel, span.nodeLabel, " +
        ".edgeLabel, .edgeLabel p, .cluster-label text, .classTitle, .state-title, " +
        "foreignObject div, foreignObject span",
    );
    for (const el of labels) {
      el.style.color = palettes.text;
      el.style.fill = palettes.text;
    }
  }
}

function normalizeMermaidBlocks(root) {
  const blocks = root.querySelectorAll("pre.mermaid");

  for (const block of blocks) {
    const source = block.querySelector("code");
    const diagram = document.createElement("div");

    diagram.className = "mermaid";
    diagram.textContent = (source || block).textContent || "";

    block.replaceWith(diagram);
  }
}

document$.subscribe(() => {
  if (typeof mermaid === "undefined") {
    return;
  }

  window.mermaidConfig = buildMermaidConfig();
  mermaid.initialize(window.mermaidConfig);
  normalizeMermaidBlocks(document);

  const nodes = Array.from(document.querySelectorAll("div.mermaid")).filter(
    (node) => node.getAttribute("data-processed") !== "true",
  );
  if (!nodes.length) {
    return;
  }

  mermaid.run({
    nodes,
  });
  const applyNormalization = () => {
    applyContrastNormalization(document);
    requestAnimationFrame(() => applyContrastNormalization(document));
    setTimeout(() => applyContrastNormalization(document), 120);
  };

  applyNormalization();
});

window.addEventListener("bijux:theme-change", () => {
  setTimeout(() => applyContrastNormalization(document), 0);
  setTimeout(() => applyContrastNormalization(document), 120);
});
