import {createServer} from 'node:http';
import {createHash} from 'node:crypto';
import {readFile, writeFile, realpath, stat, mkdtemp, rm} from 'node:fs/promises';
import {join, resolve, sep, extname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {connectCdp, debuggerEndpoint, evaluate, launchChromium} from '../atlas_browser/browser-transport.mjs';

const prefix = '/bijux-pollenomics/';
const limit = 16 * 1024 * 1024;
const mime = {'.html':'text/html', '.js':'text/javascript', '.mjs':'text/javascript', '.css':'text/css', '.json':'application/json', '.csv':'text/csv', '.pdf':'application/pdf', '.svg':'image/svg+xml', '.png':'image/png', '.ico':'image/x-icon', '.woff2':'font/woff2'};

export function relativePath(requestUrl) {
  const path = decodeURIComponent(new URL(requestUrl, 'http://localhost').pathname);
  if (!path.startsWith(prefix) || path.includes('\\') || path.includes('\0')) throw Error('request escaped production prefix');
  const relative = path.slice(prefix.length);
  if (relative.split('/').some(part => part === '..' || part === '.')) throw Error('request escaped site directory');
  return relative.endsWith('/') || relative === '' ? relative + 'index.html' : relative;
}

export function readerLayoutReady() {
  const article = document.querySelector('article');
  return document.readyState === 'complete' && document.fonts.status === 'loaded' && !!article &&
    [...article.querySelectorAll('table:not([class])')]
      .every(table => table.closest('.md-typeset__scrollwrap'));
}

async function main(planPath) {
  const started = Date.now();
  const plan = JSON.parse(await readFile(planPath, 'utf8'));
  const site = await realpath(plan.site_directory);
  const output = plan.output_directory;
  const receipt = {status:'FAIL', candidate:plan.candidate, errors:[], viewports:[], responses:[], served:[]};
  let browser, cdp, server, runtime, profile, timer, origin;
  const browserLogs = [];
  let logBytes = 0;
  const fail = (message) => { if (receipt.errors.length < 1000) receipt.errors.push(message); };
  const browserLog = (chunk) => {
    logBytes += chunk.length;
    if (logBytes <= limit) browserLogs.push(chunk);
    else { fail('browser log exceeds 16 MiB'); browser?.kill('SIGTERM'); }
  };
  const waitFor = async (expression, description) => {
    const deadline = Date.now() + 15000;
    while (Date.now() < deadline) {
      if (await evaluate(cdp, expression)) return;
      await new Promise(accept => setTimeout(accept, 50));
    }
    throw Error(`${description} did not become ready`);
  };
  const settleLayout = async () => {
    // Instant navigation exposes headings before Material wraps Markdown tables.
    await waitFor(`(${readerLayoutReady.toString()})()`, 'reader layout');
    await evaluate(cdp, 'new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))');
  };
  const navigate = async (path) => {
    const loaded = cdp.waitFor('Page.loadEventFired', 15000);
    await cdp.send('Page.navigate', {url:origin + prefix + path});
    await loaded;
    await waitFor("document.readyState === 'complete' && !!document.querySelector('main h1')", 'reader page');
    await settleLayout();
  };
  const pathExpression = (path) => JSON.stringify(prefix + path);
  try {
    const publicationRaw = await readFile(plan.publication_manifest_path);
    if(publicationRaw.length!==plan.publication_manifest.bytes || createHash('sha256').update(publicationRaw).digest('hex')!==plan.publication_manifest.sha256) throw Error('publication manifest changed');
    const publication=JSON.parse(publicationRaw);
    const qualified=new Map(publication.files.map(row=>[row.path,row]));
    server = createServer(async (request, response) => {
      try {
        const relative = relativePath(request.url);
        const file = await realpath(join(site, relative));
        if (!file.startsWith(site + sep)) throw Error('request escaped admitted site');
        const info = await stat(file);
        if (!info.isFile() || info.size > limit) throw Error('served resource missing or oversized');
        const content=await readFile(file);
        const sha256=createHash('sha256').update(content).digest('hex');
        const admitted=qualified.get(relative);
        if(!admitted || admitted.bytes!==content.length || admitted.sha256!==sha256) throw Error('served bytes differ from qualified publication');
        receipt.served.push({path:relative,bytes:content.length,sha256});
        if(receipt.served.length>5000) throw Error('served response budget exceeded');
        response.writeHead(200, {'Content-Type':mime[extname(file)] || 'application/octet-stream', 'Cache-Control':'no-store'});
        response.end(content);
      } catch (error) {
        fail(`resource ${request.url}: ${error.message}`);
        response.writeHead(404); response.end('Unavailable admitted resource');
      }
    });
    await new Promise(accept => server.listen(0, '127.0.0.1', accept));
    origin = `http://127.0.0.1:${server.address().port}`;
    receipt.local_origin = origin;
    profile = await mkdtemp(join(output,'browser-profile-'));
    runtime = await launchChromium(plan.browser_binary, profile);
    browser = runtime.browser;
    browser.stdout.on('data', browserLog); browser.stderr.on('data', browserLog);
    const endpoint = new URL(await debuggerEndpoint(browser, 15000));
    const target = await (await fetch(`http://${endpoint.host}/json/new?about:blank`, {method:'PUT'})).json();
    cdp = await connectCdp(target.webSocketDebuggerUrl);
    receipt.browser = await cdp.send('Browser.getVersion');
    cdp.onEvent(event => {
      if (event.method === 'Runtime.exceptionThrown') fail(`page exception: ${JSON.stringify(event.params.exceptionDetails)}`);
      if (event.method === 'Runtime.consoleAPICalled' && event.params.type === 'error') fail(`console error: ${JSON.stringify(event.params.args)}`);
      if (event.method === 'Log.entryAdded' && event.params.entry.level === 'error') fail(`browser log error: ${event.params.entry.text}`);
      if (event.method === 'Network.loadingFailed') fail(`network failure: ${event.params.errorText}`);
      if (event.method === 'Network.responseReceived') {
        const reply = event.params.response;
        receipt.responses.push({url:reply.url, status:reply.status});
        if (receipt.responses.length > 5000) { fail('resource response budget exceeded'); browser.kill('SIGTERM'); }
        if (reply.status >= 400) fail(`HTTP ${reply.status}: ${reply.url}`);
      }
      if (event.method === 'Fetch.requestPaused') {
        const url = new URL(event.params.request.url);
        if (url.origin !== origin || !url.pathname.startsWith(prefix)) {
          fail(`resource escaped local production prefix: ${url.href}`);
          void cdp.send('Fetch.failRequest', {requestId:event.params.requestId, errorReason:'BlockedByClient'});
        } else void cdp.send('Fetch.continueRequest', {requestId:event.params.requestId});
      }
    });
    for (const method of ['Page.enable','Runtime.enable','Network.enable','Log.enable']) await cdp.send(method);
    await cdp.send('Fetch.enable', {patterns:[{urlPattern:'http*', requestStage:'Request'}]});
    const work = async () => {
      for (const width of [1440, 390]) {
        await cdp.send('Emulation.setDeviceMetricsOverride', {width, height:900, deviceScaleFactor:1, mobile:false});
        await navigate(plan.entry);
        const viewport = {width, entry:plan.entry, entry_heading:await evaluate(cdp, "document.querySelector('main h1').textContent.trim()"), entry_overflow:await evaluate(cdp, 'document.documentElement.scrollWidth > innerWidth + 1'), routes:[], downloads:[]};
        if(viewport.entry_overflow) throw Error('scientific entry overflows viewport');
        receipt.viewports.push(viewport);
        for (const path of plan.routes) {
          await navigate(plan.entry);
          const position = await evaluate(cdp, `(() => {
            const links=[...document.querySelectorAll('article a[href]')].filter(a => new URL(a.href).origin === location.origin && new URL(a.href).pathname === ${pathExpression(path)});
            if(links.length !== 1) throw Error('missing or ambiguous rendered reader link');
            const link=links[0]; link.scrollIntoView({block:'center'});
            const rect=[...link.getClientRects()].find(box=>box.width>0&&box.height>0&&link.contains(document.elementFromPoint(box.left+box.width/2,box.top+box.height/2)));
            if(!rect) throw Error('reader link cannot be clicked');
            return {x:rect.left+rect.width/2,y:rect.top+rect.height/2};
          })()`);
          await cdp.send('Input.dispatchMouseEvent', {type:'mousePressed', ...position, button:'left', clickCount:1});
          await cdp.send('Input.dispatchMouseEvent', {type:'mouseReleased', ...position, button:'left', clickCount:1});
          await waitFor(`location.pathname === ${pathExpression(path)} && document.querySelector('main h1')?.textContent.trim() !== ${JSON.stringify(viewport.entry_heading)}`, 'clicked reader route');
          await settleLayout();
          const observed = await evaluate(cdp, `({heading:document.querySelector('main h1')?.textContent.trim(), overflow:document.documentElement.scrollWidth > innerWidth + 1, url:location.href})`);
          viewport.routes.push({path, clicked:true, ...observed});
          if (!observed.heading || observed.overflow) throw Error(`unusable reader route ${path}`);
        }
        for (const page of [...new Set(plan.downloads.map(row => row.page))]) {
          await navigate(page);
          for (const record of plan.downloads.filter(row => row.page === page)) {
            const observed = await evaluate(cdp, `(async () => {
              const links=[...document.querySelectorAll('article a[href]')].filter(a => new URL(a.href).origin===location.origin && new URL(a.href).pathname === ${pathExpression(record.path)});
              if(links.length !== 1) throw Error('missing or ambiguous rendered download link');
              const link=links[0];link.scrollIntoView({block:'center'});
              if(![...link.getClientRects()].some(box=>box.width>0&&box.height>0&&link.contains(document.elementFromPoint(box.left+box.width/2,box.top+box.height/2)))) throw Error('download anchor is not clickable');
              const response=await fetch(link.href,{cache:'no-store',credentials:'omit',redirect:'error'});
              const bytes=await response.arrayBuffer();
              if(bytes.byteLength>${limit}) throw Error('download response budget exceeded');
              const sha256=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
              return {status:response.status,bytes:bytes.byteLength,sha256,url:response.url,from_rendered_anchor:true,clickable:true};
            })()`);
            if (observed.status !== 200 || observed.bytes !== record.bytes || observed.sha256 !== record.sha256 || new URL(observed.url).pathname !== prefix + record.path) throw Error(`download identity differs: ${record.path}`);
            viewport.downloads.push({path:record.path, ...observed});
          }
        }
      }
      if (receipt.errors.length) throw Error('page, console or resource failures observed');
      receipt.status = 'PASS';
    };
    await Promise.race([work(), new Promise((_, reject) => {timer=setTimeout(() => reject(Error('browser work deadline reached')),Math.max(1,165000-(Date.now()-started)));})]);
  } catch (error) {
    fail(error.stack || error.message);
    if (cdp) try {
      receipt.failure_layout = await evaluate(cdp, `({url:location.href, width:innerWidth,
        scroll_width:document.documentElement.scrollWidth, fonts:document.fonts?.status,
        heading:document.querySelector('main h1')?.textContent.trim(),
        unwrapped_tables:[...document.querySelectorAll('article table:not([class])')]
          .filter(table => !table.closest('.md-typeset__scrollwrap')).length})`);
    } catch {}
  }
  finally {
    clearTimeout(timer);
    if (cdp) { try { await Promise.race([cdp.send('Browser.close'),new Promise(accept => setTimeout(accept,1000))]); } catch {} cdp.close(); }
    if (runtime) try {await runtime.close();} catch(error) {receipt.status='FAIL';fail(`Chromium cleanup failed: ${error}`);}
    if (profile) await rm(profile,{recursive:true,force:true});
    if (server) {server.closeAllConnections(); await new Promise(accept => server.close(accept));}
    let serialized=JSON.stringify(receipt,null,2)+'\n';
    if(Buffer.byteLength(serialized)+Math.min(logBytes,limit)>limit) {
      receipt.status='FAIL'; fail('combined browser receipt/log exceeds 16 MiB');
      serialized=JSON.stringify(receipt,null,2)+'\n';
    }
    if(Buffer.byteLength(serialized)>limit) serialized=JSON.stringify({status:'FAIL',candidate:plan.candidate,errors:['browser receipt exceeds 16 MiB']})+'\n';
    await writeFile(join(output,'browser.json'),serialized);
    await writeFile(join(output,'browser.log'),Buffer.concat(browserLogs).subarray(0,Math.max(0,limit-Buffer.byteLength(serialized))));
  }
  if(receipt.status !== 'PASS') process.exitCode=1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main(process.argv[2]);
