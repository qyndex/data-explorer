"""Routes for file upload and dataset listing/preview."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth import get_current_user_id
from app.models import PreviewResponse
from app.services import shared_data_service as data_service

router = APIRouter(tags=["upload"])

# Optional auth — if token is present, use it; otherwise anonymous mode
_optional_bearer = HTTPBearer(auto_error=False)


async def _optional_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
) -> str | None:
    """Return user ID if a valid token is present, None otherwise."""
    if credentials is None:
        return None
    try:
        return await get_current_user_id(credentials)
    except HTTPException:
        return None


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str | None = Depends(_optional_user_id),
):
    """Upload a CSV or JSON file.

    If authenticated, the dataset is persisted in the database.
    Otherwise it lives in-memory for the current server session.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")
    content = await file.read()
    try:
        summary = data_service.ingest(
            file.filename, content, owner_id=user_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "filename": file.filename,
        "summary": summary,
        "dataset_id": summary.get("dataset_id", ""),
    }


@router.get("/datasets")
async def list_datasets(
    user_id: str | None = Depends(_optional_user_id),
):
    """List datasets.

    Authenticated users get full metadata from the database.
    Unauthenticated users get in-memory dataset names.
    """
    if user_id:
        datasets = data_service.list_datasets(owner_id=user_id)
        return {"datasets": datasets}

    # In-memory mode: return simple name list for backward compat
    return {"datasets": data_service.list_dataset_names()}


@router.get("/datasets/{name}/preview", response_model=PreviewResponse)
async def preview_dataset(name: str, rows: int = 10):
    """Preview the first N rows of a dataset."""
    data = data_service.preview(name, rows)
    if data is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"data": data}
