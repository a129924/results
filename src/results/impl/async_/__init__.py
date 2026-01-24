"""Async Result implementations.

This module provides AsyncResult, an awaitable wrapper for Result[T, E]
that enables async/await workflows while maintaining LIFO context chain
semantics identical to synchronous Result types.
"""

from .result import AsyncResult

__all__ = ["AsyncResult"]
