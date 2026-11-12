"""Build docs/changelog.html from the changelog in metadata.txt.

Run from anywhere with any Python 3 (no extra packages needed):

    python docs/make_changelog.py

Re-run it whenever a version is added to metadata.txt.
"""
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
METADATA = os.path.join(HERE, "..", "metadata.txt")
OUT = os.path.join(HERE, "changelog.html")

VERSION_LINE = re.compile(r"^(\d+\.\d+(?:\.\d+)?)\s*(.*)$")


def read_changelog(path):
    """Return [(version, [items])] in file order (newest first)."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    start = next(i for i, ln in enumerate(lines) if ln.startswith("changelog="))
    block = [lines[start][len("changelog="):]]
    for ln in lines[start + 1:]:
        if ln and not ln[0].isspace():  # next key or comment ends the block
            break
        block.append(ln)

    versions = []
    for raw in block:
        text = raw.strip()
        if not text:
            continue
        m = VERSION_LINE.match(text)
        if m:
            versions.append((m.group(1), []))
            if m.group(2).strip():
                versions[-1][1].append(m.group(2).strip())
        elif text.startswith("*") and versions:
            versions[-1][1].append(text.lstrip("*").strip())
        elif versions:  # continuation of the previous item
            if versions[-1][1]:
                versions[-1][1][-1] += " " + text
            else:
                versions[-1][1].append(text)
    return versions


def read_version(path):
    with open(path, encoding="utf-8") as f:
        for ln in f:
            if ln.startswith("version="):
                return ln.split("=", 1)[1].strip()
    return ""


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tomofast-x-q Changelog</title>
<style>
:root {{
  --bg: #ffffff; --fg: #1d2329; --muted: #5d6873; --line: #dfe3e8;
  --card: #f6f8fa; --accent: #2f6f3e; --link: #1f5fa8;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #15191d; --fg: #e3e7eb; --muted: #9aa5b1; --line: #2c333a;
    --card: #1c2228; --accent: #7cc48d; --link: #7fb2ec;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #15191d; --fg: #e3e7eb; --muted: #9aa5b1; --line: #2c333a;
  --card: #1c2228; --accent: #7cc48d; --link: #7fb2ec;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
main {{ max-width: 860px; margin: 0 auto; padding: 32px 16px 64px; }}
a {{ color: var(--link); }}
h1 {{ font-size: 1.9rem; margin: 0 0 4px; }}
.sub {{ color: var(--muted); margin: 0 0 24px; }}
nav.links {{ display: flex; flex-wrap: wrap; gap: 8px 16px; margin-bottom: 28px; font-size: .95rem; }}
.jump {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 28px; }}
.jump a {{ text-decoration: none; border: 1px solid var(--line); border-radius: 999px;
  padding: 2px 10px; font-size: .85rem; color: var(--fg); background: var(--card); }}
section {{ border-top: 1px solid var(--line); padding: 18px 0 6px; }}
section h2 {{ font-size: 1.2rem; margin: 0 0 8px; display: flex; align-items: baseline; gap: 10px; }}
.latest {{ font-size: .75rem; font-weight: 600; color: var(--bg); background: var(--accent);
  border-radius: 999px; padding: 1px 8px; }}
ul {{ margin: 0 0 10px; padding-left: 22px; }}
li {{ margin: 4px 0; }}
footer {{ margin-top: 40px; color: var(--muted); font-size: .85rem; }}
</style>
</head>
<body>
<main>
<h1>Tomofast-x-q changelog</h1>
<p class="sub">Changes to the Tomofast-x QGIS plugin and ArcGIS Pro toolbox, newest first. Current version: <strong>{current}</strong>.</p>
<nav class="links">
  <a href="user_manual.html">User manual</a>
  <a href="reference_manual.html">Reference manual</a>
  <a href="https://github.com/TOMOFAST/tomofast-x-q">GitHub repository</a>
</nav>
<div class="jump">{jump}</div>
{sections}
<footer>Generated from <code>metadata.txt</code> by <code>docs/make_changelog.py</code>.</footer>
</main>
</body>
</html>
"""


def build():
    versions = read_changelog(METADATA)
    current = read_version(METADATA)
    jump = "".join(
        '<a href="#v{0}">{0}</a>'.format(html.escape(v)) for v, _ in versions
    )
    sections = []
    for i, (v, items) in enumerate(versions):
        badge = ' <span class="latest">latest</span>' if i == 0 else ""
        lis = "\n".join("  <li>{}</li>".format(html.escape(it)) for it in items)
        body = "<ul>\n{}\n</ul>".format(lis) if items else ""
        sections.append(
            '<section id="v{0}">\n<h2>Version {0}{1}</h2>\n{2}\n</section>'.format(
                html.escape(v), badge, body
            )
        )
    page = PAGE.format(current=html.escape(current), jump=jump, sections="\n".join(sections))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print("Wrote {} ({} versions)".format(OUT, len(versions)))


if __name__ == "__main__":
    build()
