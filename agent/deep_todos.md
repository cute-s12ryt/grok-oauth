# 專案歷史任務

## 2026-07-25：Grok Build OAuth Access denied 修復

- 修正 consent Server Action 錯誤先送至裸路徑、遺失 OAuth transaction query 的問題。
- 移除 consent 重複提交及英文按鈕文案相依，新增階段化 provider 錯誤解析。
- 移除可能洩漏 authorization code 的 debug 本文預覽。
- 新增 consent URL、`access_denied`、HTML 假陽性與 PKCE callback 回歸測試。
- 驗證 Python 29 項測試、compileall、Go vet、完整 Go 測試及兩個 Go binary build。

## 2026-07-25：管理台註冊與 OAuth 整合

- 完成 xAI、Grok.com 與 Grok Build OAuth 實測。
- 新增可設定的註冊後認證流程：Device Flow 或 Authorization Code + PKCE。
- 加固註冊回應、OTP 正規化、PKCE state 與 token 持久化邊界。
- 更新 README 與 `agent/memory.md` 實測紀錄。

## 2026-07-25：Go Foundation CI 修復

- 修正 7 個 `gofmt` 未通過的 Go 檔案。
- 將 Grep alias 測試對齊 `pattern` schema。
- 將 shell argv 測試對齊既有 PowerShell-safe 雙引號行為。
- 將 `.release-commit` 從 `v2.0.3` 對齊目前程式版本 `v2.0.4`。
- 驗證 `gofmt`、`go vet ./...`、`go test ./...` 與兩個 Go binary build。

## 待辦

- 無。

## 完成驗證

- GitHub Actions `Compatibility contracts` run `30129765025` 已通過。
- `contracts` 與 `go-foundation` jobs 均成功，包含 Ubuntu race test、build 與版本 pin gate。
