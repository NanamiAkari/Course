#!/usr/bin/env python3
"""Validate a course handout source or generated deliverable."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def validate_md(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if "TODO" in text or "[TODO" in text: errors.append("unresolved TODO marker")
    lines = text.splitlines()
    if not lines or not any(re.match(r"^#\s+\S", line) for line in lines): errors.append("missing level-1 title")
    if not re.search(r"(?i)(学习目标|learning objectives|objectives)", text): errors.append("missing learning objectives")
    if not re.search(r"(?i)(练习|自测|随堂思考|exercise|self-test)", text): errors.append("missing learner practice or self-test")
    if not re.search(r"(?i)(来源|参考|source|reference)", text): errors.append("missing sources section or source marker")
    for target in re.findall(r"!\[[^]]*\]\(([^)]+)\)|\[[^]]+\]\(([^)]+)\)", text):
        value = next(x for x in target if x)
        if re.match(r"(?:https?:|mailto:|#)", value): continue
        if not (path.parent / value).exists(): errors.append(f"missing local link or image: {value}")
    if len(re.findall(r"^#{1,6}\s+", text, flags=re.M)) < 3: errors.append("outline is too short for a lesson handout")
    errors += table_title_errors(lines)
    errors += citation_errors(re.sub(r"`[^`]*`", "", text))
    return errors


# Every table needs a title line directly above it, starting with 表 + number.
TABLE_TITLE = re.compile(r"^表\s*[0-9一二三四五六七八九十]")
TABLE_SEPARATOR = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$")


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


# Numeric citation markers such as [1], [2,3], [4-6], [^1], ［1］ are not allowed.
CITE = re.compile(r"(?:\[\^?|［)\d+(?:\s*[,，、\-–~]\s*\d+)*(?:\]|］)(?!\()")


# DOCX/PDF lose code-span backticks, so skip index-like brackets such as arr[1].
CITE_RENDERED = re.compile(r"(?<![A-Za-z0-9_\]\)])" + CITE.pattern)


def citation_errors(text: str, rendered: bool = False) -> list[str]:
    found = sorted(set((CITE_RENDERED if rendered else CITE).findall(text)))
    if not found: return []
    more = f" (+{len(found) - 5} more)" if len(found) > 5 else ""
    return [f"citation markers present: {' '.join(found[:5])}{more}"]


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
    if errors:
        print("validation failed for", path)
        for e in errors: print("-", e)
        return 1
    print("validated", path)
    return 0


if __name__ == "__main__": raise SystemExit(main())
