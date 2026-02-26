"""Ok[T] - Represents successful computation result.

This module implements the Ok variant of Result[T, E], containing a success value.
Ok is immutable (frozen dataclass) and implements all Result ABC methods.

Exported:
    Ok: Concrete Ok implementation
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic

from typing_extensions import override

from results.core import E, F, T, U
from results.core.base import Result

__all__ = ["Ok"]


@dataclass(frozen=True)
class Ok(Result[T, E], Generic[T, E]):
    """Represents successful computation with value of type T.

    Ok[T] is the success variant of Result[T, E]. It contains a value of type T
    and implements all Result abstract methods by operating on the success value.

    The Ok class is immutable (frozen dataclass) and uses @override decorators
    to enforce proper implementation of the Result ABC contract.

    Type Parameters:
        T: The type of the success value (can be any type)
        E: The error type (bound to Exception)

    Attributes:
        _value (T): The success value - private attribute accessible via ok() method

    Example:
        >>> from results import Ok, Err
        >>> result: Result[int, ValueError] = Ok(42)
        >>> result.is_ok()
        True
        >>> result.ok()
        42
        >>> result.err()
        None
        >>> doubled = result.map(lambda x: x * 2)
        >>> doubled.ok()
        84
    """

    _value: T

    @override
    def is_ok(self) -> bool:
        """Check if this is Ok variant.

        Returns:
            bool: Always True for Ok variant.

        Example:
            >>> Ok(42).is_ok()
            True
        """
        return True

    @override
    def is_err(self) -> bool:
        """Check if this is Err variant.

        Returns:
            bool: Always False for Ok variant.

        Example:
            >>> Ok(42).is_err()
            False
        """
        return False

    @override
    def ok(self) -> T:
        """Return value if Ok, None if Err.

        Returns:
            T: The wrapped success value T.
        Example:
            >>> Ok(42).ok()
            42
            >>> result: Result[int, ValueError] = Ok("hello")
            >>> result.ok()
            'hello'
        """
        return self._value

    @override
    def err(self) -> None:
        """Return error if Err, None if Ok.

        Returns:
            None: Always None for Ok variant.
        Example:
            >>> Ok(42).err()
            None
        """
        return None

    @override
    def unwrap(self) -> T:
        """Extract value or raise UnwrapError.

        For Ok variant, returns the contained value without raising.

        Returns:
            T: The success value.

        Example:
            >>> Ok(42).unwrap()
            42
        """
        return self._value

    @override
    def map(self, op: Callable[[T], U]) -> Result[U, E]:
        """Transform success value, preserving error type.

        Applies the given function to the success value and wraps the result
        in Ok. If operation raises an exception, it propagates.

        Parameters:
            op: Function that transforms T to U

        Returns:
            Result[U, E]: Ok containing transformed value, or exception if op fails

        Raises:
            Any exception raised by op(self._value) will propagate

        Example:
            >>> Ok(5).map(lambda x: x * 2).ok()
            10
            >>> Ok("hello").map(len).ok()
            5
        """
        return Ok(op(self._value))

    @override
    def map_err(self, op: Callable[[E], F]) -> Result[T, F]:
        """Transform error type, preserving success value.

        For Ok variant, the function is not applied and the original Ok is
        returned with the error type updated by the type system.

        Parameters:
            op: Function that transforms E to F (not used for Ok)

        Returns:
            Result[T, F]: Self with error type updated

        Example:
            >>> result: Result[int, ValueError] = Ok(42)
            >>> transformed = result.map_err(lambda e: RuntimeError(str(e)))
            >>> transformed.ok()
            42
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
            >>> result = Ok(42)
            >>> result.inspect(lambda x: print(f"Value: {x}"))
            # Prints "Value: 42"
            # Returns Ok(42)

            >>> Ok(5).inspect(lambda x: print(f"Doubling {x}")).map(lambda x: x * 2).ok()
            # Prints "Doubling 5"
            # Returns 10

            >>> # Chainable with other operations
            >>> Ok(data).inspect(log_step1).map(transform).inspect(log_step2).unwrap()
        """
        f(self._value)

        return self

    @override
    def inspect_err(self, f: Callable[[E], None]) -> Result[T, E]:
        """Inspect error value for debugging without modifying the Result.

        For Ok variant, the function is not called and self is returned unchanged.
        This method exists for API consistency and type safety - allows code to
        call inspect_err() on Result[T, E] without knowing if it's Ok or Err.

        Parameters:
            f: Function that takes the error value E (not called for Ok)

        Returns:
            Result[T, E]: Self unchanged

        Example:
            >>> Ok(42).inspect_err(lambda e: print(f"Error: {e}"))
            # Prints nothing, returns Ok(42)

            >>> # Useful for handling both Ok and Err in same chain
            >>> result: Result[int, ValueError] = fetch_user_id()
            >>> result.inspect_err(log_error).ok()  # Works for both Ok and Err
        """
        return self

    @override
    def context(self, msg: str) -> Result[T, E]:
        """Push context message to error chain (eager evaluation).

        For Ok variant, the context message is ignored and self is returned unchanged.
        This method exists for API consistency and type safety - allows code to call
        context() on Result[T, E] without knowing if it's Ok or Err.

        Parameters:
            msg: Context message (not used for Ok)

        Returns:
            Result[T, E]: Self unchanged

        Example:
            >>> Ok(42).context("some context")
            # Returns Ok(42) unchanged, message ignored

            >>> # Useful for handling both Ok and Err without branching
            >>> result = fetch_data().context("data fetch")
            >>> # Works regardless of whether fetch_data returned Ok or Err
        """
        return self

    @override
    def with_context(self, f: Callable[[], str]) -> Result[T, E]:
        """Push lazy context message to error chain (delayed evaluation).

        For Ok variant, the function is not called and self is returned unchanged.
        This method exists for API consistency and type safety. Lazy evaluation
        ensures no overhead for Ok cases - the callable is never invoked.

        Parameters:
            f: Callable that generates context message (not called for Ok)

        Returns:
            Result[T, E]: Self unchanged

        Example:
            >>> Ok(42).with_context(lambda: expensive_debug_info())
            # Returns Ok(42) unchanged, callable NOT invoked (zero overhead)

            >>> # Useful for handling both Ok and Err without branching
            >>> result = fetch_data().with_context(lambda: f"at {now()}")
            >>> # For Ok cases, now() is never called (efficient)
        """
        return self

    @override
    def and_then(self, op: Callable[[T], Result[U, F]]) -> Result[U, F | E]:
        """Chain operations, automatically accumulating error types via Union.

        Applies the given function (which returns a Result) to the success value.
        The error type is automatically accumulated using Union[F, E] by the
        type system, enabling IDE autocompletion for all possible error types
        in the chain.

        Parameters:
            op: Function that transforms T to Result[U, F]

        Returns:
            Result[U, Union[F, E]]: Result from op, with error type Union[F, E]

        Example:
            >>> def divide(x: int) -> Result[int, ZeroDivisionError]:
            ...     if x == 0:
            ...         return Err(ZeroDivisionError("Cannot divide by zero"))
            ...     return Ok(100 // x)
            >>> Ok(5).and_then(divide).ok()
            20
            >>> Ok(0).and_then(divide).is_err()
            True

            Type accumulation example:
            >>> result = Ok(10)  # Result[int, ValueError]
            >>> result = result.and_then(divide)  # Result[int, Union[ZeroDivisionError, ValueError]]
            >>> # Type checker now knows all possible error types
        """
        return op(self._value)  # type: ignore[return-value]

    @override
    def unwrap_or(self, default: T) -> T:
        """Extract success value or return default if error.

        For Ok variant, always returns the wrapped value.

        Parameters:
            default: Value to return if error (not used for Ok)

        Returns:
            T: The wrapped success value

        Example:
            >>> Ok(42).unwrap_or(0)
            42
        """
        return self._value

    @override
    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        """Extract success value or compute default from error.

        For Ok variant, always returns the wrapped value without calling the function.

        Parameters:
            f: Function to compute default (not called for Ok)

        Returns:
            T: The wrapped success value

        Example:
            >>> Ok(42).unwrap_or_else(lambda e: len(str(e)))
            42
        """
        return self._value

    def __repr__(self) -> str:
        """Return string representation for debugging.

        Returns:
            str: String like "Ok(42)" or "Ok('hello')"

        Example:
            >>> repr(Ok(42))
            "Ok(42)"
            >>> repr(Ok("test"))
            "Ok('test')"
        """
        return f"Ok({self._value!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another Ok.

        Two Ok instances are equal if their contained values are equal.

        Parameters:
            other: Object to compare with

        Returns:
            bool: True if both are Ok with equal values

        Example:
            >>> Ok(42) == Ok(42)
            True
            >>> Ok(42) == Ok(43)
            False
            >>> Ok(42) == Err(ValueError())
            TypeError
        """
        if not isinstance(other, Ok):
            return NotImplemented
        return bool(self._value == other._value)

    def __hash__(self) -> int:
        """Return hash for use in sets/dicts.

        Ok instances can be hashed if their contained value is hashable.

        Returns:
            int: Hash combining Ok type and value hash

        Raises:
            TypeError: If contained value is not hashable

        Example:
            >>> hash(Ok(42))  # OK if 42 is hashable
            >>> {Ok(1), Ok(2)}  # Works in sets
            {Ok(1), Ok(2)}
        """
        return hash(("Ok", self._value))
