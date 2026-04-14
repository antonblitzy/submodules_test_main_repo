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
