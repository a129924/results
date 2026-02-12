"""Single AsyncEither awaitable wrapper for Either[L, R].

This module implements AsyncEither as a unified awaitable container
that wraps Awaitable[Either[L, R]] and provides a complete async/await API:
- map_async, map_left_async, and_then_async, and_then_left_async
- inspect_async, inspect_left_async, bimap_async, fold_async
- unwrap_*_async methods
- context management (LIFO)

Implementation uses an operation queue pattern to accumulate transformations
and evaluate them atomically on await, reducing branching complexity.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from typing_extensions import override

from results.core.async_either_base import AsyncEitherBase
from results.core.context import ContextChain, unwrap_with_context
from results.either.sync.left import Left
from results.either.sync.right import Right

if TYPE_CHECKING:
    from results.core.either_base import Either

__all__ = ["AsyncEither"]

L = TypeVar("L")
R = TypeVar("R")
U = TypeVar("U")
V = TypeVar("V")


@dataclass(frozen=True)
class AsyncEither(AsyncEitherBase[L, R]):
    """Awaitable wrapper for Either[L, R] enabling async/await workflows.

    AsyncEither wraps an Awaitable[Either[L, R]] and provides async methods
    (map_async, and_then_async, etc.) that accumulate into an operation queue.
    The queue is evaluated atomically when the AsyncEither is awaited,
    reducing branching complexity.

    Invariants:
    - Frozen dataclass (immutable)
    - Context stack (LIFO tuple) grows via context()/with_context()
    - Await returns identical Either[L, R]
    - Both Left and Right branches have symmetric context chaining

    Attributes:
        _resolver: Callable that returns Awaitable[Either[L, R]]
        _context_chain: Tuple of context messages (head = most recent, LIFO)

    Type Parameters:
        L: Left outcome type (symmetric, not necessarily error)
        R: Right outcome type (symmetric, not necessarily success)

    Examples:
        Create from sync Either:
            >>> from results import Right, AsyncEither
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> either = await async_either  # Either[*, int]

        Create from async operation:
            >>> async def fetch() -> Either[str, Data]:
            ...     try:
            ...         data = await api.get()
            ...         return Right(data)
            ...     except Exception as e:
            ...         return Left(str(e))
            >>> async_either = AsyncEither.from_awaitable(fetch())
            >>> value = await async_either.unwrap_right_async()

        Chain async operations with context:
            >>> async_either = AsyncEither.from_either(Right(5))
            >>> result = await (
            ...     async_either
            ...     .context("fetching")
            ...     .map_async(async_double)
            ...     .context("processing")
            ... )
    """

    _resolver: Callable[[], Awaitable[Either[L, R]]]
    _context_chain: ContextChain = field(default_factory=ContextChain)

    def __await__(self) -> Generator[Any, None, Either[L, R]]:
        """Enable await AsyncEither to return Either[L, R].

        Delegates to the wrapped awaitable, returning the raw Either.

        Yields:
            Any: Delegated from internal awaitable

        Returns:
            Either[L, R]: The final Either after evaluating operation queue
        """
        return self._resolver().__await__()

    @override
    def is_right_async(self) -> Awaitable[bool]:
        """Check if value is Right asynchronously.

        Awaits the Either and checks variant.

        Returns:
            Awaitable[bool]: True if Right, False if Left

        Example:
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> result = await async_either.is_right_async()  # True
        """

        async def check() -> bool:
            either = await self
            return either.is_right()

        return check()

    @override
    def is_left_async(self) -> Awaitable[bool]:
        """Check if value is Left asynchronously.

        Awaits the Either and checks variant.

        Returns:
            Awaitable[bool]: True if Left, False if Right

        Example:
            >>> async_either = AsyncEither.from_either(Left("error"))
            >>> result = await async_either.is_left_async()  # True
        """

        async def check() -> bool:
            either = await self
            return either.is_left()

        return check()

    @override
    def map_async(self, fn: Callable[[R], Awaitable[U]]) -> AsyncEither[L, U]:
        """Transform Right value asynchronously, short-circuit if Left (right-biased).

        If value is Right, awaits fn(value) and returns new Right.
        If value is Left, short-circuits and returns unchanged Left.
        Context stack is preserved across the transformation.

        Parameters:
            fn: Async function R → Awaitable[U]

        Returns:
            AsyncEither[L, U]: New AsyncEither with transformed Right or unchanged Left

        Example:
            >>> async_either = AsyncEither.from_either(Right(5))
            >>> async def double(x: int) -> int:
            ...     await asyncio.sleep(0)
            ...     return x * 2
            >>> result = await async_either.map_async(double)
            >>> # result.unwrap_right() == 10
        """

        async def transformed() -> Either[L, U]:
            current = await self
            if current.is_right():
                value = cast(R, current.right())
                transformed_value = await fn(value)
                return Right(transformed_value)
            # Left: preserve the left value (cast for type safety)
            return current  # type: ignore

        result: AsyncEither[L, U] = AsyncEither(
            lambda: transformed(), self._context_chain
        )
        return result

    @override
    def map_left_async(self, fn: Callable[[L], Awaitable[V]]) -> AsyncEither[V, R]:
        """Transform Left value asynchronously, short-circuit if Right (left-focused).

        If value is Left, awaits fn(value) and returns new Left.
        If value is Right, short-circuits and returns unchanged Right.
        Context stack is preserved across the transformation.

        Parameters:
            fn: Async function L → Awaitable[V]

        Returns:
            AsyncEither[V, R]: New AsyncEither with transformed Left or unchanged Right

        Example:
            >>> async_either = AsyncEither.from_either(Left("error"))
            >>> async def enhance_error(e: str) -> str:
            ...     await asyncio.sleep(0)
            ...     return f"Enhanced: {e}"
            >>> result = await async_either.map_left_async(enhance_error)
            >>> # result.unwrap_left() == "Enhanced: error"
        """

        async def transformed() -> Either[V, R]:
            current = await self
            if current.is_left():
                value = cast(L, current.left())
                transformed_value = await fn(value)
                return Left(transformed_value)
            # Right: preserve the right value (cast for type safety)
            return current  # type: ignore

        result: AsyncEither[V, R] = AsyncEither(
            lambda: transformed(), self._context_chain
        )
        return result

    @override
    def and_then_async(
        self, fn: Callable[[R], Awaitable[Either[L, U]]]
    ) -> AsyncEither[L, U]:
        """Chain async operations on Right returning Either, flattening (right-biased).

        If value is Right, awaits fn(value) and returns the result.
        If value is Left, short-circuits and returns unchanged Left.

        Parameters:
            fn: Function R → Awaitable[Either[L, U]]

        Returns:
            AsyncEither[L, U]: Chained result, flattened

        Example:
            >>> async def validate_positive(x: int) -> Either[str, int]:
            ...     return Right(x) if x > 0 else Left("not positive")
            >>> async_either = AsyncEither.from_either(Right(5))
            >>> result = await async_either.and_then_async(
            ...     lambda x: asyncio.sleep(0) or validate_positive(x)
            ... )
        """

        async def transformed() -> Either[L, U]:
            current = await self
            if current.is_right():
                value = cast(R, current.right())
                return await fn(value)
            # Left: short-circuit (cast for type safety)
            return current  # type: ignore

        result: AsyncEither[L, U] = AsyncEither(
            lambda: transformed(), self._context_chain
        )
        return result

    @override
    def and_then_left_async(
        self, fn: Callable[[L], Awaitable[Either[V, R]]]
    ) -> AsyncEither[V, R]:
        """Chain async operations on Left returning Either, flattening (left-focused).

        If value is Left, awaits fn(value) and returns the result.
        If value is Right, short-circuits and returns unchanged Right.

        Parameters:
            fn: Function L → Awaitable[Either[V, R]]

        Returns:
            AsyncEither[V, R]: Chained result, flattened

        Example:
            >>> async def recover_from_error(e: str) -> Either[str, int]:
            ...     return Right(99) if "recoverable" in e else Left(e)
            >>> async_either = AsyncEither.from_either(Left("recoverable error"))
            >>> result = await async_either.and_then_left_async(recover_from_error)
        """

        async def transformed() -> Either[V, R]:
            current = await self
            if current.is_left():
                value = cast(L, current.left())
                return await fn(value)
            # Right: short-circuit (cast for type safety)
            return current  # type: ignore

        result: AsyncEither[V, R] = AsyncEither(
            lambda: transformed(), self._context_chain
        )
        return result

    @override
    def or_else_async(
        self, fn: Callable[[L], Awaitable[Either[V, R]]]
    ) -> AsyncEither[V, R]:
        """Provide alternative async operation if Left, short-circuit if Right (right-biased).

        If value is Right, returns self unchanged.
        If value is Left, awaits fn(value) and returns result.

        Parameters:
            fn: Async function returning Either[V, R]

        Returns:
            AsyncEither[V, R]: Self if Right, or result of fn(left_value) if Left

        Example:
            >>> async def fetch_default() -> Either[str, int]:
            ...     return Right(99)
            >>> async_either = AsyncEither.from_either(Left("error"))
            >>> result = await async_either.or_else_async(fetch_default)
            >>> # result.unwrap_right() == 99
        """

        async def transformed() -> Either[V, R]:
            current = await self
            if current.is_right():
                return current  # type: ignore
            # Left: apply recovery function
            value = cast(L, current.left())
            return await fn(value)

        result: AsyncEither[V, R] = AsyncEither(
            lambda: transformed(), self._context_chain
        )
        return result

    @override
    def or_else_left_async(
        self, fn: Callable[[R], Awaitable[Either[L, U]]]
    ) -> AsyncEither[L, U]:
        """Provide alternative async operation if Right, short-circuit if Left (left-focused).

        If value is Left, returns self unchanged.
        If value is Right, awaits fn(value) and returns result.

        Parameters:
            fn: Async function returning Either[L, U]

        Returns:
            AsyncEither[L, U]: Self if Left, or result of fn(right_value) if Right

        Example:
            >>> async def handle_success(x: int) -> Either[str, int]:
            ...     return Left(f"Processed {x}") if x > 10 else Right(x)
            >>> async_either = AsyncEither.from_either(Right(15))
            >>> result = await async_either.or_else_left_async(handle_success)
        """

        async def transformed() -> Either[L, U]:
            current = await self
            if current.is_left():
                return current  # type: ignore
            # Right: apply alternative function
            value = cast(R, current.right())
            return await fn(value)

        result: AsyncEither[L, U] = AsyncEither(
            lambda: transformed(), self._context_chain
        )
        return result

    @override
    def bimap_async(
        self,
        left_fn: Callable[[L], Awaitable[V]],
        right_fn: Callable[[R], Awaitable[U]],
    ) -> AsyncEither[V, U]:
        """Transform both Left and Right asynchronously (symmetric).

        Awaits left_fn on Left or right_fn on Right based on which variant is present.

        Parameters:
            left_fn: Async function L → Awaitable[V]
            right_fn: Async function R → Awaitable[U]

        Returns:
            AsyncEither[V, U]: New AsyncEither with transformed branches

        Example:
            >>> async def process_error(e: str) -> str:
            ...     return f"Error: {e}"
            >>> async def process_value(x: int) -> str:
            ...     return f"Value: {x}"
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> result = await async_either.bimap_async(process_error, process_value)
            >>> # result.unwrap_right() == "Value: 42"
        """

        async def transformed() -> Either[V, U]:
            current = await self
            if current.is_left():
                left_value = cast(L, current.left())
                left_transformed = await left_fn(left_value)
                return Left(left_transformed)
            # Right variant (value is R, transformed_value is U)
            right_value = cast(R, current.right())
            right_transformed = await right_fn(right_value)
            return Right(right_transformed)

        result: AsyncEither[V, U] = AsyncEither(
            lambda: transformed(), self._context_chain
        )
        return result

    @override
    async def fold_async(
        self,
        left_fn: Callable[[L], Awaitable[U]],
        right_fn: Callable[[R], Awaitable[U]],
    ) -> U:
        """Extract value by folding both branches asynchronously (catamorphism).

        Applies left_fn to Left or right_fn to Right based on variant.

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
        current = await self
        if current.is_left():
            return await left_fn(current.left())  # type: ignore
        else:
            return await right_fn(current.right())  # type: ignore

    @override
    def inspect_async(self, fn: Callable[[R], Awaitable[None]]) -> AsyncEither[L, R]:
        """Inspect Right value for side effects without modification (right-biased).

        If value is Right, awaits fn(value) for side effects then returns self.
        If value is Left, short-circuits.
        Context stack is preserved.

        Parameters:
            fn: Async side-effect function

        Returns:
            AsyncEither[L, R]: Self unchanged

        Example:
            >>> async def log(x: int) -> None:
            ...     print(f"Value: {x}")
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> await async_either.inspect_async(log)
            # Prints: "Value: 42"
        """

        async def inspected() -> Either[L, R]:
            current = await self
            if current.is_right():
                await fn(cast(R, current.right()))
            return current

        result: AsyncEither[L, R] = AsyncEither(
            lambda: inspected(), self._context_chain
        )
        return result

    @override
    def inspect_left_async(
        self, fn: Callable[[L], Awaitable[None]]
    ) -> AsyncEither[L, R]:
        """Inspect Left value for side effects without modification (left-focused).

        If value is Left, awaits fn(value) for side effects then returns self.
        If value is Right, short-circuits.
        Context stack is preserved.

        Parameters:
            fn: Async side-effect function

        Returns:
            AsyncEither[L, R]: Self unchanged

        Example:
            >>> async def log_error(e: str) -> None:
            ...     print(f"Error: {e}")
            >>> async_either = AsyncEither.from_either(Left("failed"))
            >>> await async_either.inspect_left_async(log_error)
            # Prints: "Error: failed"
        """

        async def inspected() -> Either[L, R]:
            current = await self
            if current.is_left():
                await fn(cast(L, current.left()))
            return current

        result: AsyncEither[L, R] = AsyncEither(
            lambda: inspected(), self._context_chain
        )
        return result

    @override
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
        either = await self
        if either.is_left():
            unwrap_with_context(either.left(), self._context_chain)
        return either.right()  # type: ignore

    @override
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
        either = await self
        if either.is_right():
            unwrap_with_context(either.right(), self._context_chain)
        return either.left()  # type: ignore

    @override
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
        either = await self
        if either.is_right():
            return either.right()  # type: ignore
        return default

    @override
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
        either = await self
        if either.is_left():
            return either.left()  # type: ignore
        return default

    @override
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
        either = await self
        if either.is_right():
            return either.right()  # type: ignore
        else:
            return await fn(either.left())  # type: ignore

    @override
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
        either = await self
        if either.is_left():
            return either.left()  # type: ignore
        else:
            return await fn(either.right())  # type: ignore

    @override
    def context(self, msg: str) -> AsyncEither[L, R]:
        """Push context message to LIFO stack (immutable).

        Adds a message to the head of the context stack. The new message
        will be shown first when unwrap_*_async() raises on wrong variant.

        Parameters:
            msg: Context message to add

        Returns:
            AsyncEither[L, R]: New AsyncEither with updated context

        Example:
            >>> async_either = AsyncEither.from_either(Right(5))
            >>> async_either = async_either.context("step1").context("step2")
            >>> # Context order (LIFO): "step2" → "step1"
        """
        new_either = AsyncEither(self._resolver, self._context_chain.push(msg))
        return new_either

    @override
    def with_context(self, f: Callable[[], str]) -> AsyncEither[L, R]:
        """Push lazily-evaluated context (called immediately, not on await).

        Parameters:
            f: Callable that returns context message

        Returns:
            AsyncEither[L, R]: New AsyncEither with evaluated context

        Example:
            >>> import time
            >>> async_either = AsyncEither.from_either(Right(5))
            >>> async_either = async_either.with_context(lambda: f"time: {time.time()}")
        """
        new_either = AsyncEither(self._resolver, self._context_chain.push_lazy(f))
        return new_either

    @staticmethod
    @override
    def from_either(e: Either[L, R]) -> AsyncEither[L, R]:
        """Create AsyncEither from synchronous Either.

        Wraps a sync Either in an immediately-resolved awaitable.

        Parameters:
            e: The Either[L, R] to wrap

        Returns:
            AsyncEither[L, R]: Wrapped as awaitable

        Example:
            >>> from results import Right, AsyncEither
            >>> async_either = AsyncEither.from_either(Right(42))
            >>> either = await async_either  # Right(42)
        """

        async def resolved() -> Either[L, R]:
            return e

        return AsyncEither(lambda: resolved())

    @staticmethod
    @override
    def from_awaitable(aw: Awaitable[Either[L, R]]) -> AsyncEither[L, R]:
        """Create AsyncEither from Awaitable[Either[L, R]].

        Directly wraps an async operation that returns an Either.

        Parameters:
            aw: The awaitable returning Either[L, R]

        Returns:
            AsyncEither[L, R]: Wrapped as AsyncEither

        Example:
            >>> async def fetch_data(id: int) -> Either[str, Data]:
            ...     return Right(data) if data else Left("not found")
            >>> async_either = AsyncEither.from_awaitable(fetch_data(123))
            >>> either = await async_either
        """
        return AsyncEither(AsyncEither[L, R]._wrap_awaitable(aw))

    @staticmethod
    def _wrap_awaitable(
        aw: Awaitable[Either[L, R]],
    ) -> Callable[[], Awaitable[Either[L, R]]]:
        """Wrap awaitable to support multiple awaits by caching in-flight task."""

        task: asyncio.Future[Either[L, R]] | None = None

        async def resolver() -> Either[L, R]:
            nonlocal task
            if task is None:
                loop = asyncio.get_running_loop()
                if isinstance(aw, asyncio.Future):
                    task = aw
                else:
                    task = loop.create_task(aw)  # type: ignore
            return await task  # type: ignore

        return resolver

    def __repr__(self) -> str:
        """Return debug representation."""
        return (
            f"AsyncEither("
            f"_resolver={self._resolver!r}, "
            f"_context_chain={self._context_chain!r})"
        )

    def __str__(self) -> str:
        """Return human-readable string."""
        if not self._context_chain.is_empty():
            context = "\n  ".join(self._context_chain.messages)
            return f"AsyncEither(context: {context})"
        return "AsyncEither()"
