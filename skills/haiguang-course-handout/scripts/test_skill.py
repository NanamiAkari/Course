#!/usr/bin/env python3
"""Small regression test for the portable handout builder."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
SCRIPTS = ROOT / "scripts"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")

LESSON = """---
title: 测试讲义
---
# 测试讲义

## 1.1、学习目标

学完后能够解释并比较两个指标。达成标志：能说出两者的差别。

## 1.2、指标怎么看

正文一句话，说明这一节讲什么。

表1-1、两个指标的对比

| 指标 | 含义 |
| --- | --- |
| A | 示例 |

## 1.3、具体实训内容

### 1.3.1、做一件事

表1-2、实训步骤

| 步 | 动作与要领 | 常见错误 | 检查点 |
| --- | --- | --- | --- |
| 1 | 做一件事 | 做反了 | 能看到结果 |

红线：不许带电操作。

## 1.4、需要的硬件设施

表1-3、工具

| 名称 | 型号 / 规格 | 用途 |
| --- | --- | --- |
| 螺丝刀 | T25 | 挂耳螺钉 |

## 1.5、配套视频

表1-4、视频清单

| 视频名 | 时长 | 内容要点 |
| --- | --- | --- |
| 装挂耳 | 5 min | 贴合检查 |

## 1.6、小结与自测

表1-5、目标回看

| 学习目标 | 达成标志 |
| --- | --- |
| 说清两个指标 | 能比较 |

【课后自测】写出一个判断条件。
"""


def build(source: Path, out: Path, formats: str) -> None:
    subprocess.run([PYTHON, str(SCRIPTS / "build_handout.py"), str(source),
                    "--out-dir", str(out), "--formats", formats], check=True)


def validate(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run([PYTHON, str(SCRIPTS / "validate_handout.py"), str(path)],
                          capture_output=True, text=True, encoding="utf-8", env=ENV)


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
            result = validate(path)
            if result.returncode != 0:
                raise AssertionError(f"a complete skeleton must pass: {path}\n{result.stdout}")

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
        if not any(p.style.name == "Heading 2" and p.text.strip().endswith("学习目标")
                   for p in doc.paragraphs):
            raise AssertionError("heading level 2 is missing")

        # Default typefaces follow the Chinese academic convention.
        if doc.styles["Normal"].font.name != "宋体":
            raise AssertionError(f"body font is {doc.styles['Normal'].font.name!r}, expected 宋体")
        if doc.styles["Heading 2"].font.name != "黑体":
            raise AssertionError(f"heading font is {doc.styles['Heading 2'].font.name!r}, expected 黑体")
        if doc.styles["Heading 2"].font.size.pt != 18 or doc.styles["Normal"].font.size.pt != 11.5:
            raise AssertionError("sizes changed; the typeface switch must not touch them")
        if doc.styles["Heading 1"].font.size.pt != 20:
            raise AssertionError("level-1 heading must stay larger than the 18 pt level-2 heading")
        h2 = next(p for p in doc.paragraphs if p.style.name == "Heading 2")
        if (h2.paragraph_format.space_before.pt != 14) or (h2.paragraph_format.space_after.pt != 8):
            raise AssertionError("level-2 heading spacing must be 14 pt before / 8 pt after")

        # Provenance & header-bar leaks must fail validation.
        leak_cases = {
            "header-bar": ("---\n# 测试讲义", "subtitle: 《智慧算力运维工程师》· 海光专项 · 课程讲义\n---\n# 测试讲义"),
            "provenance-note": ("表1-1、两个指标的对比", "表1-1、两个指标的对比（源自《H3C UniServer R4930 G7 用户指南》，6W111-20260730）"),
        }
        for name, (old_s, new_s) in leak_cases.items():
            leak_dir = work / name
            leak_dir.mkdir()
            leak_source = leak_dir / "lesson.md"
            leak_source.write_text(LESSON.replace(old_s, new_s), encoding="utf-8")
            result = validate(leak_source)
            if result.returncode == 0:
                raise AssertionError(f"forbidden {name} must fail validation: {result.stdout}")

        # The skeleton is enforced: a lesson without a practice block is rejected.
        broken = work / "no-practice"
        broken.mkdir()
        broken_source = broken / "lesson.md"
        broken_source.write_text(LESSON.replace("## 1.3、具体实训内容", "## 1.3、更多说明"),
                                 encoding="utf-8")
        result = validate(broken_source)
        if result.returncode == 0:
            raise AssertionError("a lesson without a practice section must fail validation")
        if "实训" not in result.stdout:
            raise AssertionError(f"the failure must name the missing practice block: {result.stdout}")

        # A practice task without a step table is not a practice section.
        table_block = """表1-2、实训步骤

