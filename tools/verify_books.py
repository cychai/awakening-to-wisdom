#!/usr/bin/env python3
"""Verify text fidelity, page coverage, navigation, and image references."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

from book_tools import canonical_text, markdown_visible_text, strip_audit_blocks


PAGE_MARKER = re.compile(r"^===== 第 \d+ 页 =====$", re.MULTILINE)
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def first_difference(left: str, right: str) -> dict | None:
    for index, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return {
                "index": index,
                "source": left[max(0, index - 30):index + 30],
                "gitbook": right[max(0, index - 30):index + 30],
            }
    if len(left) != len(right):
        index = min(len(left), len(right))
        return {
            "index": index,
            "source": left[max(0, index - 30):index + 30],
            "gitbook": right[max(0, index - 30):index + 30],
        }
    return None


def verify(repo: pathlib.Path) -> dict:
    audit = json.loads((repo / "build" / "audit.json").read_text(encoding="utf-8"))
    result = {"books": [], "missing_links": [], "ok": True}
    docs = repo / "docs"
    for report in audit:
        book = report["book"]
        source = (repo / "source-text" / f"book-{book}.txt").read_text(encoding="utf-8")
        source = PAGE_MARKER.sub("", source)
        markdown_parts = []
        page_markers = 0
        for section in report["sections"]:
            content = (docs / section["file"]).read_text(encoding="utf-8")
            page_markers += content.count("<!-- 原书第 ")
            markdown_parts.append(strip_audit_blocks(content))
        visible = markdown_visible_text("\n".join(markdown_parts))
        source_canonical = canonical_text(source)
        gitbook_canonical = canonical_text(visible)
        difference = first_difference(source_canonical, gitbook_canonical)
        book_result = {
            "book": book,
            "pages_expected": report["pages"],
            "pages_found": page_markers,
            "source_characters": len(source_canonical),
            "gitbook_characters": len(gitbook_canonical),
            "text_equal": difference is None,
            "first_difference": difference,
        }
        if report["scanned"]:
            assets = list((docs / ".gitbook" / "assets" / f"book-{book}").glob("page-*"))
            book_result["page_images"] = len(assets)
            if len(assets) != report["pages"]:
                result["ok"] = False
        if difference is not None or page_markers != report["pages"]:
            result["ok"] = False
        result["books"].append(book_result)

    for markdown_file in docs.rglob("*.md"):
        content = markdown_file.read_text(encoding="utf-8")
        for target in MARKDOWN_LINK.findall(content):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = (markdown_file.parent / target.split("#", 1)[0]).resolve()
            if not path.exists():
                result["missing_links"].append(
                    {"file": str(markdown_file.relative_to(repo)), "target": target}
                )
                result["ok"] = False
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path.cwd())
    args = parser.parse_args()
    result = verify(args.repo.resolve())
    build = args.repo / "build"
    build.mkdir(exist_ok=True)
    (build / "verification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
