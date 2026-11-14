# spec.py 结构

`spec.py` 是一篇论文的批注内容表，`build.py --spec spec.py` 直接执行它。一个 spec 由四部分组成：

```python
FOOTER = "论文精读批注"          # 可选，页脚左侧前缀

PAGES = [                       # 必填，一页原文一条
    dict(p=1, section="标题 · 摘要 · 引言",
         head=["本文发表在 Elsevier 期刊", "Expert Systems With Applications (2026, 322: 132407)"],
         redtitle=["面向高空光伏电站无人机巡检的", "选址—路径多目标优化", "—— 协同式 MOEA/D 方法"],
         boxes=[...], gloss=[...], marks=[...]),
]

REVIEW = dict(...)              # 可选，附页：精读总评
LESSON = dict(...)              # 可选，附页：课题启示
```

## PAGES 字段

| 字段 | 说明 |
|---|---|
| `p` | 原 PDF 页码，从 1 开始 |
| `section` | 页脚右侧文字，如 `§4.2 冲突边 · 着色可行性 · α 配比` |
| `head` | 第 1 页左上角灰色导语（期刊、卷期、DOI 之类），每项一行 |
| `redtitle` | 第 1 页中文译名，红色宋体 9.8pt，每项一行，末行带红色下划线 |
| `boxes` | 批注框，见下 |
| `gloss` | 红字译注 `(anchor_phrase, 中文短词, "L"/"R", occurrence)` |
| `marks` | 只加红色下划线、不配文字 `(anchor_phrase, occurrence)` |

### boxes 元素

```
("L", 100, "blue", "【四重耦合】", "正文……", "anchor phrase", 0)
 ^    ^     ^        ^              ^           ^                ^
边   建议  配色     框标题         正文         锚点短语（可省略）  第几个命中（默认 0）
```

- 边：`"L"` 左栏、`"R"` 右栏。左栏 x=6，右栏 x=780，宽 226。
- 配色：`blue` 结构/机制/方法，`red` 批判/硬伤/风险，`green` 肯定/可复用，`amber` 阅读路线/建议/存疑。
- `y` 是**建议起点**，实际会按同栏顺序、不少于建议值的方式堆叠；给"你想让它出现在哪个高度"即可（通常对齐它所注释的那段正文）。
- 锚点短语只有一条规则：**`search_for` 能命中**（见下）。

### gloss / marks 的锚点

锚点必须是原文里**同一行内**、能被 `page.search_for()` 命中的短语：

- 跨行短语、被连字符拆开的词（`multi-\nobjective`）、带公式或特殊符号的短语通常命不中；
- 少数页面存在文本层缺失（段落是矢量绘制），整段都搜不到 —— 换同段内另一句；
- 一个短语命中多次时用 occurrence 选第几个（按 y 再按 x 排序）。

先跑 probe：

```bash
python scripts/probe.py --src paper.pdf --page 5 "average degree" "NP-hardness" "graph coloring"
```

输出 `OK n  x= y=` 的才能用；`MISS` 就换个更短的候选。

## 附页 REVIEW / LESSON

```python
REVIEW = dict(
    kicker="附页一 · 精读总评",
    title="精读总评：这篇论文的真实分量",
    sub="作者、期刊、DOI、机构一行",
    blocks=[...],            # 见下
    closer="一句话收尾",
)
```

`blocks` 是一个有序列表，每个元素是三选一：

1. 整宽框：`dict(kind="blue", title="【…】", body="…", bsize=8.8)`
2. 半宽并排：`[dict(kind="green", …), dict(kind="red", …)]`（1–2 个，宽 468，间距 12）
3. 表格：`dict(kind="table", caption="【…】 说明", rows=[["表头1","表头2"],…], ratios=[0.3,0.3,0.4])`
4. 纯文字行：`dict(kind="text", body="…")`

正文里用 `\n` 硬换行，适合 ①②③ 分点；不要用 markdown 的 `*`、`-`。

## 内容要求（写文案时的判断口径）

- 每个框只讲一件事，标题用【】两到四个字概括，正文 40–120 字。
- 左栏优先放**结构与机制**（它在做什么、为什么这么做），右栏优先放**判断**（是否可信、值不值得学）。
- 至少每页有一条"具体到页码/表号/公式号的批判"或"具体数字复核"，否则这一页的批注没有信息增量。
- 区分作者主张与证据：写"作者称…但 Table 6 只有…"，不要写"它证明了…"。
- 不确定就写"文中未见"，不要替作者补全。
