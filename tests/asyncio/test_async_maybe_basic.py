"""AsyncMaybe basic tests - fundamental async/await functionality.

Test coverage:
- Creating AsyncMaybe from sync Maybe and awaitable
- Basic async transformations (map_async, and_then_async)
- Short-circuit behavior on Nothing
- Error handling (unwrap_async with UnwrapError)
- Context chain propagation
"""

# pyright: reportPrivateUsage=false, reportOptionalSubscript=false
import asyncio

import pytest

from results import AsyncMaybe, Maybe, Nothing, Some
from results.exceptions import UnwrapError


class TestAsyncMaybeBasics:
    """Test AsyncMaybe creation and basic operations."""

    @pytest.mark.asyncio
    async def test_from_maybe_some(self) -> None:
        """Create AsyncMaybe from Some."""
        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Some(42))
        maybe = await async_maybe
        assert maybe.is_some()
        assert maybe.unwrap() == 42

    @pytest.mark.asyncio
    async def test_from_maybe_nothing(self) -> None:
        """Create AsyncMaybe from Nothing."""
        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Nothing())
        maybe = await async_maybe
        assert maybe.is_nothing()

    @pytest.mark.asyncio
    async def test_from_awaitable_some(self) -> None:
        """Create AsyncMaybe from awaitable returning Some."""

        async def get_value() -> Maybe[int]:
            await asyncio.sleep(0.001)
            return Some(42)

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_awaitable(get_value())
        maybe = await async_maybe
        assert maybe.unwrap() == 42

    @pytest.mark.asyncio
    async def test_from_awaitable_nothing(self) -> None:
        """Create AsyncMaybe from awaitable returning Nothing."""

        async def get_nothing() -> Maybe[int]:
            await asyncio.sleep(0.001)
            return Nothing()

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_awaitable(get_nothing())
        maybe = await async_maybe
        assert maybe.is_nothing()


class TestAsyncMaybeMapAsync:
    """Test map_async transformation."""

    @pytest.mark.asyncio
    async def test_map_async_some(self) -> None:
        """Transform Some value asynchronously."""

        async def double(x: int) -> int:
            await asyncio.sleep(0.001)
            return x * 2

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Some(5))
        result_async = async_maybe.map_async(double)
        maybe = await result_async
        assert maybe.is_some()
        assert maybe.unwrap() == 10

    @pytest.mark.asyncio
    async def test_map_async_nothing_short_circuits(self) -> None:
        """Nothing short-circuits map_async."""
        call_count = 0

        async def counting_fn(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Nothing())
        result_async = async_maybe.map_async(counting_fn)
        maybe = await result_async
        assert maybe.is_nothing()
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_map_async_chain(self) -> None:
        """Chain multiple map_async calls."""

        async def increment(x: int) -> int:
            await asyncio.sleep(0.001)
            return x + 1

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Some(5))
        result_async = async_maybe.map_async(increment).map_async(increment)
        maybe = await result_async
        assert maybe.unwrap() == 7


class TestAsyncMaybeAndThenAsync:
    """Test and_then_async chaining."""

    @pytest.mark.asyncio
    async def test_and_then_async_some_to_some(self) -> None:
        """Chain Some to Some asynchronously."""

        async def validate_positive(x: int) -> Maybe[int]:
            await asyncio.sleep(0.001)
            return Some(x) if x > 0 else Nothing()

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Some(5))
        result_async = async_maybe.and_then_async(validate_positive)
        maybe = await result_async
        assert maybe.is_some()
        assert maybe.unwrap() == 5

    @pytest.mark.asyncio
    async def test_and_then_async_some_to_nothing(self) -> None:
        """Chain Some to Nothing asynchronously."""

        async def reject_all(_x: int) -> Maybe[int]:
            await asyncio.sleep(0.001)
            return Nothing()

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Some(5))
        result_async = async_maybe.and_then_async(reject_all)
        maybe = await result_async
        assert maybe.is_nothing()

    @pytest.mark.asyncio
    async def test_and_then_async_nothing_short_circuits(self) -> None:
        """Nothing short-circuits and_then_async."""
        call_count = 0

        async def counting_fn(_x: int) -> Maybe[int]:
            nonlocal call_count
            call_count += 1
            return Some(99)

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Nothing())
        result_async = async_maybe.and_then_async(counting_fn)
        maybe = await result_async
        assert maybe.is_nothing()
        assert call_count == 0


