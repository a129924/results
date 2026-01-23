"""Result type system core contract layer.

This module defines the Result abstract base class (ABC) and type variables.
All concrete implementations must adhere to the contract defined here.

Exports:
    - Result: The abstract base class for all Result implementations
    - T: Type variable for success value (no constraints)
    - E: Type variable for error type (bound=Exception)
    - U: Type variable for transformation output
    - F: Type variable for alternative error types
"""

from .base import Result
from .types import E, F, T, U

__all__ = [
    "Result",
    "T",
    "E",
    "U",
    "F",
]
