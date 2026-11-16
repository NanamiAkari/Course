# Handout style contract

The default visual language is a calm technical handout: generous margins, black body text on white, one serif for reading text and one sans for titles and headings. Use emphasis to support learning, not decoration.

All values below mirror the reference handout (`第二讲：认识算力/讲义样稿/第二讲_认识算力_学员讲义.docx`). `scripts/build_handout.py` applies them in DOCX and PDF, so the source Markdown carries no formatting.

## Typography

| Element | Font | Size | Line spacing (exact) | Space before / after | Colour |
| --- | --- | --- | --- | --- | --- |
| Title (`title` metadata) | Noto Sans CJK SC Bold | 24 pt | 31.2 pt | 0 / 6 pt | `#000000` |
| Subtitle (`subtitle`, `audience`, `duration`) | Noto Sans CJK SC | 11 pt | 14.3 pt | 0 / 6 pt | `#000000` |
| Heading 1 (`#`) | Noto Sans CJK SC Bold | 20 pt | 26.0 pt | 10 / 6 pt | `#000000` |
| Heading 2 (`##`) | Noto Sans CJK SC Bold | 18 pt | 23.4 pt | 14 / 8 pt | `#000000` |
| Heading 3 (`###`) | Noto Sans CJK SC Bold | 13 pt | 16.9 pt | 10 / 6 pt | `#000000` |
| Body text | Noto Serif CJK SC | 11.5 pt | 18.5 pt | 0 / 6 pt | `#000000` |
| List item | Noto Serif CJK SC | 11.5 pt | 18.5 pt | 0 / 6 pt | `#000000` |
| Table title (above the table) | Noto Sans CJK SC Bold | 10.5 pt | 15.5 pt | 12 / 4 pt, centred | `#000000` |
| Figure caption (below the figure) | Noto Serif CJK SC | 9.5 pt | 12.35 pt | 3 / 12 pt, centred | `#000000` |
| Table header | Noto Sans CJK SC Bold | 10.5 pt | 15.5 pt | 0 / 0 | `#000000` |
| Table body | Noto Serif CJK SC | 10.5 pt | 15.5 pt | 0 / 0 | `#000000` |
| Header / footer | Noto Sans CJK SC | 8.5 pt | 11 pt | 0 / 0 | `#000000` |

### Line spacing

Line spacing is an exact leading in points, never a multiple of the font size, and it is set per element as listed above: 18.5 pt for 11.5 pt body text, 26 pt for the 20 pt level-1 heading, 23.4 pt for the 18 pt level-2 heading, 16.9 pt for the 13 pt level-3 heading, 15.5 pt for 10.5 pt table text, 12.35 pt for 9.5 pt captions. Every element keeps its own leading so mixed-size lines never reflow each other. Paragraphs are separated by 6 pt; a figure or a table gets 12 pt of air on each side, well above a paragraph gap, so figures and tables never sit tight against the text.

The heading hierarchy is a size step plus a gap step: level 2 is 18 pt with 14 pt before / 8 pt after, level 3 is 13 pt with 10 pt before / 6 pt after, and level 1 stays at 20 pt so it never ranks below level 2. Hierarchy also reads from the numbering (`n.1、`, `n.1.1、`); a lesson that carries its title in the `title` metadata normally uses no level-1 heading at all.

The two families are configurable per document through frontmatter, and only the typeface changes: sizes, weights and spacing stay as listed above.

```yaml
heading_font: 黑体    # titles, headings, table headers, header/footer  (default)
body_font: 宋体       # body text, list items, table cells, captions      (default)
```

The defaults follow the convention used by Chinese university thesis templates — 标题黑体、正文宋体, with sizes such as 三号/四号 headings over 小四 body — so a handout written in Chinese looks like the reader's other course material. Those two families are the reader's system fonts: the DOCX is not font-embedded, and the PDF export relies on the platform mapping 黑体/宋体 onto its own Heiti/Songti faces. Office converters report such mappings as substitutions; the builder treats them as expected on macOS and warns elsewhere, because outside macOS a missing family really does change the shape of the text.

Set `heading_font: Noto Sans CJK SC` and `body_font: Noto Serif CJK SC` to use the bundled families instead: the builder then embeds subsets into the DOCX so a machine without Noto CJK still renders as designed, and `scripts/install_fonts.py` makes them available to the PDF exporter. The PDF is the export of the DOCX and therefore repeats the same typography.

## Page architecture

- Letter paper (8.5 × 11 in) with 0.85 in left and right margins, 0.65 in top and bottom margins; header at 0.25 in and footer at 0.28 in from the paper edge.
- Header, left aligned: `课程名  /  章名` (`course` metadata, default `算力运维工程师`; `chapter` metadata).
- Footer, right aligned: the lesson title, then `·`, then the page number.
- Give the first page a clear title, subtitle, audience or duration, a short orientation paragraph, and learning objectives.
- Use Arabic chapter-prefixed section headings for the main route through the lesson (`2.1、`, `2.2、`, `2.3、` for a second lesson). Use the full parent path for subsections (`2.1.1、`, `2.1.2、`).
- Put tables near the text that explains how to read them. Every table carries a title line above it and every figure carries a caption below it.
- Use page breaks at meaningful transitions: after the opening orientation, before a major section, or before a recap/self-test. Do not force a page break after every heading.

