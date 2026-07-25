# Grok Build OAuth Access denied 修復紀錄

## 基本資訊

- 日期：2026-07-25
- 範圍：管理台協議註冊的 Grok Build Authorization Code + PKCE 路徑
- 症狀：consent 階段可能回傳 `Access denied`，且既有錯誤訊息無法可靠指出失敗階段

## 根因與修復

1. consent Server Action 原先先 POST 至移除 query string 的 `/oauth2/consent`，遺失 `client_id`、`state`、PKCE challenge 等交易上下文。
2. 錯誤的第一次提交可能拒絕或消耗 pending transaction，之後再以完整 URL 重送也無法可靠恢復。
3. 現改為只使用完整 consent URL 提交，並對 origin、path 及 transaction query fail-closed 驗證。
4. 移除依賴 `Authorize` 英文文案的判斷；HTTP 200 consent 頁直接依 Server Action 流程處理。
5. callback query、短 RSC/JSON 與短可見錯誤頁會解析 provider 錯誤，`access_denied` 明確標示為 consent 階段。
6. debug log 不再輸出 consent 本文或 OAuth URL query，避免 authorization code、state、PKCE 等單次資料洩漏。

## 驗證結果

- Python `unittest discover -s tests`：29 項全部通過。
- Python `compileall`：通過。
- `go vet ./...`：通過。
- `go test ./...`：通過。
- `go build ./cmd/grok2api`：通過。
- `go build ./cmd/grok2api-migrate`：通過。
- Python LSP：環境未安裝 `basedpyright-langserver`，以測試、編譯與人工 diff 審查替代。

## 六角度檢查

1. **邏輯錯誤**：修復 consent query 遺失、具副作用的重送及按鈕文案相依。
2. **效能問題**：移除一次不必要的 consent 網路請求，未新增額外 I/O。
3. **安全性**：完整 URL 僅用於請求、不寫入錯誤；移除可能包含 authorization code 的 debug 本文。
4. **使用者體驗**：provider `access_denied` 與描述會保留並標示 consent 階段。
5. **型別安全**：helper 具明確輸入／回傳型別，缺少 query 或來源不符時 fail-closed。
6. **可維護性**：consent URL 與錯誤解析拆為純函式，已有獨立回歸測試。

## 敏感資料處理

本段不保存完整 authorize/consent URL、state、nonce、PKCE verifier/challenge、authorization code、access token、refresh token、Cookie 或 session token。

---

# xAI 與 Grok 註冊流程實測紀錄

## 基本資訊

- 執行日期：2026-07-25
- 執行方式：Playwright MCP 瀏覽器自動化
- 官方入口：`https://x.ai` → `https://console.x.ai` → `https://accounts.x.ai/sign-up?redirect=cloud-console`
- 註冊信箱：`yoyo20110918@aurax.eu.org`
- 帳號姓名：`Alex Chen`
- 團隊名稱：`Alex's team`
- 最終方案：免費 `Explore`
- 最終結果：註冊成功，已進入 xAI Console 團隊主控台

## 實際流程

1. 從 `x.ai` 首頁進入 Console，選擇 `Create an account`。
2. 拒絕非必要 Cookie，選擇使用信箱註冊。
3. 輸入信箱並送出，xAI 寄送一次性安全碼。
4. 完成信箱驗證後，填入姓名與密碼。
5. 完成帳號註冊並建立預設團隊 `Alex's team`。
6. 在首次導引中將預設付費方案改為免費 `Explore`。
7. 跳過產品體驗選擇，進入團隊主控台。
8. 重新載入團隊頁，確認登入狀態仍有效。

## 關鍵技術發現

### OTP 輸入控制項

- 郵件中的安全碼帶有連字號，但網頁 OTP 欄位設定為 `maxlength="6"`，且只接受英數字元：`pattern="^[a-zA-Z0-9]+$"`。
- 使用一般 Playwright `fill()` 輸入完整顯示碼時，頁面顯示：`Invalid input: expected string, received undefined`。
- 可行方式是先移除連字號，再使用 `pressSequentially()` 模擬逐字鍵盤輸入。
- 輸入第六個字元後，頁面會自動提交驗證碼，不需要再按確認按鈕。

### 首次導引

