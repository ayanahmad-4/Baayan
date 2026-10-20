# Bayaan — Personal AI Assistant for Syed Ayan Ahmad

> A polished, production-ready AI chatbot that lets visitors and recruiters have natural conversations about Ayan's skills, projects, experience, and background.

[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Frontend: React + Vite](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61dafb)](https://vitejs.dev/)
[![AI: Groq](https://img.shields.io/badge/AI-Groq-f55036)](https://groq.com/)

---

## 1. Project Overview

Bayaan is Ayan's personal AI assistant and portfolio companion. Visitors can ask it questions like:

- *"Tell me about Ayan."*
- *"What projects has he built?"*
- *"What are his technical skills?"*
- *"Explain his AI/ML internship."*

The assistant answers only from validated profile data extracted from Ayan's resume. It never fabricates facts.

---

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, Groq Python SDK, PyPDF, Pydantic v2, python-dotenv, Uvicorn |
| Frontend | React 19, Vite 6, React Markdown, Lucide Icons, plain CSS |
| AI Model | Groq (`openai/gpt-oss-20b`, configurable) |
| Backend Hosting | Render (or any Python platform) |
| Frontend Hosting | Netlify |

---

## 3. Project Structure

```
bayaan/
├── back-end/
│   ├── main.py            # FastAPI application
│   ├── system_prompt.txt  # Bayaan's behavior instructions (edit freely)
│   ├── __init__.py
│   └── data/
│       └── resume.pdf     # Ayan's resume (source of truth)
├── front-end/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatHeader.jsx
│   │   │   ├── ChatInput.jsx
│   │   │   ├── ChatMessage.jsx
│   │   │   ├── ChatMessages.jsx
│   │   │   ├── ChatPage.jsx   ← main orchestrator
│   │   │   ├── ChatWelcome.jsx
│   │   │   ├── ErrorMessage.jsx
│   │   │   └── TypingIndicator.jsx
│   │   ├── api.js             # All backend communication
│   │   ├── App.jsx
│   │   ├── App.css            # Chat UI styles (portfolio-matched)
│   │   ├── index.css          # Global styles + CSS variables
│   │   └── main.jsx
│   ├── public/
│   │   └── favicon.svg
│   ├── index.html
│   ├── netlify.toml
│   ├── .env                   # Local dev env (not committed)
│   └── .env.example
├── tests/
│   └── test_api.py            # 20 backend tests
├── .env                       # Local dev env (not committed)
├── .env.example               # Template (safe to commit)
├── .gitignore
├── pyproject.toml
├── requirements.txt           # For Render deployment
├── render.yaml                # Render deployment config
└── README.md
```

---

## 4. Architecture & Request Flow

```
Visitor browser
    │
    ▼
React Frontend (Netlify)
    │  POST /api/chat { message, history }
    ▼
FastAPI Backend (Render)
    │  1. Rate-limit check (in-memory, per IP)
    │  2. Load cached resume (parsed once at startup)
    │  3. Build system prompt with profile data
    │  4. Assemble messages with conversation history
    │  5. Call Groq API
    ▼
Groq AI (openai/gpt-oss-20b)
    │  Streamed/complete response
    ▼
FastAPI → JSON response → React → Rendered Markdown
```

**Resume loading:**
- PDF is read and parsed by the LLM **once at startup**.
- The result is cached in memory.
- The cache is reused for every subsequent request — no repeated Groq calls for parsing.
- Call `GET /api/profile` to verify what's cached.

---

## 5. Prerequisites

- Python 3.11+ (tested on 3.12 and 3.14)
- Node.js 18+ and npm
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A Groq API key from [console.groq.com](https://console.groq.com/)

---

## 6. Windows PowerShell Local Setup

```powershell
# Clone and enter the project
cd e:\aiml\week2\bayaan

# Install Python dependencies with uv
uv sync

# Install frontend dependencies
cd front-end
npm install
cd ..
```

---

## 7. Environment Variable Setup

### Backend (root `.env`)

Copy `.env.example` to `.env` and fill in values:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=openai/gpt-oss-20b
RESUME_PATH=back-end/data/resume.pdf
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
RATE_LIMIT_REQUESTS=30
```

### Frontend (`front-end/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000
```

> **Security**: Never put `GROQ_API_KEY` in any `VITE_*` variable. Vite embeds all `VITE_*` variables into the public JavaScript bundle.

---

## 8. Running Locally

### Start the backend

```powershell
# From the project root:
uv run uvicorn back-end.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be at `http://localhost:8000`. Open `http://localhost:8000/docs` for interactive API docs.

### Start the frontend

```powershell
# In a new terminal:
cd front-end
npm run dev
```

Visit `http://localhost:5173` to use the chatbot.

---

## 9. API Endpoint Documentation

### `GET /health`
Returns the application health status.

**Response:**
```json
{
  "status": "ok",
  "resume_loaded": true,
  "model": "openai/gpt-oss-20b"
}
```

---

### `GET /api/profile`
Returns safe, public profile metadata (no private data, no phone number).

**Response:**
```json
{
  "name": "Syed Ayan Ahmad",
  "location": "Lucknow, India",
  "email": "ayanahmad6508@gmail.com",
  "linkedin": "...",
  "github": "https://github.com/ayanahmad-4",
  "portfolio": "...",
  "career_objective": "...",
  "skills": ["Python", "JavaScript", ...],
  "education": [...],
  "certifications": [...],
  "awards": [...]
}
```

---

### `POST /api/chat`
Generate an AI response.

**Request:**
```json
{
  "message": "What projects has Ayan built?",
  "history": [
    { "role": "user", "content": "Who is Ayan?" },
    { "role": "assistant", "content": "Ayan is a CS undergraduate..." }
  ]
}
```

**Constraints:**
- `message`: 1–1000 characters, required
- `history`: max 10 entries, roles must be `"user"` or `"assistant"`

**Response:**
```json
{
  "answer": "Ayan has built several projects including...",
  "model": "openai/gpt-oss-20b"
}
```

**Error responses:**
| Status | Meaning |
|---|---|
| 422 | Validation error (empty message, invalid role, etc.) |
| 429 | Rate limit exceeded |
| 503 | Resume data unavailable |
| 502 | Groq API error |

---

## 10. Running Tests

```powershell
# From project root:
uv run pytest tests/ -v
```

**Test results (verified):**
- `TestHealthEndpoint` — 3/3 passed
- `TestChatEndpoint` — 9/9 passed (empty, whitespace, too-long, no field, invalid role, valid, history, trim, Groq error, missing resume)
- `TestProfileEndpoint` — 2/2 passed (200 response, no phone leak)
- `TestMiscRoutes` — 2/2 passed (root, legacy route)
- `TestResumeModels` — 3/3 passed (mutable default checks, phone exclusion)

**Total: 20/20 passed ✅**

### Troubleshooting

| Error | Fix |
|---|---|
| `GROQ_API_KEY is not set` | Create `.env` with your key |
| `Resume file not found` | Confirm `back-end/data/resume.pdf` exists |
| `ModuleNotFoundError: groq` | Run `uv sync` |
| `npm run dev` fails | Run `npm install` in `front-end/` first |
| Port 8000 already in use | Kill the existing process or use `--port 8001` |
| Frontend shows "Unavailable" | Make sure the backend is running and CORS is set correctly |

---

## 11. Deploying the Backend (Render)

1. Push your project to a GitHub repository (make sure `.env` is in `.gitignore`).

2. Go to [render.com](https://render.com) → **New → Web Service**.

3. Connect your GitHub repository.

4. Set the following in the Render dashboard:
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn back-end.main:app --host 0.0.0.0 --port $PORT`

5. Add Environment Variables in the Render dashboard:
   ```
   GROQ_API_KEY = <your key>
   GROQ_MODEL   = openai/gpt-oss-20b
   RESUME_PATH  = back-end/data/resume.pdf
   ALLOWED_ORIGINS = https://your-bayaan-frontend.netlify.app,https://my-portfolio-saa.netlify.app
   ```

6. Deploy. Your backend URL will be `https://your-service-name.onrender.com`.

> **Cold start warning**: Render's free tier spins down after 15 minutes of inactivity. The first request after sleep may take 30–60 seconds. The frontend shows a "Connecting" status while this happens. Consider Render's \$7/month paid tier to keep the service warm, or add a cron ping service.

---

## 12. Deploying the Frontend (Vercel)

The frontend is fully configured for Vercel with SPA rewrite rules in `front-end/vercel.json`.

1. Go to **[vercel.com](https://vercel.com)** and sign in with your GitHub account.
2. Click **"Add New..."** → **"Project"**.
3. Import your repository: `ayanahmad-4/Baayan`.
4. In the project configuration screen:
   - **Framework Preset**: Vite
   - **Root Directory**: Click "Edit" and choose `front-end`
   - **Build Command**: `npm run build` (detected automatically)
   - **Output Directory**: `dist` (detected automatically)
5. Expand **Environment Variables** and add:
   - **Name**: `VITE_API_BASE_URL`
   - **Value**: `https://your-bayaan-backend.onrender.com` (your deployed Render API URL from Step 11)
6. Click **Deploy**.
7. Vercel will deploy your app and give you a URL like `https://baayan-frontend.vercel.app` (or whatever project name you choose).

*(Optional: If you prefer Netlify instead, point Base directory to `front-end`, Build command to `npm run build`, Publish directory to `front-end/dist`, and add `VITE_API_BASE_URL` in Netlify environment variables.)*

---

## 13. Configuring Production CORS

After deploying both services, update the backend's `ALLOWED_ORIGINS` environment variable in Render:

```
ALLOWED_ORIGINS=https://baayan-frontend.vercel.app,https://my-portfolio-saa.netlify.app
```

Replace `baayan-frontend.vercel.app` with your actual Vercel domain. Never use `*` (wildcard) with credentials.

---

## 14. Embedding Bayaan in Your Portfolio

Your portfolio is at `https://my-portfolio-saa.netlify.app/`. It's a vanilla HTML site.

### Option A — Floating Chat Button (Recommended)

Add this snippet **just before `</body>`** in your portfolio's `index.html`:

```html
<!-- Bayaan AI Assistant -->
<style>
  .bayaan-launcher {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.75rem;
    font-family: 'DM Sans', sans-serif;
  }
  .bayaan-iframe-wrapper {
    display: none;
    width: 380px;
    height: 560px;
    border-radius: 4px;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    border: 1px solid rgba(201,168,76,0.25);
  }
  .bayaan-iframe-wrapper.open { display: block; }
  .bayaan-iframe-wrapper iframe {
    width: 100%;
    height: 100%;
    border: none;
  }
  .bayaan-toggle-btn {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: #C9A84C;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 20px rgba(201,168,76,0.4);
    transition: background 0.2s, transform 0.15s;
    color: #0A0A0F;
  }
  .bayaan-toggle-btn:hover {
    background: #E8C97A;
    transform: scale(1.05);
  }
  .bayaan-label {
    background: #111118;
    color: #C9A84C;
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.3rem 0.7rem;
    border-radius: 2px;
    border: 1px solid rgba(201,168,76,0.15);
    white-space: nowrap;
    pointer-events: none;
  }
  @media (max-width: 480px) {
    .bayaan-iframe-wrapper { width: calc(100vw - 2rem); height: 70vh; }
    .bayaan-launcher { bottom: 1rem; right: 1rem; }
  }
</style>

<div class="bayaan-launcher" id="bayaan-launcher">
  <div class="bayaan-iframe-wrapper" id="bayaan-panel" role="dialog" aria-label="Bayaan AI assistant">
    <iframe
      id="bayaan-iframe"
      src=""
      data-src="https://your-bayaan-frontend.netlify.app/?embed=1"
      title="Bayaan — AI assistant for Ayan Ahmad"
      loading="lazy"
      allow="clipboard-write"
    ></iframe>
  </div>
  <div style="display:flex;align-items:center;gap:0.5rem;">
    <span class="bayaan-label" aria-hidden="true">Ask Bayaan</span>
    <button
      class="bayaan-toggle-btn"
      id="bayaan-toggle"
      aria-expanded="false"
      aria-controls="bayaan-panel"
      aria-label="Open Bayaan AI assistant"
      title="Chat with Bayaan AI"
    >
      <!-- Chat icon -->
      <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    </button>
  </div>
</div>

<script>
  (function() {
    const toggle = document.getElementById('bayaan-toggle');
    const panel = document.getElementById('bayaan-panel');
    const iframe = document.getElementById('bayaan-iframe');
    let loaded = false;

    toggle.addEventListener('click', function() {
      const isOpen = panel.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(isOpen));
      toggle.setAttribute('aria-label', isOpen ? 'Close Bayaan' : 'Open Bayaan AI assistant');

      // Lazy-load iframe src only when first opened
      if (isOpen && !loaded) {
        iframe.src = iframe.dataset.src;
        loaded = true;
      }
    });
  })();
</script>
<!-- End Bayaan -->
```

**Replace** `https://your-bayaan-frontend.netlify.app` with your actual deployed Netlify URL.

### Option B — Inline Section Embed

Add a section in your portfolio HTML (e.g., after the Contact section):

```html
<section id="bayaan" style="padding: 6rem 4rem; background: #0A0A0F;">
  <div style="max-width: 860px; margin: 0 auto;">
    <p style="font-size:.72rem;letter-spacing:.25em;text-transform:uppercase;color:#C9A84C;margin-bottom:1rem;">AI Assistant</p>
    <h2 style="font-family:'Playfair Display',serif;font-size:clamp(2rem,4vw,3rem);color:#F0EDE6;margin-bottom:0.5rem;">Chat with Bayaan</h2>
    <p style="color:#9A9490;margin-bottom:2rem;">Ask me anything about Ayan — his skills, projects, and experience.</p>
    <div style="height:600px;border:1px solid rgba(201,168,76,0.15);border-radius:2px;overflow:hidden;">
      <iframe
        src="https://your-bayaan-frontend.netlify.app/?embed=1"
        title="Bayaan — AI assistant"
        style="width:100%;height:100%;border:none;"
        allow="clipboard-write"
      ></iframe>
    </div>
  </div>
</section>
```

---

## 15. Updating the Resume

1. Replace `back-end/data/resume.pdf` with the new PDF.
2. Redeploy the backend (or restart the server).
3. The new resume will be parsed and cached automatically at startup.

To force a cache refresh without restarting (not currently implemented as an API — add a reload endpoint if needed):
```python
# In your backend shell:
from back_end.main import load_resume
load_resume(force_reload=True)
```

---

## 16. Security Considerations, Quotas & Limitations

### Security
- `GROQ_API_KEY` is never exposed to the frontend or logged.
- Phone number is excluded from all API responses.
- Conversation history roles are validated — only `user` and `assistant` accepted.
- Rate limiting: 30 requests per IP per minute (configurable).
- CORS is restricted to explicit trusted origins.
- Request size is limited to 1000 characters per message.

### Quotas
- Groq offers a free tier with rate limits. Check your usage at [console.groq.com](https://console.groq.com/).
- The `openai/gpt-oss-20b` model is capable but non-standard. Switch to `llama-3.3-70b-versatile` or similar if you prefer a widely-documented model.

### Limitations
- **No persistent chat history**: Conversation is stored in browser memory only. Refreshing the page resets the chat.
- **No user accounts**: Anyone can use the chatbot.
- **Cold starts**: Render free tier sleeps after 15 minutes. First request after sleep is slow.
- **Resume parsing is LLM-dependent**: If the Groq API is unavailable at startup, resume will be parsed on the first chat request instead.
- **In-memory rate limiting**: Rate limit resets on backend restart and doesn't work across multiple backend instances.
