// 通用资源接口探测：打开 URL，收集所有返回 JSON 的 XHR/fetch 响应，
// 保存正文到 /tmp/detect_<n>.json，并输出候选接口 URL。
// 用法: node detect.mjs <url> [waitMs]
import fs from 'fs';
const BASE = 'http://127.0.0.1:9222';
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function jlist(){ return (await fetch(BASE+'/json')).json(); }
async function wsUrlFor(id){ const l=await jlist(); return l.find(x=>x.id===id).webSocketDebuggerUrl; }
function connect(ws){ return new Promise((res,rej)=>{const w=new WebSocket(ws); w.onopen=()=>res(w); w.onerror=e=>rej(e);}); }
let _id=0; function cmd(ws,method,params={}){ const i=++_id; return new Promise((res,rej)=>{ const on=m=>{const d=JSON.parse(m.data); if(d.id===i){ws.removeEventListener('message',on); if(d.error)rej(new Error(method+JSON.stringify(d.error))); else res(d.result);}}; ws.addEventListener('message',on); ws.send(JSON.stringify({id:i,method,params}));}); }

(async()=>{
  const url = process.argv[2];
  const wait = parseInt(process.argv[3]||'8000',10);
  if(!url){ console.error('usage: node detect.mjs <url> [waitMs]'); process.exit(1); }
  // 开新标签
  let r = await fetch(BASE+'/json/new?'+encodeURIComponent(url),{method:'PUT'});
  if(!r.ok) r = await fetch(BASE+'/json/new?'+encodeURIComponent(url));
  const id = (await r.json()).id;
  const ws = await connect(await wsUrlFor(id));
  await cmd(ws,'Runtime.enable'); await cmd(ws,'Network.enable');
  const reqs = {}; // requestId -> {url, method}
  const cand = [];
  ws.addEventListener('message', ev=>{
    const m = JSON.parse(ev.data);
    if(m.method==='Network.requestWillBeSent'){
      const rq=m.params.request; reqs[m.params.requestId]={url:rq.url,method:rq.method,postData:rq.postData};
    } else if(m.method==='Network.responseReceived'){
      const info=reqs[m.params.requestId]; if(!info) return;
      const ct=m.params.response.headers?m.params.response.headers['content-type']||m.params.response.headers['Content-Type']||'':'';
      if(/json/i.test(ct) || /\bapi\b|list|pageList|navigation|resource|database|db/i.test(info.url)){
        cand.push({rid:m.params.requestId, url:info.url, method:info.method, ct});
      }
    }
  });
  await new Promise(r=>setTimeout(r, wait));
  // 逐个抓响应体
  let n=0; const found=[];
  for(const c of cand){
    try{
      const b = await cmd(ws,'Network.getResponseBody',{requestId:c.rid});
      const body = b.result.base64Encoded ? Buffer.from(b.result.body,'base64').toString('utf8') : b.result.body;
      if(!body) continue;
      let parsed=null; try{ parsed=JSON.parse(body); }catch(e){}
      // 启发式：数组长度大 或 含 name/title/数据库/资源 的数组，视为资源列表
      const arr = parsed && (Array.isArray(parsed) ? parsed : (parsed.data&&Array.isArray(parsed.data)?parsed.data:(parsed.result&&Array.isArray(parsed.result)?parsed.result:(parsed.list&&Array.isArray(parsed.list)?parsed.list:null))));
      const isResList = arr && arr.length>=3 && arr.some(x=>x && typeof x==='object' && (x.name||x.title||x.dbName||x.resourceName||x.db_name));
      const fn = `/tmp/detect_${n}.json`;
      fs.writeFileSync(fn, body||'');
      found.push({n, url:c.url, method:c.method, len:(body||'').length, arrLen: arr?arr.length:'-', isResList:!!isResList});
      n++;
    }catch(e){}
  }
  console.log(JSON.stringify(found, null, 1));
  await fetch(BASE+'/json/close/'+id);
  process.exit(0);
})().catch(e=>{console.error('FATAL',e.message);process.exit(1);});
