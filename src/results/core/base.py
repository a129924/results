"""Result abstract base class - the core contract layer.

This module defines the Result abstract base class that all implementations
(Ok and Err) must adhere to. The Result type represents a computation that
can either succeed with a value (Ok[T]) or fail with an error (Err[E]).

The contract ensures:
- Type-safe error handling without exceptions
- Explicit error types in function signatures
- Chainable operations via and_then, map, map_err
- All errors automatically accumulated via Union types
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic

from .types import E, F, T, U


class Result(ABC, Generic[T, E]):
    """Abstract base class for Result type - success or failure computation.

    Result[T, E] represents a computation that can either:
    - Succeed with a value of type T (represented by Ok[T])
    - Fail with an error of type E (represented by Err[E])

    The Result type enforces explicit error handling and supports chainable
    operations that automatically accumulate error types via Union.

    Type Parameters:
        T: The success value type (any type)
        E: The error type (must be Exception subclass)

    Example:
        >>> result: Result[User, GetUserError] = get_user(user_id)
        >>> result = result.and_then(validate_user)
        # Type is now: Result[ValidatedUser, GetUserError | ValidateError]
    """

    @abstractmethod
    def map(self, op: Callable[[T], U]) -> "Result[U, E]":
        """Transform the success value if present, preserving error type.

        If this is Ok, applies the operation to the wrapped value and returns
        a new Ok with the result. If this is Err, returns self unchanged.

        Parameters:
            op: Function that transforms value of type T to type U

        Returns:
            Result[U, E]: New Result with transformed success value, or same Err

        Example:
            >>> ok_user = Ok(User(name="Alice"))
            >>> ok_user.map(lambda u: u.name.upper())  # Ok("ALICE")

            >>> err_user = Err(GetUserError("Not found"))
            >>> err_user.map(lambda u: u.name.upper())  # Err(GetUserError(...))
        """
        ...

    @abstractmethod
    def map_err(self, op: Callable[[E], F]) -> "Result[T, F]":
        """Transform the error type if present, preserving success value.

        If this is Err, applies the operation to the wrapped error and returns
        a new Err with the result. If this is Ok, returns self unchanged.

        Parameters:
            op: Function that transforms error of type E to type F

        Returns:
            Result[T, F]: New Result with transformed error type, or same Ok

        Example:
            >>> err = Err(GetUserError("Not found"))
            >>> err.map_err(lambda e: str(e))  # Err("Not found")
        """
        ...

    @abstractmethod
    def and_then(self, op: Callable[[T], "Result[U, F]"]) -> "Result[U, F | E]":
        """Chain operations that return Results, automatically accumulating error types.

        If this is Ok, applies the operation to the wrapped value. The operation
        returns a new Result which is returned. If this is Err, returns self unchanged
        but with error type expanded to F | E by the type system.

        The error type automatically accumulates via Union - each and_then adds
        the new error type to the union, enabling IDE/mypy to show all possible
        failures in the chain.

        Parameters:
            op: Function that transforms value of type T to Result[U, F]

        Returns:
            Result[U, F | E]: New Result with chained computation result,
                                    error type is union of all possible failures

        Raises:
            Nothing - all failures are represented in the Result type

        Example:
            >>> # Each and_then adds error types to the Union
            >>> result: Result[User, GetUserError] = get_user(123)
            >>> result = result.and_then(validate_user)
            # Type: Result[ValidatedUser, GetUserError | ValidateError]
            >>> result = result.and_then(send_email)
            # Type: Result[ConfirmationData, GetUserError | ValidateError | SendEmailError]
        """
        ...

    @abstractmethod
    def unwrap(self) -> T:
        """Extract the success value or raise an exception.

        If this is Ok, returns the wrapped value. If this is Err, raises
        UnwrapError with the wrapped exception as context.

        Returns:
            T: The wrapped success value

        Raises:
            UnwrapError: If this is an Err, wrapping the original exception

        Example:
            >>> ok = Ok(42)
            >>> ok.unwrap()  # 42

            >>> err = Err(ValueError("Invalid"))
            >>> err.unwrap()  # raises UnwrapError
        """
        ...

    @abstractmethod
    def ok(self) -> T | None:
        """Extract the success value as Optional.

        Returns Some(value) if Ok, None if Err.

        Returns:
            Optional[T]: The wrapped value if Ok, None if Err

        Example:
            >>> Ok(42).ok()  # 42
            >>> Err(ValueError()).ok()  # None
        """
        ...

    @abstractmethod
    def err(self) -> E | None:
        """Extract the error value as Optional.

        Returns Some(error) if Err, None if Ok.

        Returns:
            Optional[E]: The wrapped error if Err, None if Ok

        Example:
            >>> error = ValueError()
            >>> Err(error).err()  # error
            >>> Ok(42).err()  # None
        """
        ...

    @abstractmethod
    def is_ok(self) -> bool:
        """Check if this Result is Ok variant.

        Returns:
            bool: True if this is Ok, False if Err

        Example:
            >>> Ok(42).is_ok()  # True
            >>> Err(ValueError()).is_ok()  # False
        """
        ...

    @abstractmethod
    def is_err(self) -> bool:
        """Check if this Result is Err variant.

        Returns:
            bool: True if this is Err, False if Ok

        Example:
            >>> Ok(42).is_err()  # False
            >>> Err(ValueError()).is_err()  # True
        """
        ...
