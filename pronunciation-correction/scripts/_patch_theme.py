import io, os

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_html.py")
src = io.open(p, encoding="utf-8").read()

anchor = 'rows = json.load(open(os.path.join(D, "words.json"), encoding="utf-8"))["rows"]'
if "CSS = open" not in src:
    inject = (
        'ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")\n'
        'CSS = open(os.path.join(ASSETS, "theme.css"), encoding="utf-8").read()\n'
        'SCENE = open(os.path.join(ASSETS, "scene.svg"), encoding="utf-8").read()\n\n'
        + anchor
    )
    src = src.replace(anchor, inject, 1)

i = src.index('html = f"""')
head, tail = src[:i], src[i:]

a = tail.index("<style>") + len("<style>")
b = tail.index("</style>")
tail = tail[:a] + "\n{CSS}\n" + tail[b:]

tail = tail.replace('<body><div class="wrap">',
                    '<body><div class="scene">{SCENE}</div><div class="wrap">', 1)

io.open(p, "w", encoding="utf-8").write(head + tail)
print("patched")
