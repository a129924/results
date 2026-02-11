"""AsyncMaybe abstract base class - async/await support for Maybe.

This module defines the AsyncMaybe abstract base class that async implementations
of Maybe must adhere to. AsyncMaybe wraps an Awaitable[Maybe[T]] and provides
async transformation methods (map_async, and_then_async, etc.) that accumulate
into an operation queue evaluated atomically when awaited.

The AsyncMaybe type maintains the same semantics as Maybe (presence/absence,
not success/failure) with async support for long-running operations.

Key difference from Maybe:
- Cannot inspect concrete Some/Nothing until awaited
- Provides async variants of transformation methods
- Context chain preserved and evaluated on await
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Iterator
from typing import TYPE_CHECKING, Generic

from .types import T, U

if TYPE_CHECKING:
    from .maybe_base import Maybe


class AsyncMaybeBase(ABC, Generic[T]):
    """Abstract base class for AsyncMaybe - awaitable wrapper for Maybe[T].

    AsyncMaybe[T] wraps an Awaitable[Maybe[T]] and provides async methods
    (map_async, and_then_async, etc.) that accumulate into an operation queue.
    The queue is evaluated atomically when the AsyncMaybe is awaited, reducing
    branching complexity.

    Invariants:
    - Frozen dataclass (immutable)
    - Context stack (LIFO tuple) grows via context()/with_context()
    - Await returns concrete Maybe[T] (Some or Nothing)

    Type Parameters:
        T: Value type when present

    Example:
        Create from sync Maybe:
            >>> from results import Some, AsyncMaybe
            >>> async_maybe = AsyncMaybe.from_maybe(Some(42))
            >>> maybe = await async_maybe  # Maybe[int]

        Create from async operation:
            >>> async def fetch_user(id: int) -> Maybe[User]:
            ...     user = await api.get(id)
            ...     return Some(user) if user else Nothing()
            >>> async_maybe = AsyncMaybe.from_awaitable(fetch_user(123))
            >>> name = await async_maybe.map_async(lambda u: u.name).unwrap_or_async("Unknown")

        Chain async operations with context:
            >>> async_maybe = AsyncMaybe.from_maybe(Some(5))
            >>> result = await (
            ...     async_maybe
            ...     .context("fetching")
            ...     .map_async(async_double)
            ...     .context("processing")
            ... )
    """

    @abstractmethod
    def __await__(self) -> Iterator[Maybe[T]]:
        """Enable await AsyncMaybe to return Maybe[T].

        When awaited, resolves the async operation and returns the concrete
        Maybe[T] (Some or Nothing).

        Returns:
            Maybe[T]: The resolved Maybe after evaluating operation queue

        Example:
            >>> async_maybe = AsyncMaybe.from_maybe(Some(42))
            >>> maybe = await async_maybe  # Some(42)
        """
        ...

    @abstractmethod
    def map_async(self, fn: Callable[[T], Awaitable[U]]) -> AsyncMaybeBase[U]:
        """Transform value asynchronously if present, short-circuit if absent.

        If value is Some, awaits fn(value) and returns AsyncMaybe with result.
        If value is Nothing, short-circuits and returns AsyncMaybe[Nothing].
        Context stack is preserved across the transformation.

        Parameters:
            fn: Async function T → Awaitable[U]

        Returns:
            AsyncMaybe[U]: New AsyncMaybe with transformed value or Nothing

        Example:
            >>> async_maybe = AsyncMaybe.from_maybe(Some(5))
            >>> async def double(x: int) -> int:
            ...     await asyncio.sleep(0)
            ...     return x * 2
            >>> result = await async_maybe.map_async(double)
            >>> # result.unwrap() == 10
        """
        ...

    @abstractmethod
    def and_then_async(
        self, fn: Callable[[T], Awaitable[Maybe[U]]]
    ) -> AsyncMaybeBase[U]:
        """Chain async operations returning Maybe, flattening the result.

        If value is Some, awaits fn(value) and returns the result as AsyncMaybe.
        If value is Nothing, short-circuits and returns AsyncMaybe[Nothing].

        Parameters:
            fn: Function T → Awaitable[Maybe[U]]

        Returns:
            AsyncMaybe[U]: Chained result, flattened

        Example:
            >>> async def validate_positive(x: int) -> Maybe[int]:
            ...     return Some(x) if x > 0 else Nothing()
            >>> async_maybe = AsyncMaybe.from_maybe(Some(5))
            >>> result = await async_maybe.and_then_async(
            ...     lambda x: asyncio.sleep(0) or validate_positive(x)
            ... )
        """
        ...

    @abstractmethod
    def or_else_async(self, fn: Callable[[], Awaitable[Maybe[T]]]) -> AsyncMaybeBase[T]:
        """Provide alternative async operation if absent.

        If value is Some, returns self unchanged.
        If value is Nothing, awaits fn() and returns result as AsyncMaybe.

        Parameters:
            fn: Async function returning Maybe[T]

        Returns:
            AsyncMaybeBase[T]: Self if Some, or result of fn() if Nothing

        Example:
            >>> async def fetch_default() -> Maybe[int]:
            ...     return Some(99)
            >>> async_maybe = AsyncMaybe.from_maybe(Nothing())
            >>> result = await async_maybe.or_else_async(fetch_default)
            >>> # result.unwrap() == 99
        """
        ...

    @abstractmethod
    def inspect_async(self, fn: Callable[[T], Awaitable[None]]) -> AsyncMaybeBase[T]:
        """Inspect value for side effects without modification.

        If value is Some, awaits fn(value) for side effects then returns self.
        If value is Nothing, short-circuits.
        Context stack is preserved.

        Parameters:
            fn: Async side-effect function

        Returns:
            AsyncMaybeBase[T]: Self unchanged

        Example:
            >>> async def log(x: int) -> None:
            ...     print(f"Value: {x}")
            >>> async_maybe = AsyncMaybe.from_maybe(Some(42))
            >>> await async_maybe.inspect_async(log)
            # Prints: "Value: 42"
        """
        ...

    @abstractmethod
    async def unwrap_async(self) -> T:
        """Extract value or raise UnwrapError with context.

        If value is Some, returns the wrapped value.
        If value is Nothing, raises UnwrapError containing context chain.

        Returns:
            T: The value if Some

        Raises:
            UnwrapError: If Nothing, containing context chain

        Example:
            >>> async_maybe = AsyncMaybe.from_maybe(Some(42))
            >>> value = await async_maybe.unwrap_async()  # 42

            >>> async_maybe = AsyncMaybe.from_maybe(Nothing())
            >>> value = await async_maybe.unwrap_async()  # raises UnwrapError
        """
        ...

    @abstractmethod
    async def unwrap_or_async(self, default: T) -> T:
        """Extract value or return default.

        If value is Some, returns the wrapped value.
        If value is Nothing, returns the provided default.

        Parameters:
            default: Default value if Nothing

        Returns:
            T: Value if Some, or default

        Example:
            >>> async_maybe = AsyncMaybe.from_maybe(Nothing())
            >>> value = await async_maybe.unwrap_or_async(99)  # 99
        """
        ...

    @abstractmethod
    async def unwrap_or_else_async(self, fn: Callable[[], Awaitable[T]]) -> T:
        """Extract value or compute default asynchronously.

        If value is Some, returns the wrapped value without calling fn.
        If value is Nothing, awaits fn() and returns result.

        Parameters:
            fn: Async function computing default value

        Returns:
            T: Value if Some, or result of fn()

        Example:
            >>> async def compute_default() -> int:
            ...     return 99
            >>> async_maybe = AsyncMaybe.from_maybe(Nothing())
            >>> value = await async_maybe.unwrap_or_else_async(compute_default)
            # value == 99
        """
        ...

    @abstractmethod
    def context(self, msg: str) -> AsyncMaybeBase[T]:
        """Push context message to LIFO stack (immutable).

        Adds a message to the head of the context stack. The new message
        will be shown first when unwrap_async() raises on Nothing.

        Parameters:
            msg: Context message to add

        Returns:
            AsyncMaybeBase[T]: New AsyncMaybe with updated context

        Example:
            >>> async_maybe = AsyncMaybe.from_maybe(Some(5))
            >>> async_maybe = async_maybe.context("step1").context("step2")
            >>> # Context order (LIFO): "step2" → "step1"
        """
        ...

    @abstractmethod
    def with_context(self, f: Callable[[], str]) -> AsyncMaybeBase[T]:
        """Push lazily-evaluated context (called immediately, not on await).

        Parameters:
            f: Callable that returns context message

        Returns:
            AsyncMaybeBase[T]: New AsyncMaybe with evaluated context

        Example:
            >>> import time
            >>> async_maybe = AsyncMaybe.from_maybe(Some(5))
            >>> async_maybe = async_maybe.with_context(lambda: f"time: {time.time()}")
        """
        ...

    @staticmethod
    @abstractmethod
    def from_maybe(m: Maybe[T]) -> AsyncMaybeBase[T]:
        """Create AsyncMaybe from synchronous Maybe.

        Wraps a sync Maybe in an immediately-resolved awaitable.

        Parameters:
            m: The Maybe[T] to wrap

        Returns:
            AsyncMaybeBase[T]: Wrapped as awaitable

        Example:
            >>> from results import Some, AsyncMaybe
            >>> async_maybe = AsyncMaybe.from_maybe(Some(42))
            >>> maybe = await async_maybe  # Some(42)
        """
        ...

    @staticmethod
    @abstractmethod
    def from_awaitable(aw: Awaitable[Maybe[T]]) -> AsyncMaybeBase[T]:
        """Create AsyncMaybe from Awaitable[Maybe[T]].

        Directly wraps an async operation that returns a Maybe.

        Parameters:
            aw: The awaitable returning Maybe[T]

        Returns:
            AsyncMaybeBase[T]: Wrapped as AsyncMaybe

        Example:
            >>> async def fetch_user(id: int) -> Maybe[User]:
            ...     return Some(user) if user else Nothing()
            >>> async_maybe = AsyncMaybe.from_awaitable(fetch_user(123))
            >>> maybe = await async_maybe
        """
        ...
