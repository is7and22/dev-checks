# dev-checks

各項目共用的 [pre-commit](https://pre-commit.com/) 檢查。項目在 `.pre-commit-config.yaml` 引用本 repo 並固定版本，本機 `git commit` 時跑，CI 用 `pre-commit run --all-files` 再跑一次。

檢查只放「跨項目都一樣」的流程規則。單一項目自己的規則放在該項目。

## 有哪些檢查

| hook id | 擋什麼 | 狀態 |
|---|---|---|
| `ticket-format` | `docs/tasks/` 裡的派工單缺必要的行：「實際路徑：」「寫入端：」「驗收分派：」 | 有 |
| `forbidden-text` | repo 裡出現不該出現的字串，例如另一個 repo 的路徑或內部連結語法。字串由引用的項目用 `args` 給 | 有 |

每支檢查都附會紅的測試：放一份違規的檔，確認檢查擋下並說出缺什麼。

## 項目怎麼接

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/is7and22/dev-checks
    rev: v0.1.0          # 用 tag，pre-commit autoupdate 升級
    hooks:
      - id: ticket-format
      - id: forbidden-text
        args: [--pattern, "某個不該出現的字串"]
```

```sh
pre-commit install            # 裝成 git pre-commit
pre-commit run --all-files    # CI 與手動全掃
```

本 repo 是 private：CI 拉它要有讀取權限的 token（GitHub Actions、Bitbucket Pipelines 各設一次）。

## 開發

- 檢查用 Python 寫，只用標準函式庫
- 新增檢查：寫在 `checks/`，登記在 `.pre-commit-hooks.yaml`，測試放 `tests/`，更新上表
- 工具版本固定在 `mise.toml`（Python、pre-commit）：`mise install`
- 測試：`python -m unittest discover -s tests -t .`。`tests/test_try_repo.py` 在暫存 repo 裡走真的 pre-commit 框架，本機沒裝 pre-commit 時略過，CI 不略過
- `forbidden-text` 不檢 `.pre-commit-config.yaml`：它本身一定含 pattern 的字面。引用端自己寫 `exclude` 會蓋掉這個預設，要把它併進去
- 發版：改完打新 tag，引用的項目跑 `pre-commit autoupdate`
