"""Protocol definitions for monad type families.

This module defines the common protocols/interfaces that all monad types
should implement. These protocols serve as:

1. Documentation of expected behavior across monad families
2. Type hints for generic monad operations
3. Foundation for future monad types (Maybe, Either, Validation, etc.)

All Result/Maybe/Either variants inherit from or implement these protocols
to ensure consistency across the monad ecosystem.

Note: Protocols use 'Any' for return types to avoid mypy invariance issues
with TypeVars. This is a pragmatic trade-off for documentation purposes.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeVar


class ContextAware(Protocol):
    """Types that support context stacking for error tracking.

    Implemented by all error-bearing monad variants (Err, Nothing, Left, etc.)
    to provide consistent context chain functionality.

    Methods:
        context: Add a context message to the error chain
        with_context: Add a lazy-evaluated context message
    """

    def context(self, msg: str) -> Any:
        """Add context message to error chain.

        Args:
            msg: Context message describing the error location

        Returns:
            New instance with context added (immutable operation)

        Example:
            >>> result = Err(ValueError("bad input"))
            >>> result.context("validating user age")
        """
        ...

    def with_context(self, f: Callable[[], str]) -> Any:
        """Add lazy-evaluated context message to error chain.

        Useful when context computation is expensive and should only
        happen if the error is accessed.

        Args:
            f: Callable that returns context message

        Returns:
            New instance with lazy context (evaluated on demand)

        Example:
            >>> result = Err(ValueError("bad input"))
            >>> result.with_context(lambda: f"user_id={expensive_lookup()}")
        """
        ...


class Unwrappable(Protocol):
    """Types that support unwrap() - extracting success or raising error.

    All monad types must implement unwrap() to extract the success value
    or raise an exception on the error variant.
    """

    def unwrap(self) -> Any:
        """Extract success value or raise exception.

        Raises:
            Exception: Re-raised error with context chain if available
            UnwrapError: For non-Exception error types

        Example:
            >>> Ok(42).unwrap()
            42
            >>> Err(ValueError("failed")).unwrap()  # raises ValueError
        """
        ...

    async def unwrap_async(self) -> Any:
        """Async version of unwrap().

        For AsyncResult and AsyncMaybe types.

        Raises:
            Exception: Re-raised error with context chain if available
            UnwrapError: For non-Exception error types
        """
        ...


class Inspectable(Protocol):
    """Types that support inspection for debugging without unwrapping.

    Enables observing success/error values for side effects (logging,
    printing, etc.) without extracting or modifying the value.
    """

    def inspect(self, f: Callable[[Any], None]) -> Any:
        """Inspect success value (no-op on error variant).

        Args:
            f: Function to call with success value if present

        Returns:
            Self (for method chaining)

        Example:
            >>> Ok(42).inspect(print)  # prints: 42
            >>> Err("error").inspect(print)  # no-op
        """
        ...

    def inspect_err(self, f: Callable[[Any], None]) -> Any:
        """Inspect error value (no-op on success variant).

        Args:
            f: Function to call with error value if present

        Returns:
            Self (for method chaining)

        Example:
            >>> Err("error").inspect_err(print)  # prints: error
            >>> Ok(42).inspect_err(print)  # no-op
        """
        ...


class Mappable(Protocol):
    """Types that support map/map_err transformations.

    Enables functional transformations of success/error values while
    preserving the monad structure.
    """

    def map(self, op: Callable[[Any], Any]) -> Any:
        """Transform success value (no-op on error variant).

        Args:
            op: Function to apply to success value

        Returns:
            New instance with transformed value or original error

        Example:
            >>> Ok(42).map(lambda x: x * 2)  # Ok(84)
            >>> Err("error").map(lambda x: x * 2)  # Err("error")
        """
        ...

    def map_err(self, op: Callable[[Any], Any]) -> Any:
        """Transform error value (no-op on success variant).

        Args:
            op: Function to apply to error value

        Returns:
            New instance with transformed error or original value

        Example:
            >>> Err("error").map_err(str.upper)  # Err("ERROR")
            >>> Ok(42).map_err(str.upper)  # Ok(42)
        """
        ...


class Chainable(Protocol):
    """Types that support monadic chaining via and_then.

    Enables sequential operations that can fail at any step.
    """

    def and_then(self, op: Callable[[Any], Any]) -> Any:
        """Chain operations that return monad instances.

        Also known as flatMap or bind in functional programming.

        Args:
            op: Function that takes success value and returns new monad

        Returns:
            Result of chained operation or original error

        Example:
            >>> Ok(42).and_then(lambda x: Ok(x * 2))  # Ok(84)
            >>> Ok(42).and_then(lambda x: Err("failed"))  # Err("failed")
            >>> Err("error").and_then(lambda x: Ok(x))  # Err("error")
        """
        ...


class AsyncMappable(Protocol):
    """Types that support async map transformations.

    For AsyncResult and AsyncMaybe types that need to transform values
    through async operations.
    """

    def map_async(self, op: Callable[[Any], Awaitable[Any]]) -> Awaitable[Any]:
        """Transform success value using async operation.

        Args:
            op: Async function to apply to success value

        Returns:
            Awaitable that resolves to transformed result

        Example:
            >>> async def double(x):
            ...     return x * 2
            >>> await AsyncResult.from_result(Ok(42)).map_async(double)
            >>> # Result: Ok(84)
        """
        ...

    def map_err_async(self, op: Callable[[Any], Awaitable[Any]]) -> Awaitable[Any]:
        """Transform error value using async operation.

        Args:
            op: Async function to apply to error value

        Returns:
            Awaitable that resolves to result with transformed error

        Example:
            >>> async def format_error(e):
            ...     return f"Error: {e}"
            >>> await AsyncResult.from_result(Err("bad")).map_err_async(format_error)
        """
        ...


OkT = TypeVar("OkT", covariant=True)
ErrT = TypeVar("ErrT", covariant=True)


# 定義 is_ok ok is_err err 的 Able classes for type hinting and protocol adherence across monad types.
class IsOkAble(Protocol[OkT, ErrT]):
    def is_ok(self) -> bool: ...


class OkAble(Protocol[OkT, ErrT]):
    def ok(self) -> OkT: ...


class IsErrAble(Protocol[OkT, ErrT]):
    def is_err(self) -> bool: ...


class ErrAble(Protocol[OkT, ErrT]):
    def err(self) -> ErrT: ...


# Mixin for types that have is_ok and ok methods (like Result)
class OkMixin(IsOkAble[OkT, ErrT], OkAble[OkT, ErrT]):
    pass


# Mixin for types that have is_err and err methods (like Result)
class ErrMixin(IsErrAble[OkT, ErrT], ErrAble[OkT, ErrT]):
    pass