- 團隊建立畫面會預填團隊名稱，可直接使用或修改。
- 方案選擇畫面預設勾選付費 `Prototype`，金額為 `$5`，同時呈現自動加值設定。
- 若不打算付款，必須主動切換到免費 `Explore`，並確認按鈕文字變成 `Continue for free`。

### 瀏覽器訊息

- 註冊頁出現 Turnstile 資源未使用的 preload 警告與部分 WebGL 警告，未阻斷流程。
- 初始 Console 頁曾出現監控請求重新導向造成的 CORS 錯誤，登入後主要 Console 請求正常回傳 `200`。
- 信箱驗證、密碼驗證、帳號建立與團隊建立請求均成功。

## 最終狀態

- 登入狀態：正常
- Console 主控台：可存取
- 團隊：`Alex's team`
- 帳戶餘額：`$0.00`
- API key：未建立
- 付費／自動加值：未啟用
- Playwright 完成畫面：`xai-registration-complete.png`

## 六角度檢查

1. **邏輯錯誤**：OTP 顯示格式與輸入欄位限制不一致；已確認正規化與逐字輸入的替代流程。
2. **效能問題**：Turnstile 重複預載與監控請求重新導向產生額外請求，但未影響註冊完成。
3. **安全性**：未建立 API key、未購買額度；密碼不記錄於本檔案，且因曾透過對話提供，應儘快更換。
4. **使用者體驗**：預設選中付費方案容易造成誤操作；OTP 失敗訊息洩漏內部型別錯誤，缺乏可理解的提示。
5. **型別安全**：OTP 元件曾回傳 `undefined` 給字串驗證邏輯，顯示控制項與表單狀態同步不完整。
6. **可維護性**：後續自動化應把 OTP 正規化與鍵盤輸入封裝成獨立步驟，並以頁面狀態而非固定等待時間判斷流程進度。

## 敏感資料處理

本紀錄刻意不保存以下內容：

- 密碼
- 一次性安全碼
- Cookie 或 session token
- Turnstile token
- API key
- 完整請求標頭或請求本文

---

# Grok.com 註冊流程實測紀錄

## 基本資訊

- 執行日期：2026-07-25
- 執行方式：Playwright MCP 瀏覽器自動化
- 官方入口：`https://grok.com` → `https://accounts.x.ai/sign-up?redirect=grok-com&return_to=%2F`
- 註冊信箱：`s12ryt@aurax.eu.org`
- 測試姓名：`Jamie Lin`
- 最終結果：註冊成功，已回到 Grok 首頁並維持登入狀態

## 實際流程

1. 在已登出的 `grok.com` 首頁點選「註冊」。
2. 跳轉到共用的 `accounts.x.ai` 身分系統，選擇使用信箱註冊。
3. 輸入信箱並送出，進入信箱驗證畫面。
4. 將郵件安全碼正規化為 6 位英數字元，再以鍵盤事件逐字輸入。
5. 驗證成功後填入測試姓名與密碼，送出完成註冊。
6. 網站依 `redirect=grok-com` 直接返回 `https://grok.com/`，沒有 Console 團隊或方案導引。
7. 開啟帳戶設定，確認頁面只提供 SuperGrok 升級入口，沒有既存付費方案。
8. 再次直接導覽 `https://grok.com/`，確認登入狀態仍有效。

## 關鍵技術發現

### 共用身分系統

- Grok 與 xAI Console 共用 `accounts.x.ai` 註冊元件。
- Grok 使用 `redirect=grok-com&return_to=%2F`，註冊完成後直接回到 Grok 首頁。
- Console 使用 `redirect=cloud-console`，註冊後另有團隊建立與方案選擇流程；兩者不可共用固定的後續步驟。

### OTP 輸入控制項

- OTP 欄位仍是 `maxlength="6"`、`pattern="^[a-zA-Z0-9]+$"`、`autocomplete="one-time-code"`。
- 郵件顯示碼包含連字號，因此自動化需先移除非英數字元。
- 使用 `pressSequentially()` 輸入正規化後的 6 位安全碼，可觸發元件需要的鍵盤事件並成功驗證。

### 瀏覽器與網路訊息

