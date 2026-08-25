"""Persistencia SQLite con aislamiento por propietario autenticado."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from backend.config import DB_PATH


_SCHEMA = """
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
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(analyses)")}
        if "extraction_mode" not in columns:
            conn.execute(
                "ALTER TABLE analyses ADD COLUMN extraction_mode TEXT NOT NULL DEFAULT 'normal'"
            )


def guardar_analisis(
    analysis_id: str,
    filename: str,
    created_by: str,
    cifras: dict,
    indicadores: dict,
    alertas: list,
    resumen: str,
    chunks: list | None = None,
    extraction_mode: str = "normal",
) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO analyses
               (id, filename, created_at, created_by, cifras_json, indicadores_json,
                alertas_json, resumen, chunks_json, extraction_mode)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                extraction_mode,
            ),
        )


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
