from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel

from ehrlich.api.auth import get_current_user
from ehrlich.investigation.application.file_processor import FileProcessor

if TYPE_CHECKING:
    from ehrlich.investigation.domain.uploaded_file import UploadedFile as UploadedFileEntity

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])

_require_user = Depends(get_current_user)
_processor = FileProcessor()

# Pending uploads waiting to be linked to an investigation.
# Keyed by file_id, removed when claimed by POST /investigate.
_pending_uploads: dict[str, UploadedFileEntity] = {}


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    content_type: str
    preview: dict[str, Any]


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile,
    user: dict[str, Any] = _require_user,
) -> UploadResponse:
    """Upload a CSV, Excel, or PDF file for use in investigations."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    content = await file.read()

    try:
        uploaded = _processor.process(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    _pending_uploads[uploaded.file_id] = uploaded

    preview: dict[str, Any] = {}
    if uploaded.tabular:
        preview = {
            "type": "tabular",
            "columns": list(uploaded.tabular.columns),
            "dtypes": list(uploaded.tabular.dtypes),
            "row_count": uploaded.tabular.row_count,
            "sample_rows": [list(r) for r in uploaded.tabular.sample_rows[:5]],
        }
    elif uploaded.document:
        preview = {
            "type": "document",
            "text": uploaded.document.text[:500],
            "page_count": uploaded.document.page_count,
        }

    return UploadResponse(
        file_id=uploaded.file_id,
        filename=uploaded.filename,
        content_type=uploaded.content_type,
        preview=preview,
    )


def get_pending_upload(file_id: str) -> UploadedFileEntity | None:
    """Retrieve and remove a pending upload by ID. Called from investigation routes."""
    return _pending_uploads.pop(file_id, None)
