"""ticket-format：派工單要有三行開頭標籤。

pre-commit 只把 `docs/tasks/` 下的 `.md`（`README.md` 除外）傳進來，
限定寫在 `.pre-commit-hooks.yaml` 的 `files`／`exclude`。
"""

import argparse
import os
import sys

# 標籤用全形冒號「：」。半形的「:」不算。
REQUIRED_LABELS = (
    ("實際路徑：", "寫明使用者實際走哪條路（哪個畫面、哪個入口）；沒寫的話，測試可能驗的是一條沒人走的路"),
    ("寫入端：", "寫明新資料由誰寫入；只有讀取端沒有寫入端時，測試照樣全綠，正式環境卻走不到"),
    ("驗收分派：", "寫明每條驗收由誰、在哪裡驗；沒寫的話，兩邊都可能以為對方驗過了"),
)


def missing_labels(text):
    """回傳 text 裡缺的標籤。標籤要在行首（可有前導空白），且後面有值。"""
    found = set()
    for line in text.splitlines():
        stripped = line.lstrip()
        for label, _ in REQUIRED_LABELS:
            if stripped.startswith(label) and stripped[len(label):].strip():
                found.add(label)
    return [label for label, _ in REQUIRED_LABELS if label not in found]


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ticket-format",
        description="檢查派工單有沒有「實際路徑：」「寫入端：」「驗收分派：」三行。",
    )
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)

    reasons = dict(REQUIRED_LABELS)
    failed = False
    for filename in args.filenames:
        if os.path.basename(filename) == "README.md":
            continue
        with open(filename, encoding="utf-8") as f:
            text = f.read()
        missing = missing_labels(text)
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
