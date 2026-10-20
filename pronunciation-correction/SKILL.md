---
name: pronunciation-correction
display_name: 发音纠错
display_name_en: Pronunciation Correction
description: 对比朗读音频与台词本，逐词定位「读错的发音」并生成可试听的 HTML 诊断报告。当用户说"分析发音 / 哪些发音不正确 / 发音哪里有问题 / 朗读纠音 / 口语纠音 / 跟读检查 / 对比台词本看看读错了什么 / 这段录音哪里读错了 / 纠音报告"时使用。做法：三个语音识别模型分别转写录音，再与台词本逐词强制对齐，把被稳定听成别的词的发音点找出来；每处错误都能点击试听「你读的原音」，并并排一个「参考发音」按钮播放标准 TTS 读法，逐词、逐句都有。默认只输出「三个模型全部听错」的最高置信度问题。
description_zh: 对比朗读音频与台词本，逐词定位「读错的发音」并生成可试听的 HTML 诊断报告。当用户说"分析发音 / 哪些发音不正确 / 发音哪里有问题 / 朗读纠音 / 口语纠音 / 跟读检查 / 对比台词本看看读错了什么 / 这段录音哪里读错了 / 纠音报告"时使用。做法：三个语音识别模型分别转写录音，再与台词本逐词强制对齐，把被稳定听成别的词的发音点找出来；每处错误都能点击试听「你读的原音」，并并排一个「参考发音」按钮播放标准 TTS 读法，逐词、逐句都有。默认只输出「三个模型全部听错」的最高置信度问题。
description_en: Compare a read-aloud recording against its script, locate mispronounced words word-by-word, and produce a self-contained HTML report where every error has a playable "your recording" clip and a paired "reference pronunciation" TTS clip. Three ASR models transcribe independently, then a forced word-level alignment against the script flags words that were stably heard as a different word. Only the highest-confidence tier (all three models wrong) is shown by default.
category: 教育学习
version: 1.0.0
author: workbuddy
agent_created: true
---

# 发音纠错（朗读音频 × 台词本 → 逐词诊断报告）

把一个朗读录音和它的台词本对齐，找出**哪些词的发音明显不对**，产出一份单文件 HTML：
每个错误位置都能一听「原音」、再听「标准读法」，用来孩子练口语 / 自己纠音。

## 硬性规则（任何情况下都不要违反）

1. **只显示、只标注「明确听错」**（三个模型全部听错的词）。
   中间档（2/3）和存疑档（1/3）不进入表格，也不在全文里上色。
   理由：识别器自身的误判会污染结论，宁可少报也不要误报。
2. **凡是出现「错误发音」按钮的地方，旁边必须有「参考」按钮。**
   **所有参考按钮一律叫「参考」**，不再出现「参考发音」；
   词/句用 `▶ 原声` 配 `✓ 参考`，全文标注里整句按钮叫 `▶ 原句` 配 `✓ 参考`。
   不能只有错误音频而没有标准读法 —— 那样用户不知道正确的是什么。
   按钮文案统一叫 **参考**，不要写「正确」。
3. **同一个词多次出错时用大括号归并。** 一个词出现 N 次、每次听成不同东西，
   用大括号把 N 条错误括在一起，**只在汇总处放一个** `✓ 参考`，不要每行都放。
   只出现一次的才用「单词 + 原声 + 参考」的单行卡片。
4. **页面顶部不放统计汇总**（不要词数 / 句数 / 错误数那些数字卡片）。
5. **不显示「不算错的差异」章节。**
6. **全文标注只列出「含明确听错词」的句子**，没问题的句子整句不出现。
7. **忽略语气词、象声词与同义替换**。`build_html.py` 的 `IGNORE` 集合分两类：
   - 语气词/象声词（Oh / Ooh / Ah / Ho / Woo / POP …）—— 识别器必然听错
   - 同义替换（`ok / okay / bye / lots / lot`）—— 发音完全相同、只是拼写不同，
     识别器必然二选一，**永远不可能是发音错误**（实测 `OK → okay` 三个模型全错，
     但它就是同一个音）
8. **「发音习惯改善」每行只放一个归总块**（单列 `.grow`），块内横排：
   `单词 → ✓参考（垂直居中，位于大括号正前方）→ 大括号 → 错误列表`，
   每行错误里的 `▶ 原声` **右对齐**。单词列用 `min-width:104px` 让各行的
   ✓参考、大括号在同一竖线上对齐。只有一个错误时不出大括号。
