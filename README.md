# annotated-paper-reading

把一篇学术论文做成**批注式精读 PDF**：在原文每一页之上叠加中文批注——左右批注栏、原句上的红字译注、红色下划线、引线箭头——并在末尾追加"精读总评"与"课题启示"两个附页，输出一份可检索、可复制的横版 PDF。

这不是 Markdown 读书笔记，也不是摘要翻译。产物是**原论文本身**，判断直接落在作者写下的那行字上。

```
论文原文（Elsevier / Springer / IEEE / 单栏 preprint）
        │
        ├── 左栏批注：这一段在做什么、为什么这样做（结构 / 机制）
        ├── 右栏批注：可不可信、值不值得学（判断 / 批判 / 风险）
        ├── 红字译注：术语与关键量的四字中文，落在论文自身白边
        └── 附页：一句话判断 → 硬伤排序 → 主张/证据强度表 → 课题启示
```

## 版式

- 画布 1012 × 792（A4 横版），原页等比缩至高 712 居中，左右各留 226pt 批注栏；
- 四色分层：**蓝**＝结构与机制，**红**＝批判与硬伤，**绿**＝可复用，**琥珀**＝阅读路线 / 存疑；
- 红字 7.4pt 宋体置于页边，距正文 3.5pt，绝不压在正文行上（正文行距仅 10.5pt，压上去必然叠字）；
- 页脚左侧 `论文精读批注 ｜ §章节`，右侧 `N / total`，分母自动含附页；
- 原页以 Form XObject 嵌入，**文字层完整保留**：可搜索、可复制、可选中，不是图片。

## 安装（作为 Agent Skill）

```bash
git clone https://github.com/<your-name>/annotated-paper-reading.git
```

把整个目录放进技能的加载目录（路径因产品而异，形如 `.../workspace/.user_skills/`）：

```bash
cp -r annotated-paper-reading "<skills-root>/annotated-paper-reading"
```

Windows：

```powershell
Copy-Item -Recurse -LiteralPath .\annotated-paper-reading -Destination "<skills-root>\annotated-paper-reading"
```

之后提出"按这个格式精读这篇论文，给我批注后的 PDF"即会触发。

## 当独立工具用（不需要 Agent）

```bash
pip install pymupdf
python scripts/extract.py --src paper.pdf --out paper.txt          # 建页码地图
python scripts/probe.py   --src paper.pdf --page 5 "graph coloring" # 先探锚点
python scripts/build.py   --src paper.pdf --spec spec.py --out annotated.pdf --preview-dpi 120
python scripts/qc.py      annotated.pdf                            # 非零返回＝有版式问题
```

`build.py` 参数：`--limit N` 只装配前 N 页（试排用）、`--preview-dpi D` 同时导出 PNG 预览、`--no-appendix` 跳过附页。

## 五步流程

1. **建文本地图**：按页导出全文，核对"页码 ↔ 章节"对照表。图表页、双栏断页、参考文献起始页最容易错位，错位会让后面所有批注指向错误的句子。
2. **先判断再落位**：不要边读边写。先定一句话核心贡献、5–8 条按影响排序的硬伤、3–4 条真正可迁移的做法，再分页分配。
3. **探锚点再写 spec**：跨行短语、连字符断词、公式附近、文本层缺失的整段都搜不到，先 `probe.py` 验证，只留能命中的。
4. **装配与质检**：`qc.py` 抓四类肉眼难发现的问题——红字压正文、批注框越底线、孤行标点、文本越出画布。清零后再看图。
5. **附页与交付**：总评页 + 启示页；确认页数、页脚连续、文字可检索、原始 PDF 未被改动。

每页配额（超过就说明在复述，不是精读）：批注框 3–6 个、红字译注 2–4 条、下划线 1–2 条。

## 目录结构

```
SKILL.md                    触发条件、五步流程、文案口径、失败处理
scripts/
  extract.py                按页导出全文
  probe.py                  批量探测 search_for 锚点
  build.py                  装配 CLI
  engine.py                 渲染引擎（几何/字体/配色/CJK 换行/框/表/红字/贝塞尔箭头）
  appendix.py               附页全幅排版
  qc.py                     版式质检
references/
  spec-format.md            spec 字段表、锚点规则、每页配额
  layout.md                 画布参数、配色表、字体策略、改代码前必读的十个坑
assets/
  spec_template.py          空白 spec 模板（含 REVIEW / LESSON 骨架）
```

## spec 结构速览

```python
PAGES = [dict(p=1, section="标题 · 摘要 · 引言",
              head=["本文发表在 <期刊>", "<卷期 页码>"],
              redtitle=["<中文标题>", "—— <副题>"],
              boxes=[("L", 150, "blue", "【一句话贡献】", "正文…", "<anchor>"),
                     ("R", 150, "red",  "【核心判断】",   "正文…", None)],
              gloss=[("<anchor>", "四字术语", "R", 0)],
              marks=[("<支撑论点的句子>", 0)])]

REVIEW = dict(kicker=..., title=..., blocks=[整宽框 / 半宽并排 / 表格 / 纯文字行], closer=...)
LESSON = dict(...)
```

`boxes` 元素：`(边, 建议高度, 配色, 标题, 正文, 锚点短语?)`。字段细节与文案要求见 `references/spec-format.md`，可直接复制 `assets/spec_template.py` 开始填。

## 换期刊怎么办

改 `scripts/engine.py` 里的 `GEO`，一般只需一处：`col_frac`（正文左右边界占页宽的比例，默认 0.063 / 0.941）。单栏 preprint 正文几乎占满整宽时，左右只剩约 30pt，红字改放页外侧并压到 4 字以内。渲染逻辑不用动。

## 环境

- Python 3.10+，PyMuPDF ≥ 1.24（本次在 2.1 / MuPDF 1.28.6 上验证）；
- 中文需要宋体与雅黑/黑体：Windows 走 `C:\Windows\Fonts`（`msyh.ttc / msyhbd.ttc / simsun.ttc / simhei.ttf`），Linux 装 Noto CJK 或文泉驿；`engine.load_fonts()` 会明确报缺哪个角色。

## 已知的坑（详见 `references/layout.md`）

- `TextWriter.color` 是**全局属性**：单个 writer 会让整页批注渲成同一颜色（通常是最后设置的页脚灰）。引擎按颜色分桶持有多个 writer，别退回单 writer。
- `draw_rect(radius=0.0)` 抛 `bad radius value`：圆角给 0.1–0.2，或传 `None`。
- 中文断行必须把收尾标点留在上一行，否则出现孤行"。"；三层兜底：断行合并 → 宽度上限放宽一个字 → 末行纯标点强制并入上一行。
- 锚点会因跨行、连字符断词、整段文本层缺失而全部落空——所以流程把 `probe.py` 前置。
- `show_pdf_page` 逐页复制资源，体积会涨 3–5 倍，保存必须 `garbage=4, deflate=True, deflate_images=True, deflate_fonts=True`。

## 适用边界

适用：PDF 论文的单篇深度精读、组会/开题前的材料准备、把方法论文读到"能不能复现"的程度。

不适用：只做翻译、只写 Markdown 笔记、文献综述、题录核验、同行评审结论。

## License

MIT，见 [LICENSE](LICENSE)。
