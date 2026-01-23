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