9. **三个章节标题后都要有「▶ 自动朗读」和「■ 取消」按钮**（见下）。
10. **页面底部不放图例 / 提示条**，正文里也不放大段说明。
11. **常用虚词不单独占一行**：全文标注里，如果一句的错误词<b>全部</b>落在 `STOP` 表
    （`I / am / the / it / a / are / you / not / he / she / say / did / said / but`）里，
    整句不显示；只要还有一个表外的错词，这句照常显示，表内词也照常标红。
    这张表在 `build_html.py` 顶部，可增删。
12. **报告只有三个板块**：一、发音习惯改善 ／ 二、连贯朗读 ／ 三、全文标注。
    不再输出「识别器不可靠的位置」，编号固定为一/二/三。
13. **样式只用「胶囊简约风」**（`assets/theme-mac.css`）：浅灰底、白色圆角卡片、
    胶囊按钮、绿色点缀。Minecraft 版已归档（`theme-minecraft.css` / `scene-minecraft.svg`），
    `build_html.py` 不再产出。

## 章节名称

- 一、**发音习惯改善**
- 二、**连贯朗读**
- 三、**全文标注**（标题后的序号按实际显示条数从 1 连续编，不沿用台词本原行号）

## 自动朗读

三个章节标题右侧依次是：**两个圆形单选**「仅参考 / 原音+参考」（默认后者）→「▶ 自动朗读」→「■ 取消」。

两种模式：

- **原音+参考**：每条依次播放 `你读的原音 → 停顿 0.3s → 叮～ → 参考发音`
- **仅参考**：只挨个播放每条的正确读法，不放原音、也不放叮声

节奏（毫秒）：

| 位置 | 停顿 |
|---|---|
| 同一条内相邻两个错误原音之间 | 300 |
| 最后一个错误原音 → 叮 | 300 |
| 叮 → 参考发音 | 160 |
| 相邻两条之间 | 200 |

播放中的条目加 `.auto-on` 高亮并自动滚到屏幕中间，正在播放的按钮加 `.lit`；
全部走完自动清理状态。点「取消」随时中断并恢复原状。

DOM 契约（`build_html.py` 生成，改样式时不要破坏）：

| 标记 | 含义 |
|---|---|
| `.sec` + `id="sec1/2/3"` | 三个章节容器 |
| `.playitem` | 一个可朗读条目（词块 / 表格行 / 句子行） |
| `[data-wrong]` | 该条目里「你读的原声」按钮，可多个（分组内每次错误一个） |
| `[data-ref-btn]` | 该条目唯一的参考按钮（全文标注里文案是「✓ 参考」） |
| `[data-auto="secN"]` / `[data-cancel="secN"]` | 章节标题上的两个按钮 |
| `input[name="mode-secN"]` | 朗读模式单选，`value="both"`（默认）/ `value="ref"` |

「叮～」是自己合成的一段提示音 `assets/ding.mp3`（1568Hz + 3132Hz 两个正弦叠加、
指数衰减），`build_html.py` 读成 base64 内联成 `DING` 常量，离线可用。

**实现要点**：用 `token` 自增做取消令牌。`run()` 开头先 `resetAll()`（token++），
之后每个 `await` 前都检查 `t !== token` 就立刻 `return` —— 这样「取消」能立即打断，
不会出现上一轮还在播、下一轮又开始的叠音。

**怎么验证真的能跑**（不要只看截图，截图看不出 JS 行为）：复制一份 HTML，注入假的
`window.Audio`（`play()` 里 `setTimeout` 立刻触发 `onended`），在 load 时调用
`run('sec1')`，然后 `--dump-dom` 检查状态：

```bash
chrome --headless=new --virtual-time-budget=15000 --dump-dom test.html
# 期望：active 按钮出现、auto-on 只落在一处、跑完自动清零
```
假 Audio 在 `play()` 里 `push(this._src.length)`，就能核对播放序列是不是
「错误音 → 叮（base64 长度约 5.5KB）→ 参考音」。

## 会话管理（控制用量的关键）

**每做一篇报告，开一个新会话。** 技能已调好且自包含，续用旧会话不会更快，只会更贵：
消耗 ≈ 轮次 × 单轮上下文，而单轮上下文随会话历史线性膨胀。实测同一会话连做几篇后，
单轮上下文从 43K 涨到 107 万，同样一篇报告的用量涨约 20 倍（3.8M → 211M）。

