"""Codex AccMgr package."""

from .constants import APP_VERSION

__all__ = ["APP_VERSION", "__version__"]

__version__ = APP_VERSION.lstrip("v")
