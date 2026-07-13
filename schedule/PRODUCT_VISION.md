# VideoNote Forge：終極目標

## 產品定位

**VideoNote Forge** 是一個將 YouTube 或 Bilibili 技術影片，自動轉換為高品質、可追溯且可持續累積的 Markdown 學習筆記工具。

它的價值不只在語音轉文字，而是完成從「影片來源」到「個人知識庫」再到「公開知識網站」的完整流程。

## 終極成品

使用者只要貼上影片網址並選擇偏好，系統即可：

```text
YouTube / Bilibili URL
        ↓
取得官方字幕，無字幕時使用 Whisper
        ↓
清理、校正並切分逐字稿
        ↓
分析影片類型與核心內容
        ↓
規劃適合該影片的筆記章節
        ↓
生成附時間來源的 Markdown 筆記
        ↓
驗證格式、內容與逐字稿忠實度
        ↓
使用者預覽、編輯與局部重新生成
        ↓
下載 Markdown
```

> 目前交付範圍到下載 Markdown 為止。Obsidian Vault 寫入、GitHub 與 Quartz 發布保留為後續階段。

## 理想使用體驗

1. 使用者貼上單一影片網址。
2. 系統自動判斷平台、影片資訊、字幕及語言。
3. 畫面即時顯示每個處理階段與清楚的錯誤訊息。
4. 系統只產生適合影片的章節，不套用僵硬的固定模板。
5. 每個重要論點保留影片時間來源。
6. 影片內容與 AI 額外補充有明確標示。
7. 使用者可在 Markdown 編輯器中校訂並即時預覽。
8. 使用者確認後下載 Markdown；不在目前版本直接寫入任何 Vault。

## 前端產品入口

- VideoNote Forge 前端整合於個人網站的 **VideoNote** 頁面。
- 個人網站 Header 提供與 `MktAgent` 並列的 `VideoNote` 導覽項目。
- VideoNote 是獨立工作區，沿用個人網站既有的視覺語言、深淺色模式及響應式設計。
- 桌面版主要工作區採用左側 Markdown 編輯、右側即時預覽；行動版改用 Editor／Preview 切換。
- 桌面版左右面板可各自獨立捲動，預設不啟用同步捲動。
- 逐字稿來源語言由系統自動偵測，不要求一般使用者手動選擇中文或英文。

## 核心產品原則

### 來源忠實

- 影片內容與 AI 補充必須分開標示。
- 重要內容盡可能附上時間戳。
- 不捏造影片沒有提過的來源、程式碼或結論。
- LLM 驗證結果只作為品質提示，不宣稱百分之百正確。

### 使用者掌控

- 產生結果必須能預覽與修改。
- 支援只重新生成選定章節。
- 寫入同名筆記前必須詢問使用者。
- Personal Notes 預設提供待填問題，不冒充使用者觀點。

### 模組化與可靠性

- 下載、字幕、轉錄、處理、生成、驗證及匯出各自獨立。
- 所有重要階段都有 log、狀態與可理解的錯誤訊息。
- LLM 優先使用 Structured Output。
- 保留原始逐字稿及生成前後的中間資料。
- CPU 模式是最低可靠基準，GPU 是效能增強選項。

### 知識庫相容

- Markdown 同時相容 Obsidian 與 Quartz。
- 使用 YAML Frontmatter、Mermaid、Callouts 與 Wikilinks。
- 透過 canonical note index 避免同義筆記重複分裂。
- 未來 Vault 寫入由 LLM 參考筆記標題、摘要、標籤與既有資料夾，選擇既有主題資料夾或提出新主題；後端負責路徑白名單、合法名稱、Vault 邊界與重複檔名驗證，LLM 不直接控制檔案系統路徑。
- 公開知識內容與 Quartz 建議使用獨立的 `video-note-garden` repository，和 VideoNote 後端程式碼、Personal Website 分開管理。

## MVP 成品定義

第一個可交付版本必須穩定完成：

```text
URL → Transcript → Structured Note → Review → Download
```

MVP 包含：

- YouTube、Bilibili 與 Bilibili 短網址
- 官方字幕優先，Whisper 作為 fallback
- TXT、SRT 與結構化逐字稿保存
- 兩階段 LLM：章節規劃與 Markdown 生成
- Strict／Assisted／Educational grounding 模式
- 基本 Markdown 與內容驗證
- Streamlit 編輯、預覽與進度畫面
- Markdown 下載
- Windows 安裝、設定與疑難排解文件

## MVP 暫不包含

- 影片畫面、簡報或 OCR 辨識
- 播放清單批次處理
- 多人帳號與權限系統
- 雲端部署
- Obsidian Vault 寫入
- 自動 Git commit／push
- Quartz 全自動部署
- 向量資料庫與 RAG 問答

## 長期方向

MVP 穩定後，VideoNote Forge 可逐步發展為個人影音知識管線：

- 批次處理課程與播放清單
- 擷取影片畫面、投影片及程式碼片段
- 跨影片概念整合與重複內容合併
- 從現有 Vault 取得脈絡，改善 Wikilinks 與標籤
- GitHub 自動版本管理
- Quartz 自動發布與知識圖譜瀏覽
- 對影片與個人筆記進行可溯源問答

## 成功標準

- 一般使用者不需理解 `yt-dlp`、Whisper 或 LLM 細節即可操作。
- 30～60 分鐘的技術影片能穩定產生可閱讀且可校訂的筆記。
- 每個重要論點能回到逐字稿或影片時間點核對。
- 輸出的 Markdown 不需手動修復格式即可進入 Obsidian／Quartz。
- 失敗時不遺失資料、不覆蓋筆記，並能清楚指出修復方法。
