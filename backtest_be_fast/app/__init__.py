"""
Backtesting API Server Application
"""

__version__ = "1.0.0"
__description__ = "FastAPI server for backtesting.py library"

# Expose api package so tests can access `app.api` via attribute lookup
from . import api  # noqa: F401
