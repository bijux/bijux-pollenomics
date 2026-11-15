// Listing posture summarizes source qualification, never HTTP availability or admission.
function sourceResourceQualification(row, version) {
  if (!['development_resource_discovery','exposed_development'].includes(row.exposure_role)) return {metadataOnly:true};
  const statuses=row.version_statuses?.[version] || {};
  let field='qualification_status';
  if (version==='doi_frozen') {
    if (Object.hasOwn(statuses,'strict_current_binding_status') && statuses.strict_current_binding_status!=='matches_current_metadata') {
      field='strict_current_binding_status';
    } else if ((!Object.hasOwn(statuses,'qualification_status') || statuses.qualification_status==='parsed_frozen_native')
      && Object.hasOwn(statuses,'snapshot_qualification_status')) field='snapshot_qualification_status';
  } else {
    const identityRefusal=['qualification_status','source_terminal_status','acquisition_status']
      .find(name=>statuses[name]==='refused_native_protocol');
    if (identityRefusal) field=identityRefusal;
    else if (statuses.qualification_status==='not_qualified' && statuses.acquisition_status==='unsupported_dataset_type'
      && statuses.source_terminal_status==='unsupported_dataset_type' && Object.hasOwn(statuses,'current_source_qualification_status')) {
      field='current_source_qualification_status';
    }
  }
  return {field,value:statuses[field],metadataOnly:false};
}
// A shared metadata reader owns its DOM; scientific selections remain independent.
function createSourceResourceReader({browser, domain, map, leaflet, publishQuery, canPublish,
  countries = () => [], location = globalThis.location}) {
  const element = (tag, text, attributes = {}) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    Object.entries(attributes).forEach(([key,value]) => node.setAttribute(key,String(value)));
    return node;
  };
  const ownedLabel = value => typeof value === 'string' ? value.replaceAll('_',' ') : text(value);
  const text = value => value === undefined ? 'not supplied' : value === null ? 'explicit null' : typeof value === 'string' ? value : JSON.stringify(value);
  const dialog = element('dialog', undefined, {id:'source-resources-dialog',class:'help-dialog-card','aria-label':'Neotoma source resource metadata'});
  dialog.hidden = true;
  const card = element('div',undefined,{class:'focus-detail'});
  const heading = element('div', undefined, {class:'help-dialog-head'});
  const title = element('h2','Neotoma source resources');
  const close = element('button','Close metadata',{type:'button',class:'toolbar-button'});
  heading.append(title,close);
  const status = element('p','Loading source metadata…',{role:'status','aria-live':'polite','data-resource-status':''});
  const qualification = element('p','Metadata only. Current and DOI-frozen versions keep their own epochs, rights and qualification. A frozen version does not establish original-paper identity. These resources do not expand the published scientific population or establish independent evidence.');
  const controls = element('div',undefined,{class:'focus-detail'}), list = element('div',undefined,{'data-resource-list':''});
  const detail = element('section',undefined,{'aria-label':'Selected source resource','data-resource-detail':''});
  const navigation = element('div',undefined,{class:'map-actions'});
  const previous = element('button','Previous metadata page',{type:'button',class:'toolbar-button'});
  const next = element('button','Next metadata page',{type:'button',class:'toolbar-button'});
  const pageLabel = element('span');
  navigation.append(previous,pageLabel,next);
  card.append(heading,qualification,status,controls,list,navigation,detail);dialog.append(card);document.body.append(dialog);
  let initializing = false;
  let generation = 0, detailGeneration = 0, page = 0, selectedSite = null, returnFocus = null;
  let downloadIntent = null, inventory = null, context = null, rows = [], overlay = null;
  const filters = {};
  function input(label, kind, values = []) {
    const wrapper = element('label',label+' '), node = element(kind === 'search' ? 'input' : 'select');
    node.setAttribute('aria-label',label);node.className='search-input';
    if (kind === 'search') { node.type='search'; node.maxLength=4096; }
    else for (const [value,name] of values) node.append(element('option',name,{value}));
    wrapper.append(node);controls.append(wrapper);return node;
  }
  const search = input('Search source metadata','search');
  const country = input('Metadata country','select',[['','All countries'],['DK','Denmark'],['FI','Finland'],['NO','Norway'],['SE','Sweden'],['UNASSIGNED','Unassigned / review']]);
  const type = input('Native dataset type','select',[['','All native types']]);
  const role = input('Exposure role','select',[['','All exposure roles']]);
  const version = input('Source version','select',[['current','Current'],['doi_frozen','DOI-frozen']]);
  const statusFilter = input('Version status','select',[['','All version statuses']]);
  const showMetadata = element('input',undefined,{type:'checkbox','aria-label':'Show metadata geometry'});
  const showUnassigned = element('input',undefined,{type:'checkbox','aria-label':'Include unassigned metadata geometry'});
  for (const [node,label] of [[showMetadata,'Show separate metadata geometry (off by default)'],[showUnassigned,'Include unassigned / review metadata geometry']]) {
    const wrapper=element('label');wrapper.append(node,document.createTextNode(label));controls.append(wrapper);
  }
  controls.append(element('p','Geometry follows the Atlas country switches. Unassigned geometry uses its separate switch; metadata searches include unlocated and country-review sites.'));
  const geometryStatus = element('p','Metadata geometry is off. Unlocated resources remain searchable.',{'data-resource-geometry-status':''});controls.append(geometryStatus);
  function authority() { return typeof canPublish !== 'function' || canPublish(); }
  function publish(site = selectedSite, dataset = null) {
    if (!authority()) return false;
    return typeof publishQuery !== 'function' || publishQuery({neotoma_catalogue:domain.catalogue_manifest_sha256,
      neotoma_site:site,neotoma_dataset:dataset,neotoma_version:dataset ? version.value : null});
  }
  function message(error) {
    status.textContent = `Source metadata unavailable: ${error.message || error}. Retry by reopening the source resources reader.`;
    status.dataset.state='unavailable';
  }
  function rawSection(parent,label,value) {
    const section=element('details'),summary=element('summary',label),pre=element('pre',JSON.stringify(value,null,2));
    pre.className='source-diagram-plot';section.append(summary,pre);parent.append(section);
  }
  function displayFields(parent, values) {
    const table=element('dl');
    for(const [key,value] of Object.entries(values || {}))table.append(element('dt',key),element('dd',text(value)));
    parent.append(table);
  }
  function versionAndRights(record) {
    const versions=element('section',undefined,{'data-source-versions':''});versions.append(element('h4','Version-specific source posture'));
    for(const [name,fields] of Object.entries(record.versions || {})) {
      versions.append(element('h5',name));
      displayFields(versions,Object.fromEntries(Object.entries(fields).filter(([key])=>key.endsWith('_status')||key.includes('profile')||key==='epoch_kind')));
    }
    detail.append(versions);
    const rights=element('section',undefined,{'data-source-rights':''});rights.append(element('h4','Source rights and attribution'));
    displayFields(rights,record.rights);
    for(const [label,values] of [['Data-use policy',record.rights?.policy_sources],['Native dataset DOI',record.rights?.dataset_doi_values]]) {
      if(!Array.isArray(values))continue;
      for(const value of values) {
        if(typeof value!=='string')continue;
        let url;try{url=new URL(/^10\.[0-9]{4,9}\/\S+$/.test(value)?`https://doi.org/${value}`:value);}catch{continue;}
        if(!['https:','http:'].includes(url.protocol)||url.username||url.password)continue;
        const row=element('p');row.append(element('a',`${label}: ${value}`,{href:url.href,target:'_blank',rel:'noopener noreferrer'}));rights.append(row);
      }
    }
    detail.append(rights);
  }
  function addAction(parent,label,handler,attributes={}) {
    const button=element('button',label,{type:'button',class:'toolbar-button',...attributes});
    button.addEventListener('click',()=>{Promise.resolve(handler()).catch(message);});parent.append(button);return button;
  }
  async function save(record, kind) {
    downloadIntent?.abort();downloadIntent=new AbortController();
    const intent=downloadIntent, identity=detailGeneration;
    const info=detail.querySelector('[data-download-status]');
    if(info)info.textContent='Verifying the selected original bytes…';
    try {
      const selected=version.value;
      const data=await (kind==='receipt' ? browser.downloadReceipt : browser.downloadResource)(record.dataset_id,selected,{signal:intent.signal});
      if(intent.signal.aborted || identity!==detailGeneration || !authority() || !dialog.open)return;
      const href=URL.createObjectURL(new Blob([data.bytes],{type:'application/octet-stream'}));
      const anchor=element('a',undefined,{href,download:data.filename});document.body.append(anchor);anchor.click();anchor.remove();
      setTimeout(()=>URL.revokeObjectURL(href),1000);
      if(info)info.textContent=`Verified ${data.bytes.length} original bytes; SHA-256 ${data.sha256}. Source entity only; scientific admission is not asserted.`;
    } catch(error) {if(error.name!=='AbortError' && identity===detailGeneration && info)info.textContent=`Download unavailable: ${error.message}`;}
  }
  async function selectDataset(identity, {write=true}={}) {
    const token=++detailGeneration;downloadIntent?.abort();overlay?.cancelZoom();
    detail.replaceChildren(element('p','Loading the selected resource metadata…'));
    try {
      const record=await browser.resource(identity);
      if(token!==detailGeneration || !dialog.open || !authority())return;
      if(!record || selectedSite && record.site_id!==selectedSite)throw Error('The dataset does not match the selected native site.');
      if(write && !publish(record.site_id,identity))return;
      detail.replaceChildren(element('h3',`Native dataset ${identity}`));
      detail.append(element('p',`Site ${record.site_id}; collection unit ${record.collection_unit_id}; type ${text(record.dataset_type)}; role ${text(record.exposure_role)}. Metadata only; no scientific admission is asserted.`));
      const selected=record.versions?.[version.value];
      if(!selected)throw Error('The exact selected source version is unavailable.');
      versionAndRights(record);
      rawSection(detail,`${version.value}: acquisition, qualification, source epoch and locators`,selected);
      rawSection(detail,'Native metadata, country decision and rights',record);
      const site=await browser.site(record.site_id);
      if(token!==detailGeneration || !dialog.open || !authority())return;
      rawSection(detail,'All retained native site variants and geometry qualifications',site);
      const actions=element('div',undefined,{class:'map-actions'});
      if(['development_resource_discovery','exposed_development'].includes(record.exposure_role)) {
        addAction(actions,'Verify and download original source entity',()=>save(record,'body'),{'data-resource-download':'body'});
        addAction(actions,'Verify and download HTTP receipt',()=>save(record,'receipt'),{'data-resource-download':'receipt'});
      } else detail.append(element('p','Metadata-only exposure role: source body and receipt downloads are blocked before access.'));
      addAction(actions,'Zoom to this metadata geometry',async()=>{await ensureOverlay();await overlay.zoom(record.site_id);});
      detail.append(actions,element('p',['http:','https:'].includes(location?.protocol)
        ? 'Downloads verify the pinned manifest, index and selected file before saving. A raw response may contain NoRecord or a method refusal; it is not a count of scientific observations.'
        : 'Verified source downloads are unavailable in file mode. Use HTTPS or a local HTTP server.',{'data-download-status':'',role:'status','aria-live':'polite'}));
    } catch(error) {if(token===detailGeneration)message(error);}
  }
  async function ensureOverlay() {
    overlay ||= createSourceResourceGeography({browser,map,leaflet,countries,onSelect:identity=>open({site:identity}),status:geometryStatus,current:authority});
    return overlay;
  }
  async function updateOverlay() {
    if(!inventory)return;
    await ensureOverlay();
    await overlay.update({enabled:showMetadata.checked,includeUnassigned:showUnassigned.checked,rows,sites:inventory.sites});
  }
  async function refresh({write=true}={}) {
    // Initial input values are applied by the opener once its complete index arrives.
    if(initializing)return;
    const token=++generation;
    try {
      const selected=statusFilter.value ? JSON.parse(statusFilter.value) : null;
      const found=await browser.search(search.value,{country:country.value,type:type.value,role:role.value,
        ...(selected ? {version:version.value,statusField:selected[0],status:selected[1]} : {})});
      if(token!==generation || !dialog.open || !authority())return;
      rows=found.filter(row=>!selectedSite || row.site_id===selectedSite);
      page=Math.min(page,Math.max(0,Math.ceil(rows.length/25)-1));
      list.replaceChildren();
      for(const row of rows.slice(page*25,page*25+25)) {
        const item=element('section',undefined,{class:'help-card','data-resource-dataset':row.record_id});
        addAction(item,`Dataset ${row.record_id} · site ${row.site_id} · ${text(row.dataset_type)}`,()=>selectDataset(row.record_id));
        item.append(element('p',(inventory.sites.find(site=>site.record_id===row.site_id)?.native_site_names || []).join(' / ')));
        const posture=sourceResourceQualification(row,version.value);
        const label=posture.field==='current_source_qualification_status' ? 'Derived current source qualification'
          : posture.field==='snapshot_qualification_status' ? 'Snapshot source qualification'
            : posture.field==='strict_current_binding_status' ? 'Current metadata binding'
              : ['source_terminal_status','acquisition_status'].includes(posture.field) ? 'Source capture posture' : 'Source qualification';
        const qualification=posture.metadataOnly ? 'Metadata only; numerical requests blocked.' : `${label}: ${ownedLabel(posture.value)}.`;
        item.append(element('p',`${row.country_code ?? 'UNASSIGNED'} · ${ownedLabel(row.exposure_role)} · ${version.value === 'doi_frozen' ? 'DOI-frozen' : 'Current'}. ${qualification}`));
        list.append(item);
      }
      previous.disabled=page===0;next.disabled=(page+1)*25>=rows.length;
      pageLabel.textContent=`Page ${page+1} of ${Math.max(1,Math.ceil(rows.length/25))}`;
      status.textContent=`${rows.length} matching metadata resources at ${new Set(rows.map(row=>row.site_id)).size} native sites. ${domain.record_count} resources in the catalogue; ${domain.site_count} metadata sites. Scientific population unchanged.`;
      status.dataset.state='available';
      if(write)publish();
      await updateOverlay();
    }catch(error){if(token===generation)message(error);}
  }
  for(const node of [search,country,type,role,statusFilter])node.addEventListener(node===search?'input':'change',()=>{page=0;detailGeneration++;downloadIntent?.abort();overlay?.cancel();detail.replaceChildren();void refresh();});
  version.addEventListener('change',()=>{detailGeneration++;downloadIntent?.abort();overlay?.cancel();detail.replaceChildren();page=0;void refresh();});
  previous.addEventListener('click',()=>{overlay?.cancelZoom();page--;void refresh();});next.addEventListener('click',()=>{overlay?.cancelZoom();page++;void refresh();});
  for(const node of [showMetadata,showUnassigned])node.addEventListener('change',()=>{void updateOverlay().catch(message);});
  function hide({write=true}={}) {
    generation++;detailGeneration++;downloadIntent?.abort();overlay?.cancelZoom();dialog.close();dialog.hidden=true;
    if(write && authority() && typeof publishQuery==='function')publishQuery({neotoma_catalogue:null,neotoma_site:null,neotoma_dataset:null,neotoma_version:null});
    returnFocus?.focus();
  }
  addAction(controls,'All metadata sites',()=>{overlay?.cancel();selectedSite=null;search.value='';country.value='';type.value='';role.value='';statusFilter.value='';page=0;detailGeneration++;downloadIntent?.abort();detail.replaceChildren();return open();});
  close.addEventListener('click',()=>hide());
  dialog.addEventListener('cancel',event=>{event.preventDefault();hide();});
  async function open(selection = {}) {
    const token=++generation;overlay?.cancel();initializing=true;
    if(!dialog.open)returnFocus=document.activeElement;dialog.hidden=false;if(!dialog.open)dialog.showModal();status.textContent='Loading source metadata…';
    try {
      if(selection.url) {
        const query=new URL(selection.url).searchParams, keys=['neotoma_catalogue','neotoma_site','neotoma_dataset','neotoma_version'];
        if(keys.some(key=>query.getAll(key).length>1 || query.has(key) && !query.get(key))
          || !query.has('neotoma_catalogue') || [...query.keys()].some(key=>key.startsWith('neotoma_')&&!keys.includes(key)))throw Error('The shared metadata URL is incomplete or ambiguous.');
        selection={...selection,catalogue:query.get('neotoma_catalogue'),site:query.get('neotoma_site'),dataset:query.get('neotoma_dataset'),version:query.get('neotoma_version')};
      }
      if(selection.catalogue && selection.catalogue!==domain.catalogue_manifest_sha256)throw Error('The shared URL names a different catalogue epoch.');
      if(selection.version && !['current','doi_frozen'].includes(selection.version))throw Error('The shared URL source version is unsupported.');
      if(selection.site && !/^[1-9][0-9]*$/.test(selection.site) || selection.dataset && !/^[1-9][0-9]*$/.test(selection.dataset))throw Error('The shared URL native identity is invalid.');
      version.value=selection.version || 'current';
      [inventory,context]=await Promise.all([browser.inventory(),browser.context()]);
      if(token!==generation || !dialog.open || !authority())return;
      if(selection.record) {
        const joined=context.legacy_site_references?.filter(row=>row.record_id===selection.record && row.site_id===selection.site && row.status==='matched') || [];
        if(joined.length!==1)throw Error('The selected scientific record has no exact native metadata-site join.');
      }
      if(selection.site && !inventory.sites.some(row=>row.record_id===selection.site))throw Error('The shared URL native site is absent from this catalogue.');
      selectedSite=selection.site || null;page=0;detailGeneration++;downloadIntent?.abort();detail.replaceChildren();
      for(const [node,field] of [[type,'dataset_type'],[role,'exposure_role']]) {
        node.replaceChildren(element('option',field==='dataset_type'?'All native types':'All exposure roles',{value:''}));
        [...new Set(inventory.resources.map(row=>row[field]).filter(value=>typeof value==='string'))].sort().forEach(value=>node.append(element('option',value,{value})));
      }
      statusFilter.replaceChildren(element('option','All version statuses',{value:''}));
      const states=new Map();inventory.resources.forEach(row=>Object.values(row.version_statuses || {}).forEach(value=>Object.entries(value).forEach(([key,state])=>states.set(JSON.stringify([key,state]),`${key}: ${text(state)}`))));
      [...states].sort((a,b)=>a[1].localeCompare(b[1])).forEach(([value,label])=>statusFilter.append(element('option',label,{value})));
      initializing=false;
      await refresh({write:selection.write!==false});
      if(selection.dataset && token+1===generation)await selectDataset(selection.dataset,{write:selection.write!==false});
      search.focus();
    }catch(error){if(token===generation){initializing=false;message(error);}}
  }
  return Object.freeze({open,hide,countriesChanged:()=>updateOverlay().catch(message)});
}
