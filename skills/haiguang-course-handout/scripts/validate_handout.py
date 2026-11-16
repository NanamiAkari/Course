#!/usr/bin/env python3
"""Validate a course handout source or generated deliverable."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# Non-fatal findings: printed after the errors, never change the exit code.
WARNINGS: list[str] = []


def validate_md(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if "TODO" in text or "[TODO" in text: errors.append("unresolved TODO marker")
    lines = text.splitlines()
    if not lines or not any(re.match(r"^#\s+\S", line) for line in lines): errors.append("missing level-1 title")
    if not re.search(r"(?i)(学习目标|learning objectives|objectives)", text): errors.append("missing learning objectives")
    if not re.search(r"(?i)(练习|自测|随堂思考|exercise|self-test)", text): errors.append("missing learner practice or self-test")
    # A sources section is optional. What is not optional is provenance for the
    # numbers and figures copied from external material, so this is a reminder.
    if not re.search(r"(?i)(来源|参考|source|reference)", text):
        WARNINGS.append("no sources section: give every external figure and number a provenance note "
                        "(table note, figure caption, or a sources list)")
    captions: list[str] = []
    for match in re.finditer(r"!\[([^]]*)\]\(([^)]+)\)", text):
        caption, value = match.group(1).strip(), match.group(2).strip()
        if caption:
            captions.append(caption)
        if re.match(r"(?:https?:|mailto:|#)", value):
            continue
        if not caption:
            WARNINGS.append(f"figure without a caption: {value}")
        if not (path.parent / value).exists(): errors.append(f"missing local link or image: {value}")
    for target in re.findall(r"(?<!!)\[[^]]+\]\(([^)]+)\)", text):
        value = target
        if re.match(r"(?:https?:|mailto:|#)", value):
            continue
        if not (path.parent / value).exists(): errors.append(f"missing local link or image: {value}")
    if len(re.findall(r"^#{1,6}\s+", text, flags=re.M)) < 3: errors.append("outline is too short for a lesson handout")
    headings: list[tuple[int, str]] = []
    tables_at: list[tuple[int, str]] = []
    for line_no, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            headings.append((len(match.group(1)), match.group(2).strip()))
            continue
        if "|" in line and line_no + 1 < len(lines) and TABLE_SEPARATOR.match(lines[line_no + 1]):
            tables_at.append((len(headings), line.strip().strip("|").replace("|", " ")))
    structure_errors, structure_warnings = structure_report(headings, text, tables_at)
    errors += structure_errors
    WARNINGS.extend(structure_warnings)
    WARNINGS.extend(caption_source_warnings(captions + [l.strip() for l in lines if TABLE_TITLE.match(l.strip())]))
    WARNINGS.extend(next_lesson_warnings(text))
    errors += table_title_errors(lines)
    errors += table_shape_errors(lines)
    errors += meta_phrase_errors(text)
    WARNINGS.extend(quote_warnings(text))
    errors += citation_errors(re.sub(r"`[^`]*`", "", text))
    return errors


# Every table needs a title line directly above it, starting with 表 + number.
TABLE_TITLE = re.compile(r"^表\s*[0-9一二三四五六七八九十]")
TABLE_SEPARATOR = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$")


# A lesson stands on its own: no "下一讲…" bridge at the end of the analysis.
NEXT_LESSON = re.compile(r"下一讲|下一节课|下一课[：:]")


def next_lesson_warnings(text: str) -> list[str]:
    found = sorted({m.group(0) for m in NEXT_LESSON.finditer(text)})
    if not found:
        return []
    return [f"正文里有跨讲衔接「{found[0]}」：讲义自成一讲，讲到哪儿就在哪儿收尾（衔接句删掉）"]


# Figure captions and table titles describe what the reader sees. A source in
# parentheses ("(H3C iFIST 配置指导图3-19)") belongs in the sources list, not in
# the caption, so the caption stays one clean line under the picture.
SOURCE_PAREN = re.compile(r"[（(][^）)]{0,40}?(图\s*\d|手册|指南|配置指导|培训材料|原图|白皮书)[^）)]{0,20}?[）)]")


def caption_source_warnings(captions: list[str]) -> list[str]:
    found: list[str] = []
    for caption in captions:
        match = SOURCE_PAREN.search(caption)
        if match:
            snippet = caption[:40] + ("…" if len(caption) > 40 else "")
            found.append(f"图注/表题里带来源括注「{match.group(0)}」：{snippet}（出处放来源节，图注不写）")
    return found


def table_title_errors(lines: list[str]) -> list[str]:
    errors: list[str] = []
    for index in range(1, len(lines) - 1):
        if "|" not in lines[index] or not TABLE_SEPARATOR.match(lines[index + 1]):
            continue
        previous = index - 1
        while previous >= 0 and not lines[previous].strip():
            previous -= 1
        if previous < 0 or not TABLE_TITLE.match(lines[previous].strip().lstrip("*")):
            errors.append(f"table without a title line before line {index + 1} (expected 表…)")
    return errors


# A raw "|" inside a cell splits it in two: Markdown cannot escape it reliably,
# and the builder just splits on the pipe, so the whole row shifts one column.
CELL_SPLIT = re.compile(r"(?<!\\)\|")


def table_shape_errors(lines: list[str]) -> list[str]:
    errors: list[str] = []
    index = 0
    while index < len(lines) - 1:
        if "|" not in lines[index] or not TABLE_SEPARATOR.match(lines[index + 1]):
            index += 1
            continue
        header = CELL_SPLIT.split(lines[index].strip().strip("|"))
        width = len(header)
        row = index + 2
        while row < len(lines) and lines[row].strip().startswith("|"):
            cells = CELL_SPLIT.split(lines[row].strip().strip("|"))
            if len(cells) != width:
                errors.append(f"表格第 {row + 1} 行有 {len(cells)} 列、表头 {width} 列："
                              f"单元格里可能写了竖线 |，整行会错位")
            row += 1
        index = row
    return errors


ASCII_QUOTE = re.compile(r'"')


def quote_warnings(text: str) -> list[str]:
    body = text
    if body.startswith("---"):
        parts = body.split("---", 2)
        if len(parts) == 3:
            body = parts[2]
    body = re.sub(r"`[^`]*`", "", body)
    hits = len(ASCII_QUOTE.findall(body))
    if hits:
        return [f"正文里有 {hits} 个 ASCII 双引号：渲染时会变成镜像的「”」，请改用中文引号「“ ”」"]
    return []


# The handout must not talk about itself: no provenance in body text, no
# "this lesson does not cover X", no disclaimers. Those sentences are the
# model protecting itself, not information for the reader.
META_PATTERNS = (
    (re.compile(r"(本节|本讲|本文|本课)内容?(出自|来自|取材)"), "出处写进了正文，应放图注、表注或来源节"),
    (re.compile(r"(本节|本讲)(不|只|仅|不再)"), "用否定句划范围，应写成正面条件或整句删掉"),
    (re.compile(r"不在(本节|本讲)|不属于本讲|超出本讲"), "反指本讲范围，应整句删掉"),
    (re.compile(r"为避免误解|需要说明的是|需要强调的是|严格来说|限于篇幅|不再赘述"), "免责套话，应整句删掉"),
)


def meta_phrase_errors(text: str) -> list[str]:
    body = text
    if body.startswith("---"):
        parts = body.split("---", 2)
        if len(parts) == 3:
            body = parts[2]
    body = re.sub(r"`[^`]*`", "", body)
    found: list[str] = []
    for pattern, reason in META_PATTERNS:
        for match in pattern.finditer(body):
            start = max(0, match.start() - 6)
            end = min(len(body), match.end() + 20)
            snippet = re.sub(r"\s+", " ", body[start:end]).strip()
            message = f"正文有文档自指的句子：「{snippet}」（{reason}）"
            if message not in found:
                found.append(message)
    return found[:8]


# Numeric citation markers such as [1], [2,3], [4-6], [^1], ［1］ are not allowed.
CITE = re.compile(r"(?:\[\^?|［)\d+(?:\s*[,，、\-–~]\s*\d+)*(?:\]|］)(?!\()")


# DOCX/PDF lose code-span backticks, so skip index-like brackets such as arr[1].
CITE_RENDERED = re.compile(r"(?<![A-Za-z0-9_\]\)])" + CITE.pattern)


def citation_errors(text: str, rendered: bool = False) -> list[str]:
    found = sorted(set((CITE_RENDERED if rendered else CITE).findall(text)))
    if not found: return []
    more = f" (+{len(found) - 5} more)" if len(found) > 5 else ""
    return [f"citation markers present: {' '.join(found[:5])}{more}"]


# --- skeleton ---------------------------------------------------------------
#
# Every lesson carries the same blocks in this order:
#   学习目标 -> 理论节 -> 实训 -> 硬件 -> 视频 -> 小结（-> 附录 / 来源）
# The theory block is "whatever H2 sits between 目标 and 实训"; it must exist and
# must not smuggle in step-by-step practice sections.
BLOCKS = (
    ("学习目标", re.compile(r"学习目标|教学目标"), "「学习目标」"),
    ("实训节", re.compile(r"实训|实操|实践"), "「实训」或「实操」"),
    ("硬件节", re.compile(r"硬件|设施|设备"), "「硬件」或「设施」"),
    ("视频节", re.compile(r"视频"), "「视频」"),
    ("小结节", re.compile(r"小结|回顾|总结|自测"), "「小结」「回顾」或「自测」"),
)
TRAILING = re.compile(r"^(附录|来源|参考|附)")
ACTION_HEAD = re.compile(r"^(逐步|实训|实操)")
NUMBERED_H2 = re.compile(r"^\d+\.\d+、")
TABLE_ID = re.compile(r"^表\s*(\d+)\s*[-－]\s*(\d+)、")


STEPS_HEADER = ("动作与要领", "常见错误", "检查点")


def structure_report(headings: list[tuple[int, str]], text: str,
                     tables_at: list[tuple[int, str]] | None = None) -> tuple[list[str], list[str]]:
    """Check the fixed lesson skeleton. Returns (errors, warnings).

    `tables_at` holds, for every table in document order, how many headings came
    before it plus its header row. A table recorded at position n belongs to
    heading n-1, which is how the checks below know whether a section actually
    carries a table, and whether that table has the lesson step columns.
    """
    errors: list[str] = []
    warnings: list[str] = []
    tables = tables_at or []
    owners = {position - 1 for position, _ in tables}
    headers = {position - 1: header for position, header in tables}
    h2 = [(index, title) for index, (level, title) in enumerate(headings) if level == 2]
    if not h2:
        return ["没有二级标题：讲义至少要分出目标、理论、实训、硬件、视频、小结几节"], []

    found: dict[str, tuple[int, str]] = {}
    for name, pattern, _ in BLOCKS:
        for index, title in h2:
            if pattern.search(title):
                found[name] = (index, title)
                break
    for name, _, hint in BLOCKS:
        if name not in found:
            errors.append(f"缺少{name}：H2 里找不到{hint}")
    if errors:
        return errors, warnings

    order = [found[name][0] for name, _, _ in BLOCKS]
    labels = [name for name, _, _ in BLOCKS]
    for left in range(len(order) - 1):
        right_order = left + 1
        if order[left] > order[right_order]:
            errors.append(f"节顺序不对：{labels[left]} 应排在 {labels[right_order]} 之前")

    target_at, drill_at = found["学习目标"][0], found["实训节"][0]
    theory = [index for index, _ in h2 if target_at < index < drill_at]
    if not theory:
        errors.append("没有理论节：学习目标与实训之间的 H2 至少要有一个（知识内容都放这里）")

    for position, (index, title) in enumerate(h2):
        if index not in theory:
            continue
        stop = h2[position + 1][0] if position + 1 < len(h2) else len(headings)
        for level, head in headings[index + 1:stop]:
            bare = re.sub(r"^\d+\.\d+(?:\.\d+)?、", "", head).strip()
            if level == 3 and ACTION_HEAD.match(bare):
                errors.append(f"理论节里出现动作小节：{head}（逐步/实训类小节应放进实训节）")

    h2_position = {index: position for position, (index, _) in enumerate(h2)}

    def section_headings(index: int) -> list[tuple[int, int, str]]:
        position = h2_position[index]
        stop = h2[position + 1][0] if position + 1 < len(h2) else len(headings)
        return [(j, level, head) for j, (level, head) in
                enumerate(headings[index + 1:stop], start=index + 1)]

    # Every task in the practice section carries a step table.
    tasks = [head for _, level, head in section_headings(found["实训节"][0]) if level == 3]
    if not tasks:
        errors.append("实训节里没有任何任务小节（N.3.1 起，一个任务一张表）")
    for index, level, head in section_headings(found["实训节"][0]):
        if level != 3:
            continue
        if index not in owners:
            errors.append(f"实训小节没有步骤表：{head}（每个任务配一张四列表）")
            continue
        header = headers.get(index, "")
        missing = [column for column in STEPS_HEADER if column not in header]
        if missing:
            errors.append(f"实训步骤表列头缺「{'」「'.join(missing)}」：{head}"
                          f"（应为 步 / 动作与要领 / 常见错误 / 检查点）")

    # The hardware and video sections are lists, so they need a table too.
    # A table may hang off a sub-heading (42.5.1 视频清单), so scan the span.
    for name in ("硬件节", "视频节"):
        index = found[name][0]
        position = h2_position[index]
        stop = h2[position + 1][0] if position + 1 < len(h2) else len(headings)
        if not any(index <= j < stop for j in owners):
            warnings.append(f"{found[name][1]} 一节没有表格（按约定应给出清单表）")

    # The glossary closes the theory block.
    theory_heads = [(index, head) for section in theory
                    for index, level, head in section_headings(section) if level == 3]
    if not theory_heads:
        warnings.append("理论节没有小节，也没有术语表")
    elif not re.search(r"术语", theory_heads[-1][1]):
        warnings.append(f"理论节末尾不是术语表：最后一个理论小节是「{theory_heads[-1][1]}」")

    last = found["小结节"][0]
    for index, title in h2:
        bare = re.sub(r"^\d+\.\d+、", "", title).strip()
        if index > last and not TRAILING.match(bare):
            warnings.append(f"小结之后还有一节：{title}（确认不是漏排到附录里）")

    for _, title in h2:
        if not NUMBERED_H2.match(title):
            warnings.append(f"二级标题没有 N.M、 编号：{title}")

    numbers = [(int(lesson), int(seq)) for lesson, seq in TABLE_ID.findall(text)]
    if numbers:
        lessons = {lesson for lesson, _ in numbers}
        if len(lessons) > 1:
            warnings.append(f"表格题注混用了多个讲次编号：{sorted(lessons)}")
        sequences = [seq for _, seq in numbers]
        if sequences != list(range(1, len(sequences) + 1)):
            warnings.append("表格编号不是从 1 起连续：" + " ".join(f"表{numbers[0][0]}-{s}" for s in sequences))
    return errors, warnings


def validate_docx(path: Path) -> list[str]:
    try:
        from docx import Document
    except ImportError:
        return ["python-docx is unavailable for DOCX validation"]
    doc = Document(path); errors: list[str] = []
    nonempty = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    if not nonempty: errors.append("DOCX has no readable paragraphs")
    if not any(p.style and p.style.name == "Title" for p in doc.paragraphs): errors.append("DOCX has no Title paragraph style")
    if not doc.tables and len(nonempty) < 3: errors.append("DOCX has too little content")
    cells = [c.text for t in doc.tables for r in t.rows for c in r.cells]
    levels = {"Heading 1": 1, "Heading 2": 2, "Heading 3": 3}
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    headings: list[tuple[int, str]] = []
    tables_at: list[tuple[int, str]] = []
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "tbl":
            table = Table(child, doc)
            header = " ".join(cell.text.strip() for cell in table.rows[0].cells) if table.rows else ""
            tables_at.append((len(headings), header))
        elif tag == "p":
            para = Paragraph(child, doc)
            level = levels.get(para.style.name if para.style else "")
            if level and para.text.strip():
                headings.append((level, para.text.strip()))
    structure_errors, structure_warnings = structure_report(headings, "\n".join(nonempty + cells), tables_at)
    errors += structure_errors
    WARNINGS.extend(structure_warnings)
    caption_texts = [p.text.strip() for p in doc.paragraphs if p.style and p.style.name == "Caption"]
    WARNINGS.extend(caption_source_warnings(caption_texts))
    WARNINGS.extend(next_lesson_warnings("\n".join(nonempty)))
    errors += meta_phrase_errors("\n".join(nonempty + cells))
    errors += citation_errors("\n".join(nonempty + cells), rendered=True)
    return errors


def validate_pdf(path: Path) -> list[str]:
    errors: list[str] = []
    if path.stat().st_size < 1000: errors.append("PDF is unexpectedly small")
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        if not reader.pages: errors.append("PDF has no pages")
        page_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not page_text.strip(): errors.append("PDF has no extractable text")
        errors += citation_errors(page_text, rendered=True)
    except ImportError:
        if path.read_bytes()[:5] != b"%PDF-": errors.append("file is not a PDF")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate a course handout")
    ap.add_argument("path", type=Path)
    args = ap.parse_args(); path = args.path.resolve()
    if not path.exists(): print(f"error: missing {path}", file=sys.stderr); return 2
    suffix = path.suffix.lower()
    errors = validate_md(path) if suffix in {".md", ".markdown"} else validate_docx(path) if suffix == ".docx" else validate_pdf(path) if suffix == ".pdf" else [f"unsupported file type: {suffix}"]
    for warning in WARNINGS:
        print("warning:", warning)
    if errors:
        print("validation failed for", path)
        for e in errors: print("-", e)
        return 1
    print("validated", path)
    return 0


if __name__ == "__main__": raise SystemExit(main())
