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
OUT = os.path.join(ROOT, "site", "index.html")


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
  :root { --bg:#fafaf8; --card:#fff; --line:#e6e3dc; --ink:#222; --muted:#777; --accent:#7a5c3e; --soft:#f3f0ea; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#1b1a18; --card:#26241f; --line:#3a3730; --ink:#eee; --muted:#a29a8c; --accent:#c8a878; --soft:#211f1b; }
  }
  * { box-sizing:border-box; }
  body { margin:0; font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
         background:var(--bg); color:var(--ink); line-height:1.6; }
  header { position:sticky; top:0; background:var(--bg); border-bottom:1px solid var(--line);
           padding:12px 18px; z-index:10; }
  h1 { font-size:19px; margin:0 0 4px; }
  .stat { color:var(--muted); font-size:13px; margin-bottom:9px; }
  .controls { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
  .toggle button { border:1px solid var(--line); background:var(--card); color:var(--ink);
    padding:6px 14px; cursor:pointer; font-size:14px; }
  .toggle button:first-child { border-radius:6px 0 0 6px; }
  .toggle button:last-child { border-radius:0 6px 6px 0; border-left:none; }
  .toggle button.on { background:var(--accent); color:#fff; border-color:var(--accent); }
  #q { flex:1; min-width:180px; padding:7px 10px; border:1px solid var(--line);
       border-radius:6px; background:var(--card); color:var(--ink); font-size:14px; }
  main { max-width:920px; margin:0 auto; padding:18px; }
  .notice { background:var(--soft); border:1px solid var(--line); border-radius:10px;
            padding:12px 16px; margin-bottom:16px; font-size:13.5px; color:var(--ink); }
  .notice summary { cursor:pointer; font-weight:600; color:var(--accent); }
  .notice p { margin:8px 0 4px; color:var(--muted); line-height:1.7; }
  .legend { font-size:12.5px; color:var(--muted); margin-top:8px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px;
          padding:14px 16px; margin-bottom:14px; }
  .card h2 { font-size:16px; margin:0 0 6px; display:flex; align-items:center; flex-wrap:wrap; gap:6px; }
  .meta { color:var(--muted); font-size:13px; margin-bottom:8px; }
  .badge { display:inline-block; font-size:12px; padding:1px 9px; border-radius:20px;
           border:1px solid var(--line); vertical-align:middle; white-space:nowrap; }
  .b-yes { background:#e7f3e7; color:#2e7d32; border-color:#bfe0bf; }
  .b-no  { background:#fbeaea; color:#c0392b; border-color:#eec4c4; }
  .b-partial { background:#fdf3e2; color:#b9770e; border-color:#eeddb8; }
  .b-local { background:#fdeede; color:#a85b1a; border-color:#eccfa6; font-weight:600; }
  .b-unknown { background:transparent; color:var(--muted); border-style:dashed; }
  .b-unverified { background:transparent; color:var(--muted); border-style:dashed; }
  @media (prefers-color-scheme: dark) {
    .b-yes{background:#22331f;color:#8bc98b;border-color:#3c5b37;}
    .b-no{background:#331f1f;color:#e08b8b;border-color:#5b3737;}
    .b-partial{background:#332a1a;color:#d8b06a;border-color:#5b4a2f;}
    .b-local{background:#3a2c19;color:#e0a35c;border-color:#5f4526;}
  }
  .regbox { background:var(--soft); border:1px solid var(--line); border-radius:8px;
            padding:8px 12px; margin:2px 0 10px; font-size:13px; }
  .regbox b { color:var(--ink); }
  ul.rows { list-style:none; margin:6px 0 0; padding:0; }
  ul.rows li { border-top:1px dashed var(--line); padding:9px 0; }
  ul.rows li:first-child { border-top:none; }
  .libname { font-weight:600; }
  .sub { color:var(--muted); font-size:12.5px; }
  a { color:var(--accent); }
  .empty { color:var(--muted); font-style:italic; }
  .count { color:var(--muted); font-size:12.5px; font-weight:normal; }
</style>
</head>
<body>
<header>
  <h1>公立图书馆免费电子资源清单</h1>
  <div class="subtitle" style="font-size:13px;color:var(--muted);margin:-2px 0 6px">Free Digital Resources of Chinese Public Libraries</div>
  <div class="stat" id="stat"></div>
  <div class="controls">
    <span class="toggle">
      <button id="btn-res" class="on" onclick="setView('res')">按资源找</button>
      <button id="btn-lib" onclick="setView('lib')">按图书馆找</button>
    </span>
    <input id="q" placeholder="搜索资源名 / 图书馆名…" oninput="render()">
  </div>
</header>
<main>
  <details class="notice" open>
    <summary>关于本站 · 使用说明 / About &amp; How to use</summary>
    <p>本站整理国家图书馆及各省、直辖市、自治区图书馆 <b>能否线上注册读者证</b>、<b>注册指南链接</b>、<b>有哪些数字资源</b>、<b>各个数字资源能否远程访问</b>（这一点受资源限制，目前只标明了从数字资源页可直接看到能否远程访问的），数据均来自网络公开信息（主要是图书馆官网，不过，官网有时信息更新不及时，如果您对某图书馆很感兴趣，可再检索确认一下）。本站支持检索，以及按资源、图书馆分类访问。亦可于笔者 github 直接下载原数据。截至 2026 年 7 月 13 日经笔者人工全量核对。<b>如有建议请邮件 <a href="mailto:u3642567@connect.hku.hk">u3642567@connect.hku.hk</a>。</b></p>
    <p lang="en">This site compiles, for the National Library of China and the public libraries of every province, municipality and autonomous region: whether a reader's card can be <b>registered online</b>, links to the <b>registration guides</b>, <b>which digital resources</b> each library offers, and whether each resource can be <b>accessed remotely</b> (marked only where the library's resource page states it directly). Data comes from publicly available sources (mainly the libraries' official websites, which are sometimes out of date — if you are especially interested in a library, please double-check with a fresh search). <b>Note for readers outside mainland China: most online resources listed here require a mainland-China platform account, and many require a mainland-China IP address, to open.</b> You can search and browse by resource or by library; raw data is downloadable from the author's GitHub. Fully hand-verified as of 13 July 2026. Suggestions welcome — email <a href="mailto:u3642567@connect.hku.hk">u3642567@connect.hku.hk</a>.</p>
    <div class="legend">
      <b>注册 / Registration：</b>
      <span class="badge b-yes">可线上注册</span>（不限身份 open）/ <span class="badge b-local">仅本地居民线上注册</span>（local residents only）/ <span class="badge b-partial">部分可线上</span> / <span class="badge b-no">仅线下办证</span>（on-site only）
      <b>远程 / Remote：</b>
      <span class="badge b-yes">可远程访问</span>（off-site OK）/ <span class="badge b-no">仅馆内访问</span>（in-library）/ <span class="badge b-unknown">远程未标注</span>（not stated）
    </div>
  </details>
  <div id="app"></div>
</main>

<script>
const DATA = /*__DATA__*/;
let view = 'res';

function esc(s){ return (s==null?'':String(s)).replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
function link(url, text){ return url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(text||url)}</a>` : `<span class="empty">${esc(text||'—')}</span>`; }

// 能否线上注册（图书馆维度）；yes 再分 open(未注明身份限制) / local(仅本地居民)
function onlineBadge(reg){
  const o=reg&&reg.online;
  if(o==='yes'){
    return reg.online_scope==='local'
      ? '<span class="badge b-local">仅本地居民线上注册</span>'
      : '<span class="badge b-yes">可线上注册</span>';
  }
  const map={partial:['部分可线上','b-partial'],no:['仅线下办证','b-no']};
  const [t,c]=map[o]||['注册方式未核实','b-unknown'];
  return `<span class="badge ${c}">${t}</span>`;
}
// 能否远程访问（资源维度，从 access_method 判断）→ 收敛为三态，原始值放 title 供悬停
function remoteBadge(am){
  let t,c,title='';
  if(!am){ t='远程未标注'; c='b-unknown'; }
  else if(/馆外|远程|公网|OA|开放获取|开放存取|存取/.test(am)){ t='可远程访问'; c='b-yes'; }
  else if(/馆内|到馆|触摸屏|现场|自助机/.test(am)){ t='仅馆内访问'; c='b-no'; }
  else { t='远程未标注'; c='b-unknown'; title=am; }
  return `<span class="badge ${c}"${title?` title="${esc(title)}"`:''}>${t}</span>`;
}
function unverified(lib){ return lib.verified===false ? '<span class="badge b-unverified">待核实</span>' : ''; }
function regLine(lib){
  const reg=lib.registration||{};
  const bits=[];
  if(reg.eligibility) bits.push('可注册：'+esc(reg.eligibility));
  if(reg.cost) bits.push(esc(reg.cost));
  let s = bits.length? bits.join('；')+'。 ':'';
  if(reg.how) s += esc(reg.how);
  return s;
}

// 反转：canonical_id -> [{library, holding}]
function holdingsByResource(){
  const idx={};
  for(const lib of DATA.libraries){
    for(const h of (lib.resources||[])){
      const id=h.canonical_id||('__raw__'+(h.raw_name||''));
      (idx[id]=idx[id]||[]).push({lib,h});
    }
  }
  return idx;
}

function setView(v){
  view=v;
  document.getElementById('btn-res').classList.toggle('on',v==='res');
  document.getElementById('btn-lib').classList.toggle('on',v==='lib');
  render();
}

// —— 按资源：每个馆旁边直接给「能否线上注册 + 能否远程访问」两枚徽标 ——
function renderByResource(kw){
  const idx=holdingsByResource();
  const ids=Object.keys(idx).sort((a,b)=>{
    const na=(DATA.resources[a]||{}).name||a, nb=(DATA.resources[b]||{}).name||b;
    return na.localeCompare(nb,'zh');
  });
  let out='';
  for(const id of ids){
    const r=DATA.resources[id]||{name:(id.startsWith('__raw__')?id.slice(7):id), _unmatched:true};
    const holders=idx[id].slice().sort((x,y)=>(x.lib.region||'').localeCompare(y.lib.region||'','zh'));
    const hay=(r.name+' '+(r.aliases||[]).join(' ')+' '+holders.map(x=>x.lib.name).join(' ')).toLowerCase();
    if(kw && !hay.includes(kw)) continue;
    out+=`<div class="card"><h2>${esc(r.name)} <span class="count">· ${holders.length} 馆</span></h2>`;
    const m=[]; if(r.vendor)m.push(esc(r.vendor)); if(r.category)m.push(esc(r.category));
    if(m.length||r.homepage) out+=`<div class="meta">${m.join(' · ')}${r.homepage?'　'+link(r.homepage,'资源官网'):''}</div>`;
    out+='<ul class="rows">';
    for(const {lib,h} of holders){
      const reg=lib.registration||{};
      out+=`<li><span class="libname">${esc(lib.name)}</span> ${onlineBadge(reg)} ${remoteBadge(h.access_method)} ${unverified(lib)}`;
      if(h.scope) out+=` <span class="sub">（${esc(h.scope)}）</span>`;
      out+=`<div class="sub">`;
      const parts=[];
      parts.push('办证：'+(reg.tutorial_url?link(reg.tutorial_url,'注册指南↗'):'<span class="empty">—</span>'));
      parts.push('资源入口：'+(h.access_url?link(h.access_url,'打开↗'):'<span class="empty">见数字资源页</span>'));
      parts.push('数字资源页：'+link(lib.digital_resource_url,'↗'));
      out+=parts.join('　·　');
      out+=`</div></li>`;
    }
    out+='</ul></div>';
  }
  return out||'<p class="empty">没有匹配的资源。</p>';
}

// —— 按图书馆：突出「能否线上注册」+ 办证要求方框 + 每条资源的远程徽标 ——
function renderByLibrary(kw){
  const libs=[...DATA.libraries].sort((a,b)=>(a.region||'').localeCompare(b.region||'','zh'));
  let out='';
  for(const lib of libs){
    const hay=(lib.name+' '+(lib.region||'')+' '+(lib.resources||[]).map(h=>h.raw_name||'').join(' ')).toLowerCase();
    if(kw && !hay.includes(kw)) continue;
    const reg=lib.registration||{};
    const rs=lib.resources||[];
    out+=`<div class="card"><h2>${esc(lib.name)} ${onlineBadge(reg)} ${unverified(lib)} <span class="count">· ${rs.length} 个资源</span></h2>`;
    out+=`<div class="regbox"><b>办证：</b>${regLine(lib)||'<span class="empty">待核实</span>'}`;
    out+=`<div class="sub" style="margin-top:5px">`;
    out+=`${link(reg.tutorial_url,'注册指南↗')}　·　官网：${link(lib.official_site,'↗')}　·　数字资源页：${link(lib.digital_resource_url,'↗')}`;
    out+=`</div></div>`;
    out+='<ul class="rows">';
    if(!rs.length){ out+='<li class="empty">资源清单待采集</li>'; }
    for(const h of rs){
      const r=DATA.resources[h.canonical_id]||{};
      const name=r.name||h.raw_name||h.canonical_id;
      out+=`<li>${esc(name)} ${remoteBadge(h.access_method)}`;
      if(h.scope) out+=` <span class="sub">（${esc(h.scope)}）</span>`;
      if(h.access_url) out+=` <span class="sub">${link(h.access_url,'打开↗')}</span>`;
      out+='</li>';
    }
    out+='</ul></div>';
  }
  return out||'<p class="empty">没有匹配的图书馆。</p>';
}

function render(){
  const kw=(document.getElementById('q').value||'').trim().toLowerCase();
  document.getElementById('app').innerHTML =
    view==='res' ? renderByResource(kw) : renderByLibrary(kw);
}
document.getElementById('stat').textContent =
  `共 ${DATA.libraries.length} 个图书馆 · ${Object.keys(DATA.resources).length} 种数字资源`;
render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
