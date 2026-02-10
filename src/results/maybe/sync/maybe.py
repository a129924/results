"""Some variant implementation for Maybe type - presence of value.

This module implements Some[T], representing the presence of a value in the
Maybe type system. Some is an immutable, frozen dataclass that wraps a value
and supports all Maybe operations in a value-preserving manner.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic

from typing_extensions import override

from ...core.context import ContextChain
from ...core.maybe_base import Maybe
from ...core.types import T, U


@dataclass(frozen=True)
class Some(Maybe[T], Generic[T]):
    """Immutable Some variant - represents the presence of a value.

    Some[T] wraps a value of type T and propagates it through transformations.
    When operations preserve the value or compute new values, they return
    Some. Some never has a context chain (no absence to explain).

    Attributes:
        value: The wrapped value of type T
        _context_chain: Always empty for Some (no context needed for presence)

    Example:
        >>> user_age = Some(25)
        >>> user_name = Some("Alice")
        >>> user_age.map(lambda age: age + 1)  # Some(26)
        >>> user_age.zip(user_name)  # Some((25, "Alice"))
    """

    value: T
    _context_chain: ContextChain = ContextChain()

    @override
    def map(self, op: Callable[[T], U]) -> Maybe[U]:
        """Apply transformation to value, returning new Some.

        Args:
            op: Function T -> U

        Returns:
            Some[U] with transformed value
        """
        return Some(op(self.value))

    @override
    def filter(self, predicate: Callable[[T], bool]) -> Maybe[T]:
        """Filter value: Some if predicate(value), Nothing otherwise.

        Args:
            predicate: Function T -> bool

        Returns:
            Some if predicate(value) is True, Nothing with no context otherwise
        """
        if predicate(self.value):
            return self
        return Nothing()

    @override
    def and_then(self, op: Callable[[T], Maybe[U]]) -> Maybe[U]:
        """Apply operation returning Maybe, flatten result.

        Args:
            op: Function T -> Maybe[U]

        Returns:
            Result of op(value) (already flattened)
        """
        return op(self.value)

    @override
    def or_else(self, op: Callable[[], Maybe[T]]) -> Maybe[T]:
        """Some has value, ignore alternative.

        Args:
            op: Alternative computation (ignored)

        Returns:
            self (Some)
        """
        return self

    @override
    def unwrap(self) -> T:
        """Extract the value.

        Returns:
            The wrapped value T

        Example:
            >>> Some(42).unwrap()
            42
        """
        return self.value

    @override
    def unwrap_or(self, default: T) -> T:
        """Return value (default ignored).

        Args:
            default: Ignored

        Returns:
            The wrapped value
        """
        return self.value

    @override
    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        """Return value (computation ignored).

        Args:
            f: Ignored

        Returns:
            The wrapped value
        """
        return self.value

    @override
    def is_some(self) -> bool:
        """Some always has value.

        Returns:
            True
        """
        return True

    @override
    def is_nothing(self) -> bool:
        """Some is not Nothing.

        Returns:
            False
        """
        return False

    @override
    def inspect(self, f: Callable[[T], None]) -> Maybe[T]:
        """Execute f(value) for side effects.

        Args:
            f: Side effect function

        Returns:
            self (for chaining)
        """
        f(self.value)
        return self

    @override
    def context(self, msg: str) -> Maybe[T]:
        """Some has no absence to explain, no-op.

        Args:
            msg: Ignored

        Returns:
            self (Some)
        """
        return self

    @override
    def with_context(self, f: Callable[[], str]) -> Maybe[T]:
        """Some has no absence to explain, no-op.

        Args:
            f: Ignored (never called)

        Returns:
            self (Some)
        """
        return self

    @override
    def zip(self, other: Maybe[U]) -> Maybe[tuple[T, U]]:
        """Combine with another Maybe if both Some.

        Args:
            other: Another Maybe

        Returns:
            Some with combined values, or Nothing otherwise
        """
        if isinstance(other, Some):
            return Some((self.value, other.value))
        # other is Nothing, return as is
        return other  # type: ignore[return-value]

    @override
    def zip_with(self, other: Maybe[U], f: Callable[[T, U], T]) -> Maybe[T]:
        """Combine with another Maybe using function if both Some.

        Args:
            other: Another Maybe
            f: Combining function (T, U) -> T

        Returns:
            Some with combined result, or Nothing otherwise
        """
        if isinstance(other, Some):
            return Some(f(self.value, other.value))
        # other is Nothing, return as is
        return other  # type: ignore[return-value]


@dataclass(frozen=True)
class Nothing(Maybe[T], Generic[T]):
    """Immutable Nothing variant - represents absence of value.

    Nothing represents the absence of a value (like Python's None, but type-safe).
    Nothing is NOT an error, just an expected case.

    Attributes:
        _reason: Optional reason why value is absent (e.g., "not found")
        _context_chain: LIFO stack of diagnostic context messages

    Example:
        >>> def find_user(user_id: int) -> Maybe[User]:
        ...     if user_id < 0:
        ...         return Nothing().context("invalid user_id")
        ...     # ... database lookup ...
        ...     return Nothing().context("user not found")
    """

    _reason: str | None = None
    _context_chain: ContextChain = ContextChain()

    @override
    def map(self, op: Callable[[T], U]) -> Maybe[U]:
        """Nothing propagates through transformations.

        Args:
            op: Ignored

        Returns:
            Nothing with same context
        """
        # Return Nothing cast as Maybe[U]
        return Nothing()

    @override
    def filter(self, predicate: Callable[[T], bool]) -> Maybe[T]:
        """Nothing propagates unchanged.

        Args:
            predicate: Ignored

        Returns:
            self (Nothing)
        """
        return self

    @override
    def and_then(self, op: Callable[[T], Maybe[U]]) -> Maybe[U]:
        """Nothing short-circuits the chain.

        Args:
            op: Ignored

        Returns:
            Nothing (short-circuit)
        """
        # Return Nothing cast as Maybe[U]
        return Nothing()

    @override
    def or_else(self, op: Callable[[], Maybe[T]]) -> Maybe[T]:
        """Execute alternative when Nothing.

        Args:
            op: Alternative computation

        Returns:
            Result of op()
        """
        return op()

    @override
    def unwrap(self) -> T:
        """Raise error, forcing explicit handling.

        Returns:
            Never (always raises)

        Raises:
            UnwrapError: Always, with context chain if available
        """
        from ...exceptions import UnwrapError

        msg = "called `unwrap()` on Nothing"
        raise UnwrapError(
            msg,
            original_error=self._reason or "Nothing",
            context_chain=self._context_chain.messages,
        )

    @override
    def unwrap_or(self, default: T) -> T:
        """Return default value.

        Args:
            default: Fallback value

        Returns:
            default
        """
        return default

    @override
    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        """Compute and return default value.

        Args:
            f: Computation for fallback

        Returns:
            f()
        """
        return f()

    @override
    def is_some(self) -> bool:
        """Nothing is not Some.

        Returns:
            False
        """
        return False

    @override
    def is_nothing(self) -> bool:
        """Nothing is always Nothing.

        Returns:
            True
        """
        return True

    @override
    def inspect(self, f: Callable[[T], None]) -> Maybe[T]:
        """Nothing has no value to inspect, no-op.

        Args:
            f: Ignored

        Returns:
            self (Nothing)
        """
        return self

    @override
    def context(self, msg: str) -> Maybe[T]:
        """Add context message to chain.

        Args:
            msg: Context message to add

        Returns:
            New Nothing with message prepended to context chain (LIFO)
        """
        return Nothing(
            _reason=self._reason,
            _context_chain=self._context_chain.push(msg),
        )

    @override
    def with_context(self, f: Callable[[], str]) -> Maybe[T]:
        """Add lazy-evaluated context message.

        Args:
            f: Callable that returns context message

        Returns:
            New Nothing with lazy context
        """
        return Nothing(
            _reason=self._reason,
            _context_chain=self._context_chain.push_lazy(f),
        )

    @override
    def zip(self, other: Maybe[U]) -> Maybe[tuple[T, U]]:
        """Nothing propagates through zip.

        Args:
            other: Ignored

        Returns:
            self (Nothing)
        """
        return self  # type: ignore[return-value]

    @override
    def zip_with(self, other: Maybe[U], f: Callable[[T, U], T]) -> Maybe[T]:
        """Nothing propagates through zip_with.

        Args:
            other: Ignored
            f: Ignored

        Returns:
            self (Nothing)
        """
        return self
