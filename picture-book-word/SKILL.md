---
name: picture-book-word
description: 将绘本/分级读物PDF（或字幕PDF）整理为固定排版的Word文档，并按【短语短句】【句型练习】标准标注。当用户提供绘本PDF并要求"整理成Word""按格式输出""导出DOC""做成跟读/整理文档"，或上传用户自行改好的docx样板要求"学习并按这个标准整理""把这个规则写入技能"时使用。核心产出：标题18pt加粗栏内顶部不跨页、正文16pt每句首词加粗、句号后空一格且句首大写、正文两栏、按叙事单元分段段间空一行、删作者行与拟声词行；PDF含【短语短句】时正文短语斜体+下划线+上标编号并文末保留【短语短句】节，含【句型练习】时正文句型例句斜体+下划线并文末保留【句型练习】节。
---

# Picture Book Word

把绘本/分级读物（Heinemann、Peppa 字幕等）的正文整理成用户固定的 Word 排版，支持【短语短句】【句型练习】标注。最终交付 `.docx`。

## 触发场景
- 用户给绘本/字幕 PDF，要求整理正文、按固定格式排版、导出 DOC/Word。
- 用户给一份自己改好的 docx 当样板，要求"学习并按这个标准整理"——先完整读取样板（word skill 的 read.py），再按样板规则产出。
- PDF 中存在【短语短句】或【句型练习】小节时，必须保留并按下述规则标注。

## 硬性格式规则（验收标准，逐条检查）
1. **标题**：带编号（如 `13. Spider Web`）加粗 18pt；位于栏内顶部、与正文同页、不跨页——整篇单一 section，两栏设置在 body 的 sectPr 上，标题就是正文第一个段落。
2. **正文 16pt**；每句第一个单词加粗；句号后空一格（含 `."` 引号后）；每句首字母大写（`. ! ?` 后小写转大写）。
3. **两栏**（`w:cols num=2`）；按叙事单元分段，**段间不空行**——自然段之间用回车分隔即可，不插入空行段落。
4. **只保留故事主体**：删作者行、删独立拟声词行（如 `Eeek!`、`Ah~~~` 单独成行的内容）。
5. **【短语短句】命中时**：正文中该短语用 **斜体+下划线**，短语后紧跟**上标编号**（按列表顺序 1..N）；短语若含句首词，句首词同时保留加粗（b+i+u 叠加）。文末保留【短语短句】节：标题加粗，每条 `英文 + 空格 + 中文` 一行。
6. **【句型练习】命中时**：正文中对应句型例句用 **斜体+下划线**（不加编号）。文末保留【句型练习】节：标题加粗，每条英文一行 + 中文一行。
7. **中文字体统一**：所有 run（含标题、两节标题、中英对照的中文部分）的 `w:rFonts/@w:eastAsia` 一律设为 `微软雅黑`（简体中文雅黑）；西文字体保持 Word 默认（Cambria）。生成后必须跑字体校验（见工作流第 5 步）确认无漏设。

## 工作流
1. **提取 PDF**：用 PyMuPDF（`import pymupdf`）逐页 `page.get_text()` 拼接；跳过封面/版权/页码页；保留叙事正文；拟声词独立行并入上下文或删除（按第 4 条）。
2. **定位标注**：若 PDF 含【短语短句】/【句型练习】，提取列表（英+中），并找出正文中每个短语/句型例句的出现位置。
3. **构造 JSON**（schema 见下），放工作目录。
4. **生成 docx**：
   `D:\Python\Python312\python.exe <skill>/scripts/build_picture_book_docx.py <input.json> <output.docx>`
   （默认 `python` 沙箱缺 python-docx，必须用 D 盘 3.12。）
5. **验证**：
   - 结构：word skill `read.py <out.docx> -d 3`，确认 b/i/u/superscript run 与用户版一致；
   - 字体：`D:\Python\Python312\python.exe <skill>/scripts/verify_fonts.py <out.docx>`，退出码 0 且 `mismatches` 为空（全部 run 的 eastAsia=微软雅黑）；
   - 视觉：Word COM 导出 PDF（`ExportAsFixedFormat` 17）→ PyMuPDF 渲染 PNG → Read 检查两栏、标题栏内、上标可见、中文显示正常（docx 不能用 artifact-preview 出图）。
6. **交付**：present_files 交付 `.docx`。

## JSON Schema
```json
{
  "title": "13. Spider Web",
  "paragraphs": [
    [ [seg, ...], [seg, ...], ... ],   // 段 -> 句 -> segment
    ...
  ],
  "phrases": [["a complete mess", "一团糟"], ...],          // 可选【短语短句】
  "patterns": [["I wonder where ____ .", "我很好奇____在哪里."], ...]  // 可选【句型练习】
}
```
Segment 类型：
- `"plain string"`：16pt 普通文本（脚本自动做句号后空格、句首大写）
- `{"t": "text", "b": true}`：加粗（句首词）
- `{"t": "text", "b": true, "i": true, "u": true}`：加粗+斜体+下划线
- `{"ph": "phrase", "n": 5}`：斜体+下划线，随后上标 `5`
- `{"pt": "pattern text"}`：斜体+下划线（句型例句，无编号）
- `{"sup": "12"}`：上标

空格规则：segment 文本之间需要空格时写在文本内（rest 以空格开头，如 `" Pig is hard at work in the study."`）；独立的 `" "` segment 也会被脚本并入下一个文本 run。**不要**依赖句子间自动加空格——非段首句由脚本自动补一个前导空格（`leading_space`），段内其余空格由 JSON 负责。

旧格式兼容：句子若为 `["first", "rest"]` 二元组，自动转换为 `[{"t":"first","b":true}, "rest"]`。

## 已知坑（必须遵守）
- **Word 会丢弃独立纯空格 run**：所有空格必须并入文本 run（脚本已有 pending 机制处理独立 `" "` segment；短语条目中英之间的空格并入中文 run）。
- docx 视觉验证只能走 Word COM 导出 PDF（artifact-preview 对 docx 不出图）。
- 中文内容无需特殊字体设置，Word 默认中文字体即可。
