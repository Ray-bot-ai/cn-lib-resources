// 抓取某标签页里匹配 urlPattern 的网络请求(方法/请求体)与响应体。
// 用法: node capture.mjs <targetId> <urlSubstr> <reloadUrl?>
const BASE = 'http://127.0.0.1:9222';
const [id, pat, reloadUrl] = process.argv.slice(2);

async function wsUrlFor(id){const l=await (await fetch(BASE+'/json')).json();const t=l.find(x=>x.id===id);return t.webSocketDebuggerUrl;}
const WSURL = await wsUrlFor(id);
const ws = await new Promise((res,rej)=>{const w=new WebSocket(WSURL);w.onopen=()=>res(w);w.onerror=e=>rej(e);});
let _id=0; const pend=new Map();
ws.addEventListener('message',ev=>{const m=JSON.parse(ev.data);if(m.id&&pend.has(m.id)){pend.get(m.id)(m);pend.delete(m.id);}else if(m.method) onEvent(m);});
function cmd(method,params={}){const i=++_id;return new Promise(r=>{pend.set(i,r);ws.send(JSON.stringify({id:i,method,params}));});}

const reqs={}; // requestId -> {url,method,postData}
const matches=[];
function onEvent(m){
  if(m.method==='Network.requestWillBeSent'){
    const r=m.params.request; reqs[m.params.requestId]={url:r.url,method:r.method,postData:r.postData,headers:r.headers};
  }
  if(m.method==='Network.responseReceived'){
    const info=reqs[m.params.requestId];
    if(info && info.url.includes(pat)) info._rid=m.params.requestId, matches.push({rid:m.params.requestId,...info});
  }
}
await cmd('Network.enable');
if(reloadUrl) await cmd('Page.navigate',{url:reloadUrl}); else await cmd('Page.reload');
await new Promise(r=>setTimeout(r,7000));
for(const mm of matches){
  try{ const body=await cmd('Network.getResponseBody',{requestId:mm.rid});
    console.log('=== '+mm.method+' '+mm.url);
    if(mm.postData) console.log('REQ_BODY: '+mm.postData);
    console.log('REQ_HEADERS: '+JSON.stringify(mm.headers));
    const b=body.result.body; console.log('RESP_LEN='+ (b?b.length:0));
    const fs=await import('fs'); const fn='resp_'+mm.rid.replace(/[^0-9]/g,'')+'.json'; fs.writeFileSync(fn,b||''); console.log('SAVED: '+fn);
  }catch(e){ console.log('bodyErr',mm.url,e.message); }
}
if(!matches.length) console.log('NO MATCH for '+pat);
ws.close();
