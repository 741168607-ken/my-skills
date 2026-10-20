#!/usr/bin/env python3
"""从既有工作目录的 words.json 生成跨录音历史档案 history.md。

用途：技能在新会话里执行时，用它做「跨录音对比」——
同一类错误是稳定习惯、在好转、还是新出现的。
"""
import json, os, sys, glob, datetime, collections, re

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
OUT = os.path.join(SKILL, "history.md")


def strip_tail(w):
    """返回 (词干, 词尾类型)。用于自动识别词尾类错误。"""
    for suf, kind in (("ed", "-ed"), ("es", "-s"), ("s", "-s"),
                      ("ing", "-ing"), ("er", "-er")):
        if w.endswith(suf) and len(w) > len(suf) + 1:
            return w[: -len(suf)], kind
    return None, None


def load(d):
    p = os.path.join(BASE, d)
    wj = os.path.join(p, "words.json")
    if not os.path.exists(wj):
        return None
    rows = json.load(open(wj, encoding="utf-8"))["rows"]
    htmls = [h for h in glob.glob(os.path.join(p, "*.html"))
             if "_verify" not in h
             and os.path.splitext(os.path.basename(h))[0].lower() != "index"]
    if htmls:
        name = os.path.splitext(os.path.basename(htmls[0]))[0]
        name = re.split(r"\s*发音诊断|\s*-\s*", name)[0].strip()
    else:
        # 回退：取台词本里出现最多的首字母大写词（多半就是篇名里的主角）
        try:
            txt = open(os.path.join(p, "script.txt"), encoding="utf-8").read()
            words = re.findall(r"(?<!^)(?<!\. )\b([A-Z][a-z]{3,})\b", txt)
            cand = collections.Counter(words).most_common(1)
            name = cand[0][0] if cand else d
        except Exception:
            name = d
        name = f"{name}（{d}）"
    mt = os.path.getmtime(os.path.join(p, "script.txt")) \
        if os.path.exists(os.path.join(p, "script.txt")) else os.path.getmtime(wj)
    lines = set(r["line"] for r in rows)
    sev = collections.Counter(r["sev"] for r in rows)
    high = [r for r in rows if r["sev"] == "high"]
    # 按词归并
    g = collections.OrderedDict()
    for r in high:
        g.setdefault(r["raw"], []).append(r)
    return {
        "dir": d, "name": name,
        "date": datetime.datetime.fromtimestamp(mt).strftime("%Y-%m-%d"),
        "words": len(rows), "lines": len(lines),
        "ok": sev.get("ok", 0), "high": len(high),
        "mid": sev.get("mid", 0), "low": sev.get("low", 0),
        "groups": g,
    }


dirs = sorted([d for d in os.listdir(BASE)
               if os.path.isdir(os.path.join(BASE, d))
               and os.path.exists(os.path.join(BASE, d, "words.json"))])
items = [x for x in (load(d) for d in dirs) if x]
items.sort(key=lambda x: x["date"])

# 一篇都没扫到时直接退出：否则会用空内容覆盖掉既有 history.md
if not items:
    sys.exit(f"在 {BASE} 下没找到含 words.json 的工作目录，未写出 {OUT}（避免覆盖既有档案）。\n"
             f"请把父目录指对——它下面应当直接是各篇的 workN 目录。")

L = []
L.append("# 历史录音档案\n")
L.append("由 `scripts/make_history.py` 从各工作目录的 `words.json` 自动提取。\n")
L.append("**新会话执行技能时先读这里**——用于跨录音对比：同一个毛病是稳定习惯、"
         "在好转、还是新出现的。\n")
L.append("只记录 `high`（三模型全错）的词，且**未经 IGNORE/STOP 过滤**，"
         "可能含语气词与虚词，写结论前自行排除。\n")

L.append("\n## 总览\n")
L.append("| 日期 | 篇名 | 句数 | 词数 | 读准 | high | 准确率 |")
L.append("|---|---|---|---|---|---|---|")
for it in items:
    acc = it["ok"] / it["words"] * 100 if it["words"] else 0
    L.append(f"| {it['date']} | {it['name']} | {it['lines']} | {it['words']} | "
             f"{it['ok']} | {it['high']} | {acc:.0f}% |")

# 词尾类错误的跨录音趋势
L.append("\n## 词尾类错误趋势\n")
L.append("自动判定：台词本词的词尾（-s / -ed / -ing / -er）在识别结果里被丢掉。\n")
L.append("| 篇名 | -s 丢失 | -ed 丢失 | -ing 丢失 | -er 丢失 |")
L.append("|---|---|---|---|---|")
trend = {}
for it in items:
    c = collections.Counter()
    for raw, occ in it["groups"].items():
        stem, kind = strip_tail(raw.lower())
        if not kind:
            continue
        heard = [h for o in occ for h in o.get("heard", []) if isinstance(h, str)]
        if heard and sum(1 for h in heard if h.lower().strip(".,!?") in
                         (stem, stem + "e", stem[:-1] or stem)) >= 1:
            c[kind] += 1
    trend[it["name"]] = c
    L.append(f"| {it['name']} | {c.get('-s', 0)} | {c.get('-ed', 0)} | "
             f"{c.get('-ing', 0)} | {c.get('-er', 0)} |")

L.append("\n## 各篇明细\n")
for it in items:
    L.append(f"\n### {it['date']} · {it['name']}  "
             f"（{it['words']} 词 / high {it['high']}）\n")
    L.append("| 台词本 | 次数 | 听起来像 |")
    L.append("|---|---|---|")
    for raw, occ in sorted(it["groups"].items(), key=lambda kv: -len(kv[1])):
        heard = []
        for o in occ:
            for h in o.get("heard", []):
                if isinstance(h, str) and h not in heard:
                    heard.append(h)
        L.append(f"| {raw} | {len(occ)} | {' / '.join(heard[:6])} |")

open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
print(f"写出 {OUT}")
print(f"收录 {len(items)} 篇：")
for it in items:
    print(f"  {it['date']}  {it['name']:<22} {it['words']:>4} 词  high {it['high']:>3}")
