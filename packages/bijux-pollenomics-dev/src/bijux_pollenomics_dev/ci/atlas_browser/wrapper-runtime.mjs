// Qualify the actual docs iframe separately from direct-map and current-loader contracts.
import {execFileSync, spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdir, mkdtemp, readFile, realpath, rm, stat, writeFile} from 'node:fs/promises';
import {delimiter, extname, join, relative, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {connectCdp, debuggerEndpoint, evaluate, launchChromium} from './browser-transport.mjs';
import {providerInterception, verifyProviderFailureMatrix} from './provider-failures.mjs';

const moduleDirectory = fileURLToPath(new URL('.', import.meta.url));
const ownerPath = 'configs/docs/maps/report-owner.json';
const publicationOwnerPath = 'configs/docs/publication/admission.py';
const publicationReceiptLimit = 32 * 1024 * 1024;
const productionSite = 'https://bijux.io/bijux-pollenomics/';
export const parentOutput = 'public/nordic-atlas/index.html';
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const git = (repository, ...args) => execFileSync('git', args, {cwd: repository, encoding: 'utf8'}).trim();

async function readPublication(repository, site) {
  // runWrapper invokes the normal verifier before using this byte-bound plan.
  // A serialized inventory supplies expected bytes, never publication authority.
  const checkpointRaw = await readFile(join(repository, 'artifacts/website-security/source-identity.json'));
  const publicationRaw = await readFile(join(repository, 'artifacts/website-security/publication.json'));
  if (checkpointRaw.length > 16777216 || publicationRaw.length > publicationReceiptLimit) throw Error('publication receipt exceeds byte budget');
  const checkpoint = JSON.parse(checkpointRaw), publication = JSON.parse(publicationRaw);
  const source = publication.qualification?.source;
  const standard = (await readFile(join(repository, '.github/standards/bijux-docs.sha'), 'utf8')).trim();
  if (publication.schema !== 2 || publication.repository_source_sha !== git(repository, 'rev-parse', 'HEAD')
      || checkpoint.repository_source?.sha !== publication.repository_source_sha
      || checkpoint.repository_source?.tree !== git(repository, 'rev-parse', 'HEAD^{tree}')
      || publication.standard_sha !== standard || checkpoint.standard?.sha !== standard
      || publication.site_url !== productionSite || checkpoint.site_url !== publication.site_url
      || publication.site_dir !== 'artifacts/docs/site' || checkpoint.site_dir !== publication.site_dir
      || await realpath(site) !== await realpath(join(repository, publication.site_dir))
      || source?.sha256 !== digest(checkpointRaw) || JSON.stringify(source?.receipt) !== JSON.stringify(checkpoint)) {
    throw Error('publication inventory differs from current source or selected site');
  }
  if (!Array.isArray(publication.files) || publication.files.length > 100000) throw Error('publication inventory exceeds member budget');
  const members = new Map();
  for (const row of publication.files) {
    if (typeof row.path !== 'string' || row.path.startsWith('/') || row.path.includes('\\')
        || row.path.split('/').some(part => !part || part === '.' || part === '..')
        || !/^[a-f0-9]{64}$/.test(row.sha256) || !Number.isSafeInteger(row.bytes) || row.bytes < 0
        || members.has(row.path)) throw Error('publication member is ambiguous');
    members.set(row.path, row);
  }
  const records = publication.qualification?.csp?.receipt?.embedded?.records;
  if (!Array.isArray(records) || records.length > 100000) throw Error('qualified embedded publication records are unavailable');
  return {members, records, source:publication.repository_source_sha, sha256:digest(publicationRaw)};
}

export function requireScopedCandidate(repository, paths, expectedHead = null) {
  const head = git(repository, 'rev-parse', 'HEAD');
  if (expectedHead !== null && head !== expectedHead) throw Error('consumed candidate revision changed');
  for (const path of paths) {
    if (git(repository, 'ls-files', '--error-unmatch', '--', path) !== path) throw Error(`consumed path is not tracked: ${path}`);
  }
  if (git(repository, 'diff', 'HEAD', '--name-only', '--', ...paths)
      || git(repository, 'ls-files', '--others', '--exclude-standard', '--', ...paths)) throw Error('consumed candidate paths have local edits');
  return head;
}

export async function readWrapperAuthority(repository, site) {
  const publication = await readPublication(repository, site);
  const owner = JSON.parse(await readFile(join(repository, ownerPath), 'utf8'));
  const parents = owner.parents.filter(row => row.output === parentOutput);
  if (parents.length !== 1 || parents[0].reports.length !== 1) throw Error('Nordic wrapper authority is ambiguous');
  const parent = parents[0];
  const reports = owner.reports.filter(row => row.output === parent.reports[0]);
  if (reports.length !== 1) throw Error('Nordic child authority is ambiguous');
  const report = reports[0];
  for (const [kind, owned, input] of [
    ['owned-parent-frame', parent, parent.built_html_sha256],
    ['owned-report', report, report.source.sha256],
  ]) {
    const records = publication.records.filter(row => row.path === owned.output);
    if (records.length !== 1 || records[0].kind !== kind || records[0].input_sha256 !== input
        || records[0].source?.path !== owned.source.path || records[0].source?.sha256 !== owned.source.sha256) {
      throw Error('raw embedded source differs from qualified publication composition');
    }
  }
  const html = await readFile(join(site, parent.output));
  if (digest(await readFile(join(repository, parent.source.path))) !== parent.source.sha256) throw Error('wrapper source differs from approved parent');
  const expected = new Map([...publication.members].map(([path,row])=>[path,row.sha256]));
  if (digest(html) !== expected.get(parent.output) || html.length !== publication.members.get(parent.output)?.bytes) throw Error('built wrapper differs from publication inventory');
  const childHtml = await readFile(join(site, report.output));
  if (digest(childHtml) !== expected.get(report.output) || childHtml.length !== publication.members.get(report.output)?.bytes) throw Error('built child differs from publication inventory');
  if (digest(await readFile(join(repository, report.source.path))) !== report.source.sha256) throw Error('canonical map differs from approved source');
  for (const [path, row] of Object.entries(report.resources)) {
    const raw = await readFile(join(repository, row.source));
    if (digest(raw) !== row.sha256 || expected.get(path) !== row.sha256
        || publication.members.get(path).bytes !== raw.length) throw Error('owned resource differs from source or publication inventory');
  }
  const parentUrl = new URL(parent.output, productionSite).href;
  const childUrl = new URL(report.output, productionSite).href;
  const iframe = [...html.toString().matchAll(/<iframe\b[^>]*\bsrc="([^"]+)"/g)];
  if (iframe.length !== 1 || new URL(iframe[0][1], parentUrl).href !== childUrl) throw Error('real wrapper iframe target differs');
  const match = childHtml.toString().match(/<script[^>]*id="atlas-static-bootstrap"[^>]*>([\s\S]*?)<\/script>/);
  if (!match) throw Error('child scientific bootstrap is unavailable');
  const bootstrap = JSON.parse(match[1]);
  return {parent, report, parentUrl, childUrl, expected, members:publication.members, publication:{source:publication.source,sha256:publication.sha256}, buildId: bootstrap.build_id, version: bootstrap.version};
}

export async function fulfillPublicationRequest(cdp, site, request, authority) {
  const urlText = request.request.url, method = request.request.method;
  const url = new URL(urlText), base = new URL(productionSite);
  if (method !== 'GET' || url.href !== urlText || url.origin !== base.origin || url.username || url.password
      || Object.keys(request.request.headers ?? {}).some(key => /authorization|api[-_]?key|token|cookie/i.test(key))
      || url.search || url.hash || !url.pathname.startsWith(base.pathname)) throw Error('request is outside the exact production publication');
  const key = decodeURIComponent(url.pathname.slice(base.pathname.length));
  if (key.includes('\\') || key.split('/').some(part => !part || part === '.' || part === '..')
      || !authority.expected.has(key) || new URL(key, productionSite).href !== url.href) throw Error('request is not an exact publication member');
  const {bytes, path} = await readSiteMember(site, '/' + key, authority.expected);
  if (authority.members.get(key)?.bytes !== bytes.length) throw Error('publication member byte count differs');
  await cdp.send('Fetch.fulfillRequest', {requestId:request.requestId, responseCode:200, responseHeaders:[
    {name:'Cache-Control',value:'no-store'},
    {name:'Content-Type',value:({'.html':'text/html', '.js':'text/javascript', '.css':'text/css', '.json':'application/json', '.png':'image/png', '.svg':'image/svg+xml', '.woff2':'font/woff2'})[extname(path)] ?? 'application/octet-stream'},
  ], body:bytes.toString('base64')});
  return {path:key, bytes:bytes.length};
}

export async function readSiteMember(site, pathname, expected) {
  const root = await realpath(site);
  const requested = resolve(root, `.${decodeURIComponent(pathname)}`);
  const path = await realpath(requested);
  if (relative(root, path).startsWith('..')) throw Error('site request escapes root');
  if (path !== requested) throw Error('site member alias is forbidden');
  const info = await stat(path);
  if (!info.isFile() || info.nlink !== 1 || info.size > 16777216) throw Error('site member is aliased, missing or oversized');
  const bytes = await readFile(path), key = relative(root, path);
  if (!expected.has(key) || digest(bytes) !== expected.get(key)) throw Error(`owned site member differs: ${key}`);
  return {bytes, path};
}

export function childRuntime(raw, contextId) {
  if (!Number.isInteger(contextId) || contextId <= 0) throw Error('child execution context is invalid');
  return {...raw, send(method, params={}) {return raw.send(method, method === 'Runtime.evaluate' ? {...params,contextId} : params);}};
}

async function wrapperFacts(raw) {
  return evaluate(raw, `(() => {
    const frame=document.querySelector('iframe'),box=frame?.getBoundingClientRect();
    return {title:document.title,parent_path:location.pathname,iframe_path:frame?new URL(frame.src).pathname:null,
      iframe_visible:Boolean(box&&box.width>0&&box.height>0&&box.top<innerHeight&&box.bottom>0),
      navigation_available:Boolean(document.querySelector('.md-header a[href]')&&document.querySelector('.md-sidebar a[href]'))};
  })()`);
}

function evidenceIdentity(snapshot) {
  return Object.fromEntries(['build_id', 'scope_slug', 'version', 'countries', 'time_window_bp',
    'source_chronology', 'visible_point_count', 'visible_polygon_layer_count',
    'visible_governed_candidate_count', 'scientific_posture'].map(key => [key, snapshot[key]]));
}

export async function verifyPublication(repository, {timeoutMs=900000, maxOutputBytes=16777216, signal}={}) {
  if (!Number.isInteger(timeoutMs) || timeoutMs <= 0 || timeoutMs > 900000
      || !Number.isInteger(maxOutputBytes) || maxOutputBytes <= 0 || maxOutputBytes > 16777216) throw Error('publication verification bounds are invalid');
  if (process.platform === 'win32') throw Error('publication verification requires owned POSIX process groups');
  if (signal !== undefined && !(signal instanceof AbortSignal)) throw Error('publication cancellation signal is invalid');
  if (signal?.aborted) throw Error('publication verification cancelled before launch');
  repository = resolve(repository);
  const command = [join(repository,'artifacts/docs/publication/python/bin/python'), '-B', join(repository,publicationOwnerPath), 'verify'];
  const environment={...process.env,PYTHONDONTWRITEBYTECODE:'1',PYTHONNOUSERSITE:'1',
    PYTHONPATH:['bijux-pollenomics','bijux-pollenomics-dev','bijux-pollenomics-lra','pollenomics'].map(name=>join(repository,'packages',name,'src')).join(delimiter)};
  delete environment.PYTHONHOME;
  const started = performance.now(), stdout = [], stderr = [];
  let reason=null, spawnFailure=null, captured=0, observed=0, forceTimer;
  const child = spawn(command[0],command.slice(1),{cwd:repository,env:environment,detached:true,stdio:['ignore','pipe','pipe']});
  const groupExists = () => {
    if (!child.pid) return false;
    try {process.kill(-child.pid,0);return true;} catch(error) {if(error.code==='ESRCH')return false;throw error;}
  };
  const send = value => {
    if (!child.pid) return;
    try {process.kill(-child.pid,value);} catch(error) {if(error.code!=='ESRCH')spawnFailure ??= error;}
  };
  const stop = why => {
    reason ??= why;
    send('SIGTERM');
    forceTimer ??= setTimeout(()=>send('SIGKILL'),250);
  };
  const capture = (parts, chunk) => {
    observed += chunk.length;
    const kept=chunk.subarray(0,Math.max(0,maxOutputBytes-captured));
    if(kept.length){parts.push(kept);captured+=kept.length;}
    if(observed>maxOutputBytes)stop('output byte limit exceeded');
  };
  child.stdout.on('data',chunk=>capture(stdout,chunk));
  child.stderr.on('data',chunk=>capture(stderr,chunk));
  child.on('error',error=>{spawnFailure=error;});
  const closed = new Promise(accept=>child.once('close',(code,exitSignal)=>accept({code,signal:exitSignal})));
  const cancel = () => stop('cancelled');
  process.on('SIGTERM',cancel);process.on('SIGINT',cancel);
  signal?.addEventListener('abort',cancel,{once:true});
  const timer=setTimeout(()=>stop('deadline exceeded'),timeoutMs);
  if(signal?.aborted)cancel();
  let exit;
  try {
    exit=await closed;
    if(groupExists()) {
      stop(reason ?? 'verifier left surviving descendants');
      await new Promise(accept=>setTimeout(accept,250));
      send('SIGKILL');
      const deadline=performance.now()+1000;
      while(groupExists() && performance.now()<deadline)await new Promise(accept=>setTimeout(accept,20));
      if(groupExists())spawnFailure ??= Error('verification process group did not close');
    }
  } finally {
    clearTimeout(timer);clearTimeout(forceTimer);
    signal?.removeEventListener('abort',cancel);
    process.removeListener('SIGTERM',cancel);process.removeListener('SIGINT',cancel);
  }
  const completed={command,returncode:exit.code,signal:exit.signal,duration_seconds:(performance.now()-started)/1000,
    timeout_seconds:timeoutMs/1000,max_output_bytes:maxOutputBytes,captured_output_bytes:captured,
    observed_output_bytes:observed,reason,process_group_closed:!groupExists(),stdout:Buffer.concat(stdout),stderr:Buffer.concat(stderr)};
  if(reason || spawnFailure || exit.code!==0) {
    const error=Error(`owning publication verification refused: ${reason ?? spawnFailure?.message ?? 'exit '+exit.code}`);
    error.verification=completed;
    throw error;
  }
  return completed;
}

async function savePublicationVerification(output, completed) {
  const {stdout,stderr,...summary}=completed;
  await writeFile(join(output,'publication-verification.stdout.log'),stdout);
  await writeFile(join(output,'publication-verification.stderr.log'),stderr);
  await writeFile(join(output,'publication-verification.json'),JSON.stringify(summary,null,2)+'\n');
}

// Own each target from creation through failed acquisition and normal teardown.
export function createWrapperAtlasOwner({site, authority, debuggerOrigin, requests, serverErrors,
  externalRefusals, timeoutMs, fetchTarget=fetch, connect=connectCdp}) {
  const lifecycle = [];
  const detail = error => String(error?.stack || error).slice(0,4096);
  function note(atlas, phase, fields={}) {
    const bounded=Object.fromEntries(Object.entries(fields).map(([key,value])=>[key,typeof value==='string'?value.slice(0,512):value]));
    const row={phase,elapsed_ms:performance.now()-atlas.started,...bounded};
    if(atlas.lifecycle.events.length<128)atlas.lifecycle.events.push(row);
    else atlas.lifecycle.omitted_events++;
  }
  function stage(atlas, phase) {atlas.lifecycle.phase=phase;note(atlas,phase);}
  function closeTarget(atlas) {
    if(!atlas.target)return Promise.resolve();
    return atlas.targetClose ??= (async()=>{
      atlas.lifecycle.teardown.target_close_attempted=true;note(atlas,'target_close_requested');
      const response=await fetchTarget(`${debuggerOrigin.origin}/json/close/${atlas.target.id}`);
      if(!response.ok)throw Error(`owned target close failed: ${response.status}`);
      // This is the debugger HTTP acknowledgement, not a target-destroyed event.
      await response.text();atlas.lifecycle.teardown.target_close_acknowledged=true;
      note(atlas,'target_close_acknowledged');
    })();
  }
  async function closeAtlas(atlas) {
    return atlas.closing ??= (async()=>{
      const start=performance.now();stage(atlas,'teardown');let failure;
      try {
        if(atlas.raw && atlas.parentBefore) {
          const parentAfter=await wrapperFacts(atlas.raw);
          if(JSON.stringify(parentAfter)!==JSON.stringify(atlas.parentBefore))atlas.runtimeFailures.push({kind:'wrapper-state',detail:'parent title/navigation/iframe changed during child journey'});
        }
      } catch(error) {failure=error;}
      try {
        if(atlas.interception)await atlas.interception.settle(async()=>{
          await Promise.all(atlas.localReplies);await closeTarget(atlas);
        });
      } catch(error) {failure ??= error;}
      finally {
        try {await closeTarget(atlas);} catch(error) {failure ??= error;}
        if(atlas.raw) {
          try {atlas.raw.close();atlas.lifecycle.teardown.transport_close_requested=true;}
          catch(error) {failure ??= error;}
        }
        atlas.lifecycle.teardown.elapsed_ms=performance.now()-start;
        atlas.lifecycle.status=failure?'teardown_failed':'closed';note(atlas,'teardown_finished');
      }
      if(failure) {
        atlas.runtimeFailures.push({kind:'wrapper-teardown',detail:detail(failure)});
        atlas.lifecycle.teardown.error=detail(failure);throw failure;
      }
    })();
  }
  async function openAtlas(_scope, _debuggerOrigin, options) {
    const atlas={started:performance.now(),runtimeFailures:[],providerRequests:[],contexts:new Map(),localReplies:new Set()};
    atlas.lifecycle={case:options.name,status:'opening',phase:'create_target',target_id:null,
      events:[],omitted_events:0,teardown:{target_close_attempted:false,target_close_acknowledged:false,transport_close_requested:false}};
    lifecycle.push(atlas.lifecycle);
    try {
      stage(atlas,'create_target');
      const response=await fetchTarget(`${debuggerOrigin.origin}/json/new?about:blank`,{method:'PUT'});
      if(!response.ok)throw Error(`owned target creation failed: ${response.status}`);
      const target=atlas.target=await response.json();atlas.lifecycle.target_id=String(target.id).slice(0,256);
      stage(atlas,'connect_target');const raw=atlas.raw=await connect(target.webSocketDebuggerUrl);
      const {runtimeFailures, providerRequests, contexts, localReplies} = atlas;
      const interception = atlas.interception = providerInterception(raw, providerRequests, runtimeFailures, true, options.providerFailure);
      raw.onEvent(event => {
        if (['Page.frameStartedLoading','Page.frameStoppedLoading','Page.frameNavigated','Page.domContentEventFired','Page.loadEventFired','Runtime.executionContextCreated'].includes(event.method)) note(atlas, event.method, {
          frame_id:event.params.frameId ?? event.params.frame?.id ?? event.params.context?.auxData?.frameId ?? null,
          loader_id:event.params.loaderId ?? event.params.frame?.loaderId ?? null,
        });
        if (event.method === 'Runtime.executionContextCreated' && event.params.context.auxData?.isDefault) contexts.set(event.params.context.auxData.frameId, event.params.context.id);
        if (event.method === 'Runtime.exceptionThrown') runtimeFailures.push({kind:'exception', detail:event.params.exceptionDetails?.text ?? ''});
        if (event.method === 'Runtime.consoleAPICalled' && event.params.type === 'error') runtimeFailures.push({kind:'console-error', detail:event.params.args.map(row => row.description ?? row.value ?? '').join(' ')});
        const url = event.params?.request?.url;
        const provider = url && ['tile.openstreetmap.org','tile.opentopomap.org'].includes(new URL(url).hostname);
        if (event.method !== 'Fetch.requestPaused' || provider) interception.handle(event);
        if (event.method === 'Fetch.requestPaused' && !provider) {
          const task = (async () => {
            try {
              const reply = await fulfillPublicationRequest(raw, site, event.params, authority);
              requests.push({url, path:reply.path, status:200, bytes:reply.bytes, case:options.name, target_id:target.id, elapsed_ms:performance.now()-atlas.started});
            } catch (error) {
              externalRefusals.push(url);
              serverErrors.push({url, error:String(error)});
              await raw.send('Fetch.failRequest', {requestId:event.params.requestId, errorReason:'BlockedByClient'});
            }
          })().catch(error => runtimeFailures.push({kind:'request-reply', detail:String(error)})).finally(() => localReplies.delete(task));
          localReplies.add(task);
        }
        if (event.method === 'Network.requestWillBeSent' && provider) providerRequests.push({url,request_id:event.params.requestId,...(interception.requestsBlocked ? {blocked_during_teardown:true} : {})});
      });

      stage(atlas,'configure_target');
      for (const domain of ['Page','Runtime','Network']) await raw.send(`${domain}.enable`);
      await raw.send('Network.setCacheDisabled',{cacheDisabled:true});
      await raw.send('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
      await raw.send('Fetch.enable',{patterns:[{urlPattern:'http*',requestStage:'Request'}]});
      // Controlled reader input before child bootstrap; neither HTML file changes.
      await raw.send('Page.addScriptToEvaluateOnNewDocument',{source:`if(location.href===${JSON.stringify(authority.childUrl)})history.replaceState(null,'',${JSON.stringify(options.hash)});`});
      stage(atlas,'navigate');
      note(atlas,'load_wait_registered');
      const loaded=raw.waitFor('Page.loadEventFired',timeoutMs).then(event=>{note(atlas,'load_event_received');return event;});
      // Generic load events stay separate from frame/loader navigation evidence.
      note(atlas,'navigate_requested');
      const navigation=raw.send('Page.navigate',{url:authority.parentUrl}).then(reply=>{
        atlas.lifecycle.navigation={frame_id:reply.frameId?.slice(0,512)??null,loader_id:reply.loaderId?.slice(0,512)??null,error:reply.errorText?.slice(0,512)??null};
        note(atlas,'navigate_response',atlas.lifecycle.navigation);
        if(reply.errorText)throw Error(`owned navigation failed: ${reply.errorText}`);
        return reply;
      });
      // Observe both rejections immediately, including a delayed navigate reply.
      await Promise.all([navigation,loaded]);
      stage(atlas,'resolve_child');
      const tree=(await raw.send('Page.getFrameTree')).frameTree;
      const child=(tree.childFrames??[]).find(row=>{const url=new URL(row.frame.url);url.hash='';return url.href===authority.childUrl;});
      if(!child||!contexts.has(child.frame.id))throw Error('real child execution context is unavailable');
      atlas.lifecycle.child_frame_id=child.frame.id.slice(0,512);atlas.lifecycle.child_loader_id=child.frame.loaderId?.slice(0,512)??null;
      const contextId=contexts.get(child.frame.id);
      await evaluate(raw, `document.querySelector('iframe').scrollIntoView({block:'center'})`);
      atlas.cdp=childRuntime(raw,contextId);atlas.parentBefore=await wrapperFacts(raw);
      if(!atlas.parentBefore.title||!atlas.parentBefore.iframe_visible||!atlas.parentBefore.navigation_available)throw Error('real docs wrapper is not visibly usable');
      atlas.lifecycle.status='ready';stage(atlas,'ready');return atlas;
    } catch(value) {
      const error=value instanceof Error?value:Error(String(value));
      atlas.lifecycle.failure_phase=atlas.lifecycle.phase;atlas.lifecycle.error=detail(error);
      try {await closeAtlas(atlas);} catch(cleanupError) {atlas.lifecycle.cleanup_error=detail(cleanupError);}
      atlas.lifecycle.status='open_failed';
      error.wrapperFailure={lifecycle:atlas.lifecycle,provider_requests:atlas.providerRequests.slice(0,128).map(row=>({...row,url:row.url?.slice(0,2048),request_id:row.request_id?.slice(0,256),network_id:row.network_id?.slice(0,256)??null,interception_error:row.interception_error?.slice(0,4096)})),runtime_failures:atlas.runtimeFailures.slice(0,32).map(row=>({...row,detail:detail(row.detail).slice(0,2048)})),
        omitted_provider_requests:Math.max(0,atlas.providerRequests.length-128),omitted_runtime_failures:Math.max(0,atlas.runtimeFailures.length-32)};
      throw error;
    }
  }
  return {openAtlas,closeAtlas,lifecycle};
}

export async function writeWrapperScenario(output, scenario, receipts) {
  const path=`nordic-wrapper/${scenario.name}.json`;
  try {
    await mkdir(join(output,'nordic-wrapper'),{recursive:true});
    await writeFile(join(output,path),JSON.stringify(scenario,null,2)+'\n');
    receipts.push(path);
  } catch(error) {
    if(scenario.status!=='open_failed')throw error;
    // Receipt IO must not replace an already-fatal navigation error. The shared
    // lifecycle also reaches runWrapper's top-level failure report.
    scenario.receipt_error=String(error.stack||error).slice(0,4096);
    if(scenario.lifecycle)scenario.lifecycle.receipt_error=scenario.receipt_error;
  }
}

export async function runWrapper({repository, site, output, browserBinary}) {
  repository = resolve(repository); site = resolve(site); output = resolve(output);
  if (!relative(join(repository, 'artifacts'), output) || relative(join(repository, 'artifacts'), output).startsWith('..')) throw Error('output must be a child of repository artifacts');
  const verifierPaths=[publicationOwnerPath,'configs/docs/publication/downloads.json',
    ...['wrapper-runtime.mjs','browser-transport.mjs','provider-failures.mjs'].map(name=>relative(repository,join(moduleDirectory,name)))];
  const revision=requireScopedCandidate(repository,verifierPaths);
  await mkdir(output,{recursive:false});
  try {await savePublicationVerification(output,await verifyPublication(repository));}
  catch(error) {if(error.verification)await savePublicationVerification(output,error.verification);throw error;}
  const authority = await readWrapperAuthority(repository, site);
  const paths = [ownerPath, authority.parent.source.path, authority.report.source.path,
    ...Object.values(authority.report.resources).map(row => row.source),
    ...verifierPaths];
  requireScopedCandidate(repository,paths,revision);
  const requests = [], serverErrors = [], externalRefusals = [], browserLog = [];
  let browser, runtime, profile, outcome, failure, atlasOwner;
  try {
    profile = await mkdtemp(join(output,'browser-profile-'));
    runtime = await launchChromium(browserBinary, profile);
    browser = runtime.browser;
    browser.stdout.on('data', value => browserLog.push(value.toString()));
    browser.stderr.on('data', value => browserLog.push(value.toString()));
    const endpoint = await debuggerEndpoint(browser, 15000);
    const debuggerOrigin = new URL(endpoint); debuggerOrigin.protocol = 'http:'; debuggerOrigin.pathname = '';
    const browserCdp = await connectCdp(endpoint);
    const browserIdentity = await browserCdp.send('Browser.getVersion'); browserCdp.close();
    const timeoutMs = 15000;
    const scope = {name:'nordic-wrapper', document:authority.parent.output};
    atlasOwner=createWrapperAtlasOwner({site,authority,debuggerOrigin,requests,serverErrors,externalRefusals,timeoutMs});
    const result = await verifyProviderFailureMatrix(scope, debuggerOrigin.origin, {
      candidate:{build_id:authority.buildId}, timeoutMs, evidenceIdentity,
      openAtlas: atlasOwner.openAtlas,
      closeAtlas: atlasOwner.closeAtlas,
      captureReady(cdp) {return evaluate(cdp, `(() => new Promise((resolve,reject)=>{const start=performance.now();const inspect=()=>{const api=globalThis.BijuxPollenomicsAtlasCapture;if(api?.version==='atlas-capture.v1')resolve(api.awaitReady());else if(performance.now()-start>${timeoutMs})reject(Error('child capture readiness timed out'));else setTimeout(inspect,25);};inspect();}))()`);},
      evaluate,
      async screenshot(cdp, path) {await mkdir(join(output,'nordic-wrapper'),{recursive:true}); const result=await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}); await writeFile(join(output,path),Buffer.from(result.data,'base64'));},
      writeScenario(_scope, scenario, receipts) {return writeWrapperScenario(output,scenario,receipts);},
    });
    requireScopedCandidate(repository,paths,revision);
    const after = await readWrapperAuthority(repository,site);
    if (JSON.stringify(after.publication) !== JSON.stringify(authority.publication)) throw Error('publication inventory changed during browser journey');
    outcome = {source_revision:revision, publication:authority.publication, parent:authority.parent, map:{output:authority.report.output,source:authority.report.source,build_id:authority.buildId,version:authority.version}, browser:browserIdentity, scenarios:result.scenarios, lifecycle:atlasOwner.lifecycle, requests, external_refusals:externalRefusals, server_errors:serverErrors,
      scope:'Production-origin Nordic docs iframe fulfilled only from local source-bound publication bytes after the owning publication verifier. No hosted website requests, HTML/CSP rewriting, scientific or human-reader qualification. Direct results are reused, not rerun.'};
    if (result.scenarios.length !== 10 || result.scenarios.some(row=>!Object.values(row.assertions).every(value=>value===true)) || serverErrors.length || externalRefusals.length) throw Error('actual wrapper matrix did not qualify');
  } catch(error) {failure=error;}
  finally {
    if (runtime) try {await runtime.close();} catch(error) {failure ??= error; outcome=null;}
    if (profile) await rm(profile,{recursive:true,force:true});
    await writeFile(join(output,'browser.log'),browserLog.join(''));
    await writeFile(join(output,'report.json'),JSON.stringify(outcome ?? {error:String(failure),lifecycle:atlasOwner?.lifecycle??[],requests,server_errors:serverErrors},null,2)+'\n');
  }
  if(failure) throw failure;
  return outcome;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv.length !== 6) throw Error('usage: node wrapper-runtime.mjs REPOSITORY SITE OUTPUT BROWSER');
  await runWrapper({repository:process.argv[2],site:process.argv[3],output:process.argv[4],browserBinary:process.argv[5]});
}
