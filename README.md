# VideoNote

VideoNote 將 YouTube／Bilibili 影片轉成可編輯的 Markdown 學習筆記，並可將筆記安全儲存到 Obsidian Vault。

## 主要功能

- 取得影片字幕，沒有字幕時使用 Whisper 轉錄
- 使用 OpenRouter 產生結構化 Markdown 筆記
- 在網頁中編輯、預覽及下載 Markdown
- 由 LLM 判斷筆記分類並儲存到 `note-garden/content`
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
VIDEONOTE_VAULT_PATH=E:\toy project\note-garden\content
```

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
