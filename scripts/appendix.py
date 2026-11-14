# -*- coding: utf-8 -*-
"""Full-canvas summary sheets (精读总评 / 课题启示) that follow the annotated pages.

A sheet is a plain dict:
    dict(kicker="附页一 · 精读总评", title="...", sub="...",
         blocks=[ ... ])
where each block is either
    dict(kind="blue"|"red"|"green"|"amber", title="【…】", body="…")
    dict(kind="text",  body="一句话结论")          # plain grey line
    dict(kind="table", caption="【…】 说明", rows=[[...], ...], ratios=[.3,.3,.4])
or a list of 1-2 such dicts, which are laid out side by side.
"""
from engine import FONTS

M = 30
CW = 1012 - 2 * M
HALF = 468
GUT = 12
BLUE_D = (0.086, 0.278, 0.455)
SUB = (0.42, 0.42, 0.42)


def _head(b, kicker, title, sub, pno, total):
    b.text(M, 32, kicker, "yh", 8.0, SUB)
    b.text(M, 58, title, "yhb", 16.0, BLUE_D)
    b.text(M, 76, sub, "yh", 8.2, SUB)
    b.hline(M, M + CW, 88, (0.72, 0.78, 0.86), 0.9)
    b.footer("论文精读批注 ｜ " + kicker, pno, total)


def build_sheet(b, data, pno, total):
    b.blank()
    _head(b, data.get("kicker", ""), data.get("title", ""), data.get("sub", ""), pno, total)
    y = 100

    for item in data["blocks"]:
        if isinstance(item, dict):
            kind = item.get("kind", "blue")
            if kind == "text":
                b.text(M, y + 8, item["body"], "yh", item.get("bsize", 8.4), (0.30, 0.30, 0.30))
                y += 14
            elif kind == "table":
                if item.get("caption"):
                    b.text(M, y + 9, item["caption"], "yhb", 9.0, BLUE_D)
                    y += 18
                y = b.table(M, y, CW, item["rows"], item["ratios"],
                            fs=item.get("fs", 7.6), hfs=item.get("hfs", 8.0),
                            pady=item.get("pady", 4.6)) + 11
            else:
                r = b.box(M, y, CW, kind, item["title"], item["body"],
                          bsize=item.get("bsize", 8.8))
                y = r.y1 + 9
        else:
            heights = [b.box_height(HALF, d["title"], d["body"], bsize=d.get("bsize", 8.4))
                       for d in item]
            for i, d in enumerate(item):
                b.box(M + i * (HALF + GUT), y, HALF, d.get("kind", "blue"),
                      d["title"], d["body"], bsize=d.get("bsize", 8.4))
            y = y + max(heights) + 9

    if data.get("closer"):
        b.text(M, y + 6, data["closer"], "yh", 8.4, (0.30, 0.30, 0.30))
    b.flush()
