"""Result framework exception hierarchy.

This module defines all exceptions used by the Result type system:

1. ResultError: Framework-level exception base (for framework internal use)
   - UnwrapError: Raised when unwrap() is called on an Err value

2. BaseError: Optional base class for business exceptions (user-defined)
   - Provides structured exception format with frozen dataclass
   - Automatically initializes Exception.args for proper logging
   - Forces explicit __str__ implementation for clarity

The framework only raises ResultError and UnwrapError. BaseError is provided
as a convenience template for users who want structured business exceptions,
but its use is completely optional.
"""

from abc import abstractmethod
from dataclasses import astuple, dataclass


class ResultError(Exception):
    """Framework-level exception for Result internal errors.

    This is raised by the Result framework itself in specific failure cases
    (e.g., unwrap() on Err). Applications should not raise this directly;
    use application-specific exceptions instead.
    """

    pass


class UnwrapError(ResultError):
    """Exception raised when unwrap() is called on an Err value.

    This occurs when code attempts to extract the value from an Err Result
    without first checking if it's Ok. The original exception is available
    via the cause chain.

    Attributes:
        message: Description of the unwrap failure
        original_error: The exception that was wrapped in the Err

    Example:
        >>> from results import Err, UnwrapError
        >>> result = Err(ValueError("invalid"))
        >>> try:
        ...     result.unwrap()
        ... except UnwrapError as e:
        ...     print(e)  # UnwrapError: Attempted to unwrap an Err value
    """

    def __init__(self, message: str, original_error: Exception) -> None:
        """Initialize UnwrapError with context.

        Parameters:
            message: Error message describing the unwrap failure
            original_error: The exception originally wrapped in Err
        """
        self.message = message
        self.original_error = original_error
        super().__init__(message)


@dataclass(frozen=True)
class BaseError(Exception):
    """Optional base class for application business exceptions.

    This class provides a convenience template for developers who want
    structured, type-safe exceptions within Result types. It is NOT required;
    any Exception subclass can be used as the error type E in Result[T, E].

    Why use BaseError:
    - Automatic Exception.args initialization for proper logging/tracebacks
    - Structured exception format via frozen dataclass
    - Forces explicit __str__ implementation for clarity
    - Type-safe exception attributes

    Important: Using BaseError is completely optional. You can use any
    Exception subclass, or even built-in exceptions, as error types.

    Example (optional usage):
        >>> from dataclasses import dataclass
        >>> from results import BaseError, Ok, Err, Result
        >>>
        >>> @dataclass(frozen=True)
        ... class UserNotFoundError(BaseError):
        ...     user_id: int
        ...
        ...     def __str__(self) -> str:
        ...         return f"User {self.user_id} not found in database"
        >>>
        >>> def get_user(user_id: int) -> Result[dict, UserNotFoundError]:
        ...     if user_id > 0:
        ...         return Ok({"id": user_id, "name": "Alice"})
        ...     else:
        ...         return Err(UserNotFoundError(user_id))
        >>>
        >>> result = get_user(-1)
        >>> match result:
        ...     case Ok(user):
        ...         print(f"Found: {user}")
        ...     case Err(e):
        ...         print(e)  # User -1 not found in database

        You can also use built-in exceptions:
        >>> def parse_int(s: str) -> Result[int, ValueError]:
        ...     try:
        ...         return Ok(int(s))
        ...     except ValueError as e:
        ...         return Err(e)
    """

    @abstractmethod
    def __str__(self) -> str:
        """Return a clear error message.

        Subclasses MUST implement this to provide a meaningful error message.
        This message will be used in logging, tracebacks, and error reporting.

        Returns:
            str: A clear, descriptive error message
        """
        ...

    def __post_init__(self) -> None:
        """Initialize Exception.args for proper logging and tracebacks.

        This ensures that when the exception is logged or printed via traceback,
        Python's logging system can access the exception message via args.
        Called automatically after dataclass initialization.
        """
        super().__init__(*astuple(self))


__all__ = [
    "ResultError",
    "UnwrapError",
    "BaseError",
]
