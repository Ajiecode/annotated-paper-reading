# -*- coding: utf-8 -*-
"""annotated-pdf engine.

Landscape canvas, source page centred at full height, Chinese margin notes on
both sides, red Chinese glosses inside the paper's own white margins.

Everything here is generic: page geometry, fonts and colour roles are
configurable, so the same engine works for any journal PDF (Elsevier,
Springer, IEEE two-column, single-column preprint ...).
"""
import math
import os
import pymupdf

# ---------------------------------------------------------------- geometry
GEO = dict(
    canvas_w=1012, canvas_h=792,
    top=36, paper_h=712,          # paper height on canvas
    box_w=226,                    # margin box width
    left_x=6, right_x=780,        # margin box left edge
    bottom=748,                   # never draw a box below this
    col_frac=(0.063, 0.941),      # body-text left / right edge, as fraction of page width
)

KIND = {
    "blue": dict(fill=(0.918, 0.945, 0.972), border=(0.667, 0.776, 0.878),
                 title=(0.086, 0.278, 0.455), body=(0.145, 0.341, 0.537)),
    "red": dict(fill=(0.996, 0.945, 0.929), border=(0.902, 0.725, 0.663),
                title=(0.596, 0.196, 0.110), body=(0.490, 0.251, 0.169)),
    "green": dict(fill=(0.925, 0.965, 0.937), border=(0.702, 0.863, 0.769),
                  title=(0.067, 0.420, 0.204), body=(0.110, 0.392, 0.231)),
    "amber": dict(fill=(1.0, 0.973, 0.906), border=(0.922, 0.831, 0.647),
                  title=(0.475, 0.306, 0.0), body=(0.412, 0.282, 0.035)),
}

RED = (0.784, 0.051, 0.0)
RED_TITLE = (0.596, 0.196, 0.110)
BLUE_INK = (0.129, 0.243, 0.482)
GREY = (0.42, 0.42, 0.42)

# ---------------------------------------------------------------- fonts
_FONT_FILES = {
    "yh": [r"C:\Windows\Fonts\msyh.ttc",
           "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
           "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"],
    "yhb": [r"C:\Windows\Fonts\msyhbd.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"],
    "song": [r"C:\Windows\Fonts\simsun.ttc",
             "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
             "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"],
    "hei": [r"C:\Windows\Fonts\simhei.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"],
}


def load_fonts(extra_dirs=()):
    out = {}
    for key, cands in _FONT_FILES.items():
        for path in list(cands) + [os.path.join(d, n) for d in extra_dirs
                                   for n in (os.path.basename(c) for c in cands)]:
            if os.path.exists(path):
                out[key] = pymupdf.Font(fontfile=path)
                break
        else:
            raise RuntimeError("no usable font for %r; install a CJK font or pass extra_dirs" % key)
    return out


FONTS = load_fonts()


# ---------------------------------------------------------------- wrapping
def wrap(text, font, size, width):
    """Greedy CJK/latin wrap that never leaves closing punctuation orphaned."""
    if "\n" in text:
        out = []
        for para in text.split("\n"):
            out.extend(wrap(para, font, size, width))
        return out
    close = "。，、；：）」』%》！？·,.;:)"
    open_ = "（《「『(["
    out, cur, i, n = [], "", 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isascii() and (ch.isalnum() or ch in "-/.'%:×→≈≤≥+*()[]"):
            j = i
            while j < n and text[j].isascii() and (text[j].isalnum() or text[j] in "-/.'%:×→≈≤≥+*()[]"):
                j += 1
            tok = text[i:j]
        else:
            tok, j = ch, i + 1
        if cur and font.text_length(cur + tok, fontsize=size) > width:
            out.append(cur)
            cur = tok.lstrip() if tok.strip() else ""
        else:
            cur += tok
        i = j
    if cur:
        out.append(cur)
    fixed = []
    for ln in out:
        while fixed and ln and ln[0] in close:
            cand = fixed[-1] + ln[0]
            if font.text_length(cand, fontsize=size) > width + size * 1.1:
                break
            fixed[-1] = cand
            ln = ln[1:]
        if not ln:
            continue
        if fixed and fixed[-1] and fixed[-1][-1] in open_:
            ln = fixed[-1][-1] + ln
            fixed[-1] = fixed[-1][:-1]
        fixed.append(ln)
    res = [ln for ln in fixed if ln.strip()]
    if len(res) > 1 and all(ch in close for ch in res[-1]):
        res[-2] += res[-1]
        res.pop()
    return res


