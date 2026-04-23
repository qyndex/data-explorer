from fastapi import APIRouter, HTTPException
from app.services.data_service import DataService

router = APIRouter(tags=["visualize"])
data_service = DataService()


@router.get("/visualize/{name}")
async def visualize_dataset(name: str, chart_type: str = "bar", x: str = "", y: str = ""):
    chart = data_service.generate_chart(name, chart_type, x, y)
    if chart is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"chart_html": chart}


@router.get("/export/{name}")
async def export_dataset(name: str, format: str = "csv"):
    result = data_service.export(name, format)
    if result is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"data": result, "format": format}