- `VerifyEmailValidationCode`、`ValidatePassword` 與註冊提交均回傳 `200`。
- 返回 Grok 後，`/api/auth/session`、產品、速率限制、對話與設定等核心請求均回傳 `200`。
- `manifest.webmanifest` 重複回傳 `403`；部分字型因 CSP 未載入，頁面使用替代字型且主要功能正常。
- 註冊前的匿名請求曾回傳 `401`，登入完成後相同核心資源恢復為 `200`，符合權限狀態切換。

## 最終狀態

- 登入狀態：正常，重新導覽後仍有效
- Grok 首頁：可正常存取
- 方案：免費帳號，僅顯示 SuperGrok 升級入口
- 付款／訂閱：未建立
- X 帳戶：未連結
- Playwright 完成畫面：`grok-registration-complete.png`

## 六角度檢查

1. **邏輯錯誤**：OTP 顯示格式與欄位限制不一致；已用移除連字號與逐字輸入修復自動化流程。
2. **效能問題**：manifest 重複 `403`、字型 CSP 失敗及重複監控請求造成額外流量，但未阻斷註冊。
3. **安全性**：未付款、未建立 API key、未連結 X；密碼不記錄於本檔案，且因曾透過對話提供，應在測試後更換。
4. **使用者體驗**：註冊頁與 Grok 主站的中文語系不一致；登入後立即顯示升級與連結 X 提示，但沒有預設付費。
5. **型別安全**：逐字鍵盤輸入未出現型別錯誤；共用 OTP 元件仍應避免以一般 `fill()` 直接送出顯示碼。
6. **可維護性**：自動化應依 redirect 與當前頁面狀態分流，不應假設 Grok 和 Console 有相同的註冊後導引。

## 敏感資料處理

本段紀錄同樣不保存密碼、一次性安全碼、Cookie、session token、Turnstile token、API key、完整請求標頭或請求本文。

---

# Grok Build OAuth 登入流程實測紀錄

## 基本資訊

- 執行日期：2026-07-25
- 執行方式：Playwright MCP 瀏覽器自動化
- OAuth 提供者：xAI `auth.x.ai` / `accounts.x.ai`
- 授權應用程式：`Grok Build`
- 登入帳號：沿用本檔案前述 Grok 測試帳號
- 最終結果：瀏覽器授權成功，應用端完成登入交換（由使用者確認）

## 實際流程

1. 使用應用程式產生的 OAuth 2.0 Authorization Code + PKCE 授權網址進入 xAI。
2. xAI 以既有 Grok 登入狀態顯示 `Grok Build` consent 畫面。
3. 核對要求的身分、profile、email、離線存取、Grok CLI 與 xAI API 權限。
4. 點選允許後，consent 提交回傳 `200`，xAI 產生一次性登入代碼。
5. 因瀏覽器環境無法連線應用程式的 loopback callback，頁面改顯示可交付給 `Grok Build` 的手動代碼。
6. 應用端完成 OAuth 交換並登入成功；此結果由使用者確認。

## 關鍵技術發現

### OAuth 與 PKCE

- 授權流程使用 `response_type=code` 與 PKCE `S256`。
- scope 包含 `openid`、`profile`、`email`、`offline_access`、`grok-cli:access`、`api:access`。
- redirect 使用 loopback callback，適合由本機應用程式接收授權結果。
- callback 暫時不可達時，xAI consent 頁仍會顯示一次性代碼，讓應用程式完成後續交換。
- 授權網址內的 state、nonce 與 PKCE challenge 均屬單次流程資料，不應保存或重複使用。

## 最終狀態

- xAI 帳號登入：正常
- OAuth consent：成功
- consent 提交：HTTP `200`
- 應用端登入交換：成功（由使用者確認）
- 權限範圍：包含離線存取、Grok CLI 與 xAI API

## 六角度檢查

1. **邏輯錯誤**：瀏覽器授權與一次性代碼產生成功；應用端交換結果由使用者確認，流程完整。
2. **效能問題**：本次 consent 僅提交一次且正常回傳，未發現影響登入的效能問題。
3. **安全性**：授權含離線存取及 API 權限；未將完整授權網址、一次性代碼或 token 寫入本紀錄。
4. **使用者體驗**：loopback callback 不可達時會顯示手動代碼，流程可繼續，但瀏覽器的連線錯誤容易讓使用者誤判授權失敗。
5. **型別安全**：本次 consent 操作未出現欄位或表單型別錯誤。
6. **可維護性**：自動化應以 consent `200`、代碼頁出現及應用端交換結果分段判定，不應重複使用帶 state、nonce 或 PKCE 資料的舊授權網址。

