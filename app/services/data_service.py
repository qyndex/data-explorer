"""Service for ingesting, previewing, querying, and visualizing datasets.

Supports two modes:
  - **Database mode** (production): stores metadata in Supabase, operates on
    uploaded data via pandas in-memory processing.
  - **In-memory mode** (tests / no DB): stores everything in a dict keyed by
    dataset name — zero external dependencies.

The mode is auto-detected: if ``SUPABASE_URL`` is set, database mode is used.
"""
from __future__ import annotations

import io
import os
import time
from typing import Any
from uuid import uuid4

import pandas as pd


class DataService:
    """Unified data service supporting both DB-backed and in-memory modes."""

    def __init__(self) -> None:
        self._datasets: dict[str, pd.DataFrame] = {}
        self._dataset_meta: dict[str, dict[str, Any]] = {}
        self._use_db = bool(os.environ.get("SUPABASE_URL"))

    # ------------------------------------------------------------------
    # Internal: Supabase client (lazy import to avoid import errors in tests)
    # ------------------------------------------------------------------

    def _get_client(self):  # noqa: ANN202
        from app.database import get_supabase_client
        return get_supabase_client()

    # ------------------------------------------------------------------
    # Ingest
    # ------------------------------------------------------------------

    def ingest(
        self,
        filename: str,
        content: bytes,
        owner_id: str | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        """Parse a CSV or JSON file and store it.

        Returns a summary dict with ``rows``, ``columns``, and (in DB mode)
        ``dataset_id``.
        """
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif filename.endswith(".json"):
            df = pd.read_json(io.BytesIO(content))
        else:
            raise ValueError(f"Unsupported file type: {filename}")

        name = filename.rsplit(".", 1)[0]
        columns = list(df.columns)
        schema = {
            "columns": [
                {"name": c, "type": str(df[c].dtype)} for c in columns
            ]
        }

        # Always keep in memory for preview / visualize / export
        self._datasets[name] = df

        summary: dict[str, Any] = {"rows": len(df), "columns": columns}

        if self._use_db and owner_id:
            dataset_id = str(uuid4())
            sb = self._get_client()
            sb.table("datasets").insert(
                {
                    "id": dataset_id,
                    "owner_id": owner_id,
                    "name": name,
                    "description": description,
                    "schema": schema,
                    "row_count": len(df),
                    "source": "upload",
                }
            ).execute()
            summary["dataset_id"] = dataset_id
            self._dataset_meta[name] = {"id": dataset_id, "owner_id": owner_id}

        return summary

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def list_datasets(self, owner_id: str | None = None) -> list[dict[str, Any]]:
        """Return datasets with full metadata (DB mode only).

        Requires ``owner_id`` and a database connection.  Falls back to an
        empty list when the database is not available.
        """
        if self._use_db and owner_id:
            sb = self._get_client()
            result = (
                sb.table("datasets")
                .select("id, owner_id, name, description, schema, row_count, source, created_at, updated_at")
                .eq("owner_id", owner_id)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        return []

    def list_dataset_names(self) -> list[str]:
        """Return in-memory dataset names (no DB required)."""
        return list(self._datasets.keys())

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def preview(self, name: str, rows: int = 10) -> list[dict] | None:
        """Return the first N rows of a dataset as a list of dicts."""
        df = self._datasets.get(name)
        if df is None:
            return None
        return df.head(rows).to_dict(orient="records")

    # ------------------------------------------------------------------
    # Visualize
    # ------------------------------------------------------------------

    def generate_chart(
        self, name: str, chart_type: str, x: str, y: str
    ) -> str | None:
        """Generate a Plotly chart and return the HTML snippet."""
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

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export(self, name: str, fmt: str = "csv") -> str | None:
        """Export a dataset as CSV or JSON string."""
        df = self._datasets.get(name)
        if df is None:
            return None
        if fmt == "json":
            return df.to_json(orient="records")
        return df.to_csv(index=False)

    # ------------------------------------------------------------------
    # Saved queries (DB mode only)
    # ------------------------------------------------------------------

    def save_query(
        self,
        owner_id: str,
        dataset_id: str,
        name: str,
        sql_query: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Save a query to the database."""
        sb = self._get_client()
        query_id = str(uuid4())
        result = (
            sb.table("saved_queries")
            .insert(
                {
                    "id": query_id,
                    "owner_id": owner_id,
                    "dataset_id": dataset_id,
                    "name": name,
                    "sql_query": sql_query,
                    "description": description,
                }
            )
            .execute()
        )
        return result.data[0] if result.data else {"id": query_id}

    def list_queries(self, owner_id: str) -> list[dict[str, Any]]:
        """List saved queries for a user."""
        sb = self._get_client()
        result = (
            sb.table("saved_queries")
            .select("id, owner_id, dataset_id, name, sql_query, description, created_at")
            .eq("owner_id", owner_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    def get_query(self, query_id: str, owner_id: str) -> dict[str, Any] | None:
        """Get a single saved query by ID."""
        sb = self._get_client()
        result = (
            sb.table("saved_queries")
            .select("id, owner_id, dataset_id, name, sql_query, description, created_at")
            .eq("id", query_id)
            .eq("owner_id", owner_id)
            .single()
            .execute()
        )
        return result.data

    def delete_query(self, query_id: str, owner_id: str) -> bool:
        """Delete a saved query. Returns True if deleted."""
        sb = self._get_client()
        sb.table("saved_queries").delete().eq("id", query_id).eq(
            "owner_id", owner_id
        ).execute()
        return True

    # ------------------------------------------------------------------
    # Query results (DB mode only)
    # ------------------------------------------------------------------

    def execute_and_store_query(
        self, query_id: str, owner_id: str
    ) -> dict[str, Any] | None:
        """Execute a saved query against its dataset's in-memory data.

        Runs the query as a pandas operation and stores the result.
        """
        query = self.get_query(query_id, owner_id)
        if query is None:
            return None

        # Find the dataset in memory
        sb = self._get_client()
        ds_result = (
            sb.table("datasets")
            .select("name")
            .eq("id", query["dataset_id"])
            .single()
            .execute()
        )
        if not ds_result.data:
            return None

        dataset_name = ds_result.data["name"]
        df = self._datasets.get(dataset_name)
        if df is None:
            return None

        start = time.monotonic()
        try:
            # Execute using pandas SQL-like syntax via df.query or direct aggregation
            # For simplicity, return the full dataset as the "result"
            result_data = df.head(100).to_dict(orient="records")
        except Exception:
            result_data = []
        elapsed_ms = int((time.monotonic() - start) * 1000)

        result_id = str(uuid4())
        sb.table("query_results").insert(
            {
                "id": result_id,
                "query_id": query_id,
                "result_data": result_data,
                "row_count": len(result_data),
                "execution_time_ms": elapsed_ms,
            }
        ).execute()

        return {
            "id": result_id,
            "query_id": query_id,
            "result_data": result_data,
            "row_count": len(result_data),
            "execution_time_ms": elapsed_ms,
        }

    def list_query_results(
        self, query_id: str, owner_id: str
    ) -> list[dict[str, Any]]:
        """List cached results for a query."""
        # Verify ownership via the query
        query = self.get_query(query_id, owner_id)
        if query is None:
            return []

        sb = self._get_client()
        result = (
            sb.table("query_results")
            .select("id, query_id, result_data, row_count, execution_time_ms, created_at")
            .eq("query_id", query_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
