"""
Fixtures compartilhadas para testes.
Usa SQLite in-memory para isolar testes do Postgres de produção.
"""
import os
import uuid

# DEVE estar antes de qualquer import do app
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["JWT_SECRET"] = "test-secret-key"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db import Base, get_db
from app.models import User, Job
from app.auth import hash_password, create_access_token
from app.main import app


# Engine SQLite in-memory para testes
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Cria e limpa tabelas antes/depois de cada teste."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    """Sessão de banco para uso direto nos testes."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """TestClient do FastAPI."""
    return TestClient(app)


@pytest.fixture
def test_user(db):
    """Cria um usuário de teste e retorna (user, token)."""
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email="test@example.com",
        password_hash=hash_password("test123456"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return user, token


@pytest.fixture
def auth_headers(test_user):
    """Headers com Authorization Bearer para requests autenticados."""
    _, token = test_user
    return {"Authorization": f"Bearer {token}"}
