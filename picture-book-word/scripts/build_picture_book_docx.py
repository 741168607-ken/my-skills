#!/usr/bin/env python3
"""Build a picture-book Word document from a JSON spec.

Usage:
    python build_picture_book_docx.py <input.json> <output.docx>

input.json schema:
{
  "title": "13. Spider Web",
  "paragraphs": [
    [ [seg, seg, ...], [seg, ...], ... ],   # paragraphs -> sentences -> segments
    ...
  ],
  "phrases": [["a complete mess", "一团糟"], ...],     # optional 【短语短句】
  "patterns": [["I wonder where ____ .", "我很好奇____在哪里."], ...]  # optional 【句型练习】
}

Segment types:
- "plain string"                     -> 16pt normal text
- {"t": "text", "b": true}           -> bold (sentence-initial word)
- {"t": "text", "b": true, "i": true, "u": true} -> bold+italic+underline
- {"ph": "phrase text", "n": 5}      -> italic+underline, then superscript number n
- {"pt": "pattern text"}             -> italic+underline (sentence-pattern example, no number)
- {"sup": "12"}                      -> superscript text

Compatibility: legacy sentence form ["first", "rest"] is converted to
[{"t": "first", "b": true}, "rest"].

Format rules applied:
- Title: bold 18pt, first paragraph, inside column (no section break)
- Body: 16pt; sentence-initial word bold; phrases italic+underline with superscript
  numbers; sentence-pattern examples italic+underline
- Space after every period (including after a closing quote); sentence-initial
  letters capitalized (light-touch normalization on plain text segments)
- One blank paragraph between story paragraphs
- Whole document one section, two columns (w:cols num=2); title sits in the column top
- Optional trailing sections: 【短语短句】 (bold heading, one entry per line,
  "en + space + zh"), 【句型练习】 (bold heading, en line then zh line per entry)
- Unified East-Asian font: every run gets w:rFonts/@w:eastAsia="微软雅黑"
  (Simplified-Chinese YaHei), so Chinese text renders uniformly.
"""
import json
import re
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

FONT_SIZE = 16
CN_FONT = "微软雅黑"


def set_cn_font(run):
    """Set w:eastAsia on the run's rFonts so Chinese text uses 微软雅黑."""
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:eastAsia"), CN_FONT)


def normalize_text(text):
    """Light-touch fixes: space after a single period (not after ellipsis dots);
    capitalize letter after . ! ?."""
    text = re.sub(r"(?<!\.)\.(?![\s\"\u201d\u2019\u2033]|$)", ". ", text)
    text = re.sub(r"(?<=[.!?]\s)([a-z])", lambda m: m.group(1).upper(), text)
    return text


def add_run(p, text, bold=False, italic=False, underline=False, sup=False):
    r = p.add_run(text)
    r.font.size = Pt(FONT_SIZE)
    set_cn_font(r)
    if bold:
        r.bold = True
    if italic:
        r.italic = True
    if underline:
        r.underline = True
    if sup:
        r.font.superscript = True
    return r


def add_segments(p, segments, leading_space=False):
    if isinstance(segments, str):
        segments = [segments]
    pending = " " if leading_space else ""
    for seg in segments:
        if isinstance(seg, str):
            if seg.strip() == "":
                # standalone-space runs get dropped by Word; merge into next run
                pending += seg
                continue
            add_run(p, pending + normalize_text(seg))
            pending = ""
        elif "ph" in seg:
            add_run(p, pending + seg["ph"], italic=True, underline=True)
            pending = ""
            add_run(p, str(seg["n"]), sup=True)
        elif "pt" in seg:
            add_run(p, pending + seg["pt"], italic=True, underline=True)
            pending = ""
        elif "sup" in seg:
            add_run(p, pending + str(seg["sup"]), sup=True)
            pending = ""
        else:
            add_run(p, pending + normalize_text(seg.get("t", "")),
                    bold=seg.get("b", False),
                    italic=seg.get("i", False),
                    underline=seg.get("u", False))
            pending = ""


def legacy_sentence(sent):
    """Convert legacy ["first", "rest"] to segment list."""
    if len(sent) == 2 and isinstance(sent[0], str) and isinstance(sent[1], str):
        return [{"t": sent[0], "b": True}, sent[1]]
    return sent


def build(spec, output_path):
    doc = Document()

    # --- Title: bold 18pt, first paragraph, inside column ---
    title = doc.add_paragraph()
    tr = title.add_run(spec["title"])
    tr.bold = True
    tr.font.size = Pt(18)
    set_cn_font(tr)

    # --- Body (paragraphs separated by plain Enter, no blank line between) ---
    for para in spec["paragraphs"]:
        p = doc.add_paragraph()
        for idx, sent in enumerate(para):
            segments = legacy_sentence(sent)
            add_segments(p, segments, leading_space=(idx > 0))

    # --- 【短语短句】 ---
    if spec.get("phrases"):
        h = doc.add_paragraph()
        hr = h.add_run("【短语短句】")
        hr.bold = True
        hr.font.size = Pt(FONT_SIZE)
        set_cn_font(hr)
        for en, zh in spec["phrases"]:
            p = doc.add_paragraph()
            add_run(p, en)
            # space merged into the zh run (standalone-space runs are dropped by Word)
            add_run(p, " " + zh if not zh.startswith(" ") else zh)

    # --- 【句型练习】 ---
    if spec.get("patterns"):
        h = doc.add_paragraph()
        hr = h.add_run("【句型练习】")
        hr.bold = True
        hr.font.size = Pt(FONT_SIZE)
        set_cn_font(hr)
        for en, zh in spec["patterns"]:
            p = doc.add_paragraph()
            add_run(p, en)
            p = doc.add_paragraph()
            add_run(p, zh)

    # --- Two columns (single section; title stays in column top) ---
    body_sectPr = doc.sections[0]._sectPr
    cols = body_sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        body_sectPr.append(cols)
    cols.set(qn("w:num"), "2")
    cols.set(qn("w:space"), "360")

    doc.save(output_path)


def main():
    if len(sys.argv) != 3:
        print("Usage: build_picture_book_docx.py <input.json> <output.docx>")
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        spec = json.load(f)
    build(spec, sys.argv[2])
    print("Done:", sys.argv[2])


if __name__ == "__main__":
    main()
