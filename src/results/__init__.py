"""Results package - Rust-inspired Result type for Python.

This package provides a Result type similar to Rust's Result<T, E> for elegant
error handling and type-safe operations.

Basic usage:
    >>> from results import Ok, Err, Result
    >>> def divide(x: int, y: int) -> Result[int, str]:
    ...     if y == 0:
    ...         return Err("division by zero")
    ...     return Ok(x // y)
    >>> divide(10, 2).map(lambda x: x * 2).ok()
    10
    >>> divide(10, 0).err()
    'division by zero'

Exports:
    - Result: Base Result type
    - Ok: Success variant
    - Err: Error variant
    - UnwrapError: Exception raised by unwrap() on Err
"""

from __future__ import annotations

__version__ = "0.2.0"

from results.core.base import Result
from results.exceptions import UnwrapError
from results.impl.sync import Err, Ok

__all__ = [
    "Result",
    "Ok",
    "Err",
    "UnwrapError",
]
