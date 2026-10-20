#!/usr/bin/env python3
r"""Step 1 — 从 .docx 直接生成 script.txt（一步到位，不走 MCP）。

用法: python prep_docx.py <台词本.docx> <工作目录> [--keep-heading]

为什么不用 MCP 读 docx：
  - `doc_resolve_document_structure` 的 text_preview 上限 200 字，长段落被截断
  - 用 `doc_find` 补全的 related_text 会丢空格（lookeda little）
  直接只读解析 word/document.xml 拿到的才是精确原文，且快得多。

做法：
  1. 只读解析 docx，按 w:p 取每段文本（不打开 Office，不改原文件）
  2. 段内软换行合并成一行，段落间用空格连接
  3. 统一弯引号为直引号
  4. 保护 Mr. / Mrs. / Dr. 不被当成句末
  5. 按 [.!?…]["']?(?=\s|$) 断句 —— 必须容许句末标点后跟一个收尾引号，
     否则 "…squirrels!" Nana said. 会被切成两句、引号归属错乱
  6. 跳过标题段（编号开头如 "78. The Bird Feeders"，或整段不含句末标点）
"""
import os, re, sys, zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SENT_END = re.compile(r"[.!?…]\"?\'?(?=\s|$)")


def docx_paragraphs(path):
    """只读解析 docx，返回段落文本列表。"""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    out = []
    for p in root.iter(NS + "p"):
        parts = []
        for node in p.iter():
            if node.tag == NS + "t":
                parts.append(node.text or "")
            elif node.tag == NS + "tab":
                parts.append(" ")
            elif node.tag == NS + "br":
                parts.append(" ")
        out.append(re.sub(r"\s+", " ", "".join(parts)).strip())
    return [p for p in out if p]


def split_sentences(body):
    # 保护缩写，避免被当成句末
    for a, b in (("Mr.", "Mr§"), ("Mrs.", "Mrs§"), ("Dr.", "Dr§"),
                 ("St.", "St§"), ("vs.", "vs§")):
        body = body.replace(a, b)
    sents, last = [], 0
    for m in SENT_END.finditer(body):
        s = body[last:m.end()].strip()
        if s:
            sents.append(s)
        last = m.end()
    tail = body[last:].strip()
    if tail:
        sents.append(tail)
    # … 还原成三个点，保持与既往台词本一致（TTS 读法相同，但比对时少噪音）
    return [s.replace("§", ".").replace("…", "...") for s in sents]


def is_heading(p):
    """标题段判断：编号开头（"78. xxx" / "1) xxx"），或整段不含句末标点。"""
    if re.match(r"^\d+\s*[.)]\s", p):
        return True
    return not SENT_END.search(p)


def main():
    docx, D = sys.argv[1], sys.argv[2]
    keep_heading = "--keep-heading" in sys.argv

    paras = docx_paragraphs(docx)
    print(f"docx 段落 {len(paras)} 段")

    if not keep_heading and paras and is_heading(paras[0]):
        print(f"跳过标题段: {paras[0][:50]}")
        paras = paras[1:]

    body = " ".join(paras)
    body = (body.replace("\u2019", "'").replace("\u2018", "'")
                .replace("\u201c", '"').replace("\u201d", '"')
                .replace("\u2014", "-").replace("\u2013", "-"))
    body = re.sub(r"\s+", " ", body).replace(" . . .", "…").strip()

    sents = split_sentences(body)
    os.makedirs(D, exist_ok=True)
    out = os.path.join(D, "script.txt")
    open(out, "w", encoding="utf-8").write("\n".join(sents) + "\n")

    nw = sum(len(re.findall(r"[A-Za-z][A-Za-z'\-]*", s)) for s in sents)
    print(f"句数 {len(sents)} | 词数 {nw} -> {out}")
    # 自检：引号未成对不一定是错——对话跨两句时（"…pole." / "…food."）本来就该分开。
    # 所以这里只提示不报错，重点看「句数是否离谱」和「首句是否正文」。
    odd = [s for s in sents if '"' in s and s.count('"') % 2 == 1]
    print(f"自检：首句 = {sents[0][:40]}")
    if odd:
        print(f"      含奇数引号的句子 {len(odd)} 条（跨句对话属正常，非必错）")


if __name__ == "__main__":
    main()
