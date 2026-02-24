"""Unit tests for the /health HTTP endpoint.

Validates the health check endpoint behaviour using Flask's built-in test
client.  The test suite covers HTTP status code, content type, JSON response
body, and HTTP method enforcement to ensure the endpoint conforms to the
liveness-probe contract defined in the Agent Action Plan.

Test cases:
    - test_health_endpoint_returns_200: GET /health → 200
    - test_health_endpoint_returns_json: Content-Type is application/json
    - test_health_endpoint_returns_correct_body: Body is {"health": "ok"}
    - test_health_endpoint_method_not_allowed: POST /health → 405
"""

import pytest

from app import app


@pytest.fixture
def client():
    """Provide a Flask test client configured in TESTING mode.

    Sets ``app.config["TESTING"]`` to ``True`` so that exceptions propagate
    to the test runner rather than being swallowed by Flask's error handlers.
    The test client is yielded as a context-managed resource, ensuring proper
    teardown after each test.

    Yields:
        flask.testing.FlaskClient: A test client bound to the Flask
        application with TESTING mode enabled.
    """
    app.config["TESTING"] = True
    with app.test_client() as testing_client:
        yield testing_client


def test_health_endpoint_returns_200(client):
    """Verify that GET /health returns HTTP 200 OK.

    A successful liveness probe must receive a 200 status code to confirm
    the application server is operational and accepting connections.
    """
    response = client.get("/health")
    assert response.status_code == 200


def test_health_endpoint_returns_json(client):
    """Verify that GET /health returns application/json content type.

    The health endpoint uses Flask's ``jsonify()`` which sets the response
    content type to ``application/json`` automatically.  Monitoring tools
    and load balancers rely on this header to parse the response correctly.
    """
    response = client.get("/health")
    assert response.content_type == "application/json"


def test_health_endpoint_returns_correct_body(client):
    """Verify that GET /health returns the exact JSON body {"health": "ok"}.

    The liveness contract requires the response to contain exactly the key
    ``"health"`` with value ``"ok"``.  No additional fields, nested objects,
    or metadata are permitted.
    """
    response = client.get("/health")
    data = response.get_json()
    assert data == {"health": "ok"}


def test_health_endpoint_method_not_allowed(client):
    """Verify that POST /health returns HTTP 405 Method Not Allowed.

    The /health route is registered for GET requests only.  Flask's default
    behaviour returns 405 for any HTTP method not explicitly allowed on a
    route, ensuring clients cannot accidentally mutate state via the health
    check endpoint.
    """
    response = client.post("/health")
    assert response.status_code == 405
