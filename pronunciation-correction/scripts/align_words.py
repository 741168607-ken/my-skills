#!/usr/bin/env python3
"""Step 2 — 把三份 ASR 结果与台词本逐词对齐，产出 words.json + 音频切片。

用法: python align_words.py <工作目录>

输入（工作目录下）:
  script.txt              每行一句台词（已归一化，一行一句）
  audio16k.wav            16kHz 单声道 wav（ffmpeg 解码得到）
  asr_turbo.json
  asr_distil.json
  asr_small.json          三个模型的逐词结果（asr2.py 产出）

输出:
  words.json              每词的对齐状态 / 时间戳 / 三模型是否听错
  clips/w{i}.mp3          每个「非 ok」词的短切片
  clips/line{li}.mp3      每句的整句切片
"""
import json, os, re, sys, time, subprocess, unicodedata, difflib
from concurrent.futures import ThreadPoolExecutor

EQUIV = {"dr": "doctor", "mr": "mister", "mrs": "missus"}
def _ffmpeg_candidates():
    c = []
    if os.environ.get("FFMPEG_BIN"):
        c.append(os.environ["FFMPEG_BIN"])
    try:                                   # imageio-ffmpeg 自带的那份，优先用
        import imageio_ffmpeg
        c.append(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        pass
    c.append(os.path.expanduser(
        "~/.workbuddy/binaries/python/envs/default/Lib/site-packages/"
        "imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe"))
    return c


FF_CANDIDATES = _ffmpeg_candidates()


def find_ffmpeg():
    for p in FF_CANDIDATES:
        if os.path.exists(p):
            return p
    from shutil import which
    for name in ("ffmpeg", "ffmpeg.exe"):
        w = which(name)
        if w:
            return w
    raise SystemExit("找不到 ffmpeg，请先安装或修改 FF_CANDIDATES")


def norm(tok):
    t = unicodedata.normalize("NFKD", tok).lower()
    t = t.replace("\u2019", "").replace("'", "").replace("\u2018", "")
    t = re.sub(r"[^a-z]", "", t)
    return EQUIV.get(t, t) if t else None


def load_script(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    body = [l.replace("\u2019", "'").replace("\u2018", "'") for l in lines if l.strip()]
    words, per_line = [], {}
    for li, raw in enumerate(body, start=1):
        per_line[li] = []
        for m in re.finditer(r"[A-Za-z][A-Za-z'\-]*", raw):
            w = norm(m.group(0))
            if not w:
                continue
            words.append({"w": w, "raw": m.group(0), "line": li,
                          "c0": m.start(), "c1": m.end()})
            per_line[li].append(len(words) - 1)
    return words, per_line, body


def load_asr(path):
    d = json.load(open(path, encoding="utf-8"))
    out = []
    for seg in d["segments"]:
        for w in seg["words"]:
            n = norm(w["w"])
            if n:
                out.append({"w": n, "raw": w["w"].strip(),
                            "s": w["start"], "e": w["end"], "p": w["p"]})
    return out


def align(script, asr):
    a = [x["w"] for x in script]
    b = [x["w"] for x in asr]
    st = [{"state": "missing"} for _ in a]
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                st[i1 + k] = {"state": "ok", **asr[j1 + k]}
        elif tag == "replace":
            for k in range(min(i2 - i1, j2 - j1)):
                st[i1 + k] = {"state": "sub", **asr[j1 + k]}
    return st


def main():
    D = sys.argv[1]
    ff = find_ffmpeg()
    wav = os.path.join(D, "audio16k.wav")
    models = [os.path.join(D, f"asr_{n}.json") for n in ("turbo", "distil", "small")]
    models = [m for m in models if os.path.exists(m)]
    if not models:
        raise SystemExit("找不到 asr_*.json，请先跑 asr2.py")

    script, per_line, body = load_script(os.path.join(D, "script.txt"))
    aligns = {m: align(script, load_asr(m)) for m in models}

    rows = []
    for i, sw in enumerate(script):
        states = [aligns[m][i]["state"] for m in models]
        n_bad = sum(1 for s in states if s != "ok")
        heard, probs, ts = [], [], None
        for m in models:
            a = aligns[m][i]
            if a["state"] in ("ok", "sub"):
                heard.append(a["raw"])
                if a.get("p") is not None:
                    probs.append(a["p"])
                if ts is None:
                    ts = (a["s"], a["e"])
        h, seen = [], set()
        for x in heard:
            k = x.lower()
            if k not in seen:
                seen.add(k)
                h.append(x)
        diff = [x for x in h if norm(x) != sw["w"]]
        sev = "high" if n_bad == len(models) else ("mid" if n_bad == len(models) - 1
              else ("low" if n_bad >= 1 else "ok"))
        rows.append({"i": i, "line": sw["line"], "raw": sw["raw"], "w": sw["w"],
                     "c0": sw["c0"], "c1": sw["c1"],
                     "states": states, "n_bad": n_bad, "n_models": len(models),
                     "heard": h, "diff": diff,
                     "maxp": max(probs) if probs else None, "ts": ts, "sev": sev})

    last = None
    for r in rows:
        if r["ts"] is None:
            r["ts"] = last
        else:
            last = r["ts"]
    nxt = None
    for r in reversed(rows):
        if r["ts"] is None:
            r["ts"] = nxt
        else:
            nxt = r["ts"]

    json.dump({"rows": rows}, open(os.path.join(D, "words.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    clipdir = os.path.join(D, "clips")
    os.makedirs(clipdir, exist_ok=True)

    # 切片任务先全部收集，再并发执行。
    # 原来逐个 subprocess 启动 ffmpeg，174 个片段在 Windows 上光进程启动就要 ~30s；
    # 并发 6 路后降到 ~8s。输出内容与串行完全一致（同一条 ffmpeg 命令）。
    jobs = []
    for r in rows:
        if r["sev"] == "ok":
            continue
        s, e = r["ts"]
        if e - s < 0.05:
            e = s + 0.35
        jobs.append((f"w{r['i']}.mp3", s, e))
    for li in sorted(per_line):
        idxs = per_line[li]
        if idxs:
            s = min(rows[i]["ts"][0] for i in idxs)
            e = max(rows[i]["ts"][1] for i in idxs)
            jobs.append((f"line{li}.mp3", s, e))

    def clip(job):
        name, s, e = job
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", wav,
                        "-ss", f"{max(0, s - 0.12):.2f}", "-to", f"{e + 0.18:.2f}",
                        "-ac", "1", "-b:a", "48k", os.path.join(clipdir, name)], check=True)

    t0 = time.time()
    WORKERS = min(6, os.cpu_count() or 4)
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(clip, jobs))

    nh = sum(1 for r in rows if r["sev"] == "high")
    print(f"词数 {len(rows)} | 明确听错 {nh} | 切片 {len(jobs)} 个，并发 {WORKERS} 路，"
          f"耗时 {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
