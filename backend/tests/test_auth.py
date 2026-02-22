"""Testes dos endpoints de autenticação."""
import pytest


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "email": "new@example.com",
            "password": "senha123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data

    def test_register_duplicate_email(self, client, test_user):
        resp = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "senha123",
        })
        assert resp.status_code == 400
        assert "já cadastrado" in resp.json()["detail"]

    def test_register_short_password(self, client):
        resp = client.post("/auth/register", json={
            "email": "new@example.com",
            "password": "123",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "senha123",
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client, test_user):
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "test123456",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        resp = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrong-password",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        resp = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "senha123",
        })
        assert resp.status_code == 401
