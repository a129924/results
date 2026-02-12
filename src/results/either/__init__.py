"""Either monad - dual outcome type.

The Either type represents a computation that produces one of two outcomes:
- Left[L]: First alternative (contextually may represent error, but not required)
- Right[R]: Second alternative (contextually may represent success, but not required)

Unlike Result[T, E] (success/failure) or Maybe[T] (presence/absence), Either
is semantically neutral - both outcomes are equally valid. Both Left and Right
support context chains for diagnostic information.

Exports:
    Left: Left variant
    Right: Right variant
    AsyncEither: Awaitable wrapper for async/await workflows
"""

from .asyncio import AsyncEither
from .sync import Left, Right

__all__ = ["Left", "Right", "AsyncEither"]
