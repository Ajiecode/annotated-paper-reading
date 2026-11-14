# -*- coding: utf-8 -*-
"""Dump the paper page by page, so page N ↔ section mapping can be fixed before annotating.

    python extract.py --src paper.pdf --out paper.txt
"""
import argparse
import pymupdf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    d = pymupdf.open(args.src)
    with open(args.out, "w", encoding="utf-8") as f:
        for i, pg in enumerate(d):
            f.write("===== PAGE %d =====\n" % (i + 1))
            f.write(pg.get_text())
            f.write("\n")
    print("pages", d.page_count, "->", args.out)


if __name__ == "__main__":
    main()
