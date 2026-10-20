#!/usr/bin/env python3
"""Step 3 — 生成「参考发音」音频（标准英语 TTS）。

用法: python gen_tts.py <工作目录> [--voice en-US-AriaNeural] [--then-report]

产出:
  tts/line{i}.mp3              每句台词的标准读法（整句参考发音）
  tts/words/<slug>.mp3         每个「明确听错」词的标准读法（单词参考发音）

注意: edge-tts 首次调用经常返回 503（WSServerHandshakeError），属服务端限流，
脚本已内置重试，通常第二次即成功。
"""
import asyncio, json, os, re, sys

VOICE = "en-US-AriaNeural"
RATE_SENT = "+0%"
RATE_WORD = "-15%"


def slug(s):
    t = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return t or "x"


def clean(t):
    t = re.sub(r"[~]+", " ", t)
    t = re.sub(r"\.(?=[A-Z])", ". ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def main():
    D = sys.argv[1]
    voice = VOICE
    if "--voice" in sys.argv:
        voice = sys.argv[sys.argv.index("--voice") + 1]

    import edge_tts

    lines = [l.strip() for l in open(os.path.join(D, "script.txt"), encoding="utf-8") if l.strip()]
    sdir = os.path.join(D, "tts")
    wdir = os.path.join(sdir, "words")
    os.makedirs(wdir, exist_ok=True)

    rows = json.load(open(os.path.join(D, "words.json"), encoding="utf-8"))["rows"]
    high = [r for r in rows if r["sev"] == "high"]
    words = []
    seen = set()
    for r in high:
        k = slug(r["raw"])
        if k not in seen:
            seen.add(k)
            words.append((k, r["raw"]))

    async def one(text, path, rate, sem):
        if os.path.exists(path) and os.path.getsize(path) > 400:
            return "skip"
        async with sem:
            for attempt in range(6):
                try:
                    await edge_tts.Communicate(text, voice, rate=rate).save(path)
                    if os.path.getsize(path) > 400:
                        return "ok"
                except Exception:
                    await asyncio.sleep(1.2 * (attempt + 1))
        return "FAIL"

    async def run():
        # 并发 6（原为 4）。edge-tts 是网络 IO 密集型，CPU 不是瓶颈；
        # 遇到 503 限流由 one() 里的 6 次重试兜底，实测 51 句 + 44 词约 30s。
        sem = asyncio.Semaphore(6)
        jobs = []
        for i, t in enumerate(lines, 1):
            jobs.append(one(clean(t), os.path.join(sdir, f"line{i}.mp3"), RATE_SENT, sem))
        for k, raw in words:
            jobs.append(one(clean(raw), os.path.join(wdir, f"{k}.mp3"), RATE_WORD, sem))
        return await asyncio.gather(*jobs)

    res = asyncio.run(run())
    from collections import Counter
    print("句子", len(lines), "单词", len(words), Counter(res))
    if "FAIL" in res:
        print("有失败项，重跑一次即可（服务端限流）")


if __name__ == "__main__":
    main()
