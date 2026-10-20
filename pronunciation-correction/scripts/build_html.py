#!/usr/bin/env python3
"""Step 4 — 生成 HTML 诊断报告（Minecraft 卡通风格）。

用法: python build_html.py <工作目录> [--curated curated.json] [--out 名称.html]

设计规则（务必保留）:
  1. 只显示 / 只标注「明确听错」(sev == high)；mid / low 一律不上色、不进表格。
  2. 凡是出现「错误发音」按钮的位置，旁边必须有「参考」按钮：
     - 单个词：原音 + ✓参考
     - 同一个词多次出错：用大括号把各次错误括在一起，只在汇总处放一个 ✓参考
     - 句子：原声 + ✓参考发音
  3. 页面顶部不放统计汇总。
  4. 不显示「不算错的差异」。
  5. 全文标注只列出「含明确听错词」的句子。
"""
import base64, json, os, re, sys

D = sys.argv[1]
curated_path = None
if "--curated" in sys.argv:
    curated_path = sys.argv[sys.argv.index("--curated") + 1]
out_name = "诊断报告.html"
if "--out" in sys.argv:
    out_name = sys.argv[sys.argv.index("--out") + 1]

CUR = json.load(open(curated_path, encoding="utf-8")) if curated_path else {}
TITLE = CUR.get("title") or "朗读发音诊断"
SUBTITLE = CUR.get("subtitle") or ""

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
# 最终版只保留「胶囊简约风」；Minecraft 版仅作存档，不再产出
CSS = open(os.path.join(ASSETS, "theme-mac.css"), encoding="utf-8").read()
SCENE = ""
DING = "data:audio/mpeg;base64," + base64.b64encode(
    open(os.path.join(ASSETS, "ding.mp3"), "rb").read()).decode()

rows = json.load(open(os.path.join(D, "words.json"), encoding="utf-8"))["rows"]
lines = [l.replace("\u2019", "'").replace("\u2018", "'")
         for l in open(os.path.join(D, "script.txt"), encoding="utf-8").read().splitlines()
         if l.strip()]
CLIPS = os.path.join(D, "clips")
TTS = os.path.join(D, "tts")
HIGHLIGHT = {"high"}
# 语气词 / 象声词：识别器几乎必然听错，但不代表发音问题，不参与展示
IGNORE = {"oh", "ooh", "ah", "ha", "ho", "woo", "mow", "er", "mm", "mmm",
          "wow", "hmm", "huh", "shh", "ahem", "oops", "yay", "hey",
          "ohoh", "aha", "haha", "oho", "eek", "ugh", "phew", "tsk",
          # 同义替换：OK/Okay 发音完全相同，只是拼写不同，识别器必然二选一
          "ok", "okay", "bye", "bye-bye", "lot", "lots"}
# 「全文标注」里，若一句的错误词全部落在这张表里，不值得单独占一行，整句不显示
STOP = {"i", "am", "the", "it", "a", "are", "you", "not", "he", "she",
        "say", "did", "said", "but"}


def slug(s):
    t = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return t or "x"


_c = {}


def b64path(p):
    if p in _c:
        return _c[p]
    v = ""
    if p and os.path.exists(p) and os.path.getsize(p) > 200:
        v = "data:audio/mpeg;base64," + base64.b64encode(open(p, "rb").read()).decode()
    _c[p] = v
    return v


def clip_src(i):
    return b64path(os.path.join(CLIPS, f"w{i}.mp3"))


def line_src(li):
    return b64path(os.path.join(CLIPS, f"line{li}.mp3"))


def word_ref_src(raw):
    return b64path(os.path.join(TTS, "words", f"{slug(raw)}.mp3"))


def sent_ref_src(li):
    return b64path(os.path.join(TTS, f"line{li}.mp3"))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tsf(t):
    return f"{int(t//60)}:{t%60:04.1f}"


high = [r for r in rows if r["sev"] == "high" and r["w"] not in IGNORE]
show = {r["i"] for r in high}
by_word = {}
for r in high:
    by_word.setdefault(r["w"], []).append(r)

BRACE = ('<svg class="brace" viewBox="0 0 12 100" preserveAspectRatio="none">'
         '<path d="M11,1 C5,1 6,3 6,12 L6,44 C6,49 4,50 1,50 C4,50 6,51 6,56 L6,88 '
         'C6,97 5,99 11,99" fill="none" stroke="currentColor" stroke-width="4" '
         'stroke-linecap="round"/></svg>')


def ref_btn(raw, label="✓ 参考"):
    src = word_ref_src(raw)
    if not src:
        return ""
    return f'<button class="btn ref" data-ref-btn="1" data-src="{src}">{label}</button>'


