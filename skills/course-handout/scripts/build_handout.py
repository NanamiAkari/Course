#!/usr/bin/env python3
"""Build Markdown, DOCX, and PDF handouts from one portable Markdown source.

This intentionally supports a small, predictable Markdown subset rather than
trying to be a full Markdown implementation. Richer source can remain in the
canonical .md file and be refined with the format-specific document skills.

Typography is fixed by the skill's style contract and mirrors the reference
handout (讲义样稿/第二讲_认识算力_学员讲义.docx): Noto Serif CJK SC for body
text, Noto Sans CJK SC for titles and headings, black text, exact line spacing.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ASSETS = Path(__file__).resolve().parents[1] / "assets"

# --- Typography --------------------------------------------------------------
# Sizes are points; line spacing is an exact leading in points. Values come
# from the reference handout's styles.xml, except that heading 3 is set to
# 13 pt so second- and third-level headings share one size.
SERIF = "Noto Serif CJK SC"  # 正文、表格内容、图注、小字
SANS = "Noto Sans CJK SC"  # 标题、表格表头、页眉页脚
# Defaults follow the Chinese academic convention: 标题黑体、正文宋体. The bundled
# Noto families stay available when a document names them explicitly, and are the
# fallback for the embedded-font path.
DEFAULT_BODY_FONT = "宋体"
DEFAULT_HEADING_FONT = "黑体"
TEXT_COLOR = "000000"
LINK_COLOR = "23485E"

PAGE_W, PAGE_H = 8.5, 11.0  # Letter, inches
MARGIN_LR, MARGIN_TB = 0.85, 0.65
HEADER_DIST, FOOTER_DIST = 0.25, 0.28

BODY_SIZE, BODY_LINE, BODY_AFTER = 11.5, 18.5, 6.0
TITLE_SIZE, TITLE_LINE = 24.0, 31.2
TITLE_SPACING = 0.25  # letter spacing, points
SUBTITLE_SIZE, SUBTITLE_LINE = 11.0, 14.3
SUBTITLE_SPACING = 0.75
H1_SIZE, H1_LINE = 17.0, 22.1
H2_SIZE, H2_LINE = 13.0, 16.9
H3_SIZE, H3_LINE = 13.0, 16.9
HEADING_BEFORE, HEADING_AFTER = 10.0, 6.0
CAPTION_SIZE, CAPTION_LINE = 9.5, 12.35
SMALL_SIZE, SMALL_LINE = 9.5, 14.0
TABLE_SIZE, TABLE_LINE = 10.5, 15.5
META_SIZE = 8.5  # header and footer
QUOTE_INDENT = 0.25  # inches

# Code blocks: one size below body text, tight leading, a light panel behind the
# lines. The panel and the left rule are the only decoration a code block gets.
CODE_SIZE, CODE_LINE = 9.5, 12.5
CODE_FILL = "F4F6F8"
CODE_RULE = "C9D3D9"
CODE_INDENT = 0.22  # inches
CODE_FONT = "Noto Sans Mono CJK SC"

TABLE_HEADER_FILL = "E9EFF3"
TABLE_BORDER = "D9D9D9"
TABLE_PAD_V, TABLE_PAD_H = 4.25, 5.25  # points

# Spacing around figures and tables. Body paragraphs are separated by 6 pt, so a
# figure or table gets noticeably more air than a paragraph boundary.
IMAGE_BEFORE, FIGURE_NOTE_BEFORE, CAPTION_AFTER = 12.0, 3.0, 12.0
TABLE_TITLE_SIZE, TABLE_TITLE_LINE = 10.5, 15.5
TABLE_TITLE_BEFORE, TABLE_TITLE_AFTER = 12.0, 4.0
TABLE_BEFORE, TABLE_AFTER = 12.0, 12.0

DEFAULT_COURSE = "算力运维工程师"


@dataclass
class Block:
    kind: str
    text: str = ""
    level: int = 0
    items: list[str] = field(default_factory=list)
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    path: str = ""
    alt: str = ""
    brk: bool = False
    lines: list[str] = field(default_factory=list)


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    if not lines or lines[0].strip() != "---":
        return {}, lines
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, lines
    meta: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"\'')
    return meta, lines[end + 1 :]


# Numeric citation markers such as [1], [2,3], [4-6], [1][2], [^1], ［1］.
# Handouts list sources in a plain sources section instead of in-text markers.
_CITE = r"(?:(?:\[\^?|［)\d+(?:\s*[,，、\-–~]\s*\d+)*(?:\]|］))+(?!\()"
_CITE_AT_START = re.compile(r"^([ \t]*(?:[-*+>]|\d+[.)])?[ \t]*)" + _CITE + r"[ \t]*:?[ \t]*")
_CITE_INLINE = re.compile(r"[ \t]*" + _CITE)


def strip_citations(line: str) -> str:
    """Remove numeric citation markers, leaving inline code spans untouched."""
    line = _CITE_AT_START.sub(r"\1", line, count=1)
    parts = re.split(r"(`[^`]*`)", line)
    return "".join(p if p.startswith("`") else _CITE_INLINE.sub("", p) for p in parts)


def strip_citations_document(lines: list[str]) -> list[str]:
    """Strip citations line by line, skipping fenced code blocks.

    A code block is literal text: `sys.argv[1]` or `{.items[0].name}` is a
    subscript, not a citation marker, so the fence must protect it.
    """
    out: list[str] = []
    in_code = False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        out.append(line if in_code else strip_citations(line))
    return out


def split_table_row(line: str) -> list[str]:
    line = line.strip().strip("|")
    return [cell.strip() for cell in line.split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    return len(cells) >= 2 and all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells)


def parse_markdown(source: Path) -> tuple[dict[str, str], list[Block]]:
    lines = source.read_text(encoding="utf-8").splitlines()
    meta, lines = parse_frontmatter(lines)
    lines = strip_citations_document(lines)
    blocks: list[Block] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            text = " ".join(x.strip() for x in paragraph).strip()
            if text:
                blocks.append(Block("paragraph", text=text))
            paragraph.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # Material kept in the Markdown for provenance but omitted from DOCX/PDF.
        if stripped == "<!-- md-only -->":
            flush()
            while i < len(lines) and lines[i].strip() != "<!-- /md-only -->":
                i += 1
            i += 1
            continue
        if not stripped:
            flush()
            i += 1
            continue
        if stripped.lower() in {"<!-- pagebreak -->", "\\pagebreak", "[pagebreak]"}:
            flush(); blocks.append(Block("pagebreak")); i += 1; continue
        if stripped.startswith("```"):
            flush()
            i += 1
            code: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i].rstrip())
                i += 1
            i += 1
            while code and not code[-1].strip():
                code.pop()
            blocks.append(Block("code", lines=code))
            continue
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
        if m:
            flush(); blocks.append(Block("heading", text=m.group(2), level=len(m.group(1)))); i += 1; continue
        if re.match(r"^[-*_]{3,}\s*$", stripped):
            flush(); blocks.append(Block("rule")); i += 1; continue
        image = re.match(r"^!\[([^]]*)\]\(([^)]+)\)\s*$", stripped)
        if image:
            flush(); blocks.append(Block("image", alt=image.group(1), path=image.group(2))); i += 1; continue
        if stripped.startswith(">"):
            flush(); blocks.append(Block("quote", text=re.sub(r"^>\s?", "", stripped))); i += 1; continue
        if re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)", stripped):
            flush(); items: list[str] = []
            while i < len(lines):
                current = lines[i].strip()
                mm = re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)(.+)$", current)
                if not mm: break
                items.append(mm.group(1).strip()); i += 1
            blocks.append(Block("list", items=items)); continue
        if i + 1 < len(lines) and "|" in line and is_table_separator(lines[i + 1]):
            flush(); headers = split_table_row(line); i += 2; rows: list[list[str]] = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(split_table_row(lines[i])); i += 1
            blocks.append(Block("table", headers=headers, rows=rows)); continue
        paragraph.append(line)
        i += 1
    flush()
    merged: list[Block] = []
    for index, block in enumerate(blocks):
        if (block.kind == "pagebreak" and index + 1 < len(blocks)
                and blocks[index + 1].kind == "heading"):
            blocks[index + 1].brk = True
            continue
        merged.append(block)
    attach_table_titles(merged)
    return meta, merged


# A table title sits on the line just before its table and starts with 表 + number,
# for example ``表2-1、常见数值格式的占用与用途``. It is rendered centred above the table.
TABLE_TITLE = re.compile(r"^表\s*[0-9一二三四五六七八九十]")


def attach_table_titles(blocks: list[Block]) -> None:
    for index, block in enumerate(blocks):
        if block.kind != "table" or index == 0:
            continue
        previous = blocks[index - 1]
        if previous.kind == "paragraph" and TABLE_TITLE.match(previous.text):
            previous.kind = "tabletitle"


def inline_text(value: str) -> str:
    value = re.sub(r"!\[([^]]*)\]\(([^)]+)\)", r"\1", value)
    value = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"\1", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    return re.sub(r"[*_]{1,3}", "", value)


def table_layout(headers: list[str], rows: list[list[str]]) -> tuple[list[float], bool]:
    """Return relative column widths and whether the first column is centred."""
    cols = max(1, len(headers))
    def width(s: str) -> int:
        return sum(2 if ord(ch) > 0x2E7F else 1 for ch in inline_text(s))
    longest = [max([width(headers[c]) if c < len(headers) else 0] + [width(r[c]) for r in rows if c < len(r)]) for c in range(cols)]
    # +4 leaves room for cell padding so short identifiers such as FP64 never wrap.
    weights = [min(max(n, 4) + 4, 60) for n in longest]
    total = sum(weights)
    first_short = cols > 1 and all(width(r[0]) <= 10 for r in rows if r)
    return [w / total for w in weights], first_short


# Instructional labels such as 【例题】 or 【随堂思考】 at the start of a paragraph,
# list item, or quote are always bold, whether or not the source wraps them in **.
_LABEL = re.compile(r"^(\s*)(?:\*\*)?(【[^】\n]{1,10}】)(?:\*\*)?")
_EMPHASIS = re.compile(r"(\*\*.*?\*\*|\*[^*\n]+\*|`[^`]+`)")


def bold_label_md(text: str) -> str:
    return _LABEL.sub(r"\1**\2**", text, count=1)


def markup_parts(text: str) -> list[tuple[str, bool]]:
    """Split text into (content, bold) parts, honouring ** and ` spans."""
    out: list[tuple[str, bool]] = []
    for part in _EMPHASIS.split(bold_label_md(text)):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            out.append((part[2:-2], True))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            # Single asterisks mark emphasis the handout renders as plain text.
            out.append((part[1:-1], False))
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            out.append((part[1:-1], False))
        else:
            out.append((part, False))
    return out


def pdf_markup(text: str) -> str:
    return "".join(f"<b>{html.escape(c)}</b>" if b else html.escape(c) for c, b in markup_parts(text))


# --- DOCX --------------------------------------------------------------------
def _insert_child(parent: Any, child: Any, order: tuple[str, ...]) -> None:
    """Insert child in schema order; order holds local names that follow it."""
    from docx.oxml.ns import qn
    for name in order:
        existing = parent.find(qn(name))
        if existing is not None:
            existing.addprevious(child)
            return
    parent.append(child)


def _rfonts(run: Any, name: str) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    rpr = run._r.get_or_add_rPr()
    element = rpr.find(qn("w:rFonts"))
    if element is None:
        element = OxmlElement("w:rFonts")
        rpr.insert(0, element)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        element.set(qn("w:" + attr), name)
    for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        if element.get(qn("w:" + attr)) is not None:
            del element.attrib[qn("w:" + attr)]


def style_run(run: Any, font: str, size: float, bold: bool | None = None, color: str = TEXT_COLOR,
              spacing: float | None = None) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor
    _rfonts(run, font)
    if bold is not None:
        run.font.bold = bold
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    if spacing:
        element = OxmlElement("w:spacing")
        element.set(qn("w:val"), str(int(round(spacing * 20))))
        _insert_child(run._r.get_or_add_rPr(), element,
                      ("w:w", "w:kern", "w:position", "w:sz", "w:szCs", "w:highlight", "w:u"))


def add_text_runs(paragraph: Any, text: str, font: str, size: float, color: str = TEXT_COLOR,
                  bold_all: bool = False) -> None:
    for content, bold in markup_parts(text):
        style_run(paragraph.add_run(content), font, size, True if (bold or bold_all) else None, color)


def format_paragraph(paragraph: Any, before: float = 0.0, after: float = BODY_AFTER,
                     line: float = BODY_LINE, align: Any = None, keep_next: bool = False,
                     keep_lines: bool = False) -> None:
    from docx.shared import Pt
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = Pt(line)
    if align is not None:
        paragraph.alignment = align
    if keep_next:
        pf.keep_with_next = True
    if keep_lines:
        # Keep a caption on one page: a figure on one page and its caption's
        # second line on the next reads as a missing figure.
        pf.keep_together = True


def _page_field(paragraph: Any, font: str) -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = " PAGE "
    separate = OxmlElement("w:fldChar"); separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    for element in (begin, instr, separate, end):
        run._r.append(element)
    _rfonts(run, font); run.font.size = Pt(META_SIZE); run.font.color.rgb = RGBColor.from_string(TEXT_COLOR)


def build_docx(source: Path, out: Path, meta: dict[str, str], blocks: list[Block]) -> None:
    try:
        from docx import Document
        from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import Inches, Pt, RGBColor
    except ImportError as exc:
        raise RuntimeError("DOCX output requires the bundled python-docx package") from exc

    doc = Document()
    body_font = (meta.get("body_font", "").strip()
                 or os.environ.get("HANDOUT_BODY_FONT", "").strip()
                 or DEFAULT_BODY_FONT)
    head_font = (meta.get("heading_font", "").strip()
                 or os.environ.get("HANDOUT_HEADING_FONT", "").strip()
                 or DEFAULT_HEADING_FONT)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(PAGE_W), Inches(PAGE_H)
    sec.left_margin = sec.right_margin = Inches(MARGIN_LR)
    sec.top_margin = sec.bottom_margin = Inches(MARGIN_TB)
    sec.header_distance, sec.footer_distance = Inches(HEADER_DIST), Inches(FOOTER_DIST)
    text_width = sec.page_width - sec.left_margin - sec.right_margin

    # Document defaults must name a CJK font; Word otherwise falls back silently.
    rpr_default = doc.styles.element.find(qn("w:docDefaults")).find(qn("w:rPrDefault")).find(qn("w:rPr"))
    rfonts = rpr_default.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts"); rpr_default.insert(0, rfonts)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        rfonts.set(qn("w:" + attr), body_font)

    styles = doc.styles

    def set_style(name: str, font: str, size: float, bold: bool | None = False,
                  before: float = 0.0, after: float = BODY_AFTER, line: float = BODY_LINE) -> None:
        try:
            style = styles[name]
        except KeyError:
            return
        style.font.name = font
        style.font.size = Pt(size)
        if bold is not None:
            style.font.bold = bold
        style.font.color.rgb = RGBColor.from_string(TEXT_COLOR)
        element = style.element.find(qn("w:rPr"))
        if element is not None:
            fonts = element.find(qn("w:rFonts"))
            if fonts is None:
                fonts = OxmlElement("w:rFonts"); element.insert(0, fonts)
            for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
                fonts.set(qn("w:" + attr), font)
        pf = style.paragraph_format
        pf.space_before = Pt(before)
        pf.space_after = Pt(after)
        pf.line_spacing = Pt(line)
        pf.keep_with_next = name.startswith("Heading")

    set_style("Normal", body_font, BODY_SIZE)
    set_style("Title", head_font, TITLE_SIZE, True, 0.0, BODY_AFTER, TITLE_LINE)
    set_style("Subtitle", head_font, SUBTITLE_SIZE, False, 0.0, BODY_AFTER, SUBTITLE_LINE)
    # The template's Title style draws a rule under the title; the handout has none.
    for name in ("Title", "Subtitle"):
        borders = styles[name].element.find(qn("w:pPr"))
        if borders is not None:
            for node in borders.findall(qn("w:pBdr")):
                borders.remove(node)
    set_style("Heading 1", head_font, H1_SIZE, True, HEADING_BEFORE, HEADING_AFTER, H1_LINE)
    set_style("Heading 2", head_font, H2_SIZE, True, HEADING_BEFORE, HEADING_AFTER, H2_LINE)
    set_style("Heading 3", head_font, H3_SIZE, True, HEADING_BEFORE, HEADING_AFTER, H3_LINE)
    set_style("Caption", body_font, CAPTION_SIZE, False, 0.0, BODY_AFTER, CAPTION_LINE)
    try:
        code_style = styles["Handout Code"]
    except KeyError:
        code_style = styles.add_style("Handout Code", 1)
    code_style.font.name = CODE_FONT
    code_style.font.size = Pt(CODE_SIZE)
    code_style.font.color.rgb = RGBColor.from_string(TEXT_COLOR)
    _crpr = code_style.element.find(qn("w:rPr"))
    if _crpr is None:
        _crpr = OxmlElement("w:rPr"); code_style.element.append(_crpr)
    _crf = _crpr.find(qn("w:rFonts"))
    if _crf is None:
        _crf = OxmlElement("w:rFonts"); _crpr.insert(0, _crf)
    for _attr in ("ascii", "hAnsi", "cs"):
        _crf.set(qn("w:" + _attr), CODE_FONT)
    _crf.set(qn("w:eastAsia"), body_font)
    _cpf = code_style.paragraph_format
    _cpf.space_before = Pt(0); _cpf.space_after = Pt(0)
    _cpf.line_spacing = Pt(CODE_LINE)
    _cpf.left_indent = Inches(CODE_INDENT)
    styles["Subtitle"].font.italic = False

    title = doc.add_paragraph(style="Title")
    format_paragraph(title, 0.0, BODY_AFTER, TITLE_LINE, WD_ALIGN_PARAGRAPH.LEFT)
    style_run(title.add_run(meta.get("title", source.stem)), head_font, TITLE_SIZE, True, TEXT_COLOR, TITLE_SPACING)
    subtitle_parts = [meta.get(k, "") for k in ("subtitle", "audience", "duration") if meta.get(k)]
    if subtitle_parts:
        p = doc.add_paragraph(style="Subtitle")
        format_paragraph(p, 0.0, BODY_AFTER, SUBTITLE_LINE, WD_ALIGN_PARAGRAPH.LEFT)
        style_run(p.add_run("    ".join(subtitle_parts)), head_font, SUBTITLE_SIZE, False, TEXT_COLOR, SUBTITLE_SPACING)

    heading = {1: (head_font, H1_SIZE, H1_LINE), 2: (head_font, H2_SIZE, H2_LINE), 3: (head_font, H3_SIZE, H3_LINE)}

    def spacer(before: float, after: float, line: float) -> None:
        p = doc.add_paragraph()
        format_paragraph(p, before, after, line)

    for index, b in enumerate(blocks):
        previous_kind = blocks[index - 1].kind if index else ""
        if b.kind == "heading" and b.level == 1 and b.text.strip() == meta.get("title", "").strip():
            # The running title already shows the lesson title; a repeated H1 would print it twice.
            continue
        if b.kind == "heading":
            level = min(max(b.level, 1), 3)
            font, size, line = heading[level]
            p = doc.add_paragraph(style=f"Heading {level}")
            format_paragraph(p, HEADING_BEFORE, HEADING_AFTER, line, keep_next=True)
            if b.brk:
                p.paragraph_format.page_break_before = True
            style_run(p.add_run(inline_text(b.text)), font, size, True, TEXT_COLOR)
        elif b.kind == "paragraph":
            p = doc.add_paragraph()
            format_paragraph(p)
            add_text_runs(p, b.text, body_font, BODY_SIZE)
        elif b.kind == "quote":
            p = doc.add_paragraph()
            format_paragraph(p)
            p.paragraph_format.left_indent = Inches(QUOTE_INDENT)
            add_text_runs(p, b.text, body_font, BODY_SIZE)
        elif b.kind == "rule":
            p = doc.add_paragraph()
            format_paragraph(p, 0.0, BODY_AFTER, BODY_LINE)
            style_run(p.add_run("─" * 30), body_font, SMALL_SIZE, None, TEXT_COLOR)
        elif b.kind == "pagebreak":
            doc.add_page_break()
        elif b.kind == "list":
            for item in b.items:
                p = doc.add_paragraph()
                format_paragraph(p, 0.0, BODY_AFTER, BODY_LINE)
                p.paragraph_format.left_indent = Inches(QUOTE_INDENT)
                p.paragraph_format.first_line_indent = Inches(-0.18)
                style_run(p.add_run("• "), body_font, BODY_SIZE, None, TEXT_COLOR)
                add_text_runs(p, item, body_font, BODY_SIZE)
        elif b.kind == "image":
            image_path = (source.parent / b.path).resolve()
            if image_path.exists():
                p = doc.add_paragraph()
                format_paragraph(p, IMAGE_BEFORE, 0.0, BODY_LINE, WD_ALIGN_PARAGRAPH.CENTER, keep_next=True)
                # Exact leading would clip an inline picture to one line, so this
                # paragraph keeps automatic spacing.
                p.paragraph_format.line_spacing = 1.0
                p.add_run().add_picture(str(image_path), width=text_width)
                if b.alt:
                    cap = doc.add_paragraph(style="Caption")
                    format_paragraph(cap, FIGURE_NOTE_BEFORE, CAPTION_AFTER, CAPTION_LINE,
                                     WD_ALIGN_PARAGRAPH.CENTER, keep_lines=True)
                    style_run(cap.add_run(b.alt), body_font, CAPTION_SIZE, None, TEXT_COLOR)
            else:
                p = doc.add_paragraph()
                format_paragraph(p)
                style_run(p.add_run(f"[图片缺失：{b.path}]"), body_font, BODY_SIZE, None, TEXT_COLOR)
        elif b.kind == "code":
            code_font = CODE_FONT
            for line_index, line in enumerate(b.lines):
                cp = doc.add_paragraph(style="Handout Code")
                cp.paragraph_format.space_before = Pt(6 if line_index == 0 else 0)
                cp.paragraph_format.space_after = Pt(6 if line_index == len(b.lines) - 1 else 0)
                cp.paragraph_format.left_indent = Inches(CODE_INDENT)
                cp.paragraph_format.line_spacing = Pt(CODE_LINE)
                _cpr = cp._p.get_or_add_pPr()
                _shd = OxmlElement("w:shd")
                _shd.set(qn("w:val"), "clear"); _shd.set(qn("w:color"), "auto")
                _shd.set(qn("w:fill"), CODE_FILL)
                _cpr.append(_shd)
                _bdr = OxmlElement("w:pBdr")
                _left = OxmlElement("w:left")
                _left.set(qn("w:val"), "single"); _left.set(qn("w:sz"), "12")
                _left.set(qn("w:space"), "4"); _left.set(qn("w:color"), CODE_RULE)
                _bdr.append(_left)
                _cpr.append(_bdr)
                _run = cp.add_run(line if line else " ")
                _rfonts(_run, code_font)
                _run.font.size = Pt(CODE_SIZE)
                _run.font.color.rgb = RGBColor.from_string(TEXT_COLOR)
        elif b.kind == "tabletitle":
            p = doc.add_paragraph()
            format_paragraph(p, TABLE_TITLE_BEFORE, TABLE_TITLE_AFTER, TABLE_TITLE_LINE,
                             WD_ALIGN_PARAGRAPH.CENTER, keep_next=True)
            add_text_runs(p, b.text, head_font, TABLE_TITLE_SIZE, TEXT_COLOR, bold_all=True)
        elif b.kind == "table":
            spacer(0.0 if previous_kind == "tabletitle" else TABLE_BEFORE, 0.0, 6.0)
            cols = max(1, len(b.headers))
            table = doc.add_table(rows=1, cols=cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.style = "Table Grid"
            table.autofit = False
            fractions, center_first = table_layout(b.headers, b.rows)
            tbl_pr = table._tbl.tblPr
            borders = OxmlElement("w:tblBorders")
            for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
                e = OxmlElement(f"w:{edge}")
                e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4")
                e.set(qn("w:space"), "0"); e.set(qn("w:color"), TABLE_BORDER)
                borders.append(e)
            margins = OxmlElement("w:tblCellMar")
            for edge, val in (("top", 85), ("left", 105), ("bottom", 85), ("right", 105)):
                e = OxmlElement(f"w:{edge}"); e.set(qn("w:w"), str(val)); e.set(qn("w:type"), "dxa"); margins.append(e)
            tbl_w = OxmlElement("w:tblW"); tbl_w.set(qn("w:w"), str(int(round(text_width / 635)))); tbl_w.set(qn("w:type"), "dxa")
            for tag in ("w:tblW", "w:tblBorders", "w:tblCellMar"):
                old = tbl_pr.find(qn(tag))
                if old is not None: tbl_pr.remove(old)
            # Keep CT_TblPr child order: tblStyle, tblW, jc, tblBorders, tblLayout, tblCellMar, tblLook.
            style_el = tbl_pr.find(qn("w:tblStyle"))
            (style_el.addnext(tbl_w) if style_el is not None else tbl_pr.insert(0, tbl_w))
            jc = tbl_pr.find(qn("w:jc"))
            (jc if jc is not None else tbl_w).addnext(borders)
            layout = tbl_pr.find(qn("w:tblLayout"))
            (layout if layout is not None else borders).addnext(margins)
            for c_idx, col in enumerate(table.columns):
                col.width = int(text_width * fractions[c_idx])
            for cell, text in zip(table.rows[0].cells, b.headers):
                cell.text = inline_text(text)
            for row in b.rows:
                cells = table.add_row().cells
                for idx, text in enumerate(row[:cols]):
                    cells[idx].text = inline_text(text)
            for r_idx, row in enumerate(table.rows):
                tr_pr = row._tr.get_or_add_trPr()
                tr_pr.append(OxmlElement("w:cantSplit"))
                if r_idx == 0:
                    tr_pr.append(OxmlElement("w:tblHeader"))
                for c_idx, cell in enumerate(row.cells):
                    cell.width = int(text_width * fractions[c_idx])
                    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                    if r_idx == 0:
                        shd = OxmlElement("w:shd")
                        shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), TABLE_HEADER_FILL)
                        cell._tc.get_or_add_tcPr().append(shd)
                    font = head_font if r_idx == 0 else body_font
                    for para in cell.paragraphs:
                        format_paragraph(para, 0.0, 0.0, TABLE_LINE)
                        if c_idx == 0 and center_first:
                            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        for run in para.runs:
                            style_run(run, font, TABLE_SIZE, r_idx == 0, TEXT_COLOR)
            spacer(0.0, TABLE_AFTER, 6.0)

    header = sec.header.paragraphs[0]
    header_parts = [meta.get("course", DEFAULT_COURSE), meta.get("chapter", "")]
    format_paragraph(header, 0.0, 0.0, META_SIZE * 1.3, WD_ALIGN_PARAGRAPH.LEFT)
    style_run(header.add_run("  /  ".join(p for p in header_parts if p) or "课程讲义"), head_font, META_SIZE, None, TEXT_COLOR)
    footer = sec.footer.paragraphs[0]
    format_paragraph(footer, 0.0, 0.0, META_SIZE * 1.3, WD_ALIGN_PARAGRAPH.RIGHT)
    style_run(footer.add_run(meta.get("title", source.stem) + "   ·   "), head_font, META_SIZE, None, TEXT_COLOR)
    _page_field(footer, head_font)

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)

    if os.environ.get("HANDOUT_EMBED_CJK_FONT", "1") != "0":
        embedder = Path(__file__).resolve().with_name("embed_docx_font.py")
        bundled = {
            SERIF: (("embedRegular", "NotoSerifCJKsc-Regular.otf"),),
            SANS: (("embedRegular", "NotoSansCJKsc-Regular.otf"),
                   ("embedBold", "NotoSansCJKsc-Bold.otf")),
        }
        fonts = []
        for family in dict.fromkeys((body_font, head_font)):
            for role, filename in bundled.get(family, ()):
                path = ASSETS / filename
                if path.exists():
                    fonts.append(f"{family}|{role}|{path}")
        if fonts:
            args = [sys.executable, str(embedder), str(out)]
            for item in fonts:
                args += ["--font", item]
            try:
                subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                print("warning: DOCX font embedding skipped (needs lxml and fonttools)", file=sys.stderr)


# --- PDF ---------------------------------------------------------------------
_FONT_CACHE = Path(tempfile.gettempdir()) / "course-handout-fonts"


def _otf_to_ttf(src: Path, dst: Path, text: str) -> None:
    """Convert a CFF (.otf) font to a subsetted TrueType font ReportLab can embed."""
    from fontTools import subset
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont, newTable

    font = TTFont(str(src))
    options = subset.Options()
    options.name_IDs = ["*"]; options.name_languages = ["*"]
    options.layout_features = ["*"]; options.notdef_outline = True
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)

    order = font.getGlyphOrder()
    glyphs = font.getGlyphSet()
    glyf: dict[str, Any] = {}
    for name in order:
        pen = TTGlyphPen(glyphs)
        glyphs[name].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        glyf[name] = pen.glyph()
    font["loca"] = newTable("loca")
    table = font["glyf"] = newTable("glyf")
    table.glyphOrder = order
    table.glyphs = glyf
    if "CFF " in font:
        del font["CFF "]
    if "VORG" in font:
        del font["VORG"]
    maxp = font["maxp"] = newTable("maxp")
    maxp.tableVersion = 0x00010000
    for attr in ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs",
                 "maxInstructionDefs", "maxStackElements", "maxSizeOfInstructions",
                 "maxComponentElements"):
        setattr(maxp, attr, 0)
    maxp.maxZones = 1
    maxp.numGlyphs = len(order)
    font["post"].formatType = 2.0
    font["post"].extraNames = []
    font["post"].mapping = {}
    font["head"].glyphDataFormat = 0
    font.sfntVersion = "\x00\x01\x00\x00"
    font.save(str(dst))


def _extract_mono_cjk() -> Path | None:
    """Extract the Simplified Chinese Mono face from the system Noto CJK collection.

    Code blocks mix Latin commands with Chinese comments, so the code face has to
    cover CJK as well. The collection is a TTC; ReportLab wants a single face.
    """
    candidates = [
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    ]
    for source in candidates:
        if not source.exists():
            continue
        _FONT_CACHE.mkdir(parents=True, exist_ok=True)
        target = _FONT_CACHE / f"{source.stem}-MonoSC.otf"
        if target.exists() and target.stat().st_size:
            return target
        try:
            from fontTools.ttLib import TTCollection
            collection = TTCollection(str(source), lazy=True)
            for face in collection.fonts:
                if face["name"].getDebugName(1) == "Noto Sans Mono CJK SC":
                    face.save(str(target))
                    return target
        except Exception as exc:
            print(f"warning: could not extract mono CJK face: {exc}", file=sys.stderr)
            return None
    return None


def prepare_pdf_font(path: Path, text: str) -> Path | None:
    """Return a ReportLab-compatible font file, converting and caching as needed."""
    if not path.exists():
        return None
    if path.suffix.lower() in {".ttf", ".ttc"}:
        return path
    digest = hashlib.sha1()
    stat = path.stat()
    digest.update(f"{path}:{stat.st_mtime_ns}:{stat.st_size}".encode("utf-8"))
    digest.update("".join(sorted(set(text))).encode("utf-8"))
    _FONT_CACHE.mkdir(parents=True, exist_ok=True)
    target = _FONT_CACHE / f"{path.stem}-{digest.hexdigest()[:16]}.ttf"
    if target.exists() and target.stat().st_size:
        return target
    chars = set(text) | set(chr(c) for c in range(32, 127)) | set("　，。、；：？！（）【】《》“”‘’…—·")
    try:
        _otf_to_ttf(path, target, "".join(sorted(chars)))
    except Exception as exc:
        print(f"warning: could not prepare PDF font {path.name}: {exc}", file=sys.stderr)
        return None
    return target


def build_pdf(source: Path, out: Path, meta: dict[str, str], blocks: list[Block]) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.fonts import addMapping
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)
    except ImportError as exc:
        raise RuntimeError("PDF output requires the bundled reportlab package") from exc

    # ReportLab's kinsoku sets omit the full-width Chinese comma, semicolon, colon,
    # question/exclamation marks and the closing quote, so a line can begin with
    # them. Extend both sets before any paragraph is laid out.
    try:
        from reportlab.platypus import paragraph as _rl_paragraph
        from reportlab.lib import textsplit as _rl_textsplit
        extra = "，；：！？…—”’》"
        _rl_paragraph.ALL_CANNOT_START = _rl_paragraph.ALL_CANNOT_START + extra
        _rl_textsplit.CANNOT_START_LINE[0] = _rl_textsplit.CANNOT_START_LINE[0] + extra
        _rl_textsplit.ALL_CANNOT_START = u"".join(_rl_textsplit.CANNOT_START_LINE)
    except Exception:
        pass

    # Include header/footer boilerplate so those glyphs survive font subsetting.
    text_sample = "".join([meta.get("title", source.stem), meta.get("subtitle", ""), meta.get("chapter", ""),
                           meta.get("course", DEFAULT_COURSE), DEFAULT_COURSE, "课程讲义", "  /  ", "0123456789 ·"])
    for b in blocks:
        text_sample += b.text + "".join(b.items) + "".join(b.headers) + "".join("".join(r) for r in b.rows) + b.alt
        text_sample += "".join(b.lines)

    serif = prepare_pdf_font(ASSETS / "NotoSerifCJKsc-Regular.otf", text_sample)
    sans = prepare_pdf_font(ASSETS / "NotoSansCJKsc-Regular.otf", text_sample)
    sans_bold = prepare_pdf_font(ASSETS / "NotoSansCJKsc-Bold.otf", text_sample)
    mono_source = _extract_mono_cjk()
    mono = prepare_pdf_font(mono_source, text_sample) if mono_source else None

    def register_file(name: str, path: Path | None) -> str | None:
        """Register an already-prepared font file (used for the mono face)."""
        if path is None or not Path(path).exists():
            return None
        try:
            pdfmetrics.registerFont(TTFont(name, str(path)))
            return name
        except Exception as exc:
            print(f"warning: PDF font {name} unavailable: {exc}", file=sys.stderr)
            return None

    def register(name: str, path: Path | None) -> str | None:
        if path is None:
            return None
        try:
            pdfmetrics.registerFont(TTFont(name, str(path)))
            return name
        except Exception as exc:
            print(f"warning: PDF font {name} unavailable: {exc}", file=sys.stderr)
            return None

    family_serif = register("HandoutSerif", serif) or "Times-Roman"
    family_sans = register("HandoutSans", sans) or "Helvetica"
    family_bold = register("HandoutSansBold", sans_bold) or family_sans
    family_mono = register_file("HandoutMono", mono) or family_sans
    if family_serif == "Times-Roman" and any(re.search(r"[\u3400-\u9fff]", text_sample) for _ in [0]):
        print("warning: no CJK PDF font found; PDF glyphs may be incomplete", file=sys.stderr)
    for family, bold_family in ((family_serif, family_bold), (family_sans, family_bold)):
        addMapping(family, 0, 0, family); addMapping(family, 1, 0, bold_family)
        addMapping(family, 0, 1, family); addMapping(family, 1, 1, bold_family)

    black = colors.HexColor("#" + TEXT_COLOR)
    styles = getSampleStyleSheet()
    body = ParagraphStyle("HandoutBody", parent=styles["BodyText"], fontName=family_serif,
                          fontSize=BODY_SIZE, leading=BODY_LINE, spaceBefore=0, spaceAfter=BODY_AFTER,
                          textColor=black, wordWrap="CJK")
    title_style = ParagraphStyle("HandoutTitle", parent=body, fontName=family_bold, fontSize=TITLE_SIZE,
                                 leading=TITLE_LINE, spaceAfter=BODY_AFTER)
    subtitle = ParagraphStyle("HandoutSubtitle", parent=body, fontName=family_sans, fontSize=SUBTITLE_SIZE,
                              leading=SUBTITLE_LINE, spaceAfter=BODY_AFTER)
    h1 = ParagraphStyle("HandoutH1", parent=body, fontName=family_bold, fontSize=H1_SIZE, leading=H1_LINE,
                        spaceBefore=HEADING_BEFORE, spaceAfter=HEADING_AFTER, keepWithNext=True)
    h2 = ParagraphStyle("HandoutH2", parent=body, fontName=family_bold, fontSize=H2_SIZE, leading=H2_LINE,
                        spaceBefore=HEADING_BEFORE, spaceAfter=HEADING_AFTER, keepWithNext=True)
    h3 = ParagraphStyle("HandoutH3", parent=body, fontName=family_bold, fontSize=H3_SIZE, leading=H3_LINE,
                        spaceBefore=HEADING_BEFORE, spaceAfter=HEADING_AFTER, keepWithNext=True)
    caption = ParagraphStyle("HandoutCaption", parent=body, fontSize=CAPTION_SIZE, leading=CAPTION_LINE,
                             alignment=TA_CENTER, spaceBefore=FIGURE_NOTE_BEFORE, spaceAfter=CAPTION_AFTER)
    table_title = ParagraphStyle("HandoutTableTitle", parent=body, fontName=family_sans, fontSize=TABLE_TITLE_SIZE,
                                leading=TABLE_TITLE_LINE, alignment=TA_CENTER, spaceBefore=TABLE_TITLE_BEFORE,
                                spaceAfter=TABLE_TITLE_AFTER, keepWithNext=True)
    meta_style = ParagraphStyle("HandoutMeta", parent=body, fontName=family_sans, fontSize=META_SIZE, leading=META_SIZE * 1.3)
    cell_body = ParagraphStyle("HandoutCell", parent=body, fontSize=TABLE_SIZE, leading=TABLE_LINE, spaceAfter=0)
    cell_head = ParagraphStyle("HandoutCellHead", parent=cell_body, fontName=family_sans)
    cell_center = ParagraphStyle("HandoutCellCenter", parent=cell_body, alignment=TA_CENTER)
    cell_head_center = ParagraphStyle("HandoutCellHeadCenter", parent=cell_head, alignment=TA_CENTER)
    code_style = ParagraphStyle("HandoutCode", parent=body, fontName=family_mono, fontSize=CODE_SIZE,
                                leading=CODE_LINE, spaceBefore=0, spaceAfter=0,
                                leftIndent=CODE_INDENT * 72, backColor=colors.HexColor("#" + CODE_FILL),
                                borderPadding=(4, 4, 2, 6))
    quote_style = ParagraphStyle("HandoutQuote", parent=body, leftIndent=QUOTE_INDENT * 72)
    bullet = ParagraphStyle("HandoutBullet", parent=body, leftIndent=QUOTE_INDENT * 72, bulletIndent=QUOTE_INDENT * 72 - 13)

    story: list[Any] = [Paragraph(html.escape(meta.get("title", source.stem)), title_style)]
    subtitle_text = "    ".join(meta.get(k, "") for k in ("subtitle", "audience", "duration") if meta.get(k))
    if subtitle_text:
        story.append(Paragraph(html.escape(subtitle_text).replace("  ", "&nbsp;&nbsp;"), subtitle))
    for index, b in enumerate(blocks):
        previous_kind = blocks[index - 1].kind if index else ""
        if b.kind == "heading" and b.level == 1 and b.text.strip() == meta.get("title", "").strip():
            continue
        if b.kind == "heading":
            style = {1: h1, 2: h2}.get(min(max(b.level, 1), 3), h3)
            if b.brk:
                story.append(PageBreak())
            story.append(Paragraph(html.escape(inline_text(b.text)), style))
        elif b.kind == "paragraph":
            story.append(Paragraph(pdf_markup(b.text).replace("  ", "&nbsp;&nbsp;"), body))
        elif b.kind == "quote":
            story.append(Paragraph(pdf_markup(b.text), quote_style))
        elif b.kind == "rule":
            story.append(Spacer(1, 5))
        elif b.kind == "pagebreak":
            story.append(PageBreak())
        elif b.kind == "list":
            for item in b.items:
                story.append(Paragraph(pdf_markup(item), bullet, bulletText="•"))
        elif b.kind == "image":
            image_path = (source.parent / b.path).resolve()
            if image_path.exists():
                image = Image(str(image_path))
                image._restrictSize((PAGE_W - 2 * MARGIN_LR) * inch, 4.2 * inch)
                image.hAlign = "CENTER"
                story.append(Spacer(1, IMAGE_BEFORE))
                story.append(image)
                if b.alt:
                    story.append(Paragraph(html.escape(b.alt), caption))
                else:
                    story.append(Spacer(1, CAPTION_AFTER))
        elif b.kind == "code":
            code_font = CODE_FONT
            for line_index, line in enumerate(b.lines):
                cp = doc.add_paragraph(style="Handout Code")
                cp.paragraph_format.space_before = Pt(6 if line_index == 0 else 0)
                cp.paragraph_format.space_after = Pt(6 if line_index == len(b.lines) - 1 else 0)
                cp.paragraph_format.left_indent = Inches(CODE_INDENT)
                cp.paragraph_format.line_spacing = Pt(CODE_LINE)
                _cpr = cp._p.get_or_add_pPr()
                _shd = OxmlElement("w:shd")
                _shd.set(qn("w:val"), "clear"); _shd.set(qn("w:color"), "auto")
                _shd.set(qn("w:fill"), CODE_FILL)
                _cpr.append(_shd)
                _bdr = OxmlElement("w:pBdr")
                _left = OxmlElement("w:left")
                _left.set(qn("w:val"), "single"); _left.set(qn("w:sz"), "12")
                _left.set(qn("w:space"), "4"); _left.set(qn("w:color"), CODE_RULE)
                _bdr.append(_left)
                _cpr.append(_bdr)
                _run = cp.add_run(line if line else " ")
                _rfonts(_run, code_font)
                _run.font.size = Pt(CODE_SIZE)
                _run.font.color.rgb = RGBColor.from_string(TEXT_COLOR)
        elif b.kind == "code":
            for line_index, line in enumerate(b.lines):
                code_p = ParagraphStyle("HandoutCodeLine", parent=code_style,
                                        spaceBefore=6 if line_index == 0 else 0,
                                        spaceAfter=6 if line_index == len(b.lines) - 1 else 0)
                story.append(Paragraph(html.escape(line) if line else "&nbsp;", code_p))
        elif b.kind == "tabletitle":
            story.append(Paragraph(f"<b>{html.escape(inline_text(b.text))}</b>", table_title))
        elif b.kind == "table":
            fractions, center_first = table_layout(b.headers, b.rows)
            def cell(value: str, col: int, head: bool) -> Any:
                content = html.escape(inline_text(value))
                if head:
                    style = cell_head_center if col == 0 and center_first else cell_head
                    return Paragraph(f"<b>{content}</b>", style)
                style = cell_center if col == 0 and center_first else cell_body
                return Paragraph(content, style)
            cols = max(1, len(b.headers))
            data = [[cell(c, i, True) for i, c in enumerate(b.headers)]]
            data += [[cell(c, i, False) for i, c in enumerate((row + [""] * cols)[:cols])] for row in b.rows]
            avail = (PAGE_W - 2 * MARGIN_LR) * inch
            table = Table(data, colWidths=[avail * f for f in fractions], repeatRows=1, hAlign="CENTER")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#" + TABLE_HEADER_FILL)),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#" + TABLE_BORDER)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), TABLE_PAD_H),
                ("RIGHTPADDING", (0, 0), (-1, -1), TABLE_PAD_H),
                ("TOPPADDING", (0, 0), (-1, -1), TABLE_PAD_V),
                ("BOTTOMPADDING", (0, 0), (-1, -1), TABLE_PAD_V),
            ]))
            if previous_kind != "tabletitle":
                story.append(Spacer(1, TABLE_BEFORE))
            story.append(table)
            story.append(Spacer(1, TABLE_AFTER))

    header_text = "  /  ".join(p for p in (meta.get("course", DEFAULT_COURSE), meta.get("chapter", "")) if p) or "课程讲义"
    footer_text = meta.get("title", source.stem)

    def decorate(canvas: Any, _doc: Any) -> None:
        canvas.saveState()
        canvas.setFont(family_sans, META_SIZE)
        canvas.setFillColor(black)
        canvas.drawString(MARGIN_LR * inch, PAGE_H * inch - HEADER_DIST * inch - META_SIZE, header_text)
        canvas.drawRightString(PAGE_W * inch - MARGIN_LR * inch, FOOTER_DIST * inch, f"{footer_text}   ·   {canvas.getPageNumber()}")
        canvas.restoreState()

    out.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(out), pagesize=letter,
        leftMargin=MARGIN_LR * inch, rightMargin=MARGIN_LR * inch,
        topMargin=MARGIN_TB * inch, bottomMargin=MARGIN_TB * inch,
        title=meta.get("title", source.stem), author=meta.get("author", ""),
    )
    document.build(story, onFirstPage=decorate, onLaterPages=decorate)


# --- PDF via an Office converter ----------------------------------------------
# The DOCX is the layout source of truth: exporting the PDF from it keeps page
# breaks, line breaking and bold headings identical in both files. The bundled
# ReportLab renderer stays as a portable fallback.
LO_KIT_CANDIDATES = [
    "/Applications/DeepSeek Harness.app/Contents/Resources/app.asar.unpacked/dsh/node_modules/"
    "@deepseek-ai/libreoffice-kit/lib/cli.js",
]
# Family names that Office converters map onto the platform's own Heiti/Songti
# through their built-in substitution table. A font list cannot tell whether the
# substituted face is correct, so these do not count as unexpected substitutions.
CJK_FONT_ALIASES = {
    "黑体", "宋体", "楷体", "仿宋", "隶书", "幼圆",
    "SimHei", "SimSun", "KaiTi", "FangSong", "Microsoft YaHei", "微软雅黑",
}

LO_NODE_CANDIDATES = [
    "/Applications/DeepSeek Harness.app/Contents/Resources/runtime/primary-runtime/dependencies/node/bin/node",
]


def find_pdf_converter() -> tuple[str, ...] | None:
    """Return ('kit', node, cli) or ('soffice', binary) for PDF export, else None."""
    node, cli = os.environ.get("HANDOUT_LO_NODE"), os.environ.get("HANDOUT_LO_CLI")
    if node and cli and Path(node).exists() and Path(cli).exists():
        return ("kit", node, cli)
    binary = os.environ.get("HANDOUT_SOFFICE")
    if binary and Path(binary).exists():
        return ("soffice", binary)
    for name in ("dsoffice", "soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return ("soffice", found)
    for candidate in LO_KIT_CANDIDATES:
        if Path(candidate).exists():
            node = next((n for n in LO_NODE_CANDIDATES if Path(n).exists()), shutil.which("node"))
            if node:
                return ("kit", node, candidate)
    return None


def export_pdf(converter: tuple[str, ...], docx_path: Path, pdf_path: Path) -> list[str]:
    """Convert the DOCX to PDF; return any font families the converter had to substitute."""
    if pdf_path.exists():
        pdf_path.unlink()
    if converter[0] == "kit":
        _, node, cli = converter
        proc = subprocess.run([node, cli, "convert", "--input", str(docx_path), "--output", str(pdf_path)],
                              capture_output=True, text=True)
        output = (proc.stdout or "").strip()
        missing: list[str] = []
        for line in reversed(output.splitlines()):
            try:
                payload = json.loads(line)
            except ValueError:
                continue
            missing = payload.get("missingFonts") or []
            if payload.get("error"):
                raise RuntimeError(payload["error"])
            break
        if proc.returncode != 0 or not pdf_path.exists():
            raise RuntimeError(output or (proc.stderr or "").strip() or "unknown converter error")
    else:
        # Each conversion gets its own LibreOffice profile. Without this, parallel
        # builds share one user profile and the later soffice invocations silently
        # produce no PDF at all (the failure is quiet: no log output, no non-zero exit).
        env = dict(os.environ)
        profile = env.get("HANDOUT_SOFFICE_PROFILE")
        if not profile:
            profile = str(Path(tempfile.gettempdir()) / f"handout_lo_{os.getpid()}")
        Path(profile).mkdir(parents=True, exist_ok=True)
        env["SAL_USE_VCLPLUGIN"] = "svp"
        subprocess.run([converter[1], f"-env:UserInstallation=file://{profile}",
                        "--headless", "--convert-to", "pdf",
                        "--outdir", str(pdf_path.parent), str(docx_path)],
                       check=True, capture_output=True, env=env)
        shutil.rmtree(profile, ignore_errors=True)
        generated = pdf_path.parent / (docx_path.stem + ".pdf")
        if generated.exists() and generated != pdf_path:
            generated.replace(pdf_path)
        missing = []
    if not pdf_path.exists() or pdf_path.read_bytes()[:5] != b"%PDF-":
        raise RuntimeError("converter did not produce a PDF file")
    return missing


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a portable course handout")
    ap.add_argument("source", type=Path)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--formats", default="md", help="comma-separated: md,docx,pdf")
    args = ap.parse_args()
    source = args.source.resolve(); out_dir = args.out_dir.resolve(); out_dir.mkdir(parents=True, exist_ok=True)
    meta, blocks = parse_markdown(source)
    formats = {x.strip().lower() for x in args.formats.split(",") if x.strip()}
    unknown = formats - {"md", "docx", "pdf"}
    if unknown: raise SystemExit(f"unsupported format(s): {', '.join(sorted(unknown))}")
    if "md" in formats:
        raw = source.read_text(encoding="utf-8").splitlines()
        _, body = parse_frontmatter(raw)
        head = raw[: len(raw) - len(body)]
        cleaned = head + strip_citations_document(body)
        md_out = out_dir / source.name
        if md_out.resolve() == source:
            raise SystemExit("--out-dir must differ from the source directory; the source Markdown would be overwritten")
        md_out.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
        # Keep relative image links valid in the copy by carrying the images over.
        for block in blocks:
            if block.kind != "image" or re.match(r"(?:https?:|/|#)", block.path):
                continue
            origin = (source.parent / block.path).resolve()
            target = (out_dir / block.path).resolve()
            if origin.is_file() and out_dir.resolve() in target.parents:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origin, target)
    docx_path = out_dir / (source.stem + ".docx")
    if "docx" in formats or "pdf" in formats:
        build_docx(source, docx_path, meta, blocks)
    if "pdf" in formats:
        pdf_path = out_dir / (source.stem + ".pdf")
        # Default: export the PDF from the DOCX so both files share one layout.
        # HANDOUT_PDF_FROM=markdown forces the portable ReportLab renderer;
        # HANDOUT_PDF_VIA_SOFFICE=1 is kept as an alias for the same default.
        mode = os.environ.get("HANDOUT_PDF_FROM", "docx").strip().lower()
        if os.environ.get("HANDOUT_PDF_VIA_SOFFICE") == "1":
            mode = "docx"
        if mode == "markdown":
            build_pdf(source, pdf_path, meta, blocks)
        else:
            converter = find_pdf_converter()
            if converter is None:
                print("warning: no Office converter found; using the portable renderer, "
                      "which always uses the bundled Noto families, so the PDF typography will differ from the DOCX. "
                      "Set HANDOUT_LO_NODE/HANDOUT_LO_CLI or install LibreOffice to export from the DOCX.",
                      file=sys.stderr)
                build_pdf(source, pdf_path, meta, blocks)
            else:
                try:
                    missing = export_pdf(converter, docx_path, pdf_path)
                except Exception as exc:  # converter failed: keep a usable PDF
                    print(f"warning: PDF export from the DOCX failed ({exc}); "
                          "falling back to the portable renderer, which uses the bundled Noto families", file=sys.stderr)
                    build_pdf(source, pdf_path, meta, blocks)
                else:
                    # On macOS 黑体/宋体 map onto Heiti SC / Songti SC predictably;
                    # elsewhere a missing family means a real fallback, so warn.
                    aliases = CJK_FONT_ALIASES if sys.platform == "darwin" else set()
                    unexpected = [name for name in missing if name not in aliases]
                    if unexpected:
                        print("warning: the converter substituted these fonts: " + ", ".join(unexpected)
                              + ". Run scripts/install_fonts.py once, then rebuild, "
                                "so the DOCX and PDF use the bundled CJK families.", file=sys.stderr)
    print("built", ", ".join(sorted(formats)), "in", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
