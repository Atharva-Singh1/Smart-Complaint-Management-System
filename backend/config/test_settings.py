"""Explicit local fallback only; CI uses config.settings with PostgreSQL and Redis."""

from .settings import *  # noqa: F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
