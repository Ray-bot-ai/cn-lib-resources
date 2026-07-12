#!/usr/bin/env node
// 天津图书馆数字资源采集脚本
// 抓取 8 个栏目的 ArticleChannel.aspx?ChannelID=XXX 页面，解析 table 中的资源条目

import fs from 'fs';
import https from 'https';
import http from 'http';

const CHANNELS = [
  { id: 271, name: '电子图书' },
  { id: 272, name: '电子报纸' },
  { id: 273, name: '电子期刊' },
  { id: 408, name: '多媒体' },
  { id: 409, name: '数据事实' },
  { id: 625, name: '标准专利' },
  { id: 620, name: '少儿资源' },
  { id: 624, name: '试用资源' },
];

function fetch(url) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith('https') ? https : http;
    mod.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
      }
    }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        const newUrl = new URL(res.headers.location, url).href;
        return resolve(fetch(newUrl));
      }
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => {
        resolve(Buffer.concat(chunks).toString('utf-8'));
      });
    }).on('error', reject);
  });
}

// 解析 HTML 中的 table，提取资源条目
function parseTable(html, channelName) {
  const results = [];
  
  // 找到 text_con 区域，再找其中的 table
  let tableHtml = null;
  const textConMatch = html.match(/<div class="text_con">([\s\S]*?)<\/div>\s*<\/div>/);
  if (textConMatch) {
    const tableMatch = textConMatch[1].match(/<table[^>]*>([\s\S]*?)<\/table>/);
    if (tableMatch) tableHtml = tableMatch[1];
  }
  if (!tableHtml) {
    const tableMatch = html.match(/<table[^>]*>([\s\S]*?)<\/table>/);
    if (tableMatch) tableHtml = tableMatch[1];
  }
  if (!tableHtml) {
    console.error(`  [!] 未找到 table: ${channelName}`);
    return results;
  }
  
  return parseRows(tableHtml, channelName, results);
}

function parseRows(tableHtml, channelName, results) {
  // 按 <tr> 分割（包括带属性的 tr）
  const rows = tableHtml.split(/<tr[^>]*>/i).slice(1);
  
  for (const row of rows) {
    const rowContent = row.split(/<\/tr>/i)[0];
    
    // 提取所有 td（非贪婪匹配，处理嵌套）
    const tds = [];
    const tdRegex = /<td[^>]*>([\s\S]*?)<\/td>/gi;
    let m;
    while ((m = tdRegex.exec(rowContent)) !== null) {
      tds.push(m[1]);
    }
    
    if (tds.length === 0) continue;
    
    // 跳过表头行：第一个 td 文本是"资源类型"或"资源名称"
    const firstTdText = stripTags(tds[0]).trim();
    if (firstTdText === '资源类型' || firstTdText === '资源名称') continue;
    
    // 判断第一个 td 是否是 rowspan 标签行（文本恰好是栏目名）
    const isLabelRow = firstTdText === channelName;
    
    // 如果是标签行且只有1个td，跳过
    if (isLabelRow && tds.length === 1) continue;
    
    let name, desc, access;
    
    if (isLabelRow && tds.length >= 4) {
      // 第一个是 rowspan 标签，取后面3个
      name = tds[1];
      desc = tds[2];
      access = tds[3];
    } else if (tds.length >= 3) {
      name = tds[0];
      desc = tds[1];
      access = tds[2];
    } else if (tds.length === 2) {
      name = tds[0];
      desc = '';
      access = tds[1];
    } else {
      continue;
    }
    
    // 提取资源名称和 URL
    const nameInfo = extractLink(name);
    const resourceName = nameInfo.text.trim();
    if (!resourceName) continue;
    
    // 提取简介
    const descText = stripTags(desc).trim();
    
    // 提取服务方式
    const accessText = stripTags(access).trim().replace(/\s+/g, ' ');
    
    results.push({
      channel: channelName,
      name: resourceName,
      url: nameInfo.url || '',
      desc: descText,
      access: accessText,
    });
  }
  
  return results;
}

function stripTags(html) {
  return html
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&middot;/g, '·')
    .replace(/&ldquo;/g, '"')
    .replace(/&rdquo;/g, '"')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/\s+/g, ' ')
    .trim();
}

function extractLink(html) {
  const linkMatch = html.match(/<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/i);
  if (linkMatch) {
    return { url: linkMatch[1], text: stripTags(linkMatch[2]) };
  }
  return { url: '', text: stripTags(html) };
}

async function main() {
  const allResults = [];
  
  for (const ch of CHANNELS) {
    const url = `https://www.tjl.tj.cn/ArticleChannel.aspx?ChannelID=${ch.id}`;
    console.log(`采集: ${ch.name} (ChannelID=${ch.id})`);
    
    try {
      const html = await fetch(url);
      const items = parseTable(html, ch.name);
      console.log(`  -> ${items.length} 条`);
      allResults.push(...items);
    } catch (e) {
      console.error(`  [!] 采集失败: ${e.message}`);
    }
  }
  
  console.log(`\n总计: ${allResults.length} 条`);
  
  // 保存
  const outPath = '/Users/yangrui/Downloads/公立图书馆电子资源/data/tjl_66.json';
  fs.writeFileSync(outPath, JSON.stringify(allResults, null, 2), 'utf-8');
  console.log(`已保存到: ${outPath}`);
  
  // 按栏目统计
  const byChannel = {};
  for (const r of allResults) {
    byChannel[r.channel] = (byChannel[r.channel] || 0) + 1;
  }
  console.log('\n栏目分布:');
  for (const [ch, count] of Object.entries(byChannel)) {
    console.log(`  ${ch}: ${count}`);
  }
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
