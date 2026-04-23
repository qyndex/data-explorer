"""Integration tests for the /api/upload and /api/datasets routes."""
from __future__ import annotations

import io

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# POST /api/upload
# ---------------------------------------------------------------------------

class TestUploadFile:
    def test_upload_csv_returns_summary(self, client: TestClient) -> None:
        csv = b"a,b\n1,2\n3,4\n"
        files = {"file": ("test.csv", io.BytesIO(csv), "text/csv")}
        resp = client.post("/api/upload", files=files)
        assert resp.status_code == 200
        body = resp.json()
        assert body["filename"] == "test.csv"
        assert body["summary"]["rows"] == 2
        assert body["summary"]["columns"] == ["a", "b"]

    def test_upload_json_returns_summary(self, client: TestClient) -> None:
        data = b'[{"x":1,"y":2},{"x":3,"y":4}]'
        files = {"file": ("points.json", io.BytesIO(data), "application/json")}
        resp = client.post("/api/upload", files=files)
        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["rows"] == 2

    def test_upload_unsupported_extension_returns_400(self, client: TestClient) -> None:
        files = {"file": ("data.xlsx", io.BytesIO(b"dummy"), "application/octet-stream")}
        resp = client.post("/api/upload", files=files)
        assert resp.status_code == 400
        assert "Unsupported" in resp.json()["detail"]

    def test_upload_no_filename_returns_error(self, client: TestClient) -> None:
        # Send a file with an empty filename — rejected by validation (400 or 422)
        files = {"file": ("", io.BytesIO(b"a,b\n1,2\n"), "text/csv")}
        resp = client.post("/api/upload", files=files)
        assert resp.status_code in (400, 422)

    def test_upload_response_envelope_structure(self, client: TestClient) -> None:
        csv = b"col1,col2\nfoo,bar\n"
        files = {"file": ("envelope.csv", io.BytesIO(csv), "text/csv")}
        resp = client.post("/api/upload", files=files)
        body = resp.json()
        assert "filename" in body
        assert "summary" in body
        assert "rows" in body["summary"]
        assert "columns" in body["summary"]


# ---------------------------------------------------------------------------
# GET /api/datasets
# ---------------------------------------------------------------------------

class TestListDatasets:
    def test_empty_datasets_list(self, client: TestClient) -> None:
        resp = client.get("/api/datasets")
        assert resp.status_code == 200
        body = resp.json()
        assert "datasets" in body
        assert isinstance(body["datasets"], list)

    def test_datasets_after_upload(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/datasets")
        assert resp.status_code == 200
        assert "sample" in resp.json()["datasets"]

    def test_multiple_uploads_appear_in_list(self, client: TestClient) -> None:
        for name in ("alpha.csv", "beta.csv"):
            csv = b"x,y\n1,2\n"
            files = {"file": (name, io.BytesIO(csv), "text/csv")}
            client.post("/api/upload", files=files)

        datasets = client.get("/api/datasets").json()["datasets"]
        assert "alpha" in datasets
        assert "beta" in datasets


# ---------------------------------------------------------------------------
# GET /api/datasets/{name}/preview
# ---------------------------------------------------------------------------

class TestPreviewDataset:
    def test_preview_returns_data(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/datasets/sample/preview")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert isinstance(body["data"], list)
        assert len(body["data"]) > 0

    def test_preview_respects_rows_param(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/datasets/sample/preview?rows=2")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_preview_unknown_dataset_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/datasets/nonexistent/preview")
        assert resp.status_code == 404

    def test_preview_row_has_expected_keys(self, seeded_client: TestClient) -> None:
        resp = seeded_client.get("/api/datasets/sample/preview?rows=1")
        row = resp.json()["data"][0]
        # sample.csv has columns: name, age, score
        assert "name" in row
        assert "age" in row
        assert "score" in row