新会话开场用这一句就够：

    @<台词本.docx> @<录音.m4a> @skill:"C:\Users\TUF\.workbuddy\skills\pronunciation-correction\SKILL.md"
    按技能流程生成发音诊断报告，工作目录用 <你的工作区>/workN，
    交付到素材所在目录。

调优、benchmark、反复试参数这类探索性任务另开会话，别和交付混在一起。

### 跨录音对比：先读 `history.md`

新会话看不到之前几篇的结论，所以本技能维护一份 `history.md`（`make_history.py`
自动从各工作目录的 `words.json` 提取，含总览、词尾类错误趋势、各篇明细）。

**写结论前先读它**，才能说出「这是稳定习惯 / 在好转 / 新出现」，而不是只报本次的词表。
这是本技能最有价值的部分——家长要知道的是趋势，不是单次的错误清单。

新报告出来后更新档案：
`python scripts/make_history.py <工作目录的父目录>`

## 流程

### 一条命令跑完前六步

```bash
python scripts/run_pipeline.py <台词本.docx> <录音.m4a> <工作目录>
```

依次执行 prep_docx → ffmpeg 解码 → 三模型转写 → 对齐切片 → TTS → 分析，
每步打印耗时，任一失败立即停止。跑完后只剩**两件必须人做的事**：

1. 看第 6 步 `analyze.py` 的输出，写 `curated.json`（同类归纳 + 挑整句）
2. `build_html.py` 出报告，再 `verify.py` 验收

**不要跳过第 1 步去看原始 `words.json`** —— `analyze.py` 已经把「明细 / 词频归并 /
按行统计 / 时间轴 / 整段漏读自动检测 / 三模型原文 / TTS 覆盖」七件事一次做完，
它输出的就是写 `curated.json` 需要的全部材料。

### 工作目录约定 `<work>/`：

```
<work>/
  script.txt        每行一句台词（一行一句，别按原始换行切）
  audio16k.wav      16kHz 单声道 16bit
  asr_turbo.json / asr_distil.json / asr_small.json
  words.json        对齐结果
  clips/            w{i}.mp3 单词切片、line{li}.mp3 整句切片
  tts/              line{li}.mp3 整句参考发音、words/<slug>.mp3 单词参考发音
  curated.json      人工分组与解说（可选）
  诊断报告.html
  _verify/          verify.py 的验收产物（截图/分节页/测试页，交付前可删）
```

脚本一览（都在 `scripts/`）：

| 脚本 | 作用 |
|---|---|
| `run_pipeline.py` | **入口**：一条命令跑完 1–6 步 |
| `prep_docx.py` | docx → `script.txt`（只读解析 `document.xml`，不走 MCP） |
| `transcribe.py` | 三模型转写 → `asr_*.json` |
| `align_words.py` | 逐词对齐 + 并发切片 → `words.json`、`clips/` |
| `gen_tts.py` | 参考发音 → `tts/` |
| `analyze.py` | 输出写 `curated.json` 的全部材料（含整段漏读自动检测） |
| `build_html.py` | 出单文件报告 |
| `verify.py` | 三档截图 + JS 行为验证 |
| `make_history.py` | 从各 `words.json` 生成 `history.md`，供跨录音对比 |

### 1. 准备台词本

> **首选 `prep_docx.py`**（`run_pipeline.py` 已自动调用），1.5 秒出 `script.txt`。
> 下面这段 MCP 流程只在需要看段落结构、或 docx 格式异常时才用。

- `.docx` 按 Office 路由读（`workbuddy-office-routing` → `workbuddy-local-office-edit`，
  `open_file` + `doc_resolve_document_structure mode=compact text_preview_length=200 limit=0`，
  读完 `close_file`）。段落常被软换行切碎，要 join 后再按句号重分句。
  **注意 `text_preview` 上限 200 字**，长段落会被截断，且用 `doc_find` 的 `related_text`
  补全时会丢空格（`lookeda little`）。要精确原文就只读解析 `word/document.xml`
  （`zipfile` + `ElementTree`，取 `w:t` 文本），不要依赖 MCP 预览。
- **重分句时保护 `Mr. / Mrs. / Dr.`**，否则会被当成句末。
- **断句正则必须容许句末标点后跟一个收尾引号**：

  ```
  [.!?…]["']?(?=\s|$)          # 正确
  (?<=[.!?])\s+                 # 错误：会把 "…squirrels!" Nana said. 切成两句
  ```

  用错会得到「引号开在句首、闭在下一句」的乱局（同一篇被切成 42 句而不是 51 句），
  后面 TTS 整句参考音也跟着错。切完**数一下行数、抽查含引号的行**再往下走。
