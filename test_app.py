import pytest
from app import app
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Тест 1: Перевіряємо головну сторінку


def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Task Tracker API" in response.data

# Тест 2: Перевіряємо ендпоінт health/alive


def test_health_alive(client):
    response = client.get('/health/alive')
    assert response.status_code == 200
    assert b"OK" in response.data

# Тест 3: Перевіряємо health/ready


@patch('app.get_db_connection')
def test_health_ready_success(mock_get_db, client):
    # Налаштовуємо фейкове з'єднання
    mock_conn = MagicMock()
    mock_get_db.return_value = mock_conn

    response = client.get('/health/ready')
    assert response.status_code == 200
    assert b"OK" in response.data
    mock_conn.close.assert_called_once()  # Перевіряємо, чи закрилося з'єднання

# Тест 4: Перевіряємо health/ready


@patch('app.get_db_connection')
def test_health_ready_fail(mock_get_db, client):
    # Симулюємо падіння бази
    mock_get_db.side_effect = Exception("Fake DB Down")

    response = client.get('/health/ready')
    assert response.status_code == 500
    assert b"Database error" in response.data
