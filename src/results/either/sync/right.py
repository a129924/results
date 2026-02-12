"""Right[R] - Represents right outcome of Either type.

This module implements the Right variant of Either[L, R], containing a right value.
Right is immutable (frozen dataclass) and implements all Either ABC methods.
Right supports context chains (symmetric design, unlike Result).

Exported:
    Right: Concrete Right implementation
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

__all__ = ["Right"]


@dataclass(frozen=True)
class Right(Either[L, R], Generic[L, R]):
    """Represents right outcome with value of type R.

    Right[L, R] is one of the two variants of Either[L, R]. It contains a value
    of type R and implements all Either abstract methods. Right-focused operations
    (map, and_then, or_else) execute on Right. Left-focused operations
    (map_left, and_then_left, or_else_left) short-circuit on Right.

    The Right class is immutable (frozen dataclass) and uses @override decorators
    to enforce proper implementation of the Either ABC contract.

    Type Parameters:
        L: The type of the left value (unused in Right but preserved for Either[L, R])
        R: The type of the right value (any type, conventionally success-like but no requirement)

    Attributes:
        _value (R): The right value - private attribute accessible via right() method
        _context_chain (ContextChain): Chain of context messages in LIFO order.
            - Empty ContextChain by default
            - Newest context at index 0 (accessed first when unwrapping)
            - Oldest context at index -1 (appended last)
            - Used for decision tracking or other right-side diagnostics

    Example:
        >>> from results import Left, Right
        >>> result: Either[str, User] = Right(User(name="Alice"))
        >>> result.is_right()
        True
        >>> result.right()
        User(name="Alice")
        >>> result.left()
        None
        >>> result.map(lambda u: u.name.upper()).is_right()
        True

        >>> # Context chain example
        >>> result = Right(42)
        >>> result = result.context("computed value")
        >>> result = result.context("after validation")
        >>> result._context_chain
        ('after validation', 'computed value')
    """

    _value: R
    _context_chain: ContextChain = field(
        default_factory=ContextChain, repr=False, compare=False
    )

    @override
    def is_left(self) -> bool:
        """Check if this is Left variant.

        Returns:
            bool: Always False for Right variant.

        Example:
            >>> Right(42).is_left()
            False
        """
        return False

    @override
    def is_right(self) -> bool:
        """Check if this is Right variant.

        Returns:
            bool: Always True for Right variant.

        Example:
            >>> Right(42).is_right()
            True
        """
        return True

    @override
    def left(self) -> L | None:
        """Return left value if present.

        Returns:
            None: Right has no left value

        Example:
            >>> Right(42).left()
            None
        """
        return None

    @override
    def right(self) -> R | None:
        """Return right value if present.

        Returns:
            R: The right value

        Example:
            >>> Right(42).right()
            42
        """
        return self._value

    @override
    def map(self, op: Callable[[R], U]) -> Either[L, U]:
        """Right-focused transformation (executes on Right).

        Args:
            op: Function that transforms right value (R → U)

        Returns:
            Either[L, U]: New Right with transformed value

        Example:
            >>> Right(42).map(lambda x: x * 2)
            # Right(84)
        """
        return Right(op(self._value), self._context_chain)

    @override
    def map_left(self, op: Callable[[L], U]) -> Either[U, R]:
        """Left-focused transformation (short-circuits on Right).

        Args:
            op: Ignored (applied to Left only)

        Returns:
            Either[U, R]: Self cast to Either[U, R] (short-circuit)

        Example:
            >>> Right(42).map_left(str.upper)
            # Right(42)
        """
        # Right is unchanged by left-focused operations
        return self  # type: ignore

    @override
    def bimap(
        self, left_op: Callable[[L], U], right_op: Callable[[R], V]
    ) -> Either[U, V]:
        """Transform both branches simultaneously.

        Args:
            left_op: Ignored (applied to Left only)
            right_op: Function to apply to right value (R → V)

        Returns:
            Either[U, V]: New Right with transformed right value

        Example:
            >>> Right(42).bimap(str.upper, lambda x: x * 2)
            # Right(84)
        """
        return Right(right_op(self._value), self._context_chain)

    @override
    def and_then(self, op: Callable[[R], Either[L, U]]) -> Either[L, U]:
        """Right-focused monadic chain (executes on Right).

        Args:
            op: Function that transforms right value to new Either (R → Either[L, U])

        Returns:
            Either[L, U]: Result of op (flattened)

        Example:
            >>> Right(42).and_then(lambda x: Right(x * 2))
            # Right(84)
            >>> Right(42).and_then(lambda x: Left("error"))
            # Left("error")
        """
        return op(self._value)

    @override
    def and_then_left(self, op: Callable[[L], Either[U, R]]) -> Either[U, R]:
        """Left-focused monadic chain (short-circuits on Right).

        Args:
            op: Ignored (applied to Left only)

        Returns:
            Either[U, R]: Self cast to Either[U, R] (short-circuit)

        Example:
            >>> Right(42).and_then_left(lambda x: Left(x.upper()))
            # Right(42)
        """
        # Right is unchanged by left-focused operations
        return self  # type: ignore

    @override
    def or_else(self, op: Callable[[], Either[L, U]]) -> Either[L, U]:
        """Right-focused recovery (short-circuits on Right).

        Args:
            op: Ignored (applied to Left only)

        Returns:
            Either[L, U]: Self cast to Either[L, U] (short-circuit, keep Right as-is)

        Example:
            >>> Right(42).or_else(lambda: Right(99))
            # Right(42)
        """
        # Right is unchanged by right-focused recovery
        return self  # type: ignore

    @override
    def or_else_left(self, op: Callable[[], Either[U, R]]) -> Either[U, R]:
        """Left-focused recovery (executes on Right).

        Args:
            op: Alternative computation that returns new Either

        Returns:
            Either[U, R]: Result of op (fresh computation)

        Example:
            >>> Right(42).or_else_left(lambda: Left("error"))
            # Left("error")
            >>> Right(42).or_else_left(lambda: Right(99))
            # Right(99)
        """
        return op()

    @override
    def inspect(self, op: Callable[[R], None]) -> Either[L, R]:
        """Right-focused side effect (executes on Right).

        Args:
            op: Function that performs side effect

        Returns:
            Either[L, R]: Self unchanged (for chaining)

        Example:
            >>> Right(42).inspect(lambda x: print(f"Value: {x}"))
            # Right(42), prints "Value: 42"
        """
        op(self._value)
        return self

    @override
    def inspect_left(self, op: Callable[[L], None]) -> Either[L, R]:
        """Left-focused side effect (no-op on Right).

        Args:
            op: Ignored (applied to Left only)

        Returns:
            Either[L, R]: Self unchanged

        Example:
            >>> Right(42).inspect_left(lambda x: print(f"Error: {x}"))
            # Right(42), no print
        """
        return self

    @override
    def unwrap_right(self) -> R:
        """Extract right value (always succeeds on Right).

        Returns:
            R: The right value

        Example:
            >>> Right(42).unwrap_right()
            # 42
        """
        return self._value

    @override
    def unwrap_left(self) -> L:
        """Extract left value or raise exception.

        Returns:
            Never (always raises on Right)

        Raises:
            UnwrapError: Always on Right variant

        Example:
            >>> Right(42).unwrap_left()
            # UnwrapError: called `unwrap_left()` on Right
        """
        msg = "called `unwrap_left()` on Right"
        raise UnwrapError(
            msg,
            original_error=self._value,
            context_chain=self._context_chain.messages,
        )

    @override
    def unwrap_or(self, default: R) -> R:
        """Extract right value or return default.

        Args:
            default: Ignored (Right always has a value)

        Returns:
            R: The right value

        Example:
            >>> Right(42).unwrap_or(0)
            # 42
        """
        return self._value

    @override
    def unwrap_or_else(self, op: Callable[[], R]) -> R:
        """Extract right value or compute default.

        Args:
            op: Ignored (Right always has a value)

        Returns:
            R: The right value

        Example:
            >>> Right(42).unwrap_or_else(lambda: 0)
            # 42
        """
        return self._value

    @override
    def fold(self, left_op: Callable[[L], T], right_op: Callable[[R], T]) -> T:
        """Reduce to single value (apply right_op to Right).

        Args:
            left_op: Ignored (applied to Left only)
            right_op: Function to apply to right value (R → T)

        Returns:
            T: Result of right_op

        Example:
            >>> Right(42).fold(str.upper, lambda x: str(x * 2))
            # "84"
        """
        return right_op(self._value)

    @override
    def swap(self) -> Either[R, L]:
        """Exchange left and right (flip the Either).

        Returns:
            Either[R, L]: Left with value, swapped type parameters

        Example:
            >>> Right(42).swap()
            # Left(42) but typed as Either[int, Any]
        """
        from .left import Left

        return Left(self._value, self._context_chain)

    @override
    def context(self, msg: str) -> Either[L, R]:
        """Add context message to the chain.

        Args:
            msg: Diagnostic message to push

        Returns:
            Either[L, R]: New Right with context added

        Example:
            >>> Right(42).context("at value computation")
            # Right with context chain appended
        """
        new_context = self._context_chain.push(msg)
        return Right(self._value, new_context)

    @override
    def with_context(self, op: Callable[[], str]) -> Either[L, R]:
        """Add lazily-computed context message.

        Args:
            op: Function that returns context message (evaluated only if called)

        Returns:
            Either[L, R]: New Right with context added

        Example:
            >>> Right(42).with_context(lambda: expensive_debug_info())
        """
        new_context = self._context_chain.push_lazy(op)
        return Right(self._value, new_context)
