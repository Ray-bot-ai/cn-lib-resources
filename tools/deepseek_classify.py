#!/usr/bin/env python3
"""用 DeepSeek 给资源出一版分类标注，再与人工标注合并。
合并原则：
  - 「史料」只听人工：人工有则保留，人工无则即便 DeepSeek 建议也不加；绝不删人工的史料。
  - 其余标签：不删人工任何标签；DeepSeek 新增的（史料除外）追加进去。
用法（在项目根目录）：
  uv run --with requests python tools/deepseek_classify.py
读取密钥自 配置.md（不入库）。粗标即可，不追求精确。
"""
import json, os, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "data", "resources.json")
CFG = os.path.join(ROOT, "配置.md")
BASE = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-v4-flash"
BATCH = 40
WORKERS = 8


def api_key():
    txt = open(CFG, encoding="utf-8").read()
    m = re.search(r"sk-[A-Za-z0-9]+", txt)
    if not m:
        sys.exit("配置.md 里没找到 sk- 开头的密钥")
    return m.group(0)


def cats(v):
    c = v.get("category") or []
    if isinstance(c, str):
        c = [c]
    return [x for x in c if isinstance(x, str) and x.strip()]


def call(key, vocab, batch):
    """batch: list of (idx, name). 返回 {idx: [tags]}"""
    lines = "\n".join(f"{i}. {name}" for i, name in batch)
    sys_p = ("你是图书馆数字资源分类助手。根据资源名称，为每个资源标注 1-3 个最贴切的类别标签。"
             "尽量从【已有类别】里选，保持一致；若都不合适，可新增一个简短类别（2-6字）。只输出 JSON，不要解释。")
    usr_p = (f"已有类别：{'、'.join(vocab)}\n\n"
             f"为下列资源标注，输出 JSON 对象（键为编号字符串，值为标签数组）：\n{lines}\n\n"
             '只输出形如 {"1":["图书"],"2":["论文","医学"]} 的 JSON。')
    body = {"model": MODEL, "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": sys_p},
                         {"role": "user", "content": usr_p}]}
    for attempt in range(3):
        try:
            r = requests.post(BASE, headers={"Authorization": "Bearer " + key},
                              json=body, timeout=90)
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            data = json.loads(content)
            return {int(k): [t for t in (v if isinstance(v, list) else [v]) if t]
                    for k, v in data.items() if str(k).isdigit()}
        except Exception as e:
            if attempt == 2:
                print(f"  批次失败(跳过): {e}")
                return {}


def main():
    key = api_key()
    reg = json.load(open(RES, encoding="utf-8"))
    ids = [k for k in reg if not k.startswith("_")]

    # 类别词表（人工现有标签，按频次降序）
    freq = {}
    for k in ids:
        for t in cats(reg[k]):
            freq[t] = freq.get(t, 0) + 1
    vocab = sorted(freq, key=lambda t: -freq[t])
    print(f"读取到 {len(vocab)} 个人工类别；对 {len(ids)} 个资源做 DeepSeek 标注…")

    # 分批
    batches = []
    for s in range(0, len(ids), BATCH):
        chunk = ids[s:s + BATCH]
        batches.append([(j + 1, reg[cid]["name"]) for j, cid in enumerate(chunk)])
    cid_by_batch = [ids[s:s + BATCH] for s in range(0, len(ids), BATCH)]

    ds_tags = {}   # cid -> [tags]
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(call, key, vocab, b): bi for bi, b in enumerate(batches)}
        for fut in as_completed(futs):
            bi = futs[fut]
            res = fut.result()
            for local_idx, tags in res.items():
                if 1 <= local_idx <= len(cid_by_batch[bi]):
                    ds_tags[cid_by_batch[bi][local_idx - 1]] = tags
            done += 1
            if done % 5 == 0 or done == len(batches):
                print(f"  完成 {done}/{len(batches)} 批")

    # 合并
    added_tags = 0
    filled = 0
    new_labels = {}
    for cid in ids:
        orig = cats(reg[cid])
        was_empty = not orig
        final = list(orig)
        for t in ds_tags.get(cid, []):
            if t == "史料":          # 史料 只听人工
                continue
            if t not in final:
                final.append(t)
                added_tags += 1
                new_labels[t] = new_labels.get(t, 0) + 1
        if was_empty and final:
            filled += 1
        reg[cid]["category"] = final

    json.dump(reg, open(RES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n合并完成：新增标签引用 {added_tags} 次；原来无标签、现补上 {filled} 个。")
    print("DeepSeek 新增最多的标签：",
          "、".join(f"{t}×{n}" for t, n in sorted(new_labels.items(), key=lambda x: -x[1])[:15]))
    print("（史料未被 DeepSeek 增删，完全保留人工标注）")


if __name__ == "__main__":
    main()
