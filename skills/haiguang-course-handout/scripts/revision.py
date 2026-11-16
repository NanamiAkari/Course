#!/usr/bin/env python3
"""Revision helpers: back up a handout, or report what a user changed in Word.

The point is to make "the user edited the DOCX" a first-class state: you diff
their copy against your baseline before touching anything, and you keep a
timestamped backup every time you write.

    python scripts/revision.py lock   lesson.docx
    python scripts/revision.py backup lesson.docx [--to DIR]
    python scripts/revision.py diff   baseline.docx edited.docx
"""

from __future__ import annotations

import argparse
import difflib
import shutil
import sys
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def iter_blocks(doc):
    """Yield ('p', paragraph) and ('tbl', table) in document order."""
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            yield "p", Paragraph(child, doc)
        elif tag == "tbl":
            yield "tbl", Table(child, doc)


def run_sig(paragraph: Paragraph) -> str:
    parts = []
    for run in paragraph.runs:
        if not run.text:
            continue
        font = run.font
        size = font.size.pt if font.size else None
        color = str(font.color.rgb) if font.color and font.color.rgb else None
        parts.append(f"{size}|{font.bold}|{color}|{font.name}")
    pf = paragraph.paragraph_format
    line = pf.line_spacing.pt if hasattr(pf.line_spacing, "pt") else pf.line_spacing
    return f"{paragraph.style.name}|{line}|{paragraph.alignment}|" + ";".join(sorted(set(parts)))


def read_doc(path: Path):
    doc = Document(str(path))
    paragraphs, tables = [], []
    for kind, block in iter_blocks(doc):
        if kind == "p":
            text = block.text.strip()
            if text:
                paragraphs.append((text, run_sig(block)))
        else:
            rows = []
            for row in block.rows:
                cells, seen = [], set()
                for cell in row.cells:
                    if id(cell._tc) in seen:
                        continue
                    seen.add(id(cell._tc))
                    cells.append(cell.text.strip())
                rows.append(cells)
            tables.append(rows)
    return paragraphs, tables


def cmd_lock(path: Path) -> int:
    try:
        with path.open("ab"):
            pass
    except OSError as exc:
        print(f"LOCKED  {path}  ({exc.strerror}) — close the file in Word first")
        return 1
    print(f"writable {path}")
    return 0


def cmd_backup(path: Path, to: Path | None) -> int:
    if not path.exists():
        print(f"error: missing {path}", file=sys.stderr)
        return 2
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target_dir = to or path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{path.stem}_backup-{stamp}{path.suffix}"
    shutil.copyfile(path, target)
    print(f"backup: {target}")
    return 0


def cmd_diff(baseline: Path, edited: Path) -> int:
    for path in (baseline, edited):
        if not path.exists():
            print(f"error: missing {path}", file=sys.stderr)
            return 2
    base_p, base_t = read_doc(baseline)
    edit_p, edit_t = read_doc(edited)
    base_text = [t for t, _ in base_p]
    edit_text = [t for t, _ in edit_p]
    print(f"baseline: {baseline.name}  paragraphs={len(base_p)} tables={len(base_t)}")
    print(f"edited  : {edited.name}  paragraphs={len(edit_p)} tables={len(edit_t)}")

    sm = difflib.SequenceMatcher(None, base_text, edit_text, autojunk=False)
    added, removed, rewritten = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        old, new = base_text[i1:i2], edit_text[j1:j2]
        if tag == "insert":
            added.extend(new)
        elif tag == "delete":
            removed.extend(old)
        elif len(old) == len(new):
            rewritten.extend(zip(old, new))
        else:
            removed.extend(old)
            added.extend(new)

    print("\n== 文字改动 ==")
    for text in removed:
        print(f"  [删除] {text[:100]}")
    for text in added:
        print(f"  [新增] {text[:100]}")
    for old, new in rewritten:
        print(f"  [改写] {old[:60]}\n         -> {new[:60]}")

    print("\n== 格式改动（文字未变）==")
    base_sig = {}
    for text, sig in base_p:
        base_sig.setdefault(text, sig)
    edit_sig = {text: sig for text, sig in edit_p}
    format_diffs = 0
    for text, sig in edit_sig.items():
        if text in base_sig and base_sig[text] != sig:
            format_diffs += 1
            print(f"  [格式] {text[:50]}\n          {base_sig[text]}\n       -> {sig}")
    if not format_diffs:
        print("  （无）")

    print("\n== 表格改动 ==")
    table_diffs = 0
    for index, (old, new) in enumerate(zip(base_t, edit_t)):
        if old == new:
            continue
        table_diffs += 1
        print(f"  表 {index + 1}: {len(old)} 行 -> {len(new)} 行")
        for r, (ro, rn) in enumerate(zip(old, new)):
            if ro != rn:
                print(f"    第 {r + 1} 行: {ro} -> {rn}")
    if len(base_t) != len(edit_t):
        print(f"  表格数: {len(base_t)} -> {len(edit_t)}")
        table_diffs += 1
    if not table_diffs:
        print("  （无）")

    total = len(added) + len(removed) + len(rewritten)
    print(f"\n小结: 文字 {total} 处（删 {len(removed)} / 增 {len(added)} / 改 {len(rewritten)}），"
          f"格式 {format_diffs} 处，表格 {table_diffs} 处")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Back up or diff a handout DOCX")
    sub = ap.add_subparsers(dest="command", required=True)
    p_lock = sub.add_parser("lock", help="report whether the file can be written")
    p_lock.add_argument("path", type=Path)
    p_backup = sub.add_parser("backup", help="copy the file with a timestamp")
    p_backup.add_argument("path", type=Path)
    p_backup.add_argument("--to", type=Path, default=None)
    p_diff = sub.add_parser("diff", help="report what changed between two versions")
    p_diff.add_argument("baseline", type=Path)
    p_diff.add_argument("edited", type=Path)
    args = ap.parse_args()
    if args.command == "lock":
        return cmd_lock(args.path.resolve())
    if args.command == "backup":
        return cmd_backup(args.path.resolve(), args.to)
    return cmd_diff(args.baseline.resolve(), args.edited.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