- `.doc` 扩展名**不等于**旧二进制格式。先看文件头四个字节再决定怎么处理：

  ```python
  b = open(path,'rb').read(8)
  PK\x03\x04        → ZIP 包，就是 docx，prep_docx.py 直接能读
  d0cf11e0          → OLE 复合文档，真旧格式 .doc（需 Word/LibreOffice 转，
                      本机没装，这种情况只能走 MCP 读）
  {\rtf             → RTF
  ```

  实测 `80 The Boss.doc` 虽挂 `.doc`，实为 ZIP/docx，`prep_docx.py` 照读不误。
  **别因为扩展名是 .doc 就去装转换器**，先花 3 秒看文件头。
- 统一写成 `script.txt`，**一行一句**。TTS 按行读，句子切得干净参考发音才自然。
- 拿到台词本先**通读一遍再往下跑**：脚本自检只能发现引号不成对，发现不了
  「句子被从中间劈开」这类语义问题。看一眼只要 10 秒，跑完再返工要几分钟。

### 2. 解码

```bash
ffmpeg -i input.m4a -ac 1 -ar 16000 -c:a pcm_s16le <work>/audio16k.wav
```

ffmpeg 可用 `imageio-ffmpeg` 自带的那份，无需系统安装。

### 3. 转写（三个模型）

```bash
python scripts/transcribe.py <work>
```

产出 `asr_turbo.json / asr_distil.json / asr_small.json`。
模型默认在 `~/.workbuddy/models/`（可用环境变量 `WHISPER_MODELS_DIR` 覆盖）：`fw-large-v3-turbo`、`fw-distil-large-v3`、`fw-small.en`。

**这一步约 4.5 分钟，是全流程唯一的大头，属正常**。参数已调到实测最优
（`temperature=0.0`、`beam_size=5`、线程=逻辑核数），别再自己改——见「性能」一节。
可用 `--only turbo,small` 先跑两个模型快速看结果。

### 4. 对齐 + 切片

```bash
python scripts/align_words.py <work>
```

逐词对齐台词本与三份转写结果，产出 `words.json` 和音频切片（切片并发 6 路，约 9s）。
`sev` 字段：`high` = 三个模型全错，`mid` = 两个，`low` = 一个，`ok` = 都对。

### 5. 参考发音 TTS

```bash
python scripts/gen_tts.py <work>
```

用 edge-tts（`en-US-AriaNeural`）生成整句和单词的标准读法。单词用 `-15%` 语速方便跟读。
已存在且非空的文件会跳过，所以重跑很便宜。

### 5.5 分析（写 curated.json 前必看）

```bash
python scripts/analyze.py <work>
```

一次输出七块内容：概要、明确听错明细、按词频归并、按行统计、时间轴、
**整段漏读自动检测**、错误数 ≥2 的句子的三模型原文、TTS 覆盖检查。
它就是写 `curated.json` 的全部素材，不用再去翻 `words.json`。

### 6. 出报告

```bash
python scripts/build_html.py <work> --curated <work>/curated.json --out "诊断报告.html"
```

`curated.json` 是可选的，用来放人工分组和解说：

```json
{
  "title": "…", "subtitle": "…",
  "patterns":  [{"title": "…", "desc": "…", "words": ["said", "web"]}],
  "sentences": [{"line": 74, "script": "…", "heard": "…", "note": "…"}]
}
```

`notes`（不算错的差异）和 `unsure`（识别器不可靠）都已停用，写了也不会渲染 —— 报告只有三个板块。

`patterns[].words` 用的是**归一化后的词形**（去标点、去撇号、小写）：
`mountain's → mountains`、`We've → weve`、`Mrs → missus`、`Dr → doctor`。

### 视觉风格 · 胶囊简约风（唯一交付样式）

`build_html.py` 固定加载 `assets/theme-mac.css`，不加载任何场景图。要点：

- 浅灰页面底 `#f2f3f5` + 顶部一层很淡的白色径向柔光
- 白色卡片：18px 圆角、1px 浅描边、两层柔和阴影
- 胶囊按钮：`✓ 参考` 浅绿底，`▶ 原音` 白底描边；按下有 1px 下沉反馈
- 绿色 `#3fa554` 只做强调（圆点、选中态、参考按钮），不铺大面积
- 圆形序号徽章 + 发丝分隔线；表格浅灰表头、悬停变浅
- 系统无衬线字体，标题不做描边

