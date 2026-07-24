# 專案歷史任務

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
