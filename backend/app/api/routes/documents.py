"""Evidence document upload and listing."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import get_document_service
from app.core.config import get_settings
from app.core.errors import UploadValidationError
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services.documents import DocumentService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

_CHUNK = 1024 * 1024


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(..., description="Text-based PDF, .txt, or .md evidence file"),
    title: str | None = Form(default=None, max_length=500),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    settings = get_settings()
    data = bytearray()
    while True:
        chunk = await file.read(_CHUNK)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > settings.aegis_max_upload_bytes:
            raise UploadValidationError(
                f"File exceeds the {settings.aegis_max_upload_bytes // (1024 * 1024)} MB upload limit."
            )
    await file.close()

    try:
        result = service.ingest_upload(file.filename or "document", file.content_type, bytes(data))
    except UploadValidationError:
        raise
    except Exception:
        logger.exception("Document ingestion failed for a validated upload")
        raise
    return DocumentResponse(**result)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    limit: int = 50,
    service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    safe_limit = max(1, min(limit, 200))
    return DocumentListResponse(documents=service.list_documents(limit=safe_limit))
