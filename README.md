# Picture Book Skills

自用的豆包（Doubao）Agent 技能集合，用于把绘本/分级读物整理成固定排版的 Word 文档，以及把绘本 PDF + 朗读音频合成为翻页式跟读视频。

## 技能列表

| 技能 | 作用 | 核心产物 |
|------|------|---------|
| [`picture-book-word`](./picture-book-word) | 将绘本/分级读物 PDF 整理为固定排版的 Word 文档，并按【短语短句】【句型练习】标准标注 | `.docx` |
| [`picture-book-video`](./picture-book-video) | 根据分级读物 PDF + 朗读 MP3，生成翻页式图文同步跟读视频 | `.mp4` |

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

## 说明

- 本仓库由作者自用技能整理而来，排除了技能创建向导自动生成的占位文件。
- 许可方式可自定（默认未设置 LICENSE）。
