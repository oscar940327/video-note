# VideoNote Forge 專案進度

> 目前交付範圍：`URL → Transcript → Structured Note → Review → Download`。
>
> 暫緩範圍：Obsidian Vault 寫入、GitHub／Quartz 發布。

## 目前狀態

**核心影片轉筆記與 Vault／Quartz 本機流程已完成；等待建立使用者的 GitHub note-garden repository 後進行首次公開部署。**

## 整體進度

| 階段 | 狀態 | 說明 |
| --- | --- | --- |
| 專案基礎 | 完成 | 模組結構、設定、README、測試與忽略規則 |
| 影片與字幕 | 完成 | YouTube／Bilibili、人工字幕優先、自動字幕其次 |
| Whisper fallback | 完成 | 無字幕才下載音訊；自動語言偵測；CUDA 失敗退回 CPU |
| 逐字稿處理 | 完成 | 清理、去重、短段合併、時間戳、切分與長片摘要 |
| LLM 章節規劃 | 完成 | Responses API Structured Output 與 NotePlan schema |
| Markdown 生成 | 完成 | 動態章節、Frontmatter、Callout、時間來源及三種 grounding 模式 |
| 筆記驗證 | 完成 | 本機格式檢查與 LLM grounding validation |
| 背景任務 API | 完成 | 建立任務、輪詢進度、結果、驗證與章節重生 |
| 個人網站前端 | 完成 | 真實 API、進度、左右編輯預覽、下載與響應式顯示 |
| 自動化測試 | 完成 | 22 tests passed；外部服務另以最小真實請求驗證 |
| 真實端到端驗收 | 完成 | Bilibili、Whisper CPU fallback、OpenRouter、Vault 寫入與 Quartz build 均已驗證 |
| Obsidian／GitHub／Quartz | 暫緩 | 使用者指定目前不做 |

前端設定決策：MVP 階段隱藏 Note Style 與 Grounding Mode，送出任務時固定使用 `standard` 與 `assisted`；後端仍保留三種模式供未來進階設定使用。

Bilibili 穩定性：自動移除分享網址追蹤參數；HTTP 514 時延遲後重試一次並回傳可操作提示；前端 Note settings 可選擇使用本機 Chrome 或 Edge 登入 Cookie。

瀏覽器 Cookie 資料庫若被 Chrome／Edge 鎖定而無法複製，後端會自動降級為無 Cookie 模式，不再讓整個任務直接失敗。

2026-07-14 真實驗收：指定 Bilibili 影片可取得資訊並完整下載 12.26 MiB 音訊；HTTP 514、逾時與連線重置可自動重試／續傳；Chrome Cookie 鎖定可自動降級；Whisper `small` 成功以 `cpu-fallback` 偵測中文並產生 12 段；OpenRouter structured output 健康測試成功。

下載逾時改善：單次 socket 等待上限設為 15 秒，HTTP／fragment 重試提高至 20 次，保留 `.part` 檔續傳，並將 timeout／retry 狀態回報到前端，避免畫面看似卡死。

Cookie 鎖定的 yt-dlp 原始 ERROR 已從伺服器終端抑制；後端仍會捕捉該狀態、自動改用無 Cookie，並以任務進度訊息告知前端。

Windows job state 寫入改善：`job.json` 改用同目錄唯一暫存檔、flush/fsync、原子取代與 PermissionError 漸進重試，避免密集進度更新或短暫檔案鎖造成 WinError 5。

Whisper 預設模型依使用者決定改為 `large-v3`；前端、API schema、PipelineOptions 與轉錄服務的直接呼叫預設值保持一致。

VideoNote 按鈕互動統一為對比色 hover：實心按鈕反轉為頁面底色，透明／淺色按鈕反轉為文字色底，並補上鍵盤 `focus-visible` 外框。

依使用者決定，前端移除「重新生成目前章節」按鈕與相關 JavaScript；後端端點暫時保留但不在介面曝光。下一階段先理解並評估 Obsidian Vault → GitHub → Quartz 發布流程與視覺案例。

Obsidian／Quartz 階段已開始實作：`note-garden/content` 設為公開 Vault；VideoNote 新增 LLM taxonomy classification、安全 Vault 寫入與 Git commit/push API；前端新增建議位置、儲存 Vault 與發布知識網站操作。Quartz 5 Obsidian 模板、主題入口、GitHub Pages workflow 與中文範例已完成，本機正式建置成功。

## 已完成的主要功能

- [x] 接受 YouTube、Bilibili 與 Bilibili 短網址
- [x] 優先取得人工字幕，其次自動字幕
- [x] 解析 VTT、SRT、YouTube JSON3 與 Bilibili JSON 字幕
- [x] 沒有字幕才下載音訊並使用 faster-whisper
- [x] 自動偵測語言，不要求前端選擇中文或英文
- [x] 支援 Small、Medium、Large-v3 與其他 CLI 模型
- [x] 支援 CPU、CUDA 與 GPU Runtime 失敗後 CPU fallback
- [x] 輸出 TXT、SRT 與結構化 JSON
- [x] 保留原始、清理後、切分後逐字稿
- [x] 長影片按 chunk 產生忠實摘要，再生成整體筆記
- [x] 兩階段 LLM：規劃章節後才生成 Markdown
- [x] Strict／Assisted／Educational grounding 模式
- [x] Markdown 格式檢查與逐字稿忠實度檢查
- [x] 背景任務狀態、進度、錯誤與落盤結果
- [x] 左側 Markdown 修改、右側即時預覽
- [x] Editor 與 Preview 各自獨立捲動
- [x] 重新生成游標所在的 `##` 章節
- [x] 下載修改後的 Markdown

## 前端定案

- 前端位於 `E:\personal_website\video_note.html`。
- Header 中 `VideoNote` 位於 `MktAgent` 之後。
- 頁面流程為「影片輸入 → 處理進度 → Markdown 工作區」。
- 桌面使用 Editor／Preview 雙欄，行動版使用頁籤切換。
- Preview 在左側內容變更後自動更新。
- `檢查筆記` 用於格式與逐字稿忠實度，不是觸發 Preview 更新。
- Transcript Language 固定 Auto Detect。
- Obsidian 儲存按鈕已移除。

## 驗證紀錄

### 2026-07-14

- Python compile/import 通過。
- `pytest`: 15 passed。
- FastAPI `/api/health`: HTTP 200。
- 前端來源的 CORS preflight: HTTP 200。
- `video_note.html` 與 `video-note.js`: HTTP 200。
- JavaScript `node --check`: 通過。
- 尚未進行 OpenRouter API 呼叫，因為 `.env` 尚無 API Key。

## 下一步

1. 複製 `.env.example` 為 `.env` 並填入 `OPENROUTER_API_KEY`。
2. 同時啟動 FastAPI 與個人網站本機伺服器。
3. 用一支有字幕影片與一支無字幕影片各跑一次完整流程。
4. 確認 OpenRouter 帳號可使用 `.env` 設定的模型；若不可用，調整 `OPENROUTER_MODEL`。
5. 根據真實筆記結果微調 prompts。
