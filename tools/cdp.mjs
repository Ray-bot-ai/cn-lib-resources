// 极简 CDP 客户端，绕开 web-access 代理，直连 Chrome DevTools。
// 用法:
//   node cdp.mjs new <url>            -> 新建标签页并导航，打印 targetId
//   node cdp.mjs nav <id> <url>       -> 在已有标签页导航
//   node cdp.mjs eval <id> <jsExpr>   -> 在标签页执行JS，打印返回值(JSON)
//   node cdp.mjs close <id>           -> 关闭标签页
const BASE = 'http://127.0.0.1:9222';

async function jlist() { return (await fetch(BASE + '/json')).json(); }

async function wsUrlFor(id) {
  const list = await jlist();
  const t = list.find(x => x.id === id);
  if (!t) throw new Error('target not found: ' + id);
  return t.webSocketDebuggerUrl;
}

function connect(wsUrl) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => resolve(ws);
    ws.onerror = (e) => reject(new Error('ws error: ' + (e.message || e)));
  });
}

let _id = 0;
function cmd(ws, method, params = {}) {
  const id = ++_id;
  return new Promise((resolve, reject) => {
    const onMsg = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id === id) {
        ws.removeEventListener('message', onMsg);
        if (m.error) reject(new Error(method + ': ' + JSON.stringify(m.error)));
        else resolve(m.result);
      }
    };
    ws.addEventListener('message', onMsg);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function main() {
  const [op, a, ...rest] = process.argv.slice(2);

  if (op === 'new') {
    const url = a;
    // Chrome 150 需要 PUT 创建标签页
    let r = await fetch(BASE + '/json/new?' + encodeURIComponent(url), { method: 'PUT' });
    if (!r.ok) r = await fetch(BASE + '/json/new?' + encodeURIComponent(url));
    const t = await r.json();
    console.log(t.id);
    return;
  }
  if (op === 'close') {
    await fetch(BASE + '/json/close/' + a);
    console.log('closed');
    return;
  }

  const ws = await connect(await wsUrlFor(a));
  await cmd(ws, 'Runtime.enable');
  await cmd(ws, 'Page.enable');

  if (op === 'nav') {
    await cmd(ws, 'Page.navigate', { url: rest.join(' ') });
    await sleep(500);
    console.log('navigated');
  } else if (op === 'eval') {
    const expr = rest.join(' ');
    const r = await cmd(ws, 'Runtime.evaluate', {
      expression: expr,
      returnByValue: true,
      awaitPromise: true,
    });
    if (r.exceptionDetails) {
      console.error('JS EXCEPTION:', JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails));
      process.exit(2);
    }
    const v = r.result.value;
    console.log(typeof v === 'string' ? v : JSON.stringify(v));
  }
  ws.close();
}

main().catch(e => { console.error('ERR', e.message); process.exit(1); });
