from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_endpoint_is_available_in_test_environment():
    response = client.get('/metrics')
    assert response.status_code == 200
    assert 'pgcb_http_requests_total' in response.text


def test_readiness_reports_database():
    response = client.get('/ready')
    assert response.status_code == 200
    assert response.json()['database'] == 'ok'
