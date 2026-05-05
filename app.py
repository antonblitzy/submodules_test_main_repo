"""Flask application entry point.

Creates the WSGI web application instance, registers the health
Blueprint from the submodules package, and provides a development
server entry point. The app object is module-level accessible for
test client usage via 'from app import app'.

This file contains NO route definitions — all route handlers reside
in the submodules package (submodules/health_handler.py).

Application-level concerns handled here:
    - Blueprint registration (route delegation to submodules)
    - Security response headers (defense-in-depth via @after_request)
    - Server header override (avoid Werkzeug/Python version disclosure)
    - Debug mode is OFF by default; opt-in via FLASK_DEBUG env var
      (prevents Werkzeug interactive debugger console exposure)
"""

import os

from flask import Flask
from werkzeug.serving import WSGIRequestHandler

from submodules import health_bp

app = Flask(__name__)
app.register_blueprint(health_bp)


@app.after_request
def set_security_headers(response):
    """Apply standard security headers to every HTTP response.

    Implements OWASP A05 (Security Misconfiguration) defense-in-depth
    by attaching a baseline set of security headers to all responses
    produced by this Flask application — including success responses
    (e.g., 200 from /health), client errors (e.g., 404, 405), and any
    future endpoints that may be registered.

    Headers set:
        X-Content-Type-Options: nosniff
            Prevents browsers from MIME-sniffing the response away from
            the declared Content-Type, mitigating drive-by download and
            content-type-confusion attacks.

        X-Frame-Options: DENY
            Prevents the response from being rendered in a <frame>,
            <iframe>, <embed>, or <object>, mitigating clickjacking.
            DENY is appropriate because health endpoints are never
            intended for browser display.

        Content-Security-Policy: default-src 'none'; frame-ancestors 'none'
            Strict CSP suitable for a JSON API endpoint with no client
            scripts, styles, or framed embedding. frame-ancestors 'none'
            provides a modern equivalent to X-Frame-Options: DENY.

        Strict-Transport-Security: max-age=31536000; includeSubDomains
            Instructs HSTS-aware clients to use HTTPS only for one year
            (and across all subdomains). The header is harmless over
            plain HTTP and protects clients once the service is fronted
            by a TLS-terminating reverse proxy.

        Cache-Control: no-store
            Ensures health responses are not cached by intermediaries,
            so liveness checks always reflect the live application
            state rather than stale or proxied results.

        Server: health-check
            Replaces any default Server header (e.g., from Werkzeug or
            a downstream WSGI server) with a non-disclosing generic
            value. Combined with the WSGIRequestHandler subclass below,
            this guarantees the Werkzeug/Python version string is never
            present in the Server header.

    Args:
        response: The Flask Response object about to be returned to
            the client. Modified in place by setting headers.

    Returns:
        flask.Response: The same response object with security
            headers applied.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; frame-ancestors 'none'"
    )
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Server"] = "health-check"
    return response


class _NoVersionDisclosureRequestHandler(WSGIRequestHandler):
    """WSGI request handler that suppresses Werkzeug's default Server header.

    Werkzeug's stock WSGIRequestHandler inherits send_response() from
    BaseHTTPRequestHandler, which automatically writes a Server header
    of the form 'Werkzeug/<version> Python/<version>' BEFORE the Flask
    application's @after_request handler runs. This results in the
    framework and runtime versions being disclosed on every response,
    which aids attacker reconnaissance and was flagged by automated
    security scanners.

    By overriding send_response() to skip the Server header (while
    preserving the Date header and all other standard behavior), this
    subclass ensures the only Server header on the wire is the clean
    'Server: health-check' value set by the Flask @after_request
    handler — eliminating both the duplicate header and the version
    disclosure in a single place.

    The WSGI handler is wired into the development server via the
    request_handler parameter to app.run(). It has no effect on the
    Flask test client (which does not use this WSGI server layer),
    so unit tests continue to exercise only the @after_request path.
    """

    def send_response(self, code, message=None):
        """Send the HTTP response status line and standard headers.

        Mirrors BaseHTTPRequestHandler.send_response() exactly, except
        the 'Server' header is intentionally omitted to prevent
        framework/runtime version disclosure. The 'Date' header is
        still emitted to remain compliant with HTTP/1.1 RFC 7231 §7.1.1.2.

        Args:
            code: The HTTP status code to send (e.g., 200, 404).
            message: Optional reason phrase. When None, the default
                phrase associated with the status code is used.
        """
        self.log_request(code)
        self.send_response_only(code, message)
        # Intentionally omit: self.send_header("Server", self.version_string())
        self.send_header("Date", self.date_time_string())


if __name__ == "__main__":
    # Debug mode is OFF by default to prevent exposure of the Werkzeug
    # interactive debugger console at /console (a known RCE vector when
    # combined with stdout/log access). Opt in only when explicitly
    # requested via the FLASK_DEBUG environment variable, e.g.:
    #     FLASK_DEBUG=true python app.py
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(
        debug=debug_mode,
        request_handler=_NoVersionDisclosureRequestHandler,
    )
