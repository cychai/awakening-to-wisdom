#!/usr/bin/env python3
"""Verify that proofreading output preserves every non-layout source character."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

import fitz

from book_tools import canonical_text, markdown_visible_text, strip_audit_blocks
from proofread_books import PAGE_MARKER, native_lines, ocr_lines
from proofreading import apply_confirmed_corrections, normalize_spacing


def page_chunks(book_dir: pathlib.Path) -> dict[int, str]:
    result = {}
    for path in sorted(book_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        matches = list(PAGE_MARKER.finditer(content))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            result[int(match.group(1))] = content[match.end():end]
    return result


def visible_source(text: str) -> str:
    return canonical_text(markdown_visible_text(strip_audit_blocks(text)))


def expected_page(lines) -> str:
    page_text = "".join(line.text for line in lines)
    return canonical_text(apply_confirmed_corrections(normalize_spacing(page_text)))


def first_difference(left: str, right: str) -> dict | None:
    for index, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return {
                "index": index,
                "expected": left[max(0, index - 25):index + 25],
                "actual": right[max(0, index - 25):index + 25],
            }
    if len(left) != len(right):
        index = min(len(left), len(right))
        return {
            "index": index,
            "expected": left[max(0, index - 25):index + 25],
            "actual": right[max(0, index - 25):index + 25],
        }
    return None


def verify(repo: pathlib.Path, pdf_dir: pathlib.Path) -> dict:
    report = {"ok": True, "books": [], "failures": []}
    rapid = None
    for book in range(1, 6):
        doc = fitz.open(pdf_dir / f"{book}.pdf")
        chunks = page_chunks(repo / "docs" / f"book-{book}")
        if book == 3:
            from rapidocr_onnxruntime import RapidOCR
            rapid = rapid or RapidOCR()
        matched = 0
        for index, page in enumerate(doc, 1):
            lines = ocr_lines(page, rapid) if book == 3 else native_lines(page)
            expected = expected_page(lines)
            actual = visible_source(chunks.get(index, ""))
            difference = first_difference(expected, actual)
            if difference:
                report["ok"] = False
                report["failures"].append(
                    {"book": book, "page": index, "difference": difference}
                )
            else:
                matched += 1
        report["books"].append(
            {"book": book, "pages": len(doc), "character_exact_pages": matched}
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--pdf-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    report = verify(args.repo.resolve(), args.pdf_dir.resolve())
    build = args.repo / "build"
    build.mkdir(exist_ok=True)
    (build / "proofreading-verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
