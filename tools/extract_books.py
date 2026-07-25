#!/usr/bin/env python3
"""Extract the five supplied PDFs into a fidelity-audited GitBook tree."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

import fitz

from book_tools import format_page_text, toc_titles_on_page, top_level_ranges


BOOK4_PAGE_STARTS = [
    8, 10, 13, 15, 17, 19, 21, 24, 26, 28, 32, 35, 37, 38, 40, 42, 45,
    48, 51, 53, 55, 57, 59, 61, 62, 65, 67, 69, 73, 75, 79, 84, 88, 92,
    97, 101, 105, 109, 112, 115, 118, 120, 122, 124, 127, 131, 136, 139,
    141, 145, 149, 153, 156, 161, 165, 169, 175, 180, 183,
]
BOOK3_CHAPTERS = [
    ("原书目录", 1),
    ("第一章：打造被动收入，提前规划退休", 8),
    ("第二章：突破认知局限，屌丝逆天改命", 30),
    ("第三章：赚大钱的秘密", 50),
    ("第四章：穷人逆袭之路", 75),
    ("第五章：高手进阶之路", 102),
]


def clean_filename(index: int) -> str:
    return f"{index:02d}.md"


def source_blocks(page: fitz.Page) -> list[tuple[float, float, str]]:
    blocks = []
    for block in page.get_text("blocks"):
        _, y0, _, y1, text, *_ = block
        value = "".join(line.strip() for line in text.splitlines()).strip()
        if value and value not in {"更多", "kr66e9gs", "更多kr66e9gs"}:
            blocks.append((y0, y1, value))
    return blocks


def book4_ranges(doc: fitz.Document) -> tuple[list[tuple[str, int, int]], list[list[object]]]:
    starts = BOOK4_PAGE_STARTS
    entries = []
    toc = []
    if starts[0] > 1:
        entries.append(("原书前置内容", 1, starts[0] - 1))
    for index, start in enumerate(starts):
        blocks = source_blocks(doc[start - 1])
        title = blocks[0][2] if blocks else f"原书第 {start} 页"
        end = starts[index + 1] - 1 if index + 1 < len(starts) else len(doc)
        entries.append((title, start, end))
        toc.append([1, title, start])
    return entries, toc


def book3_ranges(page_count: int) -> tuple[list[tuple[str, int, int]], list[list[object]]]:
    ranges = []
    toc = []
    for index, (title, start) in enumerate(BOOK3_CHAPTERS):
        end = BOOK3_CHAPTERS[index + 1][1] - 1 if index + 1 < len(BOOK3_CHAPTERS) else page_count
        ranges.append((title, start, end))
        toc.append([1, title, start])
    return ranges, toc


def adjusted_toc(book: int, doc: fitz.Document) -> list[list[object]]:
    toc = [list(entry) for entry in doc.get_toc()]
    if book == 5:
        seen_third_part = False
        for entry in toc:
            if entry[1] == "第三部分 逆袭篇":
                seen_third_part = True
            elif seen_third_part and re.match(r"^第[一二三四]章", str(entry[1])):
                entry[0] = 2
    return toc


def ocr_pages(doc: fitz.Document) -> list[str]:
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR

    engine = RapidOCR()
    pages = []
    for index, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        result, _ = engine(image)
        lines = [text.strip() for _, text, score in (result or []) if text.strip() and score >= 0.50]
        pages.append("\n".join(lines))
        print(f"OCR 第 3 册：{index + 1}/{len(doc)}", flush=True)
    return pages


def extract_page_image(doc: fitz.Document, page_index: int, destination: pathlib.Path) -> pathlib.Path:
    page = doc[page_index]
    images = page.get_images(full=True)
    if images:
        largest = max(images, key=lambda image: image[2] * image[3])
        extracted = doc.extract_image(largest[0])
        output = destination.with_suffix(f".{extracted['ext']}")
        output.write_bytes(extracted["image"])
        return output
    output = destination.with_suffix(".png")
    page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).save(output)
    return output


def image_audit_block(book: int, page_number: int, image_name: str) -> str:
    return (
        "<!-- source-image-start -->\n"
        "<details>\n"
        f"<summary>查看原书第 {page_number} 页影像</summary>\n\n"
        f"![原书第 {page_number} 页](../.gitbook/assets/book-{book}/{image_name})\n\n"
        "</details>\n"
        "<!-- source-image-end -->"
    )


def write_book(
    book: int,
    pdf_path: pathlib.Path,
    docs_root: pathlib.Path,
    source_root: pathlib.Path,
) -> dict:
    doc = fitz.open(pdf_path)
    page_texts = ocr_pages(doc) if book == 3 else [page.get_text("text").strip() for page in doc]
    source_root.mkdir(parents=True, exist_ok=True)
    source_path = source_root / f"book-{book}.txt"
    source_path.write_text(
        "\n\n".join(
            f"===== 第 {index + 1} 页 =====\n{text}" for index, text in enumerate(page_texts)
        ) + "\n",
        encoding="utf-8",
    )

    if book == 3:
        ranges, toc = book3_ranges(len(doc))
    elif book == 4:
        ranges, toc = book4_ranges(doc)
    else:
        toc = adjusted_toc(book, doc)
        ranges = top_level_ranges(toc, len(doc))

    book_dir = docs_root / f"book-{book}"
    book_dir.mkdir(parents=True, exist_ok=True)
    asset_dir = docs_root / ".gitbook" / "assets" / f"book-{book}"
    asset_dir.mkdir(parents=True, exist_ok=True)
    scanned = book in {3, 4}
    page_images: dict[int, pathlib.Path] = {}
    if scanned:
        for page_index in range(len(doc)):
            image = extract_page_image(doc, page_index, asset_dir / f"page-{page_index + 1:03d}")
            page_images[page_index + 1] = image

    files = []
    for range_index, (label, start, end) in enumerate(ranges):
        filename = clean_filename(range_index)
        chunks = []
        for page_number in range(start, end + 1):
            chunks.append(f"<!-- 原书第 {page_number} 页 -->")
            headings = toc_titles_on_page(toc, page_number)
            text = format_page_text(page_texts[page_number - 1], headings)
            if text:
                chunks.append(text)
            if scanned:
                image = page_images[page_number]
                chunks.append(image_audit_block(book, page_number, image.name))
        (book_dir / filename).write_text("\n\n".join(chunks).rstrip() + "\n", encoding="utf-8")
        files.append({"label": label, "file": f"book-{book}/{filename}", "start": start, "end": end})

    return {
        "book": book,
        "pdf": str(pdf_path),
        "pages": len(doc),
        "characters": sum(len(text) for text in page_texts),
        "scanned": scanned,
        "sections": files,
        "source_text": str(source_path),
    }


def write_navigation(docs_root: pathlib.Path, reports: list[dict]) -> None:
    readme = (
        "# Awakening to Wisdom\n\n"
        "《醒与悟》，又名《开悟·开窍·开智》。\n\n"
        "全书共五册，正文依照原稿顺序整理，仅调整目录、标题层级、段落和页面导航。\n"
        "\n第三、四册为扫描版，正文页面末尾保留可展开的原页影像，作为原文校验基准。\n"
    )
    (docs_root / "README.md").write_text(readme, encoding="utf-8")
    lines = ["# Table of contents", "", "* [首页](README.md)"]
    for report in reports:
        lines.extend(["", f"## 第 {report['book']} 册", ""])
        for section in report["sections"]:
            lines.append(f"* [{section['label']}]({section['file']})")
    (docs_root / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", type=pathlib.Path, required=True)
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path.cwd())
    args = parser.parse_args()
    docs_root = args.repo / "docs"
    reports = []
    for book in range(1, 6):
        reports.append(write_book(book, args.pdf_dir / f"{book}.pdf", docs_root, args.repo / "source-text"))
    write_navigation(docs_root, reports)
    build = args.repo / "build"
    build.mkdir(exist_ok=True)
    (build / "audit.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