def item_block(occ):
    """一行一个归总：单词 → ✓参考（括号前方居中）→ 大括号 → 错误列表（原音右对齐）。"""
    raw = occ[0]["raw"]
    rows = []
    for r in occ:
        h = " / ".join(r["diff"]) or "漏读"
        rows.append(
            f'<div class="occ"><span class="tm">{tsf(r["ts"][0])}</span>'
            f'<span class="hz"><span class="lbl">听起来像</span><b>{esc(h)}</b></span>'
            f'<button class="btn mini" data-wrong="1" data-src="{clip_src(r["i"])}">▶ 原声</button></div>')
    brace = (f'<span class="bracewrap">{BRACE}</span>' if len(occ) > 1
             else '<span class="arrowmark"></span>')
    return (f'<div class="grow playitem"><div class="gword">{esc(raw)}</div>'
            f'{ref_btn(raw)}{brace}'
            f'<div class="occlist">{"".join(rows)}</div></div>')


# ---------- 一、系统性发音问题 ----------
pat_html = []
k = 0
for p in CUR.get("patterns", []):
    blocks = []
    for w in p.get("words", []):
        occ = by_word.get(w, [])
        if not occ:
            continue
        blocks.append(item_block(occ))
    if not blocks:
        continue
    k += 1
    pat_html.append(f"""<div class="pat"><div class="pnum">{k}</div><div class="pbody">
<h3>{p['title']}</h3><p class="desc">{p.get('desc','')}</p>
<div class="chips">{''.join(blocks)}</div></div></div>""")

# ---------- 二、整句读散了 ----------
sent_rows = []
for s in CUR.get("sentences", []):
    li = s["line"]
    bad, good = line_src(li), sent_ref_src(li)
    rowset = [r for r in rows if r["line"] == li]
    tlabel = s.get("time") or (tsf(min(r["ts"][0] for r in rowset)) if rowset else f"L{li}")
    btns = f'<button class="btn" data-wrong="1" data-src="{bad}">▶ 原声</button>'
    if good:
        btns += f'<button class="btn ref" data-ref-btn="1" data-src="{good}">✓ 参考</button>'
    sent_rows.append(
        f'<tr class="playitem"><td class="t">{esc(tlabel)}</td>'
        f'<td class="sw">{esc(s["script"])}</td>'
        f'<td class="sh">{esc(s["heard"])}</td>'
        f'<td class="nt">{s.get("note","")}</td>'
        f'<td class="pb">{btns}</td></tr>')

# 本次没有整句问题时给个说明；有表格时才输出表头，避免渲染出只有表头的空表格
if sent_rows:
    sec2_html = ('<table class="tb"><thead><tr><th>时间</th><th>台词本</th>'
                 '<th>实际听起来</th><th>说明</th><th>原声 / 参考</th></tr></thead>'
                 '<tbody>' + "".join(sent_rows) + '</tbody></table>')
else:
    sec2_html = ('<p class="desc" style="padding:14px 16px">'
                 '本次没有整句连贯性问题 —— 朗读整体是连贯的，'
                 '只在「发音习惯改善」里有几个词需要留意。</p>')

# ---------- 三、全文标注（只列有问题的句子） ----------
line_rows = []
_seq = 0
for li, raw in enumerate(lines, start=1):
    idxs = [r for r in rows if r["line"] == li]
    errs = [r for r in idxs if r["i"] in show]
    if not errs:
        continue
    if all(r["w"] in STOP for r in errs):
        continue
    _seq += 1
    parts, cursor = [], 0
    for r in idxs:
        c0, c1 = r["c0"], r["c1"]
        if c0 < cursor:
            continue
        parts.append(esc(raw[cursor:c0]))
        if r["i"] in show:
            parts.append(f'<span class="pw" data-src="{clip_src(r["i"])}" '
                         f'title="听起来像：{esc(" / ".join(r["diff"]) or "漏读")}｜点我听你读的原音">'
                         f'{esc(r["raw"])}</span>')
            parts.append(f'<b class="refmini" data-src="{word_ref_src(r["raw"])}" '
                         f'title="参考发音"></b>')
        else:
            parts.append(esc(r["raw"]))
        cursor = c1
    parts.append(esc(raw[cursor:]))

    bad, good = line_src(li), sent_ref_src(li)
    btns = ""
    if bad:
        btns += f'<button class="btn" data-wrong="1" data-src="{bad}">▶ 原句</button>'
    if good:
        btns += f'<button class="btn ref" data-ref-btn="1" data-src="{good}">✓ 参考</button>'
    line_rows.append(f'<div class="ln playitem"><div class="lno">{_seq}</div>'
                     f'<div class="ltx">{"".join(parts)}</div>'
                     f'<div class="lbtn">{btns}</div></div>')

# 报告只保留三个板块，不再输出「识别器不可靠的位置」
annot_num = "三"


