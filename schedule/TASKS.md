# VideoNote Forge 任務清單

## 本輪交付範圍

```text
URL → Transcript → Structured Note → Review → Download
```

## 已完成

### 專案基礎

- [x] 模組化 `videonote/` 套件
- [x] FastAPI 應用程式
- [x] `.env.example` 與 API Key 隔離
- [x] `.gitignore` 排除密鑰、模型產物、影音與任務資料
- [x] Windows 安裝與使用 README
- [x] API 啟動批次檔
- [x] pytest 測試基礎

### 影片、字幕與轉錄

- [x] YouTube／Bilibili／Bilibili 短網址
- [x] 影片中繼資料解析
- [x] 人工字幕優先、自動字幕其次
- [x] VTT、SRT、JSON3、Bilibili JSON 解析
- [x] 無字幕才下載音訊
- [x] faster-whisper fallback
- [x] 自動語言偵測
- [x] CPU／CUDA 與 CPU fallback
- [x] Cookies API 選項
- [x] 下載與轉錄進度回報
- [x] TXT、SRT、JSON 輸出

### 逐字稿處理

- [x] Transcript 與 TranscriptSegment 資料模型
- [x] 移除相鄰重複句子
- [x] 合併過短段落
- [x] 保留 start／end time
- [x] 依長度切分且不拆開 segment
- [x] 長影片分段摘要
- [x] 保存 raw、cleaned、chunks 與 LLM context

### LLM 筆記

- [x] OpenRouter Chat Completions API（JSON Schema structured outputs）
- [x] Structured Output JSON Schema
- [x] Stage 1 NotePlan
- [x] 依影片選擇適合章節
- [x] Stage 2 Markdown 生成
- [x] YAML Frontmatter
- [x] 繁體中文／英文輸出
- [x] Concise／Standard／Detailed
- [x] Strict／Assisted／Educational
- [x] 影片內容與 AI 補充標示規則
- [x] 時間來源、Mermaid、Minimal Code 與 Personal Notes 規則
- [x] 禁止捏造 References
- [x] LLM timeout、重試與可理解錯誤

### 驗證

- [x] YAML Frontmatter
- [x] 唯一 H1 與標題層級
- [x] Code fence 成對
- [x] 空章節與重複標題
- [x] Mermaid 基本檢查
- [x] Windows 合法檔名
- [x] LLM grounding validation
- [x] supported／unsupported claims
- [x] missing key points／possible transcription errors
- [x] 品質提示分數

### API 與前端

- [x] 背景任務與輪詢進度
- [x] 任務資料落盤
- [x] 後端重啟後載入任務紀錄
- [x] 個人網站 Header `VideoNote`
- [x] 真實 API 連線狀態
- [x] URL 與生成設定
- [x] 處理階段與進度
- [x] Markdown Editor 與即時 Preview
- [x] 左右獨立捲動
- [x] Editor／Preview／Split 切換
- [x] 手動檢查筆記
- [x] 移除「重新生成目前章節」前端入口（使用者決定不保留）
- [x] 下載 Markdown
- [x] 響應式手機版
- [x] 移除 Obsidian 寫入入口

### 測試

- [x] 字幕優先順序與格式解析
- [x] 清理、合併與切分
- [x] Markdown 驗證
- [x] LLM 回應解析與缺少 Key 錯誤
- [x] FastAPI health、validate 與 404
- [x] Mock 完整 pipeline
- [x] 15 tests passed
- [x] FastAPI、CORS 與前端靜態資源啟動檢查

## 等待使用者設定後驗收

- [ ] 在 `.env` 填入 `OPENROUTER_API_KEY`
- [ ] 以真實 YouTube 人工字幕完成端到端流程
- [ ] 以真實 Bilibili 字幕完成端到端流程
- [ ] 以無字幕影片完成 Whisper fallback 流程
- [ ] 以 30～60 分鐘影片確認長片摘要品質與 API 成本
- [ ] 在乾淨 Python 3.12 Windows 環境重新安裝驗收

## 明確暫緩

- [x] 安全寫入 Obsidian Vault
- [x] 建立 Vault taxonomy planner：掃描既有資料夾並由 LLM 回傳受控分類結果
- [x] 支援選擇既有主題資料夾、建立合法新資料夾及無法判斷時寫入 Inbox
- [x] 驗證所有輸出路徑位於 Vault 根目錄內，防止 path traversal 與任意覆寫
- [ ] canonical note index 與 Vault 既有筆記掃描
- [ ] Git add／commit／push
- [x] GitHub Actions／Quartz 發布 workflow 與本機 build
- [ ] 播放清單批次處理
- [ ] 影片畫面、投影片與 OCR
- [ ] 雲端部署、多使用者與帳號權限
- [ ] 向量資料庫與 RAG 問答
