import contextlib
import io
import os
import tempfile
import unittest

from checks import ticket_format

COMPLETE = """# 某張單

實際路徑：不適用（沒有使用者畫面）
寫入端：不適用（沒有資料）
驗收分派：執行者自驗
"""


def run(paths):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = ticket_format.main(paths)
    return code, out.getvalue()


class TicketFormatTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_complete_ticket_passes(self):
        code, out = run([self.write("ok.md", COMPLETE)])
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "")

    def test_each_label_is_required(self):
        # 三個標籤逐一拿掉，各自要紅並點名。程式裡拿掉任何一個標籤，這裡對應的子測試會紅
        for label in ("實際路徑：", "寫入端：", "驗收分派："):
            with self.subTest(label=label):
                text = "\n".join(
                    line for line in COMPLETE.splitlines() if not line.startswith(label)
                )
                path = self.write("missing.md", text)
                code, out = run([path])
                self.assertNotEqual(code, 0)
                self.assertIn("「{}」".format(label), out)
                self.assertIn(path, out)

    def test_missing_acceptance_dispatch_names_it(self):
        text = COMPLETE.replace("驗收分派：執行者自驗\n", "")
        code, out = run([self.write("no-dispatch.md", text)])
        self.assertEqual(code, 1)
        self.assertIn("缺 「驗收分派：」", out)
        self.assertNotIn("「實際路徑：」", out)
        self.assertNotIn("「寫入端：」", out)

    def test_halfwidth_colon_does_not_count(self):
        text = COMPLETE.replace("寫入端：", "寫入端:")
        code, out = run([self.write("halfwidth.md", text)])
        self.assertEqual(code, 1)
        self.assertIn("「寫入端：」", out)

    def test_label_must_start_the_line(self):
        text = COMPLETE.replace("驗收分派：執行者自驗", "要寫「驗收分派：」這行")
        code, out = run([self.write("inline.md", text)])
        self.assertEqual(code, 1)
        self.assertIn("「驗收分派：」", out)

    def test_label_without_value_does_not_count(self):
        text = COMPLETE.replace("實際路徑：不適用（沒有使用者畫面）", "實際路徑：  ")
        code, out = run([self.write("empty.md", text)])
        self.assertEqual(code, 1)
        self.assertIn("「實際路徑：」", out)

    def test_chinese_filename(self):
        bad = self.write("2026-11-19-中文單.md", "# 只有標題\n")
        code, out = run([bad])
        self.assertEqual(code, 1)
        self.assertIn("2026-11-19-中文單.md", out)
        self.assertIn("「實際路徑：」、「寫入端：」、「驗收分派：」", out)

        good = self.write("2026-11-19-完整單.md", COMPLETE)
        self.assertEqual(run([good])[0], 0)

    def test_readme_is_skipped(self):
        code, out = run([self.write("README.md", "# 單子目錄\n")])
        self.assertEqual(code, 0, out)

    def test_reports_every_failing_file(self):
        a = self.write("a.md", "# a\n")
        b = self.write("b.md", COMPLETE)
        c = self.write("c.md", "# c\n")
        code, out = run([a, b, c])
        self.assertEqual(code, 1)
        self.assertIn(a, out)
        self.assertIn(c, out)
        self.assertNotIn(b + ":", out)


if __name__ == "__main__":
    unittest.main()
