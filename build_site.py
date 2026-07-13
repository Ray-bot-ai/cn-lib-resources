#!/usr/bin/env python3
"""读取 data/ 下的数据，生成自包含的 site/index.html（双击即可打开）。
只用标准库。用法： uv run build_site.py   （或 python3 build_site.py）
"""
import json
import glob
import os
import html

ROOT = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(ROOT, "data", "libraries")
RES_FILE = os.path.join(ROOT, "data", "resources.json")
OUT = os.path.join(ROOT, "docs", "index.html")  # docs/ 供 GitHub Pages 发布，也可本地双击


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def strip_notes(d):
    """去掉以下划线开头的说明键，它们只是给人看的注释。"""
    if isinstance(d, dict):
        return {k: strip_notes(v) for k, v in d.items() if not str(k).startswith("_")}
    if isinstance(d, list):
        return [strip_notes(x) for x in d]
    return d


def main():
    resources = strip_notes(load_json(RES_FILE))

    libraries = []
    for path in sorted(glob.glob(os.path.join(LIB_DIR, "*.json"))):
        if os.path.basename(path).startswith("_"):
            continue  # 跳过 _template.json 等模板/示例文件
        libraries.append(strip_notes(load_json(path)))

    data = {"resources": resources, "libraries": libraries}
    payload = json.dumps(data, ensure_ascii=False)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.replace("/*__DATA__*/", payload))

    n_res = len([k for k in resources])
    n_lib = len(libraries)
    print(f"已生成 {OUT}")
    print(f"  资源 {n_res} 个 · 图书馆 {n_lib} 个")


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>公立图书馆免费电子资源清单 · Free E-Resources of Chinese Public Libraries</title>
<style>
  :root{
    --bg:#f4efe3; --paper:#faf6ec; --ink:#2a251f; --sub:#8b8070; --faint:#a99f8c;
    --line:#e2d9c7; --hair:#d3c9b4; --seal:#9d2b23; --sage:#556b4d; --brick:#98452f; --gold:#8a5f22;
    --serif:'Hoefler Text','Baskerville','Songti SC','STSong','Source Han Serif SC','Noto Serif SC',serif;
    --sans:-apple-system,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;
  }
  @media (prefers-color-scheme: dark){
    :root{ --bg:#191510; --paper:#201b15; --ink:#ece3d3; --sub:#9a8f7b; --faint:#6d6250;
      --line:#332c22; --hair:#3f382c; --seal:#cf7061; --sage:#93ac84; --brick:#c98a72; --gold:#c3a161; }
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{margin:0; background:var(--bg); color:var(--ink); font-family:var(--sans);
    line-height:1.65; -webkit-font-smoothing:antialiased;
    background-image:radial-gradient(120% 80% at 50% -10%, rgba(157,43,35,.035), transparent 60%);}
  a{color:var(--seal); text-decoration:none;}
  a:hover{text-decoration:underline; text-underline-offset:2px;}

  /* 报头 */
  .masthead{max-width:820px; margin:0 auto; padding:46px 22px 6px; text-align:center;}
  .kicker{font-size:11.5px; letter-spacing:.42em; color:var(--seal); text-transform:none; margin-bottom:14px; padding-left:.42em;}
  .masthead h1{font-family:var(--serif); font-weight:600; font-size:33px; letter-spacing:.05em; margin:0; color:var(--ink);}
  .masthead .en{font-family:var(--serif); font-style:italic; font-size:15px; color:var(--sub); margin-top:7px; letter-spacing:.02em;}
  .rule{display:flex; align-items:center; justify-content:center; gap:12px; margin:16px 0 8px;}
  .rule::before,.rule::after{content:""; height:1px; width:64px; background:var(--hair);}
  .rule i{width:5px; height:5px; background:var(--seal); transform:rotate(45deg); display:inline-block;}
  .stat{font-family:var(--serif); font-size:13px; color:var(--sub); letter-spacing:.03em;}

  /* 控制条（粘顶） */
  .bar{position:sticky; top:0; z-index:20; background:color-mix(in srgb, var(--bg) 88%, transparent);
    backdrop-filter:blur(8px); border-bottom:1px solid var(--hair); }
  .bar-in{max-width:820px; margin:0 auto; padding:9px 22px; display:flex; align-items:center; gap:20px; flex-wrap:wrap;}
  .tabs{display:flex; gap:22px;}
  .tabs button{background:none; border:none; cursor:pointer; font-family:var(--serif); font-size:16px;
    color:var(--sub); padding:5px 1px; position:relative; letter-spacing:.06em;}
  .tabs button.on{color:var(--ink);}
  .tabs button.on::after{content:""; position:absolute; left:0; right:0; bottom:-1px; height:2px; background:var(--seal);}
  #q{flex:1; min-width:150px; border:none; border-bottom:1px solid var(--hair); background:transparent;
    color:var(--ink); font-family:var(--sans); font-size:14px; padding:5px 2px;}
  #q::placeholder{color:var(--faint);}
  #q:focus{outline:none; border-bottom-color:var(--seal);}
  .letterbar{width:100%; display:flex; flex-wrap:wrap; gap:3px 13px; padding-top:2px;}
  .letterbar a{font-family:var(--serif); font-size:12.5px; color:var(--sub); letter-spacing:.06em;}
  .letterbar a:hover{color:var(--seal); text-decoration:none;}
  .letterbar.wide{flex-wrap:nowrap; overflow-x:auto; gap:0 14px; padding-bottom:3px; scrollbar-width:thin;}
  .letterbar.wide a{white-space:nowrap;}

  /* 史料类推荐栏（可关闭） */
  .rec{display:flex; align-items:center; gap:13px; border:1px solid var(--hair);
    background:color-mix(in srgb, var(--seal) 5%, var(--paper)); border-radius:2px;
    padding:11px 14px; margin-bottom:20px;}
  .rec-ico{flex:0 0 auto; width:27px; height:27px; background:var(--seal); color:#fff;
    font-family:var(--serif); display:flex; align-items:center; justify-content:center; border-radius:2px; font-size:15px;}
  .rec-txt{flex:1; font-size:13px; color:var(--sub); line-height:1.6;}
  .rec-txt b{color:var(--ink); font-family:var(--serif); letter-spacing:.03em;}
  .rec-txt a{margin-left:6px; font-weight:600;}
  .rec-x{flex:0 0 auto; border:none; background:none; color:var(--faint); font-size:19px;
    line-height:1; cursor:pointer; padding:2px 4px;}
  .rec-x:hover{color:var(--seal);}

  main{max-width:820px; margin:0 auto; padding:20px 22px 80px; animation:rise .5s ease both;}
  @keyframes rise{from{opacity:0; transform:translateY(6px);} to{opacity:1; transform:none;}}

  /* 凡例 / 说明 */
  .notice{border:1px solid var(--hair); background:var(--paper); border-radius:2px; padding:16px 20px; margin-bottom:26px;}
  .notice>summary{cursor:pointer; font-family:var(--serif); font-size:15px; color:var(--ink); letter-spacing:.05em; list-style:none;}
  .notice>summary::-webkit-details-marker{display:none;}
  .notice>summary::before{content:"凡例 "; color:var(--seal);}
  .notice p{margin:12px 0 4px; color:var(--sub); font-size:13.5px; line-height:1.85;}
  .notice p[lang=en]{font-family:var(--serif); font-style:normal;}
  .notice b{color:var(--ink); font-weight:600;}
  .legend{font-size:12.5px; color:var(--sub); margin-top:10px; padding-top:10px; border-top:1px solid var(--line); line-height:2.1;}
  .legend b{color:var(--ink);}

  /* 首字母分节 */
  .sec{display:flex; align-items:center; gap:16px; margin:30px 0 4px; scroll-margin-top:96px;}
  .sec:first-of-type{margin-top:6px;}
  .sec b{font-family:var(--serif); font-size:25px; color:var(--seal); line-height:1; min-width:20px;}
  .sec .ln{flex:1; height:1px; background:var(--hair);}

  /* 条目 */
  .entry{padding:15px 0; border-bottom:1px solid var(--line);}
  .entry .name{font-family:var(--serif); font-size:17px; color:var(--ink); letter-spacing:.01em;}
  .entry .cnt{font-family:var(--serif); font-size:12.5px; color:var(--faint); margin-left:8px;}
  .entry .meta{font-size:12.5px; color:var(--sub); margin-top:2px;}
  .holder{margin-top:10px; padding-left:15px; border-left:2px solid var(--hair);}
  .holder+.holder{margin-top:12px;}
  .holder .lib{font-family:var(--serif); font-size:14.5px; color:var(--ink); margin-right:8px;}
  .holder .links{font-size:12px; color:var(--sub); margin-top:3px;}
  .holder .links a{color:var(--sub);} .holder .links a:hover{color:var(--seal);}
  .sep{color:var(--faint); margin:0 8px;}
  .ali{color:var(--seal); font-family:var(--sans); font-size:11.5px; margin-left:5px; opacity:.9;}
  .sec-cat b{font-size:20px; letter-spacing:.06em;}
  .sec-cat .cnt{color:var(--faint); font-family:var(--serif); font-size:12.5px;}

  /* 图书馆视图 */
  .regbox{margin:9px 0 14px; padding:2px 0 2px 16px; border-left:2px solid var(--seal); font-size:13px; color:var(--sub); line-height:1.8;}
  .regbox b{color:var(--ink);}
  .rlist{margin:6px 0 0; padding:0; list-style:none;}
  .rlist li{padding:8px 0; border-top:1px solid var(--line); font-size:14px; color:var(--ink); display:flex; flex-wrap:wrap; align-items:baseline; gap:8px;}
  .rlist li:first-child{border-top:none;}
  .rlist .rn{font-family:var(--serif);}

  /* 标签 */
  .tag{display:inline-block; font-family:var(--sans); font-size:11px; line-height:1.6; padding:0 7px;
    border:1px solid; border-radius:2px; letter-spacing:.02em; white-space:nowrap; vertical-align:middle;}
  .t-yes{color:var(--sage); border-color:color-mix(in srgb,var(--sage) 40%,var(--line)); background:color-mix(in srgb,var(--sage) 8%,transparent);}
  .t-no{color:var(--brick); border-color:color-mix(in srgb,var(--brick) 40%,var(--line)); background:color-mix(in srgb,var(--brick) 8%,transparent);}
  .t-local{color:var(--gold); border-color:color-mix(in srgb,var(--gold) 42%,var(--line)); background:color-mix(in srgb,var(--gold) 9%,transparent); font-weight:600;}
  .t-warn{color:var(--gold); border-color:color-mix(in srgb,var(--gold) 40%,var(--line)); background:transparent;}
  .t-mut{color:var(--faint); border-color:var(--hair); border-style:dashed; background:transparent;}
  .cav{color:var(--seal); cursor:help; font-size:10px; margin-left:2px; font-family:var(--sans);}
  .empty{color:var(--faint); font-style:italic;}
  .none{color:var(--sub); font-family:var(--serif); text-align:center; padding:60px 0;}

  @media (max-width:560px){
    .masthead{padding-top:34px;} .masthead h1{font-size:26px;}
    .sec{scroll-margin-top:130px;}
  }
</style>
</head>
<body>
<header class="masthead">
  <div class="kicker">公共图书馆 · 数字资源索引</div>
  <h1>公立图书馆免费电子资源清单</h1>
  <div class="en">Free Digital Resources of Chinese Public Libraries</div>
  <div class="rule"><i></i></div>
  <div class="stat" id="stat"></div>
</header>

<div class="bar">
  <div class="bar-in">
    <nav class="tabs">
      <button id="btn-res" class="on" onclick="setView('res')">按资源</button>
      <button id="btn-lib" onclick="setView('lib')">按图书馆</button>
      <button id="btn-cat" onclick="setView('cat')">按分类</button>
    </nav>
    <input id="q" placeholder="检索 · 资源名或图书馆名…" oninput="render()">
    <div class="letterbar" id="letterbar"></div>
  </div>
</div>

<main>
  <details class="notice" open>
    <summary>· 使用说明 / About &amp; How to use</summary>
    <p>本站整理国家图书馆及各省、直辖市、自治区图书馆 <b>能否线上注册读者证</b>、<b>注册指南链接</b>、<b>有哪些数字资源</b>、<b>各个数字资源能否远程访问</b>（这一点受资源限制，目前只标明了从数字资源页可直接看到能否远程访问的），数据均来自网络公开信息（主要是图书馆官网，不过，官网有时信息更新不及时，如果您对某图书馆很感兴趣，可再检索确认一下）。本站支持检索，以及按资源、按图书馆、按分类三种方式浏览（<b>其中「分类」为人工 + DeepSeek Flash 粗略标注，仅供参考，可能有误</b>）。亦可于<a href="https://github.com/Ray-bot-ai/cn-lib-resources" target="_blank" rel="noopener">笔者 GitHub</a>直接下载原数据。截至 2026 年 7 月 13 日经笔者人工全量核对。<b>少数图书馆线上注册读者证者的可用权限少于线下办理实体读者证者，请自行确认（如国家图书馆，其远程访问已相应标注）。</b><b>如有建议请邮件 <a href="mailto:u3642567@connect.hku.hk">u3642567@connect.hku.hk</a>。</b></p>
    <p lang="en">This site compiles, for the National Library of China and the public libraries of every province, municipality and autonomous region: whether a reader's card can be <b>registered online</b>, links to the <b>registration guides</b>, <b>which digital resources</b> each library offers, and whether each resource can be <b>accessed remotely</b> (marked only where the library's resource page states it directly). Data comes from publicly available sources (mainly the libraries' official websites, which are sometimes out of date — if you are especially interested in a library, please double-check with a fresh search). <b>Note for readers outside mainland China: most online resources listed here require a mainland-China platform account, and many require a mainland-China IP address, to open.</b> At a few libraries an online-registered card grants fewer privileges than a physical card obtained in person — please verify (e.g. the National Library of China; its remote-access entries are marked accordingly). You can search and browse by resource, by library, or by category (<b>category tags are a rough classification by a human + DeepSeek Flash, for reference only</b>); raw data is downloadable from the <a href="https://github.com/Ray-bot-ai/cn-lib-resources" target="_blank" rel="noopener">author's GitHub</a>. Fully hand-verified as of 13 July 2026. Suggestions welcome — email <a href="mailto:u3642567@connect.hku.hk">u3642567@connect.hku.hk</a>.</p>
    <div class="legend">
      <b>注册 Registration</b>　<span class="tag t-yes">可线上注册</span> 不限身份 ·
      <span class="tag t-local">仅本地居民线上注册</span> local only ·
      <span class="tag t-warn">需线下激活/部分</span> ·
      <span class="tag t-no">仅线下办证</span> on-site<br>
      <b>远程 Remote</b>　<span class="tag t-yes">可远程访问</span> off-site ·
      <span class="tag t-no">仅馆内访问</span> in-library ·
      <span class="tag t-mut">远程未标注</span> not stated
    </div>
  </details>
  <div class="rec" id="rec">
    <span class="rec-ico">史</span>
    <div class="rec-txt"><b>史料类推荐</b> · 面向历史研究者——汇集史料、方志、报刊、档案、家谱、金石等资源<span id="rec-n"></span>。<a href="#" onclick="gotoShiliao();return false;">查看史料类 →</a></div>
    <button class="rec-x" onclick="dismissRec()" title="不再显示">×</button>
  </div>
  <div id="app"></div>
</main>

<script>
const DATA = /*__DATA__*/;
let view = 'res';
const app = document.getElementById('app');

function esc(s){ return (s==null?'':String(s)).replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function link(url, text){ return url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(text||url)}</a>` : `<span class="empty">${esc(text||'—')}</span>`; }

/* ——— 拼音首字母 & 排序 ——— */
const collator = new Intl.Collator('zh-Hans-CN');
const ANCH=[['A','阿'],['B','八'],['C','嚓'],['D','哒'],['E','妸'],['F','发'],['G','旮'],['H','哈'],['J','击'],['K','咔'],['L','垃'],['M','痳'],['N','拿'],['O','噢'],['P','啪'],['Q','期'],['R','然'],['S','撒'],['T','塌'],['W','挖'],['X','夕'],['Y','压'],['Z','匝']];
const INIT_OVERRIDE = {'重庆图书馆':'C'};
function cleanKey(s){ return (s||'').replace(/^[\s"'`《》〈〉「」『』【】\[\]（）()·・—\-\.。、,，:：;；*※〔〕]+/,'').trim(); }
function initialOf(s, name){
  if(name && INIT_OVERRIDE[name]) return INIT_OVERRIDE[name];
  const k=cleanKey(s); if(!k) return '#';
  const c=k[0];
  if(/[A-Za-z]/.test(c)) return c.toUpperCase();
  if(/[0-9]/.test(c)) return '#';
  if(collator.compare(c,'阿')<0) return '#';
  let L='Z';
  for(const [l,a] of ANCH){ if(collator.compare(c,a)>=0) L=l; else break; }
  return L;
}
function byName(a,b){ return collator.compare(cleanKey(a),cleanKey(b)); }
const LORDER='#ABCDEFGHIJKLMNOPQRSTUVWXYZ';
// 先按首字母档、再按名称——保证分节连续且字母升序（与 initialOf 分桶一致）
function cmpInit(nameA,nameB,la,lb){
  const ia=LORDER.indexOf(initialOf(nameA,la)), ib=LORDER.indexOf(initialOf(nameB,lb));
  return (ia-ib) || collator.compare(cleanKey(nameA),cleanKey(nameB));
}

