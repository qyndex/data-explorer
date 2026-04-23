"""Pydantic models for request/response bodies."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class SignUpRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str = ""


class SignInRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    email: str


class ProfileResponse(BaseModel):
    id: str
    email: str | None
    full_name: str | None
    plan: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------

class ColumnSchema(BaseModel):
    name: str
    type: str


class DatasetCreate(BaseModel):
    name: str
    description: str = ""


class DatasetResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    description: str
    schema_: dict[str, Any] = Field(alias="schema")
    row_count: int
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class DatasetListResponse(BaseModel):
    datasets: list[DatasetResponse]


class UploadResponse(BaseModel):
    filename: str
    summary: dict[str, Any]
    dataset_id: str


# ---------------------------------------------------------------------------
# Saved queries
# ---------------------------------------------------------------------------

class SavedQueryCreate(BaseModel):
    dataset_id: str
    name: str
    sql_query: str
    description: str = ""


class SavedQueryResponse(BaseModel):
    id: str
    owner_id: str
    dataset_id: str
    name: str
    sql_query: str
    description: str
    created_at: datetime


class SavedQueryListResponse(BaseModel):
    queries: list[SavedQueryResponse]


# ---------------------------------------------------------------------------
# Query results
# ---------------------------------------------------------------------------

class QueryResultResponse(BaseModel):
    id: str
    query_id: str
    result_data: list[dict[str, Any]]
    row_count: int
    execution_time_ms: int
    created_at: datetime


class QueryResultListResponse(BaseModel):
    results: list[QueryResultResponse]


# ---------------------------------------------------------------------------
# Preview / Visualize / Export (envelope wrappers)
# ---------------------------------------------------------------------------

class PreviewResponse(BaseModel):
    data: list[dict[str, Any]]


class ChartResponse(BaseModel):
    chart_html: str


class ExportResponse(BaseModel):
    data: str
    format: str
