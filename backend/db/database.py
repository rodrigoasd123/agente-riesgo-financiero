"""Persistencia SQLite con aislamiento por propietario autenticado."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from backend.config import (
    ADMIN_PASSWORD_HASH,
    ADMIN_USERNAME,
    ANALYST_PASSWORD_HASH,
    ANALYST_USERNAME,
    DB_PATH,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'analyst')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_sessions (
    jti TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    cifras_json TEXT NOT NULL,
    indicadores_json TEXT NOT NULL,
    alertas_json TEXT NOT NULL,
    resumen TEXT NOT NULL,
    chunks_json TEXT NOT NULL,
    embeddings_json TEXT NOT NULL DEFAULT '[]',
    extraction_mode TEXT NOT NULL DEFAULT 'normal'
);

CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id TEXT NOT NULL,
    asked_by TEXT NOT NULL,
    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    fuente TEXT,
    encontrado INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_analyses_owner_created
ON analyses(created_by, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_questions_analysis_actor
ON questions(analysis_id, asked_by);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_active
ON auth_sessions(username, revoked_at, expires_at);
"""


@contextmanager
def get_connection():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(_SCHEMA)
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT OR IGNORE INTO users
               (username, password_hash, role, is_active, created_at, updated_at)
               VALUES (?, ?, 'admin', 1, ?, ?)""",
            (normalize_username(ADMIN_USERNAME), ADMIN_PASSWORD_HASH, now, now),
        )
        conn.execute(
            """INSERT OR IGNORE INTO users
               (username, password_hash, role, is_active, created_at, updated_at)
               VALUES (?, ?, 'analyst', 1, ?, ?)""",
            (normalize_username(ANALYST_USERNAME), ANALYST_PASSWORD_HASH, now, now),
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(analyses)")}
        if "extraction_mode" not in columns:
            conn.execute(
                "ALTER TABLE analyses ADD COLUMN extraction_mode TEXT NOT NULL DEFAULT 'normal'"
            )
        if "embeddings_json" not in columns:
            conn.execute(
                "ALTER TABLE analyses ADD COLUMN embeddings_json TEXT NOT NULL DEFAULT '[]'"
            )


def normalize_username(username: str) -> str:
    return username.strip().lower()


def obtener_usuario(username: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """SELECT username, password_hash, role, is_active, created_at, updated_at
               FROM users WHERE username = ?""",
            (normalize_username(username),),
        ).fetchone()
        return dict(row) if row else None


def listar_usuarios() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT username, role, is_active, created_at, updated_at
               FROM users ORDER BY username"""
        ).fetchall()
        return [dict(row) for row in rows]


def crear_usuario(username: str, password_hash: str, role: str) -> dict:
    normalized = normalize_username(username)
    now = datetime.now(timezone.utc).isoformat()
    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO users
                   (username, password_hash, role, is_active, created_at, updated_at)
                   VALUES (?, ?, ?, 1, ?, ?)""",
                (normalized, password_hash, role, now, now),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("username_exists") from exc
    user = obtener_usuario(normalized)
    if user is None:
        raise RuntimeError("No se pudo leer el usuario creado")
    user.pop("password_hash", None)
    return user


def establecer_usuario_activo(username: str, is_active: bool) -> dict | None:
    normalized = normalize_username(username)
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE users SET is_active = ?, updated_at = ? WHERE username = ?",
            (int(is_active), now, normalized),
        )
        if cursor.rowcount != 1:
            return None
        if not is_active:
            conn.execute(
                """UPDATE auth_sessions SET revoked_at = ?
                   WHERE username = ? AND revoked_at IS NULL""",
                (now, normalized),
            )
        row = conn.execute(
            """SELECT username, role, is_active, created_at, updated_at
               FROM users WHERE username = ?""",
            (normalized,),
        ).fetchone()
        return dict(row) if row else None


def crear_sesion(jti: str, username: str, expires_at: datetime) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute("DELETE FROM auth_sessions WHERE expires_at <= ?", (now,))
        conn.execute(
            """INSERT INTO auth_sessions (jti, username, created_at, expires_at, revoked_at)
               VALUES (?, ?, ?, ?, NULL)""",
            (jti, normalize_username(username), now, expires_at.isoformat()),
        )


def obtener_identidad_de_sesion(jti: str) -> dict | None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        row = conn.execute(
            """SELECT u.username, u.role, u.is_active, s.jti, s.expires_at, s.revoked_at
               FROM auth_sessions AS s
               JOIN users AS u ON u.username = s.username
               WHERE s.jti = ? AND s.revoked_at IS NULL AND s.expires_at > ?""",
            (jti, now),
        ).fetchone()
        return dict(row) if row else None


def revocar_sesion(jti: str, username: str) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """UPDATE auth_sessions SET revoked_at = ?
               WHERE jti = ? AND username = ? AND revoked_at IS NULL""",
            (now, jti, normalize_username(username)),
        )
        return cursor.rowcount == 1


def guardar_analisis(
    analysis_id: str,
    filename: str,
    created_by: str,
    cifras: dict,
    indicadores: dict,
    alertas: list,
    resumen: str,
    chunks: list | None = None,
    embeddings: list[list[float]] | None = None,
    extraction_mode: str = "normal",
) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO analyses
               (id, filename, created_at, created_by, cifras_json, indicadores_json,
                alertas_json, resumen, chunks_json, embeddings_json, extraction_mode)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                analysis_id,
                filename,
                datetime.now(timezone.utc).isoformat(),
                created_by,
                json.dumps(cifras),
                json.dumps(indicadores),
                json.dumps(alertas),
                resumen,
                json.dumps(chunks or []),
                json.dumps(embeddings or []),
                extraction_mode,
            ),
        )


def actualizar_embeddings(
    analysis_id: str,
    created_by: str,
    embeddings: list[list[float]],
) -> bool:
    """Persist a cache only when the authenticated actor owns the analysis."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE analyses SET embeddings_json = ? WHERE id = ? AND created_by = ?",
            (json.dumps(embeddings), analysis_id, created_by),
        )
        return cursor.rowcount == 1


def guardar_pregunta(
    analysis_id: str,
    asked_by: str,
    pregunta: str,
    respuesta: str,
    fuente: str | None,
    encontrado: bool,
) -> None:
    with get_connection() as conn:
        owner = conn.execute(
            "SELECT 1 FROM analyses WHERE id = ? AND created_by = ?",
            (analysis_id, asked_by),
        ).fetchone()
        if owner is None:
            raise LookupError("Analisis no encontrado")
        conn.execute(
            """INSERT INTO questions
               (analysis_id, asked_by, pregunta, respuesta, fuente, encontrado, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                analysis_id,
                asked_by,
                pregunta,
                respuesta,
                fuente,
                int(encontrado),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def obtener_analisis(analysis_id: str, created_by: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ? AND created_by = ?",
            (analysis_id, created_by),
        ).fetchone()
        return dict(row) if row else None


def listar_analisis(created_by: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, filename, created_at, created_by, extraction_mode
               FROM analyses WHERE created_by = ? ORDER BY created_at DESC""",
            (created_by,),
        ).fetchall()
        return [dict(row) for row in rows]
