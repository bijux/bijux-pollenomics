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
  return Object.freeze({ observe, canPublish, publish });
}
