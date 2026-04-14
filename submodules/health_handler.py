"""Health endpoint handler module.

Defines a Flask Blueprint with a /health GET route that returns
a JSON liveness response. This module is the core handler for
the health check endpoint, designed to confirm the application
server is operational.

The Blueprint is imported and registered by the main Flask
application in app.py via the submodules package.
"""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health():
    """Health check endpoint handler.

    Returns a JSON response indicating the application is running
    and responsive. Used as a standard liveness probe by monitoring
    tools, load balancers, and orchestration systems.

    Returns:
        tuple: A tuple of (Response, int) where the Response contains
            the JSON body {"health": "ok"} with application/json
            content type, and the int is the HTTP 200 status code.
    """
    return jsonify({"health": "ok"}), 200
