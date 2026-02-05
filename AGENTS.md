# Memo AI - Agent Guide (`AGENTS.md`)

> **ALWAYS READ THIS FILE FIRST** when starting a new task. This guide provides essential context for AI agents working on the Memo AI codebase.

---

## 1. Project Overview

**Memo AI** is a **stateless AI secretary** that uses **Notion** as its primary memory store.
It translates user input (text, images) into structured Notion entries via an AI analysis layer.

### Core Design Principles

| Principle | Description |
| :--- | :--- |
| **Statelessness** | No internal database. All persistence is via Notion API. |
| **Local-First** | Optimized for `uvicorn` local development with `.env` configuration. |
| **Cross-Platform** | Startup commands should be OS-agnostic; config lives in `.env`. |
| **Speed** | Non-blocking model discovery; Notion data loads first. |
| **AI-Friendly Debug** | Debug endpoints/modals provide accurate context for AI assistants. |

---

## 2. Technology Stack

### Backend (`api/`)
| Component | Technology |
| :--- | :--- |
| Language | Python 3.8+ |
| Framework | FastAPI |
| Server | Uvicorn |
| AI Client | LiteLLM (supports Gemini, OpenAI, Anthropic) |
| Notion | `notion-client` SDK |

### Frontend (`public/`)
| Component | Technology |
| :--- | :--- |
| Language | Vanilla JavaScript (ES6+) |
| Framework | **None** (No React, Vue, Angular) |
| Styling | Vanilla CSS (Mobile-first, Responsive) |
| Entry Point | `index.html` |

---

## 3. Directory Structure

```
memo_ai/
├── api/                    # Backend (FastAPI)
│   ├── index.py            # Main routes: /api/chat, /api/save, /api/targets, etc.
│   ├── ai.py               # Prompt engineering, AI model interaction
│   ├── notion.py           # Notion API integration
│   ├── config.py           # Config loading from .env
│   ├── models.py           # Pydantic request/response models
│   ├── model_discovery.py  # Dynamic AI model discovery
│   ├── llm_client.py       # LiteLLM wrapper
│   └── rate_limiter.py     # Rate limiting (1000 req/hr)
│
├── public/                 # Frontend (Vanilla JS)
│   ├── index.html          # Main HTML structure
│   ├── style.css           # All styles
│   └── js/
│       ├── main.js         # Entry point, initialization, Notion target selection
│       ├── chat.js         # Chat UI: bubble rendering, history
│       ├── images.js       # Image capture and processing
│       ├── prompt.js       # System prompt management
│       ├── model.js        # AI model selection UI
│       └── debug.js        # Debug modal (DEBUG_MODE only)
│
├── .env                    # Local secrets (NEVER COMMIT)
├── .env.example            # Template for .env
├── requirements.txt        # Python dependencies
└── vercel.json             # Vercel deployment config
```

---

## 4. Environment Variables

Key variables in `.env` (see `.env.example` for template):

| Variable | Required | Description |
| :--- | :--- | :--- |
| `NOTION_API_KEY` | ✅ | Notion Integration Token |
| `NOTION_ROOT_PAGE_ID` | ✅ | Root page ID for saving data |
| `GEMINI_API_KEY` | ✅ | Google Gemini API Key |
| `DEBUG_MODE` | ❌ | `True` to enable debug endpoints/UI |
| `DEFAULT_TEXT_MODEL` | ❌ | Model for text-only requests |
| `DEFAULT_MULTIMODAL_MODEL` | ❌ | Model for image+text requests |
| `RATE_LIMIT_ENABLED` | ❌ | `True` to enable rate limiting |
| `RATE_LIMIT_GLOBAL_PER_HOUR` | ❌ | Request limit (default: 1000) |

---

## 5. Agent Action Tiers

### ✅ ALWAYS DO
- Use **absolute paths** when referencing files (e.g., `c:\git\memo_ai\...`).
- Respect `DEBUG_MODE`. If `False`, hide debug endpoints and sensitive UI.
- Use `.env` for configuration. Never hardcode API keys.
- Run **`pip install -r requirements.txt`** if dependencies change.
- Check `script.js.bak` for reference when restoring broken features.

### ❓ ASK FIRST
- Before adding new Python packages to `requirements.txt`.
- Before modifying Notion database schema or API calls.
- Before refactoring core frontend modules (`main.js`, `chat.js`).
- Before changing existing API endpoint signatures.

### ❌ NEVER DO
- **Commit secrets** (`.env`, API keys) to Git.
- Suggest adding SQLite, Postgres, or any local database (use Notion).
- Introduce frontend build tools (Webpack, Vite, etc.) without explicit request.
- Migrate to React/Vue/Next.js (the project prioritizes simplicity).

---

## 6. Operational Commands

### Start Development Server
```powershell
# From repository root (c:\git\memo_ai)
python -m uvicorn api.index:app --reload --port 8000
```

### Install Dependencies
```powershell
pip install -r requirements.txt
```

### Access the App
- **Local**: http://localhost:8000
- **Mobile (same network)**: http://192.168.x.x:8000

---

## 7. Common Debugging Patterns

| Issue | Where to Look |
| :--- | :--- |
| 404 on API endpoint | `api/index.py` – check route definition |
| Notion save failed | `api/notion.py` – check payload and API response |
| AI model not found | `api/config.py`, `.env` – verify API keys and model names |
| UI element not working | `public/js/main.js` or specific module – check event listeners |
| Rate limiting issues | `api/rate_limiter.py` – check config and sliding window |

---

## 8. Security Notes

> ⚠️ **This is a demo/educational application.**

- **No authentication** by default. Anyone with the URL can access the API.
- **Rate limiting** is optional (enable via `RATE_LIMIT_ENABLED=True`).
- **CORS** is permissive. Restrict in production by setting `ALLOWED_ORIGINS`.
- For production hardening, see the "Security" section in `README.md`.

---

## 9. Reference Materials

- **README.md**: Setup guide, troubleshooting, customization ideas.
- **script.js.bak**: Historical backup; useful for restoring original behavior.
- **Knowledge Items (KIs)**: Check `memo_ai_project_guide` in `.gemini/antigravity/knowledge/` for deeper architecture docs.

---

# エージェント向けガイド (Japanese Summary)

## プロジェクト概要
Memo AI は **Notion をメモリとして使用するステートレス AI 秘書**です。

## 技術スタック
- **Backend**: Python (FastAPI), LiteLLM, Notion SDK
- **Frontend**: Vanilla JavaScript, CSS (ビルドツールなし)

## 重要ルール
1. **絶対パスを使用**: `c:\git\memo_ai\...`
2. **`.env` で設定管理**: APIキーをハードコードしない
3. **`DEBUG_MODE` を尊重**: 本番では `False` に
4. **DB追加禁止**: Notion のみを使用
5. **フロントエンドフレームワーク禁止**: Vanilla JS を維持

## 起動コマンド
```powershell
python -m uvicorn api.index:app --reload --port 8000
```
