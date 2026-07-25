import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "book_tools.py"


def load_module():
    if not MODULE_PATH.exists():
        raise AssertionError("tools/book_tools.py does not exist yet")
    spec = importlib.util.spec_from_file_location("book_tools", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BookToolsTest(unittest.TestCase):
    def test_canonical_text_ignores_layout_whitespace_only(self):
        tools = load_module()
        self.assertEqual(
            tools.canonical_text("醒与悟\n开悟、开窍、开智"),
            "醒与悟开悟、开窍、开智",
        )

    def test_markdown_heading_preserves_original_visible_text(self):
        tools = load_module()
        original = "第一部分 开窍篇"
        markdown = tools.as_heading(original, 1)
        self.assertEqual(markdown, "# 第一部分 开窍篇")
        self.assertEqual(tools.markdown_visible_text(markdown), original)

    def test_markdown_image_does_not_count_as_source_text(self):
        tools = load_module()
        markdown = "正文\n\n![原书第 1 页](../.gitbook/assets/book-3/page-001.png)"
        self.assertEqual(tools.markdown_visible_text(markdown), "正文")

    def test_top_level_ranges_keep_front_matter_and_order(self):
        tools = load_module()
        toc = [(1, "第一部分", 4), (2, "第一节", 4), (1, "第二部分", 10)]
        self.assertEqual(
            tools.top_level_ranges(toc, page_count=15),
            [
                ("原书前置内容", 1, 3),
                ("第一部分", 4, 9),
                ("第二部分", 10, 15),
            ],
        )

    def test_format_page_marks_existing_title_without_changing_text(self):
        tools = load_module()
        source = "第一部分\n这是第一段。\n这是第二段。"
        markdown = tools.format_page_text(source, [(1, "第一部分")])
        self.assertTrue(markdown.startswith("# 第一部分\n"))
        self.assertEqual(
            tools.canonical_text(tools.markdown_visible_text(markdown)),
            tools.canonical_text(source),
        )

    def test_strip_audit_blocks_removes_non_source_image_ui(self):
        tools = load_module()
        markdown = "正文\n<!-- source-image-start -->\n<details>影像</details>\n<!-- source-image-end -->\n结尾"
        self.assertEqual(tools.strip_audit_blocks(markdown), "正文\n\n结尾")

    def test_markdown_visible_text_removes_inline_page_comment(self):
        tools = load_module()
        markdown = "前半句<!-- 原书第 2 页 -->后半句。"
        self.assertEqual(tools.markdown_visible_text(markdown), "前半句后半句。")


if __name__ == "__main__":
    unittest.main()
