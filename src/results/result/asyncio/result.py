"""Single AsyncResult awaitable wrapper for Result[T, E].

This module implements AsyncResult as a unified awaitable container
that wraps Awaitable[Result[T, E]] and provides a complete async/await API:
- map_async, map_err_async, and_then_async
- inspect_async, inspect_err_async
- unwrap_async, resolve
- context management (LIFO)

Implementation uses an operation queue pattern to accumulate transformations
and evaluate them atomically on await/resolve, reducing branching complexity.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Generator
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from typing_extensions import override

from results.core.base import Result
from results.core.context import ContextChain, unwrap_with_context
from results.result.sync.err import Err
from results.result.sync.ok import Ok

__all__ = ["AsyncResult", "AsyncResultBase"]

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")
F = TypeVar("F")


class AsyncResultBase(ABC, Generic[T, E]):
    """Contract for AsyncResult awaitable workflows."""

    @abstractmethod
    def __await__(self) -> Generator[Any, None, Result[T, E]]: ...

    @abstractmethod
    async def unwrap_async(self) -> T: ...

    @abstractmethod
    async def resolve(self) -> Result[T, E]: ...

    @abstractmethod
    def context(self, msg: str) -> AsyncResult[T, E]: ...

    @abstractmethod
    def with_context(self, f: Callable[[], str]) -> AsyncResult[T, E]: ...

    @abstractmethod
    def map_async(self, fn: Callable[[T], Awaitable[U]]) -> AsyncResult[U, E]: ...

    @abstractmethod
    def map_err_async(self, fn: Callable[[E], Awaitable[F]]) -> AsyncResult[T, F]: ...

    @abstractmethod
    def and_then_async(
        self, fn: Callable[[T], Awaitable[Result[U, F]]]
    ) -> AsyncResult[U, E | F]: ...

    @abstractmethod
    async def inspect_async(
        self, fn: Callable[[T], Awaitable[None]]
    ) -> AsyncResult[T, E]: ...

    @abstractmethod
    async def inspect_err_async(
        self, fn: Callable[[E], Awaitable[None]]
    ) -> AsyncResult[T, E]: ...


@dataclass(frozen=True)
class AsyncResult(AsyncResultBase[T, E]):
    """Awaitable wrapper for Result[T, E] enabling async/await workflows.

    AsyncResult wraps an Awaitable[Result[T, E]] and provides async methods
    (map_async, and_then_async, etc.) that accumulate into an operation queue.
    The queue is evaluated atomically when the AsyncResult is awaited or
    resolve() is called, reducing branching complexity.

    Invariants:
    - Frozen dataclass (immutable)
    - Context stack (LIFO tuple) grows via context()/with_context()
    - Await and resolve() return identical Result[T, E]

    Attributes:
        _resolver: Callable that returns Awaitable[Result[T, E]]
        _context_chain: Tuple of context messages (head = most recent, LIFO)

    Type Parameters:
        T: Success value type
        E: Error type

    Examples:
        Create from sync Result:
            >>> from results import Ok, AsyncResult
            >>> async_result = AsyncResult.from_result(Ok(42))
            >>> result = await async_result  # Result[int, None]

        Create from async operation:
            >>> async def fetch() -> Result[str, str]:
            ...     return Ok("data")
            >>> async_result = AsyncResult.from_awaitable(fetch())
            >>> value = await async_result.unwrap_async()  # "data"

        Chain async operations with context:
            >>> async_result = AsyncResult.from_result(Ok(5))
            >>> result = await (
            ...     async_result
            ...     .context("fetching")
            ...     .map_async(async_double)
            ...     .context("processing")
            ... )
    """

    _resolver: Callable[[], Awaitable[Result[T, E]]]
    _context_chain: ContextChain = ContextChain()

    def __await__(self) -> Generator[Any, None, Result[T, E]]:
        """Enable await AsyncResult to return Result[T, E].

        Delegates to the wrapped awaitable, returning the raw Result.

        Yields:
            Any: Delegated from internal awaitable

        Returns:
            Result[T, E]: The final Result after evaluating operation queue
        """
        return self._resolver().__await__()

    @override
    async def unwrap_async(self) -> T:
        """Extract success value or raise UnwrapError with context.

        Awaits the result and unwraps it. If Err, raises UnwrapError
        containing the error and complete LIFO context chain.

        Returns:
            T: The success value if Ok

        Raises:
            UnwrapError: If Err, containing the error and LIFO context

        Example:
            >>> async_result = AsyncResult.from_result(Ok(42))
            >>> value = await async_result.unwrap_async()  # 42

            >>> async_result = AsyncResult.from_result(Err("failed"))
            >>> value = await async_result.unwrap_async()  # raises UnwrapError
        """
        result = await self
        if result.is_err():
            unwrap_with_context(result.err(), self._context_chain)

        return result.ok()  # type: ignore

    @override
    async def resolve(self) -> Result[T, E]:
        """Explicitly resolve to Result[T, E].

        Equivalent to await, provided for explicitness in type-complex scenarios.

        Returns:
            Result[T, E]: The resolved Result

        Example:
            >>> async_result = AsyncResult.from_result(Ok(42))
            >>> result = await async_result.resolve()  # Result[int, None]
        """
        return await self

    @override
    def context(self, msg: str) -> AsyncResult[T, E]:
        """Push context message to LIFO stack (immutable).

        Adds a message to the head of the context stack. The new message
        will be shown first when unwrap_async() raises.

        Parameters:
            msg: Context message to add

        Returns:
            AsyncResult[T, E]: New AsyncResult with updated context

        Example:
            >>> async_result = AsyncResult.from_result(Ok(5))
            >>> async_result = async_result.context("step 1").context("step 2")
            >>> # Context order (LIFO): "step 2" → "step 1"
        """
        return AsyncResult(self._resolver, self._context_chain.push(msg))

    @override
    def with_context(self, f: Callable[[], str]) -> AsyncResult[T, E]:
        """Push lazily-evaluated context (called immediately, not on await).

        Parameters:
            f: Callable that returns context message

        Returns:
            AsyncResult[T, E]: New AsyncResult with evaluated context

        Example:
            >>> async_result = AsyncResult.from_result(Ok(5))
            >>> async_result = async_result.with_context(lambda: f"time: {now()}")
        """
        return AsyncResult(self._resolver, self._context_chain.push_lazy(f))

    @override
    def map_async(self, fn: Callable[[T], Awaitable[U]]) -> AsyncResult[U, E]:
        """Transform success value asynchronously, preserving error.

        If Ok, awaits fn(value) and returns new Ok; if Err, short-circuits.
        Context stack is preserved across the transformation.

        Parameters:
            fn: Async function T → Awaitable[U]

        Returns:
            AsyncResult[U, E]: New AsyncResult with transformed value or same Err

        Example:
            >>> async_result = AsyncResult.from_result(Ok(5))
            >>> result = await async_result.map_async(async_double)
            >>> # result.ok() == 10
        """

        async def transformed() -> Result[U, E]:
            current = await self
            if current.is_ok():
                value = current.ok()
                transformed_value = await fn(value)  # type: ignore
                return Ok(transformed_value)
            return current.map_err(lambda e: e)  # type: ignore

        return AsyncResult(lambda: transformed(), self._context_chain)

    @override
    def map_err_async(self, fn: Callable[[E], Awaitable[F]]) -> AsyncResult[T, F]:
        """Transform error asynchronously, preserving success.

        If Err, awaits fn(error) and returns new Err; if Ok, short-circuits.
        Context stack is preserved across the transformation.

        Parameters:
            fn: Async function E → Awaitable[F]

        Returns:
            AsyncResult[T, F]: New AsyncResult with transformed error or same Ok

        Example:
            >>> async_result = AsyncResult.from_result(Err(ValueError("bad")))
            >>> result = await async_result.map_err_async(async_serialize)
        """

        async def transformed() -> Result[T, F]:
            current = await self
            if current.is_err():
                error = current.err()
                transformed_error = await fn(error)  # type: ignore
                return Err(transformed_error)
            return current.map(lambda t: t)  # type: ignore

        return AsyncResult(lambda: transformed(), self._context_chain)

    @override
    def and_then_async(
        self, fn: Callable[[T], Awaitable[Result[U, F]]]
    ) -> AsyncResult[U, E | F]:
        """Chain async operations that return Results, accumulating error types.

        If Ok, awaits fn(value) and returns the result; if Err, short-circuits
        with type-accumulated error (E | F).

        Parameters:
            fn: Function T → Awaitable[Result[U, F]]

        Returns:
            AsyncResult[U, E | F]: Chained result with accumulated error type

        Example:
            >>> async_result = AsyncResult.from_result(Ok(5))
            >>> result = await async_result.and_then_async(validate_async)
            >>> # Error type is now: original_error | validate_error
        """

        async def transformed() -> Result[U, E | F]:
            current = await self
            if current.is_ok():
                value = current.ok()
                return await fn(value)  # type: ignore
            # Err: short-circuit, error type expands to E | F
            return current.map_err(lambda e: e)  # type: ignore

        return AsyncResult(lambda: transformed(), self._context_chain)

    @override
    async def inspect_async(
        self, fn: Callable[[T], Awaitable[None]]
    ) -> AsyncResult[T, E]:
        """Inspect success value for side effects without modification.

        If Ok, awaits fn(value) for side effects; if Err, short-circuits.
        Returns self (or equivalent) unchanged.

        Parameters:
            fn: Async side-effect function

        Returns:
            AsyncResult[T, E]: Self unchanged

        Example:
            >>> async_result = AsyncResult.from_result(Ok(5))
            >>> result = await async_result.inspect_async(async_log)
        """
        current = await self
        if current.is_ok():
            await fn(current.ok())  # type: ignore
        return self

    @override
    async def inspect_err_async(
        self, fn: Callable[[E], Awaitable[None]]
    ) -> AsyncResult[T, E]:
        """Inspect error value for side effects without modification.

        If Err, awaits fn(error) for side effects; if Ok, short-circuits.
        Returns self (or equivalent) unchanged.

        Parameters:
            fn: Async side-effect function

        Returns:
            AsyncResult[T, E]: Self unchanged

        Example:
            >>> async_result = AsyncResult.from_result(Err("failed"))
            >>> result = await async_result.inspect_err_async(async_log)
        """
        current = await self
        if current.is_err():
            await fn(current.err())  # type: ignore
        return self

    @staticmethod
    def from_result(result: Result[T, E]) -> AsyncResult[T, E]:
        """Create AsyncResult from synchronous Result.

        Wraps a sync Result in an immediately-resolved awaitable.

        Parameters:
            result: The Result[T, E] to wrap

        Returns:
            AsyncResult[T, E]: Wrapped as awaitable

        Example:
            >>> from results import Ok, AsyncResult
            >>> async_result = AsyncResult.from_result(Ok(42))
            >>> result = await async_result  # Ok(42)
        """

        async def resolved() -> Result[T, E]:
            return result

        return AsyncResult(lambda: resolved())

    @staticmethod
    def from_awaitable(aw: Awaitable[Result[T, E]]) -> AsyncResult[T, E]:
        """Create AsyncResult from Awaitable[Result[T, E]].

        Directly wraps an async operation that returns a Result.

        Parameters:
            aw: The awaitable returning Result[T, E]

        Returns:
            AsyncResult[T, E]: Wrapped asyncresult

        Example:
            >>> async def fetch() -> Result[str, str]:
            ...     return Ok("data")
            >>> async_result = AsyncResult.from_awaitable(fetch())
            >>> result = await async_result  # Ok("data")
        """
        return AsyncResult(AsyncResult._wrap_awaitable(aw))

    @staticmethod
    def _wrap_awaitable(
        aw: Awaitable[Result[T, E]],
    ) -> Callable[[], Awaitable[Result[T, E]]]:
        """Wrap awaitable to support multiple awaits by caching in-flight task."""

        task: asyncio.Future[Result[T, E]] | None = None

        async def resolver() -> Result[T, E]:
            nonlocal task
            if task is None:
                loop = asyncio.get_running_loop()
                if isinstance(aw, asyncio.Future):
                    task = aw
                else:
                    task = loop.create_task(aw)  # type: ignore
            return await task

        return resolver

    def __repr__(self) -> str:
        """Return debug representation."""
        return (
            f"AsyncResult("
            f"_resolver={self._resolver!r}, "
            f"_context_chain={self._context_chain!r})"
        )

    def __str__(self) -> str:
        """Return human-readable string."""
        if not self._context_chain.is_empty():
            context = "\n  ".join(self._context_chain.messages)
            return f"AsyncResult(context: {context})"
        return "AsyncResult()"