class Builder:
    def __init__(self, src_path, geo=None, fonts=None):
        self.src = pymupdf.open(src_path)
        self.out = pymupdf.open()
        self.geo = dict(GEO)
        if geo:
            self.geo.update(geo)
        self.fonts = fonts or FONTS
        self.warn = []
        self.writers = {}
        self.page = None
        self.sp = None

    # ------------------------------------------------------------- pages
    def open_page(self, pno):
        g = self.geo
        self.sp = self.src[pno - 1]
        s = g["paper_h"] / self.sp.rect.height
        w = self.sp.rect.width * s
        x0 = (g["canvas_w"] - w) / 2.0
        rect = pymupdf.Rect(x0, g["top"], x0 + w, g["top"] + g["paper_h"])
        self.page = self.out.new_page(width=g["canvas_w"], height=g["canvas_h"])
        self.page.show_pdf_page(rect, self.src, pno - 1)
        self.writers = {}
        self.rect = rect
        self.scale = s
        self.col_l = rect.x0 + g["col_frac"][0] * rect.width
        self.col_r = rect.x0 + g["col_frac"][1] * rect.width

    def blank(self):
        g = self.geo
        self.page = self.out.new_page(width=g["canvas_w"], height=g["canvas_h"])
        self.writers = {}
        self.rect = self.page.rect
        self.sp = None

    def flush(self):
        for tw in self.writers.values():
            tw.write_text(self.page)
        self.writers = {}

    def _map(self, r):
        d = self.rect
        return pymupdf.Rect(d.x0 + r.x0 * self.scale, d.y0 + r.y0 * self.scale,
                            d.x0 + r.x1 * self.scale, d.y0 + r.y1 * self.scale)

    # -------------------------------------------------------- primitives
    def text(self, x, y, s, font="yh", size=8.3, color=(0, 0, 0)):
        key = tuple(round(c, 4) for c in color)
        tw = self.writers.get(key)
        if tw is None:
            tw = pymupdf.TextWriter(self.page.rect)
            tw.color = color
            self.writers[key] = tw
        tw.append((x, y), s, font=self.fonts[font], fontsize=size)

    def line(self, p0, p1, color=RED, width=0.85):
        self.page.draw_line(p0, p1, color=color, width=width)

    def hline(self, x0, x1, y, color=(0.85, 0.85, 0.85), width=0.6):
        self.page.draw_line((x0, y), (x1, y), color=color, width=width)

    def panel(self, r, fill=None, border=(0, 0, 0), width=0.7, radius=0.0):
        self.page.draw_rect(r, color=border, fill=fill, width=width,
                            radius=radius if radius else None)

    def box_height(self, w, title, body, tsize=9.0, bsize=8.4, pad=8.5):
        tl = wrap(title, self.fonts["yhb"], tsize, w - 2 * pad)
        bl = wrap(body, self.fonts["yh"], bsize, w - 2 * pad)
        return 7.5 + len(tl) * tsize * 1.34 + 3.5 + len(bl) * bsize * 1.56 + 7.5

    def box(self, x, y, w, kind, title, body, tsize=9.0, bsize=8.4, pad=8.5):
        c = KIND[kind]
        th = tsize * 1.34
        tl = wrap(title, self.fonts["yhb"], tsize, w - 2 * pad)
        bl = wrap(body, self.fonts["yh"], bsize, w - 2 * pad)
        lineh = bsize * 1.56
        h = 7.5 + len(tl) * th + 3.5 + len(bl) * lineh + 7.5
        r = pymupdf.Rect(x, y, x + w, y + h)
        self.panel(r, fill=c["fill"], border=c["border"], width=0.7, radius=0.14)
        yy = y + 7.5
        for ln in tl:
            yy += th
            self.text(x + pad, yy - th * 0.26, ln, "yhb", tsize, c["title"])
        yy += 3.5
        for ln in bl:
            yy += lineh
            self.text(x + pad, yy - lineh * 0.29, ln, "yh", bsize, c["body"])
        return r

    def table(self, x, y, w, rows, ratios, fs=7.8, hfs=8.2, pady=5.0, padx=6):
        colw = [w * r / sum(ratios) for r in ratios]
        lh = fs * 1.5
        hh = hfs * 1.5
        heights = []
        for i, row in enumerate(rows):
            n = 1
            for c, cell in enumerate(row):
                n = max(n, len(wrap(cell, self.fonts["yh"], hfs if i == 0 else fs, colw[c] - 2 * padx)))
            heights.append(pady * 2 + n * (hh if i == 0 else lh))
        total = sum(heights)
        self.panel(pymupdf.Rect(x, y, x + w, y + total), fill=(1, 1, 1),
                  border=(0.80, 0.80, 0.80), width=0.7)
        yy = y
        for i, row in enumerate(rows):
            h, fs_i, lh_i = heights[i], (hfs if i == 0 else fs), (hh if i == 0 else lh)
            if i == 0:
                self.panel(pymupdf.Rect(x, yy, x + w, yy + h), fill=(0.918, 0.945, 0.972),
                          border=None, width=0)
            xx = x
            for c, cell in enumerate(row):
                ty = yy + pady + lh_i * 0.78
                for ln in wrap(cell, self.fonts["yh"], fs_i, colw[c] - 2 * padx):
                    self.text(xx + padx, ty, ln, "yhb" if i == 0 else "yh", fs_i,
                              (0.086, 0.278, 0.455) if i == 0 else (0.12, 0.13, 0.15))
                    ty += lh_i
                if c:
                    self.line((xx, yy), (xx, yy + h), (0.86, 0.86, 0.86), 0.6)
                xx += colw[c]
            yy += h
            if i:
                self.line((x, yy), (x + w, yy), (0.86, 0.86, 0.86), 0.6)
        return y + total

    # ------------------------------------------------------- annotations
    def find(self, phrase, occ=0):
        rects = self.sp.search_for(phrase)
        if not rects:
            self.warn.append(("anchor-miss", self.sp.number + 1, phrase))
            return None
        rects.sort(key=lambda r: (round(r.y0, 1), r.x0))
        return self._map(rects[min(occ, len(rects) - 1)])

    def mark(self, r, color=RED, width=1.05):
        self.page.draw_line((r.x0 - 0.5, r.y1 + 0.9), (r.x1 + 0.5, r.y1 + 0.9),
                            color=color, width=width)

    def gloss(self, phrase, txt, side="L", occ=0, size=7.4, color=RED, gap=3.5):
        """Red Chinese gloss sitting in the paper's own white margin + red underline."""
        r = self.find(phrase, occ)
        if r is None:
            return None
        w = self.fonts["song"].text_length(txt, fontsize=size)
        y = (r.y0 + r.y1) / 2 + size * 0.42
        x = (self.col_l - gap - w) if side == "L" else (self.col_r + gap)
        if side == "L" and x < self.rect.x0 + self.geo["box_w"] * 0 + 4:
            x = self.rect.x0 + 4
        self.text(x, y, txt, "song", size, color)
        self.mark(r, color)
        if side == "L":
            g = r.x0 - (x + w)
            if 0 < g < 26:
                self.line((x + w + 1.0, r.y1 + 0.9), (r.x0 - 1.0, r.y1 + 0.9), color, 0.6)
        else:
            g = x - r.x1
            if 0 < g < 26:
                self.line((r.x1 + 1.0, r.y1 + 0.9), (x - 1.0, r.y1 + 0.9), color, 0.6)
        return r

    def arrow(self, p0, p1, color=BLUE_INK, width=0.8):
        x0, y0 = p0
        x1, y1 = p1
        dx, dy = x1 - x0, y1 - y0
        c1 = (x0 + dx * 0.35, y0 + dy * 0.02)
        c2 = (x0 + dx * 0.70, y1 - dy * 0.10)
        pts = []
        for i in range(28):
            t = i / 27.0
            a, b, cc, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
            pts.append((a * x0 + b * c1[0] + cc * c2[0] + d * x1,
                        a * y0 + b * c1[1] + cc * c2[1] + d * y1))
        for i in range(len(pts) - 1):
            self.line(pts[i], pts[i + 1], color, width)
        ang = math.atan2(pts[-1][1] - pts[-5][1], pts[-1][0] - pts[-5][0])
        L, W = 4.6, 2.2
        self.line((x1 - L * math.cos(ang) + W * math.sin(ang),
                   y1 - L * math.sin(ang) - W * math.cos(ang)), (x1, y1), color, width)
        self.line((x1 - L * math.cos(ang) - W * math.sin(ang),
                   y1 - L * math.sin(ang) + W * math.cos(ang)), (x1, y1), color, width)

    def footer(self, left_text, pno, total):
        g = self.geo
        self.text(g["left_x"] + 2, g["canvas_h"] - 6, left_text, "yh", 6.6, (0.52, 0.52, 0.52))
        t = "%d / %d" % (pno, total)
        w = self.fonts["yh"].text_length(t, fontsize=6.6)
        self.text(g["right_x"] + g["box_w"] - w, g["canvas_h"] - 6, t, "yh", 6.6,
                  (0.52, 0.52, 0.52))
