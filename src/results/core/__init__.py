"""Result/Maybe/Either type system core contract layer.

This module defines the Result, Maybe, and Either abstract base classes (ABC),
type variables, and shared context chain infrastructure for all monad types.

All concrete implementations must adhere to the contract defined here.

Exports:
    - Result: The abstract base class for Result implementations
    - Maybe: The abstract base class for Maybe implementations
    - Either: The abstract base class for Either implementations
    - AsyncMaybeBase: The abstract base class for AsyncMaybe implementations
    - AsyncEitherBase: The abstract base class for AsyncEither implementations
    - T: Type variable for value type (no constraints)
    - E: Type variable for error type (bound=Exception)
    - U: Type variable for transformation output
    - F: Type variable for alternative error types
    - L, R, V: Type variables for Either (left, right, variant)
    - ContextChain: Immutable LIFO context stack for error tracking
    - unwrap_with_context: Unified unwrap logic across monad types
"""

from .async_either_base import AsyncEitherBase
from .async_maybe_base import AsyncMaybeBase
from .base import Result
from .context import ContextChain, unwrap_with_context
from .either_base import Either
from .maybe_base import Maybe
from .types import E, F, L, R, T, U, V

__all__ = [
    "Result",
    "Maybe",
    "Either",
    "AsyncMaybeBase",
    "AsyncEitherBase",
    "T",
    "E",
    "U",
    "F",
    "L",
    "R",
    "V",
    "ContextChain",
    "unwrap_with_context",
]
