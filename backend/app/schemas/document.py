"""Pydantic schemas for evidence documents."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    document_id: int
    title: str
    filename: str
    content_hash: str
    source_type: str
    passage_count: int
    created_at: datetime
    already_existed: bool = False


class DocumentSummary(BaseModel):
    document_id: int
    title: str
    filename: str
    source_type: str
    passage_count: int
    created_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary] = Field(default_factory=list)
