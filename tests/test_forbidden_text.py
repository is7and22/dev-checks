import contextlib
import io
import os
import tempfile
import unittest

from checks import forbidden_text


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = forbidden_text.main(argv)
    return code, out.getvalue()


class ForbiddenTextTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, data):
        path = os.path.join(self.dir, name)
        mode = "wb" if isinstance(data, bytes) else "w"
        kwargs = {} if isinstance(data, bytes) else {"encoding": "utf-8"}
        with open(path, mode, **kwargs) as f:
            f.write(data)
        return path

    def test_hit_prints_file_line_and_fails(self):
        path = self.write("a.md", "第一行\n這裡有 secret-repo/x\n第三行\n")
        code, out = run(["--pattern", "secret-repo/", path])
        self.assertEqual(code, 1)
        self.assertEqual(out, "{}:2: 這裡有 secret-repo/x\n".format(path))

    def test_no_hit_passes(self):
        path = self.write("a.md", "乾淨的內容\n")
        code, out = run(["--pattern", "secret-repo/", path])
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "")

    def test_no_pattern_is_a_config_error(self):
        # 設定漏了 --pattern 時不可以靜默通過，即使檔案裡什麼都沒有
        path = self.write("a.md", "乾淨的內容\n")
        code, out = run([path])
        self.assertNotEqual(code, 0)
        self.assertIn("--pattern", out)
        self.assertIn("設定錯誤", out)

    def test_no_pattern_fails_even_without_files(self):
        code, out = run([])
        self.assertNotEqual(code, 0)
        self.assertIn("設定錯誤", out)

    def test_empty_pattern_is_a_config_error(self):
        # 空字串會比中每一行，等於設定寫錯
        path = self.write("a.md", "內容\n")
        code, out = run(["--pattern", "", path])
        self.assertNotEqual(code, 0)
        self.assertIn("設定錯誤", out)

    def test_pattern_is_literal_not_regex(self):
        path = self.write("a.md", "a.c\nabc\n")
        code, out = run(["--pattern", "a.c", path])
        self.assertEqual(code, 1)
        self.assertIn(":1: a.c", out)
        self.assertNotIn(":2:", out)

        path2 = self.write("b.md", "連結 [[頁面]]\n")
        code, out = run(["--pattern", "[[", path2])
        self.assertEqual(code, 1)
        self.assertIn(":1: 連結 [[頁面]]", out)

    def test_multiple_patterns(self):
        path = self.write("a.md", "foo\nbar\nbaz\n")
        code, out = run(["--pattern", "foo", "--pattern=baz", path])
        self.assertEqual(code, 1)
        self.assertIn(":1: foo", out)
        self.assertIn(":3: baz", out)
        self.assertNotIn(":2:", out)

    def test_binary_file_is_skipped(self):
        path = self.write("a.png", b"\x89PNG\r\n\x00\x00secret-repo/\x00")
        code, out = run(["--pattern", "secret-repo/", path])
        self.assertEqual(code, 0, out)

    def test_chinese_filename_and_content(self):
        path = self.write("中文檔.md", "路徑是 內部庫/規則\n")
        code, out = run(["--pattern", "內部庫/", path])
        self.assertEqual(code, 1)
        self.assertIn("中文檔.md:1: 路徑是 內部庫/規則", out)


if __name__ == "__main__":
    unittest.main()