def autobar(key):
    return ('<span class="autobar">'
            f'<label class="opt"><input type="radio" name="mode-{key}" value="ref"><i></i>仅参考</label>'
            f'<label class="opt"><input type="radio" name="mode-{key}" value="both" checked><i></i>原音+参考</label>'
            f'<button class="btn auto" data-auto="{key}">▶ 自动朗读</button>'
            f'<button class="btn cancel" data-cancel="{key}">■ 取消</button>'
            '</span>')

html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(TITLE)}</title><style>
{CSS}
</style></head><body><div class="scene">{SCENE}</div><div class="wrap">

<div class="hero">
<h1>{esc(TITLE)}</h1>
<p class="sub">{SUBTITLE}</p>
<div class="grass"></div>
</div>

<h2><span class="blk"></span>一、发音习惯改善{autobar("sec1")}</h2>
<section id="sec1" class="sec"><div class="card">{''.join(pat_html) or '<p class="desc">（本次未配置分组）</p>'}</div></section>

<h2><span class="blk"></span>二、连贯朗读{autobar("sec2")}</h2>
<section id="sec2" class="sec"><div class="card plain">{sec2_html}</div></section>

<h2><span class="blk"></span>{annot_num}、全文标注{autobar("sec3")}</h2>
<p class="sub" style="margin:0 0 12px">只列出有发音问题的句子。点红字听你的原音，点绿块听参考发音。</p>
<section id="sec3" class="sec"><div class="card">{''.join(line_rows)}</div></section>
</div>
<script>
const DING="{DING}";
let token=0,cur=null;
function stopAudio(){{ token++; if(cur){{ try{{cur.pause();}}catch(e){{}} cur=null; }} }}
function play(src,t){{ return new Promise(r=>{{
  if(t!==token){{ r(); return; }}
  cur=new Audio(src);
  cur.onended=()=>r(); cur.onerror=()=>r();
  cur.play().catch(()=>r());
}}); }}
function sleep(ms){{ return new Promise(r=>setTimeout(r,ms)); }}
function clearMarks(){{
  document.querySelectorAll('.auto-on').forEach(e=>e.classList.remove('auto-on'));
  document.querySelectorAll('.lit').forEach(e=>e.classList.remove('lit'));
  document.querySelectorAll('.autobar .btn').forEach(b=>b.classList.remove('active'));
  document.querySelectorAll('.btn.cancel.floating').forEach(b=>b.classList.remove('floating'));
}}
function resetAll(){{ stopAudio(); clearMarks(); }}

async function run(key){{
  resetAll();
  const t=++token;
  const sec=document.getElementById(key); if(!sec) return;
  const btn=document.querySelector('[data-auto="'+key+'"]');
  if(btn) btn.classList.add('active');
  const cbtn=document.querySelector('[data-cancel="'+key+'"]');
  if(cbtn) cbtn.classList.add('floating');
  const modeEl=document.querySelector('input[name="mode-'+key+'"]:checked');
  const mode=modeEl?modeEl.value:'both';
  const items=[...sec.querySelectorAll('.playitem')];
  for(const it of items){{
    if(t!==token) return;
    it.classList.add('auto-on');
    it.scrollIntoView({{block:'center',behavior:'smooth'}});
    if(mode==='both'){{
      for(const w of [...it.querySelectorAll('[data-wrong]')]){{
        if(t!==token) return;
        w.classList.add('lit');
        await play(w.getAttribute('data-src'),t);
        w.classList.remove('lit');
        await sleep(300);
      }}
      if(t!==token) return;
      await play(DING,t);
      await sleep(160);
    }}
    if(t!==token) return;
    const rb=it.querySelector('[data-ref-btn]');
    if(rb){{ rb.classList.add('lit'); await play(rb.getAttribute('data-src'),t); rb.classList.remove('lit'); }}
    await sleep(200);
    it.classList.remove('auto-on');
  }}
  if(t===token) clearMarks();
}}

document.addEventListener('click',e=>{{
  const a=e.target.closest('[data-auto]');
  if(a){{ e.preventDefault(); run(a.getAttribute('data-auto')); return; }}
  const c=e.target.closest('[data-cancel]');
  if(c){{ e.preventDefault(); resetAll(); return; }}
  const el=e.target.closest('[data-src]'); if(!el) return;
  const src=el.getAttribute('data-src'); if(!src) return;
  resetAll();
  const au=new Audio(src); cur=au; au.play();
  if(el.classList.contains('btn')){{ el.classList.add('lit'); au.onended=()=>el.classList.remove('lit'); }}
}});
</script></body></html>"""

out = os.path.join(D, out_name)
open(out, "w", encoding="utf-8").write(html)
print(f"OK {len(html)/1048576:.2f}MB -> {out}")
print(f"明确听错 {len(high)} 词 | 问题句 {len(line_rows)}/{len(lines)} | 分组 {len(pat_html)} | 整句 {len(sent_rows)}")
