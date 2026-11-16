---
name: course-handout
description: Create polished, source-grounded course handouts from notes, documents, or structured outlines, using Markdown as the portable source and exporting to Markdown, DOCX, and PDF when requested.
---

# Course Handout

Use this skill when the user wants a learner-facing course handout, lesson guide, workshop booklet, or reusable lesson document. It is designed for Chinese or bilingual technical teaching material and can also handle other subjects when the same instructional structure is useful.

## Core workflow

1. Inspect the supplied outline, source files, references, and any retained handout examples. Separate facts that are supported by sources from explanations, exercises, and teaching suggestions. Do not invent product specifications, citations, or outcomes.
2. Draft one canonical Markdown source first. Keep it readable and portable: ordinary headings, paragraphs, lists, Markdown tables, images with relative paths, and `<!-- pagebreak -->` only where a deliberate page transition helps the printed version. Use YAML frontmatter only for document metadata.
3. Organize the lesson around the learner's path. A useful default is: title and audience, learning objectives, motivating scenario, core concepts, worked examples, guided practice, recap and self-test, next lesson, and sources. Adapt the number and order of sections to the subject.
4. Read [lesson-structure.md](references/lesson-structure.md) for the instructional contract and [style-contract.md](references/style-contract.md) for the visual language before producing a substantial handout.
5. Produce the formats the user requested. Markdown is the source of truth, the DOCX is the layout source, and the PDF is exported from that DOCX, so both files share one pagination and one set of fonts. Render the exported PDF to page images and inspect them before delivery. If only Markdown is requested, still run the structural checks below.
6. Run `scripts/validate_handout.py` on the Markdown source and on any generated DOCX/PDF. Resolve structural failures and review warnings. Keep intermediate render images in a temporary or work directory, not beside the final deliverables unless requested.

## Portable conversion helper

For a quick local conversion from a canonical Markdown source, run:

```text
python scripts/build_handout.py lesson.md --out-dir output/lesson --formats md,docx,pdf
```

The script uses the workspace Python runtime and common `python-docx`/ReportLab packages when available. It supports frontmatter, headings, paragraphs, lists, tables with a title line, blockquotes, local images with a caption, and page breaks.

`md` and `docx` are always produced by the builder. `pdf` is produced by exporting that DOCX with an Office converter — the bundled LibreOffice Kit when it can be found, otherwise any `soffice`/`libreoffice` on `PATH`. Export from the DOCX is the default because a second, independent renderer produces a second typography: headings lose their bold weight, line breaking and CJK spacing drift, and the two deliverables no longer look like one document. When no converter exists the builder falls back to its portable ReportLab renderer and prints a warning; set `HANDOUT_PDF_FROM=markdown` to choose that renderer deliberately, or `HANDOUT_PDF_VIA_SOFFICE=1` to keep the old export switch.

Wrap any block that should stay in the Markdown but must not appear in the DOCX or PDF with `<!-- md-only -->` … `<!-- /md-only -->`, for example a source list kept for provenance in a standalone handout. The Markdown source and the emitted `.md` copy keep the block; DOCX and PDF omit it.

Point the builder at a specific converter with `HANDOUT_LO_NODE` + `HANDOUT_LO_CLI` (LibreOffice Kit CLI) or `HANDOUT_SOFFICE` (a `soffice` binary).

Typography is fixed, not per-document, except the two typefaces, which frontmatter `heading_font` / `body_font` (or `HANDOUT_HEADING_FONT` / `HANDOUT_BODY_FONT`) can set without touching sizes, weights or spacing. The default follows the Chinese academic convention — 黑体 for titles, headings and table headers, 宋体 for body text — with Noto Serif CJK SC and Noto Sans CJK SC available when a document names them explicitly: black text, exact line spacing, 11.5 pt body, 17 pt / 13 pt / 13 pt headings, 24 pt title, with a 0.85 in side margin and a header/footer carrying the course, chapter and page number. Sizes, spacing, colours and table styling are listed in [style-contract.md](references/style-contract.md); the builder applies them in DOCX and PDF so the Markdown stays free of formatting. Do not override them with per-document HTML or raw Word styling.

The skill bundles the two OFL-licensed CJK families in `assets/` (regular serif, regular and bold sans) and embeds subsets of them in the DOCX, so the handout stays readable on machines without those fonts. Set `HANDOUT_EMBED_CJK_FONT=0` only when a controlled environment supplies the fonts.

An Office converter resolves fonts from the operating system, not from the DOCX subset. Run the bundled installer once per machine before exporting:

```text
python scripts/install_fonts.py --check     # report, change nothing
python scripts/install_fonts.py             # copy into ~/Library/Fonts (macOS) or ~/.local/share/fonts
```

It copies the three bundled files into the user font directory only, honours `HANDOUT_FONT_DIR`, and undoes itself with `--remove`. If the export prints “the converter substituted these fonts”, the PDF will not match the DOCX: install the fonts and rebuild rather than accepting the substituted faces. For a heavily art-directed document, use the same Markdown as the source, refine the DOCX, and re-export the PDF; do not make the binary file the only editable source.

