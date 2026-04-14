"""Submodules package initializer.

Re-exports the health Flask Blueprint for convenient package-level access.
This enables app.py to import via 'from submodules import health_bp'
instead of the full module path 'from submodules.health_handler import health_bp'.
"""

from submodules.health_handler import health_bp