| 步 | 动作与要领 | 常见错误 | 检查点 |
| --- | --- | --- | --- |
| 1 | 做一件事 | 做反了 | 能看到结果 |
"""
        no_table = work / "no-table"
        no_table.mkdir()
        no_table_source = no_table / "lesson.md"
        no_table_source.write_text(LESSON.replace(table_block, ""), encoding="utf-8")
        result = validate(no_table_source)
        if result.returncode == 0 or "步骤表" not in result.stdout:
            raise AssertionError(f"a task without a step table must fail: {result.stdout}")

        # A step table must carry the lesson columns, not just any table.
        steps_block = """| 步 | 动作与要领 | 常见错误 | 检查点 |
| --- | --- | --- | --- |
| 1 | 做一件事 | 做反了 | 能看到结果 |"""
        two_col_block = """| 步骤 | 说明 |
| --- | --- |
| 1 | 做一件事 |"""
        wrong_columns = work / "wrong-columns"
        wrong_columns.mkdir()
        wrong_source = wrong_columns / "lesson.md"
        wrong_source.write_text(LESSON.replace(steps_block, two_col_block), encoding="utf-8")
        result = validate(wrong_source)
        if result.returncode == 0 or "列头" not in result.stdout:
            raise AssertionError(f"a step table without the lesson columns must fail: {result.stdout}")

        # A raw pipe inside a cell shifts the row: that must be an error.
        piped = work / "piped"
        piped.mkdir()
        piped_source = piped / "lesson.md"
        piped_source.write_text(
            LESSON.replace("| 1 | 做一件事 | 做反了 | 能看到结果 |",
                           "| 1 | 做一件事 lspci | grep K0 | 做反了 | 能看到结果 |"),
            encoding="utf-8")
        result = validate(piped_source)
        if result.returncode == 0 or "竖线" not in result.stdout:
            raise AssertionError(f"a raw pipe inside a cell must fail: {result.stdout}")

        # ASCII double quotes in prose render as mirrored marks: warn, do not fail.
        quoted = work / "quoted"
        quoted.mkdir()
        quoted_source = quoted / "lesson.md"
        quoted_source.write_text(LESSON.replace("正文一句话，说明这一节讲什么。",
                                                '正文一句话，他说"这样做"。'),
                                 encoding="utf-8")
        result = validate(quoted_source)
        if result.returncode != 0:
            raise AssertionError(f"ASCII quotes are a warning, not an error: {result.stdout}")
        if "ASCII" not in result.stdout:
            raise AssertionError(f"ASCII quotes must be reported: {result.stdout}")

        # The handout must not talk about itself.
        meta_cases = {
            "scope-denial": "## 1.2、更多说明\n\n本讲不做开盖扩容。\n",
            "provenance": "## 1.2、更多说明\n\n本节内容出自《用户指南》。\n",
        }
        for name, replacement in meta_cases.items():
            meta_dir = work / name
            meta_dir.mkdir()
            meta_source = meta_dir / "lesson.md"
            meta_source.write_text(LESSON.replace("## 1.2、指标怎么看\n\n正文一句话，说明这一节讲什么。\n",
                                                  replacement), encoding="utf-8")
            result = validate(meta_source)
            if result.returncode == 0 or "文档自指" not in result.stdout:
                raise AssertionError(f"meta talk must fail ({name}): {result.stdout}")

        # Ordinary self-reference is fine and must not be flagged.
        normal = work / "normal-self-reference"
        normal.mkdir()
        normal_source = normal / "lesson.md"
        normal_source.write_text(LESSON.replace("正文一句话，说明这一节讲什么。",
                                                "本讲是海光专项的第一讲。学完本讲，你应当能够比较两个指标。"),
                                 encoding="utf-8")
        result = validate(normal_source)
        if result.returncode != 0:
            raise AssertionError(f"ordinary self-reference must pass: {result.stdout}")

        # Step-by-step sections are not allowed inside the theory block.
        mixed = work / "mixed"
        mixed.mkdir()
        mixed_source = mixed / "lesson.md"
        mixed_source.write_text(LESSON.replace("## 1.3、具体实训内容", "## 1.3、具体实训内容")
                                .replace("正文一句话，说明这一节讲什么。",
                                         "正文一句话。\n\n### 1.2.1、逐步：动手做\n\n做点事。"),
                                encoding="utf-8")
        result = validate(mixed_source)
        if result.returncode == 0 or "动作小节" not in result.stdout:
            raise AssertionError(f"a 逐步 section inside the theory block must fail: {result.stdout}")

    print("haiguang-course-handout tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
