"""Shared, deterministic helpers for the PDF-to-GitBook conversion."""

from __future__ import annotations

import re
from typing import Iterable, Sequence


IMAGE_LINE = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$")
HEADING_PREFIX = re.compile(r"^\s{0,3}#{1,6}\s+")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
AUDIT_BLOCK = re.compile(
    r"<!-- source-image-start -->.*?<!-- source-image-end -->", re.DOTALL
)


def canonical_text(text: str) -> str:
    """Remove layout whitespace while retaining every visible character."""
    return re.sub(r"\s+", "", text)


def as_heading(text: str, level: int) -> str:
    """Add Markdown heading syntax without changing the supplied title."""
    if level < 1 or level > 6:
        raise ValueError("heading level must be between 1 and 6")
    return f"{'#' * level} {text}"


def markdown_visible_text(markdown: str) -> str:
    """Return source-visible text after removing conversion-only Markdown."""
    markdown = HTML_COMMENT.sub("", markdown)
    visible = []
    for line in markdown.splitlines():
        if IMAGE_LINE.match(line):
            continue
        if line.lstrip().startswith("<!--"):
            continue
        line = HEADING_PREFIX.sub("", line)
        if line.strip():
            visible.append(line.strip())
    return "\n".join(visible)


def strip_audit_blocks(markdown: str) -> str:
    """Remove conversion-only original-page image controls."""
    return AUDIT_BLOCK.sub("", markdown)


def top_level_ranges(
    toc: Sequence[Sequence[object]], page_count: int
) -> list[tuple[str, int, int]]:
    """Convert PDF TOC entries into inclusive 1-based top-level page ranges."""
    starts = [(str(title), int(page)) for level, title, page in toc if int(level) == 1]
    ranges: list[tuple[str, int, int]] = []
    if not starts:
        return [("原书内容", 1, page_count)]
    if starts[0][1] > 1:
        ranges.append(("原书前置内容", 1, starts[0][1] - 1))
    for index, (title, start) in enumerate(starts):
        end = starts[index + 1][1] - 1 if index + 1 < len(starts) else page_count
        ranges.append((title, start, end))
    return ranges


def toc_titles_on_page(
    toc: Iterable[Sequence[object]], page_number: int
) -> list[tuple[int, str]]:
    """Return ordered heading levels/titles whose destination is a page."""
    return [
        (int(level), str(title).strip())
        for level, title, page in toc
        if int(page) == page_number and str(title).strip()
    ]


def format_page_text(text: str, headings: Sequence[tuple[int, str]]) -> str:
    """Apply heading markup to matching source lines without rewriting text."""
    remaining = list(headings)
    output: list[str] = []
    for source_line in text.splitlines():
        line = source_line.strip()
        if not line:
            if output and output[-1] != "":
                output.append("")
            continue
        match_index = next(
            (
                index
                for index, (_, title) in enumerate(remaining)
                if canonical_text(title) == canonical_text(line)
            ),
            None,
        )
        if match_index is None:
            output.append(line)
            continue
        level, _ = remaining.pop(match_index)
        output.extend([as_heading(line, min(level, 6)), ""])
    while output and output[-1] == "":
        output.pop()
    return "\n".join(output)