/* ——— 徽标 ——— */
function onlineBadge(reg){
  const o=reg&&reg.online;
  if(reg&&reg.online_label){
    const cls={'b-partial':'t-warn','b-unknown':'t-mut','b-local':'t-local','b-yes':'t-yes','b-no':'t-no'}[reg.online_label_class]||'t-warn';
    return `<span class="tag ${cls}">${esc(reg.online_label)}</span>`;
  }
  if(o==='yes') return reg.online_scope==='local'
    ? '<span class="tag t-local">仅本地居民线上注册</span>'
    : '<span class="tag t-yes">可线上注册</span>';
  const map={partial:['部分可线上','t-warn'],no:['仅线下办证','t-no']};
  const [t,c]=map[o]||['注册方式待核','t-mut'];
  return `<span class="tag ${c}">${t}</span>`;
}
function remoteBadge(am){
  let t,c,title='';
  if(!am){ t='远程未标注'; c='t-mut'; }
  else if(/馆外|远程|公网|OA|开放获取|开放存取|存取/.test(am)){ t='可远程访问'; c='t-yes'; }
  else if(/馆内|到馆|触摸屏|现场|自助机/.test(am)){ t='仅馆内访问'; c='t-no'; }
  else { t='远程未标注'; c='t-mut'; title=am; }
  return `<span class="tag ${c}"${title?` title="${esc(title)}"`:''}>${t}</span>`;
}
function isRemote(am){ return !!(am && /馆外|远程|公网|OA|开放获取|开放存取|存取/.test(am)); }
function remoteCell(am, reg){
  let s=remoteBadge(am);
  if(reg && reg.remote_caveat && isRemote(am))
    s+=` <sup class="cav" title="${esc(reg.remote_caveat)}">*线上证权限或受限</sup>`;
  return s;
}
function unverified(lib){ return lib.verified===false ? '<span class="tag t-mut">待核实</span>' : ''; }
function regLine(lib){
  const reg=lib.registration||{}; const bits=[];
  if(reg.eligibility) bits.push('可注册：'+esc(reg.eligibility));
  if(reg.cost) bits.push(esc(reg.cost));
  let s=bits.length? bits.join('；')+'。 ':'';
  if(reg.how) s+=esc(reg.how);
  return s;
}