## 敏感資料處理

本段紀錄不保存完整 authorize URL、client state、nonce、PKCE challenge、authorization code、access token、refresh token、Cookie、session token、請求標頭或請求本文。

---

# Grok Build 第二次 OAuth 登入授權實測紀錄

## 基本資訊

- 執行日期：2026-07-25
- 執行方式：Playwright MCP 瀏覽器自動化
- OAuth 提供者：xAI `auth.x.ai` / `accounts.x.ai`
- 授權應用程式：`Grok Build`
- 登入帳號：`yoyo20110918@aurax.eu.org`
- 最終結果：指定帳號登入成功，瀏覽器 consent 授權成功並產生一次性授權結果
- 未驗證範圍：應用程式端的 authorization code 交換與 token 取得

## 實際流程

1. 使用新產生的 OAuth 2.0 Authorization Code + PKCE 授權網址進入 xAI。
2. 瀏覽器當時已是登出狀態，因此直接選擇信箱登入。
3. 輸入指定信箱與密碼後，成功進入 `Grok Build` consent 頁。
4. 頁面確認目前登入身分為指定帳號。
5. 核對身分、profile、email、離線存取、Grok CLI 與 xAI API 權限。
6. 點選允許後，consent 提交回傳 HTTP `200`。
7. 頁面進入「輸入代碼完成登入」狀態，且確認一次性授權結果已產生。
8. loopback callback 無接收端時出現連線拒絕，但不影響瀏覽器端授權結果。

## 關鍵技術發現

- 授權使用 Authorization Code + PKCE `S256`。
- scope 為 `openid`、`profile`、`email`、`offline_access`、`grok-cli:access`、`api:access`。
- 授權完成應以 consent HTTP 狀態、成功訊息及授權結果存在共同判定。
- 不應以 loopback callback 的連線拒絕單獨判定授權失敗。
- 檢查瀏覽器主控台時可能連帶顯示含一次性 code 的 callback URL；自動化應只讀取成功旗標，不擷取完整錯誤 URL。

## 最終狀態

- 指定 xAI 帳號登入：成功
- OAuth consent：成功
- consent 提交：HTTP `200`
- 一次性授權結果：已產生
- 應用程式端 code-to-token 交換：未驗證

## 六角度檢查

1. **邏輯錯誤**：登入身分、應用程式、scope、PKCE 與 consent 狀態一致，未發現流程判定錯誤。
2. **效能問題**：登入頁有多筆靜態資源警告，但未阻斷登入或授權。
3. **安全性**：一次性 code 曾出現在 Playwright 工具的主控台輸出；未寫入本檔案，且缺少 PKCE verifier 時不能單獨交換 token。
4. **使用者體驗**：loopback callback 不可達時仍有手動代碼頁，但瀏覽器連線錯誤可能讓使用者誤判失敗。
5. **型別安全**：本輪沒有 OTP 輸入，登入表單未出現欄位型別錯誤。
6. **可維護性**：後續自動化只應檢查成功旗標與 HTTP 狀態，不應讀取包含 code 的完整 callback 或主控台訊息。

## 敏感資料處理

本段紀錄不保存密碼、完整 authorize URL、client state、nonce、PKCE challenge、authorization code、access token、refresh token、Cookie、session token、請求標頭或請求本文。

---

# xAI 註冊加 Grok Build OAuth 一條龍實測紀錄

## 基本資訊

- 執行日期：2026-07-25
- 執行方式：Playwright MCP 瀏覽器自動化
- 註冊與 OAuth 提供者：xAI `accounts.x.ai` / `auth.x.ai`
- 授權應用程式：`Grok Build`
- 註冊信箱：`ciallo@aurax.eu.org`
- 測試姓名：`Morgan Lin`
- 最終結果：新帳號註冊成功，瀏覽器 consent 授權成功並產生一次性授權結果
- 未驗證範圍：應用程式端的 authorization code 交換與 token 取得

## 實際流程

