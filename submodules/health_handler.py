"""Health endpoint handler module.

Defines a Flask Blueprint with a GET /health route that returns
a JSON liveness response. This module is the core implementation
of the health check feature and is designed to be registered with
any Flask application instance via Blueprint registration.

The handler returns {"health": "ok"} with HTTP 200 and
application/json content type to confirm the server is operational.
"""

from flask import Blueprint, jsonify

# Flask Blueprint for health check routing.
# Name "health" is used internally by Flask for endpoint resolution.
# This instance is imported by submodules/__init__.py and registered
# by app.py via app.register_blueprint(health_bp).
health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health():
    """Handle GET /health requests.

    Returns a JSON response confirming the application server is
    operational. This serves as a standard liveness probe endpoint
    for monitoring tools, load balancers, and orchestration systems.

    Returns:
        tuple: A (response, status_code) tuple where response is a
            Flask Response object with JSON body {"health": "ok"}
            and content type application/json, and status_code is 200.
    """
    return jsonify({"health": "ok"}), 200
