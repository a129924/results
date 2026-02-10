"""Result/Maybe type system core contract layer.

This module defines the Result and Maybe abstract base classes (ABC),
type variables, and shared context chain infrastructure for all monad types.

All concrete implementations must adhere to the contract defined here.

Exports:
    - Result: The abstract base class for Result implementations
    - Maybe: The abstract base class for Maybe implementations
    - T: Type variable for value type (no constraints)
    - E: Type variable for error type (bound=Exception)
    - U: Type variable for transformation output
    - F: Type variable for alternative error types
    - ContextChain: Immutable LIFO context stack for error tracking
    - unwrap_with_context: Unified unwrap logic across monad types
"""

from .base import Result
from .context import ContextChain, unwrap_with_context
from .maybe_base import Maybe
from .types import E, F, T, U

__all__ = [
    "Result",
    "Maybe",
    "T",
    "E",
    "U",
    "F",
    "ContextChain",
    "unwrap_with_context",
]
