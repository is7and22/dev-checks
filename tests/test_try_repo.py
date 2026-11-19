"""用 pre-commit 框架走一次真的路徑。

直接呼叫 script 驗不到 `.pre-commit-hooks.yaml` 的 `files` 寫錯：那時 hook
根本不會被呼叫，結果一律通過，不會有錯誤訊息。這裡在暫存 repo 裡讓框架
自己挑檔、自己傳參數。

本機沒有 pre-commit 時略過；CI 設 REQUIRE_PRE_COMMIT=1，沒有就失敗。
"""

import os
import shutil
import subprocess
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE_COMMIT = shutil.which("pre-commit")

COMPLETE = "# 單\n\n實際路徑：不適用（無）\n寫入端：不適用（無）\n驗收分派：自驗\n"

GIT_ENV = dict(
    {k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    GIT_AUTHOR_NAME="test",
    GIT_AUTHOR_EMAIL="test@example.invalid",
    GIT_COMMITTER_NAME="test",
    GIT_COMMITTER_EMAIL="test@example.invalid",
)


def git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "commit.gpgsign=false", *args], cwd=cwd, check=True, env=GIT_ENV,
        capture_output=True, text=True,
    ).stdout


def snapshot_repo(dest):
    """把本 repo 的工作區（含未提交、未追蹤的檔）提交成 dest 的一個 commit，回傳 rev。

    帶 args 要寫 config 指定 repo 與 rev，而 rev 必須是 commit；
    這樣測的是工作區現況，不是上一個 commit。
    """
    files = git(REPO_ROOT, "ls-files", "-co", "--exclude-standard").splitlines()
    git(dest, "init", "-q")
    for rel in files:
        src = os.path.join(REPO_ROOT, rel)
        if os.path.isfile(src):
            dst = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    git(dest, "add", "-A")
    git(dest, "commit", "-q", "-m", "snapshot")
    return git(dest, "rev-parse", "HEAD").strip()


@unittest.skipIf(
    PRE_COMMIT is None and not os.environ.get("REQUIRE_PRE_COMMIT"),
    "pre-commit 不在 PATH",
)
class PreCommitFrameworkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if PRE_COMMIT is None:
            raise AssertionError("REQUIRE_PRE_COMMIT=1 但 pre-commit 不在 PATH")
        cls._snap_tmp = tempfile.TemporaryDirectory()
        cls.snapshot = cls._snap_tmp.name
        cls.snapshot_rev = snapshot_repo(cls.snapshot)

    @classmethod
    def tearDownClass(cls):
        cls._snap_tmp.cleanup()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = self._tmp.name
        git(self.repo, "init", "-q")

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, text):
        path = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(path) or self.repo, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        git(self.repo, "add", rel)

    def pre_commit(self, *args):
        result = subprocess.run(
            [PRE_COMMIT, *args], cwd=self.repo, env=GIT_ENV,
            capture_output=True, text=True,
        )
        return result.returncode, result.stdout + result.stderr

    def test_ticket_format_try_repo_red_then_green(self):
        rel = "docs/tasks/2026-11-19-中文單.md"
        self.write(rel, COMPLETE.replace("驗收分派：自驗\n", ""))
        code, out = self.pre_commit("try-repo", self.snapshot, "ticket-format", "--files", rel)
        self.assertNotEqual(code, 0, out)
        self.assertIn("「驗收分派：」", out)

        self.write(rel, COMPLETE)
        code, out = self.pre_commit("try-repo", self.snapshot, "ticket-format", "--files", rel)
        self.assertEqual(code, 0, out)

    def test_ticket_format_files_scope(self):
        # 框架要把 docs/tasks/ 的單交給 hook；範圍外的檔不交。README 有 hook exclude 與程式兩層，這條只驗結果
        # 中文檔名走 git 列檔的路徑（git 預設把非 ASCII 印成八進位轉義）
        self.write("docs/tasks/中文缺行.md", "# 缺三行\n")
        self.write("docs/tasks/README.md", "# 目錄\n")
        self.write("docs/other/b.md", "# 範圍外\n")
        code, out = self.pre_commit("try-repo", self.snapshot, "ticket-format", "--all-files")
        self.assertNotEqual(code, 0, out)
        self.assertIn("docs/tasks/中文缺行.md", out)
        self.assertNotIn("README.md: 缺", out)
        self.assertNotIn("docs/other/b.md", out)

    def test_forbidden_text_try_repo_without_pattern_fails(self):
        # try-repo 不能帶 args，正好是「設定漏了 --pattern」的情形
        self.write("notes.md", "乾淨\n")
        code, out = self.pre_commit("try-repo", self.snapshot, "forbidden-text", "--files", "notes.md")
        self.assertNotEqual(code, 0, out)
        self.assertIn("設定錯誤", out)

    def test_forbidden_text_with_pattern_red_then_green(self):
        self.write(
            ".pre-commit-config.yaml",
            "repos:\n"
            "  - repo: {}\n"
            "    rev: {}\n"
            "    hooks:\n"
            "      - id: forbidden-text\n"
            "        args: [--pattern, \"secret-repo/\"]\n".format(
                self.snapshot, self.snapshot_rev
            ),
        )
        self.write("中文筆記.md", "第一行\n引用了 secret-repo/x\n")
        code, out = self.pre_commit("run", "--all-files")
        self.assertNotEqual(code, 0, out)
        self.assertIn("中文筆記.md:2: 引用了 secret-repo/x", out)
        # config 本身含 pattern 字面，不能被當成違規
        self.assertNotIn(".pre-commit-config.yaml:", out)

        self.write("中文筆記.md", "第一行\n乾淨\n")
        code, out = self.pre_commit("run", "--all-files")
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
