"""Results package - Rust-inspired Result and Maybe types for Python.

This package provides Result and Maybe types similar to Rust's for elegant
error handling and type-safe operations.

Basic usage:
    >>> from results import Ok, Err, Result, Some, Nothing, Maybe
    >>> def divide(x: int, y: int) -> Result[int, str]:
    ...     if y == 0:
    ...         return Err("division by zero")
    ...     return Ok(x // y)
    >>> divide(10, 2).map(lambda x: x * 2).ok()
    10

    >>> def find_user(user_id: int) -> Maybe[str]:
    ...     if user_id < 0:
    ...         return Nothing()
    ...     return Some(f"User {user_id}")
    >>> find_user(1).map(str.upper).unwrap_or("Unknown")
    "USER 1"

Exports:
    - Result: Base Result type
    - Ok: Success variant
    - Err: Error variant
    - AsyncResult: Async Result variant
    - Maybe: Base Maybe type
    - Some: Presence variant
    - Nothing: Absence variant
    - UnwrapError: Exception raised by unwrap() on Err/Nothing
"""

from __future__ import annotations

__version__ = "0.3.1"

from results.core.base import Result
from results.core.maybe_base import Maybe
from results.exceptions import UnwrapError
from results.maybe import AsyncMaybe, Nothing, Some
from results.result import AsyncResult, Err, Ok

__all__ = [
    "Result",
    "Ok",
    "Err",
    "AsyncResult",
    "Maybe",
    "Some",
    "Nothing",
    "AsyncMaybe",
    "UnwrapError",
]
