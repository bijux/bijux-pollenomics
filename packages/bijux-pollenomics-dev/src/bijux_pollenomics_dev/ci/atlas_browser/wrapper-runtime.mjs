// Qualify the actual docs iframe separately from direct-map and current-loader contracts.
import {execFileSync, spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {createServer} from 'node:http';
import {mkdir, mkdtemp, readFile, realpath, rm, writeFile} from 'node:fs/promises';
import {extname, join, relative, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {connectCdp, debuggerEndpoint, evaluate} from './browser-transport.mjs';
import {providerInterception, verifyProviderFailureMatrix} from './provider-failures.mjs';

const moduleDirectory = fileURLToPath(new URL('.', import.meta.url));
const ownerPath = 'configs/docs/maps/report-owner.json';
export const parentOutput = 'public/nordic-atlas/index.html';
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const git = (repository, ...args) => execFileSync('git', args, {cwd: repository, encoding: 'utf8'}).trim();

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
  const owner = JSON.parse(await readFile(join(repository, ownerPath), 'utf8'));
  const parents = owner.parents.filter(row => row.output === parentOutput);
  if (parents.length !== 1 || parents[0].reports.length !== 1) throw Error('Nordic wrapper authority is ambiguous');
  const parent = parents[0];
  const reports = owner.reports.filter(row => row.output === parent.reports[0]);
  if (reports.length !== 1) throw Error('Nordic child authority is ambiguous');
  const report = reports[0];
  const html = await readFile(join(site, parent.output));
  if (digest(html) !== parent.built_html_sha256) throw Error('built wrapper differs from approved parent');
  if (digest(await readFile(join(repository, parent.source.path))) !== parent.source.sha256) throw Error('wrapper source differs from approved parent');
  const expected = new Map([[parent.output, parent.built_html_sha256], [report.output, report.source.sha256],
    ...Object.entries(report.resources).map(([path, row]) => [path, row.sha256])]);
  if (digest(await readFile(join(site, report.output))) !== report.source.sha256
      || digest(await readFile(join(repository, report.source.path))) !== report.source.sha256) throw Error('built child differs from canonical map');
  const iframe = [...html.toString().matchAll(/<iframe\b[^>]*\bsrc="([^"]+)"/g)];
  if (iframe.length !== 1 || new URL(iframe[0][1], `http://localhost/${parent.output}`).pathname !== `/${report.output}`) throw Error('real wrapper iframe target differs');
  const match = (await readFile(join(site, report.output), 'utf8')).match(/<script[^>]*id="atlas-static-bootstrap"[^>]*>([\s\S]*?)<\/script>/);
  if (!match) throw Error('child scientific bootstrap is unavailable');
  const bootstrap = JSON.parse(match[1]);
  return {parent, report, expected, buildId: bootstrap.build_id, version: bootstrap.version};
}

export async function readSiteMember(site, pathname, expected) {
  const root = await realpath(site);
  const path = await realpath(resolve(root, `.${decodeURIComponent(pathname)}`));
  if (relative(root, path).startsWith('..')) throw Error('site request escapes root');
  const bytes = await readFile(path), key = relative(root, path);
  if (expected.has(key) && digest(bytes) !== expected.get(key)) throw Error(`owned site member differs: ${key}`);
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

export async function runWrapper({repository, site, output, browserBinary}) {
  repository = resolve(repository); site = resolve(site); output = resolve(output);
  if (!relative(join(repository, 'artifacts'), output) || relative(join(repository, 'artifacts'), output).startsWith('..')) throw Error('output must be a child of repository artifacts');
  const authority = await readWrapperAuthority(repository, site);
  const paths = [ownerPath, authority.parent.source.path, authority.report.source.path,
    ...Object.values(authority.report.resources).map(row => row.source),
    ...['wrapper-runtime.mjs', 'browser-transport.mjs', 'provider-failures.mjs'].map(name => relative(repository, join(moduleDirectory, name)))];
  const revision = requireScopedCandidate(repository, paths);
  await mkdir(output, {recursive: false});
  const requests = [], serverErrors = [], externalRefusals = [], browserLog = [];
  const server = createServer(async (request, response) => {
    try {
      const pathname = new URL(request.url, 'http://localhost').pathname;
      const {bytes, path} = await readSiteMember(site, pathname, authority.expected);
      requests.push({path: pathname, status: 200, bytes: bytes.length});
      response.writeHead(200, {'Cache-Control': 'no-store', 'Content-Type': ({'.html':'text/html', '.js':'text/javascript', '.css':'text/css', '.json':'application/json', '.png':'image/png', '.svg':'image/svg+xml', '.woff2':'font/woff2'})[extname(path)] ?? 'application/octet-stream'}).end(bytes);
    } catch (error) {
      serverErrors.push({path: request.url, error: String(error)});
      response.writeHead(404).end('not found');
    }
  });
  let browser, closed, profile, outcome, failure;
  try {
    await new Promise((accept, reject) => {server.once('error', reject); server.listen(0, '127.0.0.1', accept);});
    const origin = `http://127.0.0.1:${server.address().port}`;
    profile = await mkdtemp(join(output, 'browser-profile-'));
    browser = spawn(browserBinary, ['--headless=new', '--disable-gpu', '--disable-background-networking', '--disable-component-update', '--disable-default-apps', '--no-default-browser-check', '--no-first-run', '--remote-allow-origins=*', '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], {stdio:['ignore','pipe','pipe']});
    closed = new Promise(accept => browser.once('close', (code, signal) => accept({code, signal})));
    browser.stdout.on('data', value => browserLog.push(value.toString()));
    browser.stderr.on('data', value => browserLog.push(value.toString()));
    const endpoint = await debuggerEndpoint(browser, 15000);
    const debuggerOrigin = new URL(endpoint); debuggerOrigin.protocol = 'http:'; debuggerOrigin.pathname = '';
    const browserCdp = await connectCdp(endpoint);
    const browserIdentity = await browserCdp.send('Browser.getVersion'); browserCdp.close();
    const timeoutMs = 15000;
    const scope = {name:'nordic-wrapper', document:authority.parent.output};
    const result = await verifyProviderFailureMatrix(scope, debuggerOrigin.origin, {
      candidate:{build_id:authority.buildId}, timeoutMs, evidenceIdentity,
      async openAtlas(_scope, _debuggerOrigin, options) {
        const response = await fetch(`${debuggerOrigin.origin}/json/new?about:blank`, {method:'PUT'});
        if (!response.ok) throw Error(`owned target creation failed: ${response.status}`);
        const target = await response.json(), raw = await connectCdp(target.webSocketDebuggerUrl);
        const runtimeFailures = [], providerRequests = [], contexts = new Map(), localReplies = new Set();
        const interception = providerInterception(raw, providerRequests, runtimeFailures, true, options.providerFailure);
        raw.onEvent(event => {
          if (event.method === 'Runtime.executionContextCreated' && event.params.context.auxData?.isDefault) contexts.set(event.params.context.auxData.frameId, event.params.context.id);
          if (event.method === 'Runtime.exceptionThrown') runtimeFailures.push({kind:'exception', detail:event.params.exceptionDetails?.text ?? ''});
          if (event.method === 'Runtime.consoleAPICalled' && event.params.type === 'error') runtimeFailures.push({kind:'console-error', detail:event.params.args.map(row => row.description ?? row.value ?? '').join(' ')});
          const url = event.params?.request?.url;
          const provider = url && ['tile.openstreetmap.org','tile.opentopomap.org'].includes(new URL(url).hostname);
          if (event.method !== 'Fetch.requestPaused' || provider) interception.handle(event);
          if (event.method === 'Fetch.requestPaused' && !provider) {
            const local = new URL(url).origin === origin;
            if (!local) externalRefusals.push(url);
            const task = raw.send(local ? 'Fetch.continueRequest' : 'Fetch.failRequest', {requestId:event.params.requestId, ...(!local ? {errorReason:'BlockedByClient'} : {})}).catch(error => runtimeFailures.push({kind:'request-reply', detail:String(error)})).finally(() => localReplies.delete(task));
            localReplies.add(task);
          }
          if (event.method === 'Network.requestWillBeSent' && provider) providerRequests.push({url,request_id:event.params.requestId,...(interception.requestsBlocked ? {blocked_during_teardown:true} : {})});
        });
        for (const domain of ['Page','Runtime','Network']) await raw.send(`${domain}.enable`);
        await raw.send('Network.setCacheDisabled',{cacheDisabled:true});
        await raw.send('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
        await raw.send('Fetch.enable',{patterns:[{urlPattern:'http*',requestStage:'Request'}]});
        // Controlled reader input before child bootstrap; neither HTML file changes.
        await raw.send('Page.addScriptToEvaluateOnNewDocument',{source:`if(location.pathname===${JSON.stringify('/'+authority.report.output)})history.replaceState(null,'',${JSON.stringify(options.hash)});`});
        const loaded = raw.waitFor('Page.loadEventFired',timeoutMs);
        await raw.send('Page.navigate',{url:`${origin}/${authority.parent.output}`}); await loaded;
        const tree = (await raw.send('Page.getFrameTree')).frameTree;
        const child = (tree.childFrames ?? []).find(row => new URL(row.frame.url).pathname === '/'+authority.report.output);
        if (!child || !contexts.has(child.frame.id)) throw Error('real child execution context is unavailable');
        const contextId = contexts.get(child.frame.id);
        await evaluate(raw, `document.querySelector('iframe').scrollIntoView({block:'center'})`);
        const cdp = childRuntime(raw,contextId), parentBefore=await wrapperFacts(raw);
        if(!parentBefore.title||!parentBefore.iframe_visible||!parentBefore.navigation_available)throw Error('real docs wrapper is not visibly usable');
        return {cdp,raw,target,runtimeFailures,providerRequests,interception,localReplies,parentBefore};
      },
      async closeAtlas(atlas) {
        try {
          const parentAfter=await wrapperFacts(atlas.raw);
          if(JSON.stringify(parentAfter)!==JSON.stringify(atlas.parentBefore))atlas.runtimeFailures.push({kind:'wrapper-state',detail:'parent title/navigation/iframe changed during child journey'});
          await atlas.interception.settle(async () => {
          await Promise.all(atlas.localReplies);
          const response = await fetch(`${debuggerOrigin.origin}/json/close/${atlas.target.id}`);
          if (!response.ok) throw Error(`owned target close failed: ${response.status}`); await response.text();
        });} finally {atlas.cdp.close();}
      },
      captureReady(cdp) {return evaluate(cdp, `(() => new Promise((resolve,reject)=>{const start=performance.now();const inspect=()=>{const api=globalThis.BijuxPollenomicsAtlasCapture;if(api?.version==='atlas-capture.v1')resolve(api.awaitReady());else if(performance.now()-start>${timeoutMs})reject(Error('child capture readiness timed out'));else setTimeout(inspect,25);};inspect();}))()`);},
      evaluate,
      async screenshot(cdp, path) {await mkdir(join(output,'nordic-wrapper'),{recursive:true}); const result=await cdp.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false}); await writeFile(join(output,path),Buffer.from(result.data,'base64'));},
      async writeScenario(_scope, scenario, receipts) {const path=`nordic-wrapper/${scenario.name}.json`; await writeFile(join(output,path),JSON.stringify(scenario,null,2)+'\n'); receipts.push(path);},
    });
    requireScopedCandidate(repository,paths,revision);
    await readWrapperAuthority(repository,site);
    outcome = {source_revision:revision, parent:authority.parent, map:{output:authority.report.output,source:authority.report.source,build_id:authority.buildId,version:authority.version}, browser:browserIdentity, scenarios:result.scenarios, requests, external_refusals:externalRefusals, server_errors:serverErrors,
      scope:'Local retained Nordic docs iframe only; separate current-loader contract. Direct results are reused, not rerun. No hosted or release qualification.'};
    if (result.scenarios.length !== 10 || result.scenarios.some(row=>!Object.values(row.assertions).every(value=>value===true)) || serverErrors.length || externalRefusals.length) throw Error('actual wrapper matrix did not qualify');
  } catch(error) {failure=error;}
  finally {
    if (browser && browser.exitCode === null && browser.signalCode === null) browser.kill('SIGTERM');
    if (closed) {
      let timer; const stopped=await Promise.race([closed.then(()=>true),new Promise(accept=>{timer=setTimeout(()=>accept(false),5000);})]); clearTimeout(timer);
      if (!stopped) {browser.kill('SIGKILL'); await closed;}
    }
    await new Promise((accept,reject)=>server.close(error=>error?reject(error):accept()));
    if (profile) await rm(profile,{recursive:true,force:true});
    await writeFile(join(output,'browser.log'),browserLog.join(''));
    await writeFile(join(output,'report.json'),JSON.stringify(outcome ?? {error:String(failure),requests,server_errors:serverErrors},null,2)+'\n');
  }
  if(failure) throw failure;
  return outcome;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv.length !== 6) throw Error('usage: node wrapper-runtime.mjs REPOSITORY SITE OUTPUT BROWSER');
  await runWrapper({repository:process.argv[2],site:process.argv[3],output:process.argv[4],browserBinary:process.argv[5]});
}
