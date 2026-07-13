#!/usr/bin/env python3
"""归一化：读 data/libraries/*.json，给每条资源分配 canonical_id（同一资源合并），
并生成/更新 data/resources.json 资源总目录。
规则：
- 去掉表示“同一产品不同镜像/形态”的后缀标签（镜像/包库/试用/开放获取/OA…）后，同名者合并为一个资源。
- 不同名（如 CNKI 的不同子库）保持独立。
- canonical_id 用清洗后名称的稳定短哈希，跨馆一致。
这是“第一遍自动归一化”，镜像合并/范围拆分的边界仍需人工抽查校正。
用法： python3 normalize.py
"""
import json, glob, os, re, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(ROOT, "data", "libraries")
RES = os.path.join(ROOT, "data", "resources.json")

# 括号内若仅由这些词构成，视为“同一产品的形态标签”，清洗时去掉
TAGS = ["镜像", "包库", "本地镜像", "远程", "远程访问", "试用", "开放获取", "OA", "公众版", "包库版", "镜像版"]
BRACKETS = [("（", "）"), ("(", ")"), ("【", "】"), ("[", "]")]


def clean_name(name):
    s = name.strip()
    changed = True
    while changed:
        changed = False
        for lb, rb in BRACKETS:
            m = re.search(re.escape(lb) + r"([^" + re.escape(lb + rb) + r"]*)" + re.escape(rb), s)
            if m and any(t in m.group(1) for t in TAGS) and len(m.group(1)) <= 8:
                s = (s[:m.start()] + s[m.end():]).strip()
                changed = True
    return re.sub(r"\s+", " ", s).strip()


def cid(cleaned):
    h = hashlib.md5(cleaned.encode("utf-8")).hexdigest()[:8]
    return "r-" + h


def main():
    registry = {}
    if os.path.exists(RES):
        try:
            registry = {k: v for k, v in json.load(open(RES, encoding="utf-8")).items()
                        if not k.startswith("_")}
        except Exception:
            registry = {}

    lib_files = [p for p in glob.glob(os.path.join(LIB, "*.json"))
                 if not os.path.basename(p).startswith("_")]
    merged = 0
    used = set()
    for path in lib_files:
        data = json.load(open(path, encoding="utf-8"))
        for r in data.get("resources", []):
            cleaned = clean_name(r.get("raw_name", ""))
            if not cleaned:
                continue
            cid_ = cid(cleaned)
            r["canonical_id"] = cid_
            used.add(cid_)
            if cid_ not in registry:
                registry[cid_] = {"name": cleaned, "vendor": "", "category": "",
                                  "homepage": "", "aliases": [], "notes": ""}
            else:
                merged += 1
                al = registry[cid_].setdefault("aliases", [])
                rn = r.get("raw_name", "")
                if rn and rn != registry[cid_]["name"] and rn not in al:
                    al.append(rn)
        json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 清理无任何图书馆引用的孤儿条目（多因资源改名后旧 canonical_id 残留）
    orphans = [k for k in registry if k not in used]
    for k in orphans:
        del registry[k]

    out = {"_说明": "资源总目录，由 normalize.py 自动生成/更新；vendor/category 可人工补充。"}
    out.update(dict(sorted(registry.items(), key=lambda kv: kv[1]["name"])))
    json.dump(out, open(RES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"归一化完成：{len(lib_files)} 个馆，资源总目录 {len(registry)} 个唯一资源，"
          f"合并/复用 {merged} 次引用，清理孤儿 {len(orphans)} 个。")


if __name__ == "__main__":
    main()