**主题是整份替换而不是叠加**：新增皮肤必须写全所有选择器，漏一个就会退回浏览器默认样式。

### 响应式（PC / 平板 / 手机，两个断点）

页面必须真正随屏幕宽度重排，不是只在手机上打个补丁。从宽到窄三级：

| 宽度 | 布局 |
|---|---|
| **> 800px** | 完整表格 + 单列归总行（时间、听起来像、大括号全显示） |
| **641–800px** | 「连贯朗读」表格转卡片流（隐藏表头，单元格用 `::before` 补出「台词本 · / 听起来像 · / 说明 ·」），其余同宽屏 |
| **≤ 640px** | 手机简化版，见下 |

**为什么要有 800 这个中间断点**：表格有 5 列，宽度掉到 800 以下时「说明」列只剩几十像素，
中文会变成一字一行。宁可提前转成卡片，也不要挤成竖条。

手机（≤640）在卡片基础上再简化：

- **发音习惯改善**：每个词一张小卡。`单词` 与 `✓ 参考` **同一行、参考靠右**，
  两者都与 `▶ 原声` **等宽（80px）**，所以右侧按钮形成一条竖线。错误行去掉时间和
  「听起来像」四个字，左侧换成红色 `?` 圆图标，只保留「读成什么 + ▶ 原声」。
  多次错误的词**仍保留大括号**，只错一次的在括号同列放一个**同色小三角箭头**——
  两者都占 grid 第 1 列（`"word word ref" "mark list list"`），所以纵向自然对齐。
- **连贯朗读**：**时间、说明整列都隐藏**；台词本 / 听起来像 竖排；
  `▶ 原声` 与 `✓ 参考` **同一行、整体靠右**，且宽度与全文标注的两个按钮
  统一为 `min-width:88px`（两节的按钮必须一样宽、一样高：都 `padding:5px 10px`）
- **全文标注**：原句自然换行成 2 行以上；`▶ 原句` 与 `✓ 参考` **同一行、整体靠右**
- 控制条（单选 + 自动朗读 + 取消）**右对齐**并另起一行占满宽度；字号与内边距整体收紧一档

实现要点：

- 「听起来像」必须用 `<span class="lbl">` 包起来（`build_html.py` 已这么做），
  否则 CSS 没法只隐藏这四个字、保留后面的读法文本。桌面靠 `.lbl{margin-right:5px}` 留空。
- 单词条在 `build_html.py` 里区分：多次错误输出 `.bracewrap`（SVG 大括号，
  `stroke-width=4` —— 太细在手机上会看不清），单次输出 `.arrowmark`
  （CSS 三角，桌面 `display:none`）。
- 手机端 `.grow` 用 grid 而不是 flex——括号和列表必须在同一行，但单词和参考按钮要在上面两行。
- `?` 图标用 `.occ::before` 画，配色照抄「取消」按钮（`#fdf6f5` 底 / `#f3d3d0` 边 / `#b42318` 字）。

**自动朗读时的悬浮取消**：`run()` 给当前章节的取消按钮加 `.floating`，
CSS 让它 `position:fixed; top:12px`、右边界用
`right:max(12px, calc((100vw - 1100px)/2))` 贴着内容列右缘。这样列表再长，
往上翻也随时能停；`clearMarks()` 负责摘掉这个类，不朗读时按钮回到原位随页面滚动。

**按钮右缘必须两节对齐**：「连贯朗读」是 `.card.plain`（无内边距）+ 单元格 14px，
「全文标注」是卡片 22px + 行 14px = 36px。所以表格的 `.pb` 列要补
`padding-right:36px`（表头 `th:nth-child(5)` 同样补），否则两节按钮右缘差 22px，
看着就是没对齐。这条要写在**基础样式**里，PC / 平板 / 手机都生效。

**坑**：`table-layout:fixed` 下，列宽**只认第一行的 `th`**，写在 `td`（`.tb .sw` 等）上的
`width` 会被直接忽略 —— 各列被均分，按钮列过窄就折行。列宽必须写成
`.tb th:nth-child(n){width:…}`。

Minecraft 版已归档为 `theme-minecraft.css` / `scene-minecraft.svg` / `ding-minecraft.mp3`，
**不再产出**，仅作回退参考。

### 验收方式（必须做）

