"""Unit tests for DataService — no HTTP layer."""
from __future__ import annotations

import io
import textwrap

import pytest

from app.services.data_service import DataService


CSV_BYTES = textwrap.dedent(
    """\
    city,population,area
    London,9000000,1572
    Paris,2141000,105
    Berlin,3700000,892
    """
).encode()

JSON_BYTES = b'[{"x":1,"y":10},{"x":2,"y":20},{"x":3,"y":30}]'


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------

class TestIngest:
    def test_ingest_csv_returns_summary(self, data_service: DataService) -> None:
        summary = data_service.ingest("cities.csv", CSV_BYTES)
        assert summary["rows"] == 3
        assert set(summary["columns"]) == {"city", "population", "area"}

    def test_ingest_json_returns_summary(self, data_service: DataService) -> None:
        summary = data_service.ingest("points.json", JSON_BYTES)
        assert summary["rows"] == 3
        assert "x" in summary["columns"]
        assert "y" in summary["columns"]

    def test_ingest_unsupported_extension_raises(self, data_service: DataService) -> None:
        with pytest.raises(ValueError, match="Unsupported file type"):
            data_service.ingest("data.xlsx", b"dummy")

    def test_ingest_stores_dataset_by_stem(self, data_service: DataService) -> None:
        data_service.ingest("cities.csv", CSV_BYTES)
        assert "cities" in data_service.list_dataset_names()

    def test_ingest_overwrites_existing_dataset(self, data_service: DataService) -> None:
        data_service.ingest("cities.csv", CSV_BYTES)
        new_csv = b"city,pop\nRome,4000000\n"
        data_service.ingest("cities.csv", new_csv)
        preview = data_service.preview("cities")
        assert preview is not None
        assert len(preview) == 1
        assert preview[0]["city"] == "Rome"


# ---------------------------------------------------------------------------
# list_datasets
# ---------------------------------------------------------------------------

class TestListDatasets:
    def test_empty_initially(self, data_service: DataService) -> None:
        assert data_service.list_dataset_names() == []

    def test_lists_after_ingest(self, data_service: DataService) -> None:
        data_service.ingest("cities.csv", CSV_BYTES)
        data_service.ingest("points.json", JSON_BYTES)
        names = data_service.list_dataset_names()
        assert "cities" in names
        assert "points" in names

    def test_returns_list_type(self, data_service: DataService) -> None:
        assert isinstance(data_service.list_dataset_names(), list)


# ---------------------------------------------------------------------------
# preview
# ---------------------------------------------------------------------------

class TestPreview:
    def test_preview_returns_rows(self, data_service: DataService) -> None:
        data_service.ingest("cities.csv", CSV_BYTES)
        rows = data_service.preview("cities")
        assert rows is not None
        assert len(rows) == 3
        assert isinstance(rows[0], dict)

    def test_preview_respects_row_limit(self, data_service: DataService) -> None:
        data_service.ingest("cities.csv", CSV_BYTES)
        rows = data_service.preview("cities", rows=2)
        assert rows is not None
        assert len(rows) == 2

    def test_preview_unknown_dataset_returns_none(self, data_service: DataService) -> None:
        assert data_service.preview("nonexistent") is None

    def test_preview_default_ten_rows(self, data_service: DataService) -> None:
        # Build a CSV with 15 rows
        header = "id,val\n"
        body = "".join(f"{i},{i*10}\n" for i in range(15))
        data_service.ingest("big.csv", (header + body).encode())
        rows = data_service.preview("big")
        assert rows is not None
        assert len(rows) == 10


# ---------------------------------------------------------------------------
# generate_chart
# ---------------------------------------------------------------------------

class TestGenerateChart:
    def test_chart_returns_html_string(self, data_service: DataService) -> None:
        data_service.ingest("cities.csv", CSV_BYTES)
        html = data_service.generate_chart("cities", "bar", "city", "population")
        assert html is not None
        assert "<div" in html or "<p>" in html  # plotly div or error fallback

    def test_chart_unknown_dataset_returns_none(self, data_service: DataService) -> None:
        result = data_service.generate_chart("ghost", "bar", "x", "y")
        assert result is None

    def test_chart_uses_first_columns_when_axes_empty(self, data_service: DataService) -> None:
        data_service.ingest("points.json", JSON_BYTES)
        html = data_service.generate_chart("points", "line", "", "")
        assert html is not None

    def test_chart_unsupported_type_falls_back_to_bar(self, data_service: DataService) -> None:
        data_service.ingest("cities.csv", CSV_BYTES)
        # Should not raise; falls back to px.bar
        html = data_service.generate_chart("cities", "heatmap", "city", "population")
        assert html is not None


# ---------------------------------------------------------------------------
# export
# ---------------------------------------------------------------------------

class TestExport:
    def test_export_csv(self, data_service: DataService) -> None:
        data_service.ingest("cities.csv", CSV_BYTES)
        result = data_service.export("cities", "csv")
        assert result is not None
        assert "London" in result
        assert "," in result

    def test_export_json(self, data_service: DataService) -> None:
        data_service.ingest("cities.csv", CSV_BYTES)
        result = data_service.export("cities", "json")
        assert result is not None
        assert "London" in result
        assert result.startswith("[")

    def test_export_unknown_dataset_returns_none(self, data_service: DataService) -> None:
        assert data_service.export("ghost", "csv") is None

    def test_export_default_is_csv(self, data_service: DataService) -> None:
        data_service.ingest("cities.csv", CSV_BYTES)
        result = data_service.export("cities")
        assert result is not None
        assert "," in result
