#!/usr/bin/env python3
"""Embed subsetted CJK fonts in a DOCX package.

Each ``--font FAMILY|ROLE|PATH`` triple adds one embedded font. ROLE is
``embedRegular``, ``embedBold``, ``embedItalic`` or ``embedBoldItalic``. A
family may be passed more than once to supply several roles.

FontTools is intentionally optional. When it is unavailable the caller keeps a
valid DOCX and can use an installed CJK font instead.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def parse_spec(spec: str) -> tuple[str, str, Path]:
    try:
        family, role, path = spec.split("|", 2)
    except ValueError:
        raise SystemExit(f"--font must be FAMILY|ROLE|PATH, got: {spec}")
    role = role if role.startswith("embed") else "embed" + role.capitalize()
    return family.strip(), role, Path(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("docx", type=Path)
    ap.add_argument("--font", action="append", required=True, metavar="FAMILY|ROLE|PATH")
    args = ap.parse_args()
    try:
        from lxml import etree as E
    except ImportError as exc:
        print(f"font embedding unavailable: {exc}", file=sys.stderr)
        return 2
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
    CT = "http://schemas.openxmlformats.org/package/2006/content-types"
    with ZipFile(args.docx) as z:
        files = {name: z.read(name) for name in z.namelist()}

    try:
        import io

        from fontTools import subset
        from fontTools.ttLib import TTFont
        text = "".join("".join(E.fromstring(value).itertext()) for name, value in files.items()
                       if name.startswith("word/") and name.endswith(".xml"))
        chars = set(ord(c) for c in text)
        chars.update(range(32, 127))
        chars.update(range(0x3000, 0x3040))  # CJK punctuation is typed far more often than it appears
    except ImportError:
        subset = None

    font_table = E.fromstring(files["word/fontTable.xml"])
    rels = E.Element(f"{{{PKG}}}Relationships", nsmap={None: PKG})
    for index, spec in enumerate(args.font, 1):
        family, role, path = parse_spec(spec)
        if not path.exists():
            print(f"warning: font not found: {path}", file=sys.stderr)
            continue
        if subset is not None:
            font = TTFont(str(path))
            options = subset.Options()
            options.name_IDs = ["*"]; options.name_legacy = True
            options.name_languages = ["*"]; options.layout_features = ["*"]
            subsetter = subset.Subsetter(options=options)
            subsetter.populate(unicodes=chars)
            subsetter.subset(font)
            buffer = io.BytesIO(); font.save(buffer)
            data = bytearray(buffer.getvalue())
            embedded = "1"
        else:
            # A full embedded font is larger but keeps the skill functional with
            # only lxml and the Python standard library.
            data = bytearray(path.read_bytes())
            embedded = "0"
        key = uuid.uuid4(); key_bytes = key.bytes[::-1]
        for offset in range(min(32, len(data))):
            data[offset] ^= key_bytes[offset % 16]
        target = f"fonts/handoutFont{index}.odttf"
        files["word/" + target] = bytes(data)
        entry = next((node for node in font_table if node.get(f"{{{W}}}name") == family), None)
        if entry is None:
            entry = E.SubElement(font_table, f"{{{W}}}font", {f"{{{W}}}name": family})
        E.SubElement(entry, f"{{{W}}}{role}", {
            f"{{{R}}}id": f"rIdHandoutFont{index}",
            f"{{{W}}}fontKey": "{" + str(key).upper() + "}",
            f"{{{W}}}subsetted": embedded,
        })
        E.SubElement(rels, f"{{{PKG}}}Relationship", Id=f"rIdHandoutFont{index}", Type=R + "/font", Target=target)

    settings = E.fromstring(files["word/settings.xml"])
    for name in ("embedTrueTypeFonts", "saveSubsetFonts"):
        node = settings.find(f"{{{W}}}{name}")
        if node is None:
            node = E.SubElement(settings, f"{{{W}}}{name}")
        node.set(f"{{{W}}}val", "true")
    content_types = E.fromstring(files["[Content_Types].xml"])
    if not any(node.get("Extension") == "odttf" for node in content_types):
        E.SubElement(content_types, f"{{{CT}}}Default", Extension="odttf",
                     ContentType="application/vnd.openxmlformats-officedocument.obfuscatedFont")
    files["word/fontTable.xml"] = E.tostring(font_table, encoding="UTF-8", xml_declaration=True, standalone=True)
    files["word/_rels/fontTable.xml.rels"] = E.tostring(rels, encoding="UTF-8", xml_declaration=True, standalone=True)
    files["word/settings.xml"] = E.tostring(settings, encoding="UTF-8", xml_declaration=True, standalone=True)
    files["[Content_Types].xml"] = E.tostring(content_types, encoding="UTF-8", xml_declaration=True, standalone=True)
    with ZipFile(args.docx, "w", ZIP_DEFLATED) as z:
        for name, value in files.items():
            z.writestr(name, value)
    print(f"embedded {len(args.font)} font(s) in {args.docx.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
