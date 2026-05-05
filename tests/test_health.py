"""Unit tests for the /health HTTP endpoint.

Tests use Flask's built-in test client to make HTTP requests against
the Flask application without starting a real server, enabling fast
and isolated unit testing of the health check endpoint defined in
submodules/health_handler.py.

Test coverage includes:
    - HTTP 200 status code on GET /health
    - application/json content type in the response
    - Exact JSON body {"health": "ok"}
    - HTTP 405 Method Not Allowed on POST /health
    - Standard security headers attached to every response
    - Server header override (no Werkzeug version disclosure)
    - Security headers also applied to error responses (404, 405)
"""

import pytest

from app import app


@pytest.fixture
def client():
    """Create a Flask test client for endpoint testing.

    Configures the Flask application in testing mode, which propagates
    exceptions instead of handling them with error pages, and yields
    a test client instance that can make HTTP requests to the
    application routes without a running server.

    Yields:
        flask.testing.FlaskClient: A test client bound to the Flask
            application, capable of sending GET, POST, and other
            HTTP method requests to registered routes.
    """
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint_returns_200(client):
    """Verify GET /health returns HTTP 200 OK status code.

    Confirms the health endpoint is reachable and responds with
    the standard success status code, indicating the application
    server is operational and accepting requests.

    Args:
        client: Flask test client fixture for making HTTP requests.
    """
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_returns_json(client):
    """Verify GET /health returns application/json content type.

    Confirms the health endpoint response includes the correct
    Content-Type header, ensuring clients can parse the response
    body as JSON. Flask's jsonify() sets this automatically.

    Args:
        client: Flask test client fixture for making HTTP requests.
    """
    response = client.get("/health")
    assert response.content_type == "application/json"


def test_health_endpoint_returns_correct_body(client):
    """Verify GET /health returns the exact JSON body {"health": "ok"}.

    Confirms the health endpoint response body contains the precise
    expected payload with string key "health" and string value "ok".
    No additional fields, no nested objects, no metadata — just the
    exact liveness indicator payload.

    Args:
        client: Flask test client fixture for making HTTP requests.
    """
    response = client.get("/health")
    data = response.get_json()
    assert data == {"health": "ok"}


def test_health_endpoint_method_not_allowed(client):
    """Verify POST /health returns HTTP 405 Method Not Allowed.

    Confirms the health endpoint rejects non-GET HTTP methods.
    Flask's default behavior returns 405 for methods not registered
    on a route, ensuring only GET requests are accepted by the
    health check endpoint.

    Args:
        client: Flask test client fixture for making HTTP requests.
    """
    response = client.post("/health")
    assert response.status_code == 405


def test_health_endpoint_sets_security_headers(client):
    """Verify the standard security headers are attached to /health.

    Confirms the @app.after_request handler applies the OWASP A05
    baseline security headers to the successful 200 OK response from
    the health endpoint. These headers harden the application against
    MIME sniffing, clickjacking, framed embedding, plaintext HTTP
    fallback, and intermediary caching of liveness data.

    Args:
        client: Flask test client fixture for making HTTP requests.
    """
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert (
        response.headers.get("Content-Security-Policy")
        == "default-src 'none'; frame-ancestors 'none'"
    )
    assert (
        response.headers.get("Strict-Transport-Security")
        == "max-age=31536000; includeSubDomains"
    )
    assert response.headers.get("Cache-Control") == "no-store"


def test_health_endpoint_server_header_override(client):
    """Verify the Server header is overridden to a generic value.

    Confirms the @app.after_request handler replaces the default
    Werkzeug Server header (e.g., 'Werkzeug/3.1.8 Python/3.12.13')
    with a non-disclosing generic value. This mitigates the version
    disclosure flagged by security scanners and reduces an attacker's
    ability to fingerprint the underlying framework and runtime.

    Args:
        client: Flask test client fixture for making HTTP requests.
    """
    response = client.get("/health")
    server_header = response.headers.get("Server", "")
    assert server_header == "health-check"
    assert "Werkzeug" not in server_header
    assert "Python" not in server_header


def test_security_headers_applied_to_404(client):
    """Verify security headers are attached even to 404 error responses.

    Confirms the @app.after_request handler runs for client error
    responses, not just successful responses. Flask's built-in 404
    handler must also receive the standard security header set, so
    that probing attempts (which often produce 404s) do not bypass
    the application's defense-in-depth posture.

    Args:
        client: Flask test client fixture for making HTTP requests.
    """
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Cache-Control") == "no-store"
    assert response.headers.get("Server") == "health-check"


def test_security_headers_applied_to_405(client):
    """Verify security headers are attached to 405 Method Not Allowed responses.

    Confirms the @app.after_request handler runs for method-not-allowed
    responses, ensuring even rejected method probes (POST /health,
    DELETE /health, etc.) carry the standard security header set.

    Args:
        client: Flask test client fixture for making HTTP requests.
    """
    response = client.post("/health")
    assert response.status_code == 405
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Cache-Control") == "no-store"
    assert response.headers.get("Server") == "health-check"
