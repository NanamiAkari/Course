#!/usr/bin/env python3
"""Install the bundled CJK families so an Office converter can use them.

The DOCX embeds font subsets, but LibreOffice/soffice resolve fonts from the
operating system when it exports a PDF. If the two families are not installed,
the export substitutes them and the PDF no longer matches the DOCX
(headings lose their weight, characters sit at different optical sizes).

    python scripts/install_fonts.py            # copy missing files
    python scripts/install_fonts.py --check    # report only, change nothing
    python scripts/install_fonts.py --remove   # undo the copy

Files are copied to the user font directory, never to a system directory.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "assets"
FAMILIES = (
    "NotoSerifCJKsc-Regular.otf",
    "NotoSansCJKsc-Regular.otf",
    "NotoSansCJKsc-Bold.otf",
)


def font_dir() -> Path:
    override = os.environ.get("HANDOUT_FONT_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Fonts"
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Microsoft" / "Windows" / "Fonts"
    return Path.home() / ".local" / "share" / "fonts"


def refresh_cache() -> None:
    if sys.platform.startswith("linux") and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f"], capture_output=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Install or remove the bundled CJK fonts")
    ap.add_argument("--check", action="store_true", help="report status without changing anything")
    ap.add_argument("--remove", action="store_true", help="remove the files this script installed")
    args = ap.parse_args()

    target_dir = font_dir()
    missing_assets = [name for name in FAMILIES if not (ASSETS / name).exists()]
    if missing_assets:
        print("missing bundled font(s): " + ", ".join(missing_assets), file=sys.stderr)
        return 2

    installed = [name for name in FAMILIES if (target_dir / name).exists()]
    if args.check:
        print(f"target directory: {target_dir}")
        for name in FAMILIES:
            print(("  installed  " if name in installed else "  missing    ") + name)
        return 0 if len(installed) == len(FAMILIES) else 1

    if args.remove:
        removed = 0
        for name in installed:
            (target_dir / name).unlink()
            removed += 1
        refresh_cache()
        print(f"removed {removed} font file(s) from {target_dir}")
        return 0

    target_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for name in FAMILIES:
        source = ASSETS / name
        target = target_dir / name
        if target.exists() and target.stat().st_size == source.stat().st_size:
            continue
        shutil.copy2(source, target)
        copied += 1
    refresh_cache()
    print(f"installed {copied} font file(s) into {target_dir} ({len(installed)} were already present)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
