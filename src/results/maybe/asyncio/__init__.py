"""Asynchronous Maybe implementation - AsyncMaybe with async operations.

This module provides AsyncMaybe[T] for handling async/await workflows:
- AsyncMaybe: Unified type wrapping Awaitable[Maybe[T]]
- Supports async transformations: map_async, and_then_async, or_else_async
- Short-circuits naturally on Nothing
- Preserves context chain for diagnostic information
"""

from __future__ import annotations

from .maybe import AsyncMaybe

__all__ = ["AsyncMaybe"]
