#!/usr/bin/env python3
"""验收：一次跑完分节切片 + PC/平板/手机三档截图 + 假 Audio 注入验证 JS 行为。

用法: python verify.py <报告.html>

产出在 <报告目录>/_verify/：
  sec1.html sec2.html sec3.html   分节预览页（单独看某一节）
  shot_pc.png                     PC 1280（看第一板块）
  shot_sec2.png shot_sec3.png     PC 下的第二、三板块
  shot_pad.png                    平板 820
  shot_phone.png                  手机 390
  test_auto.html                  注入假 Audio 的测试页

为什么手机要用 iframe：Windows 的 Chrome headless 最小窗口宽约 485 CSS px，
直接 --window-size=390 拿到的是 485 视口、按 390 裁切，会误判成布局溢出。
套一层 390px 宽的 iframe，媒体查询才真正按手机生效。

JS 验证怎么做：注入假的 window.Audio（play() 里 setTimeout 立刻触发 onended），
load 后自动点「自动朗读」，用 --dump-dom 取回状态。
「叮」的判定用 DING 常量的真实 base64 长度（从 HTML 源码里提取，不硬编码）——
注意 const DING 是模块级声明，不挂 window，读不到，只能按长度判。
"""
import json, os, re, sys, subprocess


def find_chrome():
    env = os.environ.get("CHROME_BIN")
    if env and os.path.exists(env):
        return env
    for p in ("C:/Program Files/Google/Chrome/Application/chrome.exe",
              "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
              os.path.expanduser("~/AppData/Local/Google/Chrome/Application/chrome.exe"),
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/usr/bin/google-chrome", "/usr/bin/chromium"):
        if os.path.exists(p):
            return p
    from shutil import which
    for name in ("chrome", "google-chrome", "chromium", "msedge"):
        w = which(name)
        if w:
            return w
    raise SystemExit("找不到 Chrome，可用环境变量 CHROME_BIN 指定路径")


def main():
    report = os.path.abspath(sys.argv[1])
    D = os.path.dirname(report)
    work = os.path.join(D, "_verify")
    os.makedirs(work, exist_ok=True)
    CHROME = find_chrome()
    src = open(report, encoding="utf-8").read()

    m = re.search(r'const DING="([^"]+)"', src)
    ding_len = len(m.group(1)) if m else 0
    print(f"DING base64 长度 = {ding_len}")

    head, sep, body = src.partition("<body>")
    marks = [x.start() for x in re.finditer(r"<h2>", body)]
    print(f"章节数 {len(marks)}")

    def shot(url, out, win):
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--allow-file-access-from-files", f"--window-size={win}",
                        f"--screenshot={out}", url], capture_output=True, timeout=180)
        kb = os.path.getsize(out) // 1024 if os.path.exists(out) else 0
        print(f"  {'OK' if kb else 'FAIL'} {os.path.basename(out):<18} {kb:>4}KB")

    print("\n[1/3] 分节预览页")
    for k in range(len(marks)):
        start = marks[k]
        end = marks[k + 1] if k + 1 < len(marks) else body.find("<script>")
        p = os.path.join(work, f"sec{k+1}.html")
        open(p, "w", encoding="utf-8").write(
            head + "<body>" + body[start:end] + "</div></body></html>")
        print(f"  {os.path.basename(p)}")

    print("\n[2/3] 三档截图")
    url = "file:///" + report.replace("\\", "/")
    shot(url, os.path.join(work, "shot_pc.png"), "1280,1000")
    for k in (2, 3):
        p = os.path.join(work, f"sec{k}.html")
        if os.path.exists(p):
            shot("file:///" + p.replace("\\", "/"),
                 os.path.join(work, f"shot_sec{k}.png"), "1280,1100")
    for w, h, name in ((820, 1800, "pad"), (390, 2200, "phone")):
        p = os.path.join(work, f"frame_{name}.html")
        open(p, "w", encoding="utf-8").write(
            f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
            f'html,body{{margin:0;padding:0;background:#fff}}'
            f'iframe{{width:{w}px;height:{h}px;border:0;display:block}}</style></head>'
            f'<body><iframe src="{url}"></iframe></body></html>')
        shot("file:///" + p.replace("\\", "/"),
             os.path.join(work, f"shot_{name}.png"), f"{w+30},{h+10}")

    print("\n[3/3] JS 自动朗读验证")
    FAKE = """
<script>
window.__log=[];
class FakeAudio{
  constructor(src){this.src=src;this._src=src;}
  play(){ window.__log.push(this._src.length===DINGLEN?'DING':'CLIP'+this._src.length);
    setTimeout(()=>{ if(this.onended) this.onended(); },1);
    return Promise.resolve(); }
  pause(){}
}
Object.defineProperty(window,'Audio',{value:FakeAudio,writable:false,configurable:false});
window.addEventListener('load',()=>{ setTimeout(()=>{
  const sec=document.getElementById('sec1')?'sec1':'sec2';
  document.querySelector('[data-auto="'+sec+'"]').click();
  setTimeout(()=>{
    const d=document.createElement('div'); d.id='RESULT';
    d.textContent=JSON.stringify({
      sec:sec,
      active:document.querySelectorAll('.autobar .btn.active').length,
      floating:document.querySelectorAll('.btn.cancel.floating').length,
      items:document.querySelectorAll('#'+sec+' .playitem').length,
      seq:window.__log.slice(0,14)
    });
    document.body.appendChild(d);
  },5000);
},50);});
</script>""".replace("DINGLEN", str(ding_len))

    p = os.path.join(work, "test_auto.html")
    open(p, "w", encoding="utf-8").write(src.replace("</head>", FAKE + "</head>"))
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu",
                        "--virtual-time-budget=15000", "--dump-dom",
                        "file:///" + p.replace("\\", "/")],
                       capture_output=True, timeout=180)
    mm = re.search(r'<div id="RESULT">([^<]*)', r.stdout.decode("utf-8", "ignore"))
    if not mm:
        print("  未取到结果")
        return
    d = json.loads(mm.group(1))
    print(f"  章节 {d['sec']} | 条目 {d['items']} | 朗读按钮激活 {d['active']} | "
          f"悬浮取消 {d['floating']}")
    print(f"  播放序列: {' '.join(d['seq'])[:200]}")

    # 判定只能看「序列模式」，不能看按钮状态：
    # 假 Audio 几乎瞬间结束，条目少时（例如只有 2 条）放到 5 秒后检查早就跑完并
    # clearMarks() 了，active/floating 必然是 0 —— 那是正常的，不是 bug。
    seq = d["seq"]
    ok = False
    if seq and "DING" in seq:
        # 期望：每条都是「若干错误原声 → 叮 → 参考」，最后一条可能没走完
        first = seq.index("DING")
        ok = first >= 1 and len(seq) > first + 1
    n_ding = sum(1 for x in seq if x == "DING")
    print(f"  {'行为正常' if ok else '异常'}（{len(seq)} 条里有 {n_ding} 次「叮」，"
          f"每条应为：原声… → 叮 → 参考）")
    if not ok and d["items"] == 0:
        print("  该章节没有可朗读条目，检查一下 curated.json 的 patterns.words 是否都对得上 sev=high")
    print(f"\n验收产物在 {work}")


if __name__ == "__main__":
    main()
