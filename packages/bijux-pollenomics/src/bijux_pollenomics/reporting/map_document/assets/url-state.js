// External URL navigation reuses the complete atlas initialization boundary.
function createAtlasURLStateController({ readURL, publishURL, replayURL }) {
  let appliedURL = readURL();
  let replayPending = false;
  function observe() {
    if (replayPending || readURL() === appliedURL) return false;
    replayPending = true;
    replayURL();
    return true;
  }
  function canPublish() {
    if (replayPending) return false;
    return !observe();
  }
  function publish(hash) {
    if (!canPublish()) return false;
    const next = new URL(appliedURL);
    next.hash = hash;
    if (next.href !== appliedURL) {
      publishURL(next.href);
      appliedURL = readURL();
    }
    return true;
  }
  function publishResources(values) {
    if (!canPublish()) return false;
    const keys = new Set(['neotoma_catalogue', 'neotoma_site', 'neotoma_dataset', 'neotoma_version']);
    if (!values || typeof values !== 'object' || Array.isArray(values)
      || Object.entries(values).some(([key, value]) => !keys.has(key)
        || value !== null && (typeof value !== 'string' || value.length > 4096))) {
      throw Error('Source resource URL values must use bounded namespaced strings or null.');
    }
    const next = new URL(appliedURL);
    Object.entries(values).forEach(([key, value]) => {
      if (value === null) next.searchParams.delete(key);
      else next.searchParams.set(key, value);
    });
    if (next.href !== appliedURL) {
      publishURL(next.href);
      appliedURL = readURL();
    }
    return true;
  }
  return Object.freeze({ observe, canPublish, publish, publishResources });
}
