"""AsyncMaybe implementation - async/await wrapper for Maybe[T].

This module implements AsyncMaybe[T], providing async transformation methods
for Maybe type. AsyncMaybe wraps Awaitable[Maybe[T]] and resolves to a
concrete Maybe[T] (Some or Nothing) when awaited.

Key design: Unlike separate AsyncSome/AsyncNothing types, AsyncMaybe is
a single unified type that wraps the awaitable. This matches the AsyncResult
pattern and correctly expresses "an async computation that resolves to Maybe".
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Generator
from dataclasses import dataclass
from typing import Any, cast

from typing_extensions import override

from ...core.async_maybe_base import AsyncMaybeBase
from ...core.context import ContextChain
from ...core.maybe_base import Maybe
from ...core.types import T, U
from ...exceptions import UnwrapError
from ...maybe.sync.nothing import Nothing
from ...maybe.sync.some import Some


@dataclass(frozen=True)
class AsyncMaybe(AsyncMaybeBase[T]):
    """Awaitable wrapper for Maybe[T] enabling async/await workflows.

    AsyncMaybe[T] wraps an Awaitable[Maybe[T]] and provides async methods
    (map_async, and_then_async, etc.) that accumulate into an operation queue.
    The queue is evaluated atomically when the AsyncMaybe is awaited or
    resolve() is called, reducing branching complexity.

    Invariants:
    - Frozen dataclass (immutable)
    - Context stack (LIFO tuple) grows via context()/with_context()
    - Await and resolve() return identical Maybe[T]

    Attributes:
        _resolver: Callable that returns Awaitable[Maybe[T]]
        _context_chain: Tuple of context messages (head = most recent, LIFO)

    Type Parameters:
        T: Value type when present

    Examples:
        Create from sync Maybe:
            >>> from results import Some, AsyncMaybe
            >>> async_maybe = AsyncMaybe.from_maybe(Some(42))
            >>> maybe = await async_maybe  # Maybe[int]

        Create from async operation:
            >>> async def fetch_user(id: int) -> Maybe[User]:
            ...     user = await api.get(id)
            ...     return Some(user) if user else Nothing()
            >>> async_maybe = AsyncMaybe.from_awaitable(fetch_user(123))
            >>> name = await async_maybe.map_async(
            ...     lambda u: asyncio.sleep(0) or u.name
            ... ).unwrap_or_async("Unknown")

        Chain async operations with context:
            >>> async_maybe = AsyncMaybe.from_maybe(Some(5))
            >>> result = await (
            ...     async_maybe
            ...     .context("fetching")
            ...     .map_async(async_double)
            ...     .context("processing")
            ... )
    """

    _resolver: Callable[[], Awaitable[Maybe[T]]]
    _context_chain: ContextChain = ContextChain()

    def __await__(self) -> Generator[Any, None, Maybe[T]]:
        """Enable await AsyncMaybe to return Maybe[T].

        Delegates to the wrapped awaitable, returning the raw Maybe.

        Yields:
            Any: Delegated from internal awaitable

        Returns:
            Maybe[T]: The final Maybe after evaluating operation queue
        """
        return self._resolver().__await__()

    @override
    def map_async(self, fn: Callable[[T], Awaitable[U]]) -> AsyncMaybe[U]:
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

        async def transformed() -> Maybe[U]:
            current = await self
            # Match on concrete Some/Nothing
            match current:
                case Some(value):
                    transformed_value = await fn(value)
                    return cast(Maybe[U], Some(transformed_value))
                case Nothing():
                    # Short-circuit: return same Nothing as Maybe[U]
                    return cast(Maybe[U], current)
                case unexpected:
                    # Should never happen if invariants hold
                    raise TypeError(f"Unexpected Maybe variant: {unexpected!r}")

        return AsyncMaybe(lambda: transformed(), self._context_chain)

    @override
    def and_then_async(self, fn: Callable[[T], Awaitable[Maybe[U]]]) -> AsyncMaybe[U]:
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
            >>> result = await async_maybe.and_then_async(validate_positive)
        """

        async def transformed() -> Maybe[U]:
            current = await self
            match current:
                case Some(value):
                    # Await the Maybe-returning function
                    return await fn(value)
                case Nothing():
                    # Short-circuit: return same Nothing as Maybe[U]
                    return cast(Maybe[U], current)
                case unexpected:
                    # Should never happen if invariants hold
                    raise TypeError(f"Unexpected Maybe variant: {unexpected!r}")

        return AsyncMaybe(lambda: transformed(), self._context_chain)

    @override
    def or_else_async(self, fn: Callable[[], Awaitable[Maybe[T]]]) -> AsyncMaybe[T]:
        """Provide alternative async operation if absent.

        If value is Some, returns self unchanged.
        If value is Nothing, awaits fn() and returns result as AsyncMaybe.

        Parameters:
            fn: Async function returning Maybe[T]

        Returns:
            AsyncMaybe[T]: Self if Some, or result of fn() if Nothing

        Example:
            >>> async def fetch_default() -> Maybe[int]:
            ...     return Some(99)
            >>> async_maybe = AsyncMaybe.from_maybe(Nothing())
            >>> result = await async_maybe.or_else_async(fetch_default)
            >>> # result.unwrap() == 99
        """

        async def transformed() -> Maybe[T]:
            current = await self
            match current:
                case Some():
                    # Already have value, return as-is
                    return current
                case Nothing():
                    # Absent, try the fallback
                    return await fn()
                case _:
                    # Should never happen if invariants hold
                    raise

        return AsyncMaybe(lambda: transformed(), self._context_chain)

    @override
    def inspect_async(self, fn: Callable[[T], Awaitable[None]]) -> AsyncMaybe[T]:
        """Inspect value for side effects without modification.

        If value is Some, awaits fn(value) for side effects then returns self.
        If value is Nothing, short-circuits.
        Context stack is preserved.

        Parameters:
            fn: Async side-effect function

        Returns:
            AsyncMaybe[T]: Self unchanged

        Example:
            >>> async def log(x: int) -> None:
            ...     print(f"Value: {x}")
            >>> async_maybe = AsyncMaybe.from_maybe(Some(42))
            >>> await async_maybe.inspect_async(log)
            # Prints: "Value: 42"
        """

        async def transformed() -> Maybe[T]:
            current = await self
            match current:
                case Some(value):
                    # Inspect the value
                    await fn(value)
                    # Return unchanged
                    return cast(Maybe[T], current)
                case Nothing():
                    # Short-circuit
                    return cast(Maybe[T], current)
                case unexpected:
                    # Should never happen if invariants hold
                    raise TypeError(f"Unexpected Maybe variant: {unexpected!r}")

        return AsyncMaybe(lambda: transformed(), self._context_chain)

    @override
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
        maybe = await self
        if isinstance(maybe, Some):
            some: Some[T] = maybe
            return some.value
        if isinstance(maybe, Nothing):
            msg = "Called unwrap() on Nothing"
            context_str = " → ".join(self._context_chain.messages)
            if context_str:
                msg = f"{msg}\nContext:\n  {context_str}"
            raise UnwrapError(msg, self._context_chain) from None
        raise TypeError(f"Unexpected Maybe variant: {maybe!r}")

    @override
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
        maybe = await self
        if isinstance(maybe, Some):
            some: Some[T] = maybe
            return some.value
        if isinstance(maybe, Nothing):
            return default
        raise TypeError(f"Unexpected Maybe variant: {maybe!r}")

    @override
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
        maybe = await self
        if isinstance(maybe, Some):
            some: Some[T] = maybe
            return some.value
        if isinstance(maybe, Nothing):
            return await fn()
        raise TypeError(f"Unexpected Maybe variant: {maybe!r}")

    @override
    def context(self, msg: str) -> AsyncMaybe[T]:
        """Push context message to LIFO stack (immutable).

        Adds a message to the head of the context stack. The new message
        will be shown first when unwrap_async() raises on Nothing.

        Parameters:
            msg: Context message to add

        Returns:
            AsyncMaybe[T]: New AsyncMaybe with updated context

        Example:
            >>> async_maybe = AsyncMaybe.from_maybe(Some(5))
            >>> async_maybe = async_maybe.context("step1").context("step2")
            >>> # Context order (LIFO): "step2" → "step1"
        """
        return AsyncMaybe(self._resolver, self._context_chain.push(msg))

    @override
    def with_context(self, f: Callable[[], str]) -> AsyncMaybe[T]:
        """Push lazily-evaluated context (called immediately, not on await).

        Parameters:
            f: Callable that returns context message

        Returns:
            AsyncMaybe[T]: New AsyncMaybe with evaluated context

        Example:
            >>> import time
            >>> async_maybe = AsyncMaybe.from_maybe(Some(5))
            >>> async_maybe = async_maybe.with_context(lambda: f"time: {time.time()}")
        """
        return AsyncMaybe(self._resolver, self._context_chain.push_lazy(f))

    @staticmethod
    @override
    def from_maybe(m: Maybe[T]) -> AsyncMaybe[T]:
        """Create AsyncMaybe from synchronous Maybe.

        Wraps a sync Maybe in an immediately-resolved awaitable.

        Parameters:
            m: The Maybe[T] to wrap

        Returns:
            AsyncMaybe[T]: Wrapped as awaitable

        Example:
            >>> from results import Some, AsyncMaybe
            >>> async_maybe = AsyncMaybe.from_maybe(Some(42))
            >>> maybe = await async_maybe  # Some(42)
        """

        async def resolved() -> Maybe[T]:
            return m

        return AsyncMaybe(lambda: resolved())

    @staticmethod
    @override
    def from_awaitable(aw: Awaitable[Maybe[T]]) -> AsyncMaybe[T]:
        """Create AsyncMaybe from Awaitable[Maybe[T]].

        Directly wraps an async operation that returns a Maybe.

        Parameters:
            aw: The awaitable returning Maybe[T]

        Returns:
            AsyncMaybe[T]: Wrapped as AsyncMaybe

        Example:
            >>> async def fetch_user(id: int) -> Maybe[User]:
            ...     return Some(user) if user else Nothing()
            >>> async_maybe = AsyncMaybe.from_awaitable(fetch_user(123))
            >>> maybe = await async_maybe
        """
        return AsyncMaybe(AsyncMaybe[T]._wrap_awaitable(aw))

    @staticmethod
    def _wrap_awaitable(
        aw: Awaitable[Maybe[T]],
    ) -> Callable[[], Awaitable[Maybe[T]]]:
        """Wrap awaitable to support multiple awaits by caching in-flight task."""

        task: asyncio.Future[Maybe[T]] | None = None

        async def resolver() -> Maybe[T]:
            nonlocal task
            if task is None:
                loop = asyncio.get_running_loop()
                if isinstance(aw, asyncio.Future):
                    task = aw
                else:
                    task = cast(asyncio.Task[Maybe[T]], loop.create_task(aw))  # type: ignore
            return await task

        return resolver

    def __repr__(self) -> str:
        """Return debug representation."""
        return (
            f"AsyncMaybe("
            f"_resolver={self._resolver!r}, "
            f"_context_chain={self._context_chain!r})"
        )

    def __str__(self) -> str:
        """Return human-readable string."""
        if not self._context_chain.is_empty():
            context = "\n  ".join(self._context_chain.messages)
            return f"AsyncMaybe(context: {context})"
        return "AsyncMaybe()"
