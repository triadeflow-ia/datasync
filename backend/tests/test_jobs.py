"""Testes dos endpoints de jobs."""
import io
import uuid
from unittest.mock import patch

import pytest

from app.models import Job


class TestCreateJob:
    def test_upload_csv(self, client, auth_headers):
        csv_content = b"Nome,Email,Telefone\nJoao,joao@test.com,85999991234"
        files = {"file": ("contatos.csv", io.BytesIO(csv_content), "text/csv")}
        with patch("app.routes_jobs.queue") as mock_queue:
            mock_queue.enqueue.return_value = None
            resp = client.post("/jobs", files=files, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["status"] == "queued"
        assert data["filename_original"] == "contatos.csv"

    def test_upload_invalid_extension(self, client, auth_headers):
        files = {"file": ("data.txt", io.BytesIO(b"hello"), "text/plain")}
        resp = client.post("/jobs", files=files, headers=auth_headers)
        assert resp.status_code == 400
        assert "xlsx ou .csv" in resp.json()["detail"]

    def test_upload_too_large(self, client, auth_headers):
        big_content = b"x" * (11 * 1024 * 1024)  # 11MB
        files = {"file": ("big.csv", io.BytesIO(big_content), "text/csv")}
        with patch("app.routes_jobs.queue") as mock_queue:
            resp = client.post("/jobs", files=files, headers=auth_headers)
        assert resp.status_code == 413

    def test_upload_requires_auth(self, client):
        files = {"file": ("test.csv", io.BytesIO(b"data"), "text/csv")}
        resp = client.post("/jobs", files=files)
        assert resp.status_code == 401


class TestGetJob:
    def test_get_job_success(self, client, auth_headers, db, test_user):
        user, _ = test_user
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            user_id=user.id,
            status="queued",
            filename_original="test.csv",
            file_path="/tmp/test.csv",
        )
        db.add(job)
        db.commit()

        resp = client.get(f"/jobs/{job_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == job_id
        assert data["status"] == "queued"

    def test_get_job_not_found(self, client, auth_headers):
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/jobs/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_job_invalid_id(self, client, auth_headers):
        resp = client.get("/jobs/not-a-uuid", headers=auth_headers)
        assert resp.status_code == 422


class TestDeleteJob:
    def test_delete_job_success(self, client, auth_headers, db, test_user):
        user, _ = test_user
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            user_id=user.id,
            status="done",
            filename_original="test.csv",
            file_path="/tmp/nonexistent.csv",
        )
        db.add(job)
        db.commit()

        resp = client.delete(f"/jobs/{job_id}", headers=auth_headers)
        assert resp.status_code == 204

        # Confirma que foi deletado
        resp2 = client.get(f"/jobs/{job_id}", headers=auth_headers)
        assert resp2.status_code == 404

    def test_delete_job_not_found(self, client, auth_headers):
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"/jobs/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_requires_auth(self, client):
        fake_id = str(uuid.uuid4())
        resp = client.delete(f"/jobs/{fake_id}")
        assert resp.status_code == 401


class TestListJobs:
    def test_list_empty(self, client, auth_headers):
        resp = client.get("/jobs", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["jobs"] == []

    def test_list_with_jobs(self, client, auth_headers, db, test_user):
        user, _ = test_user
        for i in range(3):
            job = Job(
                id=str(uuid.uuid4()),
                user_id=user.id,
                status="queued",
                filename_original=f"file{i}.csv",
                file_path=f"/tmp/file{i}.csv",
            )
            db.add(job)
        db.commit()

        resp = client.get("/jobs", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["jobs"]) == 3

    def test_list_requires_auth(self, client):
        resp = client.get("/jobs")
        assert resp.status_code == 401


class TestJobPreviewDownloadReport:
    def test_preview_not_done(self, client, auth_headers, db, test_user):
        user, _ = test_user
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            user_id=user.id,
            status="queued",
            filename_original="test.csv",
            file_path="/tmp/test.csv",
        )
        db.add(job)
        db.commit()

        resp = client.get(f"/jobs/{job_id}/preview", headers=auth_headers)
        assert resp.status_code == 409

    def test_download_not_done(self, client, auth_headers, db, test_user):
        user, _ = test_user
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            user_id=user.id,
            status="processing",
            filename_original="test.csv",
            file_path="/tmp/test.csv",
        )
        db.add(job)
        db.commit()

        resp = client.get(f"/jobs/{job_id}/download", headers=auth_headers)
        assert resp.status_code == 409

    def test_report_not_done(self, client, auth_headers, db, test_user):
        user, _ = test_user
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            user_id=user.id,
            status="failed",
            filename_original="test.csv",
            file_path="/tmp/test.csv",
        )
        db.add(job)
        db.commit()

        resp = client.get(f"/jobs/{job_id}/report", headers=auth_headers)
        assert resp.status_code == 409