function holdingsByResource(){
  const idx={};
  for(const lib of DATA.libraries)
    for(const h of (lib.resources||[])){
      const id=h.canonical_id||('__raw__'+(h.raw_name||''));
      (idx[id]=idx[id]||[]).push({lib,h});
    }
  return idx;
}

/* ——— 分类（论文/图书/古籍/少儿/其他），可由 resources.json 的 category 字段覆盖 ——— */
// 分类标签（人工在 resources.json 的 category 里标注，支持多标签）
function cats(r){
  const c=r&&r.category;
  if(Array.isArray(c)) return c.filter(x=>x&&x.trim());
  if(typeof c==='string'&&c.trim()) return [c.trim()];
  return [];
}
let CAT_ORDER=null;                    // 全库标签按频次降序（多者在前）
function catOrder(){
  if(CAT_ORDER) return CAT_ORDER;
  const c={};
  for(const k in DATA.resources){ if(k[0]==='_') continue; for(const t of cats(DATA.resources[k])) c[t]=(c[t]||0)+1; }
  CAT_ORDER=Object.keys(c).sort((a,b)=>c[b]-c[a]||collator.compare(a,b));
  return CAT_ORDER;
}
function shiliaoCount(){ let n=0; for(const k in DATA.resources){ if(k[0]==='_')continue; if(cats(DATA.resources[k]).includes('史料'))n++; } return n; }
function noteHTML(r){ return r.note ? ` <span class="ali">${esc(r.note)}</span>` : ''; }
function resHay(r, holders){ return (r.name+' '+(r.aliases||[]).join(' ')+' '+(r.note||'')+' '+cats(r).join(' ')+' '+holders.map(x=>x.lib.name).join(' ')).toLowerCase(); }
function resourceEntry(r, holders){
  let out=`<div class="entry"><span class="name">${esc(r.name)}</span>${noteHTML(r)}<span class="cnt">${holders.length} 馆</span>`;
  if(r.vendor||r.homepage) out+=`<div class="meta">${r.vendor?esc(r.vendor):''}${r.vendor&&r.homepage?'　':''}${r.homepage?link(r.homepage,'资源官网'):''}</div>`;
  const hs=holders.slice().sort((x,y)=>cmpInit(x.lib.name,y.lib.name,x.lib.name,y.lib.name));
  for(const {lib,h} of hs){
    const reg=lib.registration||{};
    out+=`<div class="holder"><span class="lib">${esc(lib.name)}</span> ${onlineBadge(reg)} ${remoteCell(h.access_method,reg)} ${unverified(lib)}`;
    if(h.scope) out+=` <span class="empty">（${esc(h.scope)}）</span>`;
    out+=`<div class="links">办证 ${reg.tutorial_url?link(reg.tutorial_url,'注册指南↗'):'<span class="empty">—</span>'}<span class="sep">·</span>资源 ${h.access_url?link(h.access_url,'打开↗'):'<span class="empty">见数字资源页</span>'}<span class="sep">·</span>数字资源页 ${link(lib.digital_resource_url,'↗')}</div></div>`;
  }
  return out+'</div>';
}

