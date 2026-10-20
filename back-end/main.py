"""
Bayaan — Personal AI Assistant for Syed Ayan Ahmad
Backend API (FastAPI + Groq)
"""

from __future__ import annotations

import json
import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from groq import APIStatusError, Groq
from pydantic import BaseModel, Field, field_validator
from pypdf import PdfReader

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("bayaan")

# Groq
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. "
        "Create a .env file with GROQ_API_KEY=<your-key>"
    )

# Resume path — relative to this file's directory
_BACKEND_DIR = Path(__file__).parent
RESUME_PATH = Path(
    os.getenv("RESUME_PATH", str(_BACKEND_DIR / "data" / "resume.pdf"))
)

# CORS — comma-separated list of allowed origins
_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
)
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# Rate limiting — requests per IP per minute
RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW_SECONDS: int = 60

# Message limits
MAX_MESSAGE_LENGTH = 1000
MAX_HISTORY_MESSAGES = 10  # number of prior turns to include

# System prompt template
_SYSTEM_PROMPT_FILE = _BACKEND_DIR / "system_prompt.txt"

# ---------------------------------------------------------------------------
# Groq client (singleton)
# ---------------------------------------------------------------------------

groq_client = Groq(api_key=GROQ_API_KEY)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class Experience(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    skills_used: list[str] = Field(default_factory=list)


class Resume(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    location: Optional[str] = None
    career_objective: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)


# Generate schema once
_RESUME_SCHEMA = Resume.model_json_schema()


class HistoryMessage(BaseModel):
    role: str
    content: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        return v[:MAX_MESSAGE_LENGTH]


class ChatRequest(BaseModel):
    message: str
    history: list[HistoryMessage] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")
        if len(v) > MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters"
            )
        return v

    @field_validator("history")
    @classmethod
    def validate_history(cls, v: list[HistoryMessage]) -> list[HistoryMessage]:
        return v[-MAX_HISTORY_MESSAGES:]


class ChatResponse(BaseModel):
    answer: str
    model: str


class HealthResponse(BaseModel):
    status: str
    resume_loaded: bool
    model: str


class ProfileResponse(BaseModel):
    name: Optional[str]
    location: Optional[str]
    email: Optional[str]
    linkedin: Optional[str]
    github: Optional[str]
    portfolio: Optional[str]
    career_objective: Optional[str]
    skills: list[str]
    education: list[str]
    certifications: list[str]
    awards: list[str]


# ---------------------------------------------------------------------------
# Resume loading and caching
# ---------------------------------------------------------------------------


def _read_pdf(path: Path) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


def _parse_resume_with_llm(resume_text: str) -> Resume:
    """Ask the LLM to parse resume text into structured JSON."""
    system_prompt = f"""You are an expert resume parser.

Extract information from the resume text based on its meaning, not just section headings.
Different headings like 'Experience', 'Professional Experience', 'Internships' all count as experiences.
Skills appear in Skills sections, work descriptions, and project descriptions.

Return ONLY valid JSON matching this schema:
{json.dumps(_RESUME_SCHEMA, indent=2)}

Rules:
1. Do not invent any information.
2. If a value is missing, return null.
3. If a list has no information, return an empty list.
4. Include internships inside experiences.
5. Extract all social links (LinkedIn, GitHub, Portfolio) if present.
6. Extract career objective if present.
7. Extract awards and recognitions.
"""
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Parse this resume:\n\n{resume_text}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    raw = response.choices[0].message.content
    data = json.loads(raw)
    return Resume(**data)


# Module-level cache for resume
_cached_resume: Optional[Resume] = None
_resume_load_error: Optional[str] = None


def load_resume(force_reload: bool = False) -> Resume:
    """Load and cache the parsed resume. Raises on failure."""
    global _cached_resume, _resume_load_error

    if _cached_resume is not None and not force_reload:
        return _cached_resume

    log.info("Loading resume from %s", RESUME_PATH)

    if not RESUME_PATH.exists():
        _resume_load_error = f"Resume file not found at {RESUME_PATH}"
        raise FileNotFoundError(_resume_load_error)

    try:
        text = _read_pdf(RESUME_PATH)
    except Exception as e:
        _resume_load_error = f"Failed to read PDF: {e}"
        raise RuntimeError(_resume_load_error) from e

    if not text.strip():
        _resume_load_error = "Extracted resume text is empty"
        raise ValueError(_resume_load_error)

    try:
        resume = _parse_resume_with_llm(text)
    except json.JSONDecodeError as e:
        _resume_load_error = f"LLM returned invalid JSON: {e}"
        raise RuntimeError(_resume_load_error) from e
    except Exception as e:
        _resume_load_error = f"Resume parsing failed: {e}"
        raise RuntimeError(_resume_load_error) from e

    _cached_resume = resume
    _resume_load_error = None
    log.info("Resume loaded and cached for: %s", resume.name)
    return resume


