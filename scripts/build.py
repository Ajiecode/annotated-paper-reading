# -*- coding: utf-8 -*-
"""Assemble an annotated close-reading PDF.

Usage:
    python build.py --src paper.pdf --spec spec.py --out annotated.pdf
    python build.py --src paper.pdf --spec spec.py --out test.pdf --limit 3

The spec module supplies PAGES (one entry per paper page) plus optional REVIEW /
LESSON dicts that become extra full-canvas summary pages. See
references/spec-format.md.
"""
import argparse
import importlib.util
import os
import sys

import pymupdf

import appendix
from engine import Builder, KIND

GAP = 12          # vertical gap between two boxes in the same margin column
START_Y = 46      # first box top
ARROW_DX = 150    # only draw a leader arrow when the target is this close
ARROW_DY = 240


def load_spec(path):
    spec = importlib.util.spec_from_file_location("paper_spec", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def place_boxes(b, boxes, warn):
    per = {"L": [], "R": []}
    for item in boxes:
        side, y, kind, title, body = item[:5]
        anchor = item[5] if len(item) > 5 else None
        occ = item[6] if len(item) > 6 else 0
        r = b.find(anchor, occ) if anchor else None
        per[side].append([y, kind, title, body, r])

    placed = []
    for side in ("L", "R"):
        y = START_Y
        for it in sorted(per[side], key=lambda t: t[0]):
            y = max(it[0], y)
            x = b.geo["left_x"] if side == "L" else b.geo["right_x"]
            if y + 40 > b.geo["bottom"]:
                warn.append(("overflow", b.sp.number + 1, it[2]))
            r = b.box(x, y, b.geo["box_w"], it[1], it[2], it[3])
            placed.append((side, r, it[4]))
            y = r.y1 + GAP
    return placed


def arrow_to(b, side, box_rect, target):
    if target is None:
        return
    in_right = target.x0 > b.rect.x0 + b.rect.width * 0.5
    tx = target.x1 + 2.5 if in_right else target.x0 - 2.5
    ty = (target.y0 + target.y1) / 2
    sx = box_rect.x1 if side == "L" else box_rect.x0
    cy = (box_rect.y0 + box_rect.y1) / 2
    if abs(tx - sx) <= ARROW_DX and abs(ty - cy) <= ARROW_DY:
        sy = min(max(ty, box_rect.y0 + 9), box_rect.y1 - 9)
        b.arrow((sx, sy), (tx, ty), (0.16, 0.30, 0.55) if side == "L" else (0.60, 0.19, 0.11), 0.8)


def build_paper_page(b, pg, total, footer_prefix):
    b.open_page(pg["p"])
    for i, ln in enumerate(pg.get("head", [])):
        b.text(b.geo["left_x"] + 2, 14 + i * 10.5, ln, "yh", 7.6, (0.45, 0.45, 0.45))

    rt = pg.get("redtitle")
    if rt:
        ys = 54
        for ln in rt:
            b.text(b.geo["left_x"] + 2, ys, ln, "song", 9.8, (0.62, 0.12, 0.08))
            ys += 14
        b.line((b.geo["left_x"] + 2, ys - 3), (b.geo["left_x"] + 152, ys - 3),
               (0.78, 0.10, 0.05), 0.9)

    placed = place_boxes(b, pg["boxes"], b.warn)
    for side, r, tgt in placed:
        arrow_to(b, side, r, tgt)
    for g in pg.get("gloss", []):
        phrase, txt, side, occ = g[:4]
        b.gloss(phrase, txt, side, occ)
    for m in pg.get("marks", []):
        r = b.find(m[0], m[1] if len(m) > 1 else 0)
        if r:
            b.mark(r)
    b.footer("%s ｜ %s" % (footer_prefix, pg["section"]), pg["p"], total)
    b.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="source paper PDF")
    ap.add_argument("--spec", required=True, help="spec .py (PAGES + optional REVIEW/LESSON)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="only build the first N paper pages")
    ap.add_argument("--preview-dpi", type=int, default=0, help="also render PNG previews at this dpi")
    ap.add_argument("--no-appendix", action="store_true")
    args = ap.parse_args()

    mod = load_spec(args.spec)
    pages = mod.PAGES[:args.limit] if args.limit else mod.PAGES
    extra = 0 if args.no_appendix else (1 if getattr(mod, "REVIEW", None) else 0) + \
        (1 if getattr(mod, "LESSON", None) else 0)
    total = len(getattr(mod, "PAGES")) + extra

    b = Builder(args.src)
    prefix = getattr(mod, "FOOTER", "论文精读批注")

    for pg in pages:
        build_paper_page(b, pg, total, prefix)

    n = len(getattr(mod, "PAGES"))
    if not args.no_appendix:
        if getattr(mod, "REVIEW", None):
            appendix.build_sheet(b, mod.REVIEW, n + 1, total)
        if getattr(mod, "LESSON", None):
            appendix.build_sheet(b, mod.LESSON, n + 1 + (1 if getattr(mod, "REVIEW", None) else 0), total)

    b.out.save(args.out, garbage=4, deflate=True, deflate_images=True, deflate_fonts=True)
    print("saved", args.out, "pages", b.out.page_count, "warn", len(b.warn))
    for w in b.warn:
        print("  ", w)

    if args.preview_dpi:
        d = pymupdf.open(args.out)
        base = os.path.splitext(args.out)[0]
        for i in range(d.page_count):
            d[i].get_pixmap(dpi=args.preview_dpi).save("%s_p%02d.png" % (base, i + 1))
        print("previews ->", base + "_p*.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
