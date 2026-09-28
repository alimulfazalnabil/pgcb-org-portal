from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_and_ready_endpoints():
    health = client.get('/health')
    assert health.status_code == 200
    data = health.json()
    assert data['status'] == 'ok'
    assert data['database'] == 'connected'
    assert data['version'] == '1.0.0-rc1'

    v1_health = client.get('/api/v1/health')
    assert v1_health.status_code == 200
    assert v1_health.json()['database'] == 'connected'

    ready = client.get('/ready')
    assert ready.status_code == 200
    assert ready.json()['status'] == 'ready'


def test_public_cms_and_directory_endpoints():
    for path in (
        '/api/v1/public/home',
        '/api/v1/public/notices',
        '/api/v1/public/circulars',
        '/api/v1/public/events',
        '/api/v1/public/documents',
        '/api/v1/public/committee',
        '/api/v1/public/circles',
        '/api/v1/public/directory',
    ):
        res = client.get(path)
        assert res.status_code == 200, f'Failed endpoint {path}: {res.text}'
