# Acceptance — Finalizacion, seguridad y Gemini del agente de riesgo financiero

## Acceptance scenarios

- **AC-001** `[FR-001, SEC-001, SEC-002]`: Given `admin` y `admin123`, when login, then retorna JWT valido; password incorrecto falla 401.
- **AC-002** `[SEC-002]`: Given token expirado, alterado, con issuer/audience/type incorrecto, when endpoint protegido, then falla 401.
- **AC-003** `[FR-002, SEC-005]`: Given PDF sintetico valido y JWT, when analyze, then retorna/persiste resultados y elimina temporal.
- **AC-004** `[SEC-005, SEC-006]`: Given archivo no PDF, firma invalida o exceso de tamano, when analyze, then falla 400/413 sin parser ni detalle interno.
- **AC-005** `[SEC-003, FR-004]`: Given analisis de otro actor, when list/chat, then no se lista y chat responde 404.
- **AC-006** `[FR-003, SEC-007]`: Given pregunta sustentada, when chat, then `encontrado=true` y fuente incluye pagina; una pregunta ajena produce `encontrado=false`.
- **AC-007** `[FR-005, NFR-002]`: Given adaptador Gemini simulado, when extraer, then usa modelos configurados, timeout y esquema; salida invalida activa fallback.
- **AC-008** `[FR-006]`: Given ausencia o fallo de Gemini, when pipeline, then completa con fallback determinista sin filtrar excepcion al usuario.
- **AC-009** `[FR-007, SEC-004]`: Given configuracion valida/invalida, when health/startup, then readiness es veraz; `.env` no esta versionado.
- **AC-010** `[NFR-001, NFR-003, NFR-004]`: Given entorno limpio, when compile + pytest + E2E offline, then todas las pruebas pasan y MLflow no bloquea el flujo.

## Verification record

| Criterion | Evidence | Result |
|---|---|---|
| AC-001 | `tests/test_auth.py`, login en TestClient y HTTP real | PASS |
| AC-002 | expiracion, firma alterada, audiencia y tipo invalido en `tests/test_auth.py` | PASS |
| AC-003 | E2E con `data/estado_financiero_ejemplo.pdf` en `tests/test_api.py` | PASS |
| AC-004 | extension, magic bytes y 413 en `tests/test_api.py` | PASS |
| AC-005 | ownership de historial/chat en `tests/test_api.py` | PASS |
| AC-006 | pregunta encontrada/no encontrada con fuente por pagina | PASS |
| AC-007 | `tests/test_gemini_client.py`; modelo, schema y error sanitizado | PASS |
| AC-008 | E2E offline completo y fallbacks unitarios | PASS |
| AC-009 | health offline + `git check-ignore` para secretos/DB/tmp | PASS |
| AC-010 | `pip check`, `compileall`, `pytest` 28/28, smoke MLflow/FastAPI/Streamlit | PASS |

## Nota de proveedor externo

No se ejecuto una llamada de red a Gemini porque `GEMINI_API_KEY` se dejo vacia para que el propietario pegue su clave. Esto no se representa como evidencia: el contrato del SDK fue probado con un doble local y el README indica el smoke manual posterior.
