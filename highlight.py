# TODO visualize the spans of an ast node. needs to use fmt/reverse parse
import testlang
import random
def palette(n, s=0.5, v=0.5):
    # generate n equally spaced hues
    h = 360 * random.random()
    step = 360/n
    for _ in range(n):
        h = (h + step) % 360
        s = min(max(20, random.gauss(80, 60)), 100)
        l = min(max(20, random.gauss(80, 60)), 90)
        yield f'hsl({h}, {s}%, {l}%)'

node_t = set()
def walk(n):
    if n and isinstance(n, (tuple, list)):
        node_t.add(n[0])
        for x in n:
            walk(x)
walk(testlang.sample_ast)

def tohtml(n):
    if isinstance(n, str):
        return n
    t, *args = n
    body = ''.join(tohtml(a) for a in args)
    return f'<span class={t!r}>{body}</span>'
body = tohtml(testlang.sample_ast)
css = (
        ''.join(f'.{node} {{background-color: {color};}}' for node, color in zip(node_t, palette(len(node_t))))
)

with open('boxtext.html', 'w') as f:
    f.write(f"""<!DOCTYPE html>
<html>
  <head>
    <title>Title of the document</title>
    <style>
      span {{ border-radius: 10px; padding: 5px;}}
      {css}
    </style>
  </head>
  <body>
    <p>{body}</p>
  </body>
</html>
""")
