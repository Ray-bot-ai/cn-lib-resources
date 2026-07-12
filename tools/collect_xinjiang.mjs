#!/usr/bin/env node
// 新疆图书馆 - 获取 Vue allTypes 数据，直接调 API 获取每个分类资源
const BASE = 'http://127.0.0.1:9222';
const TARGET_URL = 'https://www.xjlib.org/engine2/m/EAC19328B24072E4?p=266336&wfwfid=6256&pageId=266336&websiteId=156885&mhType=1&publicId=6530bf5a44953111ed0a1776c93893275cbc&mhEnc=9487ec8c18cc79e3f38c641430783d2e';

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
  let r = await fetch(BASE + '/json/new?' + encodeURIComponent(TARGET_URL), { method: 'PUT' });
  if (!r.ok) r = await fetch(BASE + '/json/new?' + encodeURIComponent(TARGET_URL));
  const tab = await r.json();
  console.log('Tab created:', tab.id);
  
  const ws = await connect(tab.webSocketDebuggerUrl);
  await cmd(ws, 'Runtime.enable');
  await cmd(ws, 'Page.enable');
  await cmd(ws, 'Network.enable');
  
  console.log('Waiting for page load...');
  await sleep(8000);
  
  // 获取 Vue 实例的 allTypes 数据
  console.log('\n=== 获取 Vue allTypes ===');
  const allTypes = await cmd(ws, 'Runtime.evaluate', {
    expression: `
      (function() {
        var el = document.getElementById('type-vue');
        if (!el || !el.__vue__) return 'no vue';
        var vm = el.__vue__;
        var allTypes = vm.allTypes || [];
        var types = vm.types || [];
        return JSON.stringify({
          allTypes: allTypes,
          types: types,
          appId: vm.appId,
        });
      })()
    `,
    returnByValue: true,
  });
  
  const typeData = JSON.parse(allTypes.result?.value || '{}');
  console.log('allTypes:', JSON.stringify(typeData.allTypes, null, 2).substring(0, 3000));
  console.log('types:', JSON.stringify(typeData.types, null, 2).substring(0, 2000));
  console.log('appId:', typeData.appId);
  
  // 获取页面加载时的 API 参数（sign, engineInstanceId 等）
  // 从第一次 API 调用的 postData 提取
  console.log('\n=== 获取页面加载时的 sign 和 engineInstanceId ===');
  const pageParams = await cmd(ws, 'Runtime.evaluate', {
    expression: `
      (function() {
        var el = document.getElementById('type-vue');
        if (!el || !el.__vue__) return '{}';
        var vm = el.__vue__;
        // 找 sign 和 engineInstanceId
        var result = {
          appId: vm.appId,
          pageId: vm.pageId,
          websiteId: vm.websiteId,
        };
        // 从 parentUrl 或其他属性找
        if (vm.parentUrl) result.parentUrl = vm.parentUrl;
        // 看 crumbs
        if (vm.crumbs) result.crumbs = vm.crumbs;
        if (vm.crumbsParent) result.crumbsParent = vm.crumbsParent;
        return JSON.stringify(result);
      })()
    `,
    returnByValue: true,
  });
  console.log('页面参数:', pageParams.result?.value);
  
  // 从 Network 请求历史中获取 sign
  // 先获取当前 typeId
  const currentTypeId = await cmd(ws, 'Runtime.evaluate', {
    expression: `
      (function() {
        var el = document.getElementById('type-vue');
        if (!el || !el.__vue__) return '{}';
        var vm = el.__vue__;
        var currentType = vm.types && vm.types.length > 0 ? vm.types[0] : null;
        return JSON.stringify({
          currentTypeId: currentType ? currentType.id : null,
          currentTypeName: currentType ? currentType.name : null,
          allTypesCount: (vm.allTypes || []).length,
          typesCount: (vm.types || []).length,
        });
      })()
    `,
    returnByValue: true,
  });
  console.log('当前分类:', currentTypeId.result?.value);
  
  // 获取 allTypes 的完整结构（每个分类的 id 和 name）
  const typeDetails = await cmd(ws, 'Runtime.evaluate', {
    expression: `
      (function() {
        var el = document.getElementById('type-vue');
        if (!el || !el.__vue__) return '[]';
        var vm = el.__vue__;
        var allTypes = vm.allTypes || [];
        return JSON.stringify(allTypes.map(function(t) {
          return {
            id: t.id,
            name: t.name,
            parentId: t.parentId,
            children: (t.children || []).map(function(c) {
              return {id: c.id, name: c.name, parentId: c.parentId};
            }),
          };
        }));
      })()
    `,
    returnByValue: true,
  });
  console.log('\n=== allTypes 详细结构 ===');
  console.log(typeDetails.result?.value);
  
  // 获取 generalDatas（当前已加载的资源数据）
  const generalDatas = await cmd(ws, 'Runtime.evaluate', {
    expression: `
      (function() {
        var el = document.getElementById('type-vue');
        if (!el || !el.__vue__) return '[]';
        var vm = el.__vue__;
        var datas = vm.generalDatas || [];
        return JSON.stringify(datas.map(function(d) {
          return {
            id: d.id,
            name: d.name || d.title || '',
            typeId: d.typeId,
            url: d.url || d.link || '',
            desc: (d.desc || d.intro || d.summary || '').substring(0, 100),
          };
        }));
      })()
    `,
    returnByValue: true,
  });
  console.log('\n=== generalDatas (当前分类资源) ===');
  const datas = JSON.parse(generalDatas.result?.value || '[]');
  console.log(`资源数: ${datas.length}`);
  for (const d of datas) {
    console.log(`  - ${d.name} (typeId=${d.typeId})`);
  }
  
  ws.close();
  await fetch(BASE + '/json/close/' + tab.id);
}

main().catch(e => { console.error('ERR', e.message, e.stack); process.exit(1); });
