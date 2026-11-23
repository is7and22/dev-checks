"""ticket-format：派工單要有的幾項。

pre-commit 只把 `docs/tasks/` 下的 `.md`（`README.md` 除外）傳進來，
限定寫在 `.pre-commit-hooks.yaml` 的 `files`／`exclude`。

- 所有單：「實際路徑：」「寫入端：」「驗收分派：」
- 檔名日期 >= NEW_RULES_FROM 的單（檔名沒有日期的也算）再加：
  「最容易漏」、「手冊：」，以及範圍含後端且動到回傳時的「舊版 app 相容：」
"""

import argparse
import os
import re
import sys

# 檔名開頭 yyyy-mm-dd-。零補位的日期字串比大小就是比日期，故意用字串比，不轉成別的型別
NEW_RULES_FROM = "2026-11-23"
FILENAME_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")

# 標籤用全形冒號「：」。半形的「:」不算。
REQUIRED_LABELS = (
    ("實際路徑：", "寫明使用者實際走哪條路（哪個畫面、哪個入口）；沒寫的話，測試可能驗的是一條沒人走的路"),
    ("寫入端：", "寫明新資料由誰寫入；只有讀取端沒有寫入端時，測試照樣全綠，正式環境卻走不到"),
    ("驗收分派：", "寫明每條驗收由誰、在哪裡驗；沒寫的話，兩邊都可能以為對方驗過了"),
)

EASY_TO_MISS = "最容易漏"
MANUAL = "手冊："
OLD_APP = "舊版 app 相容："

NEW_REASONS = {
    EASY_TO_MISS: "寫一段「## 最容易漏的地方」或一行「最容易漏：」，連同症狀；接手的人最常栽在沒人提醒的地方",
    MANUAL: "寫明使用者手冊要不要改、改哪篇；沒寫的話，功能上線了手冊還是舊的",
    OLD_APP: "範圍含後端又動到回傳或 OpenAPI 時，寫明還沒更新的舊版 app 收到新回應會怎樣；沒寫的話，舊 app 可能在正式環境壞掉",
}

BACKEND_WORDS = ("backend", "後端")
# 「範圍：」行前面可能有引用、清單、標題的記號，判斷前去掉
SCOPE_PREFIX = re.compile(r"^(?:\s|>|[-*](?=\s)|#)+")
RESPONSE_WORDS = ("OpenAPI", "回傳", "新欄位")


def _lines(text):
    for line in text.splitlines():
        yield line.lstrip().lstrip("\ufeff")


def _has_label(text, label):
    return any(s.startswith(label) and s[len(label):].strip() for s in _lines(text))


def _has_easy_to_miss(text):
    for s in _lines(text):
        s = s.lstrip("#").strip()
        if not s.startswith(EASY_TO_MISS) or s.startswith(EASY_TO_MISS + ":"):
            # 半形冒號跟其他標籤一樣不算
            continue
        if s.startswith(EASY_TO_MISS + "："):
            if s[len(EASY_TO_MISS) + 1:].strip():
                return True
        else:
            return True
    return False


def _needs_old_app(text):
    """只看以「範圍：」開頭的那一行判斷後端，不看全文。行首的 `>`、`- `、`* `、`#` 不算。"""
    backend = any(
        SCOPE_PREFIX.sub("", s).startswith("範圍：")
        and any(w in s.lower() for w in BACKEND_WORDS)
        for s in _lines(text)
    )
    return backend and any(w in text for w in RESPONSE_WORDS)


def new_rules_apply(filename):
    m = FILENAME_DATE.match(os.path.basename(filename))
    return m is None or m.group(1) >= NEW_RULES_FROM


def missing_labels(text, new_rules=True):
    """回傳 text 裡缺的項目。標籤要在行首（可有前導空白），且後面有值。"""
    missing = [label for label, _ in REQUIRED_LABELS if not _has_label(text, label)]
    if new_rules:
        if not _has_easy_to_miss(text):
            missing.append(EASY_TO_MISS)
        if not _has_label(text, MANUAL):
            missing.append(MANUAL)
        if _needs_old_app(text) and not _has_label(text, OLD_APP):
            missing.append(OLD_APP)
    return missing


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ticket-format",
        description="檢查派工單有沒有「實際路徑：」「寫入端：」「驗收分派：」"
        "「最容易漏」「手冊：」，範圍含後端又動到回傳時還要「舊版 app 相容：」。",
    )
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)

    reasons = dict(REQUIRED_LABELS, **NEW_REASONS)
    failed = False
    for filename in args.filenames:
        if os.path.basename(filename) == "README.md":
            continue
        try:
            with open(filename, encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            failed = True
            print("{}: 不是 UTF-8，讀不了".format(filename))
            continue
        missing = missing_labels(text, new_rules_apply(filename))
        if not missing:
            continue
        failed = True
        print("{}: 缺 {}".format(filename, "、".join("「{}」".format(m) for m in missing)))
        for label in missing:
            print("  {} {}".format(label, reasons[label]))
    if failed:
        print("每行寫在行首、用全形冒號「：」。不適用時寫「不適用（理由）」。")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
