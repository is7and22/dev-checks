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
手冊：不適用（沒有使用者手冊）

## 最容易漏的地方

- 某件事
"""

# 範圍含後端、內文提到新欄位，缺「舊版 app 相容：」
BACKEND_NEW_FIELD = COMPLETE + """
範圍：後端加欄位
回應多一個新欄位
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

    def test_bom_on_first_line_is_ignored(self):
        text = "\ufeff實際路徑：無\n寫入端：無\n驗收分派：自驗\n手冊：無\n最容易漏：無\n"
        code, out = run([self.write("bom.md", text)])
        self.assertEqual(code, 0, out)

    def test_non_utf8_fails_with_message(self):
        path = os.path.join(self.dir, "big5.md")
        with open(path, "wb") as f:
            f.write("實際路徑：無".encode("big5"))
        code, out = run([path])
        self.assertEqual(code, 1)
        self.assertIn("不是 UTF-8", out)

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


    # 以下是 2026-11-23 起的新三項

    def test_new_labels_are_required(self):
        # 程式裡拿掉「手冊：」或「最容易漏」的檢查，對應子測試會紅
        cases = {
            "手冊：": COMPLETE.replace("手冊：不適用（沒有使用者手冊）\n", ""),
            "最容易漏": COMPLETE.replace("## 最容易漏的地方\n", ""),
        }
        for label, text in cases.items():
            with self.subTest(label=label):
                path = self.write("2026-11-23-缺{}.md".format(label.rstrip("：")), text)
                code, out = run([path])
                self.assertEqual(code, 1)
                self.assertIn("缺 「{}」".format(label), out)
                self.assertIn(path, out)
                self.assertIn(ticket_format.NEW_REASONS[label], out)

    def test_manual_label_fixed_passes(self):
        text = COMPLETE.replace("手冊：不適用（沒有使用者手冊）\n", "")
        self.assertEqual(run([self.write("2026-11-23-a.md", text)])[0], 1)
        text += "手冊：不適用（沒有使用者手冊）\n"
        code, out = run([self.write("2026-11-23-a.md", text)])
        self.assertEqual(code, 0, out)

    def test_manual_halfwidth_colon_does_not_count(self):
        text = COMPLETE.replace("手冊：", "手冊:")
        code, out = run([self.write("2026-11-23-half.md", text)])
        self.assertEqual(code, 1)
        self.assertIn("「手冊：」", out)

    def test_manual_without_value_does_not_count(self):
        text = COMPLETE.replace("手冊：不適用（沒有使用者手冊）", "手冊：")
        code, out = run([self.write("2026-11-23-empty.md", text)])
        self.assertEqual(code, 1)
        self.assertIn("「手冊：」", out)

    def test_easy_to_miss_forms(self):
        base = COMPLETE.replace("## 最容易漏的地方\n", "")
        ok = ("## 最容易漏的地方", "# 最容易漏", "最容易漏：日期門檻", "  ### 最容易漏的", "## 最容易漏：寫反")
        for line in ok:
            with self.subTest(line=line):
                code, out = run([self.write("2026-11-23-ok.md", base + line + "\n")])
                self.assertEqual(code, 0, out)
        bad = ("最容易漏：", "## 最容易漏：  ", "最容易漏:日期", "要寫最容易漏的地方", "## 注意最容易漏")
        for line in bad:
            with self.subTest(line=line):
                code, out = run([self.write("2026-11-23-bad.md", base + line + "\n")])
                self.assertEqual(code, 1, line)
                self.assertIn("「最容易漏」", out)

    def test_old_app_required_for_backend_response_change(self):
        path = self.write("2026-11-23-後端.md", BACKEND_NEW_FIELD)
        code, out = run([path])
        self.assertEqual(code, 1)
        self.assertIn("缺 「舊版 app 相容：」", out)
        self.assertIn(ticket_format.NEW_REASONS["舊版 app 相容："], out)

        fixed = BACKEND_NEW_FIELD + "舊版 app 相容：舊 app 忽略多的欄位\n"
        code, out = run([self.write("2026-11-23-後端.md", fixed)])
        self.assertEqual(code, 0, out)

    def test_old_app_trigger_words(self):
        for word in ("OpenAPI", "回傳", "新欄位"):
            with self.subTest(word=word):
                text = COMPLETE + "範圍：backend\n改" + word + "\n"
                self.assertEqual(run([self.write("2026-11-23-w.md", text)])[0], 1)

    def test_old_app_backend_word_is_case_insensitive(self):
        text = BACKEND_NEW_FIELD.replace("範圍：後端加欄位", "範圍：Backend 加欄位")
        self.assertEqual(run([self.write("2026-11-23-c.md", text)])[0], 1)

    def test_old_app_not_required_for_frontend_only(self):
        text = BACKEND_NEW_FIELD.replace("範圍：後端加欄位", "範圍：frontend")
        code, out = run([self.write("2026-11-23-前端.md", text)])
        self.assertEqual(code, 0, out)

    def test_old_app_backend_only_judged_on_scope_line(self):
        # 範圍只有前端，內文別處提到後端與新欄位：不要求
        text = BACKEND_NEW_FIELD.replace("範圍：後端加欄位", "範圍：frontend\n後端那邊已經有這個新欄位")
        code, out = run([self.write("2026-11-23-前端提後端.md", text)])
        self.assertEqual(code, 0, out)

    def test_old_app_not_required_without_response_words(self):
        text = COMPLETE + "範圍：後端改排程\n"
        code, out = run([self.write("2026-11-23-排程.md", text)])
        self.assertEqual(code, 0, out)

    def test_date_threshold(self):
        # 缺新三項的單：11-22 通過（舊單不被新規則弄紅），改名 11-23 就失敗
        text = BACKEND_NEW_FIELD.replace("手冊：不適用（沒有使用者手冊）\n", "").replace(
            "## 最容易漏的地方\n", ""
        )
        code, out = run([self.write("2026-11-22-舊單.md", text)])
        self.assertEqual(code, 0, out)

        code, out = run([self.write("2026-11-23-舊單.md", text)])
        self.assertEqual(code, 1)
        self.assertIn("「最容易漏」、「手冊：」、「舊版 app 相容：」", out)

        code, out = run([self.write("2026-12-01-新單.md", text)])
        self.assertEqual(code, 1)
        code, out = run([self.write("2025-12-31-舊單.md", text)])
        self.assertEqual(code, 0, out)

    def test_old_ticket_still_needs_original_labels(self):
        code, out = run([self.write("2026-11-22-缺.md", "# 只有標題\n")])
        self.assertEqual(code, 1)
        self.assertIn("缺 「實際路徑：」、「寫入端：」、「驗收分派：」\n", out)

    def test_undated_filename_uses_new_rules(self):
        text = COMPLETE.replace("手冊：不適用（沒有使用者手冊）\n", "")
        code, out = run([self.write("no-date.md", text)])
        self.assertEqual(code, 1)
        self.assertIn("「手冊：」", out)

    def test_date_in_directory_name_is_ignored(self):
        # 只看檔名，不看目錄
        text = COMPLETE.replace("手冊：不適用（沒有使用者手冊）\n", "")
        os.makedirs(os.path.join(self.dir, "2026-11-01-x"))
        code, out = run([self.write(os.path.join("2026-11-01-x", "單.md"), text)])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
