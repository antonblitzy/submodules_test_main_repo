"""Flask application entry point.

Creates the WSGI web application instance, registers the health
Blueprint from the submodules package, and provides a development
server entry point. The app object is module-level accessible for
test client usage via 'from app import app'.

This file contains NO route definitions — all route handlers reside
in the submodules package (submodules/health_handler.py).
"""

from flask import Flask
from submodules import health_bp

app = Flask(__name__)
app.register_blueprint(health_bp)

if __name__ == "__main__":
    app.run(debug=True)
