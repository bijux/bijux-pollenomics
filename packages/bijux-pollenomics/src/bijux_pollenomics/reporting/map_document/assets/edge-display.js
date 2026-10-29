// Limit Leaflet primitives without changing scientific selection or exports.
function atlasEdgeIntersectsViewport(map, coordinates) {
  const [first, second] = coordinates.map((point) => map.latLngToContainerPoint(point));
  const size = map.getSize();
  if (![first.x, first.y, second.x, second.y, size.x, size.y].every(Number.isFinite) || size.x < 0 || size.y < 0) {
    throw new Error('Atlas edge rendering requires finite viewport coordinates.');
  }
  // Clip the displayed projected segment, including crossings with both ends outside.
  // Projection (including any world offset) belongs to the same map as L.polyline.
  let start = 0, end = 1;
  for (const [origin, delta, maximum] of [
    [first.x, second.x - first.x, size.x],
    [first.y, second.y - first.y, size.y],
  ]) {
    if (delta === 0) {
      if (origin < 0 || origin > maximum) return false;
    } else {
      const a = -origin / delta, b = (maximum - origin) / delta;
      start = Math.max(start, Math.min(a, b));
      end = Math.min(end, Math.max(a, b));
      if (start > end) return false;
    }
  }
  return true;
}
function atlasEdgeRenderSelection(edges, entriesByRecordId, zoom, coordinatePair, intersectsViewport) {
  if (!Number.isFinite(zoom)) throw new Error('Atlas edge rendering requires a finite zoom.');
  const limit = zoom < 5 ? 128 : zoom < 8 ? 256 : 512;
  const eligible = edges.flatMap((edge) => {
    const source = entriesByRecordId.get(String(edge.source_record_id));
    const target = entriesByRecordId.get(String(edge.target_record_id));
    if (!source || !target) return [];
    const a = coordinatePair(source.feature), b = coordinatePair(target.feature);
    if (!a || !b) return [];
    const coordinates = [a, b].map((point) => [point.latitude, point.longitude]);
    if (intersectsViewport && !intersectsViewport(coordinates)) return [];
    return [{ edge, source, target }];
  });
  // Uncapped order is retained; capped membership uses literal scientific IDs,
  // independent of publication order, locale, or analytical rank.
  const ordered = eligible.length <= limit ? eligible : [...eligible].sort((left, right) => {
    const a = String(left.edge.edge_id), b = String(right.edge.edge_id);
    return a < b ? -1 : a > b ? 1 : 0;
  });
  return { rows: ordered.slice(0, limit), viewport_count: eligible.length, limit };
}
