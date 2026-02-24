"""Flask application entry point.

Creates the Flask WSGI application instance, registers the health
Blueprint from the submodules package, and provides the development
server entry point. The app instance is module-level accessible for
test client usage by tests/test_health.py.

Usage:
    python app.py

The Flask development server starts on http://localhost:5000 by default,
with the health endpoint available at GET /health.
"""

from flask import Flask

from submodules import health_bp

# Create the Flask application instance.
# __name__ is passed to Flask so it can locate the application root path
# and correctly resolve resources relative to this module.
app = Flask(__name__)

# Register the health Blueprint which adds the GET /health route.
# The Blueprint is defined in submodules/health_handler.py and
# re-exported via submodules/__init__.py for convenient access.
app.register_blueprint(health_bp)

if __name__ == "__main__":
    # Start the Flask development server when this file is executed directly.
    # debug=True enables the interactive debugger and auto-reloader,
    # providing detailed error pages and automatic restart on code changes.
    # The server listens on http://localhost:5000 by default.
    app.run(debug=True)
