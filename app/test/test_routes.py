import pytest
from flask import Flask
from app import create_app, db
from flask.testing import FlaskClient


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'mi_clave_secreta'

@pytest.fixture
def db_session(app):
    with app.app_context():
        session = db.session
        yield session
        session.remove()

@pytest.fixture
def app():
    app = create_app()
    app.config.from_object(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    return app

@pytest.fixture
def client(app) -> FlaskClient:
    return app.test_client()

@pytest.fixture
def sample_payload():
    return {
        "email": "test@example.com",
        "app_uuid": "123e4567-e89b-12d3-a456-426614174000",
        "blocked_reason": "Testing purpose"
    }

# Test de creación de blacklist con un token válido
def test_create_blacklist_success(client, sample_payload):
    headers = {
        "Authorization": f"Bearer blacklist-secret-token-2024",
        "X-Forwarded-For": "1.2.3.4"
    }
    response = client.post(
        "/blacklists", 
        json=sample_payload,
        headers=headers
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["email"] == sample_payload["email"]

# Test de blacklist con campos faltantes
def test_create_blacklist_missing_fields(client):
    headers = {"Authorization": f"Bearer blacklist-secret-token-2024"}
    response = client.post("/blacklists", json={"email": "test@example.com"}, headers=headers)
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "Faltan campos requeridos" in data["message"]

# Test de no encontrar un email en blacklist
def test_check_blacklist_not_found(client):
    headers = {"Authorization": f"Bearer blacklist-secret-token-2024"}
    response = client.get("/blacklists/nonexistent@example.com", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "El email no está en la lista negra" in data["message"]
