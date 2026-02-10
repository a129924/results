"""Err[E] - Represents failed computation result.

This module implements the Err variant of Result[T, E], containing an error value.
Err is immutable (frozen dataclass) and implements all Result ABC methods.

Exported:
    Err: Concrete Err implementation
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic

from typing_extensions import Never, override

from results.core import ContextChain, E, F, T, U
from results.core.base import Result
from results.exceptions import UnwrapError

__all__ = ["Err"]


@dataclass(frozen=True)
class Err(Result[T, E], Generic[T, E]):
    """Represents failed computation with error of type E.

    Err[E] is the failure variant of Result[T, E]. It contains an error of type E
    and implements all Result abstract methods by short-circuiting operations.

    The Err class is immutable (frozen dataclass) and uses @override decorators
    to enforce proper implementation of the Result ABC contract.

    Type Parameters:
        T: The type of the success value (unused in Err but preserved for Result[T, E])
        E: The error type (unconstrained, supports any type - Exception, str, int, dict, etc.)

    Attributes:
        _error (E): The error value - private attribute accessible via err() method
        _context_chain (ContextChain): Chain of context messages in LIFO order.
            - Empty ContextChain by default (v0.1.0 compatibility)
            - Newest context at index 0 (accessed first when unwrapping)
            - Oldest context at index -1 (appended last)
            - Implements Rust anyhow-style context stacking

    Example:
        >>> from results import Ok, Err
        >>> result: Result[int, ValueError] = Err(ValueError("invalid input"))
        >>> result.is_err()
        True
        >>> result.ok()
        None
        >>> result.err()
        ValueError('invalid input')
        >>> result.map(lambda x: x * 2).is_err()
        True

        >>> # Context chain example (v0.2.0+)
        >>> result = Err(ValueError("parse failed"))
        >>> result = result.context("parsing config file")
        >>> result = result.context("loading configuration")
        >>> result._context_chain
        ('loading configuration', 'parsing config file')
    """

    _error: E
    _context_chain: ContextChain = field(
        default_factory=ContextChain, repr=False, compare=False
    )

    @override
    def is_ok(self) -> bool:
        """Check if this is Ok variant.

        Returns:
            bool: Always False for Err variant.

        Example:
            >>> Err(ValueError()).is_ok()
            False
        """
        return False

    @override
    def is_err(self) -> bool:
        """Check if this is Err variant.

        Returns:
            bool: Always True for Err variant.

        Example:
            >>> Err(ValueError()).is_err()
            True
        """
        return True

    @override
    def ok(self) -> None:
        """Return value if Ok, None if Err.

        Returns:
            None: Always None for Err variant.
        Example:
            >>> Err(ValueError()).ok()
            None
        """
        return None

    @override
    def err(self) -> E | None:
        """Return error if Err, None if Ok.

        Returns:
            E | None: The wrapped error value E.

        Example:
            >>> error = ValueError("invalid")
            >>> Err(error).err() is error
            True
        """
        return self._error

    @override
    def unwrap(self) -> Never:
        """Extract value or raise UnwrapError with context chain display.

        For Err variant, raises the original exception (if Exception type) with
        context chain information, or raises UnwrapError for non-Exception types.

        If context chain is non-empty, formats and prepends context messages
        in LIFO order (newest context first) before raising.

        Returns:
            Never: Never returns (always raises)

        Raises:
            Exception: If _error is an Exception, raises it directly with traceback.
                If context chain is non-empty, it's included in the message.
            UnwrapError: If _error is not an Exception, wraps it in UnwrapError.

        Example:
            >>> from results import Err, UnwrapError
            >>> result = Err(ValueError("invalid"))
            >>> try:
            ...     result.unwrap()
            ... except ValueError as e:
            ...     # Exception type: raised directly
            ...     print(str(e))
            invalid

            >>> # With context chain
            >>> result = (
            ...     Err(ValueError("parse failed"))
            ...     .context("validating user age")
            ...     .context("processing user data")
            ... )
            >>> try:
            ...     result.unwrap()
            ... except ValueError as e:
            ...     # Context prepended to message
            ...     print(str(e))
            processing user data
            validating user age
            parse failed

            >>> # Non-Exception type
            >>> result = Err("string error")
            >>> try:
            ...     result.unwrap()
            ... except UnwrapError as e:
            ...     print(e.message)
            ...     print(e.original_error)
            Called unwrap on Err
            string error
        """
        if not isinstance(self._error, Exception):
            # Non-Exception: wrap in UnwrapError with context chain
            raise UnwrapError(
                "Called unwrap on Err", self._error, self._context_chain.messages
            )

        # Format context chain if present and raise with context
        if not self._context_chain.is_empty():
            context_str = self._context_chain.format_lifo()
            error_msg = f"{context_str}\n  {str(self._error)}"
            # Create a new exception with context message, preserve original traceback
            exc = type(self._error)(error_msg)
            raise exc from self._error
        # No context, raise directly
        raise self._error from self._error

    @override
    def map(self, op: Callable[[T], U]) -> Result[U, E]:
        """Transform success value, preserving error type.

        For Err variant, the function is not applied and the original Err is
        returned with the success type updated by the type system.

        Parameters:
            op: Function that transforms T to U (not used for Err)

        Returns:
            Result[U, E]: Self with success type updated

        Example:
            >>> error = ValueError("invalid")
            >>> result: Result[int, ValueError] = Err(error)
            >>> transformed = result.map(lambda x: x * 2)
            >>> transformed.is_err()
            True
            >>> transformed.err() is error
            True
        """
        return self  # type: ignore

    @override
    def map_err(self, op: Callable[[E], F]) -> Result[T, F]:
        """Transform error type, preserving success value and context chain.

        Applies the given function to the error value and wraps the result
        in Err with the original context chain preserved. If operation raises
        an exception, it propagates.

        Parameters:
            op: Function that transforms E to F

        Returns:
            Result[T, F]: Err containing transformed error with context preserved,
                         or exception if op fails

        Raises:
            Any exception raised by op(self._error) will propagate

        Example:
            >>> error = ValueError("invalid")
            >>> result: Result[int, ValueError] = Err(error)
            >>> transformed = result.map_err(lambda e: RuntimeError(str(e)))
            >>> isinstance(transformed.err(), RuntimeError)
            True

            >>> # With context chain
            >>> result = Err(ValueError("error")).context("ctx")
            >>> transformed = result.map_err(str)
            >>> transformed._context_chain
            ('ctx',)
        """
        return Err(op(self._error), self._context_chain)

    @override
    def and_then(self, op: Callable[[T], Result[U, F]]) -> Result[U, F | E]:
        """Chain operations, automatically accumulating error types via Union.

        For Err variant, the function is not applied. The Err is returned with
        the error type updated to F | E by the type system, enabling IDE
        autocompletion for all possible error types including the original.

        Parameters:
            op: Function that transforms T to Result[U, F] (not used for Err)

        Returns:
            Result[U, F | E]: Self with error type updated to F | E

        Example:
            >>> def divide(x: int) -> Result[int, ZeroDivisionError]:
            ...     if x == 0:
            ...         return Err(ZeroDivisionError("Cannot divide by zero"))
            ...     return Ok(100 // x)
            >>> error = ValueError("parse failed")
            >>> result: Result[int, ValueError] = Err(error)
            >>> chained = result.and_then(divide)
            >>> chained.is_err()
            True
            >>> chained.err() is error
            True
            >>> # Type: Result[int, ZeroDivisionError | ValueError]

            Type accumulation example:
            >>> # First error in chain prevents subsequent operations
            >>> result = Err(ValueError("first"))  # Result[int, ValueError]
            >>> result = result.and_then(divide)  # Result[int, ZeroDivisionError | ValueError]
            >>> # Error remains unchanged, but type system knows both error types
        """
        return self  # type: ignore

    @override
    def inspect(self, f: Callable[[T], None]) -> Result[T, E]:
        """Inspect success value for debugging without modifying the Result.

        Calls the given function with the success value for side effects (logging,
        printing, etc.) and returns self unchanged. This is a pure debugging tool -
        the callable cannot modify the Result.

        Any exception raised in the callable will propagate.

        Parameters:
            f: Function that takes the success value T and performs side effects

        Returns:
            Result[T, E]: Self unchanged

        Example:
            >>> result = Err(ValueError("invalid input"))
            >>> result.inspect(lambda v: print(f"Value: {v}"))
            # Does nothing, returns Err(ValueError("invalid input"))

            >>> result.inspect(lambda v: log_value(v)).map_err(str)
            # Logs nothing, returns Err("invalid input")
        """
        return self

    @override
    def inspect_err(self, f: Callable[[E], None]) -> Result[T, E]:
        """Inspect error value for debugging without modifying the Result.

        Calls the given function with the error value for side effects (logging,
        printing, etc.) and returns self unchanged. This is a pure debugging tool -
        the callable cannot modify the Result.

        Any exception raised in the callable will propagate.

        Parameters:
            f: Function that takes the error value E and performs side effects

        Returns:
            Result[T, E]: Self unchanged

        Example:
            >>> result = Err(ValueError("invalid input"))
            >>> result.inspect_err(lambda e: print(f"Error occurred: {e}"))
            # Prints "Error occurred: invalid input"
            # Returns Err(ValueError("invalid input"))

            >>> result.inspect_err(lambda e: log_error(e)).map_err(str)
            # Logs the error, returns Err("invalid input")
        """
        f(self._error)
        return self

    @override
    def context(self, msg: str) -> Result[T, E]:
        """Push context message to error chain (eager evaluation).

        Pushes the context message to the error chain in LIFO order (newest first).
        Returns a new Err with the message prepended to the context chain.

        This method is for static/predefined context strings. For dynamic context
        that depends on runtime values, use with_context() instead.

        Parameters:
            msg: Context message to add to the chain

        Returns:
            Result[T, E]: New Err with context pushed, old Err unchanged

        Example:
            >>> result = Err(ValueError("parse error"))
            >>> result = result.context("parsing config")
            >>> result._context_chain.messages
            ('parsing config',)

            >>> result = result.context("loading app")
            >>> result._context_chain.messages
            ('loading app', 'parsing config')  # LIFO order

            >>> # Chainable
            >>> result = (
            ...     Err(ValueError("error"))
            ...     .context("step C")
            ...     .context("step B")
            ...     .context("step A")
            ... )
            >>> result._context_chain.messages
            ('step A', 'step B', 'step C')  # Reversed by LIFO stacking
        """
        return Err(self._error, self._context_chain.push(msg))

    @override
    def with_context(self, f: Callable[[], str]) -> Result[T, E]:
        """Push lazy context message to error chain (delayed evaluation).

        Calls the function to generate a context message, then pushes it to the
        error chain in LIFO order. Returns a new Err with the generated message
        added to the context chain.

        Lazy evaluation allows context generation to depend on runtime state
        (timestamps, environment, etc.) without overhead for Ok cases.

        Any exception raised in the callable will propagate.

        Parameters:
            f: Callable that returns context message string

        Returns:
            Result[T, E]: New Err with lazy context pushed, old Err unchanged

        Raises:
            Any exception raised by f() will propagate

        Example:
            >>> from datetime import datetime
            >>> result = Err(ValueError("API error"))
            >>> result = result.with_context(lambda: f"Failed at {datetime.now()}")
            >>> # Context generated immediately and added to chain

            >>> result = Ok(200)
            >>> result = result.with_context(lambda: expensive_debug_info())
            # Returns Ok(200), f() NOT called (no overhead for success case)
        """
        return Err(self._error, self._context_chain.push_lazy(f))

    def __repr__(self) -> str:
        """Return string representation for debugging.

        Returns:
            str: String like "Err(ValueError('invalid'))" or with context chain
                "Err(ValueError('invalid'), context=['step B', 'step A'])"

        Example:
            >>> repr(Err(ValueError("invalid")))
            "Err(ValueError('invalid'))"
            >>> repr(Err(RuntimeError("failed")).context("processing"))
            "Err(RuntimeError('failed'), context=('processing',))"
        """
        if self._context_chain:
            return f"Err({self._error!r}, context={self._context_chain!r})"
        return f"Err({self._error!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another Err.

        Two Err instances are equal if their contained errors are equal.

        Parameters:
            other: Object to compare with

        Returns:
            bool: True if both are Err with equal errors

        Example:
            >>> Err(ValueError("msg")) == Err(ValueError("msg"))
            True
            >>> Err(ValueError("a")) == Err(ValueError("b"))
            False
            >>> Err(ValueError()) == Ok(42)
            TypeError
        """
        if not isinstance(other, Err):
            return NotImplemented
        return bool(self._error == other._error)

    def __hash__(self) -> int:
        """Return hash for use in sets/dicts.

        Err instances can be hashed if their contained error is hashable.

        Returns:
            int: Hash combining Err type and error hash

        Raises:
            TypeError: If contained error is not hashable

        Example:
            >>> hash(Err(ValueError()))  # OK if ValueError is hashable
            >>> {Err(ValueError()), Err(RuntimeError())}  # Works in sets
        """
        return hash(("Err", self._error))
