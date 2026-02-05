"""Result monad implementation - both sync and async variants.

This package provides the Result type family with synchronous and asynchronous support.

Exported:
    Ok: Success variant
    Err: Failure variant
    AsyncResult: Async Result wrapper
"""

from results.result.asyncio import AsyncResult
from results.result.sync import Err, Ok

__all__ = ["Ok", "Err", "AsyncResult"]