def is_resume_loaded() -> bool:
    return _cached_resume is not None


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_system_prompt_template() -> str:
    """Load system prompt template from file (cached)."""
    if _SYSTEM_PROMPT_FILE.exists():
        return _SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")
    # Fallback inline prompt
    return """You are Bayaan, a personal AI assistant for {profile_data}.
Answer questions accurately based on the profile data only.
Never invent facts. If information is missing, say so honestly."""


def build_system_prompt(resume: Resume) -> str:
    """Inject resume data into the system prompt template."""
    template = _load_system_prompt_template()
    profile_json = resume.model_dump_json(indent=2, exclude={"phone"})
    return template.replace("{profile_data}", profile_json)


# ---------------------------------------------------------------------------
# Rate limiting (in-memory, per IP)
# ---------------------------------------------------------------------------

_rate_store: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(ip: str) -> None:
    """Raise HTTPException if IP exceeds rate limit."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    hits = _rate_store[ip]
    # Remove old hits
    hits[:] = [t for t in hits if t > window_start]
    if len(hits) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait before sending another message.",
        )
    hits.append(now)


# ---------------------------------------------------------------------------
# FastAPI application (with lifespan for startup tasks)
# ---------------------------------------------------------------------------

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load resume on startup so the first request is fast."""
    try:
        load_resume()
    except Exception as e:
        log.warning("Could not pre-load resume on startup: %s", e)
        log.warning("Resume will be loaded on first chat request.")
    yield  # application runs here


app = FastAPI(
    title="Bayaan API",
    description="Personal AI assistant for Syed Ayan Ahmad",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "An internal error occurred. Please try again."},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """Health check endpoint for deployment platforms."""
    return HealthResponse(
        status="ok",
        resume_loaded=is_resume_loaded(),
        model=GROQ_MODEL,
    )


@app.get("/api/profile", response_model=ProfileResponse, tags=["profile"])
async def get_profile() -> ProfileResponse:
    """Return safe, public profile metadata."""
    try:
        resume = load_resume()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Profile data is temporarily unavailable.",
        ) from e
    return ProfileResponse(
        name=resume.name,
        location=resume.location,
        email=resume.email,
        linkedin=resume.linkedin,
        github=resume.github,
        portfolio=resume.portfolio,
        career_objective=resume.career_objective,
        skills=resume.skills,
        education=resume.education,
        certifications=resume.certifications,
        awards=resume.awards,
    )


@app.post("/api/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request_body: ChatRequest, request: Request) -> ChatResponse:
    """
    Generate an AI response to a user message.

    Accepts optional conversation history for follow-up questions.
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(client_ip)

    # Load resume (uses cache after first call)
    try:
        resume = load_resume()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Ayan's profile data is temporarily unavailable. Please try again shortly.",
        ) from e

    system_prompt = build_system_prompt(resume)

    # Build messages list
    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    # Add conversation history (already validated and trimmed by Pydantic)
    for msg in request_body.history:
        messages.append({"role": msg.role, "content": msg.content})

    # Add current message
    messages.append({"role": "user", "content": request_body.message})

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            timeout=30.0,
        )
        answer = response.choices[0].message.content
    except APIStatusError as e:
        log.error("Groq API error (status %s): %s", e.status_code, e.message)
        if e.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="AI service is busy. Please try again in a moment.",
            ) from e
        raise HTTPException(
            status_code=502,
            detail="AI service returned an error. Please try again.",
        ) from e
    except Exception as e:
        log.error("Unexpected error calling Groq: %s", e, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Could not reach the AI service. Please check your connection and try again.",
        ) from e

    return ChatResponse(answer=answer, model=GROQ_MODEL)


# Backward-compat alias kept for any existing integrations
@app.post("/chat", include_in_schema=False)
async def chat_legacy(request_body: ChatRequest, request: Request) -> ChatResponse:
    return await chat(request_body, request)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Bayaan API is running. See /docs for endpoints.", "health": "/health"}
