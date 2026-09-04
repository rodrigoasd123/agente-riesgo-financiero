"""Configuracion central validada desde variables de entorno."""

from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env(key: str, default: str | None = None) -> str:
    value = os.getenv(key, default)
    if value is None or not value.strip():
        raise RuntimeError(f"Falta la variable de entorno requerida: {key}")
    return value.strip()


def _positive_int(key: str, default: int, *, minimum: int = 1, maximum: int = 10_000) -> int:
    try:
        value = int(os.getenv(key, str(default)))
    except ValueError as exc:
        raise RuntimeError(f"{key} debe ser un numero entero") from exc
    if not minimum <= value <= maximum:
        raise RuntimeError(f"{key} debe estar entre {minimum} y {maximum}")
    return value


def _bool_env(key: str, default: bool) -> bool:
    raw = os.getenv(key, str(default)).strip().lower()
    if raw not in {"true", "false", "1", "0", "yes", "no"}:
        raise RuntimeError(f"{key} debe ser true o false")
    return raw in {"true", "1", "yes"}


# Gemini (el agente mantiene fallback offline si la clave esta vacia).
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001").strip()
GEMINI_TIMEOUT_SECONDS = _positive_int("GEMINI_TIMEOUT_SECONDS", 30, maximum=300)
OCR_MAX_PAGES = _positive_int("OCR_MAX_PAGES", 15, maximum=50)
OCR_RENDER_DPI = _positive_int("OCR_RENDER_DPI", 180, minimum=96, maximum=300)

# JWT: el algoritmo no es controlable desde el entorno para evitar confusion.
JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = _env("JWT_SECRET_KEY")
JWT_EXPIRE_MINUTES = _positive_int("JWT_EXPIRE_MINUTES", 60, maximum=1440)
JWT_ISSUER = _env("JWT_ISSUER", "agente-riesgo-financiero")
JWT_AUDIENCE = _env("JWT_AUDIENCE", "agente-riesgo-financiero-api")

if len(JWT_SECRET_KEY) < 32 or "REEMPLAZAR" in JWT_SECRET_KEY.upper():
    raise RuntimeError("JWT_SECRET_KEY debe ser un secreto aleatorio de al menos 32 caracteres")

# Usuario local de la demo.
ADMIN_USERNAME = _env("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = _env("ADMIN_PASSWORD_HASH")
if not re.fullmatch(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}", ADMIN_PASSWORD_HASH):
    raise RuntimeError("ADMIN_PASSWORD_HASH no tiene un formato bcrypt valido")

# Analista local de la demo; se inserta de forma idempotente y nunca sobrescribe cuentas existentes.
ANALYST_USERNAME = _env("ANALYST_USERNAME", "analista")
ANALYST_PASSWORD_HASH = _env(
    "ANALYST_PASSWORD_HASH",
    "$2a$12$voQ1vS2PpkR5Do3rPCaFJ.SmOygaLYvRP1qHKbpkMKtzr/.ugiJv6",
)
if not re.fullmatch(r"\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}", ANALYST_PASSWORD_HASH):
    raise RuntimeError("ANALYST_PASSWORD_HASH no tiene un formato bcrypt valido")

# Persistencia, limites y operacion.
_db_path = Path(os.getenv("DB_PATH", "backend/db/analisis.db"))
DB_PATH = str(_db_path if _db_path.is_absolute() else BASE_DIR / _db_path)
MAX_UPLOAD_BYTES = _positive_int("MAX_UPLOAD_MB", 10, maximum=100) * 1024 * 1024
MAX_CHAT_LENGTH = _positive_int("MAX_CHAT_LENGTH", 1000, maximum=10_000)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")
    if origin.strip()
]

MLFLOW_ENABLED = _bool_env("MLFLOW_ENABLED", True)
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db").strip()
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "agente-riesgo-financiero").strip()
_mlflow_ui_url = os.getenv("MLFLOW_UI_URL", "http://localhost:5000").strip()
MLFLOW_UI_URL = (
    _mlflow_ui_url
    if _mlflow_ui_url.startswith(("http://", "https://"))
    else "http://localhost:5000"
)

# Correo: el destino de infraestructura nunca proviene de una peticion HTTP.
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = _positive_int("SMTP_PORT", 587, maximum=65_535)
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip()
SMTP_USE_TLS = _bool_env("SMTP_USE_TLS", True)
SMTP_TIMEOUT_SECONDS = _positive_int("SMTP_TIMEOUT_SECONDS", 20, maximum=120)

# Correo HTTPS recomendado para despliegues que bloquean puertos SMTP.
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev").strip()
RESEND_TIMEOUT_SECONDS = _positive_int("RESEND_TIMEOUT_SECONDS", 20, maximum=120)

# Gmail API por OAuth 2.0. El refresh token se guarda cifrado por la aplicacion.
GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "").strip()
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "").strip()
GMAIL_REDIRECT_URI = os.getenv(
    "GMAIL_REDIRECT_URI",
    "http://localhost:8000/settings/gmail/callback",
).strip()
GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN", "").strip()
GMAIL_ACCOUNT_EMAIL = os.getenv("GMAIL_ACCOUNT_EMAIL", "").strip()
GMAIL_TIMEOUT_SECONDS = _positive_int("GMAIL_TIMEOUT_SECONDS", 20, maximum=120)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501").strip().rstrip("/")

# Lista ampliable por entorno; se compara por palabras completas y texto normalizado.
GUARDRAIL_BLOCKED_TERMS = [
    term.strip()
    for term in os.getenv(
        "GUARDRAIL_BLOCKED_TERMS",
        "idiota,imbecil,estupido,puta,mierda,fuck,shit",
    ).split(",")
    if term.strip()
]

# Umbrales deterministas de alertas financieras.
UMBRAL_LIQUIDEZ_CORRIENTE = 1.0
UMBRAL_PRUEBA_ACIDA = 0.8
UMBRAL_ENDEUDAMIENTO_TOTAL = 0.6
UMBRAL_COBERTURA_INTERESES = 1.5
UMBRAL_CAIDA_VENTAS_PORCENTUAL = -10.0
