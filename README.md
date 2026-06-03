# Local AI Guest Gateway

Local AI Guest Gateway 是一個輕量級的區域網路 AI 算力共享閘道器。
它允許主機（Host）將本地端運行的 Ollama 大語言模型算力分享給同一區域網路內的訪客（Guest）使用。系統內建了訪客申請流程、主機管理儀表板，以及專屬的動態配額（Token 與使用時間限制）機制，確保本地算力的安全與控制。

## ✨ 核心特色 (Features)

*   **等候室與申請機制**: 訪客可透過美觀的 Web 介面輸入暱稱進行算力申請，並於「等候室」中等待主機審核。
*   **主機管理儀表板**: 主機端擁有專屬的 Streamlit 後台，能一覽所有待審核的申請，並支援「一鍵同意/拒絕」。
*   **動態配額限制 (Quota & TTL)**: 主機核准訪客後，系統將自動分配使用期限（預設 2 小時）與對話 Token 額度（預設 50,000 Token）。
*   **SSE 即時串流對話**: 訪客端的 Web 聊天室完美支援 Server-Sent Events (SSE)，能呈現與 ChatGPT 相同的「打字機」逐字輸出效果。
*   **現代化 UI 設計**: 訪客介面採用 Tailwind CSS，搭配玻璃擬物化 (Glassmorphism) 設計、微動畫與深色高質感主題。

## 🛠️ 技術堆疊 (Tech Stack)

*   **後端 API & 代理閘道**: `Python` + `FastAPI` + `httpx`
*   **主機管理後台**: `Streamlit`
*   **訪客前端介面**: 純 `HTML` + `JavaScript` (Fetch API) + `Tailwind CSS`
*   **底層 LLM 引擎**: `Ollama` (本地端預設 API: `http://localhost:11434`)

---

## 🚀 安裝與啟動教學 (Getting Started)

### 1. 環境需求
- Python 3.8+
- 本機已安裝並執行 [Ollama](https://ollama.com/)，且至少 Pull 了一個模型（例如 `llama3`）。

### 2. 安裝依賴套件
請在專案目錄下開啟終端機，執行以下指令來安裝所需的 Python 套件：
```bash
pip install -r requirements.txt
```

### 3. 啟動 FastAPI 後端與訪客網頁
開啟一個終端機，啟動核心 API 伺服器：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
> **訪客連線方式**：請讓區網內的訪客透過瀏覽器連線至 `http://<您的區域網路IP>:8000` 即可開啟申請與對話介面。

### 4. 啟動主機管理儀表板
開啟**另一個**終端機，啟動 Streamlit 管理後台：
```bash
streamlit run dashboard.py
```
> **主機審核方式**：主機請於本機瀏覽器開啟 `http://localhost:8501`。**注意：請勿將此 Port 暴露給區網訪客。**

---

## 💡 使用流程說明

1. **訪客提出申請**：訪客開啟 `http://<IP>:8000`，輸入暱稱並送出。畫面會進入 `Waiting for Approval` 狀態（每 2 秒自動輪詢）。
2. **主機進行審核**：主機在 `http://localhost:8501` 的儀表板上會看到這筆新的申請，可點選「✅ 同意」或「❌ 拒絕」。
3. **訪客開始使用**：若主機點擊同意，訪客畫面將自動切換為聊天室（Chat Room）。
4. **即時對話**：訪客輸入訊息後，系統會自動代理請求至主機的 Ollama，並將生成的 AI 內容以串流方式呈現給訪客，直到達到 Token 上限或時間到期。

---

## 📂 專案結構 (Project Structure)

```text
.
├── main.py              # FastAPI 核心應用、API 路由與狀態管理
├── dashboard.py         # Streamlit 主機端審核儀表板
├── requirements.txt     # 專案 Python 依賴套件清單
├── static/
│   └── index.html       # 訪客端純前端 UI (Tailwind + Vanilla JS)
└── .gitignore           # Git 忽略檔案清單
```
