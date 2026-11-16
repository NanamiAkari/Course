#!/usr/bin/env python3
"""Small regression test for the portable handout builder."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCRIPTS = ROOT / "scripts"

LESSON = """---
title: 测试讲义
subtitle: 最小可验证样例
---
# 测试讲义

## 学习目标

学完后能够解释并比较两个指标，标题“与”字号一致。

## 随堂练习

- 写出一个判断条件。

表1-1、两个指标的对比

| 指标 | 含义 |
| --- | --- |
| A | 示例 |

## 来源

课程资料。

<!-- md-only -->

## 仅供查证（不印入 Word/PDF）

资料库编号 L99。
"""



def build(source: Path, out: Path, formats: str) -> None:
    subprocess.run([PYTHON, str(SCRIPTS / "build_handout.py"), str(source),
                    "--out-dir", str(out), "--formats", formats], check=True)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="course-handout-test-") as raw:
        work = Path(raw)
        source = work / "lesson.md"
        source.write_text(LESSON, encoding="utf-8")

        out = work / "out"
        build(source, out, "md,docx,pdf")

        for name in ("lesson.md", "lesson.docx", "lesson.pdf"):
            path = out / name
            if not path.exists() or path.stat().st_size == 0:
                raise AssertionError(f"missing output: {path}")
            subprocess.run([PYTHON, str(SCRIPTS / "validate_handout.py"), str(path)], check=True)

        if (out / "lesson.pdf").read_bytes()[:5] != b"%PDF-":
            raise AssertionError("PDF is missing its signature")

        # The frontmatter title and the H1 carry the same text: it must print once.
        from docx import Document
        doc = Document(str(out / "lesson.docx"))
        titles = [p.text.strip() for p in doc.paragraphs if p.style.name == "Title"]
        if titles != ["测试讲义"]:
            raise AssertionError(f"expected exactly one title paragraph, got {titles}")
        repeats = [p.text.strip() for p in doc.paragraphs
                   if p.style.name.startswith("Heading") and p.text.strip() == "测试讲义"]
        if repeats:
            raise AssertionError("the lesson title is duplicated as a heading")
        if not doc.tables or len(doc.tables[0].rows) < 2:
            raise AssertionError("the markdown table was not rendered")
        if not any(p.style.name == "Heading 2" and p.text.strip() == "学习目标" for p in doc.paragraphs):
            raise AssertionError("heading level 2 is missing")

        # md-only blocks stay in the Markdown and disappear from DOCX/PDF.
        if any("仅供查证" in p.text or "资料库编号 L99" in p.text for p in doc.paragraphs):
            raise AssertionError("md-only block leaked into the DOCX")
        if "仅供查证" not in (out / "lesson.md").read_text(encoding="utf-8"):
            raise AssertionError("md-only block was dropped from the Markdown copy")
        if "仅供查证" in "".join(p.extract_text() or "" for p in __import__("pypdf").PdfReader(str(out / "lesson.pdf")).pages):
            raise AssertionError("md-only block leaked into the PDF")

        # Default typefaces follow the Chinese academic convention.
        if doc.styles["Normal"].font.name != "宋体":
            raise AssertionError(f"body font is {doc.styles['Normal'].font.name!r}, expected 宋体")
        if doc.styles["Heading 2"].font.name != "黑体":
            raise AssertionError(f"heading font is {doc.styles['Heading 2'].font.name!r}, expected 黑体")
        if doc.styles["Heading 2"].font.size.pt != 13 or doc.styles["Normal"].font.size.pt != 11.5:
            raise AssertionError("sizes changed; the typeface switch must not touch them")

    print("course-handout tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
