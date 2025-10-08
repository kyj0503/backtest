"""
Backtesting API Server Application
"""

__version__ = "1.1.2"
__description__ = "FastAPI server for backtesting.py library"

# Expose api package for callers importing `app.api`
from . import api  # noqa: F401
