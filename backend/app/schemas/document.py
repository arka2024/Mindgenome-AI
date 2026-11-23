from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ChapterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    page_start: int
    page_end: int


class IngestionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    progress_pct: int
    stage_detail: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    status: str
    page_count: int | None = None
    is_low_text: bool = False
    low_text_warning: str | None = None
    created_at: datetime
    job_id: uuid.UUID | None = None
    chapters: list[ChapterResponse] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    page: int
    page_size: int
    total: int


class UploadAcceptedResponse(BaseModel):
    document_id: uuid.UUID
    job_id: uuid.UUID
    status: str = "queued"
