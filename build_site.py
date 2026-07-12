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
<title>公立图书馆免费电子资源清单</title>
<style>
  :root { --bg:#fafaf8; --card:#fff; --line:#e6e3dc; --ink:#222; --muted:#777; --accent:#7a5c3e; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#1b1a18; --card:#26241f; --line:#3a3730; --ink:#eee; --muted:#a29a8c; --accent:#c8a878; }
  }
  * { box-sizing:border-box; }
  body { margin:0; font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
         background:var(--bg); color:var(--ink); line-height:1.6; }
  header { position:sticky; top:0; background:var(--bg); border-bottom:1px solid var(--line);
           padding:14px 18px; z-index:10; }
  h1 { font-size:19px; margin:0 0 10px; }
  .controls { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
  .toggle button { border:1px solid var(--line); background:var(--card); color:var(--ink);
    padding:6px 14px; cursor:pointer; font-size:14px; }
  .toggle button:first-child { border-radius:6px 0 0 6px; }
  .toggle button:last-child { border-radius:0 6px 6px 0; border-left:none; }
  .toggle button.on { background:var(--accent); color:#fff; border-color:var(--accent); }
  #q { flex:1; min-width:180px; padding:7px 10px; border:1px solid var(--line);
       border-radius:6px; background:var(--card); color:var(--ink); font-size:14px; }
  main { max-width:900px; margin:0 auto; padding:18px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:10px;
          padding:14px 16px; margin-bottom:14px; }
  .card h2 { font-size:16px; margin:0 0 4px; }
  .meta { color:var(--muted); font-size:13px; margin-bottom:8px; }
  .badge { display:inline-block; font-size:12px; padding:1px 8px; border-radius:20px;
           border:1px solid var(--line); margin-left:6px; vertical-align:middle; }
  .b-yes { background:#e7f3e7; color:#2e7d32; border-color:#bfe0bf; }
  .b-no  { background:#fbeaea; color:#c0392b; border-color:#eec4c4; }
  .b-partial { background:#fdf3e2; color:#b9770e; border-color:#eeddb8; }
  .b-unknown { background:transparent; color:var(--muted); }
  .b-unverified { background:transparent; color:var(--muted); border-style:dashed; }
  @media (prefers-color-scheme: dark) {
    .b-yes{background:#22331f;color:#8bc98b;border-color:#3c5b37;}
    .b-no{background:#331f1f;color:#e08b8b;border-color:#5b3737;}
    .b-partial{background:#332a1a;color:#d8b06a;border-color:#5b4a2f;}
  }
  ul.rows { list-style:none; margin:6px 0 0; padding:0; }
  ul.rows li { border-top:1px dashed var(--line); padding:8px 0; }
  ul.rows li:first-child { border-top:none; }
  .sub { color:var(--muted); font-size:13px; }
  a { color:var(--accent); }
  .empty { color:var(--muted); font-style:italic; }
</style>
</head>
<body>
<header>
  <h1>公立图书馆免费电子资源清单</h1>
  <div class="controls">
    <span class="toggle">
      <button id="btn-res" class="on" onclick="setView('res')">按资源</button>
      <button id="btn-lib" onclick="setView('lib')">按图书馆</button>
    </span>
    <input id="q" placeholder="搜索资源名 / 图书馆名…" oninput="render()">
  </div>
</header>
<main id="app"></main>

<script>
const DATA = /*__DATA__*/;
let view = 'res';

function esc(s){ return (s==null?'':String(s)).replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
function link(url, text){ return url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(text||url)}</a>` : `<span class="empty">${esc(text||'待核实')}</span>`; }

function onlineBadge(o){
  const map={yes:['可线上注册','b-yes'],no:['仅线下','b-no'],partial:['部分线上','b-partial']};
  const [t,c]=map[o]||['注册方式待核实','b-unknown'];
  return `<span class="badge ${c}">${t}</span>`;
}
function unverified(lib){ return lib.verified===false ? '<span class="badge b-unverified">待核实</span>' : ''; }

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

function renderByResource(kw){
  const idx=holdingsByResource();
  const ids=Object.keys(idx).sort();
  let out='';
  for(const id of ids){
    const r=DATA.resources[id]||{name:(id.startsWith('__raw__')?id.slice(7):id), _unmatched:true};
    const holders=idx[id];
    const hay=(r.name+' '+(r.aliases||[]).join(' ')+' '+holders.map(x=>x.lib.name).join(' ')).toLowerCase();
    if(kw && !hay.includes(kw)) continue;
    out+=`<div class="card"><h2>${esc(r.name)} ${r._unmatched?'<span class="badge b-unverified">未归一化</span>':''}</h2>`;
    out+=`<div class="meta">${esc(r.vendor||'')}${r.category?' · '+esc(r.category):''} ${r.homepage?'· '+link(r.homepage,'官网'):''}</div>`;
    out+='<ul class="rows">';
    for(const {lib,h} of holders){
      out+=`<li><b>${esc(lib.name)}</b> ${unverified(lib)}`;
      const bits=[];
      if(h.scope) bits.push('范围：'+esc(h.scope));
      if(h.access_method) bits.push('方式：'+esc(h.access_method));
      out+=bits.length?` <span class="sub">（${bits.join('　')}）</span>`:'';
      out+=`<div class="sub">`;
      out+=`访问：${link(h.access_url)}　`;
      out+=`注册教程：${link(lib.registration&&lib.registration.tutorial_url)}　`;
      out+=`数字资源页：${link(lib.digital_resource_url)}`;
      out+=`</div></li>`;
    }
    out+='</ul></div>';
  }
  return out||'<p class="empty">没有匹配的资源。</p>';
}

function renderByLibrary(kw){
  const libs=[...DATA.libraries].sort((a,b)=>(a.region||'').localeCompare(b.region||'','zh'));
  let out='';
  for(const lib of libs){
    const hay=(lib.name+' '+(lib.region||')')+' '+(lib.resources||[]).map(h=>h.raw_name||'').join(' ')).toLowerCase();
    if(kw && !hay.includes(kw)) continue;
    const reg=lib.registration||{};
    out+=`<div class="card"><h2>${esc(lib.name)} ${onlineBadge(reg.online)} ${unverified(lib)}</h2>`;
    const meta=[];
    if(reg.eligibility) meta.push('可注册：'+esc(reg.eligibility));
    if(reg.cost) meta.push(esc(reg.cost));
    out+=`<div class="meta">${meta.join('　')||'注册条件待核实'}</div>`;
    out+=`<div class="sub">`;
    out+=`官网：${link(lib.official_site)}　数字资源页：${link(lib.digital_resource_url)}　注册教程：${link(reg.tutorial_url)}`;
    out+=`</div>`;
    const rs=lib.resources||[];
    out+='<ul class="rows">';
    if(!rs.length){ out+='<li class="empty">资源清单待采集</li>'; }
    for(const h of rs){
      const r=DATA.resources[h.canonical_id]||{};
      const name=r.name||h.raw_name||h.canonical_id;
      out+=`<li>${esc(name)}`;
      const bits=[];
      if(h.scope) bits.push('范围：'+esc(h.scope));
      if(h.access_method) bits.push('方式：'+esc(h.access_method));
      if(bits.length) out+=` <span class="sub">（${bits.join('　')}）</span>`;
      if(h.access_url) out+=` <span class="sub">${link(h.access_url,'访问')}</span>`;
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
render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
