#!/usr/bin/env python3
"""一条命令跑完「素材 → 可写 curated.json 的分析结果」。

用法: python run_pipeline.py <台词本.docx> <录音.m4a> <工作目录>

依次执行：
  1. prep_docx.py   docx → script.txt（只读解析，不走 MCP）
  2. ffmpeg         录音 → audio16k.wav
  3. transcribe.py  三模型转写 → asr_*.json
  4. align_words.py 对齐 + 切片 → words.json, clips/
  5. gen_tts.py     参考发音 → tts/
  6. analyze.py     输出写 curated.json 所需的全部信息

跑完后人工做两件事（这两步必须人来做，不要脚本化）：
  - 根据第 6 步的输出写 curated.json（同类归纳 + 挑整句）
  - 跑 build_html.py 出报告，再跑 verify.py 验收

每步都打印耗时，方便定位瓶颈。任一失败立即停止，不掩盖错误。
"""
import os, sys, time, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
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
    raise SystemExit("找不到 ffmpeg")


def step(name, cmd):
    print(f"\n{'='*66}\n▶ {name}\n{'='*66}", flush=True)
    t0 = time.time()
    r = subprocess.run(cmd, cwd=HERE)
    el = time.time() - t0
    if r.returncode != 0:
        raise SystemExit(f"[{name}] 失败（退出码 {r.returncode}），已停止")
    print(f"✔ {name} 完成，耗时 {el:.1f}s", flush=True)
    return el


def main():
    docx, audio, D = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(D, exist_ok=True)
    total = {}

    total["1 台词本"] = step("1/6 解析 docx → script.txt",
                            [PY, os.path.join(HERE, "prep_docx.py"), docx, D])

    wav = os.path.join(D, "audio16k.wav")
    total["2 解码"] = step("2/6 音频解码 → 16kHz 单声道",
                           [find_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
                            "-i", audio, "-ac", "1", "-ar", "16000",
                            "-c:a", "pcm_s16le", wav])

    total["3 转写"] = step("3/6 三模型转写（最慢，约 4-5 分钟）",
                           [PY, os.path.join(HERE, "transcribe.py"), D])
    total["4 对齐"] = step("4/6 逐词对齐 + 切片",
                           [PY, os.path.join(HERE, "align_words.py"), D])
    total["5 TTS"] = step("5/6 生成参考发音",
                          [PY, os.path.join(HERE, "gen_tts.py"), D])
    total["6 分析"] = step("6/6 分析（写 curated.json 看这份输出）",
                           [PY, os.path.join(HERE, "analyze.py"), D])

    print(f"\n{'='*66}\n耗时汇总\n{'='*66}")
    for k, v in total.items():
        print(f"  {k:<8} {v:7.1f}s")
    print(f"  {'合计':<8} {sum(total.values()):7.1f}s")
    print(f"\n下一步：看上面第 6 步的输出，写 {D}/curated.json")


if __name__ == "__main__":
    main()
