#!/usr/bin/env python3
"""把 sources/ 里的规则源编译成各客户端能直接订阅的格式，输出到 rules/。

sources/*.yaml  = v2fly/domain-list-community 上游 + 自己补的域名
sources/*.list  = 手写的 classical 规则，原样转换格式
"""
import json
import pathlib
import re
import sys
import urllib.request

import yaml

ROOT = pathlib.Path(__file__).resolve().parent
SRC, OUT = ROOT / "sources", ROOT / "rules"
V2FLY = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/{}"


def fetch_v2fly(name, seen=None):
    """返回 [(type, value)]，type ∈ suffix/full/keyword。递归展开 include:，跳过 regexp 和 @cn 条目。"""
    seen = seen if seen is not None else set()
    if name in seen:
        return []
    seen.add(name)
    with urllib.request.urlopen(V2FLY.format(name), timeout=30) as r:
        text = r.read().decode()
    out = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        attrs = re.findall(r"@(\S+)", line)
        line = re.sub(r"\s*@\S+", "", line).strip()
        if "cn" in attrs:
            continue
        if line.startswith("include:"):
            out += fetch_v2fly(line[len("include:"):].strip(), seen)
        elif line.startswith("full:"):
            out.append(("full", line[5:]))
        elif line.startswith("keyword:"):
            out.append(("keyword", line[8:]))
        elif line.startswith("regexp:"):
            continue
        else:
            out.append(("suffix", line.removeprefix("domain:")))
    return out


def parse_classical(path):
    kind = {"DOMAIN-SUFFIX": "suffix", "DOMAIN": "full", "DOMAIN-KEYWORD": "keyword"}
    out = []
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        t, _, v = line.partition(",")
        if t in kind:
            out.append((kind[t], v.split(",")[0].strip()))
        else:
            sys.exit(f"{path.name}: 不支持的规则类型 {line}")
    return out


def normalize(entries):
    entries = {(t, v.lower().strip(".")) for t, v in entries if v}
    suffixes = {v for t, v in entries if t == "suffix"}

    def covered(v):  # 已被更短的 suffix 覆盖
        parts = v.split(".")
        return any(".".join(parts[i:]) in suffixes for i in range(1, len(parts) - 1))

    kept = [(t, v) for t, v in entries if t == "keyword" or not covered(v)]
    # full 已被同名 suffix 覆盖的也去掉
    kept = [(t, v) for t, v in kept if not (t == "full" and v in suffixes)]
    order = {"suffix": 0, "full": 1, "keyword": 2}
    return sorted(kept, key=lambda x: (order[x[0]], x[1]))


def write(name, desc, entries):
    cls = {"suffix": "DOMAIN-SUFFIX", "full": "DOMAIN", "keyword": "DOMAIN-KEYWORD"}
    head = f"# {name}: {desc}\n# 自动生成，勿手改。源：sources/ ；共 {len(entries)} 条\n"
    lines = [f"{cls[t]},{v}" for t, v in entries]
    (OUT / f"{name}.list").write_text(head + "\n".join(lines) + "\n")
    (OUT / f"{name}.yaml").write_text(head + "payload:\n" + "".join(f"  - {l}\n" for l in lines))
    rule = {}
    for t, key in (("suffix", "domain_suffix"), ("full", "domain"), ("keyword", "domain_keyword")):
        vals = [v for tt, v in entries if tt == t]
        if vals:
            rule[key] = vals
    (OUT / f"{name}.json").write_text(json.dumps({"version": 2, "rules": [rule]}, indent=2) + "\n")
    # mihomo domain 行为格式（+.后缀 / 完整域名），可再转 .mrs；关键词规则这个格式表达不了，有关键词就不出
    if not any(t == "keyword" for t, _ in entries):
        dom = [("+." + v) if t == "suffix" else v for t, v in entries]
        (OUT / f"{name}.domain.txt").write_text("\n".join(dom) + "\n")
    print(f"{name}: {len(entries)}")


def main():
    OUT.mkdir(exist_ok=True)
    for p in sorted(SRC.glob("*.yaml")):
        cfg = yaml.safe_load(p.read_text())
        entries = []
        for up in cfg.get("upstream", []):
            entries += fetch_v2fly(up)
        for t in ("suffix", "full", "keyword"):
            entries += [(t, v) for v in (cfg.get("extra", {}) or {}).get(t, []) or []]
        write(cfg["name"], cfg.get("description", ""), normalize(entries))
    for p in sorted(SRC.glob("*.list")):
        first = p.read_text().splitlines()[0].lstrip("# ").strip()
        write(p.stem, first, normalize(parse_classical(p)))


if __name__ == "__main__":
    main()
