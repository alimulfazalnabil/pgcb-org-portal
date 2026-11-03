from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_csrf_blocks_cookie_request_with_untrusted_origin():
    # Attempt a POST with session cookie and untrusted Origin header
    res = client.post(
        "/api/v1/auth/logout",
        cookies={settings.cookie_name: "dummy-token"},
        headers={"Origin": "https://evil-attacker-site.com"},
    )
    assert res.status_code == 403
    assert res.json() == {"detail": "CSRF origin verification failed"}
    assert res.headers["x-content-type-options"] == "nosniff"


def test_csrf_blocks_cookie_request_with_untrusted_referer():
    # Attempt a POST with session cookie and untrusted Referer header
    res = client.post(
        "/api/v1/auth/logout",
        cookies={settings.cookie_name: "dummy-token"},
        headers={"Referer": "https://evil-attacker-site.com/exploit.html"},
    )
    assert res.status_code == 403
    assert res.json() == {"detail": "CSRF origin verification failed"}


def test_csrf_permits_cookie_request_with_trusted_origin():
    # When legitimate frontend origin is supplied, CSRF check passes
    trusted = settings.frontend_url.rstrip("/")
    res = client.post(
        "/api/v1/auth/logout",
        cookies={settings.cookie_name: "dummy-token"},
        headers={"Origin": trusted},
    )
    # The request should pass the CSRF middleware and reach the application handler (returning 200 or 401)
    assert res.status_code != 403


def test_csrf_permits_bearer_token_with_any_origin():
    # Bearer token auth in Authorization header is immune to browser ambient CSRF
    res = client.post(
        "/api/v1/auth/logout",
        headers={
            "Authorization": "Bearer some-bearer-token",
            "Origin": "https://third-party-client.com",
        },
    )
    # Reaches handler without 403 CSRF rejection
    assert res.status_code != 403


def test_csrf_permits_safe_get_methods():
    # GET requests are safe and not blocked by CSRF origin verification
    res = client.get(
        "/health",
        cookies={settings.cookie_name: "dummy-token"},
        headers={"Origin": "https://arbitrary-site.com"},
    )
    assert res.status_code == 200
