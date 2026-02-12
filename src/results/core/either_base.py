"""Either abstract base class - the core contract layer for dual outcomes.

This module defines the Either abstract base class that all implementations
(Left and Right) must adhere to. The Either type represents a computation that
can produce one of two outcomes (Left[L] or Right[R]) without inherent success/failure
semantics, enabling flexible pattern matching and alternative branch handling.

Unlike Result which represents success/failure (and Maybe which represents
presence/absence), Either is neutral - both outcomes are equally valid. By
convention, Right is often treated as the "happy path" (right-biased), but
semantically they're symmetric.

The contract ensures:
- Explicit handling of dual outcomes without exceptions
- Type-safe transformation of both branches independently
- Chainable operations that can handle both alternatives
- Symmetric context tracking on both branches (optional)
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic

from .types import L, R, T, U, V


class Either(ABC, Generic[L, R]):
    """Abstract base class for Either type - dual outcome computation.

    Either[L, R] represents a computation that produces one of two outcomes:
    - Left[L]: First alternative (contextually may represent error, but not required)
    - Right[R]: Second alternative (contextually may represent success, but not required)

    Unlike Result[T, E] which has semantics of success/failure, and Maybe[T]
    which has semantics of presence/absence, Either is semantically neutral.
    Both Left and Right are equally valid outcomes. By convention, Either is
    often right-biased (default operations assume Right), but this is an
    implementation choice, not a semantic requirement.

    The Either type enforces explicit handling of both outcomes and supports
    chainable operations that can transform either branch independently.

    Type Parameters:
        L: The left outcome type (any type)
        R: The right outcome type (any type)

    Example:
        >>> result: Either[str, User] = fetch_user_or_error(user_id)
        >>> result = result.map(lambda u: u.name.upper())
        # Type is now: Either[str, str]
        >>> result_flipped = result.swap()
        # Type is now: Either[str, str]
    """

    @abstractmethod
    def is_left(self) -> bool:
        """Check if this is a Left instance.

        Returns:
            bool: True if Left, False if Right

        Example:
            >>> Left("error").is_left()  # True
            >>> Right(42).is_left()  # False
        """
        ...

    @abstractmethod
    def is_right(self) -> bool:
        """Check if this is a Right instance.

        Returns:
            bool: True if Right, False if Left

        Example:
            >>> Right(42).is_right()  # True
            >>> Left("error").is_right()  # False
        """
        ...

    @abstractmethod
    def left(self) -> L | None:
        """Extract Left value if present, None otherwise.

        Returns:
            L | None: The left value if Left, None if Right

        Example:
            >>> Left("error").left()  # "error"
            >>> Right(42).left()  # None
        """
        ...

    @abstractmethod
    def right(self) -> R | None:
        """Extract Right value if present, None otherwise.

        Returns:
            R | None: The right value if Right, None if Left

        Example:
            >>> Right(42).right()  # 42
            >>> Left("error").right()  # None
        """
        ...

    @abstractmethod
    def map(self, op: Callable[[R], U]) -> "Either[L, U]":
        """Transform the Right value if present, preserving Left (right-biased).

        This is the default/primary transformation operation - it assumes the
        Right branch is the "happy path" and applies the operation there.
        Left is unchanged.

        If this is Right, applies the operation to the wrapped value and returns
        a new Right with the result. If this is Left, returns self unchanged.

        Parameters:
            op: Function that transforms value of type R to type U

        Returns:
            Either[L, U]: New Either with transformed right value, or same Left

        Example:
            >>> Right(42).map(lambda x: x * 2)  # Right(84)
            >>> Left("error").map(lambda x: x * 2)  # Left("error")
        """
        ...

    @abstractmethod
    def map_left(self, op: Callable[[L], U]) -> "Either[U, R]":
        """Transform the Left value if present, preserving Right.

        This allows explicit handling of the Left branch (the alternative outcome).
        Right is unchanged.

        If this is Left, applies the operation to the wrapped value and returns
        a new Left with the result. If this is Right, returns self unchanged.

        Parameters:
            op: Function that transforms value of type L to type U

        Returns:
            Either[U, R]: New Either with transformed left value, or same Right

        Example:
            >>> Left("error").map_left(lambda x: x.upper())  # Left("ERROR")
            >>> Right(42).map_left(lambda x: x.upper())  # Right(42)
        """
        ...

    @abstractmethod
    def bimap(
        self, left_op: Callable[[L], U], right_op: Callable[[R], V]
    ) -> "Either[U, V]":
        """Transform both Left and Right simultaneously (total transformation).

        This is the most general transformation - it applies the left_op to
        Left and right_op to Right. Semantically, one of them will execute
        depending on which branch this Either is.

        Parameters:
            left_op: Function that transforms left value (L → U)
            right_op: Function that transforms right value (R → V)

        Returns:
            Either[U, V]: New Either with both branches potentially transformed

        Example:
            >>> Left("error").bimap(str.upper, lambda x: x * 2)  # Left("ERROR")
            >>> Right(42).bimap(str.upper, lambda x: x * 2)  # Right(84)
        """
        ...

    @abstractmethod
    def and_then(self, op: Callable[[R], "Either[L, U]"]) -> "Either[L, U]":
        """Chain operations that return Either instances (monadic bind, right-biased).

        Also known as flatMap or bind in functional programming.

        If this is Right, applies the operation to the wrapped value and returns
        the result (flattened). If this is Left, returns self unchanged.

        Parameters:
            op: Function that transforms right value to new Either

        Returns:
            Either[L, U]: Result of applying op to Right, or unchanged Left

        Example:
            >>> Right(42).and_then(lambda x: Right(x * 2))  # Right(84)
            >>> Right(42).and_then(lambda x: Left("error"))  # Left("error")
            >>> Left("error").and_then(lambda x: Right(x * 2))  # Left("error")
        """
        ...

    @abstractmethod
    def and_then_left(self, op: Callable[[L], "Either[U, R]"]) -> "Either[U, R]":
        """Chain operations that return Either instances (monadic bind, left-biased).

        If this is Left, applies the operation to the wrapped value and returns
        the result (flattened). If this is Right, returns self unchanged.

        Parameters:
            op: Function that transforms left value to new Either

        Returns:
            Either[U, R]: Result of applying op to Left, or unchanged Right

        Example:
            >>> Left("error").and_then_left(lambda x: Left(x.upper()))  # Left("ERROR")
            >>> Left("error").and_then_left(lambda x: Right(42))  # Right(42)
            >>> Right(42).and_then_left(lambda x: Left(x.upper()))  # Right(42)
        """
        ...

    @abstractmethod
    def or_else(self, op: Callable[[], "Either[L, U]"]) -> "Either[L, U]":
        """Provide alternative computation on Left (right-biased recovery).

        If this is Left, applies the operation (which takes no arguments,
        performing a fresh computation) and returns the result. If this is Right,
        returns self unchanged.

        Parameters:
            op: Function that returns a new Either computation (no input)

        Returns:
            Either[L, U]: Result of op if Left, or unchanged Right

        Example:
            >>> Left("error").or_else(lambda: Right(42))  # Right(42)
            >>> Left("error").or_else(lambda: Left("recovered"))  # Left("recovered")
            >>> Right(42).or_else(lambda: Right(99))  # Right(42)
        """
        ...

    @abstractmethod
    def or_else_left(self, op: Callable[[], "Either[U, R]"]) -> "Either[U, R]":
        """Provide alternative computation on Right (left-biased recovery).

        If this is Right, applies the operation and returns the result.
        If this is Left, returns self unchanged.

        Parameters:
            op: Function that returns a new Either computation (no input)

        Returns:
            Either[U, R]: Result of op if Right, or unchanged Left

        Example:
            >>> Right(42).or_else_left(lambda: Left("error"))  # Left("error")
            >>> Left("error").or_else_left(lambda: Left("another"))  # Left("error")
        """
        ...

    @abstractmethod
    def inspect(self, op: Callable[[R], None]) -> "Either[L, R]":
        """Execute side effect on Right without modifying (right-biased inspection).

        Useful for logging, printing, or other side effects while maintaining
        the Either for further chaining.

        If this is Right, calls op and returns self unchanged. If this is Left,
        returns self unchanged.

        Parameters:
            op: Function that performs side effect (no return value)

        Returns:
            Either[L, R]: Self unchanged (for chaining)

        Example:
            >>> Right(42).inspect(lambda x: print(f"Value: {x}"))  # Right(42), prints
            >>> Left("error").inspect(lambda x: print(f"Value: {x}"))  # Left("error"), no print
        """
        ...

    @abstractmethod
    def inspect_left(self, op: Callable[[L], None]) -> "Either[L, R]":
        """Execute side effect on Left without modifying (left-biased inspection).

        Useful for error logging or other diagnostics.

        If this is Left, calls op and returns self unchanged. If this is Right,
        returns self unchanged.

        Parameters:
            op: Function that performs side effect (no return value)

        Returns:
            Either[L, R]: Self unchanged (for chaining)

        Example:
            >>> Left("error").inspect_left(lambda x: print(f"Error: {x}"))  # Left("error"), prints
            >>> Right(42).inspect_left(lambda x: print(f"Error: {x}"))  # Right(42), no print
        """
        ...

    @abstractmethod
    def unwrap_right(self) -> R:
        """Extract Right value or raise exception.

        If this is Right, returns the wrapped value. If this is Left,
        raises UnwrapError with diagnostic information.

        Returns:
            R: The right value

        Raises:
            UnwrapError: If this is Left

        Example:
            >>> Right(42).unwrap_right()  # 42
            >>> Left("error").unwrap_right()  # raises UnwrapError
        """
        ...

    @abstractmethod
    def unwrap_left(self) -> L:
        """Extract Left value or raise exception.

        If this is Left, returns the wrapped value. If this is Right,
        raises UnwrapError with diagnostic information.

        Returns:
            L: The left value

        Raises:
            UnwrapError: If this is Right

        Example:
            >>> Left("error").unwrap_left()  # "error"
            >>> Right(42).unwrap_left()  # raises UnwrapError
        """
        ...

    @abstractmethod
    def unwrap_or(self, default: R) -> R:
        """Extract Right value or return default.

        If this is Right, returns the wrapped value. If this is Left,
        returns the provided default value.

        Parameters:
            default: Value to return if Left

        Returns:
            R: Either the right value or the default

        Example:
            >>> Right(42).unwrap_or(0)  # 42
            >>> Left("error").unwrap_or(0)  # 0
        """
        ...

    @abstractmethod
    def unwrap_or_else(self, op: Callable[[], R]) -> R:
        """Extract Right value or compute from Left.

        If this is Right, returns the wrapped value. If this is Left,
        calls op (which takes no arguments) and returns the result.

        Parameters:
            op: Function that computes default value

        Returns:
            R: Either the right value or computed default

        Example:
            >>> Right(42).unwrap_or_else(lambda: 0)  # 42
            >>> Left("error").unwrap_or_else(lambda: 0)  # 0
        """
        ...

    @abstractmethod
    def fold(self, left_op: Callable[[L], T], right_op: Callable[[R], T]) -> T:
        """Reduce Either to single value (catamorphism - total deconstruction).

        Applies one of two functions depending on which branch this Either is,
        returning a single value T that represents both outcomes.

        Parameters:
            left_op: Function to apply if Left (L → T)
            right_op: Function to apply if Right (R → T)

        Returns:
            T: Unified result from either branch

        Example:
            >>> Left("error").fold(str.upper, lambda x: str(x * 2))
            # "ERROR"
            >>> Right(42).fold(str.upper, lambda x: str(x * 2))
            # "84"
        """
        ...

    @abstractmethod
    def swap(self) -> "Either[R, L]":
        """Exchange Left and Right (flip the Either).

        Parameters:
            None

        Returns:
            Either[R, L]: New Either with branches swapped

        Example:
            >>> Left("error").swap()  # Right("error")
            >>> Right(42).swap()  # Left(42)
        """
        ...

    @abstractmethod
    def context(self, msg: str) -> "Either[L, R]":
        """Add context message (diagnostic information).

        Pushes the message onto the context chain for later inspection.
        For Left variant, this is used for error diagnostics. For Right,
        can be used for decision tracking or other metadata.

        Parameters:
            msg: Context message to add

        Returns:
            Either[L, R]: Self with context added (new instance)

        Example:
            >>> Left("error").context("at user validation")
            # Left with context chain: ["at user validation", ...]
        """
        ...

    @abstractmethod
    def with_context(self, op: Callable[[], str]) -> "Either[L, R]":
        """Add lazily-computed context message.

        Like context(), but computes the message only if this is called
        (lazy evaluation). Useful for expensive diagnostics.

        Parameters:
            op: Function that returns context message

        Returns:
            Either[L, R]: Self with context added (new instance)

        Example:
            >>> Left("error").with_context(lambda: expensive_debug_info())
        """
        ...
