# My Skills · 自用 Agent 技能集

自用 Agent 技能集合：把绘本/分级读物整理成固定排版的 Word 文档、合成翻页式跟读视频，以及对照台词本诊断朗读发音。

## 技能列表

| 技能 | 作用 | 核心产物 |
|------|------|---------|
| [`picture-book-word`](./picture-book-word) | 将绘本/分级读物 PDF 整理为固定排版的 Word 文档，并按【短语短句】【句型练习】标准标注 | `.docx` |
| [`picture-book-video`](./picture-book-video) | 根据分级读物 PDF + 朗读 MP3，生成翻页式图文同步跟读视频 | `.mp4` |
| [`pronunciation-correction`](./pronunciation-correction) | 对照英文台词本逐词诊断朗读发音，三个 ASR 模型投票定位真错误 | `.html`（单文件、音频内嵌） |

---

## picture-book-word

把绘本/分级读物（Heinemann、Peppa 字幕等）的正文整理成固定的 Word 排版，支持【短语短句】【句型练习】标注。

### 格式规则（验收标准）

- **标题**：带编号加粗 18pt，位于栏内顶部、不跨页
- **正文 16pt**：每句首词加粗、句号后空一格、句首字母大写
- **两栏**布局；按叙事单元分段，段间不空行
- **只保留故事主体**：删作者行、删独立拟声词行
- 【短语短句】：正文斜体+下划线+上标编号，文末保留该节（英+中一行）
- 【句型练习】：正文句型例句斜体+下划线，文末保留该节（英文一行+中文一行）
- **中文字体统一**微软雅黑（`w:eastAsia=微软雅黑`），生成后跑字体校验

### 用法

```bash
# 1. 构造输入 JSON（schema 见 SKILL.md）
# 2. 生成 docx（需 D 盘 Python 3.12，缺 python-docx 的沙箱不行）
python scripts/build_picture_book_docx.py <input.json> <output.docx>
# 3. 校验中文字体
python scripts/verify_fonts.py <output.docx>
```

依赖：`python-docx`、`PyMuPDF`（提取 PDF）。

详细规则与 JSON Schema 见 [`picture-book-word/SKILL.md`](./picture-book-word/SKILL.md)。

---

## picture-book-video

根据分级读物 PDF + 朗读 MP3，生成翻页式图文同步跟读视频。

### 核心原则

- **音频必须 100% 逐字复述绘本正文**，绝不改写、省略、重排或增补
- 禁止用 `text_to_audio_plus` 做正文配音（AI 演绎型工具会漏词）
- **唯一默认方案**：`edge-tts` 逐字多角色 TTS（微软免费，逐字合成）
- 原始 MP3 只用于"无 edge-tts 时的同步定位参考"，绝不直接当音轨，除非用户明确要求保留原声
- 所有 `said / asked / bragged / cried` 等叙述词必须朗读，一字不省

### 角色音色映射

| 角色类型 | edge-tts 音色 |
|---------|--------------|
| 旁白（沉稳中年男性） | en-US-GuyNeural |
| 年轻/自信男性（Tiger、男孩） | en-US-ChristopherNeural |
| 低沉温和男性（Elephant、爸爸） | en-US-DavisNeural |
| 清脆/明亮女声 | en-US-AriaNeural 或 en-US-JennyNeural |
| 活泼男童 | en-US-EricNeural |

### 用法

```bash
pip install edge-tts moviepy pymupdf pillow numpy
python scripts/build_video.py --pdf <input.pdf> --audio <read.mp3> --output <out.mp4>
```

详细流程（文本分组、逐句角色归属、时长分配）见 [`picture-book-video/SKILL.md`](./picture-book-video/SKILL.md)。

---

## pronunciation-correction

把一个朗读录音和它的英文台词本对齐，逐词定位**真正读错的位置**，产出一份单文件 HTML 报告：每处错误都能点听「你读的原音」，旁边并排一个「参考」播放标准 TTS 读法。给孩子的英语跟读练习用，也可以给自己纠音。

### 核心原则

- **三模型投票**：large-v3-turbo / distil-large-v3 / small.en 分别转写，再逐词强制对齐台词本；只有**三个模型全部听成别的词**的位置才算「明确听错」
- 2/3、1/3 听错的档位不进表格、不上色 —— 宁可少报也不误报，识别器自身的误判会污染结论
- 报告只有三个板块：**发音习惯改善**（按同类归纳，比单词错误重要）／**连贯朗读**／**全文标注**
- 每处错误必须配「参考」按钮：只给原音不给正确读法，等于没帮到人
- 语气词、自造词、同义替换（OK/okay）不算发音错误，自动排除

### 用法

```bash
python scripts/run_pipeline.py <台词本.docx> <录音.m4a> <工作目录>   # 解析→解码→三模型转写→对齐切片→TTS→分析
python scripts/analyze.py <工作目录>                                 # 看材料，写 curated.json
python scripts/build_html.py <工作目录> --curated <工作目录>/curated.json --out 诊断报告.html
python scripts/verify.py 诊断报告.html                               # 三档截图 + 自动朗读行为验证
```

报告是单文件，音频全部 base64 内嵌，可直接发给别人。转写是唯一瓶颈：5 分钟音频在 6 核 CPU 上约 4–5 分钟（占全流程 75% 以上）。

依赖：`faster-whisper`、`edge-tts`（唯一需要联网的一步）、`imageio-ffmpeg`、Chrome（仅验收用）。
模型目录与 ffmpeg 路径可用 `WHISPER_MODELS_DIR` / `FFMPEG_BIN` 覆盖。

`scripts/make_history.py` 会汇总各篇准确率与词尾类错误趋势（-s / -ed / -ing / -er 丢失数），用来判断某个毛病是稳定习惯、在好转、还是新出现的。

详细规则见 [`pronunciation-correction/SKILL.md`](./pronunciation-correction/SKILL.md)。

---

## 说明

- 本仓库由作者自用技能整理而来，排除了技能创建向导自动生成的占位文件。
- 许可方式可自定（默认未设置 LICENSE）。
