# -*- coding: utf-8 -*-
"""Anchor probe — run this BEFORE writing the spec.

Every box / gloss / underline needs a phrase that `page.search_for()` can find.
Hyphenation, line breaks and font-subset quirks break many candidates, so probe
first and keep only phrases that return >=1 hit on the intended page.

    python probe.py --src paper.pdf --page 5 "average degree" "NP-hardness"
    python probe.py --src paper.pdf --page 5 --file candidates.txt
"""
import argparse
import pymupdf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--page", type=int, required=True)
    ap.add_argument("--file", help="one candidate phrase per line")
    ap.add_argument("phrases", nargs="*")
    args = ap.parse_args()

    cands = list(args.phrases)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            cands += [ln.strip() for ln in f if ln.strip()]

    pg = pymupdf.open(args.src)[args.page - 1]
    for c in cands:
        rects = pg.search_for(c)
        if not rects:
            print("MISS  %-52s  (try a shorter phrase inside one line)" % c)
        else:
            r = sorted(rects, key=lambda x: (round(x.y0, 1), x.x0))[0]
            print("OK%-3d %-52s  x=%.0f y=%.0f w=%.0f" % (len(rects), c, r.x0, r.y0, r.width))


if __name__ == "__main__":
    main()
