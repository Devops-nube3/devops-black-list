import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from app.routes import blacklist_bp, health_bp, create_blacklist, check_blacklist
from app.models import Blacklist
from datetime import datetime, UTC

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['API_TOKEN'] = 'blacklist-secret-token-2024'  # Configurar el token de prueba
    
    # Mock del decorador require_token
    with patch('app.auth.require_token') as mock_require_token:
        def mock_decorator(f):
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)
            wrapper.__name__ = f.__name__
            return wrapper
        mock_require_token.side_effect = mock_decorator
        
        app.register_blueprint(blacklist_bp, url_prefix='/blacklist')
        app.register_blueprint(health_bp, url_prefix='/health')
    
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_db():
    with patch('app.routes.db') as mock:
        # Configurar el mock para la sesión
        mock_session = MagicMock()
        mock.session = mock_session
        
        # Configurar el mock para la consulta
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = MagicMock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_filter
        mock_filter.first.return_value = mock_first
        
        yield mock

# @pytest.fixture
# def mock_blacklist_query():
#     with patch('app.models.Blacklist.query') as mock:
#         # Configurar el mock para la consulta
#         mock_filter = MagicMock()
#         mock_first = MagicMock()
        
#         mock.filter_by.return_value = mock_filter
#         mock_filter.first.return_value = mock_first
        
#         yield mock

@pytest.fixture
def mock_blacklist_query(app):
    with app.app_context():
        with patch.object(Blacklist, 'query') as mock_query:
            yield mock_query

@pytest.fixture
def mock_blacklist():
    with patch('app.routes.Blacklist') as mock:
        yield mock

def test_create_blacklist_success(client, mock_db, mock_blacklist):
    # Datos de prueba
    test_data = {
        'email': 'test@example.com',
        'app_uuid': '12345',
        'blocked_reason': 'spam'
    }
    
    response = client.post('/blacklist', 
                         json=test_data,
                         headers={'Authorization': 'Bearer blacklist-secret-token-2024'})
    
    
def test_create_blacklist_missing_fields(client):
    # Datos incompletos
    test_data = {
        'email': 'test@example.com',
        'app_uuid': '12345'
        # Falta blocked_reason
    }
    
    response = client.post('/blacklist', 
                         json=test_data,
                         headers={'Authorization': 'Bearer blacklist-secret-token-2024'})
    
    assert response.status_code == 400
    assert response.json['success'] is False
    assert response.json['message'] == 'Faltan campos requeridos'

def test_check_blacklist_found(client, mock_blacklist_query):
    # Mock de la consulta
    mock_entry = MagicMock()
    mock_entry.email = 'test@example.com'
    mock_entry.blocked_reason = 'spam'
    mock_entry.app_uuid = '12345'
    mock_entry.created_at = datetime.now(UTC)
    mock_entry.request_ip = '192.168.1.1'
    mock_entry.request_time = datetime.now(UTC)
    
    # Configurar el mock para devolver el entry
    mock_blacklist_query.filter_by.return_value.first.return_value = mock_entry
    
    response = client.get('/blacklist/test@example.com',
                        headers={'Authorization': 'Bearer blacklist-secret-token-2024'})
    
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['is_blacklisted'] is True
    assert response.json['data']['email'] == 'test@example.com'

def test_check_blacklist_not_found(client, mock_blacklist_query):
    # Configurar el mock para devolver None
    mock_blacklist_query.filter_by.return_value.first.return_value = None
    
    response = client.get('/blacklist/test@example.com',
                        headers={'Authorization': 'Bearer blacklist-secret-token-2024'})
    
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['is_blacklisted'] is False
    assert response.json['message'] == 'El email no está en la lista negra'

def test_health_check(client):
    response = client.get('/health/')
    
    assert response.status_code == 200
    assert response.json['message'] == 'API running' 