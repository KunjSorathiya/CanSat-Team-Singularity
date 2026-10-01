#!/usr/bin/env python3
"""Build the final project report PDF.

    python build.py            # content/*.md  ->  report.html  ->  ../CanSat-2026-Final-Project-Report.pdf

The chapters are Markdown with a handful of directives (figure, table caption, cross-reference,
chapter opener, table of contents). Headless Chromium prints the HTML. Page numbers in the
contents are measured, not guessed: the first pass prints the PDF, the page of every heading
is read back out of it, and the second pass prints again with the numbers filled in.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from pathlib import Path

import markdown
from pygments.formatters import HtmlFormatter

HERE = Path(__file__).resolve().parent
CONTENT = HERE / "content"
OUT_PDF = HERE.parent / "CanSat-2026-Final-Project-Report.pdf"
HTML = HERE / "report.html"
FLIGHT_FIGS = HERE.parents[2] / "analysis" / "flight-2026-09-30" / "figures"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

FIG_DIRS = [HERE / "figures", FLIGHT_FIGS]
fig_no: dict[str, int] = {}
tab_no: dict[str, int] = {}


def find_fig(name: str) -> str:
    for d in FIG_DIRS:
        if (d / name).exists():
            return str((d / name).relative_to(HERE.parents[2]))
    raise FileNotFoundError(name)


def number_things(text: str):
    for m in re.finditer(r"@@fig ([\w-]+)\s*\|", text):
        fig_no.setdefault(m.group(1), len(fig_no) + 1)
    for m in re.finditer(r"@@tab ([\w-]+)\s*\|", text):
        tab_no.setdefault(m.group(1), len(tab_no) + 1)


def expand(text: str) -> str:
    def fig(m):
        parts = [p.strip() for p in m.group(1).split("|")]
        key, path, cap = parts[0], parts[1], parts[2]
        width = parts[3] if len(parts) > 3 else "100%"
        cls = "card" if path.startswith(("photo", "photos/")) else ""
        src = ("file://" + str(HERE.parents[2] / find_fig(path))) if not path.startswith("photos/") else ("file://" + str(HERE / "figures" / path))
        cap_html = markdown.markdown(cap, extensions=["extra"]).replace("<p>", "").replace("</p>", "")
        return (f'<figure class="{cls}"><img src="{src}" style="width:{width}"/>'
                f'<figcaption><b>Figure {fig_no[key]}</b> · {cap_html}</figcaption></figure>')
    text = re.sub(r"@@fig ([^@]+)@@", fig, text)
    text = re.sub(r"@@tab ([\w-]+)\s*\|\s*([^@]+)@@",
                  lambda m: f'<div class="tabcap"><b>Table {tab_no[m.group(1)]}</b> · {html.escape(m.group(2).strip())}</div>\n', text)
    text = re.sub(r"@@ref ([\w-]+)@@", lambda m: (f"Figure {fig_no[m.group(1)]}" if m.group(1) in fig_no else f"Table {tab_no[m.group(1)]}"), text)
    text = re.sub(r"@@gallery ([^@]+)@@", gallery, text)
    return text


def gallery(m):
    lines = [l.strip() for l in m.group(1).strip().splitlines() if l.strip()]
    cls = lines[0]
    figs = []
    for l in lines[1:]:
        f, cap = [p.strip() for p in l.split("|", 1)]
        figs.append(f'<figure><img src="file://{HERE / "figures" / "photos" / f}"/><figcaption>{html.escape(cap)}</figcaption></figure>')
    return f'<div class="gallery {cls}">' + "".join(figs) + "</div>"


MD = markdown.Markdown(extensions=["extra", "toc", "md_in_html", "sane_lists",
                                   "codehilite"],
                       extension_configs={"codehilite": {"css_class": "codehilite", "guess_lang": False},
                                          "toc": {"permalink": False}})


def render_chapter(path: Path, pages: dict):
    raw = path.read_text()
    m = re.match(r"@@chapter (\w+) \| ([^|]+)\|([^@]*)@@\n", raw)
    body = raw
    head = ""
    chapter = None
    if m:
        chapter = dict(num=m.group(1).strip(), title=m.group(2).strip(), tag=m.group(3).strip())
        body = raw[m.end():]
    body = expand(body).replace('<div class="callout', '<div markdown="1" class="callout')
    MD.reset()
    h = MD.convert(body)
    secs = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', h)
    if chapter:
        li = []
        for _, t in secs:
            plain = re.sub("<[^>]+>", "", t)
            m2 = re.match(r"^([\d.A-Z]+)\s+(.*)$", plain)
            num, title = (m2.group(1), m2.group(2)) if m2 else ("", plain)
            li.append(f"<li><b>{num}</b>{title}</li>")
        items = "".join(li)
        head = (f'<section class="opener"><div class="num">{chapter["num"]}</div><div class="band"></div>'
                f'<div class="meta">{"Chapter" if chapter["num"].isdigit() else "Appendix"} {chapter["num"]}</div>'
                f'<h1>{html.escape(chapter["title"])}</h1><div class="tag">{html.escape(chapter["tag"])}</div>'
                f'<ul>{items}</ul></section>')
    return chapter, secs, head + h


def toc_html(entries, pages):
    out = ['<div class="toc">']
    for ch, secs in entries:
        pg = pages.get(ch["title"], "")
        out.append(f'<div class="tc"><span><b>{ch["num"]}</b>{html.escape(ch["title"])}</span><span>{pg}</span></div>')
        for _, t in secs:
            t = re.sub("<[^>]+>", "", t)
            out.append(f'<div class="ts"><span>{html.unescape(t)}</span><span>{pages.get(html.unescape(t), "")}</span></div>')
    out.append("</div>")
    return "\n".join(out)


def build(pages: dict) -> list:
    files = sorted(CONTENT.glob("*.md"))
    for f in files:
        number_things(f.read_text())
    rendered = [render_chapter(f, pages) for f in files]
    entries = [(c, s) for c, s, _ in rendered if c]
    css = (HERE / "report.css").read_text()
    pyg = HtmlFormatter(style="friendly").get_style_defs(".codehilite")
    pyg += "\n.codehilite .hll{background:transparent}.codehilite{background:transparent!important}\n"
    body = "".join(h for _, _, h in rendered)
    body = re.sub(r"<thead>\s*<tr>\s*(?:<th[^>]*>\s*</th>\s*)+</tr>\s*</thead>", "", body)
    body = body.replace("<!--TOC-->", toc_html(entries, pages)).replace("<p>@@toc@@</p>", toc_html(entries, pages))
    doc = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"/><title>CanSat 2026 — Final Project Report · CAN-Team-25</title>'
           f'<style>{css}\n{pyg}</style></head><body>{body}</body></html>')
    HTML.write_text(doc)
    return entries


def print_pdf(out: Path):
    cmd = [CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
           "--allow-file-access-from-files", "--run-all-compositor-stages-before-draw",
           "--virtual-time-budget=60000", f"--print-to-pdf={out}", f"file://{HTML}"]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)


def measure_pages(pdf: Path, entries) -> dict:
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    texts = []
    for p in range(1, n + 1):
        t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
        texts.append(t)
    toc_end = 0
    for i, t in enumerate(texts):
        if "Contents" in t and i < 12:
            toc_end = i + 1
    pages = {}
    start = toc_end
    norm = lambda s: re.sub(r"\s+", " ", s).strip()
    for ch, secs in entries:
        for p in range(start, n):
            if norm(ch["title"]) in norm(texts[p]) and "Chapter" in texts[p] or norm(ch["title"]).upper() in norm(texts[p]).upper() and p >= start and len(norm(texts[p])) < 700:
                pages[ch["title"]] = p + 1
                start = p
                break
        for _, t in secs:
            t = html.unescape(re.sub("<[^>]+>", "", t))
            for p in range(start, n):
                if norm(t)[:60] in norm(texts[p]):
                    pages[t] = p + 1
                    start = p
                    break
    return pages


def main():
    pages: dict = {}
    pj = HERE / "pages.json"
    if pj.exists() and "--fresh" not in sys.argv:
        pages = json.loads(pj.read_text())
    entries = build(pages)
    tmp = HERE / "pass1.pdf"
    print_pdf(tmp)
    newpages = measure_pages(tmp, entries)
    pj.write_text(json.dumps(newpages, indent=1))
    if newpages != pages:
        build(newpages)
        print_pdf(tmp)
        again = measure_pages(tmp, entries)
        if again != newpages:
            pj.write_text(json.dumps(again, indent=1))
            build(again)
            print_pdf(tmp)
    tmp.replace(OUT_PDF)
    print("wrote", OUT_PDF, OUT_PDF.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
