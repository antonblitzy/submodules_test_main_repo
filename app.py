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
from werkzeug.serving import WSGIRequestHandler

from submodules import health_bp

# Override the Werkzeug development server version string to prevent
# disclosing exact Werkzeug and Python versions in the HTTP Server header.
# Without this, the development server emits "Werkzeug/<ver> Python/<ver>"
# at the transport layer, regardless of application-level header overrides.
# Both server_version and sys_version must be set to fully suppress version
# information (BaseHTTPRequestHandler.version_string concatenates both).
WSGIRequestHandler.server_version = "Flask"
WSGIRequestHandler.sys_version = ""

# Create the Flask application instance.
# __name__ is passed to Flask so it can locate the application root path
# and correctly resolve resources relative to this module.
app = Flask(__name__)

# Register the health Blueprint which adds the GET /health route.
# The Blueprint is defined in submodules/health_handler.py and
# re-exported via submodules/__init__.py for convenient access.
app.register_blueprint(health_bp)


@app.after_request
def set_security_headers(response):
    """Add standard security headers to every HTTP response.

    Hardens the application against common web vulnerabilities including
    clickjacking (X-Frame-Options), MIME-type sniffing (X-Content-Type-Options),
    cross-site scripting (X-XSS-Protection, Content-Security-Policy), and
    information disclosure (Server header override, Referrer-Policy).
    Cache-Control and Strict-Transport-Security are set to prevent sensitive
    response caching and enforce secure transport respectively.

    Args:
        response: The Flask Response object to augment with security headers.

    Returns:
        The same Response object with security headers applied.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Suppress the default Werkzeug/Python version disclosure to reduce
    # the information available to potential attackers performing reconnaissance.
    response.headers["Server"] = "Flask"
    return response


if __name__ == "__main__":
    # Start the Flask development server when this file is executed directly.
    # debug=False prevents the Werkzeug interactive debugger and console
    # from being accessible, avoiding potential arbitrary code execution
    # if the server is network-reachable.  For development convenience,
    # set the FLASK_DEBUG environment variable instead of hardcoding True.
    # The server listens on http://localhost:5000 by default.
    app.run(debug=False)