```bash
python scripts/verify.py <报告.html>
```

一条命令做完：分节预览页 → PC/平板/手机三档截图 → 假 Audio 注入验证 JS 播放序列，
约 12 秒。产物在 `<报告目录>/_verify/`，然后**逐张看截图**确认布局。
不要只凭 CSS 想象，也不要只看 JS 输出——两者都要看。

它内部做的事：
- 按 `<h2>` 切出 `sec1/2/3.html`，单独截某一节（避免一屏到底看不清）
- PC 1280×1000、平板 820、手机 390（iframe 套）
- 注入假 `Audio`，点「自动朗读」，`--dump-dom` 取回状态与播放序列
- 「叮」按 `const DING` 的 base64 长度判定（从源码里正则提取，脚本已自动做）

**判定只看播放序列，不看按钮状态**。假 Audio 几乎瞬间结束：条目多（如 25 条）时
5 秒后还在播，`active=1`；条目少（如 2 条）时早就跑完并 `clearMarks()` 了，
`active=0` 是**正常**的。所以脚本判断的是「序列里有没有 `原声… → 叮 → 参考` 这个模式」。

需要手工细看某处时的原始命令：

```bash
chrome --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1280,900 --screenshot=shot.png "file:///.../报告.html"
```

**手机宽度怎么验**：Windows 上的 Chrome headless 有最小窗口宽度（约 485 CSS px），
直接 `--window-size=390,…` 拿到的是 485 的视口 —— 截图会按 390 裁切，看起来像内容溢出，
很容易误判成布局 bug。可靠做法是套一层固定宽度的 iframe：

```html
<iframe src="报告.html" style="width:390px;height:1800px;border:0"></iframe>
```

iframe 内部视口就是 390px，媒体查询按手机生效；外层窗口给 820×1820 截图即可。
加 `--allow-file-access-from-files` 才能加载本地 file:// 的 iframe。

## 结论怎么写

拿到 `align_words.py` 的输出后，按**同类归纳**而不是逐条罗列：

- 先找重复出现的模式（同一个音在多个词上出错），这才是「发音习惯」，比单个词重要。
- 特别留意这几类高频系统性错误：
  - 辅音连缀坍塌（br- / str- / kl- / kw- / θl）
  - 词尾辅音丢失（-s / -ed / -ing / -d / -er）
  - 浊辅音清化（/b/→/p/、/v/→/f/、/d/→/t/）
  - 元音偏移（/aʊ/→/aɪ/、/eɪ/→/ʌ/、/ʌ/→/ɒ/、/ə/→/ər/）
  - 否定词被吞（not / don't / cannot）—— 这类会改变句意，优先级最高
- 如果多份录音都出现同一个错误，明确告诉用户这是**稳定习惯**，值得专项练。

### 整段一带而过 ≠ 逐词读错（重要）

有时**连续多个词同时 `missing`**（不是 `sub`），且 `ts` 完全相同 —— 这不是「这几个词各自
读错」，而是孩子把那一整段**含混带过去了**。典型例子：
`She pointed at the biggest feeder.` 前 5 词全 missing，查 ASR 原文发现三个模型都只认出
`That is the best feeder.`，说明前面「Rose said. She pointed at the biggest」整段滑过去了。

判据：**≥3 个相邻词同时 missing，且时间戳相同** → 判定为整段漏读。

处理：**不要**放进「发音习惯改善」。`by_word` 命中会渲染成 5 行「漏读」，看起来像
5 个词分别没读出来，误导。正确做法是写进 `curated.json` 的 `sentences`
（「连贯朗读」），把整句作为一条，`note` 里写明是整段带过、要拆开慢读。

判断依据去 `asr_*.json` 里按时间段捞原文（`seg["end"] > s-0.6 and seg["start"] < e+0.6`），
别只看 `words.json` 的聚合结果。

### 当孩子读得很好（high 只有个位数）

这会发生，而且必须如实呈现——**不要为了报告好看去降级 or 硬凑分组**。
实测《The Boss》281 词里 273 个完全正确（97%），high 只有 3 个，其中 1 个是
同义替换假阳性，真正要看的只有 2 个。

处理方式：

- `patterns` 照实写，**一个组里放 2 个词也正常**；`desc` 里要把「整体情况」写清楚。
  最有说服力的写法是**给分母**：「全篇 -ed 结尾的词共 10 个，其中 7 个都咬得很准，
  只剩这两处松了」——比单说「你这两个词错了」有用得多。
