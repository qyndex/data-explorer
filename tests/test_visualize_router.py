"""Integration tests for the /api/visualize and /api/export routes."""
from __future__ import annotations

import io

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# GET /api/visualize/{name}
# ---------------------------------------------------------------------------

class TestVisualizeDataset:
    def test_visualize_returns_chart_html(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/visualize/sample")
        assert resp.status_code == 200
        body = resp.json()
        assert "chart_html" in body
        assert isinstance(body["chart_html"], str)
        assert len(body["chart_html"]) > 0

    def test_visualize_bar_chart(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/visualize/sample?chart_type=bar&x=name&y=age")
        assert resp.status_code == 200
        assert "chart_html" in resp.json()

    def test_visualize_line_chart(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/visualize/sample?chart_type=line&x=name&y=score")
        assert resp.status_code == 200
        assert "chart_html" in resp.json()

    def test_visualize_scatter_chart(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/visualize/sample?chart_type=scatter&x=age&y=score")
        assert resp.status_code == 200
        assert "chart_html" in resp.json()

    def test_visualize_unknown_dataset_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/visualize/ghost_dataset")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    def test_visualize_default_axes_when_empty(self, seeded_client: TestClient) -> None:
        # x and y default to empty string — DataService picks first two columns
        resp = seeded_client.get("/api/visualize/sample?chart_type=bar")
        assert resp.status_code == 200
        body = resp.json()
        assert "chart_html" in body

    def test_visualize_response_envelope_structure(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/visualize/sample")
        body = resp.json()
        # Must have exactly the envelope key (never a bare HTML string)
        assert set(body.keys()) == {"chart_html"}


# ---------------------------------------------------------------------------
# GET /api/export/{name}
# ---------------------------------------------------------------------------

class TestExportDataset:
    def test_export_csv_format(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/export/sample?format=csv")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert body["format"] == "csv"
        assert isinstance(body["data"], str)
        assert "," in body["data"]  # CSV has commas

    def test_export_json_format(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/export/sample?format=json")
        assert resp.status_code == 200
        body = resp.json()
        assert body["format"] == "json"
        assert body["data"].startswith("[")

    def test_export_default_is_csv(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/export/sample")
        assert resp.status_code == 200
        body = resp.json()
        assert body["format"] == "csv"

    def test_export_unknown_dataset_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/export/ghost_dataset")
        assert resp.status_code == 404

    def test_export_csv_contains_header(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/export/sample?format=csv")
        data_str: str = resp.json()["data"]
        first_line = data_str.splitlines()[0]
        # sample.csv has name, age, score columns
        assert "name" in first_line
        assert "age" in first_line
        assert "score" in first_line

    def test_export_response_envelope_structure(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/export/sample?format=csv")
        body = resp.json()
        assert "data" in body
        assert "format" in body


# ---------------------------------------------------------------------------
# Full round-trip: upload → visualize → export
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_upload_then_visualize_then_export(self, client: TestClient) -> None:
        # 1. Upload a small CSV
        csv = b"product,sales,returns\nWidget,500,10\nGadget,320,5\nDoohickey,180,2\n"
        files = {"file": ("products.csv", io.BytesIO(csv), "text/csv")}
        upload_resp = client.post("/api/upload", files=files)
        assert upload_resp.status_code == 200
        assert upload_resp.json()["summary"]["rows"] == 3

        # 2. Confirm it's listed
        list_resp = client.get("/api/datasets")
        assert "products" in list_resp.json()["datasets"]

        # 3. Preview
        preview_resp = client.get("/api/datasets/products/preview?rows=2")
        assert preview_resp.status_code == 200
        assert len(preview_resp.json()["data"]) == 2

        # 4. Visualize
        viz_resp = client.get("/api/visualize/products?chart_type=bar&x=product&y=sales")
        assert viz_resp.status_code == 200
        assert viz_resp.json()["chart_html"]

        # 5. Export as JSON
        export_resp = client.get("/api/export/products?format=json")
        assert export_resp.status_code == 200
        assert "Widget" in export_resp.json()["data"]
