"""Type variable definitions for Result type system.

This module defines the core type variables used throughout the Result framework.
All type variables are bound appropriately to ensure type safety and clarity.

Type Variables:
    - T: Represents the success value type (no constraints, any type is valid)
    - E: Represents the error type (must be Exception subclass for proper error handling)
    - U: Represents transformation output type for map operations (use in method signatures)
    - F: Represents alternative error type for error composition (use in method signatures)
    - L: Represents the left outcome type in Either[L, R] (no constraints)
    - R: Represents the right outcome type in Either[L, R] (no constraints)
    - V: Represents alternative right type for Either transformations (use in method signatures)
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

# Left outcome type variable
# Used to represent the left value type in Either[L, R]
# No constraints - can be any type (conventionally error-like, but no requirement)
# Example: Either[str, User] means L=str (error message)
L = TypeVar("L")

# Right outcome type variable
# Used to represent the right value type in Either[L, R]
# No constraints - can be any type (conventionally success-like by convention, but no requirement)
# Example: Either[str, User] means R=User (success case)
R = TypeVar("R")

# Alternative right type variable
# Used in Either transformations and bimap operations
# No constraints - can be any type, same as R
# Represents the right type from a transformation
# Example: bimap(...) -> Either[U, V] where V is new right type
V = TypeVar("V")

__all__ = [
    "T",
    "E",
    "U",
    "F",
    "L",
    "R",
    "V",
]
