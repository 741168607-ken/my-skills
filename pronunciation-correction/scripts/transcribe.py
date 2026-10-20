#!/usr/bin/env python3
"""Step 1.5 — 用三个 faster-whisper 模型分别转写，产出 asr_*.json。

用法: python transcribe.py <工作目录> [--models-dir <模型目录>] [--only turbo,distil]

前提: <工作目录>/audio16k.wav 已存在（16kHz 单声道）。
      先用 ffmpeg 解码：ffmpeg -i in.m4a -ac 1 -ar 16000 -c:a pcm_s16le out.wav

绕开 PyAV 的做法：不把文件名交给 faster-whisper，而是自己读 wav 成 numpy 数组再传入，
因此不依赖 PyAV 的版本（新版 faster-whisper 的 decode_audio 在部分 PyAV 上会报
"open() got an unexpected keyword argument 'metadata_errors'"）。
"""
import json, os, sys, time, wave
import numpy as np

MODELS = [("turbo", "fw-large-v3-turbo"),
          ("distil", "fw-distil-large-v3"),
          ("small", "fw-small.en")]

# ---- 性能相关（已实测，见 SKILL.md「性能」一节）----
# BEAM: 实测 beam=1 反而更慢且结果会变（段数 32→34），必须保持 5。
BEAM = 5
# TEMPERATURE: 默认 (0.0,0.2,...,1.0) 会在解码不满意时逐级重试，是隐藏开销。
# 锁死 0.0 后逐段文本与基线**完全一致**（md5 相同），turbo 140.2s → 130.4s。
TEMPERATURE = 0.0
# THREADS: 每模型跑满逻辑核最快。实测 3 线程 159.5s > 6 线程 130.4s。
# 注意：不要并行跑多个模型——whisper 受内存带宽限制，并行 3 模型各 2 线程
# 墙钟 257s，反而比顺序 291s 只快 12%，且单模型耗时翻倍。
THREADS = os.cpu_count() or 4


def main():
    D = sys.argv[1]
    models_dir = (os.environ.get("WHISPER_MODELS_DIR")
                  or os.path.expanduser("~/.workbuddy/models"))
    if "--models-dir" in sys.argv:
        models_dir = sys.argv[sys.argv.index("--models-dir") + 1]
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))

    from faster_whisper import WhisperModel

    wav = os.path.join(D, "audio16k.wav")
    with wave.open(wav, "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if not (sr == 16000 and ch == 1 and sw == 2):
        raise SystemExit(f"需要 16kHz 单声道 16bit wav，当前 ch={ch} sw={sw} sr={sr}")
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    print(f"audio {len(audio)/sr:.2f}s")

    for tag, mname in MODELS:
        if only and tag not in only:
            continue
        mpath = os.path.join(models_dir, mname)
        if not os.path.isdir(mpath):
            print(f"跳过 {tag}：找不到模型 {mpath}")
            continue
        t0 = time.time()
        model = WhisperModel(mpath, device="cpu", compute_type="int8",
                             cpu_threads=THREADS)
        t_load = time.time() - t0
        t1 = time.time()
        segments, info = model.transcribe(audio, language="en", beam_size=BEAM,
                                          word_timestamps=True,
                                          condition_on_previous_text=False,
                                          vad_filter=False,
                                          temperature=TEMPERATURE)
        data = {"duration": info.duration, "model": mname, "segments": []}
        for seg in segments:
            data["segments"].append({
                "start": seg.start, "end": seg.end, "text": seg.text,
                "avg_logprob": seg.avg_logprob, "no_speech_prob": seg.no_speech_prob,
                "words": [{"w": w.word, "start": w.start, "end": w.end,
                           "p": w.probability} for w in (seg.words or [])],
            })
        t_tr = time.time() - t1
        out = os.path.join(D, f"asr_{tag}.json")
        json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{tag}: {len(data['segments'])} 段 | 加载 {t_load:.1f}s 转写 {t_tr:.1f}s -> {out}")


if __name__ == "__main__":
    main()
