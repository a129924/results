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

    @abstractmethod
    def inspect(self, f: Callable[[T], None]) -> "Result[T, E]":
        """Inspect success value for debugging without modifying the Result.

        If this is Ok, applies the function to the wrapped value for side effects
        (such as logging or printing) and returns self unchanged. If this is Err,
        returns self unchanged without calling the function.

        This is a pure debugging tool - the callable cannot modify the Result.
        Any exception raised in the callable will propagate.

        Parameters:
            f: Function that takes the success value and performs side effects

        Returns:
            Result[T, E]: Returns self unchanged

        Example:
            >>> result = Ok(42)
            >>> result.inspect(lambda x: print(f"Value: {x}")).map(lambda x: x * 2)
            # Prints "Value: 42", returns Ok(84)

            >>> result = Err("error")
            >>> result.inspect(lambda x: print(f"Value: {x}"))
            # Prints nothing, returns Err("error")
        """
        ...

    @abstractmethod
    def inspect_err(self, f: Callable[[E], None]) -> "Result[T, E]":
        """Inspect error value for debugging without modifying the Result.

        If this is Err, applies the function to the wrapped error for side effects
        (such as logging or printing) and returns self unchanged. If this is Ok,
        returns self unchanged without calling the function.

        This is a pure debugging tool - the callable cannot modify the Result.
        Any exception raised in the callable will propagate.

        Parameters:
            f: Function that takes the error value and performs side effects

        Returns:
            Result[T, E]: Returns self unchanged

        Example:
            >>> result = Err(ValueError("Invalid"))
            >>> result.inspect_err(lambda e: print(f"Error: {e}"))
            # Prints "Error: Invalid", returns Err(ValueError("Invalid"))

            >>> result = Ok(42)
            >>> result.inspect_err(lambda e: print(f"Error: {e}"))
            # Prints nothing, returns Ok(42)
        """
        ...

    @abstractmethod
    def context(self, msg: str) -> "Result[T, E]":
        """Push context message to error chain (eager evaluation).

        If this is Err, pushes the context message to the chain and returns
        a new Err with the message added to the context chain. If this is Ok,
        returns self unchanged.

        Context messages are accumulated in LIFO (Last In, First Out) order,
        matching the Rust anyhow behavior. The most recent context message
        appears first when the error is displayed.

        Parameters:
            msg: Context message to push onto the error chain

        Returns:
            Result[T, E]: New Err with context pushed (LIFO order), or same Ok

        Example:
            >>> result = Err(ValueError("Invalid input"))
            >>> result = result.context("validating user age")
            >>> result = result.context("processing user data")
            # Context chain: ("processing user data", "validating user age")

            >>> result = Ok(42)
            >>> result.context("some message")
            # Returns Ok(42) unchanged
        """
        ...

    @abstractmethod
    def with_context(self, f: Callable[[], str]) -> "Result[T, E]":
        """Push lazy context message to error chain (delayed evaluation).

        If this is Err, calls the function to generate a context message,
        then pushes it to the chain and returns a new Err. If this is Ok,
        returns self unchanged without calling the function.

        Lazy evaluation allows context generation to depend on runtime values
        (e.g., timestamps, environment variables) without overhead for Ok cases.

        Parameters:
            f: Callable that generates the context message string

        Returns:
            Result[T, E]: New Err with lazy context pushed (LIFO order), or same Ok

        Raises:
            Any exception raised in the callable will propagate

        Example:
            >>> from datetime import datetime
            >>> result = Err(ValueError("Failed"))
            >>> result = result.with_context(lambda: f"Error at {datetime.now()}")
            # Context generated and pushed to chain

            >>> result = Ok(42)
            >>> result.with_context(lambda: expensive_context_generation())
            # Returns Ok(42), function not called (no overhead)
        """
        ...
