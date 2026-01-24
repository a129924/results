"""Async Result implementations.

This module provides AsyncOk and AsyncErr, which are awaitable variants of the
synchronous Result type. They enable async/await workflows while maintaining
LIFO context chain semantics identical to their sync counterparts.
"""

__all__ = ["AsyncOk", "AsyncErr"]