## Tables

One style for every table, applied by the builder in both DOCX and PDF.

- Light blue-grey header row (`#E9EFF3`) with bold sans text; white body rows with serif text; a thin light-grey grid (`#D9D9D9`) on every cell.
- Cells are vertically centred with 4.25 pt top and bottom padding and 5.25 pt left and right padding. Rows never split across pages and the header row repeats.
- The table spans the full text width. Column widths follow content length, with slack so short identifiers do not wrap.
- A first column of short identifiers (such as `FP64`, `INT8`) is centred, including its header; all other columns are left aligned.
- Do not hand-style tables in the source.
- **Never put a raw `|` inside a cell.** Markdown splits on it and the builder splits on it too, so `lspci | grep K0` silently shifts the rest of the row into the wrong columns. Write the command differently (`` `lspci 后用 grep K0 过滤` ``) instead of trying to escape it. `validate_handout.py` reports a column-count mismatch as an error.

## 中文标点

- 正文用中文标点：逗号、句号、顿号、冒号用全角，引号用 “ ”。不要用 ASCII 双引号 `"`——在中文段落里它会被渲染成两个右引号，一页能出现十几次。
- 括号里是英文术语或缩写时，可以保留半角括号与原文，例如 `OCP（Open Compute Project）`。
- 命令、参数、路径一律用反引号包起来并保留半角；反引号里的 ASCII 引号不参与上面的引号检查。

## Table titles and figure captions

- Every table has a title line directly above it, on its own line, starting with `表` and its number: `表2-1、常见数值格式的占用与用途`. Use the lesson number as the first part of the number (`表2-1` in 第2讲), keep the title short and noun-phrased, and do not put a full stop at the end.
- The builder renders that line as the table title — bold sans, 10.5 pt, centred above the table, 12 pt below the paragraph before it and 4 pt above the table. Do not write it as a heading or wrap it in `**`.
- Every figure goes on its own line as a Markdown image; the alt text is the figure caption, rendered below the image in 9.5 pt serif, centred. Describe what the reader should see instead of numbering it `图一`.
- 图注与表题不写来源括注。不要写「（H3C iFIST 配置指导图3-19）」「（海光培训材料原图）」这类尾巴；出处统一进文末「来源」节。图注的任务是把画面里的编号、位置、状态说清楚，不是给文献做注释。`validate_handout.py` 会对这类括注告警。
- Figures and tables keep 12 pt of clear space above and below, so a table or figure never crowds the surrounding paragraphs.
- 图默认按版心宽（6.8 in）插入。竖图、竖表或细节局部图这样会接近一页高，在图片路径后写 `{width=55%}` 指定印刷宽度，高度按原图比例缩放，例如 `![前面板指示灯](assets/front.png){width=45%}`。百分比只影响宽度，不改题注与留白。
- `<!-- md-only -->` 与 `<!-- /md-only -->` 之间的内容只在 Markdown 源里保留（来源清单、检索记录、写作备注），构建时整段丢弃，不进 DOCX/PDF。

## Components that help learners

- `【例题】` for a worked example with assumptions, calculation, and conclusion.
- `【随堂思考】` or `【练习】` for an unanswered prompt with writing space in DOCX/PDF.
- `【关键区别】` for a common confusion that the learner should be able to resolve.
- Instructional labels in corner brackets (`【例题】`, `【随堂思考】`, `【练习】`, `【关键区别】`, `【课后自测】`) are bold at the inherited body size and colour — no size change, no colour change, no background. Put the label at the start of its paragraph, list item, or quote; the builder bolds it in DOCX and PDF automatically, so the source does not need `**`.
- A compact recap table mapping each objective to the judgment or action it enables.

## Restraints

- Avoid dense card grids, marketing-style hero blocks, decorative gradients, oversized labels, and ornamental borders.
- Avoid relying on color alone. Tables, callouts, and captions must remain understandable in grayscale.
- Do not colour body text or headings; the only accent colour is `#23485E`, reserved for links and reference lines. Emphasise with bold, not with colour or size.
- Keep diagrams simple and labeled. Use descriptive captions instead of `图一`/`图二`/`图三`, and refer to them by their content. Use a redraw only when it clarifies a relationship; cite the source or mark it as a teaching diagram.
- Never let a polished layout conceal unsupported claims, missing conditions, or an unresolved source.
- 讲义不写关于自己的话：不声明出处（放来源节或表注，图注不写），不声明"本讲不讲什么"，不做免责（"为避免误解""需要说明的是"）。版面再干净，也盖不住这类噪音。
