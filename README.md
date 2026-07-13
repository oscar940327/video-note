# VideoNote Forge

VideoNote Forge 將 YouTube／Bilibili 技術影片轉成可編輯、可下載的結構化 Markdown 學習筆記。

目前完成的流程：

```text
Video URL
→ 優先取得人工字幕
→ 其次使用自動字幕
→ 無字幕才下載音訊並使用 faster-whisper
→ 清理、去重、保留時間戳並切分逐字稿
→ LLM 規劃適合的筆記章節
→ LLM 生成 Markdown
→ 格式與逐字稿忠實度檢查
→ 前端編輯、即時預覽、局部重新生成、下載
```

Obsidian Vault 寫入、GitHub 與 Quartz 發布目前刻意不實作。

## 環境需求

- Windows 10／11
- 建議 Python 3.12（目前開發環境也可在 Python 3.14 執行測試）
- CPU 可完整執行；NVIDIA GPU 為選用加速
- OpenRouter API Key（用於筆記規劃、生成與 grounding validation）

## 安裝

```powershell
cd "E:\toy project\video-note"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

建立設定檔：

```powershell
Copy-Item .env.example .env
```

編輯 `.env`：

```dotenv
OPENROUTER_API_KEY=你的_OpenRouter_API_Key
OPENROUTER_MODEL=~google/gemini-flash-latest
VIDEONOTE_VAULT_PATH=E:\toy project\note-garden\content
VIDEONOTE_VAULT_AUTO_CREATE_FOLDERS=true
```

API Key 不可提交到 Git；`.gitignore` 已排除 `.env`。

## 啟動後端

```powershell
cd "E:\toy project\video-note"
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8010 --reload
```

確認：

```text
http://127.0.0.1:8010/docs
http://127.0.0.1:8010/api/health
```

## 啟動個人網站前端

開另一個 PowerShell：

```powershell
cd "E:\personal_website"
python -m http.server 4173
```

打開：

```text
http://127.0.0.1:4173/video_note.html
```

若後端與前端皆正常，頁面標題旁會顯示 `API ready`。沒有 API Key 時會顯示
`API ready · Add OPENROUTER_API_KEY`，此時字幕與 Whisper 程式已可使用，但完整筆記任務會在 LLM 階段停止。

## 前端功能

- YouTube／Bilibili URL 輸入
- 自動偵測逐字稿語言
- 輸出語言、Whisper 模型、筆記詳細度與 Grounding 模式
- CPU 強制模式
- 真實後端處理進度
- 左側 Markdown Editor、右側即時 Preview
- 兩側獨立捲動
- Editor／Preview／Split 顯示切換
- Markdown 格式與 grounding 檢查
- 重新生成游標所在的 `##` 章節
- 下載修改後的 `.md`

## Grounding 模式

- `Strict`：只整理逐字稿明確支持的內容。
- `Assisted`：可補足小幅理解脈絡，但必須標示 AI 補充；預設模式。
- `Educational`：可加入教學用最小示例，但必須明確說明不是影片原始內容。

## 輸出資料

每個任務保存在：

```text
data/jobs/<job_id>/
├── job.json
├── video.json
├── transcript.raw.json
├── transcript.context.txt
├── transcript.chunks.json
├── note-plan.json
├── validation.json
├── *.md
├── raw/
└── transcripts/
    ├── *.txt
    ├── *.srt
    └── *.json
```

`data/` 預設不提交至 Git。

## API

- `GET /api/health`
- `POST /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/{job_id}/result`
- `POST /api/validate`
- `POST /api/regenerate-section`

完整 schema 可在 `/docs` 查看。

## 測試

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

測試不會下載影片，也不會呼叫付費 LLM API。

## CUDA 問題

若出現 `cublas64_12.dll`、cuDNN 或 CUDA DLL 錯誤：

1. 前端勾選 `Force CPU`，先確認完整流程。
2. 或安裝與 CTranslate2 相容的 CUDA 12／cuBLAS 環境。

後端也會在偵測到常見 CUDA Runtime 錯誤時，自動改用 CPU 重試。

## 舊版逐字稿 CLI

仍可單獨使用：

```powershell
.\.venv\Scripts\python.exe transcribe_video.py "影片網址" --model small --cpu
```