function setView(v){
  view=v;
  document.getElementById('btn-res').classList.toggle('on',v==='res');
  document.getElementById('btn-lib').classList.toggle('on',v==='lib');
  document.getElementById('btn-cat').classList.toggle('on',v==='cat');
  render();
}

function allResourceItems(){
  const idx=holdingsByResource();
  return Object.keys(idx).map(id=>{
    const r=DATA.resources[id]||{name:(id.startsWith('__raw__')?id.slice(7):id), _unmatched:true};
    return {r, holders:idx[id]};
  });
}

function renderByResource(kw){
  let items=allResourceItems().sort((a,b)=>cmpInit(a.r.name,b.r.name));
  let out='', cur='', letters=[];
  for(const {r,holders} of items){
    if(kw && !resHay(r,holders).includes(kw)) continue;
    const L=initialOf(r.name);
    if(L!==cur){ cur=L; letters.push(L); out+=`<div class="sec" id="sec-${L}"><b>${L}</b><span class="ln"></span></div>`; }
    out+=resourceEntry(r,holders);
  }
  return {html: out||'<div class="none">未见匹配的资源。</div>', letters};
}

function renderByCategory(kw){
  const items=allResourceItems();
  const byTag={}, untagged=[];
  for(const it of items){
    const ts=cats(it.r);
    if(!ts.length){ untagged.push(it); continue; }
    for(const t of ts) (byTag[t]=byTag[t]||[]).push(it);
  }
  let out='', letters=[];
  const emit=(label,arr)=>{
    arr=arr.filter(it=>!kw || resHay(it.r,it.holders).includes(kw));
    if(!arr.length) return;
    arr.sort((a,b)=>cmpInit(a.r.name,b.r.name));
    letters.push(label);
    out+=`<div class="sec sec-cat" id="sec-${label}"><b>${esc(label)}</b><span class="ln"></span><span class="cnt">${arr.length} 种</span></div>`;
    for(const {r,holders} of arr) out+=resourceEntry(r,holders);
  };
  for(const t of catOrder()) emit(t, byTag[t]||[]);
  emit('未分类', untagged);
  return {html: out||'<div class="none">未见匹配的资源。</div>', letters};
}

