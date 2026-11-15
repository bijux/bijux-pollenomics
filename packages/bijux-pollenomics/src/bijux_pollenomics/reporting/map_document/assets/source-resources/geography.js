// Metadata geometry is a separate, opt-in layer; extents never become site points.
function createSourceResourceGeography({browser,map,leaflet,countries,onSelect,status,current = () => true}) {
  const group=leaflet.layerGroup(), renderer=leaflet.svg(), codes={Denmark:'DK',Finland:'FI',Norway:'NO',Sweden:'SE'};
  let generation=0, zoomGeneration=0;
  const position=value=>Array.isArray(value)&&value.length===2&&value.every(Number.isFinite)
    &&Math.abs(value[0])<=180&&Math.abs(value[1])<=90;
  function qualifiedExtent(value) {
    if(!value || !['Polygon','MultiPolygon'].includes(value.type))return false;
    const polygons=value.type==='Polygon'?[value.coordinates]:value.coordinates;
    if(!Array.isArray(polygons)||!polygons.length||polygons.length>20000)return false;
    let count=0;
    return polygons.every(polygon=>Array.isArray(polygon)&&polygon.length&&polygon.length<=20000
      &&polygon.every(ring=>Array.isArray(ring)&&ring.length>=4&&ring.length<=20000
        &&(count+=ring.length)<=20000&&ring.every(position)&&JSON.stringify(ring[0])===JSON.stringify(ring.at(-1))));
  }
  function point(row) {
    const value=row.marker_geometry;
    return row.geometry_status==='native_point_consensus'&&value?.type==='Point'&&position(value.coordinates)?value:null;
  }
  async function geometries(row) {
    const result=[],p=point(row);
    if(p)result.push({geometry:p,kind:'point'});
    const ids=row.native_extent_variant_ids ?? [];
    if(!Array.isArray(ids)||ids.length>128)throw Error('Metadata extent membership exceeds its bound.');
    if(ids.length) {
      const site=await browser.site(row.record_id);
      if(!site||site.site_id!==row.record_id||!Array.isArray(site.native_site_variants)||site.native_site_variants.length>128)throw Error('Metadata extent site identity differs.');
      const seen=new Set();let total=0;
      for(const identity of ids) {
        if(typeof identity!=='string'||seen.has(identity))throw Error('Metadata extent variant identity repeats.');seen.add(identity);
        const matched=site.native_site_variants.filter(variant=>variant.variant_id===identity);
        if(matched.length!==1||matched[0].extent_status!=='explicit_native_extent'||!qualifiedExtent(matched[0].extent_geometry))throw Error('Metadata extent is unavailable or not qualified.');
        const geometry=matched[0].extent_geometry;
        const polygons=geometry.type==='Polygon'?[geometry.coordinates]:geometry.coordinates;
        total+=polygons.reduce((sum,polygon)=>sum+polygon.reduce((n,ring)=>n+ring.length,0),0);
        if(total>20000)throw Error('Metadata site coordinate population exceeds its bound.');
        result.push({geometry,kind:'extent'});
      }
    }
    return result;
  }
  function layer(value,identity) {
    const result=leaflet.geoJSON(value.geometry,{bubblingMouseEvents:false,renderer,
      pointToLayer:(_feature,latlng)=>leaflet.circleMarker(latlng,{renderer,radius:7,color:'#74508b',weight:2,fillOpacity:0.12,bubblingMouseEvents:false,className:'neotoma-metadata-geometry'}),
      style:()=>({color:'#74508b',weight:2,fillOpacity:0.08,dashArray:'5 4',className:'neotoma-metadata-geometry'})});
    result.bindTooltip(`Neotoma metadata ${value.kind}; native site ${identity}. No scientific admission.`);
    result.on('click',event=>{leaflet.DomEvent.stopPropagation(event);onSelect(identity);});return result;
  }
  // Superseded requests may settle, but cannot draw or describe a newer selection.
  async function update({enabled,includeUnassigned,rows,sites}) {
    const token=++generation;zoomGeneration++;group.clearLayers();if(map.hasLayer(group))map.removeLayer(group);
    if(!enabled){status.textContent='Metadata geometry is off. Unlocated resources remain searchable.';return;}
    const selected=new Set(rows.map(row=>row.site_id)),active=new Set(countries().map(country=>codes[country]||country));
    const matches=sites.filter(row=>selected.has(row.record_id)
      &&(row.country_code===null||row.country_code==='UNASSIGNED'?includeUnassigned:active.has(row.country_code)));
    let results;
    try {results=await Promise.all(matches.map(async row=>({row,values:await geometries(row)})));}
    catch(error){if(token===generation && current())status.textContent=`Metadata geometry unavailable: ${error.message}. Searchable metadata and scientific layers remain available.`;return;}
    if(token!==generation || !current())return;
    let points=0,extents=0,unlocated=0;
    for(const {row,values} of results){if(!values.length)unlocated++;for(const value of values){group.addLayer(layer(value,row.record_id));value.kind==='point'?points++:extents++;}}
    group.addTo(map);
    status.textContent=`Metadata geometry: ${points} consensus points; ${extents} native extent variants; ${unlocated} matching sites without drawable geometry. Separate metadata layer; scientific counts, fit and time filters are unchanged.`;
  }
  async function zoom(identity) {
    const token=++zoomGeneration;
    try {
    const row=await browser.site(identity);
    if(token!==zoomGeneration || !current())return;
    if(!row)throw Error('The native metadata site is unavailable.');
    const values=await geometries({...row,record_id:row.site_id});
    if(token!==zoomGeneration || !current())return;
    if(!values.length)throw Error('This metadata site has no qualified geometry; no location is invented.');
    const bounds=leaflet.featureGroup(values.map(value=>layer(value,identity))).getBounds();
    if(bounds.isValid())map.fitBounds(bounds,{padding:[30,30],maxZoom:11});
    } catch(error) {if(token===zoomGeneration && current())status.textContent=`Metadata zoom unavailable: ${error.message}. No location is invented.`;}
  }
  return Object.freeze({update,zoom,cancel:()=>{generation++;zoomGeneration++;},cancelZoom:()=>{zoomGeneration++;}});
}
