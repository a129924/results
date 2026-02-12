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
    flatten: Flatten nested Either
    swap: Swap Left and Right outcomes
    from_ok_err: Convert Result to Either
    partition: Partition sequence of Either by variant
    sequence: Collect Either sequence into Either of list
"""

from .asyncio import AsyncEither
from .sync import (
    Left,
    Right,
    flatten,
    from_ok_err,
    partition,
    sequence,
    swap,
)

__all__ = [
    "Left",
    "Right",
    "AsyncEither",
    "flatten",
    "swap",
    "from_ok_err",
    "partition",
    "sequence",
]
