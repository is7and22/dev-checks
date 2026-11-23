# ticket-format 加三項：最容易漏、手冊、舊版 app 相容

主題歸：mini-16（協調 session 名稱，回報與提問用 SendMessage 傳給它）
角色：backend

## 一句話

`ticket-format` 從三行標籤擴成六項，讓所有項目的單子都由這一支檢查擋，不再由各項目自己的 hook 各擋一份。做完後協調打 `v0.2.0`。

## 已經做完

- `v0.1.0`（`1ea4a7b`）：`ticket-format` 擋「實際路徑：」「寫入端：」「驗收分派：」

## 這一步要做

改 `checks/ticket_format.py`、`tests/test_ticket_format.py`、README「有哪些檢查」那一列。

1. 「最容易漏」：有一行去掉開頭的 `#` 與空白後以「最容易漏」開頭（例：`## 最容易漏的地方`），或以「最容易漏：」開頭且後面有值
2. 「手冊：」：行首標籤、後面有值。沒有影響的單寫「手冊：不適用（理由）」
3. 「舊版 app 相容：」：只在兩個條件都成立時要求
   - 某一行以「範圍：」開頭，且該行含 `backend` 或「後端」（英文不分大小寫）
   - 全文含 `OpenAPI`、「回傳」或「新欄位」其中之一
4. 新加的三項只對檔名日期 >= `2026-11-23` 的單生效（檔名開頭 `yyyy-mm-dd-`）。檔名沒有日期的照新規則檢查。原有三行標籤照舊對所有單生效
5. 缺的時候照現有格式印出檔名、缺哪幾項、各附一句為什麼要它

實際路徑：不適用（沒有使用者畫面）。執行路徑是 pre-commit 框架把暫存檔名當參數傳給 hook，要用 `pre-commit try-repo` 走一次真的框架
寫入端：不適用（沒有資料）。hook 的輸入只有檔名清單
驗收分派：全部由執行者跑測試與 `try-repo` 自驗，結果貼進進度；不派 qa
手冊：不適用（沒有使用者手冊）

## 驗收

1. 日期 2026-11-23 的單缺「手冊：」→ 失敗，訊息點名「手冊：」；補上就通過。把「手冊：」從程式的清單拿掉，這條測試要紅
2. 日期 2026-11-23 的單沒有任何「最容易漏」行 → 失敗；有 `## 最容易漏的地方` 就通過
3. 範圍行含「後端」、內文含「新欄位」、沒有「舊版 app 相容：」→ 失敗；範圍只有 frontend 的同一份單通過；範圍含後端但內文沒有那三個詞的通過
4. 日期 2026-11-22 的單缺新三項 → 通過（守既有的單不被新規則弄紅）；同一份改名成 2026-11-23 → 失敗
5. 暫存 repo 用 `pre-commit try-repo <dev-checks 路徑> ticket-format --files docs/tasks/<缺手冊的單>` 失敗，補齊後通過；檔名用中文
6. 本 repo 自己的 `docs/tasks/` 用新規則全綠（本單已帶六項）
7. GitHub Actions 在你推的 commit 上是綠的

## 最容易漏的地方

- 日期門檻寫反或比對成字串以外的東西，既有項目的舊單會在 CI 的 `--all-files` 全部變紅。驗收 4 守這條
- 「手冊：」用半形冒號寫的不算，跟既有三行一樣要有測試
- 「範圍：」的判斷只看以它開頭的那一行，不是全文含「後端」。全文判斷會讓只改 app、但內文提到後端的單被誤擋

## 不要做

- 不打 tag，tag 由協調打
- 不改 `forbidden-text`
- 發現要改的不只這三項，停下來回報

## 進度

09:40 dev-checks-7f：開工，worktree `~/.claude/worktrees/dev-checks-backend-ticket-format`，分支 `backend-ticket-format`（從 origin/main `8b8837e`）。
09:43 dev-checks-7f：本單 1–5 項做完，改了 `checks/ticket_format.py`、`tests/test_ticket_format.py`、README 那一列；驗收 5 另在 `tests/test_try_repo.py` 加一支。本機 `REQUIRE_PRE_COMMIT=1 python -m unittest discover -s tests -t .` 41 支全綠，try-repo 那 5 支有跑、沒有略過（pre-commit 4.7.0）；`pre-commit run --all-files` 兩支都 Passed。

- 驗收 1：`test_new_labels_are_required`、`test_manual_label_fixed_passes`；半形冒號和沒有值的情況另有測試。突變做在 commit 之後，用 `git checkout` 還原：程式拿掉「手冊：」的檢查，7 支紅
- 驗收 2：`test_easy_to_miss_forms`，`## 最容易漏的地方`、`最容易漏：x` 等 5 種寫法通過；`最容易漏：`（沒有值）、行中間出現、`## 注意最容易漏` 等 5 種失敗
- 驗收 3：範圍含後端、內文有新欄位，失敗；三個觸發詞各一條；`Backend` 不分大小寫；範圍只有 frontend 的通過；範圍是 frontend、內文其他地方提到後端的也通過；範圍含後端、內文沒有觸發詞的通過。突變：不看後端關鍵字，2 支紅；改成全文判後端，1 支紅
- 驗收 4：`test_date_threshold`，11-22 通過，同一份改名成 11-23 失敗，12-01 失敗，2025-12-31 通過。突變：門檻寫反，2 支紅；檔名沒日期時不套新規則，2 支紅。日期只看檔名，不看目錄名
- 驗收 5：手動做一次。暫存 repo 跑 `pre-commit try-repo <worktree> ticket-format --files docs/tasks/2026-11-23-缺手冊.md`，結果 `Failed`，訊息印「缺 「手冊：」」和理由；補上後 `Passed`。這個流程也寫成 `test_ticket_format_try_repo_manual_red_then_green`
- 驗收 6：`python -m checks.ticket_format docs/tasks/*.md` 回傳 0，`pre-commit run --all-files` Passed
- 單子沒寫明、我自己定的：`最容易漏:`（半形冒號）不算，跟其他標籤的半形規則一致。`OpenAPI` 照單子字面區分大小寫
- 單子三個檔以外還停在舊說法的，沒有改，交協調決定：`.pre-commit-hooks.yaml` 的 name 和 description 還寫「三行標籤」；`pyproject.toml` 的 version 還是 0.1.0；README 範例還是 `rev: v0.1.0`
- 照單子字面，判「範圍：」不去掉前綴，所以 `> 範圍：後端`、`- 範圍：後端`、`範圍:後端` 都不會觸發「舊版 app 相容：」，而且不會報錯。審查子代理統計本機各項目：`範圍：` 開頭的有 533 處，`> 範圍：` 開頭的有 25 處。要不要去掉 `>`、`-`、`#` 前綴再判斷，交協調決定

diff 審查：唯讀子代理審 `origin/main..HEAD`，對照單子的 1–5、最容易漏的地方、驗收、邊界情況（BOM、CRLF、冒號、空值、目錄名、Python 3.8）。本機沒有 Python 的審查 skill，子代理沒有載 skill，改給逐項清單。沒有應修項。已修：BOM 原本是直接寫進原始碼、看不見的字元，改回 `﻿` 跳脫；測試多一個空行。不修：上面兩項交協調；`最容易漏 ：`（中間有空格）會算通過，影響小；程式碼區塊裡的內容也會被算進去，跟原本三行標籤的行為一致
