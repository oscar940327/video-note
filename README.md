# VideoNote

VideoNote 將 YouTube／Bilibili 影片轉成可編輯的 Markdown 學習筆記，並可將筆記安全儲存到 Obsidian Vault。

## 主要功能

- 取得影片字幕，沒有字幕時使用 Whisper 轉錄
- 使用 OpenRouter 產生結構化 Markdown 筆記
- 在網頁中編輯、預覽及下載 Markdown
- 由 LLM 判斷筆記分類並儲存到 `note-garden/content`
- 從前端查看實際 Vault 分類、覆寫 LLM 建議或建立新分類；已儲存筆記可安全搬移
- 透過 Quartz 與 GitHub Pages 發布知識網站

## 安裝

```powershell
cd "E:\toy project\video-note"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

編輯 `.env`，至少設定：

```dotenv
OPENROUTER_API_KEY=你的_API_Key
OPENROUTER_GENERATION_MODEL=openai/gpt-5.6-luna-pro
OPENROUTER_CONTEXT_MODEL=qwen/qwen3.5-flash
OPENROUTER_REVIEW_MODEL=deepseek/deepseek-v4-flash
OPENROUTER_CLASSIFICATION_MODEL=qwen/qwen3.5-9b
VIDEONOTE_VAULT_PATH=E:\toy project\note-garden\content
```

模型分工固定如下：Qwen 整理超長逐字稿並分類 Vault；GPT-5.6 Luna Pro 在一次呼叫中完成規劃與完整文章；DeepSeek 獨立找錯並提出局部修改。只有重大章節問題才交回 GPT 局部重寫。完整文章輸出上限維持 20,000 tokens。

Vault 分類由 `GET /api/vault/folders` 提供 note-garden 的實際第一層資料夾。儲存或發布時以前端選擇為準；如果筆記已存在且分類改變，後端會先原子寫入新位置，再刪除舊檔。新分類會自動建立 Quartz 使用的 `index.md`。

`.env` 包含私密資料，不要提交到 Git。

## 啟動

啟動後端：

```powershell
cd "E:\toy project\video-note"
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8010 --reload
```

啟動個人網站前端：

```powershell
cd "E:\personal_website"
python -m http.server 4173
```

開啟：

```text
http://127.0.0.1:4173/video_note.html
```

後端 API 文件：

```text
http://127.0.0.1:8010/docs
```

## 使用流程

```text
貼上影片網址
→ 產生逐字稿與 Markdown 筆記
→ 在前端修改及預覽
→ 儲存到 Obsidian Vault
→ 手動 commit / push note-garden
→ Quartz 自動更新知識網站
```

相關專案：

- `E:\personal_website`：VideoNote 前端
- `E:\toy project\video-note`：轉錄與筆記生成後端
- `E:\toy project\note-garden`：Obsidian Vault 與 Quartz 網站