- `sentences` 可以留空。`build_html.py` 已有空状态兜底，会显示
  「本次没有整句连贯性问题」，不会渲染出一个只有表头的空表格。
- **先排除「音频不是这一篇」**：错误特别少时，先核对 ASR 全文和台词本是不是同一个故事
  （`transcribe.py` 跑完直接把 `asr_turbo.json` 的 segments 拼起来读一遍）。
  对齐质量好的标志是：时间轴从 0 连续到结尾、没有大量重复 ts、`ok` 占绝大多数。
- 最终回复要**明确肯定**，并说清「剩下这几个是真问题还是可以不管」。

**跨录音对比是这个技能最有价值的部分**：《The Boss》的 `-ed` 问题（loved→loves、
popped→pop）与上一份《The Bird Feeders》（watched→watch、climbed→climb、
looked→looks、made→make）是同一个毛病，只是这次 10 个词里对了 7 个。
这类「同一个人、跨多份录音稳定出现」的结论必须写进回复——单看一份报告看不出来。

## 性能（实测数据，别凭感觉优化）

测试环境：6 逻辑核 CPU、16GB 内存、Radeon RX 470（ctranslate2 在 Windows 上不支持
ROCm，所以 **GPU 路线不可用**，只能走 CPU int8）、音频 273.7 秒。

### 各步耗时（单任务，51 句 / 311 词，端到端实测 6m09s）

| 步骤 | 优化前 | 优化后 | 说明 |
|---|---|---|---|
| 1 台词本 | 2–3 分钟（MCP 反复补全） | **0.6s** | `prep_docx.py` 只读解析，不走 MCP |
| 2 解码 | 3s | **0.4s** | 单次 ffmpeg |
| 3 转写 | 291s | **272–325s** | 见下，只能省 7%，且受系统负载影响有 ±15% 波动 |
| 4 对齐切片 | ~35s（174 次进程启动） | **9.5s** | 切片改并发 6 路 |
| 5 TTS | 47s | **32.4s** | 并发 4 → 6 |
| 6 分析 | 多次翻稿写临时脚本 | **0.5s** | `analyze.py` 一次输出全材料 |
| 验收 | ~6 分钟手工截图 | **12s** | `verify.py` |

**转写仍有 ±15% 波动**：同一份音频、同一套参数，空载 270s、和其他任务并行时 325s。
它现在占全流程 75% 以上，所以总耗时区间约 **5.5–6.5 分钟**。想更准就单独跑、别同时干别的。

### 转写是硬瓶颈，而且大部分优化是负收益

实测四组配置（turbo，273.7s 音频）：

| 配置 | 耗时 | 结果 |
|---|---|---|
| beam=5，默认 temperature | 140.2s | 基准 |
| **beam=5，temperature=0.0** | **130.4s** | **逐段文本 md5 完全相同** ✓ |
| beam=1，temperature=0.0 | 145.1s | 段数 32→34，结果变了 ✗ |
| beam=5，temperature=0.0，3 线程 | 159.5s | 结果一致但更慢 ✗ |

结论：

- **`temperature=0.0` 必开**。默认的 `(0.0, 0.2, …, 1.0)` 会在解码不满意时逐级重试，
  结果**一模一样**却白花 7%。
- **`beam_size` 必须留 5**。改成 1 反而更慢（beam 搜索之外的开销占了大头），
  而且结果会漂——这个技能的全部判断都建立在三模型结果稳定上，不能动。
- **线程数 = 逻辑核数**。减半线程慢 22%。
- **绝对不要并行跑三个模型**。whisper CPU 推理受内存带宽限制，三模型各 2 线程
  墙钟 257s（比顺序 291s 只快 12%），而 turbo 单模型从 131.7s 恶化到 250s；
  各 3 线程更差（small 从 44.7s 涨到 181.8s）。**顺序跑，每个跑满核**才是最优。

### 能被真正压缩的是「胶水时间」

转写只能省 7%，但一次任务从 20 多分钟压到 **6 分钟左右**（约 70%），
靠的是把机械步骤管道化：

- 台词本准备从「MCP 预览被 200 字截断 → doc_find 补全丢空格 → 自己写正则」三步
  反复试错（2–3 分钟），变成一次只读解析 **0.6 秒**
- 对齐结果的七种视图（词频归并、按行统计、整段漏读、三模型原文……）原来要反复
  写临时脚本，现在一条 `analyze.py` **0.5 秒**
