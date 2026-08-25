"""Compatibility and ownership checks for the additive embedding cache."""

from __future__ import annotations

import json
import sqlite3

import backend.db.database as database


def test_legacy_database_migrates_without_losing_analysis(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_path))
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """CREATE TABLE analyses (
                id TEXT PRIMARY KEY, filename TEXT NOT NULL, created_at TEXT NOT NULL,
                created_by TEXT NOT NULL, cifras_json TEXT NOT NULL,
                indicadores_json TEXT NOT NULL, alertas_json TEXT NOT NULL,
                resumen TEXT NOT NULL, chunks_json TEXT NOT NULL,
                extraction_mode TEXT NOT NULL DEFAULT 'normal'
            )"""
        )
        conn.execute(
            """INSERT INTO analyses VALUES
            ('legacy', 'legacy.pdf', '2026-01-01', 'admin', '{}', '{}', '[]',
             'ok', '[\"fragmento\"]', 'normal')"""
        )

    database.init_db()
    row = database.obtener_analisis("legacy", "admin")

    assert row is not None
    assert row["embeddings_json"] == "[]"
    assert json.loads(row["chunks_json"]) == ["fragmento"]


def test_embedding_cache_update_is_owner_scoped(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "cache.db"))
    database.init_db()
    database.guardar_analisis(
        analysis_id="owned",
        filename="financial.pdf",
        created_by="admin",
        cifras={},
        indicadores={},
        alertas=[],
        resumen="ok",
        chunks=["fragmento"],
    )

    assert database.actualizar_embeddings("owned", "otro", [[0.1, 0.2]]) is False
    assert database.obtener_analisis("owned", "admin")["embeddings_json"] == "[]"
    assert database.actualizar_embeddings("owned", "admin", [[0.1, 0.2]]) is True
    assert json.loads(database.obtener_analisis("owned", "admin")["embeddings_json"]) == [[0.1, 0.2]]
