"""Build CHANGELOG.md (repository root) from the changelog in metadata.txt.

Run from anywhere with any Python 3 (no extra packages needed):

    python docs/make_changelog.py

Re-run it whenever a version is added to metadata.txt.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
METADATA = os.path.join(HERE, "..", "metadata.txt")
OUT = os.path.join(HERE, "..", "CHANGELOG.md")

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


HEADER = """# Tomofast-x-q Changelog

Changes to the Tomofast-x QGIS plugin and ArcGIS Pro toolbox, newest first. Current version: **{current}**.

[User Manual](docs/UserManual.md) · [Reference Manual](docs/ReferenceManual.md) · [README](README.md)

<!-- Generated from metadata.txt by docs/make_changelog.py. Edit metadata.txt, not this file. -->
"""


def build():
    versions = read_changelog(METADATA)
    out = [HEADER.format(current=read_version(METADATA))]
    for i, (v, items) in enumerate(versions):
        out.append("## {}{}\n".format(v, " (latest)" if i == 0 else ""))
        out.extend("- {}".format(it) for it in items)
        out.append("")
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    print("Wrote {} ({} versions)".format(os.path.normpath(OUT), len(versions)))


if __name__ == "__main__":
    build()
