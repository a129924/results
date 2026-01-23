"""Synchronous Result implementation.

This module provides Ok[T] and Err[E] - the concrete implementations of Result[T, E].
Both are immutable frozen dataclasses that implement all Result abstract methods.

Exported:
    Ok: Success variant
    Err: Failure variant
"""

from results.impl.sync.err import Err
from results.impl.sync.ok import Ok

__all__ = [
    "Ok",
    "Err",
]