function renderByLibrary(kw){
  let libs=[...DATA.libraries].sort((a,b)=>cmpInit(a.name,b.name,a.name,b.name));
  let out='', cur='', letters=[];
  for(const lib of libs){
    const rmeta=(lib.resources||[]).map(h=>{const rr=DATA.resources[h.canonical_id]||{}; return (h.raw_name||'')+' '+(rr.name||'')+' '+((rr.aliases||[]).join(' '))+' '+(rr.note||'');}).join(' ');
    const hay=(lib.name+' '+(lib.region||'')+' '+rmeta).toLowerCase();
    if(kw && !hay.includes(kw)) continue;
    const L=initialOf(lib.name, lib.name);
    if(L!==cur){ cur=L; letters.push(L); out+=`<div class="sec" id="sec-${L}"><b>${L}</b><span class="ln"></span></div>`; }
    const reg=lib.registration||{}; const rs=lib.resources||[];
    out+=`<div class="entry"><span class="name">${esc(lib.name)}</span> ${onlineBadge(reg)} ${unverified(lib)}<span class="cnt">${rs.length} 个资源</span>`;
    out+=`<div class="regbox"><b>办证：</b>${regLine(lib)||'<span class="empty">待核实</span>'}`;
    if(reg.remote_caveat) out+=`<div style="color:var(--seal);margin-top:4px">⚠ ${esc(reg.remote_caveat)}</div>`;
    out+=`<div style="margin-top:5px">${reg.tutorial_url?link(reg.tutorial_url,'注册指南↗'):''}<span class="sep">·</span>官网 ${link(lib.official_site,'↗')}<span class="sep">·</span>数字资源页 ${link(lib.digital_resource_url,'↗')}</div></div>`;
    out+='<ul class="rlist">';
    if(!rs.length) out+='<li class="empty">资源清单待采集</li>';
    const rsorted=rs.slice().sort((x,y)=>{
      const nx=(DATA.resources[x.canonical_id]||{}).name||x.raw_name||'';
      const ny=(DATA.resources[y.canonical_id]||{}).name||y.raw_name||'';
      return cmpInit(nx,ny);
    });
    for(const h of rsorted){
      const r=DATA.resources[h.canonical_id]||{};
      const name=r.name||h.raw_name||h.canonical_id;
      out+=`<li><span class="rn">${esc(name)}</span> ${remoteCell(h.access_method,reg)}`;
      if(h.scope) out+=` <span class="empty">（${esc(h.scope)}）</span>`;
      if(h.access_url) out+=` ${link(h.access_url,'打开↗')}`;
      out+='</li>';
    }
    out+='</ul></div>';
  }
  return {html: out||'<div class="none">未见匹配的图书馆。</div>', letters};
}

