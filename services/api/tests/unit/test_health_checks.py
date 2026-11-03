from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_live_endpoint():
    res = client.get("/live")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "alive"
    assert data["service"] == "pgcb-api"


def test_health_endpoint_healthy_db():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["service"] == "pgcb-api"


def test_health_endpoint_degraded_db():
    with patch("app.main.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Connection lost to database")
        mock_session.return_value = mock_db

        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "degraded"
        assert data["database"] == "unavailable"
        mock_db.close.assert_called_once()


def test_ready_endpoint_healthy_db():
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "ok"


def test_ready_endpoint_failing_db():
    with patch("app.main.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Database timeout")
        mock_session.return_value = mock_db

        res = client.get("/ready")
        assert res.status_code == 503
        data = res.json()
        assert data["status"] == "not_ready"
        assert data["database"] == "error"
        assert data["detail"] == "Database unavailable"
        mock_db.close.assert_called_once()
