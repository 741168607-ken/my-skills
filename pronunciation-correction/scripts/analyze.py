#!/usr/bin/env python3
"""一站式分析：跑完 align_words.py 后一次输出写 curated.json 所需的全部信息。

用法: python analyze.py <工作目录>

输出：
  1. 概要（词数 / 明确听错 / 问题句）
  2. 明确听错明细
  3. 按词频归并（多次出错的词 → patterns 候选）
  4. 按行统计
  5. 句子时间轴（标出大间隔）
  6. 【自动检测】整段一带而过（≥3 相邻词 missing 且时间戳相同）
  7. 错误数 ≥2 的句子的三模型 ASR 原文（写 sentences 用）
  8. TTS 覆盖检查
"""
import json, os, re, sys, collections

IGNORE = {"oh", "ooh", "ah", "ha", "ho", "woo", "mow", "er", "mm", "mmm",
          "wow", "hmm", "huh", "shh", "ahem", "oops", "yay", "hey",
          "ohoh", "aha", "haha", "oho", "eek", "ugh", "phew", "tsk"}


def slug(s):
    t = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return t or "x"


def main():
    D = sys.argv[1]
    rows = json.load(open(os.path.join(D, "words.json"), encoding="utf-8"))["rows"]
    lines = [l for l in open(os.path.join(D, "script.txt"), encoding="utf-8").read().splitlines() if l.strip()]
    high_all = [r for r in rows if r["sev"] == "high"]
    high = [r for r in high_all if r["w"] not in IGNORE]

    print("=" * 70)
    print(f"概要：台词 {len(lines)} 句 / 词 {len(rows)} | 明确听错 {len(high)}"
          f"（过滤语气词 {len(high_all)-len(high)}）")

    line_high = collections.Counter(r["line"] for r in high)
    print(f"      问题句 {len(line_high)}/{len(lines)}")

    print("\n" + "=" * 70)
    print("一、明确听错明细")
    print("-" * 70)
    for r in high:
        h = " / ".join(r["heard"]) or "漏读"
        print(f'  {r["i"]:>3} L{r["line"]:<2} {r["raw"]:<14} -> {h}')

    print("\n" + "=" * 70)
    print("二、按词频归并（patterns 候选，≥2 次的优先）")
    print("-" * 70)
    c = collections.Counter(r["w"] for r in high)
    for w, n in c.most_common():
        if n < 2:
            continue
        occ = [r for r in high if r["w"] == w]
        print(f"  {w} × {n}  (raw={occ[0]['raw']})")
        for r in occ:
            print(f'      L{r["line"]:<2} -> {" / ".join(r["heard"]) or "漏读"}')
    singles = [w for w, n in c.most_common() if n == 1]
    print(f"  【只错一次的】{', '.join(singles)}")

    print("\n" + "=" * 70)
    print("三、按行统计（错误数降序）")
    print("-" * 70)
    for li, n in sorted(line_high.items(), key=lambda x: (-x[1], x[0])):
        print(f"  L{li:<2} ×{n}  {lines[li-1][:60]}")

    print("\n" + "=" * 70)
    print("四、句子时间轴（gap>1.5s 标出）")
    print("-" * 70)
    by_line = collections.defaultdict(list)
    for r in rows:
        by_line[r["line"]].append(r)
    prev_e = 0.0
    for li in sorted(by_line):
        g = by_line[li]
        ts = [x["ts"] for x in g if x["ts"]]
        s = min(x[0] for x in ts)
        e = max(x[1] for x in ts)
        gap = s - prev_e
        flag = "   <<< 间隔大" if gap > 1.5 else ""
        print(f"  L{li:<2} {s:6.2f}-{e:6.2f} gap={gap:5.2f}{flag}")
        prev_e = e

    print("\n" + "=" * 70)
    print("五、【自动检测】整段一带而过")
    print("-" * 70)
    # 判据：≥3 个相邻词同时 missing（states 全 missing）且 ts 完全相同
    runs = []
    cur = []
    for r in rows:
        if all(st == "missing" for st in r["states"]):
            cur.append(r)
        else:
            if len(cur) >= 3:
                runs.append(cur)
            cur = []
    if len(cur) >= 3:
        runs.append(cur)
    if not runs:
        print("  未检测到（没有 ≥3 词连续 missing 的段落）")
    for run in runs:
        tss = {tuple(x["ts"]) for x in run if x["ts"]}
        li = run[0]["line"]
        print(f"  ⚠ L{li} 第 {run[0]['i']}-{run[-1]['i']} 词共 {len(run)} 个连续 missing，"
              f"时间戳{'相同' if len(tss) == 1 else '不同'}")
        print(f'      台词: {lines[li-1]}')
        print(f'      词: {" ".join(x["raw"] for x in run)}')
        print("      → 判定为【整段带过】，写进 sentences（连贯朗读），不要进 patterns")

    print("\n" + "=" * 70)
    print("六、错误数 ≥2 的句子：三模型 ASR 原文（写 sentences 的 heard 用）")
    print("-" * 70)
    seg_by_model = {}
    for tag in ("turbo", "distil", "small"):
        p = os.path.join(D, f"asr_{tag}.json")
        if os.path.exists(p):
            seg_by_model[tag] = json.load(open(p, encoding="utf-8"))["segments"]

    def asr_text_in(tag, s, e):
        buf = []
        for seg in seg_by_model.get(tag, []):
            if seg["end"] > s - 0.6 and seg["start"] < e + 0.6:
                buf.append(seg["text"])
        return " ".join(buf).strip()

    for li, n in sorted(line_high.items(), key=lambda x: (-x[1], x[0])):
        if n < 2:
            continue
        g = by_line[li]
        ts = [x["ts"] for x in g if x["ts"]]
        s, e = min(x[0] for x in ts), max(x[1] for x in ts)
        print(f'\n  L{li} ({n}处) [{s:.1f}-{e:.1f}]')
        print(f'     台词: {lines[li-1]}')
        for tag in ("turbo", "distil", "small"):
            print(f"     {tag:<7}: {asr_text_in(tag, s, e)}")

    print("\n" + "=" * 70)
    print("七、TTS 覆盖检查")
    print("-" * 70)
    wdir = os.path.join(D, "tts", "words")
    have = set(os.listdir(wdir)) if os.path.isdir(wdir) else set()
    need = {}
    for r in high:
        need.setdefault(r["w"], r["raw"])
    miss = [raw for w, raw in need.items() if f"{slug(raw)}.mp3" not in have]
    print(f"  已有 {len(have)} 个单词 TTS，需要 {len(need)} 个")
    print(f"  缺失: {miss if miss else '无'}")


if __name__ == "__main__":
    main()
