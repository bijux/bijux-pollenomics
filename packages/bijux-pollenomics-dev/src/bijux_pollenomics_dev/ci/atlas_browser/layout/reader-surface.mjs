// Verify supplied atlas reader surfaces with the production runtime in Chromium.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createServer} from 'node:http';
import {mkdir, readFile, rm, writeFile} from 'node:fs/promises';
import {extname, join, relative, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {connectCdp, debuggerEndpoint, evaluate, launchChromium} from '../browser-transport.mjs';

export function readerSurfaceReadable(facts) {
  const valid = r => r && ['left','top','right','bottom'].every(k => Number.isFinite(r[k])) && r.right > r.left && r.bottom > r.top;
  const contains = (outer, inner) => outer.left <= inner.left + 1 && outer.top <= inner.top + 1 && inner.right <= outer.right + 1 && inner.bottom <= outer.bottom + 1;
  const separate = (a, b) => a.bottom <= b.top + 1 || b.bottom <= a.top + 1 || a.right <= b.left + 1 || b.right <= a.left + 1;
  const surfaces = ['toolbar','map','status','footer'];
  if (!valid(facts.viewport) || !surfaces.every(key => valid(facts[key]) && contains(facts.viewport, facts[key]))) return false;
  if (!Number.isFinite(facts.document_width) || !Number.isFinite(facts.document_height) || facts.document_width > facts.viewport.right + 1 || facts.document_height > facts.viewport.bottom + 1) return false;
  if (!surfaces.every((key, index) => surfaces.slice(index + 1).every(other => separate(facts[key], facts[other])))) return false;
  if (facts.map.bottom - facts.map.top + 1 < Math.min(260, facts.viewport.bottom * .30)) return false;
  if (!Array.isArray(facts.targets) || !facts.targets.length) return false;
  if (!facts.targets.every(target => valid(target.rect) && target.visible && target.center_hit && contains(facts.viewport, target.rect) && valid(facts[target.owner]) && contains(facts[target.owner], target.rect) && (!target.touch || (facts.viewport.right > 640 && facts.viewport.bottom > 640) || target.rect.bottom - target.rect.top >= 43.99))) return false;
  if (facts.reader && (!valid(facts.reader) || !contains(facts.viewport, facts.reader) || !separate(facts.reader, facts.toolbar) || !separate(facts.reader, facts.status) || !separate(facts.reader, facts.footer) || !facts.reader_scrollable)) return false;
  return true;
}

export function collectReaderSurface() {
  const rect = node => {const r = node.getBoundingClientRect();return {left:r.left,top:r.top,right:r.right,bottom:r.bottom};};
  const visible = node => {const r = node.getBoundingClientRect(), style = getComputedStyle(node);return Boolean(r.width && r.height && style.display !== 'none' && style.visibility !== 'hidden');};
  const facts = {viewport:{left:0,top:0,right:innerWidth,bottom:innerHeight},document_width:document.documentElement.scrollWidth,document_height:document.documentElement.scrollHeight,targets:[]};
  for (const [key, selector] of Object.entries({toolbar:'.map-topbar',map:'.map-viewport',status:'.map-status',footer:'.map-reader-footer'})) facts[key] = rect(document.querySelector(selector));
  const targets = [
    ...[...document.querySelectorAll('.map-topbar-main button,.topbar-time-stepper button')].map(node => ({node,owner:'toolbar',touch:true})),
    ...['center-readout','basemap-readout'].map(id => ({node:document.getElementById(id),owner:'status',touch:false})),
    ...[...document.querySelectorAll('.map-reader-footer .leaflet-control')].map(node => ({node,owner:'footer',touch:false})),
    ...[...document.querySelectorAll('.map-reader-footer .leaflet-bar a')].map(node => ({node,owner:'footer',touch:true})),
  ];
  const search = document.getElementById('topbar-search');
  if (visible(search)) {
    facts.search = rect(search);
    targets.push({node:document.getElementById('search-input'),owner:'search',touch:true});
    const result = search.querySelector('[data-search-index]');
    if (result) {facts.results=rect(document.getElementById('search-results'));targets.push({node:result,owner:'results',touch:true,clip:document.getElementById('search-results')});}
  }
  for (const {node,owner,touch,clip} of targets) {
    const intrinsic = rect(node), r = {...intrinsic};
    if (clip) {const bounds=rect(clip);r.left=Math.max(r.left,bounds.left);r.top=Math.max(r.top,bounds.top);r.right=Math.min(r.right,bounds.right);r.bottom=Math.min(r.bottom,bounds.bottom);}
    facts.targets.push({id:node.id || node.className,owner,touch,rect:r,intrinsic_rect:intrinsic,visible:visible(node),center_hit:node.contains(document.elementFromPoint((r.left+r.right)/2,(r.top+r.bottom)/2))});
  }
  const reader = document.getElementById('focus-card');
  if (visible(reader)) {facts.reader = rect(reader);facts.reader_scrollable = ['auto','scroll'].includes(getComputedStyle(reader).overflowY);}
  return facts;
}

async function verify(candidateDirectory, outputDirectory, browserBinary) {
  const candidate = resolve(candidateDirectory), output = resolve(outputDirectory);
  await mkdir(output, {recursive:false});
  const expectations = JSON.parse(await readFile(join(candidate, 'expectations.json'), 'utf8'));
  const receipt = {schema_version:'atlas-reader-surface-verification.v1',status:'FAIL',scope:'Supplied candidate browser layout only; no scientific admission or full atlas qualification',cases:[],negative_controls:[],runtime_errors:[]};
  const requests = new Map();
  const server = createServer(async (request, response) => {
    const path = resolve(candidate, `.${decodeURIComponent(new URL(request.url, 'http://localhost').pathname)}`);
    if (relative(candidate,path).startsWith('..')) {response.writeHead(403).end();return;}
    try {const bytes = await readFile(path);requests.set(path,createHash('sha256').update(bytes).digest('hex'));response.writeHead(200,{'Content-Type':{'.html':'text/html','.js':'application/javascript','.css':'text/css'}[extname(path)] || 'application/octet-stream','Cache-Control':'no-store'}).end(bytes);} catch {response.writeHead(404).end();}
  });
  let runtime, cdp, timer;
  const profile = join(output,'browser-profile');
  try {
    await new Promise(accept => server.listen(0,'127.0.0.1',accept));
    await mkdir(profile);
    runtime = await launchChromium(browserBinary,profile);
    timer = setTimeout(() => runtime.browser.kill('SIGKILL'),120000);
    const endpoint = await debuggerEndpoint(runtime.browser,15000), origin = new URL(endpoint);origin.protocol = 'http:';origin.pathname = '';
    const target = await (await fetch(`${origin.origin}/json/new?about:blank`,{method:'PUT'})).json();
    cdp = await connectCdp(target.webSocketDebuggerUrl);
    await cdp.send('Page.enable');await cdp.send('Runtime.enable');await cdp.send('Network.enable');
    await cdp.send('Network.setBlockedURLs',{urls:['https://*','http://tile.*']});
    cdp.onEvent(event => {if (event.method === 'Runtime.exceptionThrown') receipt.runtime_errors.push(event.params.exceptionDetails);});
    receipt.browser = await cdp.send('Browser.getVersion');
    const waitFor = async expression => {const until = Date.now()+10000;while(Date.now()<until){if(await evaluate(cdp,expression))return;await new Promise(accept=>setTimeout(accept,40));}throw Error(`Browser condition timed out: ${expression}`);};
    const capture = async (item, state) => {
      const facts = await evaluate(cdp,`(${collectReaderSurface.toString()})()`);
      item[state] = facts;
      const shot = await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
      await writeFile(join(output,`${item.width}-${state}.png`),Buffer.from(shot.data,'base64'));
      assert.ok(readerSurfaceReadable(facts),`${item.width}×${item.height} ${state} reader surface is clipped, obscured or outside its viewport`);
    };
    const click = async selector => {
      const point = await evaluate(cdp,`(()=>{const n=document.querySelector(${JSON.stringify(selector)}),r=n.getBoundingClientRect();let left=r.left,top=r.top,right=r.right,bottom=r.bottom;for(let p=n.parentElement;p;p=p.parentElement){if(/auto|scroll|hidden/.test(getComputedStyle(p).overflowY)){const b=p.getBoundingClientRect();left=Math.max(left,b.left);top=Math.max(top,b.top);right=Math.min(right,b.right);bottom=Math.min(bottom,b.bottom);}}const x=(left+right)/2,y=(top+bottom)/2;if(right<=left||bottom<=top||!n.contains(document.elementFromPoint(x,y)))throw Error('Click target obscured');return {x,y};})()`);
      await cdp.send('Input.dispatchMouseEvent',{type:'mousePressed',...point,button:'left',clickCount:1});
      await cdp.send('Input.dispatchMouseEvent',{type:'mouseReleased',...point,button:'left',clickCount:1});
    };
    for (const [width,height] of [[320,568],[390,844],[768,900],[1440,900],[568,320],[844,390]]) {
      const item = {width,height};receipt.cases.push(item);
      await cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});
      await cdp.send('Page.navigate',{url:`http://127.0.0.1:${server.address().port}/index.html#basemap=none`});
      await waitFor('globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true');
      await capture(item,'opening');
      if (width === 320) {
        for (const [mutation, selector, transform] of [
          ['offscreen-footer','.map-reader-footer','translateY(100px)'],
          ['clipped-status','#center-readout','translateY(100px)'],
          ['obscured-zoom','.leaflet-control-zoom-in',null],
        ]) {
          const original = await evaluate(cdp,`document.querySelector(${JSON.stringify(selector)}).getAttribute('style')`);
          try {
            await evaluate(cdp,`(()=>{const n=document.querySelector(${JSON.stringify(selector)});${transform ? `n.style.transform=${JSON.stringify(transform)}` : "n.style.pointerEvents='none'"};})()`);
            const facts = await evaluate(cdp,`(${collectReaderSurface.toString()})()`), refused = !readerSurfaceReadable(facts);
            receipt.negative_controls.push({mutation,refused,facts});
            assert.equal(refused,true,`Injected ${mutation} must be refused`);
          } finally {
            await evaluate(cdp,`(()=>{const n=document.querySelector(${JSON.stringify(selector)});${original === null ? "n.removeAttribute('style')" : `n.setAttribute('style',${JSON.stringify(original)})`};})()`);
          }
        }
      }
      await click('#search-toggle');
      await evaluate(cdp,`(()=>{const n=document.getElementById('search-input');n.value=${JSON.stringify(expectations.query)};n.dispatchEvent(new Event('input',{bubbles:true}));})()`);
      await waitFor("document.querySelector('[data-search-index]') !== null");
      await capture(item,'search');
      await click('[data-search-index]');
      await waitFor(`document.getElementById('focus-title').textContent === ${JSON.stringify(expectations.title)}`);
      await capture(item,'focused');
      await evaluate(cdp,"document.getElementById('focus-card').scrollTop = document.getElementById('focus-card').scrollHeight");
      await capture(item,'reader_scrolled');
      item.export_target = await evaluate(cdp,"(()=>{const n=document.getElementById('focus-export');n.scrollIntoView({block:'center'});const r=n.getBoundingClientRect(),parent=document.getElementById('focus-card').getBoundingClientRect();return {enabled:!n.disabled,center_hit:n.contains(document.elementFromPoint(r.left+r.width/2,r.top+r.height/2)),inside_reader:r.top>=parent.top&&r.bottom<=parent.bottom,minimum_touch_height:r.height>=44};})()");
      assert.ok(Object.values(item.export_target).every(Boolean),'Source export must be reachable within the scrolled reader');
      await capture(item,'export_reachable');
      await evaluate(cdp,"document.getElementById('focus-card').scrollTop = 0");
      await click('#focus-close');
      await capture(item,'cleared');
    }
    assert.equal(receipt.runtime_errors.length,0);
    receipt.status = 'PASS';
  } catch(error) {receipt.error = String(error.stack || error);process.exitCode = 1;}
  finally {
    clearTimeout(timer);cdp?.close();await runtime?.close();await new Promise(accept=>server.close(accept));await rm(profile,{recursive:true,force:true});
    receipt.served_files_sha256 = Object.fromEntries([...requests].map(([path,hash])=>[relative(candidate,path),hash]));
    receipt.inputs_stable = (await Promise.all([...requests].map(async ([path,hash])=>createHash('sha256').update(await readFile(path)).digest('hex')===hash))).every(Boolean);
    if(!receipt.inputs_stable){receipt.status='FAIL';process.exitCode=1;}
    receipt.verifier_sha256 = createHash('sha256').update(await readFile(fileURLToPath(import.meta.url))).digest('hex');
    await writeFile(join(output,'receipt.json'),JSON.stringify(receipt,null,2)+'\n');
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if(process.argv.length !== 5) throw Error('usage: node reader-surface.mjs CANDIDATE OUTPUT BROWSER');
  await verify(...process.argv.slice(2));
}