1. 使用新產生的 OAuth 2.0 Authorization Code + PKCE 授權網址進入 xAI。
2. 頁面偵測到上一個帳號仍登入，先從 consent 頁登出，避免授權給錯誤帳號。
3. 從登入頁選擇註冊，再選擇使用信箱註冊。
4. 輸入新信箱後，成功進入一次性安全碼驗證頁。
5. OTP 欄位限制為 `maxlength=6`、`pattern=^[a-zA-Z0-9]+$`、`autocomplete=one-time-code`。
6. 將郵件顯示碼移除連字號後，以 `pressSequentially()` 逐字輸入 6 位英數碼，信箱驗證成功。
7. 使用測試姓名與指定密碼完成帳號建立，註冊後進入 `/account`。
8. 註冊連結沒有保留 OAuth `return_to`，因此完成註冊後未自動返回 consent。
9. 使用尚未消耗的原始 authorize URL 重新導覽，成功以新帳號進入 `Grok Build` consent。
10. 核對登入信箱與六項授權能力後點選允許。
11. 頁面進入授權成功狀態，成功訊息出現、一次性授權結果存在，且允許按鈕已消失。

## 關鍵技術發現

### 註冊與 OTP

- OTP 郵件顯示格式可能含連字號，但網頁欄位只接受 6 位英數字元。
- 一般 `fill()` 可能無法觸發共用 OTP 元件的逐字事件；使用 `pressSequentially()` 較穩定。
- 建立帳號後進入 `/account` 可作為註冊成功的第一個證據。

### OAuth 上下文銜接

- consent 登入頁的註冊連結導向單純的 `/sign-up`，沒有保留原本 OAuth `return_to`。
- 註冊完成後需重新使用同一輪尚未消耗的原始 authorize URL，才能回到正確 consent。
- 重新導覽後必須再次核對登入信箱，避免沿用其他帳號的 session。
- 原始 authorize URL 內含單次 state、nonce 與 PKCE challenge，只能用於當次流程且不應落盤。

## 最終狀態

- 新帳號建立：成功
- 信箱驗證：成功
- 登入 session：成功
- OAuth consent：成功
- 一次性授權結果：已產生
- 應用程式端 code-to-token 交換：未驗證
- 付款、訂閱或 API key：本流程未進行相關操作

## 六角度檢查

1. **邏輯錯誤**：註冊頁遺失 OAuth `return_to`；已以原始未消耗 authorize URL 接回 consent 並驗證登入身分。
2. **效能問題**：帳號頁與註冊頁有多筆非阻斷警告，未發現影響註冊或授權的效能問題。
3. **安全性**：先登出舊帳號並在 consent 再次核對新信箱；未保存密碼、OTP、code、token 或 Cookie。
4. **使用者體驗**：註冊完成後未自動返回原始 consent，使用者需重新開啟授權網址，流程不連續。
5. **型別安全**：OTP 欄位格式與郵件顯示格式不同；已透過正規化及逐字鍵盤事件避免輸入錯誤。
6. **可維護性**：一條龍自動化應保存於記憶體中的原始 authorize URL，並依註冊、帳戶、consent 與成功頁狀態分流。

## 敏感資料處理

本段紀錄不保存密碼、一次性安全碼、完整 authorize URL、client state、nonce、PKCE challenge、authorization code、access token、refresh token、Cookie、session token、請求標頭或請求本文。

# 管理台註冊 Worker OAuth 整合紀錄

## 基本資訊

- 日期：2026-07-25
- 預設認證路徑：SSO Device Flow
- 可選認證路徑：Grok Build Authorization Code + PKCE
- 控制方式：環境變數 `GROK2API_REG_AUTH_FLOW=device|oauth`
- 失敗策略：OAuth 模式失敗時明確終止，不靜默回退 Device Flow

## 本輪實作

