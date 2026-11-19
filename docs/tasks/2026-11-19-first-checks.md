# dev-checks 第一版：ticket-format 與 forbidden-text

主題歸：faninsights（協調 session 名稱，回報與提問用 SendMessage 傳給它）
角色：backend

## 一句話

把 README 列的兩支檢查做出來，各帶會紅的測試，讓 pre-commit 框架引用得到。做完後協調打 `v0.1.0` tag，faninsights 接上。

## 已經做完

- repo 已建（private），README 列了兩支檢查與接法（`47ffda5`）

## 這一步要做

1. `.pre-commit-hooks.yaml`：登記 `ticket-format`、`forbidden-text`，`language: python`
2. `checks/ticket_format.py`
   - 只檢 `docs/tasks/` 下的 `.md`（用 hook 的 `files` 限定），`README.md` 不檢
   - 每份單要有三行開頭標籤：「實際路徑：」「寫入端：」「驗收分派：」。值可以是「不適用（理由）」
   - 缺的時候印出檔名與缺哪幾個標籤，各附一句為什麼要它，結束碼非 0
3. `checks/forbidden_text.py`
   - `--pattern <字串>` 可給多次，照字面比對（不是正規式）
   - 命中印 `檔名:行號: 該行`，結束碼非 0
   - 一個 `--pattern` 都沒給時當成設定錯誤，印出原因並失敗。不可以靜默通過
   - 二進位檔跳過
4. 本 repo 自己的 `.pre-commit-config.yaml` 用 `repo: local` 跑這兩支，守自己的 `docs/tasks/`
5. 測試放 `tests/`，用標準函式庫 `unittest`
6. `.github/workflows/test.yml`：push 與 PR 時跑測試
7. 工具版本用 `mise.toml` 固定（Python、pre-commit）；README 的「有哪些檢查」狀態改成「有」

實際路徑：不適用（沒有使用者畫面）。執行路徑是 pre-commit 框架把暫存的檔名當參數傳給 hook，要用 `pre-commit try-repo` 走一次真的框架，不能只直接呼叫 script
寫入端：不適用（沒有資料）。hook 的輸入只有檔名清單與 `args`
驗收分派：全部由執行者跑測試與 `try-repo` 自驗，結果貼進進度；協調收單時在另一個暫存 repo 重跑第 4、5 條

## 驗收

每條都寫了什麼情況會紅。

1. 缺「驗收分派：」的單 → `ticket-format` 失敗，訊息點名缺「驗收分派：」。三行都有的單通過。把三個標籤之一從程式拿掉，對應的測試要紅（突變，跑完還原）
2. 含 pattern 的檔 → `forbidden-text` 失敗並印出行號；不含的通過
3. `forbidden-text` 沒給 `--pattern` → 失敗並說明。這條守「設定寫錯時整支檢查形同不存在」，不會有錯誤訊息
4. 暫存 repo 裡用 `pre-commit try-repo <dev-checks 路徑> ticket-format --files docs/tasks/<缺行的單>` 失敗；補齊後通過
5. 同上，`forbidden-text` 帶 `--pattern` 跑一次紅一次綠
6. GitHub Actions 在你推的 commit 上是綠的

## 最容易漏的地方

- pre-commit 只傳暫存或指定的檔，`files` 正規式寫錯時 hook 根本不會被呼叫，結果是一律通過，不會有錯誤訊息。驗收 4 就是在守這個
- 中文檔名：git 預設把非 ASCII 路徑印成八進位轉義。測試要放一份中文檔名的單
- 標籤是全形冒號「：」。用半形冒號寫的不算，要在測試裡放一份半形的，確認被擋

## 不要做

- 不打 tag、不發版（協調做）
- 不加 README 沒列的檢查。覺得還該有別的，寫進進度
- 不放任何其他 repo 的路徑或內部文字
- 發現非改不可的設計問題就停下來回報

## 進度
