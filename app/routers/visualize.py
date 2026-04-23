"""Routes for data visualization and export."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models import ChartResponse, ExportResponse
from app.services import shared_data_service as data_service

router = APIRouter(tags=["visualize"])


@router.get("/visualize/{name}", response_model=ChartResponse)
async def visualize_dataset(
    name: str,
    chart_type: str = "bar",
    x: str = "",
    y: str = "",
):
    """Generate a Plotly chart for the named dataset."""
    chart = data_service.generate_chart(name, chart_type, x, y)
    if chart is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"chart_html": chart}


@router.get("/export/{name}", response_model=ExportResponse)
async def export_dataset(name: str, format: str = "csv"):
    """Export a dataset as CSV or JSON."""
    result = data_service.export(name, format)
    if result is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"data": result, "format": format}
