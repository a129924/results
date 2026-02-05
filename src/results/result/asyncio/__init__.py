"""Result async implementation - AsyncResult wrapper.

This module implements the AsyncResult type for non-blocking Result operations.

Exported:
    AsyncResult: Awaitable Result wrapper
"""

from results.result.asyncio.result import AsyncResult

__all__ = ["AsyncResult"]
