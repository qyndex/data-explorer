from __future__ import annotations

import io
from typing import Any

import pandas as pd


class DataService:
    """Service for parsing, previewing, and visualizing uploaded data."""

    def __init__(self) -> None:
        self._datasets: dict[str, pd.DataFrame] = {}

    def ingest(self, filename: str, content: bytes) -> dict[str, Any]:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith(".json"):
            df = pd.read_json(io.BytesIO(content))
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        name = filename.rsplit(".", 1)[0]
        self._datasets[name] = df
        return {"rows": len(df), "columns": list(df.columns)}

    def list_datasets(self) -> list[str]:
        return list(self._datasets.keys())

    def preview(self, name: str, rows: int = 10) -> list[dict] | None:
        df = self._datasets.get(name)
        if df is None:
            return None
        return df.head(rows).to_dict(orient="records")

    def generate_chart(self, name: str, chart_type: str, x: str, y: str) -> str | None:
        df = self._datasets.get(name)
        if df is None:
            return None
        try:
            import plotly.express as px
            chart_fns = {"bar": px.bar, "line": px.line, "scatter": px.scatter}
            fn = chart_fns.get(chart_type, px.bar)
            fig = fn(df, x=x or df.columns[0], y=y or df.columns[1])
            return fig.to_html(include_plotlyjs="cdn", full_html=False)
        except Exception:
            return "<p>Chart generation failed</p>"

    def export(self, name: str, fmt: str = "csv") -> str | None:
        df = self._datasets.get(name)
        if df is None:
            return None
        if fmt == "json":
            return df.to_json(orient="records")
        return df.to_csv(index=False)