## Quality gate

- Objectives are observable and match the exercises.
- Definitions include the conditions that make them true; units, precision, scope, and measurement method stay attached to quantitative claims.
- Examples show reasoning and assumptions, not just answers.
- Exercises leave room for a learner response; answer keys are separated or clearly labeled when included.
- Tables compare like with like and do not hide missing conditions.
- Headings form a coherent outline when read alone.
- Markdown links and image paths resolve locally; generated DOCX/PDF have no clipped text, missing glyphs, broken tables, or empty pages.
- The DOCX and the PDF are one layout: the PDF is the export of the DOCX, the export reported no substituted fonts, and the two files paginate the same. Do not hand-edit the PDF to fix something the DOCX can fix.
- Sources are human-readable and traceable; no tool tokens or placeholder text remain.
- Do not put numeric citation markers such as `[1]`, `[2,3]`, `[4-6]`, or `[^1]` in the text, and do not number the entries in the sources list with them. List sources as plain bullet items in the sources section, without in-text markers. `build_handout.py` also removes any such markers from all outputs, and `validate_handout.py` fails if they remain.
- Chinese lesson titles use `第2讲` style. When the lesson belongs to chapter `n`, use chapter-prefixed headings such as `n.1、算力是什么` and `n.1.1、数据、算法与算力各做什么`; keep the same hierarchy through the recap, answers, and sources sections.
- Instructional labels use `【例题】` and `【随堂思考】`; diagrams use descriptive captions without Chinese numeral labels, and course positioning appears at the start of the lesson.
- Font family, font size, colour, line spacing and table styling follow [style-contract.md](references/style-contract.md) and are applied by `build_handout.py`. Second- and third-level headings are both 13 pt.
- Every table carries a title line directly above it starting with `表` and a number (`表2-1、常见数值格式的占用与用途`); the builder renders it centred above the table. Every figure carries its caption in the image alt text, rendered below the figure. Figures and tables keep 12 pt of clear space above and below. `validate_handout.py` fails a table without a title line.

## Learner-facing register

Write for the reader who has the handout and nothing else — often a vocational-college or zero-background learner. These rules come from review cycles on the 算力运维 handouts and should be applied by default, not only when asked:

- One idea per sentence. Split long sentences; keep the average near 30 characters and avoid sentences over 45. Prefer a full stop to a semicolon chain.
- No bookish anaphora. Replace 前者/后者/该/其/并非/则 with the noun itself or a short clause.
- Explain a term the first time it appears, in plain words, optionally with a familiar analogy (内存像摊开的桌面、硬盘像存资料的柜子). Keep English terms when the Chinese would lose precision, but gloss them.
- Turn conditions into actions: “不能假设任意 BMC 默认具备全部功能” → “不能假设所有 BMC 默认都有”.
- Write transitions out in full: “带外管理想要正常使用，至少需要满足下面四个条件”, not “带外管理有用，但有前提，至少有四条”.
- Address the learner directly: “学习完本讲后，试着用自己的话回答……”, not the teacher’s instruction “先遮住正文”.
- A handout is self-contained. Do not cite sources the reader does not have (“某某手册第 7 节写明……”); state the fact and keep the citation in the `md-only` reference block. Teacher-side notes (how a diagram was drawn, which manual figure it comes from) also stay out of the body.
- Keep the prose concise and proportionate: cover routine physical or clerical checks briefly with a compact checklist table instead of dramatic storytelling or padded analogies, and reserve the main depth for core mechanisms, failure modes, and verification commands.
- Avoid AI-isms and defensive filler: replace artificial jargon or bureaucratic phrasing (such as 门禁, 消缺, 临门一脚, 打回整改, 翻车场景, 幽灵资产, 算力积木, 拧成一股绳) with plain engineering words; cut fake FAQ leads ("很多新手会问……"), rhyming summary jingles, and preachy table endings ("彻底消灭……", "守住……准则"). State the concrete technical consequence instead.
- When the body lists parts that carry numbers in a figure or table, put the numbers in parentheses: “PCIe 插槽（1～4）”“两个电源模块（5、6）”.

## Format-specific notes

- **Markdown:** preserve the canonical source and relative asset paths. Use plain Markdown that renders in common editors; avoid vendor-specific extensions unless the user asks for them.
- **DOCX:** the builder supplies `Title`, heading styles, body text, header/footer with page numbers, and the shared table style; follow the document skill's render-and-inspect requirement. A level-1 heading that repeats the frontmatter `title` is dropped so the lesson title prints once.
- **PDF:** the export of that DOCX, so it is a fixed-layout copy of the Word layout rather than an independent render. Check the converter reported no substituted fonts, then render every page to PNG, inspect at full size, and fix pagination, table or font problems in the DOCX and re-export — editing the PDF by hand breaks the shared layout.

Do not invoke this skill for a paper-reading seminar page, a slide deck, or a generic Word edit unless the user is specifically asking for a course handout.