- 验收从「分段切页面 + 五次截图 + 写假 Audio 注入」手工流程（约 6 分钟），
  变成 `verify.py` 一条命令 **12 秒**

**改脚本后必须做回归**（已验，优化不能改变判断结果）：

| 脚本 | 回归方式 | 本次结果 |
|---|---|---|
| `prep_docx.py` | 与既有 `script.txt` diff | 完全一致（51 句 311 词） |
| `align_words.py` | 对比 `clips/` 的 md5 | 174/174 一致 |
| `transcribe.py` | 对比 `asr_*.json` 文本 + `words.json` 逐词 sev | 三模型文本全同、311/311 一致 |

## 必须排除的假阳性

这些**不写进报告**（规则 5：不显示「不算错的差异」），但分析时必须心里有数，
不要在最终回复里把它们当成发音错误说出去：

- **自造词 / 专有名词**（童谣里的 Eensey Weensey、人名）—— 识别器词表里没有，
  听错不代表读错，不能计入统计。
- **自然缩写**（I am → I'm、cannot → can't）—— 口语里正确，只是和台词本字数对不上。
- **同义替换**（OK → Okay、Bye-bye → Bye、lots of → a lot of）—— 已在 `IGNORE` 里
  自动过滤（`ok/okay/bye/lots/lot`）。这类发音**完全相同**，只是拼写不同，
  识别器必然二选一，属于纯噪声。
- **语气词 / 象声词**（Oh、Ooh、Woo、Ho ho ho）—— 已在 `IGNORE` 集合里自动过滤。
- **常用虚词**（I / am / the / it / a / are / you / not / he / she / say / did / said / but）
  —— 已在 `STOP` 表里：整句只有这类错误时不再单独列行。

自造词导致整句识别失败的（比如童谣里自造的名字），**不写进报告**，因为报告只有三个板块。
如果它在结论里很关键，放在最终回复的文字里说明，不要硬塞一个章节进报告。

## 已知坑

| 现象 | 原因与对策 |
|---|---|
| `WSServerHandshakeError: 503` | edge-tts 服务端限流，**重试即可**。`gen_tts.py` 已内置 6 次重试。 |
| `open() got an unexpected keyword argument 'metadata_errors'` | faster-whisper 的 `decode_audio` 与 PyAV 版本不兼容。**不要**让它读文件名，自己用 `wave` + numpy 读成数组再传给 `transcribe()`。`transcribe.py` 已这么做。 |
| HuggingFace 下载 502 | 国内网络直连被挡，改走 ModelScope。模型放在 `~/.workbuddy/models/`（或 `WHISPER_MODELS_DIR`）。 |
| 对齐结果几乎全是 `high` | 十有八九是 `script.txt` 和音频不是同一篇。先核对两边首句。 |
| 弯引号把 `Vet's` 拆成两个词 | 先统一 `’ → '`，并在归一化时直接去掉撇号。 |
| `models:0` 或分组整块消失 | 该组里的词本次都不是 `high`（可能只被 2 个模型听错）。这是规则 1 的预期行为，不要为了好看降级。 |
| 某个分组一整组「漏读」 | 多半是整段带过被误判成逐词缺失，见「整段一带而过 ≠ 逐词读错」。 |
| 测试脚本读 `window.DING` 得到 `undefined` | `const DING` 是模块级声明，**不挂 `window`**。`verify.py` 已改成从 HTML 源码正则提取真实长度（当前 5491），不要硬编码，换了提示音就会失准。 |
| 以为「并行跑三个模型会快」 | 错的，实测更慢。whisper CPU 推理吃内存带宽，并行会让每个模型都变慢，见「性能」一节。 |
| 想用 GPU 加速转写 | Windows + AMD 显卡（ROCm）ctranslate2 不支持，CUDA 版只对 NVIDIA 有效。CPU int8 是现实选择。 |
| `prep_docx.py` 把标题算进正文 | 标题段判断是「编号开头（`78. xxx`）或整段无句末标点」。文件命名不规则时用 `--keep-heading` 或手工删首行。 |

## 交付

报告是**单文件**（音频 base64 内嵌），可直接发微信。同时在用户素材目录放一份副本。
最终回复要直接给出：最确定的错误、系统性规律、以及「读错词 ≠ 发音错」的区分，
不要让用户自己去报告里翻。

交付前跑一次 `make_history.py` 更新 `history.md`，下次才能在跨录音对比里用上这次的结果。
