from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_live_endpoint_reports_release_candidate():
    r = client.get('/live')
    assert r.status_code == 200
    assert r.json()['version'] == '1.0.0-rc1'


def test_public_stats_are_non_negative():
    r = client.get('/api/v1/public/stats')
    assert r.status_code == 200
    body = r.json()
    assert all(isinstance(body[key], int) and body[key] >= 0 for key in body)


def test_public_search_returns_only_public_content_shape():
    r = client.get('/api/v1/public/search', params={'q': 'ডেমো'})
    assert r.status_code == 200
    body = r.json()
    assert 'results' in body
    assert all({'type', 'id', 'title_bn', 'href'}.issubset(item) for item in body['results'])
