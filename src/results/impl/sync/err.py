"""Err[E] - Represents failed computation result.

This module implements the Err variant of Result[T, E], containing an error value.
Err is immutable (frozen dataclass) and implements all Result ABC methods.

Exported:
    Err: Concrete Err implementation
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic

from typing_extensions import Never, override

from results.core import E, F, T, U
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
        E: The error type (bound to Exception)

    Attributes:
        _error (E): The error value - private attribute accessible via err() method

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
    """

    _error: E

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
        """Extract value or raise UnwrapError.

        For Err variant, raises UnwrapError containing the original error.

        Returns:
            Never: Never returns (always raises)

        Raises:
            UnwrapError: Always raised, containing the original error and message

        Example:
            >>> from results import Err, UnwrapError
            >>> result = Err(ValueError("invalid"))
            >>> try:
            ...     result.unwrap()
            ... except UnwrapError as e:
            ...     print(e.message)
            ...     print(e.original_error)
            Called unwrap on Err
            ValueError('invalid')
        """
        raise UnwrapError("Called unwrap on Err", self._error)

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
        """Transform error type, preserving success value.

        Applies the given function to the error value and wraps the result
        in Err. If operation raises an exception, it propagates.

        Parameters:
            op: Function that transforms E to F

        Returns:
            Result[T, F]: Err containing transformed error, or exception if op fails

        Raises:
            Any exception raised by op(self._error) will propagate

        Example:
            >>> error = ValueError("invalid")
            >>> result: Result[int, ValueError] = Err(error)
            >>> transformed = result.map_err(lambda e: RuntimeError(str(e)))
            >>> isinstance(transformed.err(), RuntimeError)
            True
        """
        return Err(op(self._error))

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

    def __repr__(self) -> str:
        """Return string representation for debugging.

        Returns:
            str: String like "Err(ValueError('invalid'))"

        Example:
            >>> repr(Err(ValueError("invalid")))
            "Err(ValueError('invalid'))"
            >>> repr(Err(RuntimeError("failed")))
            "Err(RuntimeError('failed'))"
        """
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
