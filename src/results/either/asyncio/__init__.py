"""Async implementation of Either type.

Exports:
    - AsyncEither: Awaitable wrapper for Either[L, R] with async methods
"""

from .either import AsyncEither

__all__ = ["AsyncEither"]
