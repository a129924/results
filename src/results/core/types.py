"""Type variable definitions for Result type system.

This module defines the core type variables used throughout the Result framework.
All type variables are bound appropriately to ensure type safety and clarity.

Type Variables:
    - T: Represents the success value type (no constraints, any type is valid)
    - E: Represents the error type (must be Exception subclass for proper error handling)
    - U: Represents transformation output type for map operations (use in method signatures)
    - F: Represents alternative error type for error composition (use in method signatures)
"""

from typing import TypeVar

# Success value type variable
# Used to represent the value type in Ok[T] or Result[T, E]
# No constraints - can be any type (int, str, custom class, etc.)
# Example: Result[User, GetUserError] means T=User
T = TypeVar("T")

# Error type variable
# No constraints - can be any type, following Rust's Result<T, E> design
# While Exception is the recommended usage, strings, ints, dicts, etc. are valid
# Example: Result[User, GetUserError] or Result[int, str] or Result[str, dict]
E = TypeVar("E")

# Transformation output type variable
# Used internally in method signatures for map operations
# Represents the new type after transformation
# Example: map(lambda x: str(x)) transforms T to U where U=str
U = TypeVar("U")

# Alternative error type variable
# Used in error composition and and_then operations
# No constraints - can be any type, same as E
# Represents the error type from a chained operation
# Example: result.and_then(fn) -> Result[U, F | E] where F is the new error type
F = TypeVar("F")

__all__ = [
    "T",
    "E",
    "U",
    "F",
]
