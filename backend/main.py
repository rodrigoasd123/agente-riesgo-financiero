"""Aplicacion FastAPI del agente financiero."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.gemini_client import is_gemini_configured
from backend.api.routes_analyze import router as analyze_router
from backend.api.routes_chat import router as chat_router
from backend.api.routes_history import router as history_router
from backend.api.routes_finance import router as finance_router
from backend.api.routes_settings import router as settings_router
from backend.auth.routes import router as auth_router
from backend.auth.security import validate_auth_configuration
from backend.config import CORS_ORIGINS, GEMINI_EMBEDDING_MODEL, GEMINI_MODEL, OCR_MAX_PAGES
from backend.db.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_auth_configuration()
    init_db()
    yield


app = FastAPI(
    title="Agente de Analisis de Riesgo Financiero",
    description=(
        "Analiza estados financieros sinteticos, calcula indicadores, detecta alertas "
        "y responde con fuentes. No sustituye la revision humana."
    ),
    version="1.6.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
def health() -> dict:
    gemini_ready = is_gemini_configured()
    return {
        "status": "ok",
        "ready": True,
        "mode": "gemini" if gemini_ready else "offline-fallback",
        "gemini_configured": gemini_ready,
        "gemini_model": GEMINI_MODEL,
        "embedding_model": GEMINI_EMBEDDING_MODEL,
        "ocr_configured": gemini_ready,
        "ocr_max_pages": OCR_MAX_PAGES,
    }


app.include_router(auth_router)
app.include_router(analyze_router)
app.include_router(chat_router)
app.include_router(history_router)
app.include_router(finance_router)
app.include_router(settings_router)
