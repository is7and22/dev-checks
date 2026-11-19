"""forbidden-text：檔案裡出現不該出現的字串就失敗。

字串由引用的項目用 `--pattern` 給，可給多次，照字面比對（不是正規式）。
一個都沒給時當成設定錯誤：否則設定寫錯時整支檢查形同不存在，也不會有錯誤訊息。
"""

import argparse
import sys

BINARY_SNIFF_BYTES = 8192


def is_binary(data):
    return b"\0" in data[:BINARY_SNIFF_BYTES]


def find_hits(text, patterns):
    """回傳 [(行號, 該行)]，行號從 1 起算。"""
    hits = []
    # 只在 \n 斷行：splitlines() 也在 \x0c 等字元斷，行號會和編輯器對不上
    for lineno, line in enumerate(text.split("\n"), start=1):
        line = line.rstrip("\r")
        if any(p in line for p in patterns):
            hits.append((lineno, line))
    return hits


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="forbidden-text",
        description="檔案裡出現 --pattern 給的字串就失敗（照字面比對）。",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        default=[],
        help="不該出現的字串，可給多次。以 - 開頭的字串寫成 --pattern=-xxx",
    )
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)

    patterns = [p for p in args.pattern if p]
    if not patterns:
        print(
            "forbidden-text 設定錯誤：沒有給任何 --pattern（或只給了空字串）。"
            "在 .pre-commit-config.yaml 的這支 hook 加 args: [--pattern, \"不該出現的字串\"]。"
            "沒有 pattern 時這支檢查什麼都擋不到，所以直接失敗。"
        )
        return 2

    failed = False
    for filename in args.filenames:
        with open(filename, "rb") as f:
            data = f.read()
        if is_binary(data):
            continue
        text = data.decode("utf-8", errors="replace")
        for lineno, line in find_hits(text, patterns):
            failed = True
            print("{}:{}: {}".format(filename, lineno, line))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
