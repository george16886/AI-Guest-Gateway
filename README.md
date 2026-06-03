# Local AI Guest Gateway

Local AI Guest Gateway 是一個輕量級的區域網路 AI 算力共享閘道器。
它允許主機（Host）將本地端運行的 Ollama 大語言模型算力分享給同一區域網路內的訪客（Guest）使用。系統內建了訪客申請流程、主機管理儀表板，以及專屬的動態配額（Token 與使用時間限制）機制，確保本地算力的安全與控制。

## ✨ 核心特色 (Features)

*   **等候室與申請機制**: 訪客可透過美觀的 Web 介面輸入暱稱進行算力申請，並於「等候室」中等待主機審核。
*   **主機管理儀表板**: 主機端擁有專屬的 Streamlit 後台，能一覽所有待審核的申請，並支援「一鍵同意/拒絕」。
*   **動態配額限制 (Quota & TTL)**: 主機核准訪客後，系統將自動分配使用期限與對話 Token 額度。
*   **SSE 即時串流對話**: 訪客端的 Web 聊天室完美支援 Server-Sent Events (SSE)，能呈現與 ChatGPT 相同的「打字機」逐字輸出效果。
*   **持久化儲存 (Persistence)**: 訪客連線與配額資料會自動儲存於 `database.json` 中，伺服器重啟也不會遺失連線進度。

## 🚀 全新進階功能 (Advanced Features)

*   **🌍 多人共享大廳 (Public Lounge)**: 加入了以 WebSockets 打造的即時多人聊天室。區網內的訪客可以互相聊天，並透過 `@AI` 指令召喚 AI 參與群聊，所有人都可即時看到 AI 的串流回覆！
*   **🎙️ 語音對話 (Voice Chat)**: 支援瀏覽器內建 Web Speech API，可以「語音輸入」對話，並開啟「Auto-Speech」讓 AI 直接用語音唸出回覆。
*   **🎭 AI 人設與模型切換 (Persona / Model Hub)**: 系統會自動抓取本地端 Ollama 已安裝的所有模型供訪客切換。訪客還可以自訂「專屬人設 (Custom Persona)」，讓 AI 扮演任何角色。
*   **📊 數據統計戰情室 (Analytics Dashboard)**: 主機端後台新增圖表統計介面，圓餅圖、長條圖一目了然，方便主機追蹤所有使用者的 Token 消耗與狀態。
*   **👁️ 視覺模型支援 (Vision Support)**: 支援上傳圖片，讓具有視覺能力的模型（如 LLaVA 等）幫忙分析圖片內容。
*   **🎨 動態主題切換 (Theme Switcher)**: 訪客端可以一鍵切換多種精美配色主題（如：深海沉浸、賽博龐克、幽暗森林、黑金尊爵）。
*   **💾 匯出與 Markdown 渲染**: 支援完美的 Markdown 程式碼高亮與排版，並提供一鍵「匯出對話紀錄為 .md 檔案」功能。

## 🛠️ 技術堆疊 (Tech Stack)

*   **後端 API & 代理閘道**: `Python` + `FastAPI` + `httpx` + `websockets`
*   **主機管理後台**: `Streamlit` + `Pandas`
*   **訪客前端介面**: 純 `HTML` + `JavaScript` (Fetch API, WebSockets, Web Speech API) + `Tailwind CSS`
*   **底層 LLM 引擎**: `Ollama` (本地端預設 API: `http://localhost:11434`)

---

## 🚀 安裝與啟動教學 (Getting Started)

### 1. 環境需求
- Python 3.8+
- 本機已安裝並執行 [Ollama](https://ollama.com/)，且至少 Pull 了一個模型（例如 `llama3`）。

### 2. 一鍵啟動 (Windows 推薦)
直接在專案資料夾點擊兩下執行 **`start.bat`**。
腳本會自動為您：
1. 建立虛擬環境 (env)
2. 讀取 `requirements.txt` 安裝所有依賴套件
3. 自動開啟兩個視窗，分別運行 FastAPI 後端與 Streamlit 管理後台！

*(若您使用 Mac/Linux 或想手動啟動，請參考以下步驟)*

### 3. 手動安裝與啟動
請在專案目錄下開啟終端機，安裝所需的 Python 套件：
```bash
pip install -r requirements.txt
```

開啟第一個終端機，啟動核心 API 伺服器：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
> **訪客連線方式**：請讓區網內的訪客透過瀏覽器連線至 `http://<您的區域網路IP>:8000` 即可開啟申請與對話介面。

開啟**第二個**終端機，啟動 Streamlit 管理後台：
```bash
streamlit run dashboard.py
```
> **主機審核方式**：主機請於本機瀏覽器開啟 `http://localhost:8501`。**注意：請勿將此 Port 暴露給區網訪客。**

---

## 📂 專案結構 (Project Structure)

```text
.
├── main.py              # FastAPI 核心應用、WebSocket 大廳與狀態管理
├── dashboard.py         # Streamlit 主機端審核儀表板與數據圖表
├── requirements.txt     # 專案 Python 依賴套件清單
├── start.bat            # Windows 專用一鍵啟動腳本
├── database.json        # 系統自動生成的儲存資料庫 (已加入 .gitignore)
├── static/
│   └── index.html       # 訪客端純前端 UI (Tailwind + Vanilla JS)
└── .gitignore           # Git 忽略檔案清單
```
