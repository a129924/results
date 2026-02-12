"""AsyncEither abstract base class - async/await support for Either.

This module defines the AsyncEither abstract base class that async implementations
of Either must adhere to. AsyncEither wraps an Awaitable[Either[L, R]] and provides
async transformation methods (map_async, and_then_async, etc.) that accumulate
into an operation queue evaluated atomically when awaited.

The AsyncEither type maintains the same semantics as Either (two outcomes: Left/Right,
not success/failure) with async support for long-running operations.

Key difference from Either:
- Cannot inspect concrete Left/Right until awaited
- Provides async variants of transformation methods
- Right-biased semantics (default ops on Right)
- Symmetric context chains on both branches
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Iterator
from typing import TYPE_CHECKING, Generic

from .types import L, R, U, V

if TYPE_CHECKING:
    from .either_base import Either


class AsyncEitherBase(ABC, Generic[L, R]):
    """Abstract base class for AsyncEither - awaitable wrapper for Either[L, R].

    AsyncEither[L, R] wraps an Awaitable[Either[L, R]] and provides async methods
    (map_async, and_then_async, etc.) that accumulate into an operation queue.
    The queue is evaluated atomically when the AsyncEither is awaited, reducing
    branching complexity.

    Right-biased semantics: Default operations (map, and_then, or_else) work on Right.
    Left-focused operations (map_left_async, and_then_left_async, etc.) explicitly
    handle the Left branch.

    Invariants:
    - Frozen dataclass (immutable)
    - Context stack (LIFO tuple) grows via context()/with_context()
    - Await returns concrete Either[L, R] (Left or Right)
    - Both Left and Right branches have symmetric context chains

    Type Parameters:
        L: Left outcome type (typically error-like, but symmetric)
        R: Right outcome type (typically success-like, but symmetric)

    Example:
        Create from sync Either:
            >>> from results import Right, AsyncEither
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> either = await async_either  # Either[Any, int]

        Create from async operation:
            >>> async def fetch_user(id: int) -> Either[str, User]:
            ...     try:
            ...         user = await api.get(id)
            ...         return Right(user) if user else Left("Not found")
            ...     except Exception as e:
            ...         return Left(str(e))
            >>> async_either = AsyncEither.from_awaitable(fetch_user(123))
            >>> name = await async_either.map_async(lambda u: u.name).unwrap_right_or_async("Unknown")

        Chain async operations with context:
            >>> async_either = AsyncEither.from_either(Right(5))
            >>> result = await (
            ...     async_either
            ...     .context("fetching")
            ...     .map_async(async_double)
            ...     .context("processing")
            ... )
    """

    @abstractmethod
    def __await__(self) -> Iterator[Either[L, R]]:
        """Enable await AsyncEither to return Either[L, R].

        When awaited, resolves the async operation and returns the concrete
        Either[L, R] (Left or Right).

        Returns:
            Either[L, R]: The resolved Either after evaluating operation queue

        Example:
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> either = await async_either  # Right(42)
        """
        ...

    @abstractmethod
    def is_right_async(self) -> Awaitable[bool]:
        """Check if value is Right asynchronously.

        Returns:
            Awaitable[bool]: True if Right, False if Left

        Example:
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> result = await async_either.is_right_async()  # True
        """
        ...

    @abstractmethod
    def is_left_async(self) -> Awaitable[bool]:
        """Check if value is Left asynchronously.

        Returns:
            Awaitable[bool]: True if Left, False if Right

        Example:
            >>> async_either = AsyncEither.from_either(Left("error"))
            >>> result = await async_either.is_left_async()  # True
        """
        ...

    @abstractmethod
    def map_async(self, fn: Callable[[R], Awaitable[U]]) -> AsyncEitherBase[L, U]:
        """Transform Right value asynchronously, short-circuit if Left (right-biased).

        If value is Right, awaits fn(value) and returns AsyncEither with result.
        If value is Left, short-circuits and returns AsyncEither[Left].
        Context stack is preserved across the transformation.

        Parameters:
            fn: Async function R → Awaitable[U]

        Returns:
            AsyncEitherBase[L, U]: New AsyncEither with transformed Right or unchanged Left

        Example:
            >>> async_either = AsyncEither.from_either(Right(5))
            >>> async def double(x: int) -> int:
            ...     await asyncio.sleep(0)
            ...     return x * 2
            >>> result = await async_either.map_async(double)
            >>> # result.unwrap_right() == 10
        """
        ...

    @abstractmethod
    def map_left_async(self, fn: Callable[[L], Awaitable[V]]) -> AsyncEitherBase[V, R]:
        """Transform Left value asynchronously, short-circuit if Right (left-focused).

        If value is Left, awaits fn(value) and returns AsyncEither with result.
        If value is Right, short-circuits and returns AsyncEither[Right].
        Context stack is preserved across the transformation.

        Parameters:
            fn: Async function L → Awaitable[V]

        Returns:
            AsyncEitherBase[V, R]: New AsyncEither with transformed Left or unchanged Right

        Example:
            >>> async_either = AsyncEither.from_either(Left("error"))
            >>> async def enhance_error(e: str) -> str:
            ...     await asyncio.sleep(0)
            ...     return f"Enhanced: {e}"
            >>> result = await async_either.map_left_async(enhance_error)
            >>> # result.unwrap_left() == "Enhanced: error"
        """
        ...

    @abstractmethod
    def and_then_async(
        self, fn: Callable[[R], Awaitable[Either[L, U]]]
    ) -> AsyncEitherBase[L, U]:
        """Chain async operations on Right returning Either, flattening (right-biased).

        If value is Right, awaits fn(value) and returns the result as AsyncEither.
        If value is Left, short-circuits and returns AsyncEither[Left].

        Parameters:
            fn: Function R → Awaitable[Either[L, U]]

        Returns:
            AsyncEitherBase[L, U]: Chained result, flattened

        Example:
            >>> async def validate_positive(x: int) -> Either[str, int]:
            ...     return Right(x) if x > 0 else Left("not positive")
            >>> async_either = AsyncEither.from_either(Right(5))
            >>> result = await async_either.and_then_async(
            ...     lambda x: asyncio.sleep(0) or validate_positive(x)
            ... )
        """
        ...

    @abstractmethod
    def and_then_left_async(
        self, fn: Callable[[L], Awaitable[Either[V, R]]]
    ) -> AsyncEitherBase[V, R]:
        """Chain async operations on Left returning Either, flattening (left-focused).

        If value is Left, awaits fn(value) and returns the result as AsyncEither.
        If value is Right, short-circuits and returns AsyncEither[Right].

        Parameters:
            fn: Function L → Awaitable[Either[V, R]]

        Returns:
            AsyncEitherBase[V, R]: Chained result, flattened

        Example:
            >>> async def recover_from_error(e: str) -> Either[str, int]:
            ...     return Right(99) if "recoverable" in e else Left(e)
            >>> async_either = AsyncEither.from_either(Left("recoverable error"))
            >>> result = await async_either.and_then_left_async(recover_from_error)
        """
        ...

    @abstractmethod
    def or_else_async(
        self, fn: Callable[[L], Awaitable[Either[V, R]]]
    ) -> AsyncEitherBase[V, R]:
        """Provide alternative async operation if Left, short-circuit if Right (right-biased).

        If value is Right, returns self unchanged.
        If value is Left, awaits fn(value) and returns result as AsyncEither.

        Parameters:
            fn: Async function returning Either[V, R]

        Returns:
            AsyncEitherBase[V, R]: Self if Right, or result of fn() if Left

        Example:
            >>> async def fetch_default() -> Either[str, int]:
            ...     return Right(99)
            >>> async_either = AsyncEither.from_either(Left("error"))
            >>> result = await async_either.or_else_async(fetch_default)
            >>> # result.unwrap_right() == 99
        """
        ...

    @abstractmethod
    def or_else_left_async(
        self, fn: Callable[[R], Awaitable[Either[L, U]]]
    ) -> AsyncEitherBase[L, U]:
        """Provide alternative async operation if Right, short-circuit if Left (left-focused).

        If value is Left, returns self unchanged.
        If value is Right, awaits fn(value) and returns result as AsyncEither.

        Parameters:
            fn: Async function returning Either[L, U]

        Returns:
            AsyncEitherBase[L, U]: Self if Left, or result of fn() if Right

        Example:
            >>> async def handle_success(x: int) -> Either[str, int]:
            ...     return Left(f"Processed {x}") if x > 10 else Right(x)
            >>> async_either = AsyncEither.from_either(Right(15))
            >>> result = await async_either.or_else_left_async(handle_success)
        """
        ...

    @abstractmethod
    def bimap_async(
        self,
        left_fn: Callable[[L], Awaitable[V]],
        right_fn: Callable[[R], Awaitable[U]],
    ) -> AsyncEitherBase[V, U]:
        """Transform both Left and Right asynchronously (symmetric).

        Awaits left_fn on Left or right_fn on Right based on which variant is present.

        Parameters:
            left_fn: Async function L → Awaitable[V]
            right_fn: Async function R → Awaitable[U]

        Returns:
            AsyncEitherBase[V, U]: New AsyncEither with transformed branches

        Example:
            >>> async def process_error(e: str) -> str:
            ...     return f"Error: {e}"
            >>> async def process_value(x: int) -> str:
            ...     return f"Value: {x}"
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> result = await async_either.bimap_async(process_error, process_value)
            >>> # result.unwrap_right() == "Value: 42"
        """
        ...

    @abstractmethod
    async def fold_async(
        self,
        left_fn: Callable[[L], Awaitable[U]],
        right_fn: Callable[[R], Awaitable[U]],
    ) -> U:
        """Extract value by folding both branches asynchronously (catamorphism).

        Applies left_fn to Left or right_fn to Right based on variant, awaits result.

        Parameters:
            left_fn: Async function L → Awaitable[U]
            right_fn: Async function R → Awaitable[U]

        Returns:
            U: Result of applying appropriate branch function

        Example:
            >>> async def handle_error(e: str) -> str:
            ...     return f"Error: {e}"
            >>> async def handle_value(x: int) -> str:
            ...     return f"Value: {x}"
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> result = await async_either.fold_async(handle_error, handle_value)
            >>> # result == "Value: 42"
        """
        ...

    @abstractmethod
    def inspect_async(
        self, fn: Callable[[R], Awaitable[None]]
    ) -> AsyncEitherBase[L, R]:
        """Inspect Right value for side effects without modification (right-biased).

        If value is Right, awaits fn(value) for side effects then returns self.
        If value is Left, short-circuits.
        Context stack is preserved.

        Parameters:
            fn: Async side-effect function

        Returns:
            AsyncEitherBase[L, R]: Self unchanged

        Example:
            >>> async def log(x: int) -> None:
            ...     print(f"Value: {x}")
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> await async_either.inspect_async(log)
            # Prints: "Value: 42"
        """
        ...

    @abstractmethod
    def inspect_left_async(
        self, fn: Callable[[L], Awaitable[None]]
    ) -> AsyncEitherBase[L, R]:
        """Inspect Left value for side effects without modification (left-focused).

        If value is Left, awaits fn(value) for side effects then returns self.
        If value is Right, short-circuits.
        Context stack is preserved.

        Parameters:
            fn: Async side-effect function

        Returns:
            AsyncEitherBase[L, R]: Self unchanged

        Example:
            >>> async def log_error(e: str) -> None:
            ...     print(f"Error: {e}")
            >>> async_either = AsyncEither.from_either(Left("failed"))
            >>> await async_either.inspect_left_async(log_error)
            # Prints: "Error: failed"
        """
        ...

    @abstractmethod
    async def unwrap_right_async(self) -> R:
        """Extract Right value or raise UnwrapError with context.

        If value is Right, returns the wrapped value.
        If value is Left, raises UnwrapError containing context chain.

        Returns:
            R: The Right value

        Raises:
            UnwrapError: If Left, containing context chain

        Example:
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> value = await async_either.unwrap_right_async()  # 42

            >>> async_either = AsyncEither.from_either(Left("error"))
            >>> value = await async_either.unwrap_right_async()  # raises UnwrapError
        """
        ...

    @abstractmethod
    async def unwrap_left_async(self) -> L:
        """Extract Left value or raise UnwrapError with context.

        If value is Left, returns the wrapped value.
        If value is Right, raises UnwrapError containing context chain.

        Returns:
            L: The Left value

        Raises:
            UnwrapError: If Right, containing context chain

        Example:
            >>> async_either = AsyncEither.from_either(Left("error"))
            >>> value = await async_either.unwrap_left_async()  # "error"

            >>> async_either = AsyncEither.from_either(Right(42))
            >>> value = await async_either.unwrap_left_async()  # raises UnwrapError
        """
        ...

    @abstractmethod
    async def unwrap_right_or_async(self, default: R) -> R:
        """Extract Right value or return default.

        If value is Right, returns the wrapped value.
        If value is Left, returns the provided default.

        Parameters:
            default: Default value if Left

        Returns:
            R: Right value if Right, or default

        Example:
            >>> async_either = AsyncEither.from_either(Left("error"))
            >>> value = await async_either.unwrap_right_or_async(99)  # 99
        """
        ...

    @abstractmethod
    async def unwrap_left_or_async(self, default: L) -> L:
        """Extract Left value or return default.

        If value is Left, returns the wrapped value.
        If value is Right, returns the provided default.

        Parameters:
            default: Default value if Right

        Returns:
            L: Left value if Left, or default

        Example:
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> value = await async_either.unwrap_left_or_async("no error")  # "no error"
        """
        ...

    @abstractmethod
    async def unwrap_right_or_else_async(self, fn: Callable[[L], Awaitable[R]]) -> R:
        """Extract Right value or compute default.

        If value is Right, returns the wrapped value without calling fn.
        If value is Left, awaits fn(left_value) and returns result.

        Parameters:
            fn: Async function computing default value

        Returns:
            R: Right value if Right, or result of fn(left_value)

        Example:
            >>> async def compute_default(e: str) -> int:
            ...     return 99
            >>> async_either = AsyncEither.from_either(Left("error"))
            >>> value = await async_either.unwrap_right_or_else_async(compute_default)
            # value == 99
        """
        ...

    @abstractmethod
    async def unwrap_left_or_else_async(self, fn: Callable[[R], Awaitable[L]]) -> L:
        """Extract Left value or compute default.

        If value is Left, returns the wrapped value without calling fn.
        If value is Right, awaits fn(right_value) and returns result.

        Parameters:
            fn: Async function computing default value

        Returns:
            L: Left value if Left, or result of fn(right_value)

        Example:
            >>> async def compute_default(x: int) -> str:
            ...     return f"Computed: {x}"
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> value = await async_either.unwrap_left_or_else_async(compute_default)
            # value == "Computed: 42"
        """
        ...

    @abstractmethod
    def context(self, msg: str) -> AsyncEitherBase[L, R]:
        """Push context message to LIFO stack (immutable).

        Adds a message to the head of the context stack. The new message
        will be shown first when unwrap_*_async() raises on wrong variant.

        Parameters:
            msg: Context message to add

        Returns:
            AsyncEitherBase[L, R]: New AsyncEither with updated context

        Example:
            >>> async_either = AsyncEither.from_either(Right(5))
            >>> async_either = async_either.context("step1").context("step2")
            >>> # Context order (LIFO): "step2" → "step1"
        """
        ...

    @abstractmethod
    def with_context(self, f: Callable[[], str]) -> AsyncEitherBase[L, R]:
        """Push lazily-evaluated context (called immediately, not on await).

        Parameters:
            f: Callable that returns context message

        Returns:
            AsyncEitherBase[L, R]: New AsyncEither with evaluated context

        Example:
            >>> import time
            >>> async_either = AsyncEither.from_either(Right(5))
            >>> async_either = async_either.with_context(lambda: f"time: {time.time()}")
        """
        ...

    @staticmethod
    @abstractmethod
    def from_either(e: Either[L, R]) -> AsyncEitherBase[L, R]:
        """Create AsyncEither from synchronous Either.

        Wraps a sync Either in an immediately-resolved awaitable.

        Parameters:
            e: The Either[L, R] to wrap

        Returns:
            AsyncEitherBase[L, R]: Wrapped as awaitable

        Example:
            >>> from results import Right, AsyncEither
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> either = await async_either  # Right(42)
        """
        ...

    @staticmethod
    @abstractmethod
    def from_awaitable(aw: Awaitable[Either[L, R]]) -> AsyncEitherBase[L, R]:
        """Create AsyncEither from Awaitable[Either[L, R]].

        Directly wraps an async operation that returns an Either.

        Parameters:
            aw: The awaitable returning Either[L, R]

        Returns:
            AsyncEitherBase[L, R]: Wrapped as AsyncEither

        Example:
            >>> async def fetch_data(id: int) -> Either[str, Data]:
            ...     return Right(data) if data else Left("not found")
            >>> async_either = AsyncEither.from_awaitable(fetch_data(123))
            >>> either = await async_either
        """
        ...