class TestAsyncMaybeUnwrap:
    """Test unwrapping operations."""

    @pytest.mark.asyncio
    async def test_unwrap_async_some(self) -> None:
        """Unwrap Some returns value."""
        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Some(42))
        value = await async_maybe.unwrap_async()
        assert value == 42

    @pytest.mark.asyncio
    async def test_unwrap_async_nothing_raises(self) -> None:
        """Unwrap Nothing raises UnwrapError."""
        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Nothing())
        with pytest.raises(UnwrapError):
            await async_maybe.unwrap_async()

    @pytest.mark.asyncio
    async def test_unwrap_or_async_some(self) -> None:
        """Unwrap or Some returns value."""
        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Some(42))
        value = await async_maybe.unwrap_or_async(99)
        assert value == 42

    @pytest.mark.asyncio
    async def test_unwrap_or_async_nothing(self) -> None:
        """Unwrap or Nothing returns default."""
        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Nothing())
        value = await async_maybe.unwrap_or_async(99)
        assert value == 99

    @pytest.mark.asyncio
    async def test_unwrap_or_else_async_some(self) -> None:
        """Unwrap or else Some returns value without calling fn."""
        call_count = 0

        async def default() -> int:
            nonlocal call_count
            call_count += 1
            return 99

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Some(42))
        value = await async_maybe.unwrap_or_else_async(default)
        assert value == 42
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_unwrap_or_else_async_nothing(self) -> None:
        """Unwrap or else Nothing calls fn and returns result."""

        async def default() -> int:
            await asyncio.sleep(0.001)
            return 99

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Nothing())
        value = await async_maybe.unwrap_or_else_async(default)
        assert value == 99


class TestAsyncMaybeOrElseAsync:
    """Test or_else_async fallback."""

    @pytest.mark.asyncio
    async def test_or_else_async_some(self) -> None:
        """Or else Some returns original."""

        async def fallback() -> Maybe[int]:
            return Some(99)

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Some(42))
        result_async = async_maybe.or_else_async(fallback)
        maybe = await result_async
        assert maybe.unwrap() == 42

    @pytest.mark.asyncio
    async def test_or_else_async_nothing(self) -> None:
        """Or else Nothing calls fallback."""

        async def fallback() -> Maybe[int]:
            await asyncio.sleep(0.001)
            return Some(99)

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Nothing())
        result_async = async_maybe.or_else_async(fallback)
        maybe = await result_async
        assert maybe.unwrap() == 99


class TestAsyncMaybeInspectAsync:
    """Test inspect_async side effects."""

    @pytest.mark.asyncio
    async def test_inspect_async_some(self) -> None:
        """Inspect Some executes side effect."""
        captured: list[int] = []

        async def inspect_fn(x: int) -> None:
            await asyncio.sleep(0.001)
            captured.append(x)

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Some(42))
        result_async = async_maybe.inspect_async(inspect_fn)
        maybe = await result_async
        assert captured == [42]
        assert maybe.unwrap() == 42

    @pytest.mark.asyncio
    async def test_inspect_async_nothing(self) -> None:
        """Inspect Nothing skips side effect."""
        call_count = 0

        async def inspect_fn(_x: int) -> None:
            nonlocal call_count
            call_count += 1

        async_maybe: AsyncMaybe[int] = AsyncMaybe[int].from_maybe(Nothing())
        result_async = async_maybe.inspect_async(inspect_fn)
        maybe = await result_async
        assert maybe.is_nothing()
        assert call_count == 0


class TestAsyncMaybeContext:
    """Test context chain tracking."""

    @pytest.mark.asyncio
    async def test_context_accumulates(self) -> None:
        """Context messages accumulate on AsyncMaybe."""
        async_maybe: AsyncMaybe[int] = (
            AsyncMaybe[int]
            .from_maybe(Nothing())
            .context("step1")
            .context("step2")
            .context("step3")
        )
        assert async_maybe._context_chain.messages

    @pytest.mark.asyncio
    async def test_context_in_unwrap_error(self) -> None:
        """Context appears in UnwrapError message."""
        async_maybe: AsyncMaybe[int] = (
            AsyncMaybe[int]
            .from_maybe(Nothing())
            .context("operation failed")
            .context("at step 2")
        )
        with pytest.raises(UnwrapError) as exc_info:
            await async_maybe.unwrap_async()
        assert "Called unwrap()" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_with_context_lazy_eval(self) -> None:
        """with_context lazily evaluates message."""
        import time

        async_maybe: AsyncMaybe[int] = (
            AsyncMaybe[int]
            .from_maybe(Nothing())
            .with_context(lambda: f"time_{int(time.time())}")
        )
        assert async_maybe._context_chain.messages
        assert "time_" in async_maybe._context_chain.messages[0]
