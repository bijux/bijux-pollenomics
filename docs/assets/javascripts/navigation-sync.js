function bijuxNormalizePath(target) {
  const url = new URL(target, window.location.href);
  const path = url.pathname.replace(/\/+$/, "");
  return path || "/";
}

function bijuxBestSitePath() {
  const currentPath = bijuxNormalizePath(window.location.pathname);
  const siteLinks = document.querySelectorAll(
    ".bijux-site-tabs [data-bijux-site-path]"
  );
  let bestMatch = null;

  for (const link of siteLinks) {
    const linkPath = bijuxNormalizePath(
      link.getAttribute("data-bijux-site-path") || "/"
    );
    if (
      currentPath === linkPath ||
      (linkPath !== "/" && currentPath.startsWith(`${linkPath}/`))
    ) {
      if (!bestMatch || linkPath.length > bestMatch.length) {
        bestMatch = linkPath;
      }
    }
  }

  return bestMatch;
}

function bijuxSyncSiteTabActiveState() {
  const activeSitePath = bijuxBestSitePath();

  for (const item of document.querySelectorAll(".bijux-site-tabs .bijux-tabs__item")) {
    item.classList.remove("md-tabs__item--active", "bijux-tabs__item--active");
  }
  for (const link of document.querySelectorAll(
    ".bijux-site-tabs [data-bijux-site-path]"
  )) {
    link.removeAttribute("aria-current");
  }

  if (!activeSitePath) {
    return null;
  }

  for (const link of document.querySelectorAll(
    ".bijux-site-tabs [data-bijux-site-path]"
  )) {
    const linkPath = bijuxNormalizePath(
      link.getAttribute("data-bijux-site-path") || "/"
    );
    if (linkPath === activeSitePath) {
      link.closest(".bijux-tabs__item")?.classList.add(
        "md-tabs__item--active",
        "bijux-tabs__item--active"
      );
      link.setAttribute("aria-current", "page");
    }
  }

  return activeSitePath;
}

function bijuxSyncDetailStripVisibility() {
  const activeSitePath = bijuxSyncSiteTabActiveState();
  const strips = document.querySelectorAll("[data-bijux-detail-strip]");

  for (const strip of strips) {
    const rootPath = bijuxNormalizePath(
      strip.getAttribute("data-bijux-detail-root-path") || "/"
    );
    strip.hidden = rootPath !== activeSitePath;
  }
}

function bijuxSyncDetailStripActiveState() {
  const activeStrip = document.querySelector("[data-bijux-detail-strip]:not([hidden])");
  const currentPath = bijuxNormalizePath(window.location.pathname);

  for (const item of document.querySelectorAll(
    "[data-bijux-detail-strip] .bijux-tabs__item"
  )) {
    item.classList.remove("bijux-tabs__item--active");
  }
  for (const link of document.querySelectorAll(
    "[data-bijux-detail-strip] [data-bijux-detail-path]"
  )) {
    link.removeAttribute("aria-current");
  }

  if (!activeStrip) {
    return;
  }

  let activeLink = null;

  for (const link of activeStrip.querySelectorAll("[data-bijux-detail-path]")) {
    const linkPath = bijuxNormalizePath(
      link.getAttribute("data-bijux-detail-path") || "/"
    );
    const isMatch =
      currentPath === linkPath ||
      (linkPath !== "/" && currentPath.startsWith(`${linkPath}/`));

    if (isMatch && (!activeLink || linkPath.length > activeLink.path.length)) {
      activeLink = { path: linkPath, node: link };
    }
  }

  if (activeLink) {
    activeLink.node.closest(".bijux-tabs__item")?.classList.add(
      "bijux-tabs__item--active"
    );
    activeLink.node.setAttribute("aria-current", "page");
  }
}

function bijuxRevealActiveNavigationTarget() {
  const activeSiteLink = document.querySelector(
    ".bijux-site-tabs .bijux-tabs__item--active a"
  );
  const activeDetailLink = document.querySelector(
    "[data-bijux-detail-strip]:not([hidden]) .bijux-tabs__item--active a"
  );
  const activeSidebarLink = document.querySelector(
    ".md-sidebar--primary .md-nav__link--active"
  );

  activeSiteLink?.scrollIntoView({
    block: "nearest",
    inline: "center",
  });
  activeDetailLink?.scrollIntoView({
    block: "nearest",
    inline: "center",
  });
  activeSidebarLink?.scrollIntoView({
    block: "nearest",
    inline: "nearest",
  });
}

document$.subscribe(() => {
  bijuxSyncDetailStripVisibility();
  bijuxSyncDetailStripActiveState();
  bijuxRevealActiveNavigationTarget();
});
