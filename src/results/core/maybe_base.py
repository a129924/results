"""Maybe abstract base class - the core contract layer for optional values.

This module defines the Maybe abstract base class that all implementations
(Some and Nothing) must adhere to. The Maybe type represents a computation
that can either have a value (Some[T]) or have no value (Nothing).

Unlike Result which represents success/failure, Maybe represents the
presence/absence of a value - Nothing is NOT an error.

The contract ensures:
- Explicit handling of optional values without null checks
- Chainable operations via and_then, map, filter
- All values must be explicitly unwrapped
- Context tracking for explaining why value is absent (optional reason)
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic

from .types import T, U


class Maybe(ABC, Generic[T]):
    """Abstract base class for Maybe type - presence or absence of value.

    Maybe[T] represents an optional value:
    - Some[T]: Present value of type T
    - Nothing: Absent value (no error, just absence)

    Unlike Result[T, E] which distinguishes success from failure, Maybe
    only tracks presence/absence. Nothing is NOT considered an error,
    rather an expected case (like Python's None but type-safe).

    The Maybe type enforces explicit value handling and supports chainable
    operations that preserve the Maybe context.

    Type Parameters:
        T: The value type when present (any type)

    Example:
        >>> maybe_user: Maybe[User] = get_user_if_exists(user_id)
        >>> maybe_user = maybe_user.map(lambda u: u.name)
        >>> # Type is now: Maybe[str]
        >>> maybe_user.unwrap_or("Unknown")  # str
    """

    @abstractmethod
    def map(self, op: Callable[[T], U]) -> "Maybe[U]":
        """Transform the value if present, preserving absence.

        If this is Some, applies the operation to the wrapped value and
        returns a new Some with the result. If this is Nothing, returns
        Nothing unchanged (with same context chain).

        Parameters:
            op: Function that transforms value of type T to type U

        Returns:
            Maybe[U]: New Maybe with transformed value, or Nothing

        Example:
            >>> Some(42).map(lambda x: x * 2)  # Some(84)
            >>> Some(User(name="Alice")).map(lambda u: u.name)  # Some("Alice")
            >>> Nothing().map(lambda x: x * 2)  # Nothing()
        """
        ...

    @abstractmethod
    def filter(self, predicate: Callable[[T], bool]) -> "Maybe[T]":
        """Filter value based on predicate, returning Nothing if false.

        If this is Some and predicate(value) is True, returns self.
        If this is Some and predicate(value) is False, returns Nothing.
        If this is Nothing, returns self unchanged.

        Parameters:
            predicate: Function that returns True to keep value, False to discard

        Returns:
            Maybe[T]: Self if predicate passes, Nothing otherwise

        Example:
            >>> Some(42).filter(lambda x: x > 0)  # Some(42)
            >>> Some(42).filter(lambda x: x > 100)  # Nothing()
            >>> Some(-5).filter(lambda x: x > 0)  # Nothing()
            >>> Nothing().filter(lambda x: x > 0)  # Nothing()
        """
        ...

    @abstractmethod
    def and_then(self, op: Callable[[T], "Maybe[U]"]) -> "Maybe[U]":
        """Chain operations that return Maybe instances (monadic bind).

        Also known as flatMap or bind in functional programming.

        If this is Some, applies the operation to the wrapped value and
        returns the result (flattened). If this is Nothing, returns Nothing
        unchanged.

        Parameters:
            op: Function that takes value and returns new Maybe

        Returns:
            Maybe[U]: Result of chained operation or Nothing

        Example:
            >>> Some(42).and_then(lambda x: Some(x * 2))  # Some(84)
            >>> Some(42).and_then(lambda x: Nothing())  # Nothing()
            >>> Nothing().and_then(lambda x: Some(x))  # Nothing()
        """
        ...

    @abstractmethod
    def or_else(self, op: Callable[[], "Maybe[T]"]) -> "Maybe[T]":
        """Alternative computation when Nothing, keeping value when Some.

        If this is Some, returns self unchanged. If this is Nothing,
        applies the operation to get an alternative Maybe.

        Parameters:
            op: Function that returns alternative Maybe

        Returns:
            Maybe[T]: Self if Some, result of operation if Nothing

        Example:
            >>> Some(42).or_else(lambda: Some(0))  # Some(42)
            >>> Nothing().or_else(lambda: Some(0))  # Some(0)
            >>> Nothing().or_else(lambda: Nothing())  # Nothing()
        """
        ...

    @abstractmethod
    def unwrap(self) -> T:
        """Extract value if Some, raise exception if Nothing.

        This forces explicit handling - you must handle both Some and Nothing.
        If Nothing, raises UnwrapError with optional context reason.

        Returns:
            T: The wrapped value if Some

        Raises:
            UnwrapError: If this is Nothing, includes any context reason

        Example:
            >>> Some(42).unwrap()
            42
            >>> Nothing().context("user not found").unwrap()
            # raises UnwrapError: user not found
        """
        ...

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Extract value if Some, return default if Nothing.

        Provides a safe way to handle absence with a fallback value.

        Parameters:
            default: Value to return if Nothing

        Returns:
            T: The wrapped value if Some, otherwise default

        Example:
            >>> Some(42).unwrap_or(0)
            42
            >>> Nothing().unwrap_or(0)
            0
        """
        ...

    @abstractmethod
    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        """Extract value if Some, compute default if Nothing.

        Provides a safe way to handle absence with a computed fallback.

        Parameters:
            f: Function that computes default value if needed

        Returns:
            T: The wrapped value if Some, otherwise result of f()

        Example:
            >>> Some(42).unwrap_or_else(lambda: 0)
            42
            >>> Nothing().unwrap_or_else(lambda: expensive_default())
            # expensive_default() is only called if Nothing
        """
        ...

    @abstractmethod
    def is_some(self) -> bool:
        """Check if this is Some (has a value).

        Returns:
            bool: True if Some, False if Nothing

        Example:
            >>> Some(42).is_some()
            True
            >>> Nothing().is_some()
            False
        """
        ...

    @abstractmethod
    def is_nothing(self) -> bool:
        """Check if this is Nothing (no value).

        Returns:
            bool: True if Nothing, False if Some

        Example:
            >>> Some(42).is_nothing()
            False
            >>> Nothing().is_nothing()
            True
        """
        ...

    @abstractmethod
    def inspect(self, f: Callable[[T], None]) -> "Maybe[T]":
        """Inspect value for side effects (logging, debugging, etc).

        Runs f(value) if Some, no-op if Nothing. Does not modify value.

        Parameters:
            f: Function to call with value (for side effects only)

        Returns:
            Self (for method chaining)

        Example:
            >>> Some(42).inspect(print)  # prints: 42, returns Some(42)
            >>> Nothing().inspect(print)  # no-op, returns Nothing()
        """
        ...

    @abstractmethod
    def context(self, msg: str) -> "Maybe[T]":
        """Add context message explaining why value is absent (Nothing only).

        For Nothing: Adds message to context chain explaining the absence.
        For Some: Returns self unchanged (no context on values).

        This is useful for providing diagnostic information about why
        an operation returned Nothing without treating it as an error.

        Parameters:
            msg: Context message (e.g., "user not found", "invalid id")

        Returns:
            Maybe[T]: Self with context added to chain (if Nothing)

        Example:
            >>> Nothing().context("user_id=123").context("database query failed")
            # Context chain: ["database query failed", "user_id=123"] (LIFO)

            >>> Some(42).context("invalid age")  # Some(42) - no-op
        """
        ...

    @abstractmethod
    def with_context(self, f: Callable[[], str]) -> "Maybe[T]":
        """Add lazy-evaluated context message (Nothing only).

        For Nothing: Message is computed only if accessed.
        For Some: Returns self unchanged.

        Useful when context computation is expensive.

        Parameters:
            f: Callable that returns context message

        Returns:
            Maybe[T]: Self with lazy context (if Nothing)

        Example:
            >>> Nothing().with_context(lambda: expensive_diagnostic())
            # expensive_diagnostic() only called if error is accessed
        """
        ...

    @abstractmethod
    def zip(self, other: "Maybe[U]") -> "Maybe[tuple[T, U]]":
        """Combine two Maybe values into a tuple if both are Some.

        If both are Some, returns Some((value1, value2)).
        If either is Nothing, returns Nothing.

        Parameters:
            other: Another Maybe value

        Returns:
            Maybe[tuple[T, U]]: Some with combined values, or Nothing

        Example:
            >>> Some(1).zip(Some(2))  # Some((1, 2))
            >>> Some(1).zip(Nothing())  # Nothing()
            >>> Nothing().zip(Some(2))  # Nothing()
        """
        ...

    @abstractmethod
    def zip_with(self, other: "Maybe[U]", f: Callable[[T, U], "T"]) -> "Maybe[T]":
        """Combine two Maybe values with a function if both are Some.

        If both are Some, applies f to combine them. If either is Nothing,
        returns Nothing.

        Parameters:
            other: Another Maybe value
            f: Function to combine values

        Returns:
            Maybe[T]: Some with combined result, or Nothing

        Example:
            >>> Some(1).zip_with(Some(2), lambda a, b: a + b)  # Some(3)
            >>> Some(1).zip_with(Nothing(), lambda a, b: a + b)  # Nothing()
        """
        ...
