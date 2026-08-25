"""Endpoint protegido para analizar un PDF validado y acotado."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.config import MAX_UPLOAD_BYTES
from backend.agent.gemini_client import GeminiUnavailableError, is_gemini_configured
from backend.agent.pdf_reader import OCRPageLimitError
from backend.db.database import guardar_analisis
from backend.observability.tracing import agent_run
from backend.workflow.graph import analysis_graph


logger = logging.getLogger(__name__)
router = APIRouter(tags=["analisis"])
_TMP_DIR = Path(__file__).resolve().parent.parent / "tmp_uploads"
_CHUNK_SIZE = 64 * 1024


class AnalysisResponse(BaseModel):
    analysis_id: str
    filename: str
    cifras: dict[str, Any]
    indicadores: dict[str, Any]
    alertas: list[dict[str, Any]]
    resumen: str
    extraction_mode: Literal["normal", "ocr"]


def _safe_filename(filename: str | None) -> str:
    leaf = (filename or "documento.pdf").replace("\\", "/").split("/")[-1]
    cleaned = "".join(char for char in leaf if char.isprintable()).strip()
    return (cleaned or "documento.pdf")[:255]


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[str, Depends(get_current_user)],
    extraction_mode: Annotated[Literal["normal", "ocr"], Form()] = "normal",
) -> AnalysisResponse:
    filename = _safe_filename(file.filename)
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="El archivo debe tener extension .pdf")

    _TMP_DIR.mkdir(parents=True, exist_ok=True)
    analysis_id = str(uuid.uuid4())
    pdf_path = _TMP_DIR / f"{analysis_id}.pdf"
    size = 0
    header = b""

    try:
        with pdf_path.open("wb") as buffer:
            while chunk := await file.read(_CHUNK_SIZE):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="El PDF excede el limite de carga configurado",
                    )
                if len(header) < 5:
                    header = (header + chunk)[:5]
                buffer.write(chunk)

        if not header.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="El contenido no es un PDF valido")
        if extraction_mode == "ocr" and not is_gemini_configured():
            raise HTTPException(
                status_code=409,
                detail="El modo OCR requiere una clave Gemini configurada y validada en Configuracion",
            )

        with agent_run(run_name=f"analisis-{analysis_id}"):
            resultado = analysis_graph.invoke(
                {
                    "pdf_path": str(pdf_path),
                    "analysis_id": analysis_id,
                    "extraction_mode": extraction_mode,
                }
            )

        guardar_analisis(
            analysis_id=analysis_id,
            filename=filename,
            created_by=current_user,
            cifras=resultado.get("cifras", {}),
            indicadores=resultado.get("indicadores", {}),
            alertas=resultado.get("alertas", []),
            resumen=resultado.get("resumen", ""),
            chunks=resultado.get("chunks", []),
            extraction_mode=extraction_mode,
        )
    except HTTPException:
        raise
    except OCRPageLimitError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except GeminiUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="No se pudo completar el OCR. Revisa la conexion, el modelo o la cuota de Gemini.",
        ) from None
    except Exception as exc:
        logger.error(
            "Fallo interno durante el analisis %s (tipo=%s)",
            analysis_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=422,
            detail=(
                "No se pudo procesar el PDF. Verifica que contenga texto financiero legible; "
                "si es un documento escaneado, selecciona OCR con Gemini."
            ),
        ) from None
    finally:
        await file.close()
        pdf_path.unlink(missing_ok=True)

    return AnalysisResponse(
        analysis_id=analysis_id,
        filename=filename,
        cifras=resultado.get("cifras", {}),
        indicadores=resultado.get("indicadores", {}),
        alertas=resultado.get("alertas", []),
        resumen=resultado.get("resumen", ""),
        extraction_mode=extraction_mode,
    )
