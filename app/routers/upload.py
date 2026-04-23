from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.data_service import DataService

router = APIRouter(tags=["upload"])
data_service = DataService()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")
    content = await file.read()
    try:
        summary = data_service.ingest(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"filename": file.filename, "summary": summary}


@router.get("/datasets")
async def list_datasets():
    return {"datasets": data_service.list_datasets()}


@router.get("/datasets/{name}/preview")
async def preview_dataset(name: str, rows: int = 10):
    data = data_service.preview(name, rows)
    if data is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"data": data}
