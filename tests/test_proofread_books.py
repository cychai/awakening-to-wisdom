import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from proofread_books import render_page
from proofreading import LayoutLine


class ProofreadBooksTest(unittest.TestCase):
    def test_corrected_heading_remains_a_heading_on_rerun(self):
        lines = [LayoutLine("销甲的秘密", 100, 100, 120)]
        metadata = {
            "headings": [(1, "铠甲的秘密")],
            "audit": "",
        }

        rendered = render_page(4, 141, lines, metadata, front_matter=False)

        self.assertIn("# 铠甲的秘密", rendered)


if __name__ == "__main__":
    unittest.main()
