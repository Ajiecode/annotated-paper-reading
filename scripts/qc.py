# -*- coding: utf-8 -*-
"""Layout QC for the assembled PDF: catches the failures that are invisible at a glance.

    python qc.py annotated.pdf
"""
import sys
import pymupdf

PAPER_L, PAPER_R = 239.0, 773.0     # canvas geometry defaults
COL_L, COL_R = 272.7, 741.6
BOX_L, BOX_R = 232.0, 778.0
BOTTOM = 750.0


def main(path):
    d = pymupdf.open(path)
    total_issue = 0
    for pno in range(d.page_count):
        pg = d[pno]
        issues = []
        for blk in pg.get_text("dict")["blocks"]:
            for line in blk.get("lines", []):
                for s in line["spans"]:
                    col = s["color"]
                    r, g, b = (col >> 16) & 255, (col >> 8) & 255, col & 255
                    x0, y0, x1, y1 = s["bbox"]
                    txt = s["text"]
                    if r > 150 and g < 90 and b < 90 and s["size"] < 9:
                        if x1 > COL_L + 2 and x0 < COL_R - 2:
                            issues.append(("gloss-on-text", round(x0), round(y0), txt[:16]))
                    if txt.strip() and (x0 < 2 or x1 > 1010 or y1 > 792):
                        if not (x0 < BOX_L or x0 > BOX_R):
                            issues.append(("off-canvas", round(x0), round(y0), txt[:16]))
                    if txt.strip() and len(txt.strip()) <= 2 and txt.strip()[0] in "。，、；：）":
                        issues.append(("orphan-punct", round(x0), round(y0), txt.strip()))
        for dr in pg.get_drawings():
            rr = dr["rect"]
            if 180 < rr.width < 240 and rr.y1 > BOTTOM:
                issues.append(("box-too-low", round(rr.y0), round(rr.y1)))
        if issues:
            total_issue += len(issues)
            print("page", pno + 1, issues[:8])
    print("qc done, pages", d.page_count, "issues", total_issue)
    return 1 if total_issue else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "out.pdf"))
