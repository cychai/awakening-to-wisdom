#!/usr/bin/env python3
"""Reflow the five volumes conservatively from their original page geometry."""

from __future__ import annotations

import argparse
import difflib
import json
import pathlib
import re
import statistics
import sys
from collections import Counter

import fitz

from proofreading import (
    LayoutLine,
    apply_confirmed_corrections,
    group_layout_lines,
    group_semantic_lines,
    join_across_page_markers,
    normalize_spacing,
)


PAGE_MARKER = re.compile(r"<!-- 原书第 (\d+) 页 -->")
HEADING = re.compile(r"^(#{1,6})\s+(.+)$")
AUDIT_START = "<!-- source-image-start -->"
AUDIT_END = "<!-- source-image-end -->"
NOISE = {"更多", "kr66e9gs", "更多kr66e9gs"}


def canonical(text: str) -> str:
    return re.sub(r"\s+", "", text)


def existing_page_metadata(book_dir: pathlib.Path) -> dict[int, dict]:
    pages: dict[int, dict] = {}
    for path in sorted(book_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        matches = list(PAGE_MARKER.finditer(content))
        for index, match in enumerate(matches):
            page = int(match.group(1))
            end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            chunk = content[match.end():end]
            headings = []
            for line in chunk.splitlines():
                heading = HEADING.match(line.strip())
                if heading:
                    headings.append((len(heading.group(1)), heading.group(2).strip()))
            audit = ""
            if AUDIT_START in chunk and AUDIT_END in chunk:
                audit = (
                    chunk[chunk.index(AUDIT_START):chunk.index(AUDIT_END) + len(AUDIT_END)]
                    .strip()
                )
            pages[page] = {"file": path, "headings": headings, "audit": audit}
    return pages


def line_text(raw_line: dict) -> str:
    return "".join(span["text"] for span in raw_line["spans"]).strip()


def native_lines(page: fitz.Page) -> list[LayoutLine]:
    lines = []
    for block in page.get_text("dict")["blocks"]:
        for raw in block.get("lines", []):
            text = line_text(raw)
            x0, y0, _, y1 = raw["bbox"]
            if not text or canonical(text) in NOISE:
                continue
            if y0 > page.rect.height * 0.88 and re.fullmatch(r"[—\-]?\d+[—\-]?", text):
                continue
            lines.append(LayoutLine(text, x0, y0, y1))
    return sorted(lines, key=lambda line: (line.y0, line.x0))


def ocr_lines(page: fitz.Page, engine) -> list[LayoutLine]:
    import numpy as np

    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    result, _ = engine(image)
    lines = []
    for box, text, score in result or []:
        text = text.strip()
        x0 = min(point[0] for point in box)
        y0 = min(point[1] for point in box)
        y1 = max(point[1] for point in box)
        if not text or canonical(text) in NOISE or score < 0.50:
            continue
        if y0 > pix.height * 0.90 and re.fullmatch(r"\d+", text):
            continue
        lines.append(LayoutLine(text, x0, y0, y1))
    return sorted(lines, key=lambda line: (line.y0, line.x0))


def estimate_base_x(lines: list[LayoutLine], headings: list[tuple[int, str]]) -> float:
    heading_keys = {canonical(title) for _, title in headings}
    body = [line.x0 for line in lines if canonical(line.text) not in heading_keys]
    if not body:
        return min((line.x0 for line in lines), default=0.0)
    rounded = Counter(round(value / 2) * 2 for value in body)
    return float(rounded.most_common(1)[0][0])


def render_page(
    book: int,
    page_number: int,
    lines: list[LayoutLine],
    metadata: dict,
    front_matter: bool,
) -> str:
    headings = metadata["headings"]
    heading_by_key = {canonical(title): (level, title) for level, title in headings}
    base_x = estimate_base_x(lines, headings)
    indent = 18.0 if book in {1, 2, 5} else 14.0
    output = [f"<!-- 原书第 {page_number} 页 -->"]
    pending: list[LayoutLine] = []

    def flush() -> None:
        if not pending:
            return
        if front_matter:
            paragraphs = [apply_confirmed_corrections(normalize_spacing(line.text)) for line in pending]
        elif book == 3:
            paragraphs = group_semantic_lines(pending)
        else:
            paragraphs = group_layout_lines(pending, base_x=base_x, indent_threshold=indent)
        output.extend(apply_confirmed_corrections(paragraph) for paragraph in paragraphs)
        pending.clear()

    for line in lines:
        key = canonical(apply_confirmed_corrections(normalize_spacing(line.text)))
        if key in heading_by_key:
            flush()
            level, title = heading_by_key[key]
            output.append(
                f"{'#' * level} {apply_confirmed_corrections(normalize_spacing(title))}"
            )
        else:
            pending.append(line)
    flush()
    if metadata["audit"]:
        output.append(metadata["audit"])
    return "\n\n".join(part for part in output if part.strip()).rstrip() + "\n"


def diff_record(before: str, after: str, book: int, page: int, path: pathlib.Path) -> dict | None:
    if before == after:
        return None
    matcher = difflib.SequenceMatcher(a=before, b=after)
    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            changes.append({"type": tag, "before": before[i1:i2], "after": after[j1:j2]})
    return {"book": book, "page": page, "file": str(path), "changes": changes}


def original_page_body(path: pathlib.Path, page: int) -> str:
    content = path.read_text(encoding="utf-8")
    marker = f"<!-- 原书第 {page} 页 -->"
    start = content.index(marker) + len(marker)
    match = PAGE_MARKER.search(content, start)
    chunk = content[start:match.start() if match else len(content)]
    if AUDIT_START in chunk:
        chunk = chunk[:chunk.index(AUDIT_START)]
    return chunk.strip()


def proofread_book(book: int, pdf: pathlib.Path, docs: pathlib.Path) -> list[dict]:
    book_dir = docs / f"book-{book}"
    metadata = existing_page_metadata(book_dir)
    originals = {page: original_page_body(data["file"], page) for page, data in metadata.items()}
    doc = fitz.open(pdf)
    engine = None
    if book == 3:
        from rapidocr_onnxruntime import RapidOCR
        engine = RapidOCR()
    rendered: dict[int, str] = {}
    records = []
    for page_number, page in enumerate(doc, 1):
        data = metadata[page_number]
        lines = ocr_lines(page, engine) if engine else native_lines(page)
        front_matter = data["file"].stem == "00"
        rendered[page_number] = render_page(book, page_number, lines, data, front_matter)
        record = diff_record(originals[page_number], rendered[page_number], book, page_number, data["file"])
        if record:
            records.append(record)
        print(f"校订第 {book} 册：{page_number}/{len(doc)}", flush=True)

    by_file: dict[pathlib.Path, list[int]] = {}
    for page, data in metadata.items():
        by_file.setdefault(data["file"], []).append(page)
    for path, pages in by_file.items():
        content = "\n".join(rendered[page].rstrip() for page in sorted(pages)) + "\n"
        path.write_text(join_across_page_markers(content), encoding="utf-8")
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", type=pathlib.Path, required=True)
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--books", nargs="*", type=int, default=[1, 2, 3, 4, 5])
    args = parser.parse_args()
    build = args.repo / "build"
    build.mkdir(exist_ok=True)
    all_records = []
    for book in args.books:
        records = proofread_book(book, args.pdf_dir / f"{book}.pdf", args.repo / "docs")
        (build / f"proofreading-book-{book}.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        all_records.extend(records)
    (build / "proofreading-report.json").write_text(
        json.dumps(all_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