function buildLetterBar(letters){
  const bar=document.getElementById('letterbar');
  if(!letters.length){ bar.innerHTML=''; return; }
  bar.innerHTML=letters.map(L=>`<a href="#sec-${L}">${L}</a>`).join('');
}

function render(){
  const kw=(document.getElementById('q').value||'').trim().toLowerCase();
  const {html, letters}= view==='res' ? renderByResource(kw) : view==='cat' ? renderByCategory(kw) : renderByLibrary(kw);
  app.innerHTML=html;
  document.getElementById('letterbar').classList.toggle('wide', view==='cat');
  buildLetterBar(letters);
}

// 史料类推荐栏（可关闭，记忆到 localStorage）
function gotoShiliao(){ setView('cat'); setTimeout(()=>{ location.hash=''; location.hash='#sec-史料'; }, 30); }
function dismissRec(){ const el=document.getElementById('rec'); if(el) el.style.display='none'; try{localStorage.setItem('hideRec','1');}catch(e){} }
(function(){
  const rec=document.getElementById('rec'); if(!rec) return;
  try{ if(localStorage.getItem('hideRec')==='1') rec.style.display='none'; }catch(e){}
  const n=shiliaoCount(); const el=document.getElementById('rec-n'); if(el) el.textContent=n?`（共 ${n} 种）`:'';
})();

document.getElementById('stat').textContent =
  `收录 ${DATA.libraries.length} 馆 · ${Object.keys(DATA.resources).length} 种数字资源`;
render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