1. 修復註冊回應分類中的未定義 `hard_fail` 執行期錯誤。
2. HTTP 200 註冊回應改為 fail-closed，只有具備明確 session、Cookie 或正常 RSC 證據時才判定成功。
3. 將 OTP 擷取與正規化抽成純函式，支援郵件顯示的 `AAA-BBB` 與 xAI 內容中的六位英數格式。
4. PKCE callback 必須包含且完全符合預期 `state`，缺少或不符都拒絕。
5. consent action ID 改由頁面或 chunk 內容動態擷取，找不到時才使用相容常數。
6. OAuth 完成函式新增 `persist` 控制；管理台 worker 使用 `persist=False`，不額外寫入 OAuth token 檔案。
7. 管理台註冊 worker 在完成註冊並取得 session 後，依環境變數選擇 Device Flow 或純 HTTP Grok Build OAuth，再共用既有帳號匯入格式。

## 單元測試與回歸

- Python `unittest`：20 項全部通過。
- 覆蓋範圍：OTP 正規化、認證路徑設定、註冊回應分類、PKCE state、consent action、`persist=False` 不落盤。
- Python `compileall`：通過。
- Go registration 與 server 套件測試：通過。
- Python LSP：環境未安裝 `basedpyright-langserver`，因此以單元測試、編譯檢查及人工 diff 審查替代。

## 六角度檢查

1. **邏輯錯誤**：修復未知 HTTP 200 誤判、缺少 PKCE state 仍接受，以及 worker 認證路徑未分流等問題。
2. **效能問題**：Device Flow 預設路徑不增加額外請求；只有明確啟用 OAuth 時才增加授權交換 I/O。
3. **安全性**：OAuth 不靜默降級、state 嚴格驗證，且 worker 不額外保存 OAuth token 檔案。
4. **使用者體驗**：環境變數值錯誤時明確失敗；工作進度會區分 Device Flow 與 Grok Build OAuth。
5. **型別安全**：OTP 郵件資料與 OAuth token 都先檢查資料形狀及必要欄位再使用。
6. **可維護性**：OTP、認證路徑與 consent action 已抽成可獨立測試的純函式。

## 敏感資料處理

本段紀錄不保存密碼、OTP、SSO、完整 authorize URL、state、nonce、PKCE verifier/challenge、authorization code、access token、refresh token、Cookie 或 session token。

---

# Go Foundation CI 修復紀錄

## 基本資訊

- 日期：2026-07-25
- 目標 workflow：`.github/workflows/compatibility.yml` 的 `go-foundation`
- 根因：7 個 Go 檔案未通過 `gofmt`，另有 Grep schema 與 shell argv 引號的過期測試期待。

## 本輪修改

1. 對 CI 在 LF checkout 真正列出的 7 個 Go 檔案套用 `gofmt`。
2. Grep 的 `search` alias 測試改為期待 required field `pattern`，與正式 schema 及正規化邏輯一致。
3. shell argv 含空白 token 的測試改為期待雙引號，對齊既有 PowerShell-safe 實作。
4. 將 `.release-commit` 從 `v2.0.3` 對齊 Python 與 Go 目前版本 `v2.0.4`。
5. 未修改 workflow，也未變更正式 shell 或 Grep 執行行為。

## 驗證結果

- LF 乾淨 clone：`gofmt -l cmd internal` 無輸出。
- `go vet ./...`：通過。
- `go test ./...`：通過。
- `go build ./cmd/grok2api`：通過。
- `go build ./cmd/grok2api-migrate`：通過。
- release version pin gate：通過，Python、Go 與 `.release-commit` 均為 `2.0.4`。
- LSP：環境未安裝 `gopls`，以 vet、完整測試、build 與人工 diff 審查替代。
- Race test：Windows 本機 `CGO_ENABLED=0` 無法執行，交由 Ubuntu GitHub Actions 驗證。
- GitHub Actions：`Compatibility contracts` run `30129765025` 通過；Ubuntu 的格式、vet、完整測試、race、build、版本 pin 與 contracts jobs 均成功。

## 六角度檢查

1. **邏輯錯誤**：修正 Grep `query`／`pattern` 與 shell 單／雙引號的 stale tests。
2. **效能問題**：僅格式與測試契約調整，未增加執行期計算或 I/O。
3. **安全性**：未變更權限、輸入處理或敏感資料流程。
4. **使用者體驗**：測試失敗訊息與實際 schema 一致，CI 診斷更準確。
5. **型別安全**：JSON 欄位期待與 required schema 一致；完整 Go 測試與 vet 通過。
6. **可維護性**：同步過期註解與所有相同 shell expected values，避免寬鬆測試掩蓋舊契約。
