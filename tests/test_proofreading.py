import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "proofreading.py"


def load_module():
    if not MODULE_PATH.exists():
        raise AssertionError("tools/proofreading.py does not exist yet")
    spec = importlib.util.spec_from_file_location("proofreading", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProofreadingTest(unittest.TestCase):
    def test_removes_spaces_between_chinese_characters(self):
        p = load_module()
        self.assertEqual(p.normalize_spacing("帮 忙，价 值"), "帮忙，价值")

    def test_removes_spaces_around_chinese_punctuation(self):
        p = load_module()
        self.assertEqual(p.normalize_spacing("人情 。 其实， 很简单"), "人情。其实，很简单")

    def test_keeps_spaces_between_english_words(self):
        p = load_module()
        self.assertEqual(p.normalize_spacing("personal IP and AI"), "personal IP and AI")

    def test_normalizes_number_measure_word_spacing(self):
        p = load_module()
        self.assertEqual(p.normalize_spacing("2022 年 8 月 7 日"), "2022年8月7日")

    def test_normalizes_chinese_closing_parenthesis(self):
        p = load_module()
        self.assertEqual(p.normalize_spacing("也吸引不到值钱的人)"), "也吸引不到值钱的人）")

    def test_groups_layout_lines_using_indentation(self):
        p = load_module()
        lines = [
            p.LayoutLine("第一段开始，", 114, 145, 157),
            p.LayoutLine("这是第一段续行。", 90, 168, 180),
            p.LayoutLine("第二段开始，", 114, 215, 227),
            p.LayoutLine("这是第二段续行。", 90, 239, 251),
        ]
        self.assertEqual(
            p.group_layout_lines(lines, base_x=90, indent_threshold=12),
            ["第一段开始，这是第一段续行。", "第二段开始，这是第二段续行。"],
        )

    def test_groups_layout_lines_using_large_vertical_gap(self):
        p = load_module()
        lines = [
            p.LayoutLine("第一段。", 80, 100, 112),
            p.LayoutLine("第二段。", 80, 145, 157),
        ]
        self.assertEqual(
            p.group_layout_lines(lines, base_x=80, indent_threshold=12),
            ["第一段。", "第二段。"],
        )

    def test_keeps_numbered_items_separate(self):
        p = load_module()
        lines = [
            p.LayoutLine("1，第一项内容。", 104, 100, 116),
            p.LayoutLine("2，第二项内容。", 104, 130, 146),
        ]
        self.assertEqual(
            p.group_layout_lines(lines, base_x=72, indent_threshold=12),
            ["1，第一项内容。", "2，第二项内容。"],
        )

    def test_joins_sentence_across_page_marker(self):
        p = load_module()
        text = "这是一个连续句的前半部\n<!-- 原书第 16 页 -->\n\n分。"
        self.assertEqual(
            p.join_across_page_markers(text),
            "这是一个连续句的前半部<!-- 原书第 16 页 -->分。",
        )

    def test_semantic_grouping_joins_wrapped_lines(self):
        p = load_module()
        lines = [
            p.LayoutLine("答：房子现在价值400", 100, 100, 120),
            p.LayoutLine("万元。", 100, 150, 170),
            p.LayoutLine("结果呢？", 100, 200, 220),
        ]
        self.assertEqual(
            p.group_semantic_lines(lines),
            ["答：房子现在价值400万元。", "结果呢？"],
        )

    def test_applies_only_confirmed_ocr_corrections(self):
        p = load_module()
        source = "如果你能看明臼以后，别婖不知耻，也不要做婖狗。"
        self.assertEqual(
            p.apply_confirmed_corrections(source),
            "如果你能看明白以后，别恬不知耻，也不要做舔狗。",
        )

    def test_applies_confirmed_systematic_ocr_corrections(self):
        p = load_module()
        source = "他己经跪薛一群女生，追求内非肤，也把冷当成铝甲。"
        self.assertEqual(
            p.apply_confirmed_corrections(source),
            "他已经跪舔一群女生，追求内啡肽，也把冷当成铠甲。",
        )

    def test_repairs_confirmed_corrupt_pdf_glyphs(self):
        p = load_module()
        source = "他还说裸采禮鞏：6頒家子气，像扲整扇猪肉一样。"
        self.assertEqual(
            p.apply_confirmed_corrections(source),
            "他还说啰里啰嗦，一副小家子气，像拎整扇猪肉一样。",
        )


if __name__ == "__main__":
    unittest.main()
