#!/usr/bin/env python3
"""Verify East-Asian font uniformity of a picture-book docx.

Usage:
    python verify_fonts.py <docx>

Checks that every non-empty run carries w:rFonts/@w:eastAsia == "微软雅黑"
(Simplified-Chinese YaHei). Reports mismatched runs as a JSON result on stdout:
{"ok": true|false, "checked": N, "mismatches": [{"para": i, "run": j, "text": "...", "eastAsia": ...}, ...]}
Exit code 0 when all runs pass, 1 when mismatches exist, 2 on input errors.
"""
import json
import re
import sys

from docx import Document
from docx.oxml.ns import qn

CN_FONT = "微软雅黑"
HAN_RE = re.compile(r"[\u4e00-\u9fff]")


def check(path):
    doc = Document(path)
    mismatches = []
    checked = 0
    for pi, p in enumerate(doc.paragraphs):
        for ri, r in enumerate(p.runs):
            if not r.text:
                continue
            checked += 1
            rPr = r._element.rPr
            east = None
            if rPr is not None:
                rf = rPr.find(qn("w:rFonts"))
                if rf is not None:
                    east = rf.get(qn("w:eastAsia"))
            if east != CN_FONT:
                mismatches.append({
                    "para": pi,
                    "run": ri,
                    "text": r.text[:30],
                    "has_chinese": bool(HAN_RE.search(r.text)),
                    "eastAsia": east,
                })
    return checked, mismatches


def main():
    if len(sys.argv) != 2:
        print("Usage: verify_fonts.py <docx>")
        sys.exit(2)
    try:
        checked, mismatches = check(sys.argv[1])
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        sys.exit(2)
    result = {
        "ok": len(mismatches) == 0,
        "checked": checked,
        "mismatches": mismatches,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
