"""Left[L] - Represents left outcome of Either type.

This module implements the Left variant of Either[L, R], containing a left value.
Left is immutable (frozen dataclass) and implements all Either ABC methods.
Left supports context chains (symmetric design, unlike Result which only has context on Err).

Exported:
    Left: Concrete Left implementation
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Generic

from typing_extensions import override

from ...core.context import ContextChain
from ...core.either_base import Either
from ...core.types import L, R, T, U, V
from ...exceptions import UnwrapError

__all__ = ["Left"]


@dataclass(frozen=True)
class Left(Either[L, R], Generic[L, R]):
    """Represents left outcome with value of type L.

    Left[L, R] is one of the two variants of Either[L, R]. It contains a value
    of type L and implements all Either abstract methods. Right-focused operations
    (map, and_then, or_else) short-circuit on Left. Left-focused operations
    (map_left, and_then_left, or_else_left) execute.

    The Left class is immutable (frozen dataclass) and uses @override decorators
    to enforce proper implementation of the Either ABC contract.

    Type Parameters:
        L: The type of the left value (any type, conventionally error-like but no requirement)
        R: The type of the right value (unused in Left but preserved for Either[L, R])

    Attributes:
        _value (L): The left value - private attribute accessible via left() method
        _context_chain (ContextChain): Chain of context messages in LIFO order.
            - Empty ContextChain by default
            - Newest context at index 0 (accessed first when unwrapping)
            - Oldest context at index -1 (appended last)
            - Used for diagnostic information about the left outcome

    Example:
        >>> from results import Left, Right
        >>> result: Either[str, User] = Left("user not found")
        >>> result.is_left()
        True
        >>> result.left()
        "user not found"
        >>> result.right()
        None
        >>> result.map(lambda u: u.name).is_left()
        True

        >>> # Context chain example
        >>> result = Left("connection timeout")
        >>> result = result.context("trying primary database")
        >>> result = result.context("fetching user profile")
        >>> result._context_chain
        ('fetching user profile', 'trying primary database')
    """

    _value: L
    _context_chain: ContextChain = field(
        default_factory=ContextChain, repr=False, compare=False
    )

    @override
    def is_left(self) -> bool:
        """Check if this is Left variant.

        Returns:
            bool: Always True for Left variant.

        Example:
            >>> Left("error").is_left()
            True
        """
        return True

    @override
    def is_right(self) -> bool:
        """Check if this is Right variant.

        Returns:
            bool: Always False for Left variant.

        Example:
            >>> Left("error").is_right()
            False
        """
        return False

    @override
    def left(self) -> L | None:
        """Return left value if present.

        Returns:
            L: The left value

        Example:
            >>> Left("error").left()
            "error"
        """
        return self._value

    @override
    def right(self) -> R | None:
        """Return right value if present.

        Returns:
            None: Left has no right value

        Example:
            >>> Left("error").right()
            None
        """
        return None

    @override
    def map(self, op: Callable[[R], U]) -> Either[L, U]:
        """Right-focused transformation (short-circuits on Left).

        Args:
            op: Ignored (applied to Right only)

        Returns:
            Either[L, U]: Self cast to Either[L, U] (short-circuit)

        Example:
            >>> Left("error").map(lambda x: x * 2)
            # Left("error")
        """
        # Left is unchanged by right-focused operations
        return self  # type: ignore[return-value]  # Left[L, R] 是 Either[L, U] 的合法變體

    @override
    def map_left(self, op: Callable[[L], U]) -> Either[U, R]:
        """Left-focused transformation (executes on Left).

        Args:
            op: Function that transforms left value (L → U)

        Returns:
            Either[U, R]: New Left with transformed value

        Example:
            >>> Left("error").map_left(str.upper)
            # Left("ERROR")
        """
        return Left(op(self._value), self._context_chain)

    @override
    def bimap(
        self, left_op: Callable[[L], U], right_op: Callable[[R], V]
    ) -> Either[U, V]:
        """Transform both branches simultaneously.

        Args:
            left_op: Function to apply to left value (L → U)
            right_op: Ignored (applied to Right only)

        Returns:
            Either[U, V]: New Left with transformed left value

        Example:
            >>> Left("error").bimap(str.upper, lambda x: x * 2)
            # Left("ERROR")
        """
        return Left(left_op(self._value), self._context_chain)

    @override
    def and_then(self, op: Callable[[R], Either[L, U]]) -> Either[L, U]:
        """Right-focused monadic chain (short-circuits on Left).

        Args:
            op: Ignored (applied to Right only)

        Returns:
            Either[L, U]: Self cast to Either[L, U] (short-circuit)

        Example:
            >>> Left("error").and_then(lambda x: Right(x * 2))
            # Left("error")
        """
        # Left is unchanged by right-focused operations
        return self  # type: ignore[return-value]  # Left[L, R] ⊆ Either[L, U]（協變）

    @override
    def and_then_left(self, op: Callable[[L], Either[U, R]]) -> Either[U, R]:
        """Left-focused monadic chain (executes on Left).

        Args:
            op: Function that transforms left value to new Either (L → Either[U, R])

        Returns:
            Either[U, R]: Result of op (flattened)

        Example:
            >>> Left("error").and_then_left(lambda x: Left(x.upper()))
            # Left("ERROR")
            >>> Left("error").and_then_left(lambda x: Right(42))
            # Right(42)
        """
        return op(self._value)

    @override
    def or_else(self, op: Callable[[], Either[L, U]]) -> Either[L, U]:
        """Right-focused recovery (executes on Left).

        Args:
            op: Alternative computation that returns new Either

        Returns:
            Either[L, U]: Result of op (fresh computation)

        Example:
            >>> Left("error").or_else(lambda: Right(42))
            # Right(42)
            >>> Left("error").or_else(lambda: Left("recovered"))
            # Left("recovered")
        """
        return op()

    @override
    def or_else_left(self, op: Callable[[], Either[U, R]]) -> Either[U, R]:
        """Left-focused recovery (short-circuits on Left).

        Args:
            op: Ignored (applied to Right only)

        Returns:
            Either[U, R]: Self cast to Either[U, R] (short-circuit, keep Left as-is)

        Example:
            >>> Left("error").or_else_left(lambda: Left("another"))
            # Left("error")
        """
        # Left is unchanged by left-focused recovery
        return self  # type: ignore[return-value]  # Left[L, R] -> Either[U, R]（L 不變於 U）

    @override
    def inspect(self, op: Callable[[R], None]) -> Either[L, R]:
        """Right-focused side effect (no-op on Left).

        Args:
            op: Ignored (applied to Right only)

        Returns:
            Either[L, R]: Self unchanged

        Example:
            >>> Left("error").inspect(lambda x: print(f"Value: {x}"))
            # Left("error"), no print
        """
        return self

    @override
    def inspect_left(self, op: Callable[[L], None]) -> Either[L, R]:
        """Left-focused side effect (executes on Left).

        Args:
            op: Function that performs side effect

        Returns:
            Either[L, R]: Self unchanged (for chaining)

        Example:
            >>> Left("error").inspect_left(lambda x: print(f"Error: {x}"))
            # Left("error"), prints "Error: error"
        """
        op(self._value)
        return self

    @override
    def unwrap_right(self) -> R:
        """Extract right value or raise exception.

        Returns:
            Never (always raises on Left)

        Raises:
            UnwrapError: Always on Left variant

        Example:
            >>> Left("error").unwrap_right()
            # UnwrapError: called `unwrap_right()` on Left
        """
        msg = "called `unwrap_right()` on Left"
        raise UnwrapError(
            msg,
            original_error=self._value,
            context_chain=self._context_chain.messages,
        )

    @override
    def unwrap_left(self) -> L:
        """Extract left value (always succeeds on Left).

        Returns:
            L: The left value

        Example:
            >>> Left("error").unwrap_left()
            # "error"
        """
        return self._value

    @override
    def unwrap_or(self, default: R) -> R:
        """Extract right value or return default.

        Args:
            default: Fallback value for Left

        Returns:
            R: Always returns default on Left

        Example:
            >>> Left("error").unwrap_or(0)
            # 0
        """
        return default

    @override
    def unwrap_or_else(self, op: Callable[[], R]) -> R:
        """Extract right value or compute default.

        Args:
            op: Alternative computation for Left

        Returns:
            R: Result of op() on Left

        Example:
            >>> Left("error").unwrap_or_else(lambda: 0)
            # 0
        """
        return op()

    @override
    def fold(self, left_op: Callable[[L], T], right_op: Callable[[R], T]) -> T:
        """Reduce to single value (apply left_op to Left).

        Args:
            left_op: Function to apply to left value (L → T)
            right_op: Ignored (applied to Right only)

        Returns:
            T: Result of left_op

        Example:
            >>> Left("error").fold(str.upper, lambda x: str(x * 2))
            # "ERROR"
        """
        return left_op(self._value)

    @override
    def swap(self) -> Either[R, L]:
        """Exchange left and right (flip the Either).

        Returns:
            Either[R, L]: Right with value, swapped type parameters

        Example:
            >>> Left("error").swap()
            # Right("error") but typed as Either[Any, str]
        """
        from .right import Right

        return Right(self._value, self._context_chain)

    @override
    def context(self, msg: str) -> Either[L, R]:
        """Add context message to the chain.

        Args:
            msg: Diagnostic message to push

        Returns:
            Either[L, R]: New Left with context added

        Example:
            >>> Left("error").context("at user validation")
            # Left with context chain appended
        """
        new_context = self._context_chain.push(msg)
        return Left(self._value, new_context)

    @override
    def with_context(self, op: Callable[[], str]) -> Either[L, R]:
        """Add lazily-computed context message.

        Args:
            op: Function that returns context message (evaluated only if called)

        Returns:
            Either[L, R]: New Left with context added

        Example:
            >>> Left("error").with_context(lambda: expensive_debug_info())
        """
        new_context = self._context_chain.push_lazy(op)
        return Left(self._value, new_context)
